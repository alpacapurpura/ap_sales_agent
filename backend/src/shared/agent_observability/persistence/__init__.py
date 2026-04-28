"""Persistence — reference-data repos + abstract repo protocols.

Reference data (cross-tenant, cross-agent):

* :mod:`pricing_snapshot_repository` — versioned pricing (LiteLLM sync writes).
* :mod:`tenant_billing_config_repository` — per-tenant anchor day + currency.

Abstract protocols (each agent declares its concrete repo over its own table):

* :mod:`base_llm_call_repo` — Protocol for ``*_llm_call`` writers.
* :mod:`base_trace_event_repo` — Protocol for ``*_trace_event`` writers.
"""
