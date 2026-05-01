"""Copilot system-prompt builder + shared orchestrator helpers.

After F8 §5.3 the legacy ReAct ``copilot_graph`` was removed — the
deep-agent harness in ``deep_agent.py`` is the only graph runtime. This
module now hosts:

* ``build_system_prompt`` — cache-friendly fragment composer (F8 §5.2).
* The fragment helpers it composes (lighthouse injectors, studio /
  guided / volatile / inspirations layers).
* ``_tool_message_content`` + ``_truncate_tool_content`` — pure data
  helpers reused by the SSE adapter and a regression test.

Tools are selected per-route via ``get_tools_for_context`` from the tool
registry; the deep-agent harness invokes that helper and binds the
result to the ``create_deep_agent`` toolset.
"""

import json
import re
from uuid import UUID

import structlog

from src.modules.copilot.application.orchestrator.state import CopilotState
from src.modules.copilot.domain.module_registry import get_module_registry
from src.modules.copilot.infrastructure.prompts.base import prompt_loader
from src.modules.copilot.infrastructure.prompts.sanitizer import (
    sanitize_selected_fields,
)
from src.shared.links.ports.editable_fields import get_catalog

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


def _compute_field_completion(
    domain: str,
    entity_id: str | None,
    field_paths: tuple[str, ...] | list[str],
    tenant_id: UUID | None,
) -> tuple[list[str], list[str]]:
    """Partition ``field_paths`` into (filled, empty) using live entity data.

    Best-effort. On repository failure the entire input is reported as
    ``empty`` so the LLM errs on the side of over-asking rather than
    silently skipping filled fields. Used by both the guided-setup block
    (narrow, per-block paths) and the studio snapshot layer (wide, whole
    catalog).
    """
    paths = list(field_paths)
    if not paths or not tenant_id:
        return [], paths
    try:
        registry = get_module_registry()
        desc = registry.get(domain)
        if desc is None or not desc.repo_factory or not desc.read_fn:
            return [], paths

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
                return [], paths
            payload = data.model_dump(mode="json") if hasattr(data, "model_dump") else dict(data)
        finally:
            db.close()
    except Exception:  # noqa: BLE001 — orchestrator resilience
        return [], paths

    filled: list[str] = []
    empty: list[str] = []
    for path in paths:
        value: object = payload
        for key in path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            else:
                value = None
                break
        if value is None or (isinstance(value, (str, list, dict)) and not value):
            empty.append(path)
        else:
            filled.append(path)
    return filled, empty


def _compute_pending_field_paths(
    domain: str,
    entity_id: str | None,
    field_paths: tuple[str, ...] | list[str],
    tenant_id: UUID | None,
) -> list[str]:
    """Return the subset of ``field_paths`` whose value is empty for the entity.

    Thin wrapper over :func:`_compute_field_completion` preserved for the
    guided-setup layer, which only needs the ``empty`` half.
    """
    _, empty = _compute_field_completion(domain, entity_id, field_paths, tenant_id)
    return empty


