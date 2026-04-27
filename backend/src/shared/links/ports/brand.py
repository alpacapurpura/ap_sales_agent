"""BrandDataPort — cross-module port for brand knowledge access.

``sales_agent`` uses this to build the agent identity document without
importing brand repositories directly.

``BrandFieldApplyPort`` is the write-side counterpart used by ``copilot``
to apply ``ProposalCard`` updates server-side without importing
``BrandRepository`` directly (B22-FP1 — preserves the F1 ratchet against
new ``copilot -> module`` imports).

Canonical implementations: ``brand.application.services.brand_data_adapter``
and ``brand.application.services.brand_field_apply_adapter``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any

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


class BrandFieldApplyPort(ABC):
    """Port for writing a single brand field across module boundaries.

    Used by the copilot ``MutationApplyService`` to persist ProposalCard
    updates targeting brand fields without taking a direct dependency on
    ``BrandRepository``.
    """

    @abstractmethod
    def apply_field(
        self,
        tenant_id: UUID,
        field_path: str,
        new_value: Any,  # noqa: ANN401  # JSONB-shaped value
    ) -> None:
        """Persist ``new_value`` at ``field_path`` for ``tenant_id``."""
        ...


def create_brand_data_port(db: object) -> BrandDataPort:
    """Create a BrandDataPort instance.

    Lazy-imports the concrete adapter from brand module.
    """
    from src.modules.brand.application.services.brand_data_adapter import (
        BrandDataAdapter,
    )

    return BrandDataAdapter(db)


def create_brand_field_apply_port(db: object) -> BrandFieldApplyPort:
    """Create a BrandFieldApplyPort instance (B22-FP1).

    Lazy-imports the concrete adapter so callers (copilot) only depend on
    ``shared/links/ports`` and the F1 ratchet stays clean.
    """
    from src.modules.brand.application.services.brand_field_apply_adapter import (
        BrandFieldApplyAdapter,
    )

    return BrandFieldApplyAdapter(db)
