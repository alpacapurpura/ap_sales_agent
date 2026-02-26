from typing import Optional, List
from pydantic import Field, ConfigDict
from src.shared.domain.base_entity import BaseEntity

class BrandStoryMilestone(BaseEntity):
    id: Optional[str] = None
    year: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(extra='allow')

class BrandStory(BaseEntity):
    """
    The narrative and history of the brand.
    """
    origin_story: Optional[str] = Field(None)
    mission: Optional[str] = Field(None)
    vision: Optional[str] = Field(None)
    
    # Updated to support structured milestones
    milestones: List[BrandStoryMilestone] = Field(default_factory=list)
    
    # Legacy support for string list
    milestones_legacy: Optional[List[str]] = Field(None)
    
    model_config = ConfigDict(extra='allow')
