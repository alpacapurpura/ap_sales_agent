"""Placement service — manages the M:N link between source rows and surfaces."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.modules.social_proof.domain.events import (
    PlacementAdded,
    PlacementRemoved,
    PlacementReordered,
)
from src.modules.social_proof.domain.placement import Placement
from src.modules.social_proof.infrastructure.repositories.placement_repository import (
    PlacementRepository,
)
from src.shared.domain.events import EventBus

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.social_proof.domain.enums import SourceTable, SurfaceType


class PlacementService:
    """Application service for placement M:N management with events."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db
        self.repo = PlacementRepository(db)

    def add(
        self,
        *,
        tenant_id: UUID,
        source_table: SourceTable,
        source_id: UUID,
        surface_type: SurfaceType,
        surface_ref_id: UUID | None,
        sort_order: int = 0,
        is_visible: bool = True,
    ) -> Placement:
        """Link a source row to a surface. Emits ``placement_added``."""
        entity = Placement(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            source_table=source_table,
            source_id=source_id,
            surface_type=surface_type,
            surface_ref_id=surface_ref_id,
            sort_order=sort_order,
            is_visible=is_visible,
        )
        created = self.repo.create(entity)
        EventBus.publish(
            PlacementAdded.create(
                tenant_id=tenant_id,
                placement_id=created.id,
                source_table=source_table,
                source_id=source_id,
                surface_type=surface_type,
                surface_ref_id=surface_ref_id,
            ),
            session=self.db,
        )
        return created

    def remove(self, tenant_id: UUID, placement_id: UUID) -> bool:
        """Soft-delete a placement. Source row stays intact. Emits ``placement_removed``."""
        ok = self.repo.soft_delete(tenant_id, placement_id)
        if ok:
            EventBus.publish(
                PlacementRemoved.create(
                    tenant_id=tenant_id,
                    placement_id=placement_id,
                ),
                session=self.db,
            )
        return ok

    def update(
        self,
        tenant_id: UUID,
        placement_id: UUID,
        updates: dict,
    ) -> Placement | None:
        """Update sort_order / is_visible. Emits ``placement_reordered``."""
        result = self.repo.update(tenant_id, placement_id, updates)
        if result is not None:
            EventBus.publish(
                PlacementReordered.create(
                    tenant_id=tenant_id,
                    placement_id=placement_id,
                    changed_fields=list(updates.keys()),
                ),
                session=self.db,
            )
        return result

    def list_for_source(
        self,
        tenant_id: UUID,
        source_table: SourceTable,
        source_id: UUID,
    ) -> list[Placement]:
        """Return every live placement that points at the given source row."""
        return self.repo.list_by_source(tenant_id, source_table, source_id)
