"""Dummy ``audit_inspector`` subagent — plumbing only.

F2 deliverable to validate end-to-end ``task()`` flow + subagent context
isolation. The main agent can spawn this subagent to "auditar una
sección"; the subagent has no tools beyond the deepagents builtins
(write_todos, scratchpad ops) inherited from the parent — its job in
F2 is exclusively to prove the wiring works.

F4 (URL contextual scratchpad) and F5 (ask_tenant_data subgraph) will
replace this with real subagents (``url_analyzer`` / ``data_query``).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deepagents import SubAgent

# Spanish neutro LatAm — matches user-facing copy invariants.
_AUDIT_INSPECTOR_PROMPT = """Eres un sub-agente del Copilot Nicolify especializado en auditar
secciones del studio activo (brand, offer, landing, etc.) cuando el agente
principal te delega una revisión rápida.

Tu trabajo:
1. Lee el contexto que recibes en el prompt.
2. Identifica los 3 hallazgos más relevantes (gaps, oportunidades, errores).
3. Devuelve un resumen breve en español neutro latinoamericano.

Limita tu respuesta a 6 líneas. No inventes datos: si no tienes
contexto suficiente, di "necesito más información sobre <X>" y termina.
""".strip()


AUDIT_INSPECTOR_SUBAGENT: SubAgent = {
    "name": "audit_inspector",
    "description": (
        "Audita una sección del studio activo (brand/offer/landing/...) y devuelve "
        "los 3 hallazgos más relevantes. Úsalo cuando el usuario pida una revisión "
        "estructural rápida. No edita campos — solo reporta."
    ),
    "system_prompt": _AUDIT_INSPECTOR_PROMPT,
}
