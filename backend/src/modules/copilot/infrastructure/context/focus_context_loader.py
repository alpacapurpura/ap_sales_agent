"""Loads entity data for Focus Mode — used by the orchestrator."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

import structlog

from src.modules.copilot.infrastructure.persisters.brand_persister import BrandPersister
from src.modules.copilot.infrastructure.persisters.persister_registry import get_persister

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class FocusContextLoader:
    """Load entity snapshot for focus mode system prompt and tools.

    Each persister issues exactly one DB query — no N+1 queries.
    Brand data lives in a single JSONB column; offer data in a single row
    with JSONB fields for pricing, deliverables, and objections.
    """

    def __init__(self, db: Session) -> None:
        """Initialize with database session."""
        self.db = db

    def load(self, tenant_id: UUID, domain: str, entity_id: str | None) -> dict:
        """Load entity data as a flat dict.

        Args:
            tenant_id: The tenant UUID.
            domain: "offer", "brand", or "buyer_persona".
            entity_id: Entity UUID string (None for brand singleton).

        Returns:
            Flat dict of entity field values.

        Raises:
            ValueError: If domain has no registered persister.

        """
        # Raises ValueError if domain is unknown — propagate intentionally.
        persister = get_persister(domain, self.db)
        eid = UUID(entity_id) if entity_id else None
        try:
            if isinstance(persister, BrandPersister):
                # BrandPersister.load_existing is a singleton lookup (no entity_id).
                return persister.load_existing(tenant_id)
            return persister.load_existing(tenant_id, eid)
        except Exception:
            logger.exception("focus_context_load_error", domain=domain, entity_id=entity_id)
            return {}
