"""Reglas compartidas de validación de DNI compatibles con v2.1.0."""

from typing import Optional


def normalizar_dni(dni_raw: object) -> Optional[str]:
    """
    Valida y normaliza un DNI siguiendo las reglas institucionales (heredadas de main.py v2.1.0):
    - Debe ser una cadena de texto (str) no vacía.
    - Se eliminan espacios laterales (.strip()).
    - Debe contener únicamente dígitos numéricos y al menos 7 caracteres (máx. 10).
    """
    if not dni_raw or not isinstance(dni_raw, str):
        return None

    dni_limpio = dni_raw.strip()
    if 7 <= len(dni_limpio) <= 10 and dni_limpio.isdigit():
        return dni_limpio

    return None


def validar_dni_estricto(dni_raw: object) -> str:
    """Normaliza el DNI o lanza ValueError descriptivo para esquemas Pydantic / servicios."""
    dni = normalizar_dni(dni_raw)
    if dni is None:
        raise ValueError(
            "El DNI es obligatorio y debe contener entre 7 y 10 dígitos numéricos sin puntos ni letras."
        )
    return dni

