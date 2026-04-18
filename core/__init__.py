"""
Módulo core del bot.
Contiene la aplicación principal y jobs programados.
"""

from core.bot_app import bot_app
from core.jobs import setup_jobs

__all__ = ['bot_app', 'setup_jobs']