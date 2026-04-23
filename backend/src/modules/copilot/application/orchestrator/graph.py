"""Copilot ReAct Agent — LangGraph StateGraph with tool-calling loop.

The agent follows a simple cycle:
  1. LLM generates a response (possibly with tool calls)
  2. If tool calls → execute them → feed results back to LLM → repeat
  3. If no tool calls → respond to user → END

Tools are selected dynamically based on the user's current route.
The system prompt is enriched with a completion snapshot and module list.
"""

from typing import Literal
from uuid import UUID

import structlog
from langchain_core.messages import AIMessage, SystemMessage
from langgraph.graph import END, START, StateGraph

from src.core.enums import ModelRole
from src.modules.copilot.application.orchestrator.context_budget import truncate_history
from src.modules.copilot.application.orchestrator.state import CopilotState
from src.modules.copilot.application.tools.registry import (
    get_all_tools,
    get_tools_for_context,
)
from src.modules.copilot.domain.module_registry import get_module_registry
from src.modules.copilot.infrastructure.prompts.base import prompt_loader
from src.modules.copilot.infrastructure.prompts.sanitizer import (
    sanitize_selected_fields,
)
from src.shared.infrastructure.llm.factory import LLMFactory

logger = structlog.get_logger()


# ── Nodes ────────────────────────────────────────────────────────────


def _get_completion_snapshot(tenant_id: UUID) -> str:
    """Build a quick completion snapshot for the system prompt.

    Uses the awareness tool logic directly (not via tool invocation)
    to avoid a tool call just for the system prompt.
    """
    from sqlalchemy import text

    from src.core.database import SessionLocal
    from src.modules.copilot.domain.schema_introspection import (
        check_section_completion,
        format_completion_markdown,
        get_model_sections,
    )

    registry = get_module_registry()
    db = SessionLocal()
    lines = []
    try:
        # ── Brand (introspectable) ──
        brand_desc = registry.get("brand")
        if brand_desc and brand_desc.model_class and brand_desc.repo_factory:
            try:
                repo = brand_desc.repo_factory(db)
                data = brand_desc.read_fn(repo, tenant_id)
                if data and hasattr(data, "model_dump"):
                    raw = data.model_dump(mode="json")
                    sections = get_model_sections(brand_desc.model_class)
                    completion = check_section_completion(raw, sections)
                    lines.append(
                        format_completion_markdown(
                            brand_desc.label,
                            completion,
                            sections,
                        ),
                    )
                else:
                    lines.append(f"### ⚠️ {brand_desc.label}\n  Sin datos configurados")
            except Exception:  # noqa: BLE001 — orchestrator resilience
                lines.append(f"### ⚠️ {brand_desc.label}\n  Error al leer datos")

        # Offer (SQL count)
        try:
            count = (
                db.execute(
                    text(
                        "SELECT COUNT(*) FROM products WHERE tenant_id = :tid AND is_active = true",
                    ),
                    {"tid": str(tenant_id)},
                ).scalar()
                or 0
            )
            icon = "✅" if count > 0 else "⚠️"
            lines.append(f"### {icon} Offer Studio\n  {count} oferta(s) configurada(s)")
        except Exception:  # noqa: BLE001 — orchestrator resilience
            pass

        # Connections (SQL count)
        try:
            conn_count = (
                db.execute(
                    text(
                        "SELECT COUNT(*) FROM channel_connections WHERE tenant_id = :tid AND is_active = true",
                    ),
                    {"tid": str(tenant_id)},
                ).scalar()
                or 0
            )
            icon = "✅" if conn_count > 0 else "⚠️"
            lines.append(f"### {icon} Conexiones\n  {conn_count} activa(s)")
        except Exception:  # noqa: BLE001 — orchestrator resilience
            pass

    except Exception as e:  # noqa: BLE001 — orchestrator resilience
        logger.warning("completion_snapshot_error", error=str(e))
    finally:
        db.close()

    return "\n\n".join(lines) if lines else ""


