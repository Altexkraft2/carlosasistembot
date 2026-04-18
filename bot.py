#!/usr/bin/env python3
"""Bot de Telegram para recordatorios con verificación por fotos."""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.bot_app import bot_app
from core.jobs import setup_jobs
from handlers import (
    get_start_handler, get_help_handler, get_about_handler, get_horario_handler,
    get_programar_handler, get_estado_handler, get_cancelar_handler,
    get_photo_handler, get_callback_handler,
    get_grupo_estado_handler, get_limpiar_grupo_handler
)
from utils.logger import setup_logger

logger = setup_logger(__name__)

def register_handlers():
    app = bot_app.get_app()
    logger.info("📋 Registrando handlers...")
    
    app.add_handler(get_start_handler())
    app.add_handler(get_help_handler())
    app.add_handler(get_about_handler())
    app.add_handler(get_horario_handler())
    app.add_handler(get_programar_handler())
    app.add_handler(get_estado_handler())
    app.add_handler(get_cancelar_handler())
    app.add_handler(get_photo_handler())
    app.add_handler(get_callback_handler())
    app.add_handler(get_grupo_estado_handler())
    app.add_handler(get_limpiar_grupo_handler())
    
    logger.info(f"📋 11 handlers registrados")

async def main():
    print("\n" + "=" * 50)
    print("🤖 INICIANDO BOT DE RECORDATORIOS v2.0")
    print("=" * 50 + "\n")
    
    try:
        register_handlers()
        setup_jobs(bot_app)
        await bot_app.run()
    except KeyboardInterrupt:
        logger.info("👋 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())