"""
Servicio de alertas con SQLAlchemy.
"""

from datetime import datetime
from database.models import ReminderDB, AlertLog, SessionLocal
from services.reminder_service_db import ReminderServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config
from sqlalchemy.orm import joinedload

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
        """Verifica y envía alertas"""
        if not self.bot:
            return 0
        
        now = datetime.now()
        logger.info(f"🕐 Verificando alertas: {now.strftime('%H:%M:%S')}")
        
        if not Config.is_work_time(now):
            logger.info(f"⏸️ Fuera de horario laboral")
            return 0
        
        session = SessionLocal()
        sent = 0
        
        try:
            reminders = session.query(ReminderDB)\
                .options(joinedload(ReminderDB.user))\
                .filter(ReminderDB.active == True)\
                .all()
            
            logger.info(f"🔍 Recordatorios activos: {len(reminders)}")
            
            for r in reminders:
                user_id = r.user.telegram_id if r.user else "?"
                logger.info(f"  📝 '{r.keyword}' | chat={r.chat_id} | user={user_id} | tipo={r.reminder_type} | fotos={r.photos_received}/{r.photos_required}")
            
            for reminder in reminders:
                try:
                    if reminder.should_alert(now):
                        logger.info(f"  📨 Enviando alerta '{reminder.keyword}' a chat {reminder.chat_id}")
                        success = await self._send_alert(reminder)
                        
                        if success:
                            reminder.mark_alert_sent()
                            log = AlertLog(reminder_id=reminder.id, status='sent')
                            session.add(log)
                            session.commit()
                            sent += 1
                            logger.info(f"  ✅ Alerta enviada")
                        else:
                            logger.warning(f"  ❌ Falló envío")
                            
                except Exception as e:
                    logger.error(f"  ❌ Error: {e}")
                    session.rollback()
            
            return sent
            
        except Exception as e:
            session.rollback()
            logger.error(f"❌ Error general: {e}")
            return 0
        finally:
            session.close()
    
    async def _send_alert(self, reminder: ReminderDB) -> bool:
        """Envía una alerta"""
        try:
            # Mensaje diferente según tipo
            if reminder.reminder_type == 'simple':
                footer = f"\n\n❌ Para detener: /cancelar {reminder.keyword}"
            else:
                remaining = max(0, Config.PHOTOS_REQUIRED - reminder.photos_received)
                footer = f"\n\n⚠️ Faltan {remaining} foto(s) con `{reminder.keyword}`\n📸 Envía fotos con la palabra clave."
            
            chat_id = int(reminder.chat_id) if str(reminder.chat_id).lstrip('-').isdigit() else reminder.chat_id
            
            if reminder.original_file_id and reminder.original_message_type in ['photo', 'video', 'document']:
                caption = f"{reminder.original_caption or reminder.message}{footer}"
                
                if reminder.original_message_type == 'photo':
                    await self.bot.send_photo(
                        chat_id=chat_id, photo=reminder.original_file_id,
                        caption=caption, parse_mode='Markdown',
                        reply_markup=inline_keyboards.get_alert_keyboard()
                    )
                elif reminder.original_message_type == 'video':
                    await self.bot.send_video(
                        chat_id=chat_id, video=reminder.original_file_id,
                        caption=caption, parse_mode='Markdown',
                        reply_markup=inline_keyboards.get_alert_keyboard()
                    )
                elif reminder.original_message_type == 'document':
                    await self.bot.send_document(
                        chat_id=chat_id, document=reminder.original_file_id,
                        caption=caption, parse_mode='Markdown',
                        reply_markup=inline_keyboards.get_alert_keyboard()
                    )
                else:
                    await self.bot.send_message(
                        chat_id=chat_id, text=f"{reminder.message}{footer}",
                        parse_mode='Markdown',
                        reply_markup=inline_keyboards.get_alert_keyboard()
                    )
            else:
                await self.bot.send_message(
                    chat_id=chat_id, text=f"{reminder.message}{footer}",
                    parse_mode='Markdown',
                    reply_markup=inline_keyboards.get_alert_keyboard()
                )
            
            return True
        except Exception as e:
            logger.error(f"❌ Error enviando alerta: {e}")
            return False