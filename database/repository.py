"""
Repositorio de recordatorios.
"""

from typing import Optional, Dict
from models.reminder import Reminder
from database.json_storage import JSONStorage
from utils.logger import setup_logger

logger = setup_logger(__name__)

class ReminderRepository:
    """Repositorio para manejar recordatorios"""
    
    def __init__(self, storage: JSONStorage = None):
        self.storage = storage or JSONStorage()
        logger.info("📚 Repositorio inicializado")
    
    def find_by_id(self, reminder_id: str) -> Optional[Reminder]:
        return self.storage.get_by_id(reminder_id)
    
    def find_by_keyword(self, user_id: str, chat_id: int, keyword: str) -> Optional[Reminder]:
        reminder_id = f"{chat_id}_{user_id}_{keyword.upper()}"
        return self.find_by_id(reminder_id)
    
    def find_all_active(self) -> Dict[str, Reminder]:
        return self.storage.get_all_active()
    
    def find_active_by_chat(self, chat_id: int) -> Dict[str, Reminder]:
        return self.storage.get_active_by_chat(chat_id)
    
    def find_active_by_user(self, user_id: str, chat_id: int = None) -> Dict[str, Reminder]:
        return self.storage.get_active_by_user(user_id, chat_id)
    
    def has_active_reminder_with_keyword(self, user_id: str, chat_id: int, keyword: str) -> bool:
        reminder = self.find_by_keyword(user_id, chat_id, keyword)
        return reminder is not None and reminder.active
    
    def save(self, reminder: Reminder) -> Reminder:
        self.storage.save_reminder(reminder)
        return reminder
    
    def delete(self, reminder_id: str) -> bool:
        return self.storage.delete(reminder_id)
    
    def delete_by_keyword(self, user_id: str, chat_id: int, keyword: str) -> bool:
        reminder_id = f"{chat_id}_{user_id}_{keyword.upper()}"
        return self.delete(reminder_id)
    
    def count_active(self) -> int:
        return len(self.find_all_active())
    
    def count_active_in_chat(self, chat_id: int) -> int:
        return len(self.find_active_by_chat(chat_id))
    
    def get_stats(self) -> dict:
        return self.storage.get_stats()