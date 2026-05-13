"""Eval simulator observability — cost bucket separation for synthetic LLM traffic.

Importing this package triggers spec.py side-effect:
  register_agent_observability(agent_kind="eval_simulator", ...)

Tables eval_simulator_llm_call + eval_simulator_trace_event created in migration 125.
Lookup table eval_synthetic_tenants enables prod Streamlit query filtering.

Origin: PI-12 Story B eval-foundation-simulator-homologation (2026-05-07).
Pattern parity: campaigns/observability/__init__.py (PI-1 S0 PR-1 / Alembic 083).

Decision H6 (spec): separate cost bucket prevents eval synthetic traffic from
polluting mv_daily_llm_cost_per_tenant_v2 + budget guards + Streamlit dashboards.
"""

from __future__ import annotations

from src.modules.sales_agent.observability.eval_simulator import (
    spec as _spec,  # noqa: F401  # deferred Nicolify-local eval_simulator
)