def _get_behavior_summary(tenant_id: UUID, user_id: UUID) -> str:
    """Build a user behavior summary from copilot events for the system prompt."""
    from src.core.database import SessionLocal
    from src.modules.copilot.infrastructure.repositories.event_repository import (
        CopilotEventRepository,
    )

    db = SessionLocal()
    try:
        repo = CopilotEventRepository(db)
        summary = repo.get_user_behavior_summary(tenant_id, user_id, days=30)
        if not summary:
            return ""

        lines = []
        # Proposals
        accepted = summary.get("proposal_accepted", 0)
        rejected = summary.get("proposal_rejected", 0)
        if accepted or rejected:
            total = accepted + rejected
            rate = round(accepted / total * 100) if total else 0
            lines.append(
                f"- Propuestas: acepta {rate}% ({accepted} aceptadas, {rejected} rechazadas)",
            )

        # Nudges
        nudge_clicked = summary.get("nudge_clicked", 0)
        nudge_dismissed = summary.get("nudge_dismissed", 0)
        if nudge_clicked or nudge_dismissed:
            lines.append(
                f"- Nudges: {nudge_clicked} aceptados, {nudge_dismissed} descartados",
            )

        # Navigation
        nav = summary.get("navigation_clicked", 0)
        if nav:
            lines.append(f"- Navegaciones realizadas: {nav}")

        # Messages
        msgs = summary.get("message_sent", 0)
        if msgs:
            activity = "muy activo" if msgs > 30 else "activo" if msgs > 10 else "moderado"
            lines.append(f"- Mensajes enviados: {msgs} (usuario {activity})")

        # Copilot opens — friction map for this user
        opens = summary.get("copilot_opened", 0)
        if opens:
            lines.append(f"- Aperturas del copilot: {opens}")

        # RAG searches
        ks = repo.get_knowledge_search_stats(tenant_id, user_id, days=30)
        if ks["search_count"]:
            scope_info = f" (scope preferido: {ks['most_queried_scope']})" if ks["most_queried_scope"] else ""
            lines.append(
                f"- Busquedas en knowledge base: {ks['search_count']}{scope_info}",
            )

        # Procedures
        proc_rates = repo.get_procedure_completion_rates(tenant_id, days=30)
        for proc_id, info in proc_rates.items():
            name = info.get("name", proc_id)
            abandoned = info.get("abandoned", 0)
            avg_step = info.get("avg_abandoned_step")
            total = info.get("started", 0)
            if abandoned and avg_step is not None:
                lines.append(
                    f"- Procedimiento '{name}': abandonado {abandoned}/{total} veces en paso ~{avg_step}",
                )

        return "\n".join(lines) if lines else ""
    except Exception as e:  # noqa: BLE001 — orchestrator resilience
        logger.warning("behavior_summary_error", error=str(e))
        return ""
    finally:
        db.close()


def _compute_pending_field_paths(
    domain: str,
    entity_id: str | None,
    field_paths: tuple[str, ...] | list[str],
    tenant_id: UUID | None,
) -> list[str]:
    """Return the subset of ``field_paths`` whose value is empty for the entity.

    Best-effort: if the repository lookup fails, returns the full list so the
    LLM gets a conservative (over-ask) rather than incorrect (skip-filled)
    signal. Uses the module registry to stay domain-agnostic.
    """
    if not field_paths or not tenant_id:
        return list(field_paths)
    try:
        registry = get_module_registry()
        desc = registry.get(domain)
        if desc is None or not desc.repo_factory or not desc.read_fn:
            return list(field_paths)

        from src.core.database import SessionLocal

        db = SessionLocal()
        try:
            repo = desc.repo_factory(db)
            # Pass entity_id when the read_fn signature accepts it (offers,
            # personas); brand's read_fn takes only tenant_id.
            try:
                data = desc.read_fn(repo, tenant_id, entity_id) if entity_id else desc.read_fn(repo, tenant_id)
            except TypeError:
                data = desc.read_fn(repo, tenant_id)
            if data is None:
                return list(field_paths)
            payload = data.model_dump(mode="json") if hasattr(data, "model_dump") else dict(data)
        finally:
            db.close()
    except Exception:  # noqa: BLE001 — orchestrator resilience
        return list(field_paths)

    pending: list[str] = []
    for path in field_paths:
        value: object = payload
        for key in path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        if value is None or (isinstance(value, (str, list, dict)) and not value):
            pending.append(path)
    return pending


