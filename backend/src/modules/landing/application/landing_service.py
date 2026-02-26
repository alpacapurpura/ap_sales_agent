from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.landing.domain.landing_page import LandingPage
from src.modules.landing.infrastructure.repositories.landing_repository import LandingRepository
from src.modules.landing.domain.content import LandingPageConfig
from src.modules.landing.domain.enums import LandingPageArchetype

class LandingService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = LandingRepository(db)

    def create_landing(self, tenant_id: UUID, slug: str, offer_id: Optional[UUID] = None) -> LandingPage:
        import uuid
        # Default Config
        config = LandingPageConfig(
            archetype=LandingPageArchetype.THE_SQUEEZE,
            slug=slug,
            content={
                "headline": "New Landing Page", 
                "subheadline": "Edit me",
                "bullets": [],
                "cta_text": "Click me"
            }
        )
        
        landing = LandingPage(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            offer_id=offer_id,
            slug=slug,
            config=config,
            is_published=False
        )
        return self.repository.create(landing)

    def get_landing(self, landing_id: UUID) -> Optional[LandingPage]:
        return self.repository.get_by_id(landing_id)

    def list_landings(self, tenant_id: UUID) -> List[LandingPage]:
        return self.repository.list_by_tenant(tenant_id)

    def update_landing(self, landing_id: UUID, config: dict) -> LandingPage:
        landing = self.repository.get_by_id(landing_id)
        if not landing:
            raise ValueError("Landing not found")
            
        # Merge config
        # In a real app, careful merging of nested pydantic models
        landing.config = LandingPageConfig(**config)
        return self.repository.update(landing)

    def publish_landing(self, landing_id: UUID) -> LandingPage:
        landing = self.repository.get_by_id(landing_id)
        if not landing:
            raise ValueError("Landing not found")
        
        landing.is_published = True
        return self.repository.update(landing)
