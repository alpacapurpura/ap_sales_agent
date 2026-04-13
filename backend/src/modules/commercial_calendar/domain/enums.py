"""Enumeration types for the commercial_calendar domain."""

from enum import StrEnum


class EventCategory(StrEnum):
    """Enumerate event category values."""

    FERIADO = "feriado"
    CAMPANA = "campaña"
    CYBER = "cyber"
    SALE = "sale"
    DIA_ESPECIAL = "dia_especial"
    TEMPORADA = "temporada"
    CULTURAL = "cultural"
    ELECCIONES = "elecciones"
    CUSTOM = "custom"