def _build_guided_layer(state: dict[str, object]) -> str:
    """Render the guided-setup prompt layer + active-extraction banner.

    Two conditional blocks share the same helper:

    - ``active_extraction_job`` — rendered when the conversation has a URL/doc
      extraction in flight. Tells the LLM to pause ``extract_structured`` for
      the active module and conversational-stall the user for 1-2 min.
    - ``guided_state`` — rendered when the user is in a guided setup run.
      Lists current block, completed blocks, and the subset of fields still
      pending (computed from live entity data so the LLM never asks for
      fields that already have a value).

    Either, both, or neither can be active. Blocks are regenerated from the
    catalog so labels/descriptions stay in sync with any schema change.
    """
    guided_raw = state.get("guided_state")
    active_job_raw = state.get("active_extraction_job")
    tenant_id = state.get("tenant_id")

    has_guided = bool(guided_raw and isinstance(guided_raw, dict))
    has_active_job = bool(active_job_raw and isinstance(active_job_raw, dict))
    if not has_guided and not has_active_job:
        return ""

    template_ctx: dict[str, object] = {
        "guided_active": False,
        "active_extraction_job": active_job_raw if has_active_job else None,
    }

    if has_guided:
        from src.modules.copilot.application.guided.block_generator import (
            block_by_id,
            build_blocks,
        )

        assert isinstance(guided_raw, dict)  # noqa: S101 — narrowing for type checker
        domain = str(guided_raw.get("domain", ""))
        current_id = str(guided_raw.get("current_block_id", ""))
        completed = list(guided_raw.get("completed_blocks", []))
        entity_id = guided_raw.get("entity_id")
        if domain and current_id:
            blocks = build_blocks(domain)  # type: ignore[arg-type]
            current_block = block_by_id(domain, current_id)  # type: ignore[arg-type]
            if current_block is not None:
                pending = _compute_pending_field_paths(
                    domain=domain,
                    entity_id=str(entity_id) if entity_id else None,
                    field_paths=current_block.field_paths,
                    tenant_id=tenant_id if isinstance(tenant_id, UUID) else None,
                )
                template_ctx.update(
                    {
                        "guided_active": True,
                        "domain": domain,
                        "entity_id": entity_id,
                        "current_block_id": current_block.id,
                        "current_block_label": current_block.label,
                        "current_block_field_paths": list(current_block.field_paths),
                        "pending_field_paths": pending,
                        "blocks_completed_count": len(completed),
                        "total_blocks": len(blocks),
                    },
                )

    try:
        return prompt_loader.render("copilot_guided", **template_ctx)
    except Exception:
        logger.exception("Error rendering guided prompt layer")
        return ""


def build_system_prompt(state: CopilotState) -> str:
    """Render the system prompt with current context, completion snapshot, and module list."""
    ctx = state.get("client_context", {})
    tenant_id = state.get("tenant_id")

    # Build completion snapshot
    snapshot = ""
    if tenant_id:
        try:
            snapshot = _get_completion_snapshot(tenant_id)
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("snapshot_build_error", error=str(e))

    # Build module list from registry
    registry = get_module_registry()
    modules = [
        {"label": d.label, "route_prefix": d.route_prefix, "description": d.description} for d in registry.values()
    ]

    # Build behavior summary
    behavior_summary = ""
    user_id = state.get("user_id")
    if tenant_id and user_id:
        try:
            behavior_summary = _get_behavior_summary(tenant_id, user_id)
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("behavior_summary_build_error", error=str(e))

    # Active tool names
    active_tools = state.get("active_tool_names", [])

    # Editable-fields catalog — the compact SSoT view the LLM uses to decide
    # which field_ids are valid for propose_field_updates. Separated from
    # the completion snapshot: snapshot = "is it configured?"; catalog =
    # "what CAN I edit?". The LLM needs both.
    try:
        from src.modules.copilot.domain.schema_introspection import (
            format_all_editable_catalogs_markdown,
        )

        editable_catalog = format_all_editable_catalogs_markdown()
    except Exception as e:  # noqa: BLE001 — orchestrator resilience
        logger.warning("editable_catalog_error", error=str(e))
        editable_catalog = ""

    # Build active procedure context for system prompt
    active_procedure_ctx = None
    active_proc = state.get("active_procedure")
    if active_proc:
        from src.modules.copilot.application.tools.procedure_tools import (
            PROCEDURE_REGISTRY,
        )

        proc = PROCEDURE_REGISTRY.get(active_proc.get("procedure_id", ""))
        if proc:
            idx = active_proc.get("current_step_index", 0)
            total = len(proc.steps)
            if idx < total:
                step = proc.steps[idx]
                active_procedure_ctx = {
                    "name": proc.name,
                    "current_step": idx + 1,
                    "total_steps": total,
                    "instruction": step.instruction,
                    "tips": step.tips,
                }

    # Sanitize user-provided values before template insertion to prevent prompt injection
    safe_selected_fields = sanitize_selected_fields(ctx.get("selected_fields", []))

    try:
        base_prompt = prompt_loader.render(
            "copilot_system",
            current_route=ctx.get("current_route"),
            selected_fields=safe_selected_fields,
            completion_snapshot=snapshot,
            behavior_summary=behavior_summary,
            modules=modules,
            available_tools=active_tools,
            active_procedure=active_procedure_ctx,
            editable_catalog=editable_catalog,
        )
    except Exception as e:  # noqa: BLE001 — orchestrator resilience
        logger.warning("copilot_system_prompt_fallback", error=str(e))
        base_prompt = (
            "Eres el Copilot de Nicolify, un asistente experto en marketing y ventas. "
            "Habla siempre en español, de forma profesional pero cercana."
        )

    # Compose: base prompt + guided layer when guided mode is active.
    return base_prompt + _build_guided_layer(state)


