from typing import List, Optional
from pydantic import Field, ConfigDict
from src.shared.domain.base_entity import BaseEntity
import uuid


class CreativeConcept(BaseEntity):
    """A creative concept that ties multiple assets together."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: Optional[str] = Field(None, description="Nombre del concepto creativo")
    description: Optional[str] = None
    tone: Optional[str] = Field(None, description="Tono del concepto (ej: 'Empático + Provocador')")
    model_config = ConfigDict(extra='ignore')


class FunnelAsset(BaseEntity):
    """A communication asset tied to a funnel stage."""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    funnel_stage: Optional[str] = Field(None, description="TOFU | MOFU | BOFU | retention")
    asset_type: Optional[str] = Field(None, description="Free-form: reel, carousel, email, etc.")
    title: Optional[str] = None
    idea: Optional[str] = Field(None, description="Brief creativo")
    copy_draft: Optional[str] = Field(None, description="Copy sugerido")
    objective: Optional[str] = Field(None, description="Awareness | Engagement | Conversion | Retention")
    concept_id: Optional[str] = Field(None, description="Link a CreativeConcept.id")
    status: Optional[str] = Field("draft", description="draft | approved | produced")
    model_config = ConfigDict(extra='ignore')


class CommunicationAssets(BaseEntity):
    """
    Dynamic funnel-stage communication assets.
    Groups creative concepts and individual assets by funnel stage.
    """
    creative_concepts: List[CreativeConcept] = Field(default_factory=list)
    assets: List[FunnelAsset] = Field(default_factory=list)
    custom_asset_types: List[str] = Field(default_factory=list, description="Extensible: usuario agrega nuevos tipos")
    model_config = ConfigDict(extra='ignore')
