from typing import List, Optional, Any
from pydantic import Field, ConfigDict, model_validator
from src.shared.domain.base_entity import BaseEntity
import uuid

class BrandCompetitor(BaseEntity):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    differentiation: Optional[str] = None
    model_config = ConfigDict(extra='allow')

class BrandMethodologyPillar(BaseEntity):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    model_config = ConfigDict(extra='allow')

class BrandStrategy(BaseEntity):
    """
    Brand methodology — proprietary framework, method, or system.
    Strategic positioning fields (UVP, competitors, etc.) live in BrandPositioning.
    """
    methodology_name: Optional[str] = Field(None, description="Name of the methodology.")
    methodology_description: Optional[str] = Field(None, description="Description of the methodology.")

    methodology_pillars: List[BrandMethodologyPillar] = Field(default_factory=list, description="Pillars of the methodology.")

    model_config = ConfigDict(extra='ignore')

    @model_validator(mode='before')
    @classmethod
    def migrate_legacy_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            # Migrar methodology_pillars_legacy -> methodology_pillars
            pillars = data.get('methodology_pillars')
            legacy_pillars = data.get('methodology_pillars_legacy')

            # Solo migramos si pillars está vacío o nulo y tenemos legacy data
            if not pillars and legacy_pillars and isinstance(legacy_pillars, list):
                new_pillars = []
                for pillar in legacy_pillars:
                    if isinstance(pillar, str):
                         new_pillars.append({
                            "id": str(uuid.uuid4()),
                            "title": pillar,
                            "description": None
                        })
                    elif isinstance(pillar, dict):
                        if "id" not in pillar:
                            pillar["id"] = str(uuid.uuid4())
                        new_pillars.append(pillar)
                data['methodology_pillars'] = new_pillars

        return data
