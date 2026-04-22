"""
Handler para procesar callbacks de botones inline.
Versión simplificada.
"""

from telegram import Update
from telegram.ext import CallbackQueryHandler, ContextTypes
from services.reminder_service_db import ReminderServiceDB
from keyboards import inline_keyboards
from utils.logger import setup_logger
from config import Config
from datetime import datetime

logger = setup_logger(__name__)

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Procesa todos los callbacks de botones inline."""
    query = update.callback_query
    await query.answer()
    
    user_id = str(query.from_user.id)
    chat_id = update.effective_chat.id
    data = query.data
    
    logger.info(f"🔘 Callback: {data} de usuario {user_id}")
    
    reminder_service: ReminderServiceDB = context.bot_data.get('reminder_service')
    
    # === MENÚ PRINCIPAL ===
    
    if data == "menu_programar":
        await query.edit_message_text(
            "*Programar Recordatorio*\n\n"
            "Usa el comando:\n"
            "`/programar [frecuencia] [palabra] [mensaje]`\n\n"
            "*Frecuencias válidas:*\n"
            "• `5min`, `30min` → minutos\n"
            "• `1h`, `2h` → horas\n"
            "• `1:30`, `0:45` → horas:minutos\n\n"
            "*Ejemplo:*\n"
            "`/programar 5min MEDICINA Tomar pastilla`",
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    
    elif data == "menu_estado":
        if reminder_service:
            reminders = reminder_service.get_user_reminders(user_id, chat_id)
            if reminders:
                message = "📊 *TUS RECORDATORIOS ACTIVOS*\n\n"
                for r in reminders:
                    message += f"🔑 `{r.keyword}` - {r.photos_received}/{Config.PHOTOS_REQUIRED} 📸\n"
                message += "\nUsa `/estado [palabra]` para ver detalles."
            else:
                message = "ℹ️ No tienes recordatorios activos."
            
            await query.edit_message_text(
                message,
                parse_mode='Markdown',
                reply_markup=inline_keyboards.get_main_menu_keyboard()
            )
    
    elif data == "menu_ayuda":
        await query.edit_message_text(
            "*AYUDA*\n\n"
            "• `/programar` - Crear recordatorio\n"
            "• `/estado` - Ver progreso\n"
            "• `/cancelar` - Detener alertas\n"
            "• `/horario` - Horario laboral",
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
            status = f"⏸️ *Fuera de horario laboral*\nPróximo inicio: {next_work}"
        
        message = f"{status}\n\n{Config.get_work_schedule_text()}"
        await query.edit_message_text(
            message,
            parse_mode='Markdown',
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    
    elif data == "menu_principal":
        await query.edit_message_text(
            "¿Qué quieres hacer?",
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    
    # === ACCIONES ===
    
    elif data == "cancelar_recordatorio":
        if reminder_service:
            # Mostrar confirmación
            await query.edit_message_text(
                "¿Estás seguro de cancelar TODOS tus recordatorios?\n\n"
                "Usa `/cancelar` para cancelar todos o `/cancelar [palabra]` para uno específico.",
                reply_markup=inline_keyboards.get_main_menu_keyboard()
            )
    
    # === SELECCIÓN DE HORA ===
    
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
                f"✏️ Usa el comando manualmente:\n"
                f"`/programar [frecuencia] [palabra] [mensaje]`\n\n"
                f"Formatos: `5min`, `1h`, `1:30`",
                parse_mode='Markdown',
                reply_markup=inline_keyboards.get_main_menu_keyboard()
            )
        else:
            await query.edit_message_text(
                f"✅ Configuración:\n"
                f"• Hora: {hora}\n"
                f"• Frecuencia: {frecuencia}\n\n"
                f"Usa el comando:\n"
                f"`/programar {frecuencia} [palabra] [mensaje]`",
                parse_mode='Markdown',
                reply_markup=inline_keyboards.get_main_menu_keyboard()
            )
    
    elif data == "cancelar_seleccion":
        await query.edit_message_text(
            "Operación cancelada.",
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )
    
    else:
        await query.edit_message_text(
            "Opción no disponible.",
            reply_markup=inline_keyboards.get_main_menu_keyboard()
        )

def get_callback_handler():
    return CallbackQueryHandler(button_callback)