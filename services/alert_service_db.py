"""
Servicio de alertas con SQLAlchemy.
"""

from datetime import datetime
from database.models import ReminderDB
from services.reminder_service_db import ReminderServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class AlertServiceDB:
    """Servicio para manejar alertas periódicas con SQLite"""
    
    def __init__(self, reminder_service: ReminderServiceDB = None):
        self.reminder_service = reminder_service or ReminderServiceDB()
        self.bot = None
        logger.info("🔔 Servicio de alertas (DB) inicializado")
    
    def set_bot(self, bot):
        self.bot = bot
        logger.info("🤖 Bot vinculado")
    
    async def check_and_send_alerts(self) -> int:
        if not self.bot:
            return 0
        
        now = datetime.now()
        
        if not Config.is_work_time(now):
            logger.debug(f"⏸️ Fuera de horario laboral: {now.strftime('%H:%M')}")
            return 0
        
        active = self.reminder_service.get_all_active_reminders()
        if not active:
            return 0
        
        sent = 0
        for reminder in active:
            try:
                if reminder.should_alert(now):
                    await self._send_alert(reminder)
                    reminder.mark_alert_sent()
                    self.reminder_service.repository.save(
                        reminder, 
                        reminder.user.telegram_id if reminder.user else "unknown"
                    )
                    self.reminder_service.repository.log_alert(reminder.id, 'sent')
                    sent += 1
            except Exception as e:
                logger.error(f"❌ Error enviando alerta: {e}")
                self.reminder_service.repository.log_alert(
                    reminder.id, 'error', str(e)
                )
        
        if sent > 0:
            logger.info(f"📨 {sent} alertas enviadas")
        
        return sent
    
    async def _send_alert(self, reminder: ReminderDB):
        remaining = max(0, Config.PHOTOS_REQUIRED - reminder.photos_received)
        message = (
            f"{reminder.message}\n\n"
            f"⚠️ Faltan {remaining} foto(s) con `{reminder.keyword}` para detener las alertas.\n"
            f"📸 Envía las fotos con la palabra clave en el pie de foto."
        )
        
        await self.bot.send_message(
            chat_id=int(reminder.chat_id) if reminder.chat_id.isdigit() else reminder.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_alert_keyboard()
        )