"""BrandDataPort — cross-module port for brand knowledge access.

``sales_agent`` uses this to build the agent identity document without
importing brand repositories directly.

Canonical implementation: ``brand.application.services.brand_data_adapter``
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from pydantic import BaseModel

if TYPE_CHECKING:
    from uuid import UUID


class BrandKnowledgeDTO(BaseModel):
    """Pre-serialized brand knowledge for the sales agent identity builder."""

    brand_data: dict = {}
    avatars: list[dict] = []
    personality_profile: dict | None = None


class BrandDataPort(ABC):
    """Port for accessing brand knowledge across module boundaries."""

    @abstractmethod
    def get_brand_knowledge(self, tenant_id: UUID) -> BrandKnowledgeDTO:
        """Return all brand data needed for the agent identity builder."""
        ...


def create_brand_data_port(db: object) -> BrandDataPort:
    """Create a BrandDataPort instance.

    Lazy-imports the concrete adapter from brand module.
    """
    from src.modules.brand.application.services.brand_data_adapter import (
        BrandDataAdapter,
    )

    return BrandDataAdapter(db)
