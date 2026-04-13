"""Landing Repository implementation."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.landing.domain.content import LandingPageConfig
from src.modules.landing.domain.landing_page import LandingPage
from src.modules.landing.infrastructure.models.landing_model import LandingPageModel


class LandingRepository:
    """Concrete repository implementation for landing."""

    def __init__(self, db: Session) -> None:
        """Initialize LandingRepository."""
        self.db = db

    def _to_domain(self, model: LandingPageModel) -> LandingPage:
        return LandingPage(
            id=model.id,
            tenant_id=model.tenant_id,
            offer_id=model.offer_id,
            slug=model.slug,
            config=LandingPageConfig(**model.config),
            is_published=model.is_published,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def _to_model(self, entity: LandingPage) -> LandingPageModel:
        return LandingPageModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            offer_id=entity.offer_id,
            slug=entity.slug,
            config=entity.config.model_dump(mode="json"),
            is_published=entity.is_published,
        )

    def create(self, entity: LandingPage) -> LandingPage:
        """Handle create operation."""
        model = self._to_model(entity)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, landing_id: UUID) -> LandingPage | None:
        """Retrieve by id."""
        stmt = select(LandingPageModel).where(
            LandingPageModel.id == landing_id,
            LandingPageModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if model:
            return self._to_domain(model)
        return None

    def get_by_slug_and_tenant(self, slug: str, tenant_id: UUID) -> LandingPage | None:
        """Tenant-scoped slug lookup for the public endpoint."""
        stmt = select(LandingPageModel).where(
            LandingPageModel.tenant_id == tenant_id,
            LandingPageModel.slug == slug,
            LandingPageModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if model:
            return self._to_domain(model)
        return None

    def get_by_offer(self, tenant_id: UUID, offer_id: UUID) -> LandingPage | None:
        """Retrieve by offer."""
        stmt = select(LandingPageModel).where(
            LandingPageModel.tenant_id == tenant_id,
            LandingPageModel.offer_id == offer_id,
            LandingPageModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if model:
            return self._to_domain(model)
        return None

    def list_by_tenant(self, tenant_id: UUID) -> list[LandingPage]:
        """List by tenant."""
        stmt = select(LandingPageModel).where(
            LandingPageModel.tenant_id == tenant_id,
            LandingPageModel.deleted_at.is_(None),
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def update(self, entity: LandingPage) -> LandingPage:
        """Handle update operation."""
        stmt = select(LandingPageModel).where(
            LandingPageModel.id == entity.id,
            LandingPageModel.deleted_at.is_(None),
        )
        model = self.db.execute(stmt).scalars().first()
        if not model:
            msg = "Landing Page not found"
            raise ValueError(msg)

        model.slug = entity.slug
        model.config = entity.config.model_dump(mode="json")
        model.is_published = entity.is_published

        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)
