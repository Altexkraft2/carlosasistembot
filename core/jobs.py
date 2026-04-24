"""
Tareas programadas del bot.
"""

from datetime import datetime
from telegram.ext import ContextTypes
from services.alert_service_db import AlertServiceDB
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)
_job_configured = False

async def check_reminders_job(context: ContextTypes.DEFAULT_TYPE):
    """Job que verifica y envía alertas"""
    alert_service: AlertServiceDB = context.bot_data.get('alert_service')
    
    if not alert_service:
        logger.error("❌ AlertService no encontrado")
        return
    
    try:
        alerts_sent = await alert_service.check_and_send_alerts()
        if alerts_sent > 0:
            logger.info(f"📨 {alerts_sent} alertas enviadas")
    except Exception as e:
        logger.error(f"❌ Error en job: {e}")

async def heartbeat_job(context: ContextTypes.DEFAULT_TYPE):
    """Job de heartbeat"""
    now = datetime.now()
    reminder_service = context.bot_data.get('reminder_service')
    if reminder_service:
        try:
            active = reminder_service.repository.count_active()
        except:
            active = 0
    else:
        active = 0
    logger.info(f"💓 Heartbeat: {now.strftime('%H:%M')} | Activos: {active}")

def setup_jobs(bot_app):
    """Configura los jobs programados"""
    global _job_configured
    
    if _job_configured:
        return
    
    app = bot_app.get_app()
    job_queue = app.job_queue
    
    reminder_service = bot_app.reminder_service
    
    alert_service = AlertServiceDB(reminder_service)
    alert_service.set_bot(app.bot)
    
    app.bot_data['alert_service'] = alert_service
    
    job_queue.run_repeating(
        check_reminders_job,
        interval=Config.CHECK_INTERVAL_SECONDS,
        first=10,
        name="check_reminders"
    )
    logger.info(f"✅ Job configurado (cada {Config.CHECK_INTERVAL_SECONDS}s)")
    
    job_queue.run_repeating(
        heartbeat_job,
        interval=3600,
        first=60,
        name="heartbeat"
    )
    logger.info("✅ Job heartbeat configurado")
    
    _job_configured = True