# Route → domain resolvers for the studio snapshot layer. Brand Studio is
# tenant-scoped so no entity id is needed. Offer Studio embeds ``offerId``
# in the path; only the offer-detail route (``/offer-studio/offer/<uuid>``)
# can be snapshotted — the offer-list route has no specific entity. Buyer
# personas live under brand-studio but their detail route embeds the
# persona UUID — same shape as offer.
_STUDIO_OFFER_ID_RE = re.compile(
    r"/offer-studio/offer/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)
_STUDIO_PERSONA_ID_RE = re.compile(
    r"/brand-studio/publico/persona/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})",
    re.IGNORECASE,
)


def _resolve_studio_context(current_route: str | None) -> tuple[str, str | None] | None:
    """Map a route into ``(domain, entity_id)`` for the studio snapshot layer.

    Returns ``None`` when the route does not point at a known studio
    surface, or when the route is missing the required entity segment
    (e.g. ``/offer-studio`` without a selected offer).
    """
    if not current_route:
        return None
    # Offer studio — detail route only; list route has no entity.
    match = _STUDIO_OFFER_ID_RE.search(current_route)
    if match:
        return "offer", match.group(1)
    # Buyer persona detail route — embedded UUID required. Must check
    # before the generic /brand-studio fallback so the persona_id is not
    # silently dropped (was the root cause of the read_document → loop bug
    # observed 2026-04-27 with conversation fbc79125-…). The persona list
    # route (no UUID) falls through to the brand bucket below.
    persona_match = _STUDIO_PERSONA_ID_RE.search(current_route)
    if persona_match:
        return "buyer_persona", persona_match.group(1)
    if "/brand-studio" in current_route:
        return "brand", None
    return None


# Display labels for domains that are not registered as full
# ``ModuleDescriptor``s. Keeps the snapshot layer prompt human-readable
# without forcing buyer_persona to register as a top-level module — which
# would also imply nav/awareness/etc. surface area we don't need.
_DOMAIN_DISPLAY_LABELS: dict[str, str] = {
    "buyer_persona": "Buyer Persona",
}


def _render_studio_snapshot(
    *,
    domain: str,
    entity_id: str | None,
    tenant_id: UUID,
    current_route: str,
) -> str:
    """Compute filled/empty partition for ``domain`` and render the layer."""
    try:
        catalog = get_catalog(domain)
    except Exception:
        logger.exception("studio_snapshot_catalog_error", domain=domain)
        return ""
    paths = [spec.path for spec in catalog]
    if not paths:
        return ""

    filled, empty = _compute_field_completion(
        domain=domain,
        entity_id=entity_id,
        field_paths=paths,
        tenant_id=tenant_id,
    )

    registry = get_module_registry()
    desc = registry.get(domain)
    module_label = desc.label if desc else _DOMAIN_DISPLAY_LABELS.get(domain, domain)

    try:
        return prompt_loader.render(
            "copilot_studio_snapshot",
            module_label=module_label,
            current_route=current_route,
            domain=domain,
            entity_id=entity_id,
            filled_paths=filled,
            empty_paths=empty,
        )
    except Exception:
        logger.exception("studio_snapshot_render_error", domain=domain)
        return ""


def _build_studio_snapshot_layer(state: dict[str, object]) -> str:
    """Render the free-form studio snapshot — filled vs empty fields of the current studio.

    Skips itself when the guided layer is active: guided already reports
    pending fields at a finer (per-block) granularity, so doubling up
    would only bloat the prompt.

    Emitted when:
      * ``client_context.current_route`` matches a known studio surface
        (``/brand-studio/*`` or ``/offer-studio/offer/<uuid>[...]``)
      * No guided setup is active
      * The editable-field catalog for the domain is non-empty
    """
    if state.get("guided_state"):
        return ""
    ctx = state.get("client_context")
    if not isinstance(ctx, dict):
        return ""
    tenant_id = state.get("tenant_id")
    if not isinstance(tenant_id, UUID):
        return ""

    current_route = ctx.get("current_route")
    route_str = current_route if isinstance(current_route, str) else None
    resolved = _resolve_studio_context(route_str)
    if resolved is None or route_str is None:
        return ""
    domain, entity_id = resolved
    return _render_studio_snapshot(
        domain=domain,
        entity_id=entity_id,
        tenant_id=tenant_id,
        current_route=route_str,
    )


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


def _collect_context_injectors_prefix(
    *,
    target_route: str | None,
    tenant_id: UUID | None,
) -> str:
    """Aggregate per-route context injector fragments into a prompt prefix.

    F3 lighthouse hook (``[COPILOT-BRAND-SUMMARY-F3]``). The aggregator
    runs each provider's ``ContextInjector.inject_for(route, tenant_id)``
    and concatenates the non-empty fragments. Fragments live BEFORE the
    base prompt so the LLM sees the brand voice anchor first AND the
    Anthropic prompt cache treats them as a stable prefix when only the
    completion snapshot below changes turn-to-turn.
    """
    if not target_route or tenant_id is None:
        return ""

    try:
        from src.modules.copilot.application.discovery import discover_providers
    except Exception as exc:  # noqa: BLE001 — orchestrator resilience
        logger.warning("context_injector_discovery_unavailable", error=str(exc))
        return ""

    fragments: list[str] = []
    for module_id, provider in discover_providers().items():
        try:
            injector = provider.context_injector()
        except Exception:
            logger.exception("context_injector_lookup_failed", module=module_id)
            continue
        if injector is None:
            continue
        try:
            fragment = _await_sync(
                injector.inject_for(
                    target_route=target_route,
                    tenant_id=tenant_id,
                )
            )
        except Exception:
            logger.exception("context_injector_inject_for_failed", module=module_id)
            continue
        if fragment:
            fragments.append(fragment.strip())

    if not fragments:
        return ""
    return "\n\n".join(fragments) + "\n\n"


def _await_sync(coro: object) -> object:
    """Run an awaitable from a sync code path safely.

    ``build_system_prompt`` is sync (called from agent_node + the deep
    agent harness). ``ContextInjector.inject_for`` is async because F4+
    fan-outs may hit the network. When we're already inside an event
    loop (FastAPI request) we cannot ``asyncio.run`` so we delegate to
    ``asyncio.run_coroutine_threadsafe`` via a fresh thread executor;
    when sync (worker callsite, tests) we use ``asyncio.run`` directly.
    """
    import asyncio

    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is None:
        return asyncio.run(coro)

    # Loop is already running — cannot block. Run the coro on a fresh
    # event loop in a worker thread.
    import concurrent.futures

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        return pool.submit(lambda: asyncio.run(coro)).result()


def _safe_render(template_name: str, **kwargs: object) -> str:
    """Render a Jinja template, returning empty string on failure.

    Wraps ``prompt_loader.render`` so that a single template failure cannot
    break the orchestrator. Failures are logged but the prompt continues to
    assemble with the remaining fragments.
    """
    try:
        return prompt_loader.render(template_name, **kwargs)
    except Exception as e:  # noqa: BLE001 — orchestrator resilience
        logger.warning("system_prompt_template_failed", template=template_name, error=str(e))
        return ""


def _resolve_active_procedure_ctx(state: CopilotState) -> dict[str, object] | None:
    """Build the active-procedure context dict consumed by the volatile template."""
    active_proc = state.get("active_procedure")
    if not active_proc:
        return None
    from src.modules.copilot.application.tools.procedure_tools import (
        PROCEDURE_REGISTRY,
    )

    proc = PROCEDURE_REGISTRY.get(active_proc.get("procedure_id", ""))
    if proc is None:
        return None
    idx = active_proc.get("current_step_index", 0)
    total = len(proc.steps)
    if idx >= total:
        return None
    step = proc.steps[idx]
    return {
        "name": proc.name,
        "current_step": idx + 1,
        "total_steps": total,
        "instruction": step.instruction,
        "tips": step.tips,
    }


def _build_workflow_state_fragment(
    *,
    current_route: str | None,
    selected_fields: list,
    behavior_summary: str,
    active_procedure_ctx: dict[str, object] | None,
    guided_or_studio_layer: str,
) -> str:
    """Compose the WORKFLOW_STATE slot — per-turn user context.

    Aggregates: current route + selected fields + behavior summary + active
    procedure step + the state-aware guided/studio layer. Returned text is
    placed AFTER the cache boundary because every input changes per turn.
    """
    rendered = _safe_render(
        "copilot_system_volatile",
        current_route=current_route,
        selected_fields=selected_fields,
        behavior_summary=behavior_summary,
        active_procedure=active_procedure_ctx,
    )
    parts = [rendered.strip(), guided_or_studio_layer.strip()]
    return "\n\n".join(p for p in parts if p)


def _build_studio_snapshot_fragment(state: CopilotState, tenant_id: UUID | None) -> str:
    """Compose the STUDIO_SNAPSHOT slot — per-turn business state."""
    if tenant_id is None:
        return ""
    try:
        snapshot = _get_completion_snapshot(tenant_id)
    except Exception as e:  # noqa: BLE001 — orchestrator resilience
        logger.warning("snapshot_build_error", error=str(e))
        return ""
    return _safe_render("copilot_system_snapshot", completion_snapshot=snapshot)


def _build_inspirations_fragment(state: CopilotState) -> str:
    """Compose the INSPIRATIONS slot (F4 hook)."""
    from src.modules.copilot.application.orchestrator.inspirations_layer import (
        build_inspirations_layer,
    )

    return build_inspirations_layer(state)


def _build_static_identity_fragment() -> str:
    """Compose the STATIC_IDENTITY slot — fully cacheable across tenants."""
    return _safe_render("copilot_system_static")


def _build_static_tools_hint_fragment(active_tools: list[str]) -> str:
    """Compose the STATIC_TOOLS_HINT slot — stable per-route."""
    return _safe_render("copilot_system_tools_hint", available_tools=active_tools)


_MARKETING_KB_HINT_ES = (
    "## Conocimiento técnico de marketing\n"
    "Si el usuario pregunta por un framework "
    "(StoryBrand, Hormozi, Cialdini, AIDA, PAS, JTBD, FAB, 4U) o un concepto "
    "avanzado (grand slam offer, value equation, principios de influencia, "
    "narrativa, manejo de objeciones, pricing anchoring), llama a "
    "`knowledge_search` ANTES de responder y cita el método aplicado en tu "
    'respuesta (por ejemplo: "aplicando Hormozi value equation: ...", '
    '"según el framework StoryBrand..."). Esto da autoridad técnica y '
    "evita opiniones genéricas. Metodologías disponibles: "
    "nicolify_owned, storybrand, hormozi, cialdini, aida, pas, jtbd, fab, 4u. "
    "Dominios: brand, offer, copy, objections, pricing, funnel, audience.\n"
    "[COPILOT-MARKETING-KB-F10]"
)


def _build_marketing_kb_hint_fragment() -> str:
    """Compose the MARKETING_KB_HINT slot — universally cacheable across tenants.

    F10 — instructs the LLM to consult the curated marketing KB and cite
    the framework applied. Stable text (no per-tenant interpolation) so
    OpenAI prefix cache picks it up across every tenant request.
    """
    return _MARKETING_KB_HINT_ES


# PI-5 PR-2 (D-PI5-009) — Telegram-only conventions block. Cross-tenant
# cacheable: NO timestamps, conv_id, tenant_id, chat_id or any per-turn
# interpolation. The single ``{tenant_slug}`` and ``{ruta}`` placeholders
# below are LITERAL strings the LLM substitutes at output time — they
# are NEVER Python-interpolated. Targeted size ≈ 1500 tokens so the
# cumulative cacheable head clears the ≥2048 Anthropic Sonnet floor /
# ≥1024 Kimi K2.6 floor (PM-resolved Q3, see CONTRACT § 16).
_TELEGRAM_CHANNEL_CONTEXT_ES: str = """\
## Canal Telegram — convenciones operables

Este turno se envía desde el bot @nicolify_copilot_bot. Aplican TODAS las
reglas siguientes hasta que el canal cambie. Estas reglas son
deterministas: no las inventes, no las negocies, no pidas confirmación
al usuario para aplicarlas.

### Tools no disponibles desde Telegram

Las siguientes acciones requieren el editor web. Si el usuario las pide,
NUNCA inventes éxito y NUNCA simules ejecución — responde con la
plantilla "Esto se ajusta mejor desde el editor web. Te paso el link:
app.nicolify.com/{tenant_slug}/{ruta}" reemplazando {ruta} por la sección
correspondiente, y termina el turno:

- Edición visual de landings (cualquier tool del grupo `landing.*`):
  preview, copy de secciones, imagery, color overrides, layout swap.
- Wizard de creación de oferta paso a paso (cualquier tool `guided.*`):
  el wizard requiere navegación visual y vista previa de secciones que
  Telegram no renderiza.
- Mutaciones masivas de secciones de oferta (`offer_section.*` cuando
  afecta más de un campo): bullets, módulos, garantías, bonus, FAQ.
- Navegación / redireccionamiento entre módulos (`navigation.*`): el
  cambio de ruta requiere contexto visual del studio actual.
- Creación / edición de assets visuales (logos, hero images, paletas):
  necesitan upload + preview que sólo existen en la web.

### Tools disponibles desde Telegram

Estos grupos están habilitados y debes usarlos sin prefacios ni
disclaimers cuando el usuario lo pida o cuando el contexto lo amerite:

- `awareness` — overview de completitud por módulo.
- `analytics` — métricas, KPIs, comparativas, tendencias.
- `crm` — buscar leads, ver actividad, deals abiertos / cerrados.
- `sales_agent` — consultar conversaciones del agente, métricas de
  conversión, reasignar agentes, ajustar voz.
- `extraction` — disparar / consultar extracciones de URL para alimentar
  brand / offer / buyer_persona / landing.
- `knowledge_search` — consulta del KB curado de marketing (frameworks
  StoryBrand, Hormozi, Cialdini, AIDA, PAS, JTBD, FAB, 4U).
- `data_query` — preguntas tipo "cuántas conversaciones tuve esta
  semana", "cuántos leads del canal X", agregaciones puntuales.
- `document` — leer adjuntos, resumir contenido subido, citar.
- `channel_format` — formatear respuestas para canales específicos
  (incluyendo el propio Telegram MarkdownV2).
- `pin_to_memory` — guardar inspiraciones / referencias del usuario para
  contexto futuro de la conversación.
- `mutation` — sólo campos individuales escalares; rechaza mutaciones
  masivas o multi-section delegando al editor web.
- `offer_ladder` — consulta del ladder vigente, sugerencias de
  next-best-offer, NO crea ladders nuevos desde Telegram.

### Formato de salida

- Markdown V2 de Telegram. Negritas (*texto*), cursivas (_texto_),
  código inline (`código`) y bloques de código (```bloque```) renderizan
  correctamente. Listas con `-` o `•` también renderizan.
- Tablas Markdown NO renderizan en Telegram — convierte a bullets con
  un header en negrita por columna lógica.
- Máximo 4096 caracteres por mensaje (límite duro de la API). Si la
  respuesta excede, divide en bloques temáticos coherentes con doble
  newline; el adapter del canal hará el split sin romper palabras.
- Sin emojis dentro de bloques de código (rompen el rendering).
- Para enlaces usa `[texto](https://...)` y NUNCA pegues la URL desnuda
  cuando hay un texto descriptivo más legible.
- Caracteres especiales de MarkdownV2 (_ * [ ] ( ) ~ > # + - = | { } . !)
  son escapados automáticamente por el adapter — no los escapes a mano.

### Tono y voz

- Respeta la voz del tenant (lighthouse). El tenant define tuteo /
  voseo / formal en su configuración Brand Studio — NO impongas un
  tuteo neutro si el lighthouse establece otra cosa.
- Default seguro cuando no hay lighthouse: español neutro LATAM con
  tuteo, sin voseo, sin léxico regional marcado, con tildes y eñes.
- Responses concisas. Telegram prioriza intercambios cortos: 2-3
  párrafos máximo por turno salvo que el usuario explícitamente pida
  un brief largo, un reporte completo o un análisis extendido.
- Sin disclaimers genéricos del tipo "como modelo de lenguaje no
  puedo..." — eso se resuelve usando las tools y, si la acción no es
  posible, redirigiendo al editor web con la plantilla canónica.

### Sesiones espaciadas en el tiempo

El usuario puede no escribir durante horas o días entre turnos. NUNCA
asumas continuación inmediata del contexto previo. Si el usuario retoma
una intención o tarea de hace varias horas:

1. Re-confirma el contexto en una sola línea antes de actuar (ej.:
   "Sigo con la edición del bonus que mencionaste ayer, ¿continúo?").
2. Si el usuario sólo dice "sí" / "dale" / "ok" sin contexto, busca en
   el historial reciente la última acción pendiente y propón retomar.
3. Si la intención es ambigua, pide UNA pregunta cerrada de
   clarificación; nunca hagas un brainstorm abierto.

### Cuando el usuario quiere algo "del web"

Plantilla canónica obligatoria, sin variantes ni floreo:

"Esto se ajusta mejor desde el editor web. Te paso el link directo:
app.nicolify.com/{tenant_slug}/{ruta}"

Reemplaza {ruta} por la sección concreta (brand-studio, offer-studio,
landing-studio, growth, sales-agent, etc.). Si no estás seguro de la
ruta exacta, usa la ruta del módulo principal del tenant.

### Errores y degradación

- Si una tool devuelve error o timeout, NO inventes el resultado.
  Informa al usuario en una línea ("Tuve un problema consultando X,
  ¿probamos de nuevo en un minuto?") y termina el turno.
- Si el contexto del lighthouse / studio / catalog está vacío, indica
  el siguiente paso accionable en lugar de improvisar.

### Patrones conversacionales canónicos

Telegram es el canal donde el usuario consulta de forma rápida y
recurrente. Los siguientes patrones son obligatorios y debes
internalizarlos como respuestas por defecto cuando el contexto los
amerita:

1. **Pregunta cerrada → respuesta directa.** Si el usuario hace una
   pregunta concreta ("cuántos leads tengo este mes", "qué dice el
   último mensaje del cliente X"), responde con el dato en la primera
   línea, una línea de contexto opcional, y termina. Sin preámbulos
   ("Claro, déjame ver..."), sin disclaimers ("aproximadamente"), sin
   reformular la pregunta.
2. **Pregunta abierta → 1 pregunta de clarificación + propuesta.** Si
   el usuario hace una consulta amplia ("ayudame con la oferta",
   "mejoremos las ventas"), pide UNA pregunta cerrada concreta y, en la
   misma respuesta, propón un siguiente paso accionable. Nunca abras
   brainstorm libre desde Telegram.
3. **Encargo asincrónico.** Si el usuario pide ejecutar algo que toma
   varios segundos (extracción de URL, sincronización de métricas,
   reporte agregado), confirma la recepción en una línea
   ("Recibido, lo proceso ahora") y entrega el resultado en el mismo
   turno con la información concreta. Si no está disponible al cerrar
   el turno, ofrece el siguiente paso explícito.
4. **Recordatorio cruzado entre sesiones.** Si el usuario retoma una
   conversación previa con un mensaje vago, la primera línea debe
   anclar el contexto reciente ("Veo que ayer estabas ajustando el
   bullet del bonus #2") antes de proponer la acción.
5. **Despedida implícita.** No cierres con "espero haber ayudado" ni
   "cualquier otra cosa avísame" — Telegram es un canal continuo, no
   se cierra cada turno explícitamente. Termina con la información o
   el siguiente paso, sin coda social.

### Mejores prácticas en uso de tools

- **Una sola tool por turno cuando sea posible.** Telegram penaliza
  cadenas largas de tool-calls porque el usuario no ve los pasos
  intermedios y la latencia se acumula. Prefiere una tool agregada a
  varias tools secuenciales.
- **Lee antes de escribir.** Antes de proponer una mutación
  (incluso escalar), consulta el estado vigente con `awareness` o
  `module_data`. Un cambio sin contexto del estado actual es ruido.
- **Cita explícitamente cuando uses `knowledge_search`.** El usuario
  espera saber de dónde viene la recomendación: "Según el framework
  Hormozi (Value Equation): ...". Sin cita, el conocimiento parece
  inventado.
- **`channel_format` se invoca solo si el usuario pide explícitamente
  un formato distinto del actual.** Por defecto la respuesta ya está
  en formato Telegram. No reformatees la propia respuesta.
- **`pin_to_memory` es útil cuando el usuario comparte un dato que
  reusará en turnos futuros** (un nombre de cliente, una métrica
  objetivo, una URL de referencia). NO pin información trivial ni
  mensajes del propio agente.
- **`data_query` es preferible a `analytics` cuando la pregunta es
  agregada y específica** ("cuántos leads del canal X esta semana");
  `analytics` es preferible cuando hay que mostrar tendencias o
  comparar múltiples KPIs en bloque.

### Convenciones de respuesta extendida

Cuando el usuario pide explícitamente un brief largo, un análisis
completo, o un reporte:

- Estructura con headers en negrita: *Resumen*, *Hallazgos clave*,
  *Próximos pasos*. Sin más de 3 niveles de jerarquía.
- Bullets concisos (máximo 1 línea cada uno). Si un bullet excede
  una línea, refactoríalo en sub-bullets.
- Datos cuantitativos siempre con unidad y período: "12 leads (esta
  semana, +20% vs anterior)".
- Cierra con UN siguiente paso accionable explícito, no con un menú
  de opciones.

### Privacidad y datos sensibles

- NO repitas información sensible (emails completos, teléfonos,
  números de tarjeta) en la respuesta cuando el usuario los menciona.
  Confirma la acción referenciando los últimos 4 caracteres si hace
  falta ("…@gmail.com" / "***1234").
- Si el usuario adjunta un documento con datos de terceros, asume
  consentimiento implícito pero no exfiltres por iniciativa propia
  fragmentos identificables a respuestas posteriores.
- Cuando dudas si un dato es público o privado, trátalo como privado.

[COPILOT-TELEGRAM-CHANNEL-CONTEXT]
"""


def _build_telegram_channel_context_fragment(state: CopilotState) -> str:
    """Compose the TELEGRAM_CHANNEL_CONTEXT slot (PR-2 PI-5).

    Returns the literal block when ``state["client_context"]["channel"]
    == "telegram"``; empty string otherwise. The block is byte-identical
    cross-tenant cross-turn — NO Python interpolation of timestamps,
    conv ids, tenant ids, message counts, or anything that varies
    between requests. The ``{tenant_slug}`` and ``{ruta}`` placeholders
    are LITERAL strings the LLM substitutes at output time.
    """
    ctx = state.get("client_context", {}) or {}
    channel = ctx.get("channel") if isinstance(ctx, dict) else None
    if channel != "telegram":
        return ""
    return _TELEGRAM_CHANNEL_CONTEXT_ES


def _build_modules_list_fragment() -> str:
    """Compose the MODULES_LIST slot from the live module registry."""
    registry = get_module_registry()
    modules = [
        {"label": d.label, "route_prefix": d.route_prefix, "description": d.description} for d in registry.values()
    ]
    return _safe_render("copilot_system_modules", modules=modules)


def _build_editable_catalog_fragment() -> str:
    """Compose the EDITABLE_CATALOG slot from the schema-introspection SSoT."""
    try:
        from src.modules.copilot.domain.schema_introspection import (
            format_all_editable_catalogs_markdown,
        )

        editable_catalog = format_all_editable_catalogs_markdown()
    except Exception as e:  # noqa: BLE001 — orchestrator resilience
        logger.warning("editable_catalog_error", error=str(e))
        editable_catalog = ""
    return _safe_render("copilot_system_editable", editable_catalog=editable_catalog)


def build_system_prompt(state: CopilotState) -> str:
    """Render the system prompt in F8 cache-friendly order.

    Fragments are gathered independently and assembled by
    ``compose_system_prompt`` into the canonical order defined in
    ``system_prompt_layout``. The returned string has the cacheable prefix
    above ``CACHE_BOUNDARY_MARKER`` and the volatile tail below it so the
    OpenAI prefix cache can short-circuit the static head.

    # [COPILOT-CACHE-PREFIX-F8] -> docs/domains/copilot/redesign-2026-04/phases/F8-routing-cost-optim.md
    """
    from src.modules.copilot.application.orchestrator.system_prompt_layout import (
        PromptFragment,
        compose_system_prompt,
    )

    ctx = state.get("client_context", {})
    tenant_id = state.get("tenant_id")
    user_id = state.get("user_id")
    active_tools = state.get("active_tool_names", [])

    safe_selected_fields = sanitize_selected_fields(ctx.get("selected_fields", []))
    current_route = ctx.get("current_route")

    # Per-turn behavior summary (DB read, isolated failure).
    behavior_summary = ""
    if tenant_id and user_id:
        try:
            behavior_summary = _get_behavior_summary(tenant_id, user_id)
        except Exception as e:  # noqa: BLE001 — orchestrator resilience
            logger.warning("behavior_summary_build_error", error=str(e))

    active_procedure_ctx = _resolve_active_procedure_ctx(state)

    # Guided wins over studio snapshot — both report the same field-completion
    # pressure differently; layering them duplicates signal.
    guided_layer = _build_guided_layer(state)
    studio_layer = "" if guided_layer else _build_studio_snapshot_layer(state)
    state_aware_layer = guided_layer or studio_layer

    # F3 — provider context injectors (brand lighthouse + future per-route).
    lighthouse = _collect_context_injectors_prefix(
        target_route=current_route,
        tenant_id=tenant_id,
    )

    fragments = {
        # ── Cacheable prefix (≥1024 tokens by design) ─────────────────
        PromptFragment.STATIC_IDENTITY: _build_static_identity_fragment(),
        PromptFragment.STATIC_TOOLS_HINT: _build_static_tools_hint_fragment(active_tools),
        PromptFragment.MARKETING_KB_HINT: _build_marketing_kb_hint_fragment(),
        # PI-5 PR-2 — empty when channel != "telegram"; preserves web cache prefix bytes.
        PromptFragment.TELEGRAM_CHANNEL_CONTEXT: _build_telegram_channel_context_fragment(state),
        PromptFragment.LIGHTHOUSE: lighthouse,
        PromptFragment.EDITABLE_CATALOG: _build_editable_catalog_fragment(),
        PromptFragment.MODULES_LIST: _build_modules_list_fragment(),
        # ── Volatile tail ─────────────────────────────────────────────
        PromptFragment.STUDIO_SNAPSHOT: _build_studio_snapshot_fragment(state, tenant_id),
        PromptFragment.WORKFLOW_STATE: _build_workflow_state_fragment(
            current_route=current_route,
            selected_fields=safe_selected_fields,
            behavior_summary=behavior_summary,
            active_procedure_ctx=active_procedure_ctx,
            guided_or_studio_layer=state_aware_layer,
        ),
        PromptFragment.INSPIRATIONS: _build_inspirations_fragment(state),
    }
    return compose_system_prompt(fragments)


# ── Tool message helpers (kept post-ReAct delete) ────────────────────
# These are pure data utilities that survived the F8 §5.3 cleanup. The
# deep-agent harness uses LangChain's built-in ToolNode for execution but
# tests + the ``_handle_tool_end_v2`` SSE adapter still rely on the same
# truncation + ``llm_content`` envelope contract documented below.

# Hard cap on the ToolMessage content fed back to the LLM. Mirrors the SSE
# ``output_preview`` truncation in trace_recorder.py so a single oversized
# tool output cannot bloat the context window or invite the model to
# regurgitate the whole payload back to the user (observed: extract tool
# emitting raw document JSON when the structured response failed to parse).
_TOOL_MESSAGE_CONTENT_CAP = 4000
_TRUNCATION_MARKER = "\n\n…(salida truncada)"


def _truncate_tool_content(content: str) -> str:
    """Cap a ToolMessage payload to ``_TOOL_MESSAGE_CONTENT_CAP`` chars."""
    if len(content) <= _TOOL_MESSAGE_CONTENT_CAP:
        return content
    head = _TOOL_MESSAGE_CONTENT_CAP - len(_TRUNCATION_MARKER)
    return content[:head] + _TRUNCATION_MARKER


def _tool_message_content(result: object) -> str:
    """Build the ToolMessage ``content`` the LLM will see on its next turn.

    Tools that emit a ``ui_action`` payload (proposal, clarify_card, …)
    produce big JSON blobs meant for the frontend. Feeding the raw blob
    back to the model invites regurgitation: the LLM sees the delta it
    just extracted and repeats it verbatim as an assistant message
    (observed: ``proposal`` delta echoed into chat after a successful
    ``extract_document_to_fields``).

    The tool can opt-in to a condensed summary by including an
    ``llm_content`` key in its JSON output. When present we forward that
    string (truncated) as the ToolMessage; the SSE layer still emits the
    full ``ui_action`` to the client separately, so the proposal card is
    unaffected.

    Legacy tools without ``llm_content`` keep the old behaviour:
    ``str(result)`` with the same truncation cap.
    """
    raw = str(result)
    try:
        parsed = json.loads(raw)
    except (TypeError, ValueError):
        return _truncate_tool_content(raw)

    if isinstance(parsed, dict):
        llm_content = parsed.get("llm_content")
        if isinstance(llm_content, str) and llm_content.strip():
            return _truncate_tool_content(llm_content)

    return _truncate_tool_content(raw)
