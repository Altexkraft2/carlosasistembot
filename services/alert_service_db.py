"""
Servicio de alertas con SQLAlchemy.
"""
from datetime import datetime
from database.models import ReminderDB, SessionLocal
from database.repository_db import ReminderRepositoryDB
from services.reminder_service_db import ReminderServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class AlertServiceDB:
    """Servicio para manejar alertas periódicas"""
    
    def __init__(self, reminder_service: ReminderServiceDB = None):
        self.reminder_service = reminder_service or ReminderServiceDB()
        self.bot = None
        logger.info("🔔 Servicio de alertas (DB) inicializado")
    
    def set_bot(self, bot):
        self.bot = bot
        logger.info("🤖 Bot vinculado")
    
    async def check_and_send_alerts(self) -> int:
        """Verifica y envía alertas - USA SU PROPIA SESIÓN"""
        if not self.bot:
            return 0
        
        now = datetime.now()
        logger.info(f"🕐 Verificando alertas: {now.strftime('%H:%M:%S')}")
        
        if not Config.is_work_time(now):
            logger.info(f"⏸️ Fuera de horario laboral")
            return 0
        
        # USAR UNA SESIÓN DIRECTA para todo el proceso
        session = SessionLocal()
        sent = 0
        
        try:
            # Consultar recordatorios activos DIRECTAMENTE
            from database.models import User
            from sqlalchemy.orm import joinedload
            
            reminders = session.query(ReminderDB)\
                .options(joinedload(ReminderDB.user))\
                .filter(ReminderDB.active == True)\
                .all()
            
            logger.info(f"🔍 Recordatorios activos encontrados: {len(reminders)}")
            
            if not reminders:
                logger.info("ℹ️ No hay recordatorios activos")
                return 0
            
            # Mostrar cada recordatorio
            for r in reminders:
                user_id = r.user.telegram_id if r.user else "?"
                logger.info(f"  📝 '{r.keyword}' | chat={r.chat_id} | user={user_id} | fotos={r.photos_received}/{r.photos_required} | last_alert={r.last_alert} | freq={r.frequency_minutes}min")
            
            # Procesar cada recordatorio
            for reminder in reminders:
                try:
                    should_alert = reminder.should_alert(now)
                    logger.info(f"  ⏰ '{reminder.keyword}': should_alert={should_alert}")
                    
                    if should_alert:
                        logger.info(f"  📨 Enviando alerta a chat {reminder.chat_id}...")
                        
                        # Enviar mensaje
                        try:
                            remaining = max(0, Config.PHOTOS_REQUIRED - reminder.photos_received)
                            message = (
                                f"{reminder.message}\n\n"
                                f"⚠️ Faltan {remaining} foto(s) con `{reminder.keyword}` para detener las alertas.\n"
                                f"📸 Envía las fotos con la palabra clave en el pie de foto."
                            )
                            
                            chat_id = reminder.chat_id
                            if isinstance(chat_id, str) and chat_id.lstrip('-').isdigit():
                                chat_id = int(chat_id)
                            
                            await self.bot.send_message(
                                chat_id=chat_id,
                                text=message,
                                parse_mode='Markdown',
                                reply_markup=inline_keyboards.get_alert_keyboard()
                            )
                            
                            # Actualizar en la MISMA sesión
                            reminder.last_alert = datetime.now()
                            reminder.updated_at = datetime.now()
                            
                            # Guardar log de alerta
                            from database.models import AlertLog
                            log = AlertLog(
                                reminder_id=reminder.id,
                                status='sent'
                            )
                            session.add(log)
                            session.commit()
                            
                            sent += 1
                            logger.info(f"  ✅ Alerta enviada y guardada")
                            
                        except Exception as e:
                            logger.error(f"  ❌ Error enviando alerta: {e}")
                            session.rollback()
                            
                except Exception as e:
                    logger.error(f"  ❌ Error procesando '{reminder.keyword}': {e}")
                    session.rollback()
            
            logger.info(f"📨 Total alertas enviadas: {sent}")
            return sent
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error general: {e}", exc_info=True)
            return 0
        finally:
            session.close()