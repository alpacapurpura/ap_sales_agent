"""Cross-agent ARQ workers.

* :mod:`pricing_sync_task` — daily LiteLLM pricing reconciliation.

Agent-specific workers (retention, aggregate refresh, cost alert) live
in each module's observability subpackage until their SQL is parameterised
cross-agent (S1/S2).
"""
