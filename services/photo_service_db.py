"""
Servicio de fotos con SQLAlchemy.
"""

from typing import Dict
from database.models import ReminderDB
from database.repository_db import ReminderRepositoryDB
from config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

def escape_markdown(text: str) -> str:
    """Escapa caracteres especiales de Markdown"""
    if not text:
        return text
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

class PhotoServiceDB:
    """Servicio para manejar la verificación de fotos con SQLite"""
    
    def __init__(self, repository: ReminderRepositoryDB = None):
        self.repository = repository or ReminderRepositoryDB()
        logger.info("📸 Servicio de fotos (DB) inicializado")
    
    def process_photo(self, user_telegram_id: str, chat_id: int, caption: str = "",
                      username: str = None, first_name: str = None) -> Dict:
        """
        Procesa una foto recibida.
        
        Args:
            user_telegram_id: ID de Telegram del usuario que envía la foto
            chat_id: ID del chat donde se envió
            caption: Pie de foto (debe contener la palabra clave)
            username: Username del usuario (opcional)
            first_name: Nombre del usuario (opcional)
            
        Returns:
            Diccionario con el resultado del procesamiento
        """
        caption_upper = caption.strip().upper()
        active_reminders = self.repository.find_active_by_chat(chat_id)
        
        matching_reminder = None
        for reminder in active_reminders:
            if reminder.keyword in caption_upper:
                matching_reminder = reminder
                break
        
        if not matching_reminder:
            return {
                'success': False,
                'has_reminder': False,
                'message': 'ℹ️ No se encontró ningún recordatorio activo con esa palabra clave.'
            }
        
        # Verificar si la foto la envía el dueño del recordatorio
        reminder_owner = matching_reminder.user.telegram_id if matching_reminder.user else None
        is_owner = reminder_owner == user_telegram_id
        
        # Añadir foto
        completed = matching_reminder.add_photo()
        
        # Guardar en base de datos
        saved_reminder = self.repository.save(
            matching_reminder, 
            reminder_owner or user_telegram_id,
            username,
            first_name
        )
        
        # Registrar en PhotoLog
        self.repository.log_photo(
            reminder_id=saved_reminder.id,
            user_telegram_id=user_telegram_id,
            chat_id=chat_id,
            caption=caption,
            keyword_matched=True,
            photo_number=saved_reminder.photos_received
        )
        
        if completed:
            logger.info(f"🎉 Recordatorio {saved_reminder.reminder_id} completado")
            return {
                'success': True,
                'completed': True,
                'photos_received': saved_reminder.photos_received,
                'keyword': saved_reminder.keyword,
                'is_owner': is_owner,
                'message': self._get_completion_message(saved_reminder)
            }
        else:
            remaining = Config.PHOTOS_REQUIRED - saved_reminder.photos_received
            logger.info(f"📸 Foto {saved_reminder.photos_received}/{Config.PHOTOS_REQUIRED} para {saved_reminder.keyword}")
            return {
                'success': True,
                'completed': False,
                'photos_received': saved_reminder.photos_received,
                'photos_required': Config.PHOTOS_REQUIRED,
                'remaining': remaining,
                'keyword': saved_reminder.keyword,
                'is_owner': is_owner,
                'message': self._get_progress_message(saved_reminder)
            }
    
    def get_photo_status(self, user_telegram_id: str, chat_id: int, keyword: str) -> Dict:
        """
        Obtiene el estado de fotos de un recordatorio específico.
        
        Args:
            user_telegram_id: ID de Telegram del usuario
            chat_id: ID del chat
            keyword: Palabra clave del recordatorio
            
        Returns:
            Diccionario con el estado
        """
        reminder = self.repository.find_by_keyword(user_telegram_id, str(chat_id), keyword)
        
        if not reminder:
            return {
                'success': False,
                'message': f"❌ No se encontró el recordatorio '{keyword}'."
            }
        
        return {
            'success': True,
            'keyword': reminder.keyword,
            'active': reminder.active,
            'photos_received': reminder.photos_received,
            'photos_required': reminder.photos_required,
            'remaining': reminder.photos_missing,
            'progress_percentage': (reminder.photos_received / reminder.photos_required * 100) if reminder.photos_required > 0 else 0
        }
    
    def _get_progress_message(self, reminder: ReminderDB) -> str:
        """Genera un mensaje de progreso"""
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
    
    def _get_completion_message(self, reminder: ReminderDB) -> str:
        """Genera un mensaje de completado"""
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
        """Crea una barra de progreso visual"""
        if total == 0:
            return "[▒▒▒▒▒▒▒▒▒▒] 0%"
        filled = int((current / total) * length)
        empty = length - filled
        bar = "█" * filled + "▒" * empty
        percentage = (current / total) * 100
        return f"[{bar}] {percentage:.0f}%"