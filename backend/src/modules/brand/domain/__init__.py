"""Brand domain package."""

from .aggregates import BrandSettings
from .communication_assets import CommunicationAssets, CreativeConcept, FunnelAsset
from .entities import Avatar, ExtractRequest
from .identity import BrandIdentity, BrandVisuals
from .narrative import (
    BrandNarrative,
    StoryBrandCTA,
    StoryBrandGuide,
    StoryBrandHero,
    StoryBrandOutcome,
    StoryBrandPlanStep,
    StoryBrandProblem,
)
from .positioning import (
    BrandBenefits,
    BrandPersonality,
    BrandPositioning,
    BrandValues,
    CompetitiveEnvironment,
    ConsumerInsight,
    ReasonToBelieve,
)
from .story import BrandStory, BrandStoryMilestone
from .strategy import BrandCompetitor, BrandMethodologyPillar, BrandStrategy
from .team import (
    BrandAuthorityItem,
    BrandContact,
    BrandTeamWrapper,
    BrandTestimonial,
    KeyFigure,
)

__all__ = [
    "Avatar",
    "BrandAuthorityItem",
    "BrandBenefits",
    "BrandCompetitor",
    "BrandContact",
    "BrandIdentity",
    "BrandMethodologyPillar",
    "BrandNarrative",
    "BrandPersonality",
    "BrandPositioning",
    "BrandSettings",
    "BrandStory",
    "BrandStoryMilestone",
    "BrandStrategy",
    "BrandTeamWrapper",
    "BrandTestimonial",
    "BrandValues",
    "BrandVisuals",
    "CommunicationAssets",
    "CompetitiveEnvironment",
    "ConsumerInsight",
    "CreativeConcept",
    "ExtractRequest",
    "FunnelAsset",
    "KeyFigure",
    "ReasonToBelieve",
    "StoryBrandCTA",
    "StoryBrandGuide",
    "StoryBrandHero",
    "StoryBrandOutcome",
    "StoryBrandPlanStep",
    "StoryBrandProblem",
]
