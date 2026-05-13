"""Landing Service for the landing module."""

# NOTE(async-migration): This service uses Session (sync). Needs migration to AsyncSession.
from uuid import UUID

from luana_core_landing.application.landing_content_builders import _resolve_content
from luana_core_landing.domain.content import LandingPageConfig, SqueezeContent
from luana_core_landing.domain.enums import LandingPageArchetype
from luana_core_landing.domain.landing_page import LandingPage
from luana_core_landing.infrastructure.repositories.landing_repository import (
    LandingRepository,
)
from sqlalchemy import text as sa_text
from sqlalchemy.orm import Session


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

    @staticmethod
    def _select_landing_archetype_from_preset(preset_id: str | None) -> LandingPageArchetype:
        """Pick a landing archetype from the offer's ``OfferTypePreset`` flags.

        The selector uses the preset's ``default_flags`` to branch among the
        six existing landing archetypes — *not* the offer's ``archetype`` tag
        directly. This aligns the landing with the business intent the
        tenant captured in the wizard (lead capture, high-ticket, recurring,
        event) rather than the fulfilment model alone.

        Catalog access goes through ``shared/links/ports/offer.py`` so the
        DDD boundary is preserved (no direct cross-module import from
        ``landing`` into ``offer``).

        Resolution order (first match wins):

        1. ``IS_LEAD_MAGNET`` → ``THE_SQUEEZE`` (opt-in focused)
        2. ``REQUIRES_START_DATE`` → ``THE_EVENT`` (date-anchored)
        3. ``HIGH_TICKET`` → ``THE_TRANSFORMER`` (long-form with proof)
        4. ``RECURRING_BILLING`` → ``THE_VELVET_ROPE`` (membership feel)
        5. Unknown / no preset → ``THE_BROCHURE`` (safe general default)
        """
        from luana_core_platform.links.ports.offer import (
            get_offer_type_preset,
            get_preset_flag_values,
        )

        preset = get_offer_type_preset(preset_id)
        if preset is None:
            return LandingPageArchetype.THE_BROCHURE
        preset_flag = get_preset_flag_values()
        flags = set(preset.default_flags)  # type: ignore[attr-defined]
        if preset_flag.IS_LEAD_MAGNET in flags:
            return LandingPageArchetype.THE_SQUEEZE
        if preset_flag.REQUIRES_START_DATE in flags:
            return LandingPageArchetype.THE_EVENT
        if preset_flag.HIGH_TICKET in flags:
            return LandingPageArchetype.THE_TRANSFORMER
        if preset_flag.RECURRING_BILLING in flags:
            return LandingPageArchetype.THE_VELVET_ROPE
        return LandingPageArchetype.THE_BROCHURE

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
                    # Core identity fields
                    "SELECT name, headline_promise, primary_outcome, marketing_pain_points,"
                    " preset_id,"
                    # Promise narrative fields
                    " before_state, after_state, why_now, measurable_outcomes,"
                    # Psychology narrative fields
                    " objections, marketing_desires, cultural_trust_barriers,"
                    " emotional_triggers, status_drivers, regret_scenarios,"
                    # Closing narrative fields
                    " refund_process_description, urgency_drivers, scarcity_reason_honest,"
                    " bonus_if_act_now, final_push_copy,"
                    # Supporting fields for content builders
                    " guarantee_terms, guarantee_type, support_duration_days,"
                    " deliverables, pricing"
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

        public_name: str = row["name"] or "Mi oferta"
        preset_id = row["preset_id"]

        # Create a simple slug based on offer name
        slug = f"{public_name.lower().replace(' ', '-')}-{str(offer_id)[:8]}"

        # Resolve landing archetype from preset flags. Lead magnets stay on
        # THE_SQUEEZE regardless (explicit opt-in focus). Other archetypes
        # pick a more fitting template when possible, fallback to SQUEEZE.
        landing_archetype = self._select_landing_archetype_from_preset(preset_id)

        # Strategy pattern: delegate content building to per-archetype builder.
        # _resolve_content() applies graceful degradation — if the specific
        # builder returns None (missing required fields), falls back to SQUEEZE.
        actual_archetype, content = _resolve_content(landing_archetype, row)

        config = LandingPageConfig(
            archetype=actual_archetype,
            slug=slug,
            content=content,
            seo_title=public_name,
            seo_description=row.get("headline_promise") or public_name,
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
