from typing import Optional, List, Dict
from pydantic import Field, ConfigDict
from src.shared.domain.base_entity import BaseEntity



class BrandVisuals(BaseEntity):
    # Colors
    primary_color: Optional[str] = None
    accent_color: Optional[str] = None
    background_color: Optional[str] = None
    text_primary_color: Optional[str] = None
    text_on_primary: Optional[str] = None

    # Typography
    font_heading: Optional[str] = None
    font_body: Optional[str] = None

    # Style
    style_preset: Optional[str] = None
    design_style: Optional[str] = None
    usage_guidelines: List[str] = Field(default_factory=list)

    # Extended palette
    color_palette: List[str] = Field(default_factory=list)  # additional hex colors beyond the 5 primary ones
    border_radius_style: Optional[str] = None  # "rounded", "sharp", "pill", "mixed"

    # Assets
    logo_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    logos: Optional[Dict[str, Optional[str]]] = Field(default_factory=dict) # primary, secondary, etc.

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
    archetype: Optional[str] = Field(None, description="Jungian archetype (Hero, Sage, Creator, etc.).")
    keywords: List[str] = Field(default_factory=list, description="5-8 strategic brand keywords.")
    voice_tone: Optional[str] = Field(None, description="Voice tone descriptors (e.g. 'conversacional, aspiracional').")
    legal_name: Optional[str] = Field(None, description="Legal entity name.")
    tax_id: Optional[str] = Field(None, description="Tax ID (RFC, NIF, CUIT, EIN).")
    fiscal_address: Optional[str] = Field(None, description="Fiscal address.")
    legal_representative: Optional[str] = Field(None, description="Legal representative name.")
    terms_url: Optional[str] = Field(None, description="Terms and conditions URL.")
    privacy_url: Optional[str] = Field(None, description="Privacy policy URL.")

    model_config = ConfigDict(extra='allow')
