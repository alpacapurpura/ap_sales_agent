from enum import Enum

class LandingPageArchetype(str, Enum):
    """
    Los 6 Arquetipos Maestros de Landing Pages definidos por la 'Fórmula Secreta'.
    """
    THE_SQUEEZE = "THE_SQUEEZE"          # Captura Pura (Lead Magnet)
    THE_EVENT = "THE_EVENT"              # Webinar / Reto / Lanzamiento
    THE_FLASH_OFFER = "THE_FLASH_OFFER"  # Tripwire / Low Ticket
    THE_TRANSFORMER = "THE_TRANSFORMER"  # Cursos / Mentorías (Sales Letter)
    THE_VELVET_ROPE = "THE_VELVET_ROPE"  # High Ticket / Aplicación
    THE_BROCHURE = "THE_BROCHURE"        # Servicios B2B / Corporativo

class LandingPageThemeColor(str, Enum):
    """
    Paletas de colores predefinidas o permitidas.
    """
    DEFAULT = "DEFAULT"
    OCEAN = "OCEAN"
    SUNSET = "SUNSET"
    FOREST = "FOREST"
    LUXURY = "LUXURY"
    MINIMAL = "MINIMAL"

class LandingPageFont(str, Enum):
    """
    Pares de fuentes tipográficas.
    """
    SANS_SERIF = "SANS_SERIF" # Inter / Roboto
    SERIF = "SERIF"           # Playfair / Merriweather
    MODERN = "MODERN"         # Montserrat / Open Sans
