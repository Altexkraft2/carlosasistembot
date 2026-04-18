"""Handlers de recordatorios"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from services.reminder_service import ReminderService
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config
from datetime import datetime

logger = setup_logger(__name__)

def escape_markdown(text: str) -> str:
    if not text: return text
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def programar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    
    reminder_service: ReminderService = context.bot_data.get('reminder_service')
    if not reminder_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    args = context.args
    if not args:
        await update.message.reply_text(
            "📝 *Uso:* `/programar [frecuencia] [palabra] [mensaje]`\n\n"
            "*Ejemplos:*\n`/programar 5 MEDICINA Tomar pastilla`\n`/programar 10 REUNION`",
            parse_mode='Markdown'
        )
        return
    
    frequency = Config.DEFAULT_FREQUENCY_MINUTES
    keyword = "RECORDATORIO"
    message = None
    
    try:
        frequency = int(args[0])
        if len(args) > 1:
            keyword = args[1].strip()
            if len(args) > 2:
                message = ' '.join(args[2:])
    except ValueError:
        keyword = args[0].strip()
        if len(args) > 1:
            message = ' '.join(args[1:])
    
    if not message:
        message = f"⏰ ¡Es hora de tu recordatorio! Envía 2 fotos con '{keyword}'"
    
    try:
        reminder = reminder_service.create_reminder(
            user_id=user_id, chat_id=chat_id,
            frequency=frequency, message=message, keyword=keyword
        )
        
        escaped_keyword = escape_markdown(keyword)
        success_message = (
            f"✅ *¡Recordatorio activado!*\n\n"
            f"🔄 Frecuencia: cada {frequency} min\n"
            f"🔑 Palabra clave: `{escaped_keyword}`\n"
            f"📝 Mensaje: {message}\n\n"
            f"📸 Envía 2 fotos con `{escaped_keyword}` para detenerlo."
        )
        
        await update.message.reply_text(
            success_message, parse_mode='Markdown',
            reply_markup=inline_keyboards.get_reminder_actions_keyboard(user_id)
        )
        logger.info(f"✅ Recordatorio creado: {reminder.id}")
        
    except ValueError as e:
        await update.message.reply_text(f"❌ {str(e)}")

async def estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    args = context.args
    
    reminder_service: ReminderService = context.bot_data.get('reminder_service')
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
        status_message = (
            f"📊 *Estado: {escaped_keyword}*\n\n{estado_emoji}\n"
            f"📝 {status['message']}\n"
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
        for r in reminders.values():
            escaped_keyword = escape_markdown(r.keyword)
            message += f"🔑 `{escaped_keyword}` - {r.photos_received}/{Config.PHOTOS_REQUIRED} 📸\n"
        message += "\nUsa `/estado [palabra]` para ver detalles."
        await update.message.reply_text(message, parse_mode='Markdown')

async def cancelar_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    args = context.args
    
    reminder_service: ReminderService = context.bot_data.get('reminder_service')
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
def get_estado_handler(): return CommandHandler("estado", estado_command)
def get_cancelar_handler(): return CommandHandler("cancelar", cancelar_command)