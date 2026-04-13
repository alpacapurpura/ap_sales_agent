"""Landing Service for the landing module."""

# NOTE(async-migration): This service uses Session (sync). Needs migration to AsyncSession.
from uuid import UUID

from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session

from src.modules.landing.domain.content import LandingPageConfig, SqueezeContent
from src.modules.landing.domain.enums import LandingPageArchetype
from src.modules.landing.domain.landing_page import LandingPage
from src.modules.landing.infrastructure.repositories.landing_repository import (
    LandingRepository,
)


class LandingService:
    """Manage landing operations."""

    def __init__(self, db: Session) -> None:
        """Initialize LandingService."""
        self.db = db
        self.repository = LandingRepository(db)

    def create_landing(
        self,
        tenant_id: UUID,
        slug: str,
        offer_id: UUID | None = None,
        config: LandingPageConfig | None = None,
    ) -> LandingPage:
        """Create a new landing."""
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
                    privacy_text="We respect your privacy",
                ),
            )

        landing = LandingPage(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            offer_id=offer_id,
            slug=slug,
            config=config,
            is_published=False,
        )
        return self.repository.create(landing)

    def get_landing(self, landing_id: UUID) -> LandingPage | None:
        """Retrieve landing."""
        return self.repository.get_by_id(landing_id)

    def get_landing_by_offer(
        self,
        tenant_id: UUID,
        offer_id: UUID,
    ) -> LandingPage | None:
        """Retrieve landing by offer."""
        return self.repository.get_by_offer(tenant_id, offer_id)

    def list_landings(self, tenant_id: UUID) -> list[LandingPage]:
        """List landings."""
        return self.repository.list_by_tenant(tenant_id)

    def update_landing(self, landing_id: UUID, config: dict) -> LandingPage:
        """Update landing."""
        landing = self.repository.get_by_id(landing_id)
        if not landing:
            msg = "Landing not found"
            raise ValueError(msg)

        # Merge config
        # In a real app, careful merging of nested pydantic models
        landing.config = LandingPageConfig(**config)
        return self.repository.update(landing)

    def publish_landing(self, landing_id: UUID) -> LandingPage:
        """Publish landing."""
        landing = self.repository.get_by_id(landing_id)
        if not landing:
            msg = "Landing not found"
            raise ValueError(msg)

        landing.is_published = True
        return self.repository.update(landing)

    def generate_landing_for_offer(
        self,
        tenant_id: UUID,
        offer_id: UUID,
    ) -> LandingPage:
        """Generate landing for offer."""
        # Check if landing already exists
        existing = self.repository.get_by_offer(tenant_id, offer_id)
        if existing:
            return existing

        row = (
            self.db.execute(
                sa_text(
                    "SELECT name, headline_promise, primary_outcome, marketing_pain_points"
                    " FROM products WHERE id = :oid AND tenant_id = :tid",
                ),
                {"oid": str(offer_id), "tid": str(tenant_id)},
            )
            .mappings()
            .first()
        )
        if not row:
            msg = "Offer not found"
            raise ValueError(msg)

        import json as _json

        public_name = row["name"] or "Untitled"
        headline = row["headline_promise"] or f"Discover {public_name}"
        outcome = row["primary_outcome"] or "Transform your life today"
        raw_pains = row["marketing_pain_points"] or []
        pains = _json.loads(raw_pains) if isinstance(raw_pains, str) else (raw_pains or [])

        # Create a simple slug based on offer name
        slug = f"{public_name.lower().replace(' ', '-')}-{str(offer_id)[:8]}"

        # Create default content based on offer
        content = SqueezeContent(
            headline=headline,
            subheadline=outcome,
            bullets=pains[:3] if pains else ["Solve your problem", "Save time", "Get results"],
            cta_text="Get Access Now",
            privacy_text="100% Secure",
        )

        config = LandingPageConfig(
            archetype=LandingPageArchetype.THE_SQUEEZE,
            slug=slug,
            content=content,
            seo_title=public_name,
            seo_description=headline,
        )

        return self.create_landing(tenant_id, slug, offer_id, config)

    def update_landing_for_offer(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        config_updates: dict,
    ) -> LandingPage:
        """Update landing for offer."""
        landing = self.repository.get_by_offer(tenant_id, offer_id)
        if not landing:
            msg = "Landing page not found for this offer"
            raise ValueError(msg)

        # Get current config as dict and update
        current_config_dict = landing.config.model_dump()
        current_config_dict.update(config_updates)

        # Re-validate and create new config object
        landing.config = LandingPageConfig(**current_config_dict)

        return self.repository.update(landing)

    def get_public_landing(self, slug: str, tenant_id: UUID) -> LandingPage | None:
        """Return a published landing page by slug scoped to a tenant.

        Returns None if the slug does not exist for that tenant or if the page
        is not published — callers should treat both cases as 404.
        """
        landing = self.repository.get_by_slug_and_tenant(slug=slug, tenant_id=tenant_id)
        if not landing or not landing.is_published:
            return None
        return landing

    def regenerate_block(
        self,
        current_content: str,
        block_type: str,
        context: dict | None = None,
    ) -> str:
        """Handle regenerate block operation."""
        # Mock AI generation logic
        # Returns modified content to simulate AI improvement
        return f"{current_content} (Optimized by AI)"
