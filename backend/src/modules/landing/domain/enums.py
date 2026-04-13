"""Enumeration types for the landing domain."""

from enum import StrEnum


class LandingPageArchetype(StrEnum):
    """Enumerate landing page archetype values."""

    THE_SQUEEZE = "THE_SQUEEZE"
    THE_EVENT = "THE_EVENT"
    THE_FLASH_OFFER = "THE_FLASH_OFFER"
    THE_TRANSFORMER = "THE_TRANSFORMER"
    THE_VELVET_ROPE = "THE_VELVET_ROPE"
    THE_BROCHURE = "THE_BROCHURE"


class LandingPageFont(StrEnum):
    """Enumerate landing page font values."""

    SANS_SERIF = "SANS_SERIF"
    SERIF = "SERIF"
    MONO = "MONO"
