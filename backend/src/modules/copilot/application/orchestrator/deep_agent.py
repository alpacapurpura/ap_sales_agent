"""Deep Agents harness — sole graph runtime for the Copilot orchestrator.

Builds a ``CompiledStateGraph`` via :func:`deepagents.create_deep_agent`
exposing the ``astream_events`` interface the chat orchestrator drives.

After F8 §5.3 this is the **only** graph runtime — the legacy ReAct
``copilot_graph`` and the ``COPILOT_DEEP_AGENT_V2`` flag have both been
removed. The harness was introduced in F2 with a flag, validated in
F3-F7, and promoted to default in F8 once observability + provider
discovery + workflow runtime stabilised.

# [COPILOT-DEEP-AGENT-V2] -> docs/domains/copilot/redesign-2026-04/phases/F2-deep-agents-harness.md

Capabilities (all on by default now):

- Planning visible: built-in ``write_todos`` tool emits a TODO list
  before the agent acts on multi-step tasks.
- Scratchpad: ephemeral filesystem (StateBackend, default) gives the
  agent ``read_file`` / ``write_file`` / ``ls`` / ``edit_file`` /
  ``glob`` / ``grep``. Lives inside the deep-agent state for the
  current turn — nothing crosses conversations.
- Subagents: built-in ``task`` tool spawns isolated workers. F2 shipped
  the dummy ``audit_inspector``; F4/F5 added real subagents.

Invariants preserved across the migration:

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
    DATA_QUERY_SUBAGENT,
    URL_ANALYZER_SUBAGENT,
)
from src.modules.copilot.application.tools.registry import get_tools_for_context
from src.shared.infrastructure.llm.factory import LLMFactory

if TYPE_CHECKING:
    from uuid import UUID

    from langchain_core.language_models import BaseChatModel
    from langchain_core.tools import BaseTool
    from langgraph.graph.state import CompiledStateGraph

    from src.modules.copilot.application.orchestrator.state import CopilotState
    from src.shared.billing.application.budget_guard import BudgetGuard

logger = structlog.get_logger()


# Append-only suffix layered on top of ``build_system_prompt`` output.
# Lives here rather than in a Jinja template because the deepagents
# boilerplate (tool semantics, planning behavior) is opinionated and
# already shipped by the library — we only nudge tone + scope.
_DEEP_AGENT_SUFFIX_ES = """

---

## Modo Deep Agent (planning + scratchpad)

Tienes acceso a herramientas adicionales:

- `write_todos`: cuando la tarea tiene 3+ pasos visibles, anota el plan ANTES
  de ejecutar. El usuario ve el plan en una `plan_card`. Marca pasos como
  `completed` a medida que avanzas.

  **Obligatorio cuando vayas a invocar tools que modifican estado del
  tenant.** Tools que mutan datos (incluyen pero no se limitan a):
  `extract_from_doc`, `extract_from_url`, `extract_document_to_fields`,
  `propose_field_updates`, `transition_workflow_state`. Antes del primer
  call a cualquiera de ellas, llama `write_todos` con 2-4 pasos describiendo
  ÚNICAMENTE acciones que tú vas a ejecutar (leer documento, extraer
  campos, generar propuesta de cambios). El usuario ve el plan ANTES del
  cambio — sin sorpresas. La regla aplica también a tools nuevas que se
  sumen al set en futuras fases (criterio: cualquier tool cuyo efecto
  visible es una mutación o una propuesta de mutación).

  **Reglas estrictas de write_todos:**

  1. **Solo acciones del agente.** Cada `content` describe una acción que
     tú ejecutas con tools. NO incluyas pasos como "esperar confirmación
     del usuario", "esperar que el usuario revise", "aguardar feedback":
     esos NO son tu trabajo, son del usuario, y dejan el plan abierto
     para siempre porque nunca puedes marcarlos `completed`.
  2. **Marca el último step `completed` antes de cerrar el turn.**
     Cuando ya emitiste la propuesta (o ejecutaste la mutación), el plan
     está terminado. Tu obligación: re-llamar `write_todos` con todos los
     steps `status: 'completed'`. Si dejas el último en `in_progress`,
     el usuario ve el plan colgado.
  3. **Máximo 2 calls a `write_todos` por turn**: uno al inicio (plan con
     todos `pending`/`in_progress`) y uno al final (plan con todos
     `completed`). NO actualices step-por-step en medio. La FE dedupea el
     plan_card en pantalla, así que más calls no aportan valor visible y
     gastan tokens.
