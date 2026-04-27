"""Recording layer — turns external signals into persisted trace rows.

Two ingress points:

* :class:`callback_handler.ObservabilityCallbackHandler` — subclass of
  ``langchain_core.callbacks.BaseCallbackHandler``. Wired via
  ``RunnableConfig(callbacks=[handler])`` at the orchestrator boundary
  (Phase 2). Captures LLM, tool, chain and error events natively.
* :func:`domain_subscribers.register_subscribers` — registers handlers on
  the shared ``EventBus`` for copilot-emitted domain events (cards,
  routing, mutations) that LangChain doesn't see.

Both write through :mod:`event_store` (low-level row persister) and
:mod:`sanitization` (truncate + future PII redaction).
"""
