"""
Configuración central del bot.
Compatible con Render.
"""

import os
from pathlib import Path

class Config:
    """Configuración global del bot"""
    
    # Token del bot (desde variable de entorno en Render)
    BOT_TOKEN = os.environ.get('BOT_TOKEN')
    
    # Configuración de recordatorios
    CHECK_INTERVAL_SECONDS = int(os.environ.get('CHECK_INTERVAL_SECONDS', 60))
    DEFAULT_FREQUENCY_MINUTES = int(os.environ.get('DEFAULT_FREQUENCY_MINUTES', 5))
    PHOTOS_REQUIRED = int(os.environ.get('PHOTOS_REQUIRED', 2))
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    
    # Horario laboral
    WORK_HOURS = [
        {"start": "08:00", "end": "12:00"},
        {"start": "14:00", "end": "17:00"},
    ]
    WORK_DAYS = [0, 1, 2, 3, 4]  # Lunes a Viernes
    
    # Rutas - En Render usamos /tmp para datos persistentes
    BASE_DIR = Path(__file__).parent
    DATA_DIR = Path(os.environ.get('DATA_DIR', '/tmp/data'))
    DATA_FILE = DATA_DIR / 'recordatorios.json'
    
    @classmethod
    def is_work_time(cls, dt=None):
        from datetime import datetime
        if dt is None:
            dt = datetime.now()
        if dt.weekday() not in cls.WORK_DAYS:
            return False
        current_time = dt.strftime("%H:%M")
        for period in cls.WORK_HOURS:
            if period["start"] <= current_time < period["end"]:
                return True
        return False
    
    @classmethod
    def get_next_work_time(cls, dt=None):
        from datetime import datetime, timedelta
        if dt is None:
            dt = datetime.now()
        if cls.is_work_time(dt):
            return None
        current_time = dt.strftime("%H:%M")
        current_day = dt.weekday()
        for period in cls.WORK_HOURS:
            if current_time < period["start"] and current_day in cls.WORK_DAYS:
                return period["start"]
        days_to_add = 1
        next_day = (current_day + 1) % 7
        while next_day not in cls.WORK_DAYS:
            days_to_add += 1
            next_day = (next_day + 1) % 7
        next_date = dt + timedelta(days=days_to_add)
        return f"{next_date.strftime('%Y-%m-%d')} {cls.WORK_HOURS[0]['start']}"
    
    @classmethod
    def get_work_schedule_text(cls):
        days = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
        work_days_text = ", ".join([days[d] for d in cls.WORK_DAYS])
        periods_text = [f"{p['start']} - {p['end']}" for p in cls.WORK_HOURS]
        return f"📅 *Horario laboral:*\n{work_days_text}\n🕐 {', '.join(periods_text)}"
    
    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            print("⚠️ ADVERTENCIA: BOT_TOKEN no configurado. Configúralo en Render.")
        cls.DATA_DIR.mkdir(exist_ok=True, parents=True)
        print(f"✅ Directorio de datos: {cls.DATA_DIR}")

# Validar configuración
try:
    Config.validate()
except Exception as e:
    print(f"⚠️ {e}")