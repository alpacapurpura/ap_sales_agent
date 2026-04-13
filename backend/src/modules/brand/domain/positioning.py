import uuid

from pydantic import ConfigDict, Field

from src.shared.domain.base_entity import BaseEntity

from .strategy import BrandCompetitor


class CompetitiveEnvironment(BaseEntity):
    """Brand Love Key: Competitive landscape analysis."""

    technical_enemy: str | None = Field(
        None,
        description="El enemigo técnico (ej: 'El Franken-stack')",
    )
    philosophical_enemy: str | None = Field(
        None,
        description="El enemigo filosófico (ej: 'La cultura del humo')",
    )
    direct_competitors: list[BrandCompetitor] = Field(default_factory=list)
    indirect_competitors: list[BrandCompetitor] = Field(default_factory=list)
    model_config = ConfigDict(extra="ignore")


class ConsumerInsight(BaseEntity):
    """Brand Love Key: La verdad oculta del consumidor."""

    tension: str | None = Field(None, description="La verdad oculta del consumidor")
    observation: str | None = Field(None, description="Lo que se observa en el mercado")
    implication: str | None = Field(
        None,
        description="Lo que esto significa para la marca",
    )
    model_config = ConfigDict(extra="ignore")


class BrandBenefits(BaseEntity):
    """Brand Love Key: Functional and emotional benefits."""

    functional_benefits: list[str] = Field(
        default_factory=list,
        description="Beneficios funcionales",
    )
    emotional_benefits: list[str] = Field(
        default_factory=list,
        description="Beneficios emocionales",
    )
    model_config = ConfigDict(extra="ignore")


class BrandValues(BaseEntity):
    """Brand Love Key: Core values and personality."""

    core_values: list[str] = Field(
        default_factory=list,
        description="Valores fundamentales",
    )
    personality_traits: list[str] = Field(
        default_factory=list,
        description="Rasgos de personalidad",
    )
    archetype: str | None = Field(None, description="Arquetipo de marca")
    model_config = ConfigDict(extra="ignore")


class ReasonToBelieve(BaseEntity):
    """Brand Love Key: Evidence supporting the brand promise."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str | None = Field(
        None,
        description="dato | caso_exito | certificacion | tecnologia | proceso",
    )
    statement: str | None = Field(
        None,
        description="Declaración de la razón para creer",
    )
    proof_url: str | None = Field(None, description="URL de evidencia")
    model_config = ConfigDict(extra="ignore")


class BrandPositioning(BaseEntity):
    """
    Brand Love Key framework: Complete brand positioning model.
    Covers competitive environment, consumer insight, benefits, values, RTBs,
    discriminator and brand essence.
    """

    competitive_environment: CompetitiveEnvironment | None = None
    insight: ConsumerInsight | None = None
    benefits: BrandBenefits | None = None
    values: BrandValues | None = None
    reasons_to_believe: list[ReasonToBelieve] = Field(default_factory=list)
    discriminator: str | None = Field(
        None,
        description="Diferenciador único (2-3 frases)",
    )
    brand_essence: str | None = Field(
        None,
        description="Esencia de marca en 2-3 palabras",
    )
    unique_value_proposition: str | None = Field(
        None,
        description="Propuesta de valor única",
    )
    model_config = ConfigDict(extra="ignore")
