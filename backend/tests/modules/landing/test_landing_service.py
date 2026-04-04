"""Tests for LandingService — create, publish, get_public, generate_for_offer."""
import uuid
import pytest
from unittest.mock import MagicMock, patch

from src.modules.landing.application.landing_service import LandingService
from src.modules.landing.domain.content import LandingPageConfig, SqueezeContent
from src.modules.landing.domain.enums import LandingPageArchetype


def _make_config(slug: str = "test-page") -> LandingPageConfig:
    return LandingPageConfig(
        archetype=LandingPageArchetype.THE_SQUEEZE,
        slug=slug,
        content=SqueezeContent(
            headline="Free Guide",
            subheadline="No more struggle",
            bullets=["B1", "B2", "B3"],
        ),
    )


class TestCreateLanding:
    def test_create_landing_with_default_config(self, db, seed_tenant, tenant_id):
        """create_landing without explicit config creates a default SQUEEZE page."""
        service = LandingService(db)
        landing = service.create_landing(tenant_id=tenant_id, slug="auto-page")

        assert landing.id is not None
        assert landing.slug == "auto-page"
        assert landing.tenant_id == tenant_id
        assert landing.is_published is False
        assert landing.config.archetype == LandingPageArchetype.THE_SQUEEZE
        assert isinstance(landing.config.content, SqueezeContent)

    def test_create_landing_with_explicit_config(self, db, seed_tenant, tenant_id):
        """create_landing with an explicit config preserves it."""
        service = LandingService(db)
        config = _make_config(slug="explicit-page")
        landing = service.create_landing(tenant_id=tenant_id, slug="explicit-page", config=config)

        assert landing.slug == "explicit-page"
        assert landing.config.archetype == LandingPageArchetype.THE_SQUEEZE

    def test_create_landing_with_offer_id(self, db, seed_tenant, tenant_id):
        """create_landing stores the offer_id when provided."""
        service = LandingService(db)
        offer_id = uuid.uuid4()
        landing = service.create_landing(tenant_id=tenant_id, slug="offer-page", offer_id=offer_id)

        assert landing.offer_id == offer_id

    def test_create_landing_is_not_published_by_default(self, db, seed_tenant, tenant_id):
        service = LandingService(db)
        landing = service.create_landing(tenant_id=tenant_id, slug="unpublished")
        assert landing.is_published is False


class TestPublishLanding:
    def test_publish_landing_sets_is_published_true(self, db, seed_tenant, tenant_id):
        service = LandingService(db)
        landing = service.create_landing(tenant_id=tenant_id, slug="to-publish")
        assert landing.is_published is False

        published = service.publish_landing(landing.id)
        assert published.is_published is True

    def test_publish_nonexistent_landing_raises(self, db, seed_tenant):
        service = LandingService(db)
        with pytest.raises(ValueError, match="Landing not found"):
            service.publish_landing(uuid.uuid4())

    def test_publish_landing_persists_state(self, db, seed_tenant, tenant_id):
        """After publishing, re-fetching by ID still returns is_published=True."""
        service = LandingService(db)
        landing = service.create_landing(tenant_id=tenant_id, slug="persist-pub")
        service.publish_landing(landing.id)

        fetched = service.get_landing(landing.id)
        assert fetched.is_published is True


class TestGetPublicLanding:
    def test_get_public_landing_returns_published_page(self, db, seed_tenant, tenant_id):
        """get_public_landing returns a page only if it is published."""
        service = LandingService(db)
        landing = service.create_landing(tenant_id=tenant_id, slug="public-page")
        service.publish_landing(landing.id)

        result = service.get_public_landing(slug="public-page", tenant_id=tenant_id)
        assert result is not None
        assert result.slug == "public-page"
        assert result.is_published is True

    def test_get_public_landing_unpublished_returns_none(self, db, seed_tenant, tenant_id):
        """Unpublished pages MUST return None — security requirement."""
        service = LandingService(db)
        service.create_landing(tenant_id=tenant_id, slug="hidden-page")

        result = service.get_public_landing(slug="hidden-page", tenant_id=tenant_id)
        assert result is None

    def test_get_public_landing_nonexistent_slug_returns_none(self, db, seed_tenant, tenant_id):
        service = LandingService(db)
        result = service.get_public_landing(slug="ghost", tenant_id=tenant_id)
        assert result is None

    def test_get_public_landing_tenant_isolation(self, db, seed_tenant, seed_other_tenant, tenant_id, other_tenant_id):
        """Tenant A cannot access tenant B's published page by providing tenant A's ID."""
        service = LandingService(db)
        landing = service.create_landing(tenant_id=other_tenant_id, slug="b-public-page")
        service.publish_landing(landing.id)

        # Tenant A tries to access tenant B's page
        result = service.get_public_landing(slug="b-public-page", tenant_id=tenant_id)
        assert result is None


