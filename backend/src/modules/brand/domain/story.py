"""Brand story value objects."""

from luana_core_platform.domain.base_entity import BaseEntity
from pydantic import ConfigDict, Field


class BrandStoryMilestone(BaseEntity):
    """Represent brand story milestone data."""

    id: str | None = None
    year: str | None = None
    title: str | None = None
    description: str | None = None
    model_config = ConfigDict(extra="allow")


class BrandStory(BaseEntity):
    """The narrative and history of the brand."""

    origin_story: str | None = Field(None)
    mission: str | None = Field(None)
    vision: str | None = Field(None)

    # Updated to support structured milestones
    milestones: list[BrandStoryMilestone] = Field(default_factory=list)

    # Legacy support for string list
    milestones_legacy: list[str] | None = Field(None)

    model_config = ConfigDict(extra="allow")
