"""F5 — ``ask_tenant_data`` tool + decomposed pipeline.

Public entry point is :func:`ask_tenant_data` (see :mod:`.tool`); the
sub-modules expose the deterministic pipeline stages so each can be tested
in isolation:

* :mod:`.intent_classifier` — LLM FAST → ``IntentResult``
* :mod:`.date_parser` — Spanish LatAm period phrases → ``(since, until)``
* :mod:`.query_builder` — assemble ``DataQueryPlan`` from intent + question
* :mod:`.executor` — dispatch plan to first ``DataAccessProvider`` that supports it
* :mod:`.state_check` — annotate result with state flags (zero, archived, …)
* :mod:`.synthesizer` — LLM FAST channel-aware reply

[COPILOT-ASK-TENANT-DATA-F5]
"""

from src.modules.copilot.application.tools.ask_tenant_data.tool import (
    _ask_tenant_data_impl,
    ask_tenant_data,
)

__all__ = ("_ask_tenant_data_impl", "ask_tenant_data")
