from typing import Optional, List
from pydantic import Field, ConfigDict
from src.shared.domain.base_entity import BaseEntity

from .identity import BrandIdentity, BrandVisuals
from .strategy import BrandStrategy
from .story import BrandStory
from .team import KeyFigure, BrandContact, BrandTestimonial, BrandAuthorityItem, BrandTeam

class BrandSettings(BaseEntity):
    """
    Configuration for the Brand Identity, Story, Strategy, and Team.
    Stored in Tenant.config_json['brand_settings'].
    """
    model_config = ConfigDict(extra='ignore')

    identity: Optional[BrandIdentity] = Field(None, description="Visual identity and design system")
    strategy: Optional[BrandStrategy] = Field(None, description="Strategic positioning")
    story: Optional[BrandStory] = Field(None, description="Brand narrative")
    
    # Updated to support List[KeyFigure] from frontend
    team: Optional[List[KeyFigure]] = Field(default_factory=list, description="Team structure and leadership")
    
    # New fields
    contact: Optional[BrandContact] = Field(None, description="Contact information")
    testimonials: List[BrandTestimonial] = Field(default_factory=list, description="Customer testimonials")
    authority_vault: List[BrandAuthorityItem] = Field(default_factory=list, description="Authority resources and links")
    visuals: Optional[BrandVisuals] = Field(None, description="Brand visual assets")
    
    # Legacy field support
    team_metadata: Optional[BrandTeam] = Field(None, description="Legacy team metadata")
