"""
Repositorio con SQLAlchemy para producción.
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_

from database.models import (
    User, ReminderDB, AlertLog, PhotoLog, 
    SessionLocal, init_db, engine
)
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ReminderRepositoryDB:
    """Repositorio con SQLAlchemy"""
    
    def __init__(self):
        init_db()
        logger.info("📚 Repositorio SQLAlchemy inicializado")
    
    def _get_session(self) -> Session:
        return SessionLocal()
    
    def _get_or_create_user(self, session: Session, telegram_id: str, 
                           username: str = None, first_name: str = None) -> User:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name
            )
            session.add(user)
            session.commit()
            session.refresh(user)
            logger.info(f"👤 Nuevo usuario creado: {telegram_id}")
        else:
            if username:
                user.username = username
            if first_name:
                user.first_name = first_name
            user.updated_at = datetime.now()
            session.commit()
        
        return user
    
    def find_by_keyword(self, user_telegram_id: str, chat_id: str, keyword: str) -> Optional[ReminderDB]:
        session = self._get_session()
        try:
            reminder = session.query(ReminderDB)\
                .options(joinedload(ReminderDB.user))\
                .join(User)\
                .filter(
                    and_(
                        User.telegram_id == user_telegram_id,
                        ReminderDB.chat_id == str(chat_id),
                        ReminderDB.keyword == keyword.upper(),
                        ReminderDB.active == True
                    )
                ).first()
            
            if reminder:
                session.expunge(reminder)
            return reminder
        finally:
            session.close()
    
    def find_all_active(self) -> List[ReminderDB]:
        session = self._get_session()
        try:
            reminders = session.query(ReminderDB)\
                .options(joinedload(ReminderDB.user))\
                .filter(ReminderDB.active == True)\
                .all()
            
            for r in reminders:
                session.expunge(r)
            
            return reminders
        finally:
            session.close()
    
    def find_active_by_chat(self, chat_id: int) -> List[ReminderDB]:
        session = self._get_session()
        try:
            reminders = session.query(ReminderDB)\
                .options(joinedload(ReminderDB.user))\
                .filter(
                    and_(
                        ReminderDB.chat_id == str(chat_id),
                        ReminderDB.active == True
                    )
                ).all()
            
            for r in reminders:
                session.expunge(r)
            
            return reminders
        finally:
            session.close()
    
    def find_active_by_user(self, user_telegram_id: str, chat_id: int = None) -> List[ReminderDB]:
        session = self._get_session()
        try:
            query = session.query(ReminderDB)\
                .options(joinedload(ReminderDB.user))\
                .join(User)\
                .filter(
                    and_(
                        User.telegram_id == user_telegram_id,
                        ReminderDB.active == True
                    )
                )
            if chat_id:
                query = query.filter(ReminderDB.chat_id == str(chat_id))
            
            reminders = query.all()
            
            for r in reminders:
                session.expunge(r)
            
            return reminders
        finally:
            session.close()
    
    def has_active_reminder_with_keyword(self, user_telegram_id: str, chat_id: int, keyword: str) -> bool:
        reminder = self.find_by_keyword(user_telegram_id, str(chat_id), keyword)
        return reminder is not None
    
    def save(self, reminder: ReminderDB, user_telegram_id: str, 
             username: str = None, first_name: str = None) -> ReminderDB:
        session = self._get_session()
        try:
            user = self._get_or_create_user(session, user_telegram_id, username, first_name)
            
            existing = session.query(ReminderDB).filter(
                and_(
                    ReminderDB.user_id == user.id,
                    ReminderDB.chat_id == reminder.chat_id,
                    ReminderDB.keyword == reminder.keyword
                )
            ).first()
            
            if existing:
                existing.active = reminder.active
                existing.message = reminder.message
                existing.frequency_minutes = reminder.frequency_minutes
                existing.photos_received = reminder.photos_received
                existing.photos_required = reminder.photos_required
                existing.last_alert = reminder.last_alert
                existing.updated_at = datetime.now()
                session.commit()
                session.refresh(existing)
                logger.info(f"🔄 Recordatorio actualizado: {existing.reminder_id}")
                return existing
            else:
                reminder.user_id = user.id
                session.add(reminder)
                session.commit()
                session.refresh(reminder)
                logger.info(f"✅ Recordatorio creado: {reminder.reminder_id}")
                return reminder
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error guardando recordatorio: {e}")
            raise
        finally:
            session.close()
    
    def delete_by_keyword(self, user_telegram_id: str, chat_id: int, keyword: str) -> bool:
        session = self._get_session()
        try:
            user = session.query(User).filter(User.telegram_id == user_telegram_id).first()
            if not user:
                return False
            
            reminder = session.query(ReminderDB).filter(
                and_(
                    ReminderDB.user_id == user.id,
                    ReminderDB.chat_id == str(chat_id),
                    ReminderDB.keyword == keyword.upper()
                )
            ).first()
            
            if reminder:
                reminder.active = False
                session.commit()
                logger.info(f"🗑️ Recordatorio desactivado: {reminder.reminder_id}")
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error eliminando recordatorio: {e}")
            return False
        finally:
            session.close()
    
    def log_alert(self, reminder_id: int, status: str = 'sent', error_message: str = None):
        session = self._get_session()
        try:
            log = AlertLog(
                reminder_id=reminder_id,
                status=status,
                error_message=error_message
            )
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error guardando log de alerta: {e}")
        finally:
            session.close()
    
    def log_photo(self, reminder_id: int, user_telegram_id: str, chat_id: int, 
                  caption: str, keyword_matched: bool, photo_number: int):
        session = self._get_session()
        try:
            log = PhotoLog(
                reminder_id=reminder_id,
                user_telegram_id=user_telegram_id,
                chat_id=str(chat_id),
                caption=caption,
                keyword_matched=keyword_matched,
                photo_number=photo_number
            )
            session.add(log)
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error guardando log de foto: {e}")
        finally:
            session.close()
    
    def get_stats(self) -> dict:
        session = self._get_session()
        try:
            total_users = session.query(User).count()
            total_reminders = session.query(ReminderDB).count()
            active_reminders = session.query(ReminderDB).filter(ReminderDB.active == True).count()
            total_photos = session.query(PhotoLog).count()
            total_alerts = session.query(AlertLog).count()
            
            return {
                'total_usuarios': total_users,
                'total_recordatorios': total_reminders,
                'activos': active_reminders,
                'inactivos': total_reminders - active_reminders,
                'total_fotos': total_photos,
                'total_alertas': total_alerts
            }
        finally:
            session.close()
    
    def count_active(self) -> int:
        session = self._get_session()
        try:
            return session.query(ReminderDB).filter(ReminderDB.active == True).count()
        finally:
            session.close()
    
    def count_active_in_chat(self, chat_id: int) -> int:
        session = self._get_session()
        try:
            return session.query(ReminderDB).filter(
                and_(
                    ReminderDB.chat_id == str(chat_id),
                    ReminderDB.active == True
                )
            ).count()
        finally:
            session.close()