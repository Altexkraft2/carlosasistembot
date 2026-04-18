"""
Núcleo de la aplicación del bot.
Compatible con PTB 21.x y Python 3.13
"""

from telegram.ext import Application
from config import Config
from database.repository import ReminderRepository
from services.reminder_service import ReminderService
from services.photo_service import PhotoService
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BotApp:
    """Clase principal de la aplicación del bot"""
    
    def __init__(self):
        logger.info("🤖 Inicializando BotApp...")
        
        # Crear aplicación (PTB 21.x)
        self.app = Application.builder().token(Config.BOT_TOKEN).build()
        logger.info("✅ Aplicación de Telegram creada")
        
        # Inicializar repositorio
        self.repository = ReminderRepository()
        logger.info("✅ Repositorio inicializado")
        
        # Inicializar servicios
        self.reminder_service = ReminderService(self.repository)
        logger.info("✅ Servicio de recordatorios inicializado")
        
        self.photo_service = PhotoService(self.repository)
        logger.info("✅ Servicio de fotos inicializado")
        
        # Guardar en bot_data
        self.app.bot_data['reminder_service'] = self.reminder_service
        self.app.bot_data['photo_service'] = self.photo_service
        
        stats = self.reminder_service.get_stats()
        logger.info(f"📊 Estado inicial: {stats['activos']} recordatorios activos")
        logger.info("🎉 BotApp inicializada correctamente")
    
    def get_app(self):
        return self.app
    
    async def run(self):
        """Inicia el bot (async en PTB 21.x)"""
        logger.info("🚀 Iniciando bot...")
        logger.info("=" * 50)
        logger.info("🤖 BOT DE RECORDATORIOS CON FOTOS")
        logger.info("=" * 50)
        logger.info(f"📸 Fotos requeridas: {Config.PHOTOS_REQUIRED}")
        logger.info(f"🔄 Frecuencia: {Config.DEFAULT_FREQUENCY_MINUTES} min")
        logger.info("=" * 50)
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("✅ Bot está corriendo...")
        
        # Mantener el bot corriendo
        import asyncio
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("👋 Deteniendo bot...")
            await self.app.stop()

bot_app = BotApp()