"""Tests for ``offer_prompt_renderer.filter_offer_for_prompt``.

Verifies the lifecycle gate that bridges :data:`OFFER_FIELD_CONTRACTS`
status with the ``agent_identity.j2`` rendering: paths with
``status != ACTIVE`` get stripped from the offer dict, while ACTIVE
paths and enrichment-only keys (``preset_*``) survive.

Workspace: ``docs/refactors/field-contract-platform/`` Fase 05.
"""

from __future__ import annotations

from dataclasses import replace

import pytest

from luana_core_sales_agent.application.services.offer_prompt_renderer import (
    filter_offer_for_prompt,
)
from luana_core_platform.domain.field_contract import (
    FieldStatus,
    get_module_contracts,
    register_module_contracts,
)


@pytest.fixture(autouse=True)
def _restore_offer_registry():
    """Snapshot + restore the offer registry around each test."""
    snapshot = get_module_contracts("offer")
    yield
    register_module_contracts("offer", snapshot)


def _replace_path_status(path: str, status: FieldStatus) -> None:
    contracts = get_module_contracts("offer")
    mutated = tuple(replace(c, status=status) if c.path == path else c for c in contracts)
    register_module_contracts("offer", mutated)


def test_filter_keeps_active_paths_and_enrichment_keys() -> None:
    offer = {
        "headline_promise": "promesa",
        "primary_outcome": "resultado",
        "preset_label": "Coach bootcamp",
        "preset_description": "descripción",
        "preset_flags": ["HIGH_TICKET"],
        "type": "programa",
    }

    out = filter_offer_for_prompt(offer)

    assert out == offer  # nothing removed when registry is all ACTIVE


def test_filter_strips_deprecated_paths() -> None:
    _replace_path_status("headline_promise", FieldStatus.DEPRECATED)

    offer = {
        "headline_promise": "promesa",
        "primary_outcome": "resultado",
        "preset_label": "Coach bootcamp",
    }

    out = filter_offer_for_prompt(offer)

    assert "headline_promise" not in out
    assert out["primary_outcome"] == "resultado"
    assert out["preset_label"] == "Coach bootcamp"


def test_filter_strips_removed_paths() -> None:
    _replace_path_status("time_to_value", FieldStatus.REMOVED)

    offer = {"time_to_value": "30 días", "primary_outcome": "resultado"}

    out = filter_offer_for_prompt(offer)

    assert "time_to_value" not in out
    assert out["primary_outcome"] == "resultado"


def test_filter_returns_new_dict_does_not_mutate_input() -> None:
    offer = {"headline_promise": "promesa"}
    out = filter_offer_for_prompt(offer)
    assert out is not offer  # separate identity
    assert offer == {"headline_promise": "promesa"}  # unchanged
