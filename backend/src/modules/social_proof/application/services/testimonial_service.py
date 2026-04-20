"""Testimonial service — orchestrates persistence and event publishing."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from src.modules.social_proof.domain.events import (
    TestimonialCreated,
    TestimonialSoftDeleted,
    TestimonialUpdated,
)
from src.modules.social_proof.domain.testimonial import Testimonial
from src.modules.social_proof.infrastructure.repositories.testimonial_repository import (
    TestimonialRepository,
)
from src.shared.domain.events import EventBus

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class TestimonialService:
    """Application service for Testimonial CRUD with event publishing."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db
        self.repo = TestimonialRepository(db)

    def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        author_name: str,
        **fields: object,
    ) -> Testimonial:
        """Create a Testimonial and emit ``testimonial_created``."""
        entity = Testimonial(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            author_name=author_name,
            **fields,  # type: ignore[arg-type]
        )
        created = self.repo.create(entity)
        EventBus.publish(
            TestimonialCreated.create(tenant_id=tenant_id, testimonial_id=created.id),
            session=self.db,
        )
        return created

    def update(
        self,
        tenant_id: UUID,
        testimonial_id: UUID,
        updates: dict,
    ) -> Testimonial | None:
        """Patch a Testimonial and emit ``testimonial_updated``."""
        result = self.repo.update(tenant_id, testimonial_id, updates)
        if result is not None:
            EventBus.publish(
                TestimonialUpdated.create(
                    tenant_id=tenant_id,
                    testimonial_id=testimonial_id,
                    changed_fields=list(updates.keys()),
                ),
                session=self.db,
            )
        return result

    def soft_delete(self, tenant_id: UUID, testimonial_id: UUID) -> bool:
        """Soft-delete a Testimonial, cascade placements, emit event."""
        from src.modules.social_proof.domain.enums import SourceTable
        from src.modules.social_proof.infrastructure.repositories.placement_repository import (
            PlacementRepository,
        )

        ok = self.repo.soft_delete(tenant_id, testimonial_id)
        if ok:
            PlacementRepository(self.db).cascade_soft_delete_for_source(
                tenant_id,
                SourceTable.TESTIMONIAL,
                testimonial_id,
            )
            EventBus.publish(
                TestimonialSoftDeleted.create(
                    tenant_id=tenant_id,
                    testimonial_id=testimonial_id,
                ),
                session=self.db,
            )
        return ok

    def get(self, tenant_id: UUID, testimonial_id: UUID) -> Testimonial | None:
        """Return a single Testimonial by id."""
        return self.repo.get_by_id(tenant_id, testimonial_id)

    def list_tenant(self, tenant_id: UUID) -> list[Testimonial]:
        """List all testimonials for a tenant."""
        return self.repo.list_by_tenant(tenant_id)

    def clone(
        self,
        tenant_id: UUID,
        source_id: UUID,
        user_id: UUID,
    ) -> Testimonial | None:
        """Clone an existing Testimonial for targeted customization.

        The clone is a brand-new row: later edits do NOT propagate back to
        the original. Callers are responsible for creating a placement to
        route the clone to a specific surface.
        """
        original = self.repo.get_by_id(tenant_id, source_id)
        if original is None:
            return None
        data = original.model_dump(
            exclude={"id", "tenant_id", "created_at", "updated_at", "deleted_at", "user_id"},
        )
        return self.create(tenant_id=tenant_id, user_id=user_id, **data)
