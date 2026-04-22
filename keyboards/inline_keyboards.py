"""
Teclados inline para el bot.
Versión simplificada - solo botones esenciales.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """Teclado del menú principal."""
    keyboard = [
        [
            InlineKeyboardButton("📝 Programar", callback_data="menu_programar"),
            InlineKeyboardButton("📊 Estado", callback_data="menu_estado")
        ],
        [
            InlineKeyboardButton("❓ Ayuda", callback_data="menu_ayuda"),
            InlineKeyboardButton("🕐 Horario", callback_data="menu_horario")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reminder_actions_keyboard(user_id: str = None) -> InlineKeyboardMarkup:
    """Teclado con acciones para un recordatorio activo (solo cancelar)."""
    keyboard = [
        [
            InlineKeyboardButton("❌ Cancelar recordatorio", callback_data="cancelar_recordatorio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_alert_keyboard() -> InlineKeyboardMarkup:
    """Teclado que aparece en las alertas (solo cancelar)."""
    keyboard = [
        [
            InlineKeyboardButton("❌ Cancelar recordatorio", callback_data="cancelar_recordatorio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_photo_progress_keyboard(photos_received: int, photos_required: int) -> InlineKeyboardMarkup:
    """Teclado de progreso de fotos (solo cancelar)."""
    keyboard = [
        [
            InlineKeyboardButton("❌ Cancelar recordatorio", callback_data="cancelar_recordatorio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_help_keyboard() -> InlineKeyboardMarkup:
    """Teclado para la sección de ayuda."""
    keyboard = [
        [
            InlineKeyboardButton("🔙 Volver al menú", callback_data="menu_principal")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str, item_id: str = "") -> InlineKeyboardMarkup:
    """Teclado genérico de confirmación."""
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí, confirmar", callback_data=f"confirmar_{action}_{item_id}"),
            InlineKeyboardButton("❌ No, cancelar", callback_data="cancelar_confirmacion")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_time_selection_keyboard() -> InlineKeyboardMarkup:
    """Teclado para seleccionar horas predefinidas."""
    common_times = [
        ["08:00", "09:00", "10:00", "11:00"],
        ["12:00", "13:00", "14:00", "15:00"],
        ["16:00", "17:00", "18:00", "19:00"],
        ["20:00", "21:00", "22:00"]
    ]
    
    keyboard = []
    for row in common_times:
        buttons = [InlineKeyboardButton(time, callback_data=f"seleccionar_hora_{time}") for time in row]
        keyboard.append(buttons)
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_seleccion")])
    return InlineKeyboardMarkup(keyboard)

def get_frequency_selection_keyboard() -> InlineKeyboardMarkup:
    """Teclado para seleccionar frecuencias predefinidas."""
    frequencies = [
        ("1 minuto", "1min"),
        ("5 minutos", "5min"),
        ("10 minutos", "10min"),
        ("15 minutos", "15min"),
        ("30 minutos", "30min"),
        ("1 hora", "1h"),
        ("2 horas", "2h"),
        ("Personalizada", "custom")
    ]
    
    keyboard = []
    for i in range(0, len(frequencies), 2):
        row = []
        for j in range(2):
            if i + j < len(frequencies):
                label, value = frequencies[i + j]
                row.append(InlineKeyboardButton(label, callback_data=f"frecuencia_{value}"))
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_seleccion")])
    return InlineKeyboardMarkup(keyboard)