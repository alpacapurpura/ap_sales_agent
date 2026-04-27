"""ARQ workers for the observability module.

* :mod:`pricing_sync_task` — daily 03:00 UTC pull of LiteLLM pricing.
* :mod:`aggregate_refresh_task` — hourly ``REFRESH MATERIALIZED VIEW``
  (skeleton; completed in Phase 3).
* :mod:`retention_task` — daily drop of trace rows older than N days
  (skeleton; completed in Phase 3).
"""
