"""Brand narrative value objects."""

import uuid

from pydantic import ConfigDict, Field

from src.shared.domain.base_entity import BaseEntity


class StoryBrandHero(BaseEntity):
    """StoryBrand: The hero (customer)."""

    identity: str | None = Field(None, description="Quién es el héroe")
    desire: str | None = Field(None, description="Qué quiere lograr")
    model_config = ConfigDict(extra="ignore")


class StoryBrandProblem(BaseEntity):
    """StoryBrand: The three-layer problem."""

    villain: str | None = Field(None, description="El villano")
    external_problem: str | None = Field(None, description="Problema externo")
    internal_problem: str | None = Field(
        None,
        description="Problema interno (emocional)",
    )
    philosophical_problem: str | None = Field(
        None,
        description="Problema filosófico (injusticia)",
    )
    model_config = ConfigDict(extra="ignore")


class StoryBrandGuide(BaseEntity):
    """StoryBrand: The guide (brand)."""

    empathy_statement: str | None = Field(None, description="Declaración de empatía")
    authority_statement: str | None = Field(
        None,
        description="Declaración de autoridad",
    )
    model_config = ConfigDict(extra="ignore")


class StoryBrandPlanStep(BaseEntity):
    """StoryBrand: A step in the plan."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    step_number: int = 1
    title: str | None = None
    description: str | None = None
    model_config = ConfigDict(extra="ignore")


class StoryBrandCTA(BaseEntity):
    """StoryBrand: Calls to action."""

    direct_cta: str | None = Field(
        None,
        description="CTA directo (ej: 'Agenda tu demo gratis')",
    )
    transitional_cta: str | None = Field(
        None,
        description="CTA transicional (ej: 'Descarga la guía')",
    )
    model_config = ConfigDict(extra="ignore")


class StoryBrandOutcome(BaseEntity):
    """StoryBrand: Success and failure outcomes."""

    success_transformation: str | None = Field(
        None,
        description="Transformación exitosa",
    )
    failure_consequence: str | None = Field(
        None,
        description="Consecuencia del fracaso",
    )
    model_config = ConfigDict(extra="ignore")


class BrandNarrative(BaseEntity):
    """Represent the complete brand narrative using StoryBrand framework (Donald Miller).

    Hero -> Problem -> Guide -> Plan -> CTA -> Outcome.
    """

    hero: StoryBrandHero | None = None
    problem: StoryBrandProblem | None = None
    guide: StoryBrandGuide | None = None
    plan: list[StoryBrandPlanStep] = Field(
        default_factory=list,
        description="3-4 pasos max",
    )
    cta: StoryBrandCTA | None = None
    outcome: StoryBrandOutcome | None = None
    one_liner: str | None = Field(None, description="Síntesis StoryBrand en 1 oración")
    model_config = ConfigDict(extra="ignore")
