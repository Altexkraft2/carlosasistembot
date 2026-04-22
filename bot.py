#!/usr/bin/env python3
"""
Bot de Telegram para recordatorios con verificación por fotos.
Versión final con health check para Render.
"""

import sys
import asyncio
import os
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.bot_app import bot_app
from core.jobs import setup_jobs
from handlers import (
    get_start_handler,
    get_help_handler,
    get_about_handler,
    get_horario_handler,
    get_programar_handler,
    get_estado_handler,
    get_cancelar_handler,
    get_photo_handler,
    get_callback_handler,
    get_grupo_estado_handler,
    get_limpiar_grupo_handler
)
from utils.logger import setup_logger
from aiohttp import web

logger = setup_logger(__name__)

# ========== HEALTH CHECK PARA RENDER ==========
async def health_check(request):
    """Endpoint de health check para Render y UptimeRobot"""
    return web.Response(text="OK")

async def run_web_server():
    """Inicia un servidor web para el health check de Render"""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    
    port = int(os.environ.get('PORT', 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"✅ Servidor web iniciado en puerto {port}")
    print(f"✅ Health check disponible en: http://0.0.0.0:{port}/health")
# =============================================

def register_handlers():
    """Registra todos los manejadores de eventos"""
    app = bot_app.get_app()
    
    logger.info("📋 Registrando handlers...")
    
    # Comandos básicos
    app.add_handler(get_start_handler())
    app.add_handler(get_help_handler())
    app.add_handler(get_about_handler())
    app.add_handler(get_horario_handler())
    logger.info("  ✅ Handlers básicos (4)")
    
    # Comandos de recordatorios
    app.add_handler(get_programar_handler())
    app.add_handler(get_estado_handler())
    app.add_handler(get_cancelar_handler())
    logger.info("  ✅ Handlers de recordatorios (3)")
    
    # Handlers de interacción
    app.add_handler(get_photo_handler())
    app.add_handler(get_callback_handler())
    logger.info("  ✅ Handlers de interacción (2)")
    
    # Comandos administrativos
    app.add_handler(get_grupo_estado_handler())
    app.add_handler(get_limpiar_grupo_handler())
    logger.info("  ✅ Handlers administrativos (2)")
    
    logger.info(f"📋 Total: 11 handlers registrados")

async def main():
    """Función principal asíncrona"""
    print("\n" + "=" * 50)
    print("🤖 INICIANDO BOT DE RECORDATORIOS v2.0")
    print("=" * 50 + "\n")
    
    try:
        # 1. Registrar handlers
        register_handlers()
        
        # 2. Configurar jobs programados
        setup_jobs(bot_app)
        
        # 3. Iniciar servidor web para Render (health check)
        if os.environ.get('PORT'):
            await run_web_server()
        
        # 4. Iniciar el bot
        await bot_app.run()
        
    except KeyboardInterrupt:
        logger.info("👋 Bot detenido por el usuario")
    except Exception as e:
        logger.error(f"❌ Error fatal: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())