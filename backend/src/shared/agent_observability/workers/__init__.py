"""Cross-agent ARQ workers.

* :mod:`pricing_sync_task` — daily LiteLLM pricing reconciliation.
* :mod:`aggregate_refresh_task` — hourly REFRESH for both daily-cost
  MVs (legacy ``mv_daily_llm_cost_per_tenant`` + cross-agent
  ``mv_daily_llm_cost_per_tenant_v2``).
* :mod:`retention_task` — daily purge iterating
  :func:`agent_observability_registry`.
* :mod:`cost_alert_task` — daily cross-agent cost-alert scan; uses
  :class:`CrossAgentCostAggregator` so emitted warnings carry the
  per-agent breakdown.
"""
