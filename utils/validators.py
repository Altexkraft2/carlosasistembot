"""
Utilidades de validación.
Funciones para validar datos de entrada.
"""

import re
from datetime import datetime


def validate_frequency(minutes: int) -> bool:
    """
    Valida que la frecuencia sea razonable.
    
    Args:
        minutes: Minutos entre alertas
        
    Returns:
        True si es válida (1-1440), False si no
    """
    return 1 <= minutes <= 1440  # Máximo 24 horas

def validate_message_length(message: str, max_length: int = 500) -> bool:
    """
    Valida que el mensaje no sea demasiado largo.
    
    Args:
        message: Mensaje a validar
        max_length: Longitud máxima permitida
        
    Returns:
        True si es válido, False si no
    """
    return len(message) <= max_length

def parse_reminder_args(args: list) -> dict:
    """
    Parsea los argumentos del comando /programar.
    Nuevo formato: [frecuencia] [mensaje]
    """
    result = {
        'frequency': None,
        'message': None
    }
    
    if not args:
        return result
    
    # Intentar parsear el primer argumento como frecuencia
    try:
        result['frequency'] = int(args[0])
        # El resto es el mensaje
        if len(args) > 1:
            result['message'] = ' '.join(args[1:])
    except ValueError:
        # Si no es número, todo es el mensaje
        result['message'] = ' '.join(args)
    
    return result