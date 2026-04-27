"""Copilot observability module.

Self-contained subscription-based observability for the copilot. Wires into
LangChain via ``BaseCallbackHandler`` (standard API) and into the copilot
domain via the shared ``EventBus``. The orchestrator never imports from
here except for the single entrypoint :class:`turn_envelope.ObservabilityContext`.

Subpackages:

* ``recording``  — LangChain callback handler, domain subscribers, turn
  envelope, sanitization, low-level event store.
* ``pricing``    — Provider/model unit-cost resolver with point-in-time
  snapshots fed by a daily LiteLLM sync worker.
* ``cost``       — Cost calculator (tokens times unit price) and FX resolver
  (USD → tenant currency).
* ``persistence``— SQLAlchemy repositories for the new tables and a clean
  interface over ``copilot_trace_event``.
* ``reporting``  — Billing-cycle service and cost aggregator (Phase 3
  consumers).
* ``workers``    — ARQ background tasks (pricing sync, retention, MV
  refresh).
* ``api``        — Internal admin endpoints consumed by Streamlit (Phase
  3).
"""
