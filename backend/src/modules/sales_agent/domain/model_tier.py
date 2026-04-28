"""Specialist → ModelRole mapping (S4 SSoT).

Sales_agent specialists declare WHAT model role they need (NANO / FAST /
REASONING / AGENT) — concrete provider + wire model name resolve at
runtime via :func:`Settings.get_provider_for_role` + ``AI_PROVIDER_<ROLE>``
env vars (multi-provider per-role routing implemented in
``shared/infrastructure/llm/router.py``).

Single source of truth: any specialist that invokes the LLM consumes
this mapping in ``application/agents/sales/nodes.py``. New specialists
add an entry here + a node + a fitness-test snapshot.

S4 mapping rationale (matches ``phases/S4-chatmodelspec-tier.md``):

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

Adding a specialist: declare the role here, import + use in nodes.py,
and the architectural fitness test
(``tests/architecture/test_no_hardcoded_models_sales_agent.py``) keeps
new code from pinning wire model names.
"""

from __future__ import annotations

from src.core.enums import ModelRole

__all__ = ["SPECIALIST_TO_ROLE"]


SPECIALIST_TO_ROLE: dict[str, ModelRole] = {
    "supervisor": ModelRole.NANO,
    "qualifier": ModelRole.REASONING,
    "product_expert": ModelRole.REASONING,
    "closer": ModelRole.AGENT,
}
