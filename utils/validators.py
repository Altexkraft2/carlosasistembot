"""
Utilidades de validación.
Formatos de frecuencia simplificados.
"""

import re
from datetime import datetime

def validate_time_format(time_str: str) -> bool:
    """Valida que una cadena tenga formato HH:MM."""
    if not time_str:
        return False
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    if not re.match(pattern, time_str):
        return False
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False

def parse_frequency(freq_str: str) -> int:
    """
    Parsea una cadena de frecuencia a minutos.
    
    Formatos soportados:
    - "5min", "30min" → minutos
    - "1h", "2h" → horas (SOLO ENTEROS)
    - "1:30", "2:45" → formato HH:MM
    - "5", "30" → minutos (por defecto)
    """
    if not freq_str:
        raise ValueError("La frecuencia no puede estar vacía")
    
    freq_str = freq_str.strip().lower()
    
    # Caso 1: Formato HH:MM (ej: "1:30", "2:45")
    if ':' in freq_str:
        pattern = r'^(\d+):([0-5]?\d)$'
        match = re.match(pattern, freq_str)
        if match:
            hours = int(match.group(1))
            minutes = int(match.group(2))
            total_minutes = hours * 60 + minutes
            if total_minutes < 1:
                raise ValueError("La frecuencia debe ser al menos 1 minuto")
            if total_minutes > 1440:
                raise ValueError("La frecuencia máxima es 24 horas (1440 minutos)")
            return total_minutes
        else:
            raise ValueError(f"Formato HH:MM inválido: '{freq_str}'. Ejemplo: '1:30'")
    
    # Caso 2: Termina con 'h' (horas - SOLO ENTEROS)
    if freq_str.endswith('h'):
        try:
            hours_str = freq_str[:-1]
            if '.' in hours_str:
                raise ValueError(f"No se permiten decimales en horas. Usa formato HH:MM en su lugar (ej: '1:30')")
            hours = int(hours_str)
            total_minutes = hours * 60
            if total_minutes < 1:
                raise ValueError("La frecuencia debe ser al menos 1 minuto")
            if total_minutes > 1440:
                raise ValueError("La frecuencia máxima es 24 horas (1440 minutos)")
            return total_minutes
        except ValueError as e:
            if "No se permiten" in str(e):
                raise
            raise ValueError(f"Formato de horas inválido: '{freq_str}'. Usa números enteros (ej: '1h', '2h')")
    
    # Caso 3: Termina con 'min' (minutos - SOLO ENTEROS)
    if freq_str.endswith('min'):
        try:
            mins_str = freq_str[:-3]
            if '.' in mins_str:
                raise ValueError(f"No se permiten decimales en minutos. Usa números enteros.")
            minutes = int(mins_str)
            if minutes < 1:
                raise ValueError("La frecuencia debe ser al menos 1 minuto")
            if minutes > 1440:
                raise ValueError("La frecuencia máxima es 24 horas (1440 minutos)")
            return minutes
        except ValueError as e:
            if "No se permiten" in str(e):
                raise
            raise ValueError(f"Formato de minutos inválido: '{freq_str}'. Ejemplo: '5min'")
    
    # Caso 4: Solo número (minutos por defecto - SOLO ENTEROS)
    try:
        if '.' in freq_str:
            raise ValueError(f"No se permiten decimales. Usa números enteros.")
        minutes = int(freq_str)
        if minutes < 1:
            raise ValueError("La frecuencia debe ser al menos 1 minuto")
        if minutes > 1440:
            raise ValueError("La frecuencia máxima es 24 horas (1440 minutos)")
        return minutes
    except ValueError as e:
        if "No se permiten" in str(e):
            raise
        raise ValueError(
            f"Formato de frecuencia no reconocido: '{freq_str}'\n"
            f"Formatos válidos:\n"
            f"  • '5min', '30min' → minutos\n"
            f"  • '1h', '2h' → horas (enteros)\n"
            f"  • '1:30', '0:45' → horas:minutos\n"
            f"  • '5', '30' → minutos (por defecto)"
        )

def format_frequency(minutes: int) -> str:
    """Formatea minutos a un formato legible."""
    if minutes < 60:
        return f"{minutes} min"
    hours = minutes // 60
    mins = minutes % 60
    if mins == 0:
        return f"{hours}h"
    else:
        return f"{hours}h {mins}min"

def validate_frequency(minutes: int) -> bool:
    """Valida que la frecuencia sea razonable (1-1440 minutos)"""
    return 1 <= minutes <= 1440

def validate_message_length(message: str, max_length: int = 500) -> bool:
    """Valida que el mensaje no sea demasiado largo."""
    return len(message) <= max_length

def parse_reminder_args(args: list) -> dict:
    """Parsea los argumentos del comando /programar."""
    result = {'frequency': None, 'keyword': None, 'message': None}
    if not args:
        return result
    try:
        result['frequency'] = parse_frequency(args[0])
        if len(args) > 1:
            result['keyword'] = args[1].strip()
            if len(args) > 2:
                result['message'] = ' '.join(args[2:])
    except ValueError:
        result['keyword'] = args[0].strip()
        if len(args) > 1:
            result['message'] = ' '.join(args[1:])
    return result