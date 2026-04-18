"""
Sistema de logging para el bot.
Permite ver qué está haciendo el bot en tiempo real y guardar un historial.
"""

import logging
import sys
from pathlib import Path
from config import Config

def setup_logger(name: str = None) -> logging.Logger:
    """
    Configura y retorna un logger personalizado.
    
    Args:
        name: Nombre del logger (normalmente __name__ del módulo)
    
    Returns:
        Logger configurado
    """
    # Crear logger con el nombre proporcionado
    logger = logging.getLogger(name or __name__)
    
    # Evitar duplicar handlers si ya existe
    if logger.handlers:
        return logger
    
    # Nivel de logging desde la configuración
    logger.setLevel(getattr(logging, Config.LOG_LEVEL))
    
    # Formato de los mensajes de log
    # Formato: FECHA - NOMBRE - NIVEL - MENSAJE
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Handler 1: Mostrar en consola
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Handler 2: Guardar en archivo
    log_dir = Config.BASE_DIR / 'logs'
    log_dir.mkdir(exist_ok=True)  # Crear directorio si no existe
    
    file_handler = logging.FileHandler(
        log_dir / 'bot.log',
        encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

# Logger por defecto para uso general
logger = setup_logger('telegram_bot')