- `read_file` / `write_file` / `edit_file` / `ls` / `glob` / `grep`: tu
  scratchpad efímero por conversación. Útil para guardar fragmentos largos
  (transcript, notas, borrador) que no quieres re-pegar en cada turno.
- `task(name, prompt)`: delega una tarea aislada a un sub-agente especializado.
  Disponibles:
    - `audit_inspector` (revisión rápida de una sección).
    - `url_analyzer` (analiza una o más URLs como inspiración de la
      conversación; persiste resumen y abre `inspiration_saved` cards).

Reglas:
- Tareas chicas (1-2 pasos, pregunta directa): responde sin write_todos.
- Tareas largas (auditoría, diseño, multi-step): write_todos primero.
- Spanish neutro LatAm en todo lo user-facing. Usa tuteo (`tú`, `tienes`,
  `puedes`, `quieres`, imperativos como `anota`/`marca`/`responde`). NO uses
  formas verbales con acento final (`-ás`/`-és`/`-ís`) ni el pronombre
  rioplatense. Tu plan visible es user-facing.
- No alucines paths del scratchpad. Usa `ls` antes de `read_file`.

## Reglas de delegación a sub-agente (`task`)

Cuando uses `task(subagent_type, description)` para delegar a un sub-agente:

1. NO leas la misma data desde tools del parent en el MISMO turn. El sub-agente
   tiene sus propias tools y lee lo que necesita. Pasa contexto en
   `description`. Lecturas paralelas duplican costo y producen reportes
   redundantes.

2. El sub-agente devuelve su reporte como ToolMessage en tu historial. Tu
   próxima respuesta al usuario tiene tres partes (en este orden):
   - una frase introductoria breve (máx 1 línea, p. ej. "Aquí va el resultado:");
   - el reporte del sub-agente con cambios mínimos (negritas, viñetas si
     aplica, sin re-redactar el contenido);
   - una pregunta o paso siguiente accionable (máx 1 línea).

3. Prohibido re-escribir el reporte con tus palabras. Ya viene en español
   neutro LatAm y ya tiene la estructura correcta. Re-redactarlo gasta
   tokens, duplica el contenido en pantalla y rompe la traza del
   razonamiento del sub-agente.

4. Un solo `task` por turno como regla general. Si el usuario pide algo que
   pareciera necesitar 2+ sub-agentes, primero ejecuta uno y entrega su
   resultado; el siguiente turno decide si delegar otro.
