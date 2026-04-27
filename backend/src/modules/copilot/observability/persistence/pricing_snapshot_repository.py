"""Repository for ``model_pricing_snapshot``.

**Cross-tenant by design.** Pricing is reference data — every tenant
shares the same provider/model rates — so queries here do not filter by
tenant_id. The arch-tests' tenant-isolation gate explicitly tolerates
this for reference tables (see ``ARCHITECTURE.md`` §4.2).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import or_, select, update

from src.modules.copilot.observability.persistence.models.pricing_snapshot_model import (
    ModelPricingSnapshotModel,
)

if TYPE_CHECKING:
    import datetime as dt

    from sqlalchemy.orm import Session

logger = structlog.get_logger()


class PricingSnapshotRepository:
    """Persist and query pricing snapshots."""

    def __init__(self, db: Session) -> None:
        """Bind the repository to a session."""
        self.db = db

    def add(self, **kwargs: Any) -> ModelPricingSnapshotModel:  # noqa: ANN401 — column kwargs vary
        """Insert a new pricing snapshot row."""
        row = ModelPricingSnapshotModel(**kwargs)
        self.db.add(row)
        return row

    def find_active(self, *, provider: str, model: str) -> ModelPricingSnapshotModel | None:
        """Return the row with ``valid_to IS NULL`` for ``(provider, model)``.

        Backed by the partial unique index ``ix_pricing_active`` so this
        is the resolver's hot path.
        """
        stmt = select(ModelPricingSnapshotModel).where(
            ModelPricingSnapshotModel.provider == provider,
            ModelPricingSnapshotModel.model == model,
            ModelPricingSnapshotModel.valid_to.is_(None),
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def find_at(
        self,
        *,
        provider: str,
        model: str,
        at_ts: dt.datetime,
    ) -> ModelPricingSnapshotModel | None:
        """Return the snapshot in effect for ``at_ts``.

        That is: ``valid_from <= at_ts AND (valid_to IS NULL OR valid_to > at_ts)``.

        The ``valid_to`` filter runs in SQL (not Python) so naive vs. aware
        ``datetime`` representation between dialects (SQLite drops tzinfo,
        Postgres preserves it) doesn't break the comparison.
        """
        stmt = (
            select(ModelPricingSnapshotModel)
            .where(
                ModelPricingSnapshotModel.provider == provider,
                ModelPricingSnapshotModel.model == model,
                ModelPricingSnapshotModel.valid_from <= at_ts,
                or_(
                    ModelPricingSnapshotModel.valid_to.is_(None),
                    ModelPricingSnapshotModel.valid_to > at_ts,
                ),
            )
            .order_by(ModelPricingSnapshotModel.valid_from.desc())
            .limit(1)
        )
        return self.db.execute(stmt).scalar_one_or_none()

    def close_active(
        self,
        *,
        provider: str,
        model: str,
        at_ts: dt.datetime,
    ) -> ModelPricingSnapshotModel | None:
        """Set ``valid_to = at_ts`` on the active row, if any. Returns the closed row."""
        active = self.find_active(provider=provider, model=model)
        if active is None:
            return None
        stmt = update(ModelPricingSnapshotModel).where(ModelPricingSnapshotModel.id == active.id).values(valid_to=at_ts)
        self.db.execute(stmt)
        # Refresh in-memory state so callers see the new valid_to without
        # an extra round-trip.
        active.valid_to = at_ts
        return active
