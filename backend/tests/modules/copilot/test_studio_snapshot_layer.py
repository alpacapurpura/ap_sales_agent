"""Tests for `_build_studio_snapshot_layer` in the copilot graph.

Covers the free-form (non-guided) studio prompt layer: when the user sits
on ``/brand-studio/*`` or ``/offer-studio/offer/<id>/...`` without guided
mode, the LLM must receive a per-field completion snapshot so it can stop
asking for values the entity already has.

Guided mode wins: if `guided_state` is present, the snapshot layer must
stay empty — `_build_guided_layer` already emits a richer block-scoped
version.
"""

from __future__ import annotations

import uuid
from typing import Any
from unittest.mock import patch

import pytest

from src.modules.copilot.application.orchestrator.graph import (
    _build_studio_snapshot_layer,
    _resolve_studio_context,
)

_TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
_OFFER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")
_PERSONA_ID = uuid.UUID("ed91a7c8-29d9-4370-a595-cba3be148605")


# ── Route resolver ───────────────────────────────────────────────────


def test_resolve_studio_context_brand_route() -> None:
    result = _resolve_studio_context(f"/{_TENANT_ID}/brand-studio/identity")
    assert result == ("brand", None)


def test_resolve_studio_context_brand_root_route() -> None:
    result = _resolve_studio_context(f"/{_TENANT_ID}/brand-studio")
    assert result == ("brand", None)


def test_resolve_studio_context_offer_with_id() -> None:
    result = _resolve_studio_context(
        f"/{_TENANT_ID}/offer-studio/offer/{_OFFER_ID}/promise",
    )
    assert result == ("offer", str(_OFFER_ID))


def test_resolve_studio_context_offer_list_without_id() -> None:
    # Offer list page has no offer UUID — no snapshot possible.
    result = _resolve_studio_context(f"/{_TENANT_ID}/offer-studio")
    assert result is None


def test_resolve_studio_context_buyer_persona_with_id() -> None:
    """Persona detail route must yield (buyer_persona, persona_id) so the
    agent receives the entity_id needed by extract_from_doc / start_guided.

    Reproduces the bug where /brand-studio/publico/persona/{id} matched the
    generic /brand-studio bucket and dropped the persona_id silently.
    """
    result = _resolve_studio_context(
        f"/{_TENANT_ID}/brand-studio/publico/persona/{_PERSONA_ID}",
    )
    assert result == ("buyer_persona", str(_PERSONA_ID))


def test_resolve_studio_context_buyer_persona_with_field_query() -> None:
    """Persona route with ?field= query and trailing segments still matches."""
    result = _resolve_studio_context(
        f"/{_TENANT_ID}/brand-studio/publico/persona/{_PERSONA_ID}/identidad",
    )
    assert result == ("buyer_persona", str(_PERSONA_ID))


def test_resolve_studio_context_buyer_persona_list_without_id() -> None:
    """Persona list (no UUID after /persona) must NOT claim buyer_persona —
    falls back to generic brand-studio bucket so the existing snapshot layer
    still renders brand-level context."""
    result = _resolve_studio_context(f"/{_TENANT_ID}/brand-studio/publico/persona")
    assert result == ("brand", None)


def test_resolve_studio_context_buyer_persona_invalid_uuid() -> None:
    """Garbage in the persona slot must not crash the resolver."""
    result = _resolve_studio_context(
        f"/{_TENANT_ID}/brand-studio/publico/persona/not-a-uuid",
    )
    # Falls through to generic brand-studio match (safe fallback).
    assert result == ("brand", None)


def test_resolve_studio_context_dashboard_route() -> None:
    assert _resolve_studio_context(f"/{_TENANT_ID}/dashboard") is None


def test_resolve_studio_context_empty_route() -> None:
    assert _resolve_studio_context("") is None
    assert _resolve_studio_context(None) is None  # type: ignore[arg-type]


# ── Layer rendering ──────────────────────────────────────────────────


def _state_on_route(route: str, *, guided: bool = False) -> dict[str, Any]:
    state: dict[str, Any] = {
        "tenant_id": _TENANT_ID,
        "client_context": {"current_route": route},
    }
    if guided:
        state["guided_state"] = {
            "domain": "brand",
            "current_block_id": "identity",
            "completed_blocks": [],
            "entity_id": None,
        }
    return state


def test_layer_empty_when_not_on_studio_route() -> None:
    state = _state_on_route(f"/{_TENANT_ID}/dashboard")
    assert _build_studio_snapshot_layer(state) == ""