class TestGenerateLandingForOffer:
    def test_generate_for_offer_creates_landing_when_none_exists(self, db, seed_tenant, tenant_id):
        """generate_landing_for_offer creates a new landing linked to the offer."""
        service = LandingService(db)
        offer_id = uuid.uuid4()

        # Mock the OfferRepository.get_by_id call
        mock_offer = MagicMock()
        mock_offer.id = offer_id
        mock_offer.public_name = "My Course"
        mock_offer.headline_promise = "Transform your life in 30 days"
        mock_offer.primary_outcome = "6-figure income"
        mock_offer.marketing_pain_points = ["No time", "No system", "No results"]

        with patch(
            "src.modules.landing.application.landing_service.OfferRepository"
        ) as MockOfferRepo:
            MockOfferRepo.return_value.get_by_id.return_value = mock_offer
            landing = service.generate_landing_for_offer(tenant_id=tenant_id, offer_id=offer_id)

        assert landing is not None
        assert landing.offer_id == offer_id
        assert landing.tenant_id == tenant_id
        assert landing.config.archetype == LandingPageArchetype.THE_SQUEEZE
        assert "my-course" in landing.slug

    def test_generate_for_offer_returns_existing_when_already_exists(self, db, seed_tenant, tenant_id):
        """If a landing already exists for this offer, return it without creating a new one."""
        service = LandingService(db)
        offer_id = uuid.uuid4()
        # Create an existing landing for this offer
        existing = service.create_landing(
            tenant_id=tenant_id,
            slug="existing-offer-page",
            offer_id=offer_id,
        )

        with patch(
            "src.modules.landing.application.landing_service.OfferRepository"
        ) as MockOfferRepo:
            result = service.generate_landing_for_offer(tenant_id=tenant_id, offer_id=offer_id)
            # OfferRepository should NOT be called since existing was found
            MockOfferRepo.return_value.get_by_id.assert_not_called()

        assert result.id == existing.id

    def test_generate_for_offer_uses_pain_points_as_bullets(self, db, seed_tenant, tenant_id):
        """generate_landing_for_offer uses the offer's marketing pain points as bullets."""
        service = LandingService(db)
        offer_id = uuid.uuid4()

        mock_offer = MagicMock()
        mock_offer.id = offer_id
        mock_offer.public_name = "Offer X"
        mock_offer.headline_promise = "headline"
        mock_offer.primary_outcome = "outcome"
        mock_offer.marketing_pain_points = ["Pain 1", "Pain 2", "Pain 3"]

        with patch(
            "src.modules.landing.application.landing_service.OfferRepository"
        ) as MockOfferRepo:
            MockOfferRepo.return_value.get_by_id.return_value = mock_offer
            landing = service.generate_landing_for_offer(tenant_id=tenant_id, offer_id=offer_id)

        content = landing.config.content
        assert isinstance(content, SqueezeContent)
        assert "Pain 1" in content.bullets

    def test_generate_for_offer_nonexistent_offer_raises(self, db, seed_tenant, tenant_id):
        """generate_landing_for_offer raises ValueError when offer does not exist."""
        service = LandingService(db)

        with patch(
            "src.modules.landing.application.landing_service.OfferRepository"
        ) as MockOfferRepo:
            MockOfferRepo.return_value.get_by_id.return_value = None
            with pytest.raises(ValueError, match="Offer not found"):
                service.generate_landing_for_offer(tenant_id=tenant_id, offer_id=uuid.uuid4())
