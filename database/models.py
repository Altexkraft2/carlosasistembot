"""
Modelos SQLAlchemy para la base de datos.
Compatible con SQLAlchemy 1.4.x y 2.0.x
"""

from datetime import datetime
from sqlalchemy import (
    create_engine, Column, String, Integer, Boolean, 
    DateTime, ForeignKey, Text
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.pool import NullPool
from config import Config

Base = declarative_base()

class User(Base):
    """Modelo de usuario de Telegram"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), unique=True, nullable=False, index=True)
    username = Column(String(100), nullable=True)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    reminders = relationship("ReminderDB", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"User(telegram_id={self.telegram_id}, username={self.username})"


class ReminderDB(Base):
    """Modelo de recordatorio en la base de datos"""
    __tablename__ = 'reminders'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    chat_id = Column(String(50), nullable=False, index=True)
    keyword = Column(String(100), nullable=False)
    message = Column(Text, nullable=False)
    frequency_minutes = Column(Integer, default=5)
    active = Column(Boolean, default=True)
    photos_received = Column(Integer, default=0)
    photos_required = Column(Integer, default=2)
    last_alert = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    # Campos para mensajes reenviados
    original_message_id = Column(Integer, nullable=True)
    original_message_type = Column(String(20), nullable=True)
    original_caption = Column(Text, nullable=True)
    original_file_id = Column(String(200), nullable=True)
    
    # Tipo de recordatorio
    reminder_type = Column(String(20), default='photo_verify')  # 'photo_verify' o 'simple'
    
    # Relaciones
    user = relationship("User", back_populates="reminders")
    alert_logs = relationship("AlertLog", back_populates="reminder", cascade="all, delete-orphan")
    
    @property
    def reminder_id(self):
        user_telegram = self.user.telegram_id if self.user else "unknown"
        return f"{self.chat_id}_{user_telegram}_{self.keyword}"
    
    @property
    def photos_missing(self):
        return max(0, self.photos_required - self.photos_received)
    
    @property
    def is_completed(self):
        if self.reminder_type == 'simple':
            return not self.active
        return self.photos_received >= self.photos_required
    
    def should_alert(self, current_time: datetime) -> bool:
        if not self.active:
            return False
        if self.last_alert is None:
            return True
        minutes_passed = (current_time - self.last_alert).total_seconds() / 60
        return minutes_passed >= self.frequency_minutes
    
    def add_photo(self) -> bool:
        if self.reminder_type == 'simple':
            return False
        self.photos_received += 1
        self.updated_at = datetime.now()
        if self.photos_received >= self.photos_required:
            self.active = False
            return True
        return False
    
    def mark_alert_sent(self):
        self.last_alert = datetime.now()
        self.updated_at = datetime.now()
    
    def to_dict(self) -> dict:
        return {
            'id': self.reminder_id,
            'user_id': self.user.telegram_id if self.user else None,
            'chat_id': int(self.chat_id) if self.chat_id.isdigit() else self.chat_id,
            'active': self.active,
            'frequency_minutes': self.frequency_minutes,
            'message': self.message,
            'keyword': self.keyword,
            'photos_received': self.photos_received,
            'reminder_type': self.reminder_type,
            'last_alert': self.last_alert.isoformat() if self.last_alert else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f"ReminderDB(id={self.id}, keyword={self.keyword}, type={self.reminder_type}, active={self.active})"


class AlertLog(Base):
    """Modelo para registrar alertas enviadas"""
    __tablename__ = 'alert_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey('reminders.id'), nullable=False)
    sent_at = Column(DateTime, default=datetime.now)
    status = Column(String(20), default='sent')
    error_message = Column(Text, nullable=True)
    
    reminder = relationship("ReminderDB", back_populates="alert_logs")
    
    def __repr__(self):
        return f"AlertLog(id={self.id}, reminder_id={self.reminder_id})"


class PhotoLog(Base):
    """Modelo para registrar fotos recibidas"""
    __tablename__ = 'photo_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    reminder_id = Column(Integer, ForeignKey('reminders.id'), nullable=False)
    user_telegram_id = Column(String(50), nullable=False)
    chat_id = Column(String(50), nullable=False)
    caption = Column(Text, nullable=True)
    keyword_matched = Column(Boolean, default=False)
    photo_number = Column(Integer, nullable=False)
    received_at = Column(DateTime, default=datetime.now)
    
    def __repr__(self):
        return f"PhotoLog(id={self.id}, reminder_id={self.reminder_id}, photo_number={self.photo_number})"


# Configuración de la base de datos
DATABASE_URL = f"sqlite:///{Config.DB_FILE}"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
    echo=False,
    poolclass=NullPool
)

SessionLocal = sessionmaker(
    autocommit=False, 
    autoflush=False, 
    bind=engine,
    expire_on_commit=False
)

def init_db():
    """Inicializa la base de datos creando todas las tablas"""
    Config.DATA_DIR.mkdir(exist_ok=True, parents=True)
    Base.metadata.create_all(bind=engine)
    print(f"✅ Base de datos inicializada en: {Config.DB_FILE}")

def get_db():
    """Obtiene una sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()