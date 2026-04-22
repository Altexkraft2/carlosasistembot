"""
Servicio de recordatorios con SQLAlchemy.
"""

from datetime import datetime
from typing import Optional, Dict, List
from database.models import ReminderDB
from database.repository_db import ReminderRepositoryDB
from config import Config
from utils.logger import setup_logger
from utils.validators import validate_frequency

logger = setup_logger(__name__)

class ReminderServiceDB:
    """Servicio de recordatorios con base de datos"""
    
    def __init__(self, repository: ReminderRepositoryDB = None):
        self.repository = repository or ReminderRepositoryDB()
        logger.info("🔄 Servicio de recordatorios (DB) inicializado")
    
    def create_reminder(self, user_telegram_id: str, chat_id: int,
                       frequency: int = None, message: str = None,
                       keyword: str = None, username: str = None,
                       first_name: str = None) -> ReminderDB:
        """Crea un nuevo recordatorio"""
        frequency = frequency or Config.DEFAULT_FREQUENCY_MINUTES
        if not validate_frequency(frequency):
            raise ValueError(f"La frecuencia debe ser entre 1 y 1440 minutos")
        
        if not message:
            message = "⏰ ¡Es hora de tu recordatorio!"
        if not keyword:
            keyword = "RECORDATORIO"
        
        if self.repository.has_active_reminder_with_keyword(user_telegram_id, chat_id, keyword):
            raise ValueError(f"Ya tienes un recordatorio activo con la palabra clave '{keyword}'")
        
        reminder = ReminderDB(
            chat_id=str(chat_id),
            keyword=keyword.upper(),
            message=message,
            frequency_minutes=frequency,
            active=True,
            photos_received=0,
            photos_required=Config.PHOTOS_REQUIRED
        )
        
        saved = self.repository.save(reminder, user_telegram_id, username, first_name)
        logger.info(f"✅ Recordatorio creado: {saved.reminder_id}")
        return saved
    
    def cancel_reminder(self, user_telegram_id: str, chat_id: int, keyword: str = None) -> bool:
        """Cancela recordatorios"""
        if keyword:
            return self.repository.delete_by_keyword(user_telegram_id, chat_id, keyword)
        else:
            reminders = self.repository.find_active_by_user(user_telegram_id, chat_id)
            for r in reminders:
                r.active = False
                self.repository.save(r, user_telegram_id)
            return len(reminders) > 0
    
    def get_user_reminders(self, user_telegram_id: str, chat_id: int) -> List[ReminderDB]:
        """Obtiene recordatorios de un usuario"""
        return self.repository.find_active_by_user(user_telegram_id, chat_id)
    
    def get_chat_reminders(self, chat_id: int) -> List[ReminderDB]:
        """Obtiene recordatorios de un chat"""
        return self.repository.find_active_by_chat(chat_id)
    
    def get_reminder_status(self, user_telegram_id: str, chat_id: int, keyword: str) -> Optional[Dict]:
        """Obtiene estado de un recordatorio"""
        reminder = self.repository.find_by_keyword(user_telegram_id, str(chat_id), keyword)
        if not reminder:
            return None
        return self._format_status(reminder)
    
    def _format_status(self, reminder: ReminderDB) -> Dict:
        """Formatea el estado de un recordatorio"""
        now = datetime.now()
        minutes_active = int((now - reminder.created_at).total_seconds() / 60) if reminder.created_at else 0
        
        next_alert_in = None
        if reminder.active and reminder.last_alert:
            seconds_passed = (now - reminder.last_alert).total_seconds()
            minutes_to_next = reminder.frequency_minutes - (seconds_passed / 60)
            next_alert_in = max(0, round(minutes_to_next))
        
        return {
            'id': reminder.id,
            'active': reminder.active,
            'message': reminder.message,
            'keyword': reminder.keyword,
            'frequency': reminder.frequency_minutes,
            'photos_received': reminder.photos_received,
            'photos_required': reminder.photos_required,
            'photos_missing': reminder.photos_missing,
            'last_alert': reminder.last_alert.isoformat() if reminder.last_alert else None,
            'minutes_active': minutes_active,
            'next_alert_in': next_alert_in,
            'created_at': reminder.created_at.isoformat() if reminder.created_at else None,
            'user_id': reminder.user.telegram_id if reminder.user else None
        }
    
    def get_all_active_reminders(self) -> List[ReminderDB]:
        """Obtiene todos los recordatorios activos"""
        return self.repository.find_all_active()
    
    def get_stats(self) -> Dict:
        """Obtiene estadísticas"""
        return self.repository.get_stats()
    
    def process_photo(self, user_telegram_id: str, chat_id: int, caption: str) -> Dict:
        """Procesa una foto recibida"""
        from services.photo_service_db import PhotoServiceDB
        photo_service = PhotoServiceDB(self.repository)
        return photo_service.process_photo(user_telegram_id, chat_id, caption)