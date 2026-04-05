import uuid

from pydantic import ConfigDict, Field

from src.shared.domain.base_entity import BaseEntity


class CreativeConcept(BaseEntity):
    """A creative concept that ties multiple assets together."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str | None = Field(None, description="Nombre del concepto creativo")
    description: str | None = None
    tone: str | None = Field(
        None, description="Tono del concepto (ej: 'Empático + Provocador')"
    )
    model_config = ConfigDict(extra="ignore")


class FunnelAsset(BaseEntity):
    """A communication asset tied to a funnel stage."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    funnel_stage: str | None = Field(None, description="TOFU | MOFU | BOFU | retention")
    asset_type: str | None = Field(
        None, description="Free-form: reel, carousel, email, etc."
    )
    title: str | None = None
    idea: str | None = Field(None, description="Brief creativo")
    copy_draft: str | None = Field(None, description="Copy sugerido")
    objective: str | None = Field(
        None, description="Awareness | Engagement | Conversion | Retention"
    )
    concept_id: str | None = Field(None, description="Link a CreativeConcept.id")
    status: str | None = Field("draft", description="draft | approved | produced")
    model_config = ConfigDict(extra="ignore")


class CommunicationAssets(BaseEntity):
    """
    Dynamic funnel-stage communication assets.
    Groups creative concepts and individual assets by funnel stage.
    """

    creative_concepts: list[CreativeConcept] = Field(default_factory=list)
    assets: list[FunnelAsset] = Field(default_factory=list)
    custom_asset_types: list[str] = Field(
        default_factory=list, description="Extensible: usuario agrega nuevos tipos"
    )
    model_config = ConfigDict(extra="ignore")
