from typing import Any, Optional, List, Dict
from pydantic import Field, ConfigDict
from src.shared.domain.base_entity import BaseEntity



class BrandVisuals(BaseEntity):
    # === COLORES (core) ===
    primary_color: Optional[str] = None
    secondary_color: Optional[str] = None           # 2nd brand color (sections, headers)
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    surface_color: Optional[str] = None              # Card/modal background
    text_primary_color: Optional[str] = None
    text_secondary_color: Optional[str] = None       # Subtitles, captions
    text_on_primary: Optional[str] = None
    text_on_secondary: Optional[str] = None          # Text on secondary color

    # === COLORES (extended) ===
    color_palette: List[str] = Field(default_factory=list)
    neutral_colors: List[str] = Field(default_factory=list)
    semantic_colors: Optional[Dict[str, Optional[str]]] = None  # {success, error, warning, info}
    gradient_definitions: List[str] = Field(default_factory=list)  # CSS gradient strings
    color_usage_rules: Optional[str] = None          # 60-30-10 distribution rules

    # === TYPOGRAPHY ===
    font_heading: Optional[str] = None
    font_body: Optional[str] = None
    font_accent: Optional[str] = None                # Decorative/display font
    font_weights: Optional[Dict[str, Any]] = None    # {heading: [700,600], body: [400]}
    typography_scale: Optional[Dict[str, str]] = None # {h1: "48px", body: "16px"}

    # === DESIGN SYSTEM ===
    border_radius_style: Optional[str] = None        # "rounded", "sharp", "pill", "mixed"
    border_radius_values: Optional[Dict[str, str]] = None  # {sm: "4px", md: "8px"}
    shadow_style: Optional[str] = None               # none|subtle|moderate|prominent
    spacing_base: Optional[str] = None               # "8px"
    visual_density: Optional[str] = None             # compact|comfortable|spacious

    # === VISUAL PERSONALITY ===
    brand_mood: Optional[Dict[str, Any]] = None      # {adjectives: [...], energy: "high"}
    visual_references: Optional[str] = None          # "Similar a Apple + Stripe"
    photography_style: Optional[str] = None          # lifestyle|product|abstract|minimal
    icon_style: Optional[str] = None                 # outlined|filled|duotone

    # === STYLE ===
    style_preset: Optional[str] = None
    design_style: Optional[str] = None
    usage_guidelines: List[str] = Field(default_factory=list)

    # === ASSETS ===
    logo_url: Optional[str] = None
    favicon_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    logos: Optional[Dict[str, Optional[str]]] = Field(default_factory=dict)

    model_config = ConfigDict(extra='allow')

class BrandIdentity(BaseEntity):
    """
    Core identity of the brand.
    Visual aspects are delegated to BrandVisuals.
    """
    # --- Identity ---
    brand_name: Optional[str] = Field(None, description="The name of the brand.")
    industry: Optional[str] = Field(None, description="The industry or category of the brand.")
    tagline: Optional[str] = Field(None, description="Brand tagline or slogan.")
    description: Optional[str] = Field(None, description="Positioning statement (2-3 sentences).")
    founding_year: Optional[str] = Field(None, description="Year the brand was founded.")
    website: Optional[str] = Field(None, description="Canonical website URL.")
    language: Optional[str] = Field(None, description="Primary language code (e.g. 'es', 'en').")
    timezone: Optional[str] = Field(None, description="Operational timezone (e.g. 'America/Mexico_City').")
    voice_tone: Optional[str] = Field(None, description="Voice tone descriptors (e.g. 'conversacional, aspiracional').")
    legal_name: Optional[str] = Field(None, description="Legal entity name.")
    tax_id: Optional[str] = Field(None, description="Tax ID (RFC, NIF, CUIT, EIN).")
    fiscal_address: Optional[str] = Field(None, description="Fiscal address.")
    legal_representative: Optional[str] = Field(None, description="Legal representative name.")
    terms_url: Optional[str] = Field(None, description="Terms and conditions URL.")
    privacy_url: Optional[str] = Field(None, description="Privacy policy URL.")

    model_config = ConfigDict(extra='allow')
