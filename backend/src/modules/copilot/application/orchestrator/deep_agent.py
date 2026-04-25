"""F2 — Deep Agents harness wrapping ``copilot_graph``.

Builds a ``CompiledStateGraph`` via :func:`deepagents.create_deep_agent`
that exposes the same ``astream_events`` interface the legacy
``copilot_graph`` does. The chat orchestrator picks one or the other
based on ``settings.COPILOT_DEEP_AGENT_V2``.

# [COPILOT-DEEP-AGENT-V2] -> docs/domains/copilot/redesign-2026-04/phases/F2-deep-agents-harness.md

What changes vs the legacy ReAct loop:

- Planning visible: built-in ``write_todos`` tool emits a TODO list
  before the agent acts on multi-step tasks.
- Scratchpad: ephemeral filesystem (StateBackend, default) gives the
  agent ``read_file`` / ``write_file`` / ``ls`` / ``edit_file`` /
  ``glob`` / ``grep``. Lives inside the deep-agent state for the
  current turn — nothing crosses conversations.
- Subagents: built-in ``task`` tool spawns isolated workers. F2 ships
  the dummy ``audit_inspector``; F4/F5 add real subagents.

What stays:

- Per-turn dynamic tool selection via :func:`get_tools_for_context`
  (route-based). The agent is rebuilt per request precisely so that
  this call still drives the bound toolset.
- The 4-tier model router (``LLMFactory.get_service().get_client``).
- Tenant isolation: tools read tenant_id from contextvars, not state.
- Spanish-neutro LatAm system prompt.

Why we rebuild per turn (instead of caching the compiled graph):
``build_system_prompt`` injects per-turn snapshots, behavior summaries
and guided/studio layers, and ``get_tools_for_context`` filters tools
by route + guided flag. Both inputs change every turn, so a cached
graph would either go stale or require middleware acrobatics. The
compile is cheap (microseconds) versus the LLM call.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from deepagents import create_deep_agent

from src.core.enums import ModelRole
from src.modules.copilot.application.orchestrator.graph import build_system_prompt
from src.modules.copilot.application.orchestrator.subagents import (
    AUDIT_INSPECTOR_SUBAGENT,
    URL_ANALYZER_SUBAGENT,
)
from src.modules.copilot.application.tools.registry import get_tools_for_context
from src.shared.infrastructure.llm.factory import LLMFactory

if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.graph.state import CompiledStateGraph

    from src.modules.copilot.application.orchestrator.state import CopilotState

logger = structlog.get_logger()


# Append-only suffix layered on top of ``build_system_prompt`` output.
# Lives here rather than in a Jinja template because the deepagents
# boilerplate (tool semantics, planning behavior) is opinionated and
# already shipped by the library — we only nudge tone + scope.
_DEEP_AGENT_SUFFIX_ES = """

---

## Modo Deep Agent (planning + scratchpad)

Tienes acceso a herramientas adicionales:

- `write_todos`: cuando la tarea tiene 3+ pasos visibles, anotá el plan ANTES
  de ejecutar. El usuario ve el plan en una `plan_card`. Marcá pasos como
  `completed` a medida que avanzás.
- `read_file` / `write_file` / `edit_file` / `ls` / `glob` / `grep`: tu
  scratchpad efímero por conversación. Útil para guardar fragmentos largos
  (transcript, notas, borrador) que no querés re-pegar en cada turno.
- `task(name, prompt)`: delegá una tarea aislada a un sub-agente especializado.
  Disponibles:
    - `audit_inspector` (revisión rápida de una sección).
    - `url_analyzer` (analiza una o más URLs como inspiración de la
      conversación; persiste resumen y abre `inspiration_saved` cards).

Reglas:
- Tareas chicas (1-2 pasos, pregunta directa): respondé sin write_todos.
- Tareas largas (auditoría, diseño, multi-step): write_todos primero.
- Spanish neutro LatAm en todo lo user-facing (sin voseo, sin "che", sin
  "vos/tenés/podés"). Tu plan visible es user-facing.
- No alucines paths del scratchpad. Usá `ls` antes de `read_file`.
""".strip()


def _build_combined_system_prompt(state: CopilotState) -> str:
    """Compose the Nicolify dynamic prompt + deep-agent suffix."""
    base = build_system_prompt(state)
    return f"{base}\n{_DEEP_AGENT_SUFFIX_ES}"


def build_deep_agent_graph(
    state: CopilotState,
    *,
    llm: BaseChatModel | None = None,
    tools: list[BaseTool] | None = None,
) -> CompiledStateGraph:
    """Compile a deep-agent graph for the current turn.

    Args:
        state: The CopilotState dict for the current request. Used to
            build the system prompt + select tools.
        llm: Override the LLM (test only). Production code passes
            ``None`` and the 4-tier router resolves the AGENT model.
        tools: Override the tool list (test only). Production code
            passes ``None`` and ``get_tools_for_context`` resolves
            tools by route.

    Returns:
        Compiled LangGraph graph with the deepagents middleware stack
        (TodoListMiddleware, FilesystemMiddleware, SubAgentMiddleware,
        SummarizationMiddleware, PatchToolCallsMiddleware) wired in.
        Same ``astream_events(state, version="v2")`` contract the
        legacy ``copilot_graph`` exposes — chat.py can swap them.
    """
    if llm is None:
        llm = LLMFactory.get_service().get_client(ModelRole.AGENT)
        # Match the legacy graph's temperature so output style is stable
        # when the flag flips per-tenant.
        llm = llm.bind(temperature=0.6)

    if tools is None:
        ctx = state.get("client_context", {})
        tools = list(get_tools_for_context(ctx))

    system_prompt = _build_combined_system_prompt(state)

    return create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        subagents=[AUDIT_INSPECTOR_SUBAGENT, URL_ANALYZER_SUBAGENT],
    )
