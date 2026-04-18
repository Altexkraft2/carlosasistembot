"""
Servicio de recordatorios.
"""

from datetime import datetime
from typing import Optional, Dict
from models.reminder import Reminder
from database.repository import ReminderRepository
from config import Config
from utils.logger import setup_logger
from utils.validators import validate_frequency

logger = setup_logger(__name__)

class ReminderService:
    """Servicio para manejar la lógica de recordatorios"""
    
    def __init__(self, repository: ReminderRepository = None):
        self.repository = repository or ReminderRepository()
        logger.info("🔄 Servicio de recordatorios inicializado")
    
    def create_reminder(self, user_id: str, chat_id: int,
                       frequency: int = None, message: str = None, 
                       keyword: str = None) -> Reminder:
        frequency = frequency or Config.DEFAULT_FREQUENCY_MINUTES
        if not validate_frequency(frequency):
            raise ValueError(f"La frecuencia debe ser entre 1 y 1440 minutos")
        
        if not message:
            message = "⏰ ¡Es hora de tu recordatorio!"
        if not keyword:
            keyword = "RECORDATORIO"
        
        if self.repository.has_active_reminder_with_keyword(user_id, chat_id, keyword):
            raise ValueError(f"Ya tienes un recordatorio activo con la palabra clave '{keyword}'")
        
        reminder = Reminder.create(
            user_id=user_id,
            chat_id=chat_id,
            frequency_minutes=frequency,
            message=message,
            keyword=keyword
        )
        
        self.repository.save(reminder)
        logger.info(f"✅ Recordatorio creado: {reminder.id}")
        return reminder
    
    def cancel_reminder(self, user_id: str, chat_id: int, keyword: str = None) -> bool:
        if keyword:
            return self.repository.delete_by_keyword(user_id, chat_id, keyword)
        else:
            active = self.repository.find_active_by_user(user_id, chat_id)
            for reminder in active.values():
                reminder.active = False
                self.repository.save(reminder)
            return len(active) > 0
    
    def get_active_reminder(self, user_id: str, chat_id: int, keyword: str) -> Optional[Reminder]:
        return self.repository.find_by_keyword(user_id, chat_id, keyword)
    
    def get_user_reminders(self, user_id: str, chat_id: int) -> Dict[str, Reminder]:
        return self.repository.find_active_by_user(user_id, chat_id)
    
    def get_chat_reminders(self, chat_id: int) -> Dict[str, Reminder]:
        return self.repository.find_active_by_chat(chat_id)
    
    def get_reminder_status(self, user_id: str, chat_id: int, keyword: str = None) -> Optional[Dict]:
        if keyword:
            reminder = self.repository.find_by_keyword(user_id, chat_id, keyword)
            if not reminder:
                return None
            return self._format_status(reminder)
        return None
    
    def _format_status(self, reminder: Reminder) -> Dict:
        now = datetime.now()
        created = datetime.fromisoformat(reminder.created_at)
        minutes_active = int((now - created).total_seconds() / 60)
        
        next_alert_in = None
        if reminder.active and reminder.last_alert:
            last = datetime.fromisoformat(reminder.last_alert)
            seconds_passed = (now - last).total_seconds()
            minutes_to_next = reminder.frequency_minutes - (seconds_passed / 60)
            next_alert_in = max(0, round(minutes_to_next))
        
        return {
            'id': reminder.id,
            'active': reminder.active,
            'message': reminder.message,
            'keyword': reminder.keyword,
            'frequency': reminder.frequency_minutes,
            'photos_received': reminder.photos_received,
            'photos_required': Config.PHOTOS_REQUIRED,
            'photos_missing': max(0, Config.PHOTOS_REQUIRED - reminder.photos_received),
            'last_alert': reminder.last_alert,
            'minutes_active': minutes_active,
            'next_alert_in': next_alert_in,
            'created_at': reminder.created_at,
            'user_id': reminder.user_id
        }
    
    def get_all_active_reminders(self) -> Dict[str, Reminder]:
        return self.repository.find_all_active()
    
    def get_stats(self) -> Dict:
        return self.repository.get_stats()