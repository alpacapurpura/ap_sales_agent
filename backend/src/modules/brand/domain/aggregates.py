from typing import Optional, List, Any
from pydantic import Field, ConfigDict, model_validator
from src.shared.domain.base_entity import BaseEntity

from .identity import BrandIdentity, BrandVisuals
from .strategy import BrandStrategy
from .story import BrandStory
from .team import KeyFigure, BrandContact, BrandTestimonial, BrandAuthorityItem, BrandTeam
from .positioning import BrandPositioning
from .narrative import BrandNarrative
from .communication_assets import CommunicationAssets

class BrandSettings(BaseEntity):
    """
    Configuration for the Brand Identity, Story, Strategy, and Team.
    Stored in Tenant.config_json['brand_settings'].
    """
    model_config = ConfigDict(extra='ignore')

    @model_validator(mode='before')
    @classmethod
    def migrate_strategy_to_positioning(cls, data: Any) -> Any:
        """Migrate fields removed from BrandStrategy into BrandPositioning.

        Handles legacy JSON where unique_value_proposition and competitors
        lived under strategy. Moves them to positioning before Pydantic
        validates child models (which would reject unknown fields).
        """
        if not isinstance(data, dict):
            return data

        strategy = data.get('strategy')
        if not isinstance(strategy, dict):
            return data

        # Ensure positioning dict exists
        positioning = data.get('positioning')
        if positioning is None:
            positioning = {}
            data['positioning'] = positioning
        if not isinstance(positioning, dict):
            return data

        # 1. Migrate unique_value_proposition
        uvp = strategy.get('unique_value_proposition')
        if uvp and not positioning.get('unique_value_proposition'):
            positioning['unique_value_proposition'] = uvp

        # 2. Migrate competitors -> competitive_environment.direct_competitors
        competitors = strategy.get('competitors')
        if competitors and isinstance(competitors, list):
            comp_env = positioning.get('competitive_environment')
            if comp_env is None:
                comp_env = {}
                positioning['competitive_environment'] = comp_env
            if isinstance(comp_env, dict) and not comp_env.get('direct_competitors'):
                comp_env['direct_competitors'] = competitors

        # 3. Remove migrated fields from strategy to avoid validation errors
        for field in (
            'unique_value_proposition', 'competitors',
            'value_proposition', 'target_audience',
            'differentiation', 'offerings',
        ):
            strategy.pop(field, None)

        return data

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

    # Strategic frameworks
    positioning: Optional[BrandPositioning] = Field(None, description="Brand Love Key positioning framework")
    narrative: Optional[BrandNarrative] = Field(None, description="StoryBrand narrative framework")
    communication_assets: Optional[CommunicationAssets] = Field(None, description="Dynamic funnel-stage communication assets")

    # Legacy field support
    team_metadata: Optional[BrandTeam] = Field(None, description="Legacy team metadata")
