"""
Teclados inline para el bot.
Los teclados inline aparecen debajo de los mensajes.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Optional

def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado del menú principal.
    Aparece cuando el usuario usa /start
    """
    keyboard = [
        [
            InlineKeyboardButton("📝 Programar recordatorio", callback_data="menu_programar"),
            InlineKeyboardButton("📊 Ver estado", callback_data="menu_estado")
        ],
        [
            InlineKeyboardButton("❓ Ayuda", callback_data="menu_ayuda"),
            InlineKeyboardButton("ℹ️ Acerca de", callback_data="menu_acerca")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_programar_confirm_keyboard(time_str: str, frequency: int, message: str) -> InlineKeyboardMarkup:
    """
    Teclado de confirmación para programar un recordatorio.
    
    Args:
        time_str: Hora programada
        frequency: Frecuencia en minutos
        message: Mensaje del recordatorio
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Confirmar", callback_data=f"confirmar_programar_{time_str}_{frequency}"),
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_programar")
        ],
        [
            InlineKeyboardButton("✏️ Editar", callback_data="editar_programar")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reminder_actions_keyboard(user_id: str = None) -> InlineKeyboardMarkup:
    """
    Teclado con acciones para un recordatorio activo.
    SIN opción de pausar.
    """
    keyboard = [
        [
            InlineKeyboardButton("📸 Enviar fotos", callback_data="enviar_fotos"),
            InlineKeyboardButton("📊 Ver estado", callback_data="ver_estado")
        ],
        [
            InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_recordatorio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_alert_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado que aparece en las alertas.
    SIN opción de silenciar.
    """
    keyboard = [
        [
            InlineKeyboardButton("📸 Ya envié fotos", callback_data="verificar_fotos"),
        ],
        [
            InlineKeyboardButton("📊 Ver estado", callback_data="ver_estado"),
        ],
        [
            InlineKeyboardButton("❌ Cancelar recordatorio", callback_data="cancelar_recordatorio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_alert_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado que aparece en las alertas.
    """
    keyboard = [
        [
            InlineKeyboardButton("📸 Ya envié fotos", callback_data="verificar_fotos"),
        ],
        [
            InlineKeyboardButton("📊 Ver estado", callback_data="ver_estado"),
            InlineKeyboardButton("🔕 Silenciar 1h", callback_data="silenciar_1h")
        ],
        [
            InlineKeyboardButton("❌ Cancelar recordatorio", callback_data="cancelar_recordatorio")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_photo_progress_keyboard(photos_received: int, photos_required: int) -> InlineKeyboardMarkup:
    """
    Teclado que muestra el progreso de fotos.
    
    Args:
        photos_received: Fotos recibidas
        photos_required: Fotos requeridas
    """
    keyboard = []
    
    # Botón para enviar más fotos si aún faltan
    if photos_received < photos_required:
        keyboard.append([
            InlineKeyboardButton(
                f"📸 Enviar foto {photos_received + 1} de {photos_required}", 
                callback_data="enviar_fotos"
            )
        ])
    
    # Botones de acción
    keyboard.append([
        InlineKeyboardButton("📊 Ver estado", callback_data="ver_estado"),
        InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_recordatorio")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_confirmation_keyboard(action: str, item_id: str = "") -> InlineKeyboardMarkup:
    """
    Teclado genérico de confirmación.
    
    Args:
        action: Acción a confirmar (cancelar, pausar, etc.)
        item_id: ID del item (opcional)
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Sí, confirmar", callback_data=f"confirmar_{action}_{item_id}"),
            InlineKeyboardButton("❌ No, volver", callback_data="cancelar_confirmacion")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_help_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para la sección de ayuda.
    """
    keyboard = [
        [
            InlineKeyboardButton("📝 Cómo programar", callback_data="help_programar"),
            InlineKeyboardButton("📸 Cómo usar fotos", callback_data="help_fotos")
        ],
        [
            InlineKeyboardButton("⏰ Recordatorios", callback_data="help_recordatorios"),
            InlineKeyboardButton("⚙️ Configuración", callback_data="help_config")
        ],
        [
            InlineKeyboardButton("🔙 Volver al menú", callback_data="menu_principal")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_time_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para seleccionar horas predefinidas.
    """
    # Horas comunes para recordatorios
    common_times = [
        ["08:00", "09:00", "10:00", "11:00"],
        ["12:00", "13:00", "14:00", "15:00"],
        ["16:00", "17:00", "18:00", "19:00"],
        ["20:00", "21:00", "22:00"]
    ]
    
    keyboard = []
    for row in common_times:
        buttons = [
            InlineKeyboardButton(time, callback_data=f"seleccionar_hora_{time}")
            for time in row
        ]
        keyboard.append(buttons)
    
    # Añadir opción personalizada
    keyboard.append([
        InlineKeyboardButton("✏️ Hora personalizada", callback_data="hora_personalizada")
    ])
    
    # Botón de cancelar
    keyboard.append([
        InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_seleccion")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def get_frequency_selection_keyboard() -> InlineKeyboardMarkup:
    """
    Teclado para seleccionar frecuencias predefinidas.
    """
    frequencies = [
        ("1 minuto", 1),
        ("5 minutos", 5),
        ("10 minutos", 10),
        ("15 minutos", 15),
        ("30 minutos", 30),
        ("1 hora", 60),
        ("2 horas", 120),
        ("Personalizada", "custom")
    ]
    
    # Crear filas de 2 botones
    keyboard = []
    for i in range(0, len(frequencies), 2):
        row = []
        for j in range(2):
            if i + j < len(frequencies):
                label, value = frequencies[i + j]
                row.append(
                    InlineKeyboardButton(label, callback_data=f"frecuencia_{value}")
                )
        keyboard.append(row)
    
    keyboard.append([
        InlineKeyboardButton("❌ Cancelar", callback_data="cancelar_seleccion")
    ])
    
    return InlineKeyboardMarkup(keyboard)

def create_pagination_keyboard(current_page: int, total_pages: int, base_callback: str) -> InlineKeyboardMarkup:
    """
    Crea un teclado de paginación genérico.
    
    Args:
        current_page: Página actual
        total_pages: Total de páginas
        base_callback: Prefijo para los callbacks
    """
    keyboard = []
    row = []
    
    # Botón anterior
    if current_page > 1:
        row.append(
            InlineKeyboardButton("⬅️ Anterior", callback_data=f"{base_callback}_{current_page - 1}")
        )
    
    # Indicador de página
    row.append(
        InlineKeyboardButton(f"📄 {current_page}/{total_pages}", callback_data="ignore")
    )
    
    # Botón siguiente
    if current_page < total_pages:
        row.append(
            InlineKeyboardButton("Siguiente ➡️", callback_data=f"{base_callback}_{current_page + 1}")
        )
    
    keyboard.append(row)
    
    # Botón de volver
    keyboard.append([
        InlineKeyboardButton("🔙 Volver", callback_data="menu_principal")
    ])
    
    return InlineKeyboardMarkup(keyboard)