"""LLM call site → ModelRole mapping (S4 SSoT, S6 broadened).

Sales_agent declares WHAT model role each LLM call site needs (NANO /
FAST / REASONING / AGENT) — concrete provider + wire model name resolve
at runtime via :func:`Settings.get_provider_for_role` +
``AI_PROVIDER_<ROLE>`` env vars (multi-provider per-role routing
implemented in ``shared/infrastructure/llm/router.py``).

Two views over the same SSoT:

- :data:`LLM_ROLE_BY_SITE` — superset. Every LLM call in sales_agent
  (specialists + infra + workers + orchestrator helpers) consumes it.
- :data:`SPECIALIST_TO_ROLE` — back-compat sub-view restricted to
  StateGraph specialists (supervisor / qualifier / product_expert /
  closer). Consumed by ``application/agents/sales/nodes.py`` and the
  S4 fitness test.

S4 specialist rationale (matches ``phases/S4-chatmodelspec-tier.md``):

* **supervisor → NANO** — classifier with ``max_output_tokens=10``;
  paridad copilot F8 routing tier. NANO defaults to gpt-4o-mini today;
  drops to gpt-5.4-nano when the catalog ships.
* **qualifier → REASONING** — razonamiento sobre lead context.
  ``AI_PROVIDER_REASONING=deepseek`` rutea a DeepSeek-V4 con auto-cache
  disk-based (~1/10 cost input tras price cut abril 2026).
* **product_expert → REASONING** — mismo razonamiento + DeepSeek cache.
* **closer → AGENT** — cierres largos con manejo de objeciones.
  ``AI_PROVIDER_AGENT=kimi`` rutea a Kimi K2.6 con auto-cache 75-83%
  savings + `extra_body.thinking={"type": "disabled"}` forzado por
  ``KimiService`` para mantener compat de tool-call round-trip.

S6 broadened sites:

* **summary → NANO** — ``orchestrator/chat.py::_build_pre_invoke_state``
  genera resúmenes <100 tokens con ``temperature=0``. Costo trivial,
  NANO baja factura sin perder calidad.
* **follow_up_nudge → NANO** — ``workers/follow_up_engine`` genera
  nudge corto post-72h. NANO suficiente; el nudge replica la voz del
  agent_identity ya cacheado.
* **safety → FAST** — ``infrastructure/external/safety_service`` hace
  context check con prompt corto. Mantiene FAST (gpt-4o-mini quality)
  porque el fail-safe (``return True``) es costoso.

Adding a new call site: declare the role here, import
:data:`LLM_ROLE_BY_SITE` + use ``LLM_ROLE_BY_SITE["site_name"]``.
Adding a new specialist: además sumar a :data:`SPECIALIST_TO_ROLE`
y registrar el snapshot en
``tests/architecture/test_no_hardcoded_models_sales_agent.py``.
"""

from __future__ import annotations

from src.core.enums import ModelRole

__all__ = ["LLM_ROLE_BY_SITE", "SPECIALIST_TO_ROLE"]


LLM_ROLE_BY_SITE: dict[str, ModelRole] = {
    # StateGraph specialists (S4) ──────────────────────────────────────
    "supervisor": ModelRole.NANO,
    "qualifier": ModelRole.REASONING,
    "product_expert": ModelRole.REASONING,
    "closer": ModelRole.AGENT,
    # Infra / orchestrator helpers (S6) ────────────────────────────────
    "summary": ModelRole.NANO,
    "follow_up_nudge": ModelRole.NANO,
    "safety": ModelRole.FAST,
    # Scheduler reminder workers (S8) ──────────────────────────────────
    # Short messages (~50 tokens) reusing the cached brand-voice prefix
    # that S7 already populates in slot 5 — NANO is plenty.
    "appointment_reminder_t24h": ModelRole.NANO,
    "appointment_reminder_t1h": ModelRole.NANO,
    "appointment_postcheck": ModelRole.NANO,
}


# Back-compat sub-view consumed por ``nodes.py`` y los tests S4.
SPECIALIST_TO_ROLE: dict[str, ModelRole] = {
    site: role
    for site, role in LLM_ROLE_BY_SITE.items()
    if site in {"supervisor", "qualifier", "product_expert", "closer"}
}
