from typing import List, Optional
from pydantic import Field, ConfigDict
from src.shared.domain.base_entity import BaseEntity
import uuid


class StoryBrandHero(BaseEntity):
    """StoryBrand: The hero (customer)."""
    identity: Optional[str] = Field(None, description="Quién es el héroe")
    desire: Optional[str] = Field(None, description="Qué quiere lograr")
    model_config = ConfigDict(extra='ignore')


class StoryBrandProblem(BaseEntity):
    """StoryBrand: The three-layer problem."""
    villain: Optional[str] = Field(None, description="El villano")
    external_problem: Optional[str] = Field(None, description="Problema externo")
    internal_problem: Optional[str] = Field(None, description="Problema interno (emocional)")
    philosophical_problem: Optional[str] = Field(None, description="Problema filosófico (injusticia)")
    model_config = ConfigDict(extra='ignore')


class StoryBrandGuide(BaseEntity):
    """StoryBrand: The guide (brand)."""
    empathy_statement: Optional[str] = Field(None, description="Declaración de empatía")
    authority_statement: Optional[str] = Field(None, description="Declaración de autoridad")
    model_config = ConfigDict(extra='ignore')


class StoryBrandPlanStep(BaseEntity):
    """StoryBrand: A step in the plan."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_number: int = 1
    title: Optional[str] = None
    description: Optional[str] = None
    model_config = ConfigDict(extra='ignore')


class StoryBrandCTA(BaseEntity):
    """StoryBrand: Calls to action."""
    direct_cta: Optional[str] = Field(None, description="CTA directo (ej: 'Agenda tu demo gratis')")
    transitional_cta: Optional[str] = Field(None, description="CTA transicional (ej: 'Descarga la guía')")
    model_config = ConfigDict(extra='ignore')


class StoryBrandOutcome(BaseEntity):
    """StoryBrand: Success and failure outcomes."""
    success_transformation: Optional[str] = Field(None, description="Transformación exitosa")
    failure_consequence: Optional[str] = Field(None, description="Consecuencia del fracaso")
    model_config = ConfigDict(extra='ignore')


class BrandNarrative(BaseEntity):
    """
    StoryBrand framework (Donald Miller): Complete brand narrative model.
    Hero → Problem → Guide → Plan → CTA → Outcome.
    """
    hero: Optional[StoryBrandHero] = None
    problem: Optional[StoryBrandProblem] = None
    guide: Optional[StoryBrandGuide] = None
    plan: List[StoryBrandPlanStep] = Field(default_factory=list, description="3-4 pasos max")
    cta: Optional[StoryBrandCTA] = None
    outcome: Optional[StoryBrandOutcome] = None
    one_liner: Optional[str] = Field(None, description="Síntesis StoryBrand en 1 oración")
    model_config = ConfigDict(extra='ignore')
