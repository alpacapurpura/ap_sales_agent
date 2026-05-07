"""Tests for load_eval_tenant() and TenantContext.

Status in T-1: MIXED (some GREEN, some RED expected until T-3 creates YAMLs)
  - test_loads_all_5_archetype_slugs     → RED (no tenant YAML dirs yet)
  - test_dialect_code_per_archetype_matches_table → RED (no tenant YAML dirs yet)
  - test_offer_ladder_no_lead_magnet_emits_warning_proceeds_load → RED (no tenant dirs)
  - test_buyer_personas_count_3_per_tenant → RED (no tenant YAML dirs yet)
  - test_pricing_currency_pen_for_all   → RED (no tenant YAML dirs yet)
  - test_loader_raises_on_missing_archetype_slug → GREEN (pure loader logic)

Acceptance A3 confirms: "Tests baseline RED expected until T-3."
"""

from __future__ import annotations

import pytest
import structlog.testing

from tests.fixtures.eval.tenants.loader import (
    ARCHETYPE_DIALECT_MAP,
    ARCHETYPE_SLUGS,
    TenantContext,
    load_eval_tenant,
)

# ---------------------------------------------------------------------------
# Parametrized test fixtures (declared via conftest.py pytest_generate_tests)
# ---------------------------------------------------------------------------


# ---------------------------------------------------------------------------
# Tests GREEN in T-1
# ---------------------------------------------------------------------------


def test_loader_raises_on_missing_archetype_slug() -> None:
    """load_eval_tenant() with an unknown slug must raise ValueError immediately."""
    with pytest.raises(ValueError, match="Unknown archetype_slug"):
        load_eval_tenant("tenant_does_not_exist")


# ---------------------------------------------------------------------------
# Tests RED in T-1 — unblocked when T-3 creates the YAML files
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("archetype_slug", list(ARCHETYPE_SLUGS))
def test_loads_all_5_archetype_slugs(archetype_slug: str) -> None:
    """load_eval_tenant() must return a TenantContext for each ratified slug.

    RED until T-3 creates the 6 YAML files per archetype folder.
    Each loaded context must:
      - be a TenantContext instance
      - have non-empty brand, personality_profile, offer_ladder, pricing,
        buyer_personas, communication_assets
      - have archetype_slug == the requested slug
    """
    ctx = load_eval_tenant(archetype_slug)
    assert isinstance(ctx, TenantContext)
    assert ctx.archetype_slug == archetype_slug
    assert ctx.brand  # non-empty dict
    assert ctx.personality_profile
    assert ctx.offer_ladder is not None
    assert ctx.pricing
    assert ctx.buyer_personas
    assert ctx.communication_assets


@pytest.mark.parametrize("archetype_slug", list(ARCHETYPE_SLUGS))
def test_dialect_code_per_archetype_matches_table(archetype_slug: str) -> None:
    """dialect_code on TenantContext must match the ratified ARCHETYPE_DIALECT_MAP.

    RED until T-3 creates personality_profile.yaml with dialect_code field.
    """
    expected = ARCHETYPE_DIALECT_MAP[archetype_slug]
    ctx = load_eval_tenant(archetype_slug)
    assert ctx.dialect_code == expected, (
        f"Expected dialect_code='{expected}' for {archetype_slug}, got '{ctx.dialect_code}'"
    )


def test_offer_ladder_no_lead_magnet_emits_warning_proceeds_load() -> None:
    """A4 and A5 have no L0 → loader emits warning but succeeds.

    A1/A2/A3 have L0 → no warning emitted.

    RED until T-3 creates the offer_ladder.yaml files with correct L0 presence.
    """
    # Archetypes WITHOUT lead magnet (A4+A5 per spec)
    no_lead_magnet_slugs = [
        "tenant_agencia_growth_video",
        "tenant_agencia_automatizacion_ia",
    ]
    # Archetypes WITH lead magnet (A1+A2+A3 per spec)
    with_lead_magnet_slugs = [
        "tenant_coach_lat",
        "tenant_medicina_estetica",
        "tenant_clinica_dental",
    ]

    # A4 + A5: warning emitted, load succeeds, has_lead_magnet=False
    for slug in no_lead_magnet_slugs:
        with structlog.testing.capture_logs() as cap:
            ctx = load_eval_tenant(slug)
        assert not ctx.offer_ladder.has_lead_magnet, f"{slug} should NOT have has_lead_magnet=True"
        warning_events = [e for e in cap if e.get("event") == "offer_ladder_missing_lead_magnet"]
        assert warning_events, f"Expected structlog warning 'offer_ladder_missing_lead_magnet' for {slug}"
        assert warning_events[0].get("tenant_slug") == slug

    # A1 + A2 + A3: no warning emitted, has_lead_magnet=True
    for slug in with_lead_magnet_slugs:
        with structlog.testing.capture_logs() as cap:
            ctx = load_eval_tenant(slug)
        assert ctx.offer_ladder.has_lead_magnet, f"{slug} SHOULD have has_lead_magnet=True"
        warning_events = [e for e in cap if e.get("event") == "offer_ladder_missing_lead_magnet"]
        assert not warning_events, f"Unexpected warning 'offer_ladder_missing_lead_magnet' for {slug}"


@pytest.mark.parametrize("archetype_slug", list(ARCHETYPE_SLUGS))
def test_buyer_personas_count_3_per_tenant(archetype_slug: str) -> None:
    """Each tenant must have exactly 3 buyer personas (2 base + 1 adversarial).

    RED until T-3 creates buyer_personas.yaml files.
    """
    ctx = load_eval_tenant(archetype_slug)
    personas = ctx.buyer_personas.get("personas", [])
    assert len(personas) == 3, (
        f"Expected exactly 3 buyer personas for {archetype_slug}, "
        f"got {len(personas)}. (Q8 ratified: 2 base + 1 adversarial)"
    )


@pytest.mark.parametrize("archetype_slug", list(ARCHETYPE_SLUGS))
def test_pricing_currency_pen_for_all(archetype_slug: str) -> None:
    """All 5 tenants must use currency=PEN (Q3 ratified single-currency seed).

    RED until T-3 creates pricing.yaml files.
    """
    ctx = load_eval_tenant(archetype_slug)
    currency = ctx.pricing.get("currency")
    assert currency == "PEN", (
        f"Expected currency='PEN' for {archetype_slug}, got '{currency}'. (Q3: single-currency PEN for test isolation)"
    )
