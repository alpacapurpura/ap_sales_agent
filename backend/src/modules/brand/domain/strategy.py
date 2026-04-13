import uuid
from typing import Any

from pydantic import ConfigDict, Field, model_validator

from src.shared.domain.base_entity import BaseEntity


class BrandCompetitor(BaseEntity):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    differentiation: str | None = None
    model_config = ConfigDict(extra="allow")


class BrandMethodologyPillar(BaseEntity):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str | None = None
    model_config = ConfigDict(extra="allow")


class BrandStrategy(BaseEntity):
    """
    Brand methodology — proprietary framework, method, or system.
    Strategic positioning fields (UVP, competitors, etc.) live in BrandPositioning.
    """

    methodology_name: str | None = Field(None, description="Name of the methodology.")
    methodology_description: str | None = Field(
        None,
        description="Description of the methodology.",
    )

    methodology_pillars: list[BrandMethodologyPillar] = Field(
        default_factory=list,
        description="Pillars of the methodology.",
    )

    model_config = ConfigDict(extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Migrar methodology_pillars_legacy -> methodology_pillars
            pillars = data.get("methodology_pillars")
            legacy_pillars = data.get("methodology_pillars_legacy")

            # Solo migramos si pillars está vacío o nulo y tenemos legacy data
            if not pillars and legacy_pillars and isinstance(legacy_pillars, list):
                new_pillars = []
                for pillar in legacy_pillars:
                    if isinstance(pillar, str):
                        new_pillars.append(
                            {
                                "id": str(uuid.uuid4()),
                                "title": pillar,
                                "description": None,
                            },
                        )
                    elif isinstance(pillar, dict):
                        if "id" not in pillar:
                            pillar["id"] = str(uuid.uuid4())
                        new_pillars.append(pillar)
                data["methodology_pillars"] = new_pillars

        return data
