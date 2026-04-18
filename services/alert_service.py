"""
Servicio de alertas.
"""

from datetime import datetime
from models.reminder import Reminder
from services.reminder_service import ReminderService
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class AlertService:
    """Servicio para manejar alertas periódicas"""
    
    def __init__(self, reminder_service: ReminderService = None):
        self.reminder_service = reminder_service or ReminderService()
        self.bot = None
        logger.info("🔔 Servicio de alertas inicializado")
    
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
        for reminder_id, reminder in active.items():
            try:
                if reminder.should_alert(now):
                    await self._send_alert(reminder)
                    reminder.mark_alert_sent()
                    self.reminder_service.repository.save(reminder)
                    sent += 1
            except Exception as e:
                logger.error(f"❌ Error enviando alerta: {e}")
        
        if sent > 0:
            logger.info(f"📨 {sent} alertas enviadas")
        
        return sent
    
    async def _send_alert(self, reminder: Reminder):
        remaining = max(0, Config.PHOTOS_REQUIRED - reminder.photos_received)
        message = (
            f"{reminder.message}\n\n"
            f"⚠️ Faltan {remaining} foto(s) con `{reminder.keyword}` para detener las alertas.\n"
            f"📸 Envía las fotos con la palabra clave en el pie de foto."
        )
        
        await self.bot.send_message(
            chat_id=reminder.chat_id,
            text=message,
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_alert_keyboard()
        )