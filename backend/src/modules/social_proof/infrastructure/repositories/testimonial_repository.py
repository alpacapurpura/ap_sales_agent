"""Repository for Testimonial CRUD with mandatory tenant isolation."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from pydantic import ValidationError
from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

from src.modules.social_proof.domain.testimonial import Testimonial
from src.modules.social_proof.infrastructure.models.testimonial_model import (
    TestimonialModel,
)
from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger()


class TestimonialRepository:
    """CRUD repository for Testimonial, tenant-scoped on every query."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db

    def create(self, entity: Testimonial) -> Testimonial:
        """Persist and return the validated entity."""
        row = TestimonialModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            user_id=entity.user_id,
            author_name=entity.author_name,
            author_role=entity.author_role,
            author_avatar_url=entity.author_avatar_url,
            content=entity.content,
            media_type=entity.media_type.value,
            media_url=entity.media_url,
            rating=entity.rating,
            source_url=entity.source_url,
            captured_at=entity.captured_at,
            language=entity.language,
            tags=entity.tags,
            is_active=entity.is_active,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return Testimonial.model_validate(row)

    def get_by_id(self, tenant_id: UUID, entity_id: UUID) -> Testimonial | None:
        """Return a single testimonial or None."""
        stmt = select(TestimonialModel).where(
            TestimonialModel.tenant_id == tenant_id,
            TestimonialModel.id == entity_id,
            TestimonialModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        return self._safe_validate(row) if row else None

    def list_by_tenant(
        self,
        tenant_id: UUID,
        *,
        active_only: bool = True,
    ) -> list[Testimonial]:
        """List testimonials for a tenant."""
        stmt = select(TestimonialModel).where(
            TestimonialModel.tenant_id == tenant_id,
            TestimonialModel.deleted_at.is_(None),
        )
        if active_only:
            stmt = stmt.where(TestimonialModel.is_active.is_(True))
        stmt = stmt.order_by(TestimonialModel.created_at.desc())
        rows = self.db.execute(stmt).scalars().all()
        return [v for v in (self._safe_validate(r) for r in rows) if v is not None]

    def list_by_ids(self, tenant_id: UUID, ids: list[UUID]) -> list[Testimonial]:
        """Load a batch of testimonials by id for a tenant (used by the resolver)."""
        if not ids:
            return []
        stmt = select(TestimonialModel).where(
            TestimonialModel.tenant_id == tenant_id,
            TestimonialModel.id.in_(ids),
            TestimonialModel.deleted_at.is_(None),
        )
        rows = self.db.execute(stmt).scalars().all()
        return [v for v in (self._safe_validate(r) for r in rows) if v is not None]

    def update(
        self,
        tenant_id: UUID,
        entity_id: UUID,
        updates: dict,
    ) -> Testimonial | None:
        """Apply partial updates and return the refreshed entity."""
        stmt = select(TestimonialModel).where(
            TestimonialModel.tenant_id == tenant_id,
            TestimonialModel.id == entity_id,
            TestimonialModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        if row is None:
            return None
        for key, value in updates.items():
            if hasattr(row, key):
                setattr(row, key, value)
        self.db.commit()
        self.db.refresh(row)
        return Testimonial.model_validate(row)

    def soft_delete(self, tenant_id: UUID, entity_id: UUID) -> bool:
        """Soft-delete by setting deleted_at. Returns True on success."""
        stmt = select(TestimonialModel).where(
            TestimonialModel.tenant_id == tenant_id,
            TestimonialModel.id == entity_id,
            TestimonialModel.deleted_at.is_(None),
        )
        row = self.db.execute(stmt).scalars().first()
        if row is None:
            return False
        row.deleted_at = utc_now()
        self.db.commit()
        return True

    @staticmethod
    def _safe_validate(row: TestimonialModel | None) -> Testimonial | None:
        if row is None:
            return None
        try:
            return Testimonial.model_validate(row)
        except ValidationError:
            logger.warning(
                "testimonial.corrupt_row_skipped",
                testimonial_id=str(row.id),
                tenant_id=str(row.tenant_id),
            )
            return None
