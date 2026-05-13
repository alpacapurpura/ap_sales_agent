"""Campaigns observability — placeholder spec registration (PI-1 S0 PR-1).

Registers agent_kind="campaign" in shared/agent_observability/registry.py.
Tables campaign_llm_call + campaign_trace_event created in migration 083.

PR-1: registration only. Callback handler + persisters = S2 (when
CampaignExecutionWorker invokes a real LLM). Tables empty until then.
UNION-ALL view in mv_daily_llm_cost_per_tenant_v2 includes them
automatically via the registry.
"""

from __future__ import annotations

from luana_core_campaigns.observability.persistence.models.llm_call_model import (
    CampaignLlmCallModel,
)
from luana_core_observability.registry import (
    AgentObservabilitySpec,
    register_agent_observability,
)

register_agent_observability(
    AgentObservabilitySpec(
        agent_kind="campaign",
        llm_call_model=CampaignLlmCallModel,
        trace_event_table="campaign_trace_event",
        llm_call_table="campaign_llm_call",
        trace_retention_env_var="CAMPAIGN_TRACE_RETENTION_DAYS",
        llm_call_retention_env_var="CAMPAIGN_LLM_CALL_RETENTION_DAYS",
        trace_default_days=30,
        llm_call_default_days=90,
        has_lead_id=True,
    ),
)
