# DECISIONS LOG

## 2026-04-22 — Initial proposal (first pass)

User brief: copilot extraction silenciosa; user no ve progreso ni cierre. Restricción: no romper estructura actual.
Approach: generic `AsyncToolJob` primitive applicable to any extraction source.
7 proposals drafted. v1 = 1+2+3+6.

## 2026-04-22 — Design iteration (scope + reuse + genericity)

User corrections:
1. `extract_from_url` no es brand-only. Debe poder targetear brand / offer / asset y soportar entidad completa / sección / campo + reemplazar vs. llenar vacíos vs. sugerir.
2. `extract_from_doc` debe existir con el mismo contract — nada de `extract_offer_from_doc`.
3. UX debe cubrir el caso "estoy en Identidad pero extraigo todo el brand" — feedback en secciones no visibles.

**Second research pass (before editing anything)** surfaced:
- `extract_from_url` YA acepta `module: Literal["brand", "offer"]` + `scope: "full"|"visuals"` + `mode: "initial"|"update"`. Solo faltan `section`, `field`, `entity_id`, y ampliar los Literals. **Extender, no reemplazar.**
- Docstring del tool YA instruye al LLM a llamar `clarify` antes de despachar. Minimal delta: enriquecer las opciones con el axis de scope.
- `BRAND_SECTIONS`/`OFFER_SECTIONS` son catálogos tipados con `slug` — directamente utilizables para el mapping `current_route → default section`.
- `BrandStudioNavRail.tsx:19` tiene el comentario explícito *"optional completion preview"* — el slot fue anticipado, nunca construido. Proposal 4 lo llena.
- `NavigationCard.tsx` YA existe como pill pequeña con `MapPin` + `ArrowRight` — sirve tal cual para las inline section-complete pills. **Cero componente nuevo para Proposal 5.**
- `ClarifyCard.tsx` soporta multi-item (`items.slice(0, 4)`) — el scope picker cabe sin componente nuevo.
- `copilot-highlight` CSS class ya existe (`globals.css:262-267`) — reuso directo para field shimmer.
- `pollExtractionStatus` helper huérfano en `ai-actions.ts:92-101` — generalizable a `pollJobStatus`.
- Card kinds existentes: `proposal | alternatives | clarify | checkpoint | interview_complete | metric_summary | comparison | checklist | multi_option | navigation`. Solo **1 nuevo kind** (`extraction_summary`) — el resto se reusa.

### Decisiones tomadas

| # | Decisión | Razón |
|---|---|---|
| D1 | Extender `extract_from_url` en lugar de reemplazar | Backwards compat + pertinencia (`module` ya multiplexa) |
| D2 | Nuevo `extract_from_doc` paralelo, wraps `extract_document_to_fields` existente bajo contract unificado | Evita duplicar lógica del guided extract |
| D3 | `mode` agrega `"suggest"` — mantiene `"initial"` y `"update"` | Backwards compat; `"suggest"` es un use-case nuevo legítimo |
| D4 | Deprecar `offer_id`, aliasar a `entity_id` genérico | Unificación, no rompe calls existentes |
| D5 | Scope picker = reuso directo de `ClarifyCard` con 2 items | Zero componente nuevo, zero LLM retraining |
| D6 | Inline section-complete pills = reuso de `card_kind="navigation"` + `NavigationCard.tsx` sin cambios | Zero componente nuevo |
| D7 | `extraction_summary` = nuevo `CardKind` y componente | Es único en forma (barras de cobertura + CTAs) — no cabe en ningún card existente |
| D8 | Section badges = extensión de `SectionRow` en ambos NavRails | El slot fue anticipado por el autor original (`BrandStudioNavRail.tsx:19`) |
| D9 | Proposal 7 (section badges) promoted P3 → P1 | Sin esto, el caso "extraigo todo pero estoy en una sección" queda ciego |
| D10 | Nueva Proposal 5 (inline pills) agregada a v1 | Refuerzo del mismo caso — feedback por sección en el chat history |
| D11 | v1 bundle = 0+1+2+3+4+5+6 (antes 1+2+3+6) | Cubre todos los issues del user |
| D12 | Worker emite summary card + section pills como mensajes persistidos | Parity con conversation history, sobrevive reload |
| D13 | Idempotency key en mensajes del worker (`f"summary:{job_id}"`) | ARQ puede reintentar — no duplicar cards |

### Rejected / deferred

- **Custom `extract_scope` card kind** con 2 radio groups en un solo card: descartado. ClarifyCard con 2 items es indistinguible para el user y cero código nuevo.
- **WebSocket/SSE push para progreso**: descartado para v1. Polling 2s es suficiente dado el throughput del caso.
- **Streaming de tokens del LLM dentro del chip** (Perplexity-style): descartado. Overkill para v1.
- **Job queue UI global** (lista todos los jobs running/done): deferido a v3.
- **Per-field undo**: fuera de scope. El conversation-level undo de `MutationUndoButton` sigue siendo el mecanismo.

### Pendiente de aprobación

- [x] User OK a v1 bundle definitivo (0+1+2+3+4+5+6). → Aprobado 2026-04-22.
- [x] User OK a extender `extract_from_url`. → Aprobado.
- [x] Implementación. → Ejecutada.

---

## 2026-04-22 (late) — Implementation round

### Cómo se ejecutó
- `nicolify-backend` + `nicolify-frontend` en paralelo con briefs apuntando a los specs como contrato.
- Segunda invocación `nicolify-frontend` para Phase 3 (NavRail badges).
- Auditoría manual (auditor agent se quedó sin budget, orchestrator hizo review).

### Archivos nuevos (5 backend + 7 frontend)
Backend: `extract_from_doc.py`, `card_emitter.py`, 4 archivos de tests.
Frontend: `use-async-tool-job.ts`, `use-section-status.ts`, `use-tab-notification-permission.ts`, `lib/job-invalidation-map.ts`, `ExtractionSummaryCard.tsx`, 3 archivos de tests.

### Archivos extendidos
Backend: `extraction_tools.py`, `domain/card_payloads.py`, `domain/message_blocks.py`, `brand/workers/tasks.py`, `offer/workers/tasks.py`, `brand/api/dto/extraction.py`, `offer/api/dto/extraction.py`.
Frontend: `copilot-store.ts`, `use-copilot-chat.ts`, `ToolCallChip.tsx`, `types/message-blocks.ts`, `components/blocks/CardBlock.tsx`, `lib/api/ai-actions.ts`, `BrandStudioNavRail.tsx`, `OfferStudioNavRail.tsx`, `tool-labels.ts`.

### Audit findings corregidos durante la misma sesión
- H-1: English labels en summary card → backend emite slug + module, frontend resuelve desde catálogo (SSoT).
- M-1: card_emitter usaba stdlib logger con kwargs → swap a `structlog.get_logger`.
- M-2: resolver sin branch `offer` → agregado `getOfferSectionLabel` (ya existía en el catálogo).
- 3 tests frágiles corregidos (asertion literals, StructuredTool callability, ConversationRepository patching).

### Tests finales
- Backend contratos + worker + arch (focused): 49 passed.
- Frontend copilot + NavRails + arch (full): 248 passed.
- TSC + ESLint + Ruff en rutas tocadas: clean.

### Pendiente commit
- [ ] User decide estrategia de commit (sugerido: `feat(copilot): ...` x2 — backend + frontend+docs).
