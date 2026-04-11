"""Tests for Offer.has_editions field — wizard-driven edition visibility."""

import uuid

from src.modules.offer.domain.enums import OfferArchetype
from src.modules.offer.domain.offer import Offer

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


def _make_offer(archetype: OfferArchetype, **overrides) -> Offer:
    defaults = {
        "tenant_id": TENANT_ID,
        "internal_sku": "TEST-SKU",
        "public_name": "Test Offer",
        "archetype": archetype,
        "headline_promise": "Transform your life",
        "primary_outcome": "Complete transformation",
        "time_to_value": "8 weeks",
        "target_avatar_match": [],
        "requires_application": False,
        "min_financial_capacity": "LOW_INCOME",
        "pricing_options": [],
        "guarantee_type": "none",
        "guarantee_terms": "",
        "status": "draft",
        "currency": "USD",
    }
    defaults.update(overrides)
    return Offer(**defaults)


class TestHasEditionsDefault:
    """Archetype-aware default for has_editions.

    Mirrors current UX expectations:
    - PROGRAMA/SERVICIO/EXPERIENCIA default to True (editions section visible)
    - PRODUCTO/MEMBRESIA default to False (editions section hidden, N/A)
    """

    def test_default_true_for_programa(self):
        offer = _make_offer(OfferArchetype.PROGRAMA)
        assert offer.has_editions is True

    def test_default_true_for_servicio(self):
        offer = _make_offer(OfferArchetype.SERVICIO)
        assert offer.has_editions is True

    def test_default_true_for_experiencia(self):
        offer = _make_offer(OfferArchetype.EXPERIENCIA)
        assert offer.has_editions is True

    def test_default_false_for_producto(self):
        offer = _make_offer(OfferArchetype.PRODUCTO)
        assert offer.has_editions is False

    def test_default_false_for_membresia(self):
        offer = _make_offer(OfferArchetype.MEMBRESIA)
        assert offer.has_editions is False


class TestHasEditionsExplicit:
    """When the wizard passes the field explicitly, domain must honor it."""

    def test_programa_can_be_set_to_false(self):
        """User said 'no cohortes' in the wizard for an evergreen program."""
        offer = _make_offer(OfferArchetype.PROGRAMA, has_editions=False)
        assert offer.has_editions is False

    def test_servicio_can_be_set_to_false(self):
        """User said 'no convocatorias' for an on-demand service."""
        offer = _make_offer(OfferArchetype.SERVICIO, has_editions=False)
        assert offer.has_editions is False

    def test_experiencia_can_be_set_to_false(self):
        """User said 'una sola salida' for a one-time event."""
        offer = _make_offer(OfferArchetype.EXPERIENCIA, has_editions=False)
        assert offer.has_editions is False

    def test_producto_cannot_opt_in(self):
        """Archetypes that don't support editions ignore has_editions=True."""
        offer = _make_offer(OfferArchetype.PRODUCTO, has_editions=True)
        assert offer.has_editions is False

    def test_membresia_cannot_opt_in(self):
        """Membresía is evergreen by definition — no editions ever."""
        offer = _make_offer(OfferArchetype.MEMBRESIA, has_editions=True)
        assert offer.has_editions is False
