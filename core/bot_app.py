"""
Núcleo de la aplicación del bot.
Con soporte para SQLite.
"""

from telegram.ext import Application
from config import Config
from database.repository_db import ReminderRepositoryDB
from services.reminder_service_db import ReminderServiceDB
from services.photo_service_db import PhotoServiceDB
from utils.logger import setup_logger

logger = setup_logger(__name__)

class BotApp:
    """Clase principal de la aplicación del bot"""
    
    def __init__(self):
        logger.info("🤖 Inicializando BotApp...")
        
        self.app = Application.builder().token(Config.BOT_TOKEN).build()
        logger.info("✅ Aplicación de Telegram creada")
        
        # Inicializar repositorio con SQLite
        self.repository = ReminderRepositoryDB()
        logger.info("✅ Repositorio SQLite inicializado")
        
        # Inicializar servicios
        self.reminder_service = ReminderServiceDB(self.repository)
        logger.info("✅ Servicio de recordatorios inicializado")
        
        self.photo_service = PhotoServiceDB(self.repository)
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
        logger.info("🚀 Iniciando bot...")
        logger.info("=" * 50)
        logger.info("🤖 BOT DE RECORDATORIOS v2.0 (SQLite)")
        logger.info("=" * 50)
        logger.info(f"📸 Fotos requeridas: {Config.PHOTOS_REQUIRED}")
        logger.info(f"🔄 Frecuencia: {Config.DEFAULT_FREQUENCY_MINUTES} min")
        logger.info(f"🗄️ Base de datos: {Config.DB_FILE}")
        logger.info("=" * 50)
        
        await self.app.initialize()
        await self.app.start()
        await self.app.updater.start_polling(drop_pending_updates=True)
        
        logger.info("✅ Bot está corriendo...")
        
        import asyncio
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            logger.info("👋 Deteniendo bot...")
            await self.app.stop()

bot_app = BotApp()