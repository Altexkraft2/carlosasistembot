"""Handlers administrativos para grupos"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from services.reminder_service_db import ReminderServiceDB
from utils.logger import setup_logger
from config import Config
from utils.validators import format_frequency

logger = setup_logger(__name__)

def escape_markdown(text: str) -> str:
    if not text: return text
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def grupo_estado_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("ℹ️ Este comando solo está disponible en grupos.")
        return
    
    reminder_service: ReminderServiceDB = context.bot_data.get('reminder_service')
    if not reminder_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    reminders = reminder_service.get_chat_reminders(chat_id)
    
    if not reminders:
        await update.message.reply_text("📊 No hay recordatorios activos en este grupo.")
        return
    
    by_user = {}
    for r in reminders:
        owner_id = r.user.telegram_id if r.user else "desconocido"
        if owner_id not in by_user:
            by_user[owner_id] = []
        by_user[owner_id].append(r)
    
    message = f"📊 *RECORDATORIOS ACTIVOS*\nTotal: {len(reminders)}\n\n"
    for uid, user_reminders in by_user.items():
        message += f"*Usuario {uid[-4:]}*\n"
        for r in user_reminders:
            escaped_keyword = escape_markdown(r.keyword)
            freq_display = format_frequency(r.frequency_minutes)
            tipo = "📸" if r.reminder_type == 'photo_verify' else "📝"
            message += f"  {tipo} `{escaped_keyword}` - {r.photos_received}/{r.photos_required} 📸 - cada {freq_display}\n"
        message += "\n"
    
    await update.message.reply_text(message, parse_mode='Markdown')
    logger.info(f"📊 /grupo_estado en chat {chat_id}")

async def limpiar_grupo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if update.effective_chat.type == "private":
        await update.message.reply_text("ℹ️ Este comando solo está disponible en grupos.")
        return
    
    chat_member = await context.bot.get_chat_member(chat_id, user.id)
    if chat_member.status not in ["administrator", "creator"]:
        await update.message.reply_text("❌ Solo los administradores pueden usar este comando.")
        return
    
    reminder_service: ReminderServiceDB = context.bot_data.get('reminder_service')
    if not reminder_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    reminders = reminder_service.get_chat_reminders(chat_id)
    count = len(reminders)
    
    for reminder in reminders:
        reminder.active = False
        reminder_service.repository.save(
            reminder, 
            reminder.user.telegram_id if reminder.user else "unknown"
        )
    
    await update.message.reply_text(f"✅ {count} recordatorios cancelados.")
    logger.info(f"🧹 /limpiar_grupo en chat {chat_id} por admin {user.id}")

def get_grupo_estado_handler(): return CommandHandler("grupo_estado", grupo_estado_command)
def get_limpiar_grupo_handler(): return CommandHandler("limpiar_grupo", limpiar_grupo_command)