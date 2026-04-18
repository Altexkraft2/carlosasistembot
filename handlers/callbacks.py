"""Handler de callbacks"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from services.reminder_service import ReminderService
from keyboards import inline_keyboards
from utils.logger import setup_logger

logger = setup_logger(__name__)

def escape_markdown(text: str) -> str:
    if not text: return text
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    data = query.data
    logger.info(f"🔘 Callback: {data}")
    
    reminder_service: ReminderService = context.bot_data.get('reminder_service')
    
    if data == "menu_programar":
        await query.edit_message_text(
            "*Programar Recordatorio*\n\n`/programar [frecuencia] [palabra] [mensaje]`",
            parse_mode='Markdown', reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "menu_estado":
        await query.edit_message_text(
            "Usa `/estado` para ver tus recordatorios activos.",
            parse_mode='Markdown', reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "menu_ayuda":
        await query.edit_message_text(
            "*AYUDA*\n/programar - /estado - /cancelar - /horario",
            parse_mode='Markdown', reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "menu_acerca":
        await query.edit_message_text(
            "ℹ️ Bot v2.0 - Múltiples recordatorios",
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "menu_principal":
        await query.edit_message_text(
            "¿Qué quieres hacer?",
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "cancelar_recordatorio":
        await query.edit_message_text(
            "Usa `/cancelar [palabra]` para cancelar un recordatorio específico.",
            parse_mode='Markdown'
        )
    elif data in ["enviar_fotos", "ver_estado", "verificar_fotos"]:
        await query.edit_message_text(
            "Usa los comandos:\n/estado - Ver estado\n/cancelar - Cancelar"
        )
    else:
        await query.edit_message_text("Opción no disponible")

def get_callback_handler(): return CallbackQueryHandler(button_callback)