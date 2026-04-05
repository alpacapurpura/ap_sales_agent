from enum import Enum


class LandingPageArchetype(str, Enum):
    THE_SQUEEZE = "THE_SQUEEZE"
    THE_EVENT = "THE_EVENT"
    THE_FLASH_OFFER = "THE_FLASH_OFFER"
    THE_TRANSFORMER = "THE_TRANSFORMER"
    THE_VELVET_ROPE = "THE_VELVET_ROPE"
    THE_BROCHURE = "THE_BROCHURE"


class LandingPageFont(str, Enum):
    SANS_SERIF = "SANS_SERIF"
    SERIF = "SERIF"
    MONO = "MONO"
