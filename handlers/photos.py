"""Handler de fotos - Soporta álbumes"""

from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters
from services.photo_service_db import PhotoServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger

logger = setup_logger(__name__)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa fotos individuales y álbumes"""
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    caption = update.message.caption or ""
    media_group_id = update.message.media_group_id

    if media_group_id:
        logger.info(f"📸 Foto de álbum: media_group={media_group_id}, caption='{caption[:30] if caption else '(vacío)'}'")
        album_key = f"album_{media_group_id}"

        if caption:
            context.user_data[album_key] = {'caption': caption, 'photos_processed': 0}
            logger.debug(f"📝 Caption guardado: '{caption}'")

        album_data = context.user_data.get(album_key, {})
        effective_caption = caption if caption else album_data.get('caption', '')

        if not effective_caption:
            return

        album_data['photos_processed'] = album_data.get('photos_processed', 0) + 1
        context.user_data[album_key] = album_data

        await _process_album_photo(update, context, user_id, chat_id, effective_caption, user, media_group_id, album_data['photos_processed'])
    else:
        logger.info(f"📸 Foto individual: '{caption[:50]}'")
        await _process_single_photo(update, context, user_id, chat_id, caption, user)

async def _process_single_photo(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                user_id: str, chat_id: int, caption: str, user):
    """Procesa una foto individual"""
    photo_service: PhotoServiceDB = context.bot_data.get('photo_service')
    if not photo_service:
        await update.message.reply_text("❌ Error interno.")
        return

    result = photo_service.process_photo(
        user_telegram_id=user_id, chat_id=chat_id, caption=caption,
        username=user.username, first_name=user.first_name
    )
    await _send_result(update, result, user_id)

async def _process_album_photo(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               user_id: str, chat_id: int, caption: str, user,
                               media_group_id: str, photo_number: int):
    """Procesa una foto de álbum"""
    photo_service: PhotoServiceDB = context.bot_data.get('photo_service')
    if not photo_service:
        await update.message.reply_text("❌ Error interno.")
        return

    result = photo_service.process_photo(
        user_telegram_id=user_id, chat_id=chat_id, caption=caption,
        username=user.username, first_name=user.first_name
    )

    if result.get('completed'):
        await update.message.reply_text(result['message'])
    elif result.get('success') and photo_number == 1:
        remaining = result.get('remaining', 0)
        keyword = result.get('keyword', '')
        await update.message.reply_text(
            f"📸 ¡Primera foto del álbum recibida!\n"
            f"🔑 Palabra clave: `{keyword}`\n"
            f"⚠️ Faltan {remaining} foto(s) más.\n\n"
            f"📸 Las demás fotos se procesarán automáticamente.",
            parse_mode='Markdown'
        )

async def _send_result(update: Update, result: dict, user_id: str):
    """Envía el resultado del procesamiento de fotos"""
    if result.get('completed'):
        await update.message.reply_text(result['message'])
    elif result.get('success'):
        keyboard = inline_keyboards.get_photo_progress_keyboard(
            result.get('photos_received', 0),
            result.get('photos_required', 2)
        )
        await update.message.reply_text(result['message'], parse_mode='Markdown', reply_markup=keyboard)
    else:
        await update.message.reply_text(result['message'])

def get_photo_handler():
    return MessageHandler(filters.PHOTO, photo_handler)