"""Tests for OfferReadPort ABC and OfferReadPortImpl.

VEN-04: OfferReadPort returns offer data without cross-module domain imports.
Wave 0 stubs -- will fail until 08-01 creates production code.
"""
import pytest
from uuid import UUID


class TestOfferReadPortABC:
    """OfferReadPort ABC contract tests."""

    def test_offer_read_port_is_abstract(self):
        """OfferReadPort cannot be instantiated directly."""
        from src.modules.analytics.domain.ports import OfferReadPort
        with pytest.raises(TypeError):
            OfferReadPort()

    def test_offer_read_dto_has_required_fields(self):
        """OfferReadDTO has id, tenant_id, public_name, offer_type, value_level, pricing_type."""
        from src.modules.analytics.domain.ports import OfferReadDTO
        dto = OfferReadDTO(
            id=UUID("22222222-2222-2222-2222-222222222222"),
            tenant_id=UUID("11111111-1111-1111-1111-111111111111"),
            public_name="Test Offer",
            offer_type="self_paced_course",
            value_level="level_1_low_ticket",
            pricing_type="one_time",
            currency="USD",
        )
        assert dto.public_name == "Test Offer"
        assert dto.pricing_type == "one_time"


class TestOfferReadPortImpl:
    """OfferReadPortImpl integration tests (requires DB or mock)."""

    def test_impl_implements_port(self):
        """OfferReadPortImpl is a subclass of OfferReadPort."""
        from src.modules.analytics.domain.ports import OfferReadPort
        from src.modules.offer.application.services.offer_read_port_impl import OfferReadPortImpl
        assert issubclass(OfferReadPortImpl, OfferReadPort)

    def test_impl_does_not_import_offer_domain(self):
        """OfferReadPortImpl must NOT import from offer.domain (DDD boundary)."""
        import inspect
        from src.modules.offer.application.services import offer_read_port_impl
        source = inspect.getsource(offer_read_port_impl)
        assert "from src.modules.offer.domain" not in source, (
            "OfferReadPortImpl must not import from offer.domain -- use ProductModel directly"
        )
