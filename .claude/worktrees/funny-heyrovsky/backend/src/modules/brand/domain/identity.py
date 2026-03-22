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

    # Assets
    logo_url: Optional[str] = None
    images: List[str] = Field(default_factory=list)
    logos: Optional[Dict[str, Optional[str]]] = Field(default_factory=dict) # primary, secondary, etc.
    
    model_config = ConfigDict(extra='allow')

class BrandIdentity(BaseEntity):
    """
    Core identity of the brand (Name, Industry).
    Visual aspects are delegated to BrandVisuals.
    """
    # --- Identity ---
    brand_name: Optional[str] = Field(None, description="The name of the brand.")
    industry: Optional[str] = Field(None, description="The industry or category of the brand.")
    
    # NOTE: Visual fields (colors, fonts) have been moved to BrandVisuals
    # to avoid duplication and ambiguity.
    
    model_config = ConfigDict(extra='allow')
