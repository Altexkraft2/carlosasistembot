"""
Servicio de fotos.
"""

from typing import Dict, Optional
from models.reminder import Reminder
from database.repository import ReminderRepository
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

def escape_markdown(text: str) -> str:
    if not text:
        return text
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

class PhotoService:
    """Servicio para manejar la verificación de fotos."""
    
    def __init__(self, repository: ReminderRepository = None):
        self.repository = repository or ReminderRepository()
        logger.info("📸 Servicio de fotos inicializado")
    
    def process_photo(self, user_id: str, chat_id: int, caption: str = "") -> Dict:
        caption_upper = caption.strip().upper()
        active_reminders = self.repository.find_active_by_chat(chat_id)
        
        matching_reminder = None
        for reminder in active_reminders.values():
            if reminder.keyword in caption_upper:
                matching_reminder = reminder
                break
        
        if not matching_reminder:
            return {
                'success': False,
                'has_reminder': False,
                'message': 'ℹ️ No se encontró ningún recordatorio activo con esa palabra clave.'
            }
        
        completed = matching_reminder.add_photo(caption)
        self.repository.save(matching_reminder)
        
        if completed:
            logger.info(f"🎉 Recordatorio {matching_reminder.id} completado")
            return {
                'success': True,
                'completed': True,
                'photos_received': matching_reminder.photos_received,
                'keyword': matching_reminder.keyword,
                'message': self._get_completion_message(matching_reminder)
            }
        else:
            remaining = Config.PHOTOS_REQUIRED - matching_reminder.photos_received
            return {
                'success': True,
                'completed': False,
                'photos_received': matching_reminder.photos_received,
                'photos_required': Config.PHOTOS_REQUIRED,
                'remaining': remaining,
                'keyword': matching_reminder.keyword,
                'message': self._get_progress_message(matching_reminder)
            }
    
    def _get_progress_message(self, reminder: Reminder) -> str:
        remaining = Config.PHOTOS_REQUIRED - reminder.photos_received
        progress_bar = self._create_progress_bar(reminder.photos_received, Config.PHOTOS_REQUIRED)
        escaped_keyword = escape_markdown(reminder.keyword)
        
        if remaining == 1:
            return (
                f"📸 ¡Foto {reminder.photos_received} recibida!\n"
                f"🔑 Palabra clave: `{escaped_keyword}`\n"
                f"{progress_bar}\n"
                f"⚠️ Necesitas enviar 1 foto más con `{escaped_keyword}` para detener las alertas."
            )
        else:
            return (
                f"📸 ¡Foto {reminder.photos_received} recibida!\n"
                f"🔑 Palabra clave: `{escaped_keyword}`\n"
                f"{progress_bar}\n"
                f"⚠️ Faltan {remaining} fotos con `{escaped_keyword}` para completar."
            )
    
    def _get_completion_message(self, reminder: Reminder) -> str:
        progress_bar = self._create_progress_bar(Config.PHOTOS_REQUIRED, Config.PHOTOS_REQUIRED)
        escaped_keyword = escape_markdown(reminder.keyword)
        
        return (
            f"🎉 ¡FELICITACIONES! 🎉\n"
            f"{progress_bar}\n"
            f"✅ Has completado el recordatorio.\n"
            f"🔑 Palabra clave: `{escaped_keyword}`\n"
            f"🔕 Las alertas se han detenido.\n\n"
            f"📊 Total de fotos válidas: {reminder.photos_received}"
        )
    
    def _create_progress_bar(self, current: int, total: int, length: int = 10) -> str:
        if total == 0:
            return "[▒▒▒▒▒▒▒▒▒▒] 0%"
        filled = int((current / total) * length)
        empty = length - filled
        bar = "█" * filled + "▒" * empty
        percentage = (current / total) * 100
        return f"[{bar}] {percentage:.0f}%"