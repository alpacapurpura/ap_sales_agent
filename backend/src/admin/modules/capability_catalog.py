"""Streamlit admin: Capability Catalog — all copilot capabilities in one place."""

import pandas as pd
import streamlit as st


def render_capability_catalog() -> None:
    """Render the copilot capability catalog dashboard."""
    st.title("🔧 Capacidades del Copilot")

    # KPIs — static counts from code
    try:
        from src.modules.copilot.application.procedures.brand_setup import BRAND_SETUP
        from src.modules.copilot.application.procedures.first_setup import FIRST_SETUP
        from src.modules.copilot.application.procedures.offer_creation import (
            OFFER_CREATION,
        )
        from src.modules.copilot.application.tools.registry import (
            ROUTE_TOOL_MAP,
            TOOL_GROUPS,
            get_all_tools,
        )
        from src.modules.copilot.domain.module_registry import get_module_registry

        all_tools = get_all_tools()
        procedures = [BRAND_SETUP, FIRST_SETUP, OFFER_CREATION]
        registry = get_module_registry()

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(
            "Tools",
            len(all_tools),
            help="Herramientas disponibles para el copilot",
        )
        col2.metric("Grupos", len(TOOL_GROUPS), help="Categorias de herramientas")
        col3.metric(
            "Procedimientos",
            len(procedures),
            help="Flujos guiados paso a paso",
        )
        col4.metric("Nudge Rules", 4, help="Reglas de sugerencias proactivas")
        col5.metric(
            "Modulos",
            len(registry),
            help="Modulos que el copilot puede introspeccionar",
        )

    except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
        st.error(f"Error cargando capacidades: {e}")
        return

    # Group labels — F10 update reflects Redesign 2026-04 toolset.
    group_labels = {
        "navigation": (
            "🧭 Navegacion",
            "Herramientas para navegar al usuario a paginas y campos",
        ),
        "awareness": (
            "👁️ Awareness",
            "Introspección del estado de configuracion del tenant",
        ),
        "mutation": ("✏️ Mutacion", "Proponer cambios a campos del formulario"),
        "module_data": ("📦 Datos de Modulo", "Leer datos de módulos del tenant"),
        "analytics": ("📊 Analytics", "Métricas de marketing y ventas"),
        "crm": ("👥 CRM", "Leads, clientes y pipeline"),
        "sales_agent": ("🤖 Sales Agent", "Rendimiento del agente de ventas IA"),
        "connections": ("🔗 Conexiones", "Canales e integraciones externas"),
        "landing": ("📄 Landing Pages", "Páginas de aterrizaje"),
        "procedure": ("📋 Procedimientos", "Flujos guiados paso a paso"),
        "knowledge": (
            "📚 Marketing KB (F10)",
            "Búsqueda en `nicolify_marketing_kb` (curado por Nicolify, "
            "tenant-agnóstico). Filtra por dominio (brand/offer/copy/...) "
            "y metodología (StoryBrand/Hormozi/Cialdini/AIDA/PAS/JTBD/FAB/4U).",
        ),
        "offer_ladder": ("🪜 Offer Ladder", "Secuencias de ofertas en escalera"),
        "offer_section": ("🧱 Offer Sections", "Editor por sección del studio de ofertas"),
        "guided": ("🧑‍🏫 Guided Setup", "Onboarding paso a paso (post-interview)"),
        "assets": ("🖼️ Assets", "Galería de imágenes/audios/docs subidos por el tenant"),
        "document": ("📄 Document Read", "Lectura on-demand de docs adjuntos"),
        "shared_tools": ("🧰 Shared", "Primitivas conversacionales (clarify, confirm, ...)"),
        "extraction": ("🔌 Extraction", "URL/Doc → studio (rellenar campos automático)"),
        "url_context": (
            "🔗 URL Inspirations (F4)",
            "`fetch_url` + `pin_to_memory` — pegás un link de competencia, "
            "queda como inspiración persistente en `/inspirations/*`.",
        ),
        "data_query": (
            "❓ Q&A datos tenant (F5)",
            "`ask_tenant_data` — pipeline determinístico (intent → plan → "
            "execute → synth) con 2 LLM calls FAST. Responde 'cuántas personas "
            "escribieron', 'dame resumen del programa X', etc.",
        ),
        "channel_format": (
            "📱 Channel Formatter (F7)",
            "`format_for_channel` — adapta texto a chat/whatsapp/email/sms/voice/"
            "instagram_dm/telegram. Determinístico (sin LLM call).",
        ),
    }

    st.divider()

    # TABS
    (
        tab_tools,
        tab_routes,
        tab_procs,
        tab_nudges,
        tab_ui,
        tab_usage,
        tab_redesign,
    ) = st.tabs(
        [
            "🛠️ Tools",
            "🗺️ Mapeo de Rutas",
            "📋 Procedimientos",
            "💡 Nudges",
            "🎨 Componentes UI",
            "📊 Uso de Tools",
            "🚀 Redesign 2026-04",
        ],
    )

    # ── Tab 1: Tools ──────────────────────────────────────────────────────
    with tab_tools:
        st.header("Herramientas del Copilot")
        st.caption(
            "Agrupadas por categoria. Cada tool es una funcion que el LLM puede invocar.",
        )

        for group_name, tools in TOOL_GROUPS.items():
            label, desc = group_labels.get(group_name, (group_name, ""))
            with st.expander(f"{label} ({len(tools)} tools)", expanded=False):
                st.caption(desc)
                for tool in tools:
                    st.markdown(f"**`{tool.name}`** — {tool.description}")

    # ── Tab 2: Route Map ──────────────────────────────────────────────────
    with tab_routes:
        st.header("Mapeo de Rutas")
        st.caption(
            "Muestra que herramientas tiene disponibles el copilot segun la pagina donde este el usuario",
        )

        # Build matrix
        group_names = list(TOOL_GROUPS.keys())
        # Create short labels for columns
        short_labels = {
            "navigation": "nav",
            "awareness": "aware",
            "mutation": "mut",
            "module_data": "mod",
            "analytics": "anal",
            "crm": "crm",
            "sales_agent": "sales",
            "connections": "conn",
            "landing": "land",
            "procedure": "proc",
            "knowledge": "know",
        }

        rows = []
        for route, groups in ROUTE_TOOL_MAP.items():
            row = {"Ruta": route}
            for gn in group_names:
                col_name = short_labels.get(gn, gn)
                row[col_name] = "✅" if gn in groups else ""
            rows.append(row)

        df = pd.DataFrame(rows)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # ── Tab 3: Procedures ─────────────────────────────────────────────────
    with tab_procs:
        st.header("Procedimientos Guiados")
        st.caption("Flujos paso a paso que el copilot guia al usuario")

        for proc in procedures:
            st.subheader(f"📋 {proc.name.upper()} (`{proc.procedure_id}`)")
            st.write(f"*{proc.description}*")
            st.write(f"**{len(proc.steps)} pasos:**")

            for i, step in enumerate(proc.steps, 1):
                with st.container():
                    st.markdown(
                        f"**{i}. `{step.step_id}`** — {step.instruction}\n\n"
                        f"📍 Ruta: `{step.route_hint}` | "
                        f"Validacion: `{step.validation}` | "
                        f"Modulo: `{step.module_id}`",
                    )
                    if step.tips:
                        tips_str = " | ".join(f'"{t}"' for t in step.tips)
                        st.caption(f"💡 {tips_str}")
            st.divider()

    # ── Tab 4: Nudges ─────────────────────────────────────────────────────
    with tab_nudges:
        st.header("Reglas de Nudges Proactivos")
        st.caption("Sugerencias automaticas basadas en el estado del modulo")

        nudge_rules = [
            {
                "name": "Modulo Vacio (EmptyModuleNudge)",
                "priority": "🔴 1 (maxima)",
                "trigger": "El modulo de la ruta actual tiene 0% de completitud",
                "action": "Muestra banner sugiriendo configurar el modulo",
                "example": '"Tu Brand Studio esta vacio — Configura tu identidad de marca..."',
            },
            {
                "name": "Brecha Cross-Modulo: Brand→Offer",
                "priority": "🟡 2",
                "trigger": "Brand >30% configurado pero Offer esta vacio",
                "action": "Sugiere crear la primera oferta",
                "example": '"Tu marca esta configurada, ¿y tus ofertas?"',
            },
            {
                "name": "Brecha Cross-Modulo: Offer→Connections",
                "priority": "🟡 3",
                "trigger": "Brand y Offer configurados pero sin conexiones",
                "action": "Sugiere conectar el primer canal",
                "example": '"Conecta tu primer canal de ventas"',
            },
            {
                "name": "Modulo Incompleto (IncompleteModuleNudge)",
                "priority": "🟢 4",
                "trigger": "El modulo tiene entre 1-30% de completitud",
                "action": "Muestra banner sugiriendo completar la configuracion",
                "example": '"Tu Brand Studio esta al 20% — Completa la configuracion..."',
            },
        ]

        for rule in nudge_rules:
            with st.container(border=True):
                st.markdown(f"### {rule['name']}")
                col1, col2 = st.columns(2)
                col1.write(f"**Prioridad:** {rule['priority']}")
                col2.write(f"**Trigger:** {rule['trigger']}")
                st.write(f"**Accion:** {rule['action']}")
                st.info(f"Ejemplo: {rule['example']}")

    # ── Tab 5: UI Components ──────────────────────────────────────────────
    with tab_ui:
        st.header("Componentes UI del Copilot")
        st.caption("Tipos de respuestas visuales que el copilot puede renderizar")

        components = [
            (
                "📊 MetricSummaryCard",
                "metric_summary",
                "Grid de metricas con tendencias y comparaciones",
            ),
            (
                "📋 ComparisonTable",
                "comparison",
                "Tabla comparativa con fila recomendada resaltada",
            ),
            (
                "✅ ProgressChecklist",
                "checklist",
                "Lista de pasos clickeable con navegacion integrada",
            ),
            (
                "🔘 MultiOptionSelector",
                "multi_option",
                "Selector de opciones con confirmacion del usuario",
            ),
            (
                "🧭 NavigationCard",
                "navigate",
                "Card con boton para navegar a una ruta especifica",
            ),
            (
                "✏️ ProposalCard",
                "proposal",
                "Propuesta de cambios con botones aceptar/rechazar por campo",
            ),
        ]

        for label, action_type, description in components:
            with st.container(border=True):
                st.markdown(f"### {label}")
                st.code(f'ui_action type: "{action_type}"', language="json")
                st.write(description)

    # ── Tab 6: Tool Usage (dynamic) ───────────────────────────────────────
    with tab_usage:
        st.header("Uso de Tools en Conversaciones")
        st.caption("Analiza conversaciones reales para ver que tools se invocan mas")

        if st.button("Analizar Uso", key="cap_usage_btn"):
            try:
                from src.core.database import SessionLocal
                from src.modules.copilot.infrastructure.repositories.conversation_repository import (
                    ConversationRepository,
                )

                db = SessionLocal()
                try:
                    repo = ConversationRepository(db)
                    convs = repo.list_all_paginated(limit=200)

                    tool_counts: dict[str, int] = {}
                    total_convs_with_tools = 0

                    for conv in convs:
                        msgs = conv.messages or []
                        conv_has_tools = False
                        for msg in msgs:
                            if isinstance(msg, dict) and msg.get("role") == "assistant":
                                tool_calls = msg.get("tool_calls", [])
                                if isinstance(tool_calls, list):
                                    for tc in tool_calls:
                                        name = tc.get("name", "unknown") if isinstance(tc, dict) else "unknown"
                                        tool_counts[name] = tool_counts.get(name, 0) + 1
                                        conv_has_tools = True
                        if conv_has_tools:
                            total_convs_with_tools += 1

                    if tool_counts:
                        total_invocations = sum(tool_counts.values())
                        rows = []
                        for name, count in sorted(
                            tool_counts.items(),
                            key=lambda x: -x[1],
                        ):
                            rows.append(
                                {
                                    "Tool": name,
                                    "Invocaciones": count,
                                    "% del Total": f"{round(count / total_invocations * 100, 1)}%",
                                    "Avg/Conv": round(
                                        count / max(total_convs_with_tools, 1),
                                        1,
                                    ),
                                },
                            )

                        df = pd.DataFrame(rows)
                        st.dataframe(df, use_container_width=True, hide_index=True)

                        # Bar chart — top 15
                        chart_df = pd.DataFrame(rows[:15])
                        st.bar_chart(chart_df.set_index("Tool")["Invocaciones"])
                    else:
                        st.info(
                            "No se encontraron invocaciones de tools en las conversaciones.",
                        )
                finally:
                    db.close()
            except Exception as e:  # noqa: BLE001 — Streamlit UI error boundary
                st.error(f"Error: {e}")

    # ── Tab 7: Redesign 2026-04 — fase by fase ────────────────────────────
    with tab_redesign:
        st.header("Copilot Redesign 2026-04 — 'Claude Code de Marketing'")
        st.caption(
            "Plan de 11 fases (F0–F10) ejecutado entre marzo y abril 2026. "
            "Cada fase entrega una rebanada de la topología destino sin "
            "tocar el §3 (lo que NO se toca). Estado al cierre F10:",
        )

        phases = [
            (
                "F0 · Audit + freeze",
                "Línea base: cross-module imports congelados, scope creep "
                "evidenciado, decisión de descentralizar via providers.",
            ),
            (
                "F1 · Provider pattern + discovery",
                "Cada módulo trae su `copilot_provider/` (tools, workflows, "
                "summary, context_inject). Discovery filesystem scan + entry "
                "points. Ratchet `copilot → módulo` shrunk 28 → 22 frozen.",
            ),
            (
                "F2 · Deep Agents harness",
                "`build_deep_agent_graph(state)` compila per turn con "
                "deepagents 0.5.3. `write_todos` emite `plan_card` desde args. "
                "Migración 067 + `copilot_pinned_memory` listas para F4.",
            ),
            (
                "F3 · Brand summary lighthouse",
                "Tabla `brand_summary` + ARQ regen + judge sync (length + "
                "voseo regex). Inyectado como prefix cacheable en system "
                "prompt — el copilot 'respira' la marca.",
            ),
            (
                "F4 · URL contextual + scratchpad",
                "Tool `fetch_url(url)` (httpx + trafilatura 2.0 + LLM "
                "FAST analyzer + brand-relevance score). Tabla "
                "`copilot_inspiration` (FIFO 5 visibles, cap 10/conv). "
                "Tool `pin_to_memory(slug)` promueve a memoria persistente.",
            ),
            (
                "F5 · ask_tenant_data subgraph",
                "Pipeline determinístico de 6 pasos con SOLO 2 LLM calls "
                "FAST (intent + synth). 3 kinds soportados: `offer_lookup`, "
                "`lead_count`, `conversation_count`. Cache TTL 60s.",
            ),
            (
                "F6 · Workflow unification",
                "`Workflow` dataclass declarativo + `WorkflowEngine` Python "
                "+ migración 071 (`workflow_state` JSONB con dual-read "
                "fallback a `procedure_state` legacy). 4 sistemas conviven "
                "hasta el cutover.",
            ),
            (
                "F7 · Channel formatter registry",
                "`ChannelFormat` registry (chat/whatsapp/email/sms/voice/"
                "instagram_dm/telegram). `format_for_channel(content, channel)` "
                "tool determinístico — strip markdown + truncate + emoji "
                "según política del canal.",
            ),
            (
                "F8 · Routing + cost optim",
                "`LLMClassifier` NANO fallback. Reorden cache-friendly del "
                "system prompt (≥1024 tokens prefix → OpenAI prefix cache). "
                "Borrado ReAct legacy + flag dispatch. Migración FE a SSE v2 "
                "block_*. Admin `/copilot-routing` con tier distribution.",
            ),
            (
                "F9 · Quality + observability",
                "`CopilotJudge` (NANO + 4-dim CoT rubric). 20 goldens "
                "across 8 categorías. ARQ weekly cron lunes 05:00 UTC. "
                "Trazas `node_enter`/`node_exit` per turn. Admin "
                "`/copilot-quality` con KPIs precomputados (no LLM en render).",
            ),
            (
                "F10 · Marketing KB curado",
                "Colección `nicolify_marketing_kb` tenant-agnóstica. "
                "Tool `knowledge_search(query, domain?, methodology?)` "
                "(refactor del legacy con scope per-tenant). Chunker "
                "**breadcrumb-aware** (contextual retrieval state-of-art "
                "abril 2026): cada chunk lleva `# H1 > ## H2 > ### H3` "
                "como prefix de embed. 31 docs base curados (StoryBrand, "
                "Hormozi, Cialdini, AIDA, PAS, JTBD, FAB, 4U, archetypes, "
                "objections, funnel, pricing, email, WhatsApp). Endpoint "
                "tenant `/api/v1/copilot/ingest` cerrado (HTTP 410 Gone).",
            ),
        ]

        for title, body in phases:
            with st.container(border=True):
                st.markdown(f"### {title}")
                st.write(body)

        st.divider()
        st.subheader("Tools transversales nuevos (F4–F10)")
        st.markdown(
            "- `fetch_url(url, why?)` — F4 — agrega inspiración persistente.\n"
            "- `pin_to_memory(slug)` — F4 — promueve a memoria persistente.\n"
            "- `ask_tenant_data(question, output_channel?)` — F5 — Q&A datos del tenant.\n"
            "- `format_for_channel(content, channel_id)` — F7 — adapta texto al canal.\n"
            "- `knowledge_search(query, domain?, methodology?, limit?)` — F10 — KB curado.\n",
        )

        st.subheader("Anchors del redesign")
        st.code(
            "COPILOT-PROVIDER-PATTERN  · F1\n"
            "COPILOT-DEEP-AGENT-V2     · F2\n"
            "COPILOT-BRAND-SUMMARY-F3  · F3\n"
            "COPILOT-INSPIRATION-F4    · F4\n"
            "COPILOT-FETCH-URL-F4      · F4\n"
            "COPILOT-ASK-TENANT-DATA-F5 · F5\n"
            "COPILOT-WORKFLOW-F6       · F6\n"
            "COPILOT-CHANNEL-FORMATTER-F7 · F7\n"
            "COPILOT-LLM-CLASSIFIER-F8 · F8\n"
            "COPILOT-CACHE-PREFIX-F8   · F8\n"
            "COPILOT-SSE-V2-ONLY-F8    · F8\n"
            "COPILOT-LLM-JUDGE-F9      · F9\n"
            "COPILOT-WORKFLOW-METRIC-F9 · F9\n"
            "COPILOT-NODE-TRACE-F9     · F9\n"
            "COPILOT-MARKETING-KB-F10  · F10",
            language="text",
        )
