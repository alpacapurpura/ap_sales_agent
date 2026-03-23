from typing import List, Optional
from pydantic import Field, ConfigDict
from src.shared.domain.base_entity import BaseEntity
from .strategy import BrandCompetitor
import uuid


class CompetitiveEnvironment(BaseEntity):
    """Brand Love Key: Competitive landscape analysis."""
    technical_enemy: Optional[str] = Field(None, description="El enemigo técnico (ej: 'El Franken-stack')")
    philosophical_enemy: Optional[str] = Field(None, description="El enemigo filosófico (ej: 'La cultura del humo')")
    direct_competitors: List[BrandCompetitor] = Field(default_factory=list)
    indirect_competitors: List[BrandCompetitor] = Field(default_factory=list)
    model_config = ConfigDict(extra='ignore')


class ConsumerInsight(BaseEntity):
    """Brand Love Key: La verdad oculta del consumidor."""
    tension: Optional[str] = Field(None, description="La verdad oculta del consumidor")
    observation: Optional[str] = Field(None, description="Lo que se observa en el mercado")
    implication: Optional[str] = Field(None, description="Lo que esto significa para la marca")
    model_config = ConfigDict(extra='ignore')


class BrandBenefits(BaseEntity):
    """Brand Love Key: Functional and emotional benefits."""
    functional_benefits: List[str] = Field(default_factory=list, description="Beneficios funcionales")
    emotional_benefits: List[str] = Field(default_factory=list, description="Beneficios emocionales")
    model_config = ConfigDict(extra='ignore')


class BrandValues(BaseEntity):
    """Brand Love Key: Core values and personality."""
    core_values: List[str] = Field(default_factory=list, description="Valores fundamentales")
    personality_traits: List[str] = Field(default_factory=list, description="Rasgos de personalidad")
    archetype: Optional[str] = Field(None, description="Arquetipo de marca")
    model_config = ConfigDict(extra='ignore')


class ReasonToBelieve(BaseEntity):
    """Brand Love Key: Evidence supporting the brand promise."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: Optional[str] = Field(None, description="dato | caso_exito | certificacion | tecnologia | proceso")
    statement: Optional[str] = Field(None, description="Declaración de la razón para creer")
    proof_url: Optional[str] = Field(None, description="URL de evidencia")
    model_config = ConfigDict(extra='ignore')


class BrandPositioning(BaseEntity):
    """
    Brand Love Key framework: Complete brand positioning model.
    Covers competitive environment, consumer insight, benefits, values, RTBs,
    discriminator and brand essence.
    """
    competitive_environment: Optional[CompetitiveEnvironment] = None
    insight: Optional[ConsumerInsight] = None
    benefits: Optional[BrandBenefits] = None
    values: Optional[BrandValues] = None
    reasons_to_believe: List[ReasonToBelieve] = Field(default_factory=list)
    discriminator: Optional[str] = Field(None, description="Diferenciador único (2-3 frases)")
    brand_essence: Optional[str] = Field(None, description="Esencia de marca en 2-3 palabras")
    unique_value_proposition: Optional[str] = Field(None, description="Propuesta de valor única")
    model_config = ConfigDict(extra='ignore')
