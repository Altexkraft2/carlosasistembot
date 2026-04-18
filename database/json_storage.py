"""
Capa de almacenamiento en JSON.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from models.reminder import Reminder
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class JSONStorage:
    """Almacenamiento en archivo JSON"""
    
    def __init__(self, file_path: Path = None):
        self.file_path = file_path or Config.DATA_FILE
        self._data: Dict[str, dict] = {}
        self.load()
    
    def load(self) -> None:
        try:
            if self.file_path.exists():
                with open(self.file_path, 'r', encoding='utf-8') as f:
                    self._data = json.load(f)
                logger.info(f"✅ Datos cargados: {len(self._data)} recordatorios encontrados")
                activos = sum(1 for r in self._data.values() if r.get('active', False))
                logger.info(f"   - Activos: {activos}")
                logger.info(f"   - Inactivos: {len(self._data) - activos}")
            else:
                self._data = {}
                logger.info("📝 No se encontró archivo de datos, iniciando vacío")
        except Exception as e:
            logger.error(f"❌ Error cargando datos: {e}")
            self._data = {}
    
    def save(self) -> None:
        try:
            self.file_path.parent.mkdir(exist_ok=True)
            with open(self.file_path, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
            logger.debug(f"💾 Datos guardados: {len(self._data)} recordatorios")
        except Exception as e:
            logger.error(f"❌ Error guardando datos: {e}")
    
    def get_by_id(self, reminder_id: str) -> Optional[Reminder]:
        data = self._data.get(reminder_id)
        if data:
            try:
                return Reminder.from_dict(data)
            except Exception as e:
                logger.error(f"❌ Error cargando recordatorio {reminder_id}: {e}")
        return None
    
    def get_all_active(self) -> Dict[str, Reminder]:
        active = {}
        for reminder_id, data in self._data.items():
            if data.get('active', False):
                try:
                    active[reminder_id] = Reminder.from_dict(data)
                except Exception as e:
                    logger.error(f"❌ Error cargando recordatorio {reminder_id}: {e}")
        return active
    
    def get_active_by_chat(self, chat_id: int) -> Dict[str, Reminder]:
        active = self.get_all_active()
        return {rid: r for rid, r in active.items() if r.chat_id == chat_id}
    
    def get_active_by_user(self, user_id: str, chat_id: int = None) -> Dict[str, Reminder]:
        active = self.get_all_active()
        if chat_id:
            return {rid: r for rid, r in active.items() if r.user_id == user_id and r.chat_id == chat_id}
        return {rid: r for rid, r in active.items() if r.user_id == user_id}
    
    def save_reminder(self, reminder: Reminder) -> None:
        self._data[reminder.id] = reminder.to_dict()
        self.save()
        logger.info(f"✅ Recordatorio guardado: {reminder.id}")
    
    def delete(self, reminder_id: str) -> bool:
        if reminder_id in self._data:
            del self._data[reminder_id]
            self.save()
            logger.info(f"🗑️ Recordatorio eliminado: {reminder_id}")
            return True
        return False
    
    def get_stats(self) -> dict:
        total = len(self._data)
        activos = sum(1 for r in self._data.values() if r.get('active', False))
        fotos = sum(r.get('photos_received', 0) for r in self._data.values())
        return {
            'total_recordatorios': total,
            'activos': activos,
            'inactivos': total - activos,
            'total_fotos': fotos,
            'archivo': str(self.file_path)
        }