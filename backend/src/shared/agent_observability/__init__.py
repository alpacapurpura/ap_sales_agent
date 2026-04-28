"""Shared agent observability primitives — cross-agent.

Cross-cutting capa para agentes (copilot, sales_agent, …):

* ``recording``  — sanitization regex + abstract callback handler base.
* ``pricing``    — provider/model alias map + point-in-time resolver +
  daily LiteLLM sync.
* ``cost``       — pure cost calculator (tokens x snapshot) + FX resolver
  (USD → tenant currency).
* ``persistence``— reference-data tables (``model_pricing_snapshot``,
  ``tenant_billing_config``) + abstract repo protocols para que cada
  agent declare su concrete repo (``copilot_llm_call``, ``sales_agent_llm_call``,
  …).
* ``reporting``  — billing cycle window math (anchor day) + service.
* ``workers``    — ARQ tasks cross-agent (pricing sync diario).

Cada bounded context (``modules/copilot/observability/``,
``modules/sales_agent/observability/`` cuando S1 lo cree) consume estos
primitives + declara su concrete callback handler / repos / model SQLA.

Reference: `docs/domains/sales-agent/redesign-2026-04/phases/S0-shared-observability-extract.md`.
"""
