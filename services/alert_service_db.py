"""
Servicio de alertas con SQLAlchemy.
Con logs de depuración detallados.
"""

from datetime import datetime
from database.models import ReminderDB
from services.reminder_service_db import ReminderServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config

logger = setup_logger(__name__)

class AlertServiceDB:
    """Servicio para manejar alertas periódicas con SQLite"""
    
    def __init__(self, reminder_service: ReminderServiceDB = None):
        self.reminder_service = reminder_service or ReminderServiceDB()
        self.bot = None
        logger.info("🔔 Servicio de alertas (DB) inicializado")
    
    def set_bot(self, bot):
        self.bot = bot
        logger.info("🤖 Bot vinculado al servicio de alertas")
    
    async def check_and_send_alerts(self) -> int:
        """Verifica y envía alertas a todos los recordatorios activos"""
        if not self.bot:
            logger.warning("⚠️ Bot no configurado para enviar alertas")
            return 0
        
        now = datetime.now()
        logger.debug(f"🕐 Verificando alertas a las {now.strftime('%H:%M:%S')}")
        
        # Verificar horario laboral
        if not Config.is_work_time(now):
            logger.debug(f"⏸️ Fuera de horario laboral: {now.strftime('%H:%M')}")
            return 0
        
        # Obtener recordatorios activos
        try:
            active = self.reminder_service.get_all_active_reminders()
            logger.info(f"🔍 Recordatorios activos encontrados: {len(active)}")
            
            # Mostrar detalles de cada recordatorio activo
            for r in active:
                user_info = r.user.telegram_id if r.user else "desconocido"
                logger.info(f"  📝 ID:{r.id} | keyword:'{r.keyword}' | chat_id:{r.chat_id} | user:{user_info} | fotos:{r.photos_received}/{r.photos_required} | freq:{r.frequency_minutes}min | last_alert:{r.last_alert}")
                
        except Exception as e:
            logger.error(f"❌ Error obteniendo recordatorios activos: {e}", exc_info=True)
            return 0
        
        if not active:
            logger.info("ℹ️ No hay recordatorios activos para verificar")
            return 0
        
        sent = 0
        for reminder in active:
            try:
                should_alert = reminder.should_alert(now)
                logger.debug(f"  ⏰ '{reminder.keyword}': should_alert={should_alert}, last_alert={reminder.last_alert}, freq={reminder.frequency_minutes}min")
                
                if should_alert:
                    logger.info(f"📨 Intentando enviar alerta para '{reminder.keyword}' al chat {reminder.chat_id}")
                    success = await self._send_alert(reminder)
                    
                    if success:
                        reminder.mark_alert_sent()
                        try:
                            self.reminder_service.repository.save(
                                reminder,
                                reminder.user.telegram_id if reminder.user else "unknown"
                            )
                            self.reminder_service.repository.log_alert(reminder.id, 'sent')
                            sent += 1
                            logger.info(f"  ✅ Alerta enviada y guardada para chat {reminder.chat_id}")
                        except Exception as e:
                            logger.error(f"  ❌ Error guardando alerta: {e}")
                    else:
                        logger.warning(f"  ❌ Falló el envío de alerta al chat {reminder.chat_id}")
                        
            except Exception as e:
                logger.error(f"❌ Error procesando alerta para '{reminder.keyword}': {e}", exc_info=True)
                try:
                    self.reminder_service.repository.log_alert(
                        reminder.id, 'error', str(e)[:500]
                    )
                except:
                    pass
        
        if sent > 0:
            logger.info(f"📨 Total de alertas enviadas en esta ronda: {sent}")
        else:
            logger.debug("📭 No se enviaron alertas en esta ronda")
        
        return sent
    
    async def _send_alert(self, reminder: ReminderDB) -> bool:
        """Envía una alerta al chat correspondiente"""
        try:
            remaining = max(0, Config.PHOTOS_REQUIRED - reminder.photos_received)
            message = (
                f"{reminder.message}\n\n"
                f"⚠️ Faltan {remaining} foto(s) con `{reminder.keyword}` para detener las alertas.\n"
                f"📸 Envía las fotos con la palabra clave en el pie de foto."
            )
            
            # Convertir chat_id a entero si es posible
            chat_id = reminder.chat_id
            if isinstance(chat_id, str) and chat_id.lstrip('-').isdigit():
                chat_id = int(chat_id)
            
            logger.debug(f"  📤 Enviando mensaje a chat_id={chat_id} (tipo: {type(chat_id).__name__})")
            
            await self.bot.send_message(
                chat_id=chat_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=inline_keyboards.get_alert_keyboard()
            )
            logger.debug(f"  ✅ Mensaje enviado exitosamente a {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"  ❌ Error enviando mensaje al chat {reminder.chat_id}: {e}")
            return False