"""Eval simulator observability spec registration.

Registers agent_kind="eval_simulator" in shared/agent_observability/registry.py
so cross-agent ops (cost aggregator, cost alerts, retention worker) discover it.

Tables eval_simulator_llm_call + eval_simulator_trace_event created in migration 125.

Consumed by:
- shared.agent_observability.workers.retention_task (30-day retention for synthetic data)
- shared.agent_observability.reporting.cost_aggregator (eval cost breakdown per tenant)
- shared.agent_observability.workers.aggregate_refresh_task (MV UNION ALL refresh)

Origin: PI-12 Story B eval-foundation-simulator-homologation (2026-05-07).
Pattern parity: campaigns/observability/__init__.py (PI-1 S0 PR-1 / Alembic 083).
"""

from __future__ import annotations

from luana_core_observability.registry import (
    AgentObservabilitySpec,
    register_agent_observability,
)

# deferred Nicolify-local — not yet lifted to luana_core_sales_agent
from src.modules.sales_agent.observability.eval_simulator.persistence.models.eval_simulator_llm_call import (
    EvalSimulatorLlmCallModel,
)

register_agent_observability(
    AgentObservabilitySpec(
        agent_kind="eval_simulator",
        llm_call_model=EvalSimulatorLlmCallModel,
        trace_event_table="eval_simulator_trace_event",
        llm_call_table="eval_simulator_llm_call",
        trace_retention_env_var="EVAL_SIMULATOR_TRACE_RETENTION_DAYS",
        llm_call_retention_env_var="EVAL_SIMULATOR_LLM_CALL_RETENTION_DAYS",
        trace_default_days=30,  # synthetic — short retention, no audit obligation
        llm_call_default_days=30,
        has_lead_id=False,  # eval simulator does not use per-lead audit rows
    ),
)
