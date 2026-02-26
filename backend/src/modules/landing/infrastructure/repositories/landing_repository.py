from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.landing.domain.landing_page import LandingPage
from src.modules.landing.domain.content import LandingPageConfig
from src.modules.landing.infrastructure.models.landing_model import LandingPageModel

class LandingRepository:
    def __init__(self, db: Session):
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
            updated_at=model.updated_at
        )

    def _to_model(self, entity: LandingPage) -> LandingPageModel:
        return LandingPageModel(
            id=entity.id,
            tenant_id=entity.tenant_id,
            offer_id=entity.offer_id,
            slug=entity.slug,
            config=entity.config.model_dump(mode='json'),
            is_published=entity.is_published
        )

    def create(self, entity: LandingPage) -> LandingPage:
        model = self._to_model(entity)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, landing_id: UUID) -> Optional[LandingPage]:
        model = self.db.query(LandingPageModel).filter(LandingPageModel.id == landing_id).first()
        if model:
            return self._to_domain(model)
        return None

    def get_by_slug(self, slug: str) -> Optional[LandingPage]:
        model = self.db.query(LandingPageModel).filter(LandingPageModel.slug == slug).first()
        if model:
            return self._to_domain(model)
        return None

    def list_by_tenant(self, tenant_id: UUID) -> List[LandingPage]:
        models = self.db.query(LandingPageModel).filter(LandingPageModel.tenant_id == tenant_id).all()
        return [self._to_domain(m) for m in models]

    def update(self, entity: LandingPage) -> LandingPage:
        model = self.db.query(LandingPageModel).filter(LandingPageModel.id == entity.id).first()
        if not model:
            raise ValueError("Landing Page not found")
            
        model.slug = entity.slug
        model.config = entity.config.model_dump(mode='json')
        model.is_published = entity.is_published
        
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)
