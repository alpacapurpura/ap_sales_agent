"""Tests for campaigns observability spec registration.

CONTRACT §3.C — PR-1 S0 campaigns observability placeholder.
Tests verify agent_kind='campaign' is correctly registered with
has_lead_id=True and correct table names.
"""

from __future__ import annotations


def test_campaigns_observability_bootstrap_registers_campaign() -> None:
    """Importing bootstrap must register agent_kind='campaign' in registry."""
    import src.shared.infrastructure.agent_observability_bootstrap
    from luana_core_observability.registry import agent_observability_registry

    kinds = [spec.agent_kind for spec in agent_observability_registry()]
    assert "campaign" in kinds, "campaigns observability spec not registered"


def test_campaigns_spec_has_lead_id_true() -> None:
    """Campaign spec must declare has_lead_id=True (per-lead telemetry)."""
    import src.shared.infrastructure.agent_observability_bootstrap
    from luana_core_observability.registry import get_spec

    spec = get_spec("campaign")
    assert spec.has_lead_id is True


def test_campaigns_spec_trace_event_table() -> None:
    """Trace event table must be 'campaign_trace_event'."""
    import src.shared.infrastructure.agent_observability_bootstrap
    from luana_core_observability.registry import get_spec

    spec = get_spec("campaign")
    assert spec.trace_event_table == "campaign_trace_event"


def test_campaigns_spec_llm_call_table() -> None:
    """LLM call table must be 'campaign_llm_call'."""
    import src.shared.infrastructure.agent_observability_bootstrap
    from luana_core_observability.registry import get_spec

    spec = get_spec("campaign")
    assert spec.llm_call_table == "campaign_llm_call"


def test_campaigns_spec_retention_env_vars() -> None:
    """Retention env var names must match config.py declarations."""
    import src.shared.infrastructure.agent_observability_bootstrap
    from luana_core_observability.registry import get_spec

    spec = get_spec("campaign")
    assert spec.trace_retention_env_var == "CAMPAIGN_TRACE_RETENTION_DAYS"
    assert spec.llm_call_retention_env_var == "CAMPAIGN_LLM_CALL_RETENTION_DAYS"


def test_campaigns_spec_retention_defaults() -> None:
    """PR-1 sets shorter retention (30d trace, 90d llm_call) for placeholder."""
    import src.shared.infrastructure.agent_observability_bootstrap
    from luana_core_observability.registry import get_spec

    spec = get_spec("campaign")
    assert spec.trace_default_days == 30
    assert spec.llm_call_default_days == 90


def test_campaigns_llm_call_model_tablename() -> None:
    """CampaignLlmCallModel must map to 'campaign_llm_call' table."""
    from luana_core_campaigns.observability.persistence.models.llm_call_model import (
        CampaignLlmCallModel,
    )

    assert CampaignLlmCallModel.__tablename__ == "campaign_llm_call"
