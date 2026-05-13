"""Async repository for ``model_pricing_snapshot``.

Cross-tenant by design — pricing is reference data shared across all
tenants.  Mirrors the sync ``PricingSnapshotRepository.find_active``
signature but binds to ``AsyncSession`` to avoid blocking the event loop
at 1000 concurrent LLM calls.

PR-6 / PI-1 S2 — architect decision D-NEW-1.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from luana_core_observability.persistence.models.pricing_snapshot_model import (
    ModelPricingSnapshotModel,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger(__name__)


class PricingSnapshotRepoAsync:
    """Async mirror of sync ``PricingSnapshotRepository``.

    Only exposes ``find_active`` (hot path) — ``find_at`` and
    ``close_active`` are write-path ops used by the LiteLLM sync worker
    only, so they stay on the sync repo.

    Cross-tenant by design (reference data). Queries do NOT filter by
    ``tenant_id`` — the arch-tests' tenant-isolation gate explicitly
    tolerates this for reference tables.
    """

    def __init__(self, db: AsyncSession) -> None:
        """Bind to an async session."""
        self.db = db

    async def find_active(
        self,
        *,
        provider: str,
        model: str,
    ) -> ModelPricingSnapshotModel | None:
        """Return the active snapshot for ``(provider, model)``.

        Active means ``valid_to IS NULL``.  Backed by partial unique index
        ``ix_pricing_active`` so this is always a single-row seek.
        """
        stmt = select(ModelPricingSnapshotModel).where(
            ModelPricingSnapshotModel.provider == provider,
            ModelPricingSnapshotModel.model == model,
            ModelPricingSnapshotModel.valid_to.is_(None),
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
