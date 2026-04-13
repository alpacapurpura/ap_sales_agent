from enum import StrEnum


class EventCategory(StrEnum):
    FERIADO = "feriado"
    CAMPANA = "campaña"
    CYBER = "cyber"
    SALE = "sale"
    DIA_ESPECIAL = "dia_especial"
    TEMPORADA = "temporada"
    CULTURAL = "cultural"
    ELECCIONES = "elecciones"
    CUSTOM = "custom"
