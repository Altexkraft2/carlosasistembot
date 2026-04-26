"""Handler de fotos - Soporta álbumes correctamente"""

from telegram import Update
from telegram.ext import MessageHandler, ContextTypes, filters
from services.photo_service_db import PhotoServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config
from datetime import datetime

logger = setup_logger(__name__)

async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Procesa fotos individuales y álbumes.
    """
    user = update.effective_user
    user_id = str(user.id)
    chat_id = update.effective_chat.id
    caption = update.message.caption or ""
    media_group_id = update.message.media_group_id
    
    if media_group_id:
        # Es parte de un álbum
        logger.info(f"📸 Foto de álbum recibida: media_group={media_group_id}, caption='{caption[:30] if caption else '(vacío)'}'")
        
        # Clave para este álbum
        album_key = f"album_{media_group_id}"
        
        # Si esta foto tiene caption, lo guardamos para las demás fotos del álbum
        if caption:
            context.user_data[album_key] = {
                'caption': caption,
                'photos_processed': 0
            }
            logger.debug(f"📝 Caption guardado para álbum {media_group_id}: '{caption}'")
        
        # Obtener el caption guardado (si esta foto no tiene, usamos el guardado)
        album_data = context.user_data.get(album_key, {})
        effective_caption = caption if caption else album_data.get('caption', '')
        
        if not effective_caption:
            logger.warning(f"⚠️ Álbum sin caption en ninguna foto")
            await update.message.reply_text("❌ El álbum no tiene pie de foto. Añade la palabra clave.")
            return
        
        # Incrementar contador de fotos procesadas
        album_data['photos_processed'] = album_data.get('photos_processed', 0) + 1
        context.user_data[album_key] = album_data
        
        # Procesar la foto con el caption efectivo
        await _process_album_photo(
            update, context, user_id, chat_id, effective_caption, 
            user, media_group_id, album_data['photos_processed']
        )
    else:
        # Foto individual
        logger.info(f"📸 Foto individual recibida: '{caption[:50]}'")
        await _process_single_photo(update, context, user_id, chat_id, caption, user)

async def _process_single_photo(update: Update, context: ContextTypes.DEFAULT_TYPE,
                                user_id: str, chat_id: int, caption: str, user):
    """Procesa una foto individual"""
    photo_service: PhotoServiceDB = context.bot_data.get('photo_service')
    
    if not photo_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    result = photo_service.process_photo(
        user_telegram_id=user_id,
        chat_id=chat_id,
        caption=caption,
        username=user.username,
        first_name=user.first_name
    )
    
    await _send_result(update, result, user_id)

async def _process_album_photo(update: Update, context: ContextTypes.DEFAULT_TYPE,
                               user_id: str, chat_id: int, caption: str, user,
                               media_group_id: str, photo_number: int):
    """
    Procesa una foto que es parte de un álbum.
    Si es la última foto del álbum, completamos el recordatorio si corresponde.
    """
    photo_service: PhotoServiceDB = context.bot_data.get('photo_service')
    
    if not photo_service:
        await update.message.reply_text("❌ Error interno.")
        return
    
    caption_upper = caption.strip().upper()
    active_reminders = photo_service.repository.find_active_by_chat(chat_id)
    
    matching_reminder = None
    for reminder in active_reminders:
        if reminder.keyword in caption_upper:
            matching_reminder = reminder
            break
    
    if not matching_reminder:
        # Solo mostramos error en la primera foto para no spamear
        if photo_number == 1:
            await update.message.reply_text('ℹ️ No se encontró ningún recordatorio activo con esa palabra clave.')
        return
    
    reminder_owner = matching_reminder.user.telegram_id if matching_reminder.user else None
    
    # Verificar cuántas fotos faltan
    photos_needed = Config.PHOTOS_REQUIRED - matching_reminder.photos_received
    
    if photos_needed <= 0:
        # Ya está completado
        if photo_number == 1:
            await update.message.reply_text(f"✅ El recordatorio '{matching_reminder.keyword}' ya está completado.")
        return
    
    # Añadir UNA foto (cada llamada a este método cuenta como 1 foto)
    completed = matching_reminder.add_photo()
    
    # Guardar en base de datos
    photo_service.repository.save(
        matching_reminder,
        reminder_owner or user_id,
        user.username,
        user.first_name
    )
    
    # Registrar en PhotoLog
    photo_service.repository.log_photo(
        reminder_id=matching_reminder.id,
        user_telegram_id=user_id,
        chat_id=chat_id,
        caption=caption,
        keyword_matched=True,
        photo_number=matching_reminder.photos_received
    )
    
    logger.info(f"📸 Álbum - Foto {matching_reminder.photos_received}/{Config.PHOTOS_REQUIRED} para '{matching_reminder.keyword}'")
    
    # Solo responder en la primera foto o cuando se complete
    if completed:
        # ¡Completado!
        await update.message.reply_text(
            f"📸 ¡Álbum recibido! Has completado las {Config.PHOTOS_REQUIRED} fotos requeridas.\n"
            f"✅ Recordatorio '{matching_reminder.keyword}' completado.\n",
            parse_mode='Markdown'
        )
        
        # Limpiar datos del álbum
        album_key = f"album_{media_group_id}"
        if album_key in context.user_data:
            del context.user_data[album_key]
    elif photo_number == 1:
        # Primera foto del álbum - informar progreso
        remaining = Config.PHOTOS_REQUIRED - matching_reminder.photos_received
        await update.message.reply_text(
            f"📸 ¡Primera foto del álbum recibida!\n"
            f"🔑 Palabra clave: `{matching_reminder.keyword}`\n"
            f"⚠️ Faltan {remaining} foto(s) más para completar.\n\n"
            f"📸 Las demás fotos del álbum se procesarán automáticamente.",
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
        await update.message.reply_text(
            result['message'],
            parse_mode='Markdown',
            reply_markup=keyboard
        )
    else:
        await update.message.reply_text(result['message'])

def get_photo_handler():
    return MessageHandler(filters.PHOTO, photo_handler)