"""Sales-agent observability — event-sourced parity with copilot.

Importing this package registers the sales_agent observability spec in
:mod:`src.shared.agent_observability.registry` so cross-agent ops
(cost aggregator, cost alerts, retention worker) discover it.
"""

from __future__ import annotations

from src.modules.sales_agent.observability.persistence.models.llm_call_model import (
    SalesAgentLlmCallModel,
)
from src.shared.agent_observability.registry import (
    AgentObservabilitySpec,
    register_agent_observability,
)

register_agent_observability(
    AgentObservabilitySpec(
        agent_kind="sales_agent",
        llm_call_model=SalesAgentLlmCallModel,
        trace_event_table="sales_agent_trace_event",
        llm_call_table="sales_agent_llm_call",
        trace_retention_env_var="SALES_AGENT_TRACE_RETENTION_DAYS",
        llm_call_retention_env_var="SALES_AGENT_LLM_CALL_RETENTION_DAYS",
        has_lead_id=True,
    ),
)
