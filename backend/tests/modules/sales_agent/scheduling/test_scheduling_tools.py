"""S8 — Scheduling tools (create / verify / get_slots) end-to-end.

Covers idempotency of ``tool_create_booking_link`` (re-firing same
turn → reuse), ``tool_verify_booking_status`` mapping, and the
stage-scoped ``get_tools_for_stage`` registry.
"""

from __future__ import annotations

import datetime as dt
import uuid
from unittest.mock import patch

import pytest

from src.modules.sales_agent.application.agents.sales.tools import TOOL_REGISTRY
from src.modules.sales_agent.application.tools.registry import (
    ALWAYS_AVAILABLE,
    STAGE_TOOL_SCOPE,
    get_tools_for_stage,
    is_tool_available_in_stage,
)
from src.modules.sales_agent.application.tools.scheduling.tools import (
    SCHEDULING_TOOL_REGISTRY,
    tool_create_booking_link,
    tool_verify_booking_status,
)


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.UUID("aaaa2222-0000-0000-0000-000000000001")


@pytest.fixture
def lead_id() -> uuid.UUID:
    return uuid.UUID("bbbb2222-0000-0000-0000-000000000001")


@pytest.fixture
def populated_db(db, tenant_id, lead_id):
    from src.modules.crm.infrastructure.models.lead_model import LeadModel
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
        AgentStateCheckpointModel,
    )

    db.add(TenantModel(id=tenant_id, slug="acme", name="Acme", config_json={}))
    db.add(LeadModel(id=lead_id, tenant_id=tenant_id))
    db.add(
        AgentStateCheckpointModel(
            id=uuid.uuid4(),
            session_id="s8",
            tenant_id=tenant_id,
            lead_id=lead_id,
            channel_type="whatsapp",
            current_stage="presentation",
            scheduled_meetings=[],
        ),
    )
    db.commit()
    return db


def _build_state(tenant_id: uuid.UUID, lead_id: uuid.UUID, **extra) -> dict:
    return {
        "tenant_id": str(tenant_id),
        "lead_id": str(lead_id),
        "active_product": {"scheduling_event_slug": "discovery-call"},
        "_tool_args": extra.get("args", {}),
        **{k: v for k, v in extra.items() if k != "args"},
    }


def test_create_booking_link_returns_url(populated_db, tenant_id, lead_id) -> None:
    state = _build_state(tenant_id, lead_id)
    with patch("src.shared.links.ports.domain_lookup.create_domain_lookup") as mock_lookup:
        mock_lookup.return_value.get_verified_domain.return_value = None
        result = tool_create_booking_link(state, populated_db)

    assert result["status"] == "success"
    assert result["url"].startswith("http")
    assert result["tracking_id"]
    assert result["reused"] is False


def test_create_booking_link_idempotent_within_window(populated_db, tenant_id, lead_id) -> None:
    """Re-invoking with the same lead+slug returns the same active link."""
    state = _build_state(tenant_id, lead_id)
    with patch("src.shared.links.ports.domain_lookup.create_domain_lookup") as mock_lookup:
        mock_lookup.return_value.get_verified_domain.return_value = None
        first = tool_create_booking_link(state, populated_db)
        second = tool_create_booking_link(state, populated_db)

    assert first["status"] == "success"
    assert second["status"] == "success"
    assert second["reused"] is True
    assert second["tracking_id"] == first["tracking_id"]


def test_create_booking_link_missing_event_slug(populated_db, tenant_id, lead_id) -> None:
    state = _build_state(tenant_id, lead_id)
    state["active_product"] = {}  # no slug
    state["_tool_args"] = {}
    result = tool_create_booking_link(state, populated_db)
    assert result["status"] == "error"
    assert "event_slug" in result["message"]


def test_create_booking_link_invalid_expires_in_hours(populated_db, tenant_id, lead_id) -> None:
    state = _build_state(tenant_id, lead_id, args={"expires_in_hours": 0})
    result = tool_create_booking_link(state, populated_db)
    assert result["status"] == "error"


def test_verify_booking_status_unknown(populated_db, tenant_id, lead_id) -> None:
    state = _build_state(tenant_id, lead_id, args={"tracking_id": "not-real"})
    result = tool_verify_booking_status(state, populated_db)
    assert result["status"] == "success"
    assert result["status_value"] if "status_value" in result else result.get("tracking_id") == "not-real"
    assert result.get("provider") == "internal"


def test_scheduling_tools_registered_in_main_registry() -> None:
    """SCHEDULING_TOOL_REGISTRY merged into TOOL_REGISTRY."""
    for name in SCHEDULING_TOOL_REGISTRY:
        assert name in TOOL_REGISTRY, f"{name} missing from TOOL_REGISTRY"


def test_stage_scoping_rapport_excludes_booking() -> None:
    tools = get_tools_for_stage("rapport", TOOL_REGISTRY)
    assert "create_booking_link" not in tools
    assert "escalate_to_human" in tools  # always available


def test_stage_scoping_closing_includes_booking() -> None:
    tools = get_tools_for_stage("closing", TOOL_REGISTRY)
    assert "create_booking_link" in tools
    assert "send_payment_link" in tools


def test_stage_scoping_unknown_stage_falls_back_to_rapport() -> None:
    tools = get_tools_for_stage("nonexistent_stage", TOOL_REGISTRY)
    rapport_tools = get_tools_for_stage("rapport", TOOL_REGISTRY)
    assert set(tools) == set(rapport_tools)


def test_is_tool_available_in_stage_matches_get_tools() -> None:
    for stage in STAGE_TOOL_SCOPE:
        tools = get_tools_for_stage(stage, TOOL_REGISTRY)
        for name in tools:
            assert is_tool_available_in_stage(name, stage)


def test_always_available_tools_resolve_in_registry() -> None:
    """Every name in ALWAYS_AVAILABLE must exist in TOOL_REGISTRY."""
    for name in ALWAYS_AVAILABLE:
        assert name in TOOL_REGISTRY, f"ALWAYS_AVAILABLE[{name}] missing from TOOL_REGISTRY"