""".strip()


def _build_channel_intent_hint(state: CopilotState) -> str:
    """Emit a system-prompt instruction when channel intent is detected.

    FP2 (B24) — Kimi K2.6 (no-thinking, phrasing-sensitive per B11-TP6)
    consistently dropped the ``format_for_channel`` tool call when the
    user wrote "armame copy WhatsApp" / "para email" / "copy WA literal".
    The tool was bound (``ALWAYS_AVAILABLE_GROUPS`` ships it on every
    route) but the LLM never decided to invoke it.

    The hint is **append-only** to the existing suffix so the deep-agent
    behaviour rules (planning, scratchpad, voseo prohibition) remain
    intact. Idempotent: a missing intent yields an empty string and the
    suffix renders verbatim.
    """
    intent = state.get("channel_intent")
    if not intent:
        return ""
    channel = str(intent.get("channel", "")).strip()
    label = str(intent.get("label", "")).strip() or channel
    if not channel:
        return ""
    return (
        "\n\n"
        f"## REGLA OBLIGATORIA — Canal de salida: {label}\n\n"
        f"El usuario pidió expresamente la respuesta en formato `{label}`. "
        "Esta es una **instrucción de canal vinculante**, no una sugerencia.\n\n"
        "Tu próximo turno DEBE ejecutar exactamente este flujo:\n\n"
        f"1. Genera el copy adaptado a {label} usando el contexto disponible "
        "(nombre de marca, oferta, audiencia, contenido proporcionado por el usuario "
        "o ya conocido en este chat). Si la información es mínima, genera un copy "
        "genérico con placeholders explícitos — el usuario los completará después. "
        "**NUNCA pidas más datos antes de generar al menos un primer borrador.**\n"
        "2. **OBLIGATORIO** — invoca la herramienta "
        f"`format_for_channel(content=<tu copy>, channel_id='{channel}')`. "
        "Esto NO es opcional: cada respuesta de canal debe pasar por esta tool "
        "para validar largo, limpiar markdown y reportar warnings.\n"
        f"3. Entrega al usuario el `content` que devuelve la tool, listo para "
        f"copiar y pegar en {label}. Nada más, nada menos. Sin markdown asterisks `**` "
        "ni headers `#`. Sin explicaciones meta sobre el proceso.\n\n"
        "Saltar la tool, pedir clarificación adicional antes de generar el primer "
        "borrador, o entregar prosa larga estilo informe rompe la experiencia. "
        "Si te falta un dato puntual (fecha, link), inclúyelo como placeholder "
        f"(`[FECHA]`, `[LINK]`) en el copy — el usuario lo completa después de "
        "validar el formato."
    )


def _build_combined_system_prompt(state: CopilotState) -> str:
    """Compose the Nicolify dynamic prompt + deep-agent suffix + channel hint."""
    base = build_system_prompt(state)
    channel_hint = _build_channel_intent_hint(state)
    return f"{base}\n{_DEEP_AGENT_SUFFIX_ES}{channel_hint}"


def build_deep_agent_graph(
    state: CopilotState,
    *,
    llm: BaseChatModel | None = None,
    tools: list[BaseTool] | None = None,
    budget_guard: BudgetGuard | None = None,
    tenant_id: UUID | None = None,
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
        budget_guard: PR-6 Sub-C — when provided, ``llm`` is wrapped in
            ``BudgetGuardingChatModel`` enforcing pre-call budget check.
            Single enforcement point: every callsite consuming this
            graph (deep_agent.ainvoke / astream_events) is gated.
        tenant_id: Required when ``budget_guard`` is provided. Used as
            the budget bucket key for the wrapper.

    Returns:
        Compiled LangGraph graph with the deepagents middleware stack
        (TodoListMiddleware, FilesystemMiddleware, SubAgentMiddleware,
        SummarizationMiddleware, PatchToolCallsMiddleware) wired in.
        Same ``astream_events(state, version="v2")`` contract the
        legacy ``copilot_graph`` exposes — chat.py can swap them.
    """
    if llm is None:
        # Temperature override va por el factory (NO ``.bind()``):
        # ``deepagents 0.5+`` rechaza ``RunnableBinding`` en
        # ``resolve_model`` — el harness profile cache hace ``dict.get``
        # y RunnableBinding es unhashable. Ver
        # ``LLMFactory.get_client(temperature=...)`` y
        # ``tests/modules/copilot/test_deep_agent_factory_wire.py``.
        llm = LLMFactory.get_service().get_client(
            ModelRole.AGENT,
            temperature=0.6,
        )

    if budget_guard is not None and tenant_id is not None:
        from src.shared.billing.application.llm_guards import BudgetGuardingChatModel

        llm = BudgetGuardingChatModel(  # type: ignore[assignment]
            inner=llm,
            budget_guard=budget_guard,
            tenant_id=tenant_id,
            agent_kind="copilot",
        )

    if tools is None:
        ctx = state.get("client_context", {})
        tools = list(get_tools_for_context(ctx))

    system_prompt = _build_combined_system_prompt(state)

    return create_deep_agent(
        model=llm,
        tools=tools,
        system_prompt=system_prompt,
        subagents=[
            AUDIT_INSPECTOR_SUBAGENT,
            URL_ANALYZER_SUBAGENT,
            DATA_QUERY_SUBAGENT,
        ],
    )
