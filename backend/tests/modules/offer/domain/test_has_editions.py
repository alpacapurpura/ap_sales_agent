"""Tests for Offer.has_editions field — wizard-driven variant visibility.

Sprint 15.1: ``has_editions`` is now True by default for every archetype
(PROGRAMA cohorts, SERVICIO convocatorias, EXPERIENCIA salidas, PRODUCTO
SKUs, MEMBRESIA planes). The flag is still user-overridable to False so a
tenant can run an evergreen / single-variant offer without the collection
ceremony.
"""

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
    """Every archetype defaults ``has_editions=True`` post Sprint 15.1.

    The UX still decides whether to *surface* the collection view — e.g.
    MEMBRESIA with ``allow_single_variant=True`` + a single TIER plan
    collapses to the direct editor. But at the domain level the flag is
    uniformly True so ``_ensure_placeholder_edition`` can spawn the first
    variant for any archetype.
    """

    def test_default_true_for_programa(self) -> None:
        assert _make_offer(OfferArchetype.PROGRAMA).has_editions is True

    def test_default_true_for_servicio(self) -> None:
        assert _make_offer(OfferArchetype.SERVICIO).has_editions is True

    def test_default_true_for_experiencia(self) -> None:
        assert _make_offer(OfferArchetype.EXPERIENCIA).has_editions is True

    def test_default_true_for_producto(self) -> None:
        """PRODUCTO admits SKU_VARIANT (talla/color) — editions are now legitimate."""
        assert _make_offer(OfferArchetype.PRODUCTO).has_editions is True

    def test_default_true_for_membresia(self) -> None:
        """MEMBRESIA admits TIER (plan Gold/Platinum) — editions are now legitimate."""
        assert _make_offer(OfferArchetype.MEMBRESIA).has_editions is True


class TestHasEditionsExplicit:
    """When the wizard passes the field explicitly, domain must honor it."""

    def test_programa_can_be_set_to_false(self) -> None:
        """User said 'no cohortes' in the wizard for an evergreen program."""
        assert _make_offer(OfferArchetype.PROGRAMA, has_editions=False).has_editions is False

    def test_servicio_can_be_set_to_false(self) -> None:
        assert _make_offer(OfferArchetype.SERVICIO, has_editions=False).has_editions is False

    def test_experiencia_can_be_set_to_false(self) -> None:
        assert _make_offer(OfferArchetype.EXPERIENCIA, has_editions=False).has_editions is False

    def test_producto_can_be_set_to_false(self) -> None:
        """Producto sin variantes (1 ebook, 1 SKU) opt-outs via has_editions=False."""
        assert _make_offer(OfferArchetype.PRODUCTO, has_editions=False).has_editions is False

    def test_membresia_can_be_set_to_false(self) -> None:
        """Membresía con 1 plan único opt-outs via has_editions=False."""
        assert _make_offer(OfferArchetype.MEMBRESIA, has_editions=False).has_editions is False
