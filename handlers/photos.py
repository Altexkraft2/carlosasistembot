"""Handler de fotos"""

from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters
from services.photo_service import PhotoService
from keyboards import inline_keyboards
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    chat_id = update.effective_chat.id
    caption = update.message.caption or ""
    
    logger.info(f"📸 Foto recibida en chat {chat_id}: '{caption[:50]}'")
    
    photo_service: PhotoService = context.bot_data.get('photo_service')
    if not photo_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    result = photo_service.process_photo(user_id, chat_id, caption)
    
    if result.get('completed'):
        await update.message.reply_text(result['message'])
    elif result.get('success'):
        await update.message.reply_text(result['message'], parse_mode='Markdown')
    else:
        await update.message.reply_text(result['message'])

def get_photo_handler(): return MessageHandler(filters.PHOTO, photo_handler)