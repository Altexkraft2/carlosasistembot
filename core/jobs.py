"""
Tareas programadas del bot.
Con logs de depuración.
"""

from datetime import datetime
from telegram.ext import ContextTypes
from services.alert_service_db import AlertServiceDB
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)
_job_configured = False

async def check_reminders_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que verifica y envía alertas periódicamente"""
    logger.info("⏰ === INICIANDO VERIFICACIÓN DE ALERTAS ===")
    
    alert_service: AlertServiceDB = context.bot_data.get('alert_service')
    
    if not alert_service:
        logger.error("❌ AlertService no encontrado en bot_data")
        logger.error(f"   bot_data keys: {list(context.bot_data.keys())}")
        return
    
    try:
        alerts_sent = await alert_service.check_and_send_alerts()
        logger.info(f"⏰ === VERIFICACIÓN COMPLETADA: {alerts_sent} alertas enviadas ===")
    except Exception as e:
        logger.error(f"❌ Error en job de verificación: {e}", exc_info=True)

async def heartbeat_job(context: ContextTypes.DEFAULT_TYPE):
    """Job de heartbeat para verificar que el bot sigue vivo"""
    now = datetime.now()
    reminder_service = context.bot_data.get('reminder_service')
    
    if reminder_service:
        try:
            active_count = reminder_service.repository.count_active()
            logger.info(f"💓 Heartbeat: {now.strftime('%H:%M:%S')} | Recordatorios activos: {active_count}")
        except Exception as e:
            logger.error(f"❌ Error en heartbeat: {e}")
            logger.info(f"💓 Heartbeat: {now.strftime('%H:%M:%S')} | Error obteniendo activos")
    else:
        logger.warning(f"💓 Heartbeat: {now.strftime('%H:%M:%S')} | ReminderService no disponible")

def setup_jobs(bot_app):
    """Configura los jobs programados"""
    global _job_configured
    
    if _job_configured:
        logger.warning("⚠️ Jobs ya configurados, omitiendo...")
        return
    
    app = bot_app.get_app()
    job_queue = app.job_queue
    
    if not job_queue:
        logger.error("❌ JobQueue no disponible")
        return
    
    reminder_service = bot_app.reminder_service
    
    # Crear y configurar servicio de alertas
    alert_service = AlertServiceDB(reminder_service)
    alert_service.set_bot(app.bot)
    
    # Guardar en bot_data para acceso desde handlers
    app.bot_data['alert_service'] = alert_service
    logger.info("✅ AlertService guardado en bot_data")
    
    # Job principal de verificación de recordatorios
    job_queue.run_repeating(
        check_reminders_job,
        interval=Config.CHECK_INTERVAL_SECONDS,
        first=10,
        name="check_reminders"
    )
    logger.info(f"✅ Job 'check_reminders' configurado (cada {Config.CHECK_INTERVAL_SECONDS}s)")
    
    # Job de heartbeat
    job_queue.run_repeating(
        heartbeat_job,
        interval=3600,
        first=60,
        name="heartbeat"
    )
    logger.info("✅ Job 'heartbeat' configurado (cada hora)")
    
    _job_configured = True
    logger.info(f"📋 Total jobs configurados: 2")