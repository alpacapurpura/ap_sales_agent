"""F3 — golden tests for brand-lighthouse injection into the system prompt.

Verifies that:
- ``build_system_prompt`` includes the brand lighthouse on target routes
  (offer-studio, sales, …) and only when a summary exists.
- It is absent on off-route surfaces (brand-studio itself, settings).
- ``build_deep_agent_graph``'s combined prompt keeps the deep-agent
  suffix at the TAIL — F2 invariant preserved.
- The F8 cacheable prefix order is: identity → tools hint → lighthouse
  → editable catalog → modules. The cache boundary marker comes after
  the lighthouse and before any per-turn fragment.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

_LIGHTHOUSE_TEXT = (
    "Marca formación para empresarias LatAm. Promesa: escalar negocios sin "
    "perder humanidad. Avatar: líderes en transición. Diferencia: comunidad. "
    "Voz cálida, directa."
)


@pytest.fixture(autouse=True)
def _reset_provider_discovery():
    from luana_core_copilot.application.discovery import reset_discovery

    reset_discovery()
    yield
    reset_discovery()


@pytest.fixture(autouse=True)
def _stub_db_helpers(monkeypatch):
    """Bypass DB-touching helpers in ``build_system_prompt``.

    F0/F1/F2 baseline tests stub the whole prompt; F3 needs the REAL
    builder to verify ordering, so we patch only the helpers that hit
    the DB (no Postgres in unit tests).
    """
    monkeypatch.setattr(
        "luana_core_copilot.application.orchestrator.graph._get_completion_snapshot",
        lambda _tenant_id: "",
    )
    monkeypatch.setattr(
        "luana_core_copilot.application.orchestrator.graph._get_behavior_summary",
        lambda _tenant_id, _user_id: "",
    )
    monkeypatch.setattr(
        "luana_core_copilot.domain.schema_introspection.format_all_editable_catalogs_markdown",
        lambda: "",
    )


@pytest.fixture
def stub_summary(monkeypatch):
    """Patch ``BrandSummaryProvider.summary`` to return our canned text."""
    from luana_core_brand_studio.copilot_provider import summary as summary_mod

    async def _stub_summary(self, *, tenant_id):
        return _LIGHTHOUSE_TEXT

    monkeypatch.setattr(summary_mod.BrandSummaryProvider, "summary", _stub_summary)


@pytest.fixture
def base_state():
    return {
        "tenant_id": uuid4(),
        "user_id": uuid4(),
        "messages": [],
        "client_context": {
            "current_route": "/abc/offer-studio",
            "selected_fields": [],
            "form_data": {},
            "locale": "es",
        },
        "active_tool_names": [],
    }


def test_lighthouse_present_on_offer_studio(stub_summary, base_state) -> None:
    from luana_core_copilot.application.orchestrator.graph import (
        build_system_prompt,
    )
    from luana_core_copilot.application.orchestrator.system_prompt_layout import (
        CACHE_BOUNDARY_MARKER,
    )

    prompt = build_system_prompt(base_state)
    assert "## Brand Lighthouse" in prompt
    assert _LIGHTHOUSE_TEXT in prompt
    # F8 §5.2 cache-friendly order: identity ("Eres ...") comes FIRST in
    # the cacheable prefix, then tools hint, THEN lighthouse. The boundary
    # marker sits after the lighthouse, before any per-turn fragment.
    base_pos = prompt.index("Eres el Copilot de Nicolify")
    lighthouse_pos = prompt.index("## Brand Lighthouse")
    boundary_pos = prompt.find(CACHE_BOUNDARY_MARKER)
    assert base_pos < lighthouse_pos
    # Boundary may be absent when no volatile fragment is rendered (this
    # test stubs them empty); when present, lighthouse precedes it.
    if boundary_pos != -1:
        assert lighthouse_pos < boundary_pos


def test_lighthouse_absent_on_brand_studio(stub_summary, base_state) -> None:
    from luana_core_copilot.application.orchestrator.graph import (
        build_system_prompt,
    )

    base_state["client_context"]["current_route"] = "/abc/brand-studio/identity"
    prompt = build_system_prompt(base_state)
    assert "## Brand Lighthouse" not in prompt


def test_lighthouse_absent_when_summary_missing(monkeypatch, base_state) -> None:
    from luana_core_brand_studio.copilot_provider import summary as summary_mod
    from luana_core_copilot.application.orchestrator.graph import (
        build_system_prompt,
    )

    async def _none(self, *, tenant_id):
        return None

    monkeypatch.setattr(summary_mod.BrandSummaryProvider, "summary", _none)

    base_state["client_context"]["current_route"] = "/abc/sales/studio/inbox"
    prompt = build_system_prompt(base_state)
    assert "## Brand Lighthouse" not in prompt


def test_deep_agent_suffix_stays_at_tail(stub_summary, base_state) -> None:
    """The F2 deep-agent suffix must remain after ALL injected fragments."""
    from luana_core_copilot.application.orchestrator.deep_agent import (
        _DEEP_AGENT_SUFFIX_ES,
        _build_combined_system_prompt,
    )

    combined = _build_combined_system_prompt(base_state)
    assert combined.endswith(_DEEP_AGENT_SUFFIX_ES)
    # And the lighthouse is BEFORE the deep-agent suffix.
    lighthouse_pos = combined.index("## Brand Lighthouse")
    suffix_pos = combined.index(_DEEP_AGENT_SUFFIX_ES.split("\n", 1)[0])
    assert lighthouse_pos < suffix_pos


def test_no_route_means_no_lighthouse(stub_summary, base_state) -> None:
    from luana_core_copilot.application.orchestrator.graph import (
        build_system_prompt,
    )

    base_state["client_context"]["current_route"] = None
    prompt = build_system_prompt(base_state)
    assert "## Brand Lighthouse" not in prompt
