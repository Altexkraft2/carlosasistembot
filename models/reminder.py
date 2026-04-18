"""
Modelo de datos para los recordatorios.
Con soporte para múltiples recordatorios por usuario.
"""

from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional

@dataclass
class Reminder:
    """Representa un recordatorio en el sistema"""
    
    id: str
    user_id: str
    chat_id: int
    active: bool
    frequency_minutes: int
    message: str
    keyword: str
    photos_received: int
    last_alert: Optional[str]
    created_at: str
    updated_at: str
    
    @classmethod
    def create(cls, user_id: str, chat_id: int, 
               frequency_minutes: int, message: str, keyword: str) -> 'Reminder':
        """Crea un nuevo recordatorio con palabra clave"""
        now = datetime.now().isoformat()
        clean_keyword = keyword.strip().upper()
        reminder_id = f"{chat_id}_{user_id}_{clean_keyword}"
        
        return cls(
            id=reminder_id,
            user_id=user_id,
            chat_id=chat_id,
            active=True,
            frequency_minutes=frequency_minutes,
            message=message,
            keyword=clean_keyword,
            photos_received=0,
            last_alert=None,
            created_at=now,
            updated_at=now
        )
    
    def add_photo(self, caption: str = "") -> bool:
        """Registra una nueva foto recibida."""
        from config import Config
        
        clean_caption = caption.strip().upper()
        
        if self.keyword not in clean_caption:
            return False
        
        self.photos_received += 1
        self.updated_at = datetime.now().isoformat()
        
        if self.photos_received >= Config.PHOTOS_REQUIRED:
            self.active = False
            return True
        return False
    
    def should_alert(self, current_time: datetime) -> bool:
        """Determina si debe enviarse una alerta ahora"""
        if not self.active:
            return False
        
        if self.last_alert is None:
            return True
        
        last = datetime.fromisoformat(self.last_alert)
        minutes_passed = (current_time - last).total_seconds() / 60
        
        return minutes_passed >= self.frequency_minutes
    
    def mark_alert_sent(self):
        """Registra que se ha enviado una alerta"""
        self.last_alert = datetime.now().isoformat()
        self.updated_at = self.last_alert
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Reminder':
        data.pop('start_time', None)
        data.pop('hora_inicio', None)
        if 'keyword' not in data:
            data['keyword'] = 'RECORDATORIO'
        if 'id' not in data:
            data['id'] = f"{data.get('chat_id', 0)}_{data.get('user_id', 'unknown')}_{data['keyword']}"
        return cls(**data)
    
    def get_status_text(self) -> str:
        from config import Config
        
        status = "🟢 ACTIVO" if self.active else "🔴 INACTIVO"
        photos_missing = max(0, Config.PHOTOS_REQUIRED - self.photos_received)
        
        created = datetime.fromisoformat(self.created_at)
        now = datetime.now()
        minutes_active = int((now - created).total_seconds() / 60)
        
        return (
            f"📊 *Estado del recordatorio*\n\n"
            f"{status}\n"
            f"📝 *Mensaje:* {self.message}\n"
            f"🔑 *Palabra clave:* `{self.keyword}`\n"
            f"🔄 *Frecuencia:* cada {self.frequency_minutes} min\n"
            f"⏱️ *Activo desde:* hace {minutes_active} minutos\n"
            f"📸 *Fotos válidas:* {self.photos_received}/{Config.PHOTOS_REQUIRED}\n"
            f"⚠️ *Faltan:* {photos_missing} foto(s)"
        )
    
    def __repr__(self) -> str:
        return f"Reminder(id={self.id}, active={self.active}, keyword={self.keyword}, photos={self.photos_received})"