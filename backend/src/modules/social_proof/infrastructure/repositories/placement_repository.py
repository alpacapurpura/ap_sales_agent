"""Repository for Placement (social_proof_placements) with tenant isolation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from pydantic import ValidationError
from sqlalchemy import select

from src.modules.social_proof.domain.placement import Placement
from src.modules.social_proof.infrastructure.models.placement_model import (
    PlacementModel,
)
from src.shared.domain.datetime_utils import utc_now

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.social_proof.domain.enums import SourceTable, SurfaceType

logger = structlog.get_logger()


class PlacementRepository:
    """CRUD repository for Placement, tenant-scoped on every query."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db

    def create(self, entity: Placement) -> Placement:
        """Persist and return the validated entity."""
        row = PlacementModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            source_table=entity.source_table.value,
            source_id=entity.source_id,
            surface_type=entity.surface_type.value,
            surface_ref_id=entity.surface_ref_id,
            sort_order=entity.sort_order,
            is_visible=entity.is_visible,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return Placement.model_validate(row)

    def list_by_source(
        self,
        tenant_id: UUID,
        source_table: SourceTable,
        source_id: UUID,
    ) -> list[Placement]:
        """List live placements for one source row."""
        stmt = (
            select(PlacementModel)
            .where(
                PlacementModel.tenant_id == tenant_id,
                PlacementModel.source_table == source_table.value,
                PlacementModel.source_id == source_id,
                PlacementModel.deleted_at.is_(None),
            )
            .order_by(PlacementModel.sort_order.asc())
        )
        rows = self.db.execute(stmt).scalars().all()
        return [v for v in (self._safe_validate(r) for r in rows) if v is not None]

    def list_for_surface(
        self,
        tenant_id: UUID,
        surface_type: SurfaceType,
        surface_ref_id: UUID | None,
        *,
        source_table: SourceTable | None = None,
    ) -> list[Placement]:
        """List visible, live placements for one surface (optionally one source type)."""
        stmt = select(PlacementModel).where(
            PlacementModel.tenant_id == tenant_id,
            PlacementModel.surface_type == surface_type.value,
            PlacementModel.is_visible.is_(True),
            PlacementModel.deleted_at.is_(None),
        )
        if surface_ref_id is None:
            stmt = stmt.where(PlacementModel.surface_ref_id.is_(None))
        else:
            stmt = stmt.where(PlacementModel.surface_ref_id == surface_ref_id)
        if source_table is not None:
            stmt = stmt.where(PlacementModel.source_table == source_table.value)
        stmt = stmt.order_by(PlacementModel.sort_order.asc())
        rows = self.db.execute(stmt).scalars().all()
        return [v for v in (self._safe_validate(r) for r in rows) if v is not None]

    def get_by_id(self, tenant_id: UUID, placement_id: UUID) -> Placement | None:
        """Return a single entity by id, or ``None`` when not found."""
        stmt = select(PlacementModel).where(
            PlacementModel.tenant_id == tenant_id,
            PlacementModel.id == placement_id,
            PlacementModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        return self._safe_validate(row) if row else None

    def update(
        self,
        tenant_id: UUID,
        placement_id: UUID,
        updates: dict,
    ) -> Placement | None:
        """Apply partial updates and return the refreshed entity."""
        stmt = select(PlacementModel).where(
            PlacementModel.tenant_id == tenant_id,
            PlacementModel.id == placement_id,
            PlacementModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        if row is None:
            return None
        for key, value in updates.items():
            if hasattr(row, key):
                setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return Placement.model_validate(row)

    def soft_delete(self, tenant_id: UUID, placement_id: UUID) -> bool:
        """Soft-delete by setting ``deleted_at``. Returns ``True`` on success."""
        stmt = select(PlacementModel).where(
            PlacementModel.tenant_id == tenant_id,
            PlacementModel.id == placement_id,
            PlacementModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        if row is None:
            return False
        row.deleted_at = utc_now()
        self.db.commit()
        return True

    def cascade_soft_delete_for_source(
        self,
        tenant_id: UUID,
        source_table: SourceTable,
        source_id: UUID,
    ) -> int:
        """Soft-delete all placements pointing at a source row. Returns count."""
        stmt = select(PlacementModel).where(
            PlacementModel.tenant_id == tenant_id,
            PlacementModel.source_table == source_table.value,
            PlacementModel.source_id == source_id,
            PlacementModel.deleted_at.is_(None),
        )
        rows = self.db.execute(stmt).scalars().all()
        now = utc_now()
        for row in rows:
            row.deleted_at = now
        self.db.commit()
        return len(rows)

    @staticmethod
    def _safe_validate(row: PlacementModel | None) -> Placement | None:
        if row is None:
            return None
        try:
            return Placement.model_validate(row)
        except ValidationError:
            logger.warning(
                "placement.corrupt_row_skipped",
                placement_id=str(row.id),
                tenant_id=str(row.tenant_id),
            )
            return None
