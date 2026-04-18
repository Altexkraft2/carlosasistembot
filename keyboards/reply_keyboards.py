"""
Teclados de respuesta para el bot.
Estos teclados reemplazan el teclado normal del usuario temporalmente.
"""

from telegram import ReplyKeyboardMarkup, KeyboardButton
from typing import List, Optional

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Teclado de respuesta principal.
    """
    keyboard = [
        [KeyboardButton("📝 Programar"), KeyboardButton("📊 Estado")],
        [KeyboardButton("❌ Cancelar"), KeyboardButton("❓ Ayuda")]
    ]
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True,
        input_field_placeholder="Selecciona una opción..."
    )

def get_photo_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Teclado específico para enviar fotos.
    """
    keyboard = [
        [KeyboardButton("📸 Enviar foto"), KeyboardButton("📊 Ver progreso")],
        [KeyboardButton("🔙 Volver al menú")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="Envía una foto o selecciona una opción"
    )

def get_cancel_reply_keyboard() -> ReplyKeyboardMarkup:
    """
    Teclado simple con solo opción de cancelar.
    """
    keyboard = [
        [KeyboardButton("❌ Cancelar operación")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=True,  # Se oculta después de usar
        input_field_placeholder="Presiona Cancelar para volver"
    )

def get_time_input_keyboard() -> ReplyKeyboardMarkup:
    """
    Teclado para input de hora con opciones comunes.
    """
    keyboard = [
        [KeyboardButton("08:00"), KeyboardButton("12:00"), KeyboardButton("16:00")],
        [KeyboardButton("20:00"), KeyboardButton("Personalizada"), KeyboardButton("❌ Cancelar")]
    ]
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        input_field_placeholder="Selecciona o escribe una hora (HH:MM)"
    )

def remove_keyboard() -> ReplyKeyboardMarkup:
    """
    Elimina el teclado de respuesta personalizado.
    """
    return ReplyKeyboardMarkup.remove()