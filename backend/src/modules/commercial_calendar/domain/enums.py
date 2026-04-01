from enum import Enum


class EventCategory(str, Enum):
    FERIADO = "feriado"
    CAMPANA = "campaña"
    CYBER = "cyber"
    SALE = "sale"
    DIA_ESPECIAL = "dia_especial"
    TEMPORADA = "temporada"
    CULTURAL = "cultural"
    ELECCIONES = "elecciones"
    CUSTOM = "custom"
