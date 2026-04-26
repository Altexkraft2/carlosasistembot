"""Handlers de recordatorios"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from services.reminder_service_db import ReminderServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config
from datetime import datetime
from utils.validators import parse_frequency, format_frequency
from database.models import ReminderDB

logger = setup_logger(__name__)

def escape_markdown(text: str) -> str:
    if not text: return text
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def programar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /programar - Recordatorio con verificación de fotos"""
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    
    reminder_service: ReminderServiceDB = context.bot_data.get('reminder_service')
    if not reminder_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "📝 *Uso:* `/programar [frecuencia] [palabra] [mensaje]`\n\n"
            "*Frecuencias:*\n"
            "• `5min`, `30min` → minutos\n"
            "• `1h`, `2h` → horas\n"
            "• `1:30`, `0:45` → horas:minutos\n"
            "• `diario`, `24h` → cada 24 horas\n\n"
            "*Ejemplos:*\n"
            "`/programar 5min MEDICINA Tomar pastilla`\n"
            "`/programar 1h REUNION Reunión`\n"
            "`/programar diario REPORTE Enviar reporte`",
            parse_mode='Markdown'
        )
        return
    
    frequency = Config.DEFAULT_FREQUENCY_MINUTES
    keyword = "RECORDATORIO"
    message = None
    
    if args:
        try:
            frequency = parse_frequency(args[0])
            if len(args) > 1:
                keyword = args[1].strip()
                if len(args) > 2:
                    message = ' '.join(args[2:])
        except ValueError as e:
            keyword = args[0].strip()
            if len(args) > 1:
                message = ' '.join(args[1:])
    
    if not message:
        message = f"⏰ ¡Es hora de tu recordatorio! Envía 2 fotos con '{keyword}'"
    
    try:
        reminder = reminder_service.create_reminder(
            user_telegram_id=user_id,
            chat_id=chat_id,
            frequency=frequency,
            message=message,
            keyword=keyword,
            username=user.username,
            first_name=user.first_name
        )
        
        escaped_keyword = escape_markdown(keyword)
        freq_display = format_frequency(frequency)
        
        await update.message.reply_text(
            f"✅ *¡Recordatorio activado!*\n\n"
            f"🔄 Frecuencia: cada {freq_display}\n"
            f"🔑 Palabra clave: `{escaped_keyword}`\n"
            f"📝 Mensaje: {message}\n\n"
            f"📸 Envía 2 fotos con `{escaped_keyword}` para detenerlo.",
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_reminder_actions_keyboard(user_id)
        )
        logger.info(f"✅ Recordatorio creado: {reminder.reminder_id}")
        
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def recordar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /recordar - Recordatorio simple sin verificación de fotos"""
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    
    replied_message = update.message.reply_to_message
    if not replied_message:
        await update.message.reply_text(
            "📝 *Uso:* Responde a un mensaje y escribe `/recordar [frecuencia] [palabra]`\n\n"
            "*Ejemplos:*\n"
            "`/recordar 24h IMPORTANTE`\n"
            "`/recordar diario REPORTE`\n\n"
            "El bot repetirá ese mensaje hasta que lo canceles con `/cancelar PALABRA`.",
            parse_mode='Markdown'
        )
        return
    
    reminder_service: ReminderServiceDB = context.bot_data.get('reminder_service')
    if not reminder_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "❌ Necesitas al menos la palabra clave.\n"
            "Ejemplo: `/recordar 24h IMPORTANTE`",
            parse_mode='Markdown'
        )
        return
    
    frequency = Config.DEFAULT_FREQUENCY_MINUTES
    keyword = "RECORDATORIO"
    
    try:
        frequency = parse_frequency(args[0])
        if len(args) > 1:
            keyword = args[1].strip()
    except ValueError:
        keyword = args[0].strip()
    
    # Datos del mensaje original
    original_type = 'text'
    original_file_id = None
    original_caption = replied_message.caption or ""
    original_text = replied_message.text or replied_message.caption or ""
    
    if replied_message.photo:
        original_type = 'photo'
        original_file_id = replied_message.photo[-1].file_id
    elif replied_message.video:
        original_type = 'video'
        original_file_id = replied_message.video.file_id
    elif replied_message.document:
        original_type = 'document'
        original_file_id = replied_message.document.file_id
    elif replied_message.audio:
        original_type = 'audio'
        original_file_id = replied_message.audio.file_id
    elif replied_message.voice:
        original_type = 'voice'
        original_file_id = replied_message.voice.file_id
    
    record_message = original_text[:500] if original_text else f"Recordatorio: {keyword}"
    
    try:
        reminder = ReminderDB(
            chat_id=str(chat_id),
            keyword=keyword.upper(),
            message=record_message,
            frequency_minutes=frequency,
            active=True,
            photos_received=0,
            photos_required=0,
            reminder_type='simple',
            original_message_id=replied_message.message_id,
            original_message_type=original_type,
            original_caption=original_caption,
            original_file_id=original_file_id
        )
        
        saved = reminder_service.repository.save(reminder, user_id, user.username, user.first_name)
        
        escaped_keyword = escape_markdown(keyword)
        freq_display = format_frequency(frequency)
        
        await update.message.reply_text(
            f"✅ *¡Recordatorio simple creado!*\n\n"
            f"🔄 Frecuencia: cada {freq_display}\n"
            f"🔑 Palabra clave: `{escaped_keyword}`\n"
            f"📝 Contenido: {record_message[:100]}\n\n"
            f"❌ Para detenerlo: `/cancelar {escaped_keyword}`",
            parse_mode='Markdown'
        )
        logger.info(f"✅ Recordatorio simple creado: {saved.reminder_id}")
        
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /estado - Muestra el estado de los recordatorios"""
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    args = context.args
    
    reminder_service: ReminderServiceDB = context.bot_data.get('reminder_service')
    if not reminder_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    if args:
        keyword = args[0].strip()
        status = reminder_service.get_reminder_status(user_id, chat_id, keyword)
        if not status:
            await update.message.reply_text(f"ℹ️ No hay recordatorio con palabra '{keyword}'.")
            return
        
        estado_emoji = "🟢 ACTIVO" if status['active'] else "🔴 INACTIVO"
        escaped_keyword = escape_markdown(keyword)
        freq_display = format_frequency(status['frequency'])
        tipo = "📸 Verificación por fotos" if status.get('reminder_type', 'photo_verify') == 'photo_verify' else "📝 Simple (sin fotos)"
        
        status_message = (
            f"📊 *Estado: {escaped_keyword}*\n\n"
            f"{estado_emoji} | {tipo}\n"
            f"📝 {status['message']}\n"
            f"🔄 Frecuencia: cada {freq_display}\n"
            f"📸 Fotos: {status['photos_received']}/{status['photos_required']}\n"
            f"⚠️ Faltan: {status['photos_missing']} foto(s)"
        )
        await update.message.reply_text(status_message, parse_mode='Markdown')
    else:
        reminders = reminder_service.get_user_reminders(user_id, chat_id)
        if not reminders:
            await update.message.reply_text("ℹ️ No tienes recordatorios activos.")
            return
        
        message = "📊 *TUS RECORDATORIOS ACTIVOS*\n\n"
        for r in reminders:
            escaped_keyword = escape_markdown(r.keyword)
            tipo = "📸" if r.reminder_type == 'photo_verify' else "📝"
            message += f"{tipo} `{escaped_keyword}` - {r.photos_received}/{r.photos_required} 📸\n"
        message += "\nUsa `/estado [palabra]` para ver detalles."
        await update.message.reply_text(message, parse_mode='Markdown')

async def cancelar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Comando /cancelar - Cancela recordatorios"""
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    args = context.args
    
    reminder_service: ReminderServiceDB = context.bot_data.get('reminder_service')
    if not reminder_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    keyword = args[0].strip() if args else None
    cancelled = reminder_service.cancel_reminder(user_id, chat_id, keyword)
    
    if cancelled:
        if keyword:
            await update.message.reply_text(f"✅ Recordatorio '{keyword}' cancelado.")
        else:
            await update.message.reply_text("✅ Todos tus recordatorios cancelados.")
    else:
        await update.message.reply_text("ℹ️ No se encontraron recordatorios para cancelar.")

def get_programar_handler(): return CommandHandler("programar", programar_command)
def get_recordar_handler(): return CommandHandler("recordar", recordar_command)
def get_estado_handler(): return CommandHandler("estado", estado_command)
def get_cancelar_handler(): return CommandHandler("cancelar", cancelar_command)