def test_layer_empty_when_guided_active() -> None:
    """Guided layer already covers completion — avoid redundant prompt bloat."""
    state = _state_on_route(f"/{_TENANT_ID}/brand-studio/identity", guided=True)
    assert _build_studio_snapshot_layer(state) == ""


def test_layer_empty_when_tenant_id_missing() -> None:
    state: dict[str, Any] = {
        "client_context": {"current_route": f"/{_TENANT_ID}/brand-studio/identity"},
    }
    # No tenant_id — renderer can't query anything, must stay empty.
    assert _build_studio_snapshot_layer(state) == ""


def test_layer_brand_route_partitions_filled_and_empty() -> None:
    """Stub out `_compute_field_completion` to verify the template contract."""
    state = _state_on_route(f"/{_TENANT_ID}/brand-studio/identity")
    with patch(
        "src.modules.copilot.application.orchestrator.graph._compute_field_completion",
        return_value=(
            ["identity.brand_name", "identity.tagline"],
            ["positioning.brand_essence"],
        ),
    ):
        rendered = _build_studio_snapshot_layer(state)

    assert rendered != ""
    # Filled paths must be visible so the LLM doesn't re-ask
    assert "identity.brand_name" in rendered
    assert "identity.tagline" in rendered
    # Empty paths must also appear so the LLM knows what to pursue
    assert "positioning.brand_essence" in rendered
    # The "do not re-ask" directive must be present in neutral Spanish
    lower = rendered.lower()
    assert "no preguntes" in lower or "ya están" in lower


def test_layer_offer_route_includes_entity_id_context() -> None:
    state = _state_on_route(
        f"/{_TENANT_ID}/offer-studio/offer/{_OFFER_ID}/promise",
    )
    with patch(
        "src.modules.copilot.application.orchestrator.graph._compute_field_completion",
        return_value=(["public_name"], ["primary_outcome"]),
    ):
        rendered = _build_studio_snapshot_layer(state)

    assert rendered != ""
    assert "public_name" in rendered
    assert "primary_outcome" in rendered


def test_layer_empty_when_catalog_returns_no_paths() -> None:
    state = _state_on_route(f"/{_TENANT_ID}/brand-studio/identity")
    with patch(
        "src.modules.copilot.application.orchestrator.graph.get_catalog",
        return_value=(),
    ):
        # No editable fields → nothing to announce; stay silent.
        assert _build_studio_snapshot_layer(state) == ""


@pytest.mark.parametrize(
    "route,expected_domain",
    [
        ("/aaa/brand-studio", "brand"),
        ("/aaa/brand-studio/visuals", "brand"),
        (
            f"/aaa/offer-studio/offer/{_OFFER_ID}",
            "offer",
        ),
        (
            f"/aaa/offer-studio/offer/{_OFFER_ID}/psychology",
            "offer",
        ),
        (
            f"/aaa/brand-studio/publico/persona/{_PERSONA_ID}",
            "buyer_persona",
        ),
    ],
)
def test_resolve_studio_context_matches_expected_domain(
    route: str,
    expected_domain: str,
) -> None:
    result = _resolve_studio_context(route)
    assert result is not None
    assert result[0] == expected_domain


def test_layer_buyer_persona_route_renders_persona_id_in_prompt() -> None:
    """When user is on /brand-studio/publico/persona/{id}, the snapshot layer
    must include the persona_id in the prompt so the agent can pass it to
    extract_from_doc / start_guided / propose_field_updates.

    Stub out the entity reader to keep the test hermetic."""
    state = _state_on_route(
        f"/{_TENANT_ID}/brand-studio/publico/persona/{_PERSONA_ID}",
    )
    with patch(
        "src.modules.copilot.application.orchestrator.graph._compute_field_completion",
        return_value=(
            ["identity.name", "psychology.symptoms"],
            ["psychology.desires", "psychology.fears"],
        ),
    ):
        rendered = _build_studio_snapshot_layer(state)

    assert rendered != ""
    # The persona UUID must appear in the rendered prompt — without it the
    # agent has no anchor to call extract_from_doc(entity_id=...) and falls
    # back to scanning unrelated modules (root cause of the loop bug).
    assert str(_PERSONA_ID) in rendered
    # Module label must read "Buyer Persona" (Spanish neutro), not "Brand".
    assert "buyer persona" in rendered.lower()
    # Filled + empty paths must be partitioned correctly.
    assert "identity.name" in rendered
    assert "psychology.desires" in rendered