def agent_node(state: CopilotState) -> dict:
    """Call LLM with conversation history and system prompt.

    The LLM may return text, tool calls, or both.
    Tools are selected dynamically based on the user's current route.
    """
    llm = LLMFactory.get_service().get_client(ModelRole.AGENT)
    llm = llm.bind(temperature=0.6)

    # Dynamic tool selection based on mode (interview > focus > chat)
    ctx = state.get("client_context", {})
    tools = get_tools_for_context(ctx)

    if tools:
        llm = llm.bind_tools(tools)

    system_prompt = build_system_prompt(state)
    history = truncate_history(list(state["messages"]))
    messages = [SystemMessage(content=system_prompt), *history]
    response = llm.invoke(messages)

    # Store active tool names for logging/state
    tool_names = [t.name for t in tools]

    return {"messages": [response], "active_tool_names": tool_names}


async def tool_executor_node(state: CopilotState) -> dict:
    """Execute tool calls from the last AIMessage and return ToolMessages.

    Uses route-based tool selection to build the tool map.

    Async so ``StructuredTool``s backed by ``async def`` (e.g. the
    ``extract_from_url`` tool that awaits an ARQ ``enqueue_job``) can run
    without tripping ``NotImplementedError: StructuredTool does not support
    sync invocation``. ``ainvoke`` works for both sync and async tools —
    sync tools are wrapped in a threadpool under the hood — so this is
    universal rather than special-casing.
    """
    from langchain_core.messages import ToolMessage

    last_message = state["messages"][-1]
    if not isinstance(last_message, AIMessage) or not last_message.tool_calls:
        return {"messages": []}

    # Build tool map from mode-scoped tools + all tools as fallback
    ctx = state.get("client_context", {})
    route_tools = get_tools_for_context(ctx)
    all_tools = get_all_tools()

    # Route tools first, then fallback to all tools for robustness
    tool_map = {t.name: t for t in all_tools}
    tool_map.update({t.name: t for t in route_tools})

    tool_messages = []
    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        if tool_name in tool_map:
            try:
                result = await tool_map[tool_name].ainvoke(tool_args)
                tool_messages.append(
                    ToolMessage(
                        content=str(result),
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    ),
                )
            except Exception as e:
                logger.exception("copilot_tool_error", tool=tool_name, error=str(e))
                tool_messages.append(
                    ToolMessage(
                        content=f"Error ejecutando {tool_name}: {e!s}",
                        tool_call_id=tool_call["id"],
                        name=tool_name,
                    ),
                )
        else:
            tool_messages.append(
                ToolMessage(
                    content=f"Tool '{tool_name}' no encontrada.",
                    tool_call_id=tool_call["id"],
                    name=tool_name,
                ),
            )

    return {"messages": tool_messages}


def should_continue(state: CopilotState) -> Literal["tools", "end"]:
    """Route: if the LLM made tool calls, go to tool_executor; otherwise end."""
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        return "tools"
    return "end"


# ── Build Graph ──────────────────────────────────────────────────────

workflow = StateGraph(CopilotState)

workflow.add_node("agent", agent_node)
workflow.add_node("tools", tool_executor_node)

workflow.add_edge(START, "agent")
workflow.add_conditional_edges("agent", should_continue, {"tools": "tools", "end": END})
workflow.add_edge("tools", "agent")

copilot_graph = workflow.compile()
