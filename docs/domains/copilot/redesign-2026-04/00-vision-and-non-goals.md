# Visión + lo que NO se toca

## §1 Visión: "Claude Code de Marketing"

El usuario debe sentir, conversando con el copilot, lo mismo que un dev siente conversando con Claude Code:

- **Calidad de respuesta**: no opinión genérica. Responde como experto que respira la marca del usuario y aplica metodología.
- **Profundidad bajo demanda**: tareas chicas (chat) en mini, auditorías y diseños en HEAVY con sub-agentes y planning visible.
- **Memoria viva**: la marca es el faro. Cada vez que crea offer/landing/campaign, lo hace con la marca presente. No hay que recordársela.
- **Q&A sobre datos propios**: "dame resumen del programa propósito-prosperidad para WhatsApp", "cuántas personas escribieron esta semana", "qué ofertas tengo activas con descuento". Resuelto con tool agentic, no con SQL crudo en prompt.
- **URL contextual**: pegás link de competencia y queda como inspiración persistente. "Rescata el bloque de testimonios de mujerescoraje" funciona en turn 7 igual que en turn 2.
- **Diseño guiado adaptive**: cuando entrego URL/doc, el copilot analiza primero, pregunta 1 a 1 lo que falta (cada respuesta cambia la siguiente pregunta), y recién después propone cambios — actuando como diseñador, no como rellenador.
- **RAG técnico curado**: cuando tiene duda de framework (StoryBrand, Hormozi, Cialdini, metodología propia Nicolify), busca en su base de conocimiento curada por nosotros y cita método aplicado.
- **Plug-in friendly**: agregar mañana "creador de campañas en growth" o "auditor de funnel" no requiere editar `copilot/`. Cada módulo trae su provider.

---

## §2 Capacidades target (mapa)

| Capacidad | Hoy | Target |
|---|---|---|
| URL contextual persistente | NO | tool `fetch_url` + scratchpad `/inspirations/*` + system prompt enriquecido |
| Brand "lighthouse" siempre on | NO (solo % completion) | tabla `brand_summary` + event-driven regen + auto-inject |
| Q&A datos tenant fuzzy + time | PARCIAL | subgraph `ask_tenant_data` (intent → resolve → query → state-check → synthesize) |
| Diseño adaptive con clarify loop | NO | Workflow estandarizado, max-questions cap, cada respuesta refina pregunta |
| RAG marketing curado | corpus VACÍO + tenants pueden contaminar | `nicolify_marketing_kb` tenant-agnostic, ingest cerrado a admin |
| Plug-in tools por módulo | NO (todo hardcoded en copilot/) | provider pattern via Python entry_points |
| Workflow unificado (guided + procedure + extraction) | 3 sistemas paralelos | 1 concepto `Workflow` declarativo |
| Channel-aware output (chat\|whatsapp\|email\|sms) | NO | registry `OutputChannelFormat` + synthesizer node |
| Subagentes para tareas pesadas | NO | `langchain-deepagents` harness: planning + scratchpad + spawn_subagent |

---

## §3 Lo que NO se toca (LISTA EXHAUSTIVA)

> Esto funciona. Cualquier fase que lo modifique sin justificación documentada **se reverta**.

### §3.1 Frontend / UX

- **Sidebar 3-state** (`collapsed` / `rail` / `full`) — `frontend/src/features/copilot/components/CopilotSidebar.tsx`. Ver `docs/domains/copilot/UI-SPEC.md` v2.
- **Atajos teclado** (C/R/F/N/Ctrl+K/Esc).
- **Mobile sheet behavior**.
- **Conversation history pagination** + secciones Hoy/Ayer/Últimos 7d/Anterior.
- **Composer multimodal** (input texto + adjuntos + grabación voz).
- **Voice dual-mode UI** (recorder, waveform, transcript playback).
- **Renderer multimodal** de bloques (`TextBlock`, `ImageBlock`, `AudioBlock`, `VideoBlock`, `DocumentBlock`, `TableBlock`, `CodeBlock`, `CitationBlock`, `QuoteReplyBlock`).
- **Cards UI** existentes: `proposal`, `clarify_card`, `preview_update`, `plan_card`. Pueden recibir nuevos campos pero el contrato visual se preserva.
- **Tailwind theme + Shadcn UI** stack.

### §3.2 Backend infra

- **AssetsService** + R2 storage + MIME detection + AI metadata pipeline. Voice-upload-and-transcribe canonical endpoint.
- **`BaseChannel.send_rich_message`** con default flatten — adapters viejos siguen funcionando.
- **SSE v2 protocol** (`block_start`, `block_delta`, `block_end`, `message_start`, `message_end`). Coexistencia con legacy permitida hasta P7.
- **Context Window Builder** + **Rolling Summarizer** (`memory/context_window_builder.py` + `memory/rolling_summarizer.py`). Refinar parámetros OK; no rehacer.
- **Trace recorder + observability** (`copilot_trace_event` + admin Streamlit `/trazas`). Extender (más eventos), no rehacer.
- **4-tier model router** (NANO/MINI/REASONING/HEAVY) — `domain/model_tier.py` + `application/router/`. Refinar reglas y agregar `LLMClassifier` fallback OK.
- **Conversation persistence** (`copilot_conversations.messages` JSONB + `procedure_state` JSONB) — el storage queda. Renames OK.
- **Routing telemetry** (`copilot_routing_log`).
- **Mutation journal** (`copilot_mutation_journal`) + endpoint `/revert`.
- **Anchor comments `[COPILOT-*]`** + arch test que los enforce.
- **Tenant isolation** (`X-Tenant-ID` middleware, filter en queries).

### §3.3 Patrones conceptualmente correctos (descentralizar, no eliminar)

- **MODULE_REGISTRY** (`domain/module_registry.py`) — el patrón es bueno. Se descentraliza vía providers (cada módulo se auto-registra). NO se elimina el concepto de "registro de módulos disponibles".
- **`schema_introspection.py`** + **`editable_fields` ports** — siguen siendo SSoT lectura/escritura. Los providers los siguen usando.
- **`navigation_map.py`** declarativo — sigue siendo SSoT route → page → section → fields.
- **Existing extraction pipelines** en ARQ workers (Brand/Offer/Asset extraction) — los workflows nuevos los reusan, no los reescriben.
- **Skills + Rules + Hooks loaders** (`skills_loader.py`, `rules_loader.py`, `in_memory_hook_registry.py`) — si están en uso real, mantener. Si dead code confirmado en F0, eliminar.

### §3.4 Estándares cross-stack

- **Spanish neutro LatAm** en todo user-facing (ver `.claude/rules/spanish-text.md`).
- **DDD inside-out** en backend modules.
- **FSD-Lite** en frontend.
- **Conventional Commits** + `development` branch único.
- **Native dev tools** (lint/tests/type-check WSL, nunca `docker exec`).

---

## §4 Definición de "terminado" para cada fase

Una fase está terminada **solo si**:

1. Código mergeado a `development` con tests verdes (`/test-backend` + `/test-frontend` o equivalente del scope).
2. Arch tests existentes pasan + nuevos tests fitness agregados donde correspondan.
3. Migraciones idempotentes verificadas en clone DB si aplica.
4. **Nada de §3 fue tocado**, o si fue tocado, está justificado en `learnings/F#-*.md` con razón + diff.
5. Entregable user-visible (o dev-visible) verificado manualmente.
6. Documento `learnings/F#-*.md` con plantilla completa.
7. Documento `prompts/F{#+1}-start.md` listo para arrancar siguiente fase.

Sin alguno de los 7 puntos, la fase **no se cierra**.
