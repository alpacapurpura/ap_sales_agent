# TODO(async-migration): This service uses Session (sync). Needs migration to AsyncSession.
from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.landing.domain.landing_page import LandingPage
from src.modules.landing.infrastructure.repositories.landing_repository import LandingRepository
from src.modules.landing.domain.content import LandingPageConfig, SqueezeContent
from src.modules.landing.domain.enums import LandingPageArchetype
from src.modules.offer.infrastructure.repositories.offer_repository import OfferRepository

class LandingService:
    def __init__(self, db: Session):
        self.db = db
        self.repository = LandingRepository(db)

    def create_landing(self, tenant_id: UUID, slug: str, offer_id: Optional[UUID] = None, config: Optional[LandingPageConfig] = None) -> LandingPage:
        import uuid
        # Default Config
        if not config:
            config = LandingPageConfig(
                archetype=LandingPageArchetype.THE_SQUEEZE,
                slug=slug,
                content=SqueezeContent(
                    headline="New Landing Page", 
                    subheadline="Edit me",
                    bullets=["Benefit 1", "Benefit 2", "Benefit 3"],
                    cta_text="Click me",
                    privacy_text="We respect your privacy"
                )
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

    def get_landing_by_offer(self, tenant_id: UUID, offer_id: UUID) -> Optional[LandingPage]:
        return self.repository.get_by_offer(tenant_id, offer_id)

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

    def generate_landing_for_offer(self, tenant_id: UUID, offer_id: UUID) -> LandingPage:
        # Check if landing already exists
        existing = self.repository.get_by_offer(tenant_id, offer_id)
        if existing:
            return existing

        offer_repo = OfferRepository(self.db)
        offer = offer_repo.get_by_id(offer_id, tenant_id)
        if not offer:
            raise ValueError("Offer not found")
        
        # Create a simple slug based on offer name
        slug = f"{offer.public_name.lower().replace(' ', '-')}-{str(offer.id)[:8]}"
        
        # Create default content based on offer
        content = SqueezeContent(
            headline=offer.headline_promise or f"Discover {offer.public_name}",
            subheadline=offer.primary_outcome or "Transform your life today",
            bullets=offer.marketing_pain_points[:3] if offer.marketing_pain_points else ["Solve your problem", "Save time", "Get results"],
            cta_text="Get Access Now",
            privacy_text="100% Secure"
        )
        
        config = LandingPageConfig(
            archetype=LandingPageArchetype.THE_SQUEEZE,
            slug=slug,
            content=content,
            seo_title=offer.public_name,
            seo_description=offer.headline_promise
        )
        
        return self.create_landing(tenant_id, slug, offer_id, config)

    def update_landing_for_offer(self, tenant_id: UUID, offer_id: UUID, config_updates: dict) -> LandingPage:
        landing = self.repository.get_by_offer(tenant_id, offer_id)
        if not landing:
            raise ValueError("Landing page not found for this offer")
            
        # Get current config as dict and update
        current_config_dict = landing.config.model_dump()
        current_config_dict.update(config_updates)
        
        # Re-validate and create new config object
        landing.config = LandingPageConfig(**current_config_dict)
        
        return self.repository.update(landing)

    def get_public_landing(self, slug: str, tenant_id: UUID) -> Optional[LandingPage]:
        """Return a published landing page by slug scoped to a tenant.

        Returns None if the slug does not exist for that tenant or if the page
        is not published — callers should treat both cases as 404.
        """
        landing = self.repository.get_by_slug_and_tenant(slug=slug, tenant_id=tenant_id)
        if not landing or not landing.is_published:
            return None
        return landing

    def regenerate_block(self, current_content: str, block_type: str, context: Optional[dict] = None) -> str:
        # Mock AI generation logic
        # Returns modified content to simulate AI improvement
        return f"{current_content} (Optimized by AI)"
