"""Handler para procesar callbacks de botones inline"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from services.reminder_service_db import ReminderServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config
from datetime import datetime

logger = setup_logger(__name__)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    chat_id = update.effective_chat.id
    data = query.data
    logger.info(f"🔘 Callback: {data}")
    
    reminder_service: ReminderServiceDB = context.bot_data.get('reminder_service')
    
    if data == "menu_programar":
        await query.edit_message_text(
            "*Programar Recordatorio*\n\n"
            "`/programar [frecuencia] [palabra] [mensaje]`\n\n"
            "También puedes usar `/recordar` respondiendo a un mensaje.",
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "menu_estado":
        await query.edit_message_text(
            "Usa `/estado` para ver tus recordatorios activos.",
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "menu_ayuda":
        await query.edit_message_text(
            "*AYUDA*\n/programar - /recordar - /estado - /cancelar - /horario",
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_help_keyboard()
        )
    elif data == "menu_horario":
        now = datetime.now()
        is_work = Config.is_work_time(now)
        if is_work:
            status = "✅ *Estamos en horario laboral*"
        else:
            next_work = Config.get_next_work_time(now)
            status = f"⏸️ *Fuera de horario*\nPróximo: {next_work}"
        await query.edit_message_text(
            f"{status}\n\n{Config.get_work_schedule_text()}",
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "menu_acerca":
        await query.edit_message_text(
            "🤖 Bot de Recordatorios v2.0\n📸 Verificación por fotos\n📝 Recordatorios simples",
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "menu_principal":
        await query.edit_message_text(
            "¿Qué quieres hacer?",
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    elif data == "cancelar_recordatorio":
        await query.edit_message_text(
            "Usa `/cancelar` para cancelar todos tus recordatorios o `/cancelar [palabra]` para uno específico.",
            parse_mode='Markdown'
        )
    elif data.startswith("seleccionar_hora_"):
        hora = data.replace("seleccionar_hora_", "")
        context.user_data['temp_hora'] = hora
        await query.edit_message_text(
            f"🕐 Hora: {hora}\n\nSelecciona la frecuencia:",
            reply_markup=inline_keyboards.get_frequency_selection_keyboard()
        )
    elif data.startswith("frecuencia_"):
        frecuencia = data.replace("frecuencia_", "")
        hora = context.user_data.get('temp_hora', '14:00')
        
        if frecuencia == "custom":
            await query.edit_message_text(
                "✏️ Usa el comando manualmente:\n`/programar [frecuencia] [palabra] [mensaje]`",
                parse_mode='Markdown',
                reply_markup=inline_keyboards.get_main_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                f"✅ Usa:\n`/programar {frecuencia} [palabra] [mensaje]`",
                parse_mode='Markdown',
                reply_markup=inline_keyboards.get_main_menu_keyboard()
            )
    elif data == "cancelar_seleccion":
        await query.edit_message_text(
            "Operación cancelada.",
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    else:
        await query.edit_message_text("Opción no disponible")

def get_callback_handler():
    return CallbackQueryHandler(button_callback)