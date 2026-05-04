# Pre-investigación obligatoria — Fase 09 (multi-channel projection)

> Evidencia recolectada vía `grep` + `read` antes del primer Write/Edit
> de código. ADR-017.

## Sección 1 — Estado infra channel

**Q1.1** — ¿Whatsapp/Telegram/Instagram channel adapters existen?

**Sí.** Inventario:

| Adapter | Path | Estado |
|---|---|---|
| Telegram | `connections/infrastructure/channels/telegram.py` + `telegram_service.py` | Producción (webhook + global + per-tenant) |
| WhatsApp | `connections/infrastructure/channels/whatsapp/{base,interface,factory}.py` | Producción (webhook + QR) |
| Instagram (Meta) | `connections/infrastructure/channels/meta.py` | Producción (webhooks Meta) |
| Base | `shared/infrastructure/channels/base.py::BaseChannel` | Abstract interface |

Channel resolver para outbound: `sales_agent/application/services/channel_resolver.py`
mapea `_CHANNEL_MAP = {"telegram", "whatsapp", "instagram"}` → adapter
factory + lead user_id field. Soporta `preferred_channel` + fallback al
primer canal disponible.

**Q1.2** — ¿Quién consume canales hoy?

**Sales-agent SOLO.** Webhook → `MessageHandlerPort` (puerto en
`shared/links/ports/message_handler.py`) → `ChatOrchestrator`
(`sales_agent/application/orchestrator/chat.py`, 1082 LOC) → sales subgraph
(`sales_agent/application/agents/sales/graph.py`).

Sales subgraph: `supervisor → {qualifier, product_expert, closer,
tool_executor, escalation, respond} → signal_accumulator`. Está orientado
a **vender al lead** (qualifying, objections, scheduling, payment,
follow-up), NO a configurar la cuenta del tenant.

**Q1.3** — ¿El copilot (que sí asiste al tenant owner a configurar
brand/offer/buyer_persona) está conectado a canales?

**No.** El copilot vive en `copilot/application/orchestrator/graph.py`
(712 LOC, ReAct StateGraph). Entry point: `/api/v1/copilot/chat` (web
UI). Sin webhook ni adapter binding. El `MessageHandlerPort` solo despacha
al sales-agent.

**Implicación scope Fase 09**: el wiring "copilot → whatsapp/telegram"
para tenant onboarding NO existe. Construir esa infra es **out of scope**
de esta fase per ADR-011 / PLAN.md §Fase 09 (asume infra existente).
Esta fase entrega el algoritmo + adapter port + tests channel-agnostic
para que el wiring real (cuando exista) sea drop-in.

## Sección 2 — Question selection actual

**Q2.1** — ¿Dónde decide hoy el copilot qué preguntar?

`copilot/application/guided/block_generator.py`. Decisión BLOCK-level
(section granularity), no field-level. `build_blocks(domain)` agrupa
fields por `FieldSpec.section` y emite ordered tuple de `GuidedBlock`
con `field_paths` + `coverage_threshold`. Tools `start_guided_setup`,
`advance_guided_setup`, `end_guided_setup` orquestan transition.

Dentro de un bloque, **el LLM decide** qué preguntar y en qué orden.
No hay algoritmo determinístico que ranking field-by-field.

**Q2.2** — ¿FieldContract copilot meta está populada?

Auditoría `human_question_es=` populated en overrides:

| Module | overrides w/ human_question_es | total contracts |
|---|---|---|
| offer | 24 | 153 |
| brand | 0 | 113 |
| buyer_persona | 0 | 18 |

`gate=` populated:

| Module | gate populated |
|---|---|
| offer | 1 (`value_level` gate=`archetype`) |
| brand | 0 |
| buyer_persona | 0 |

**Implicación**: el algoritmo `next_question` debe degradarse
gracefully cuando `human_question_es is None` (fallback: `_humanize(path)`
o label). Enrichment progressive es scope sub-fase 09.F (high-priority
required fields).

## Sección 3 — Trade-off algoritmo vs LLM

**Decisión**: híbrido determinístico-asistido.

- **Algoritmo (puro, testeable)**: `next_question(module, current_state,
  active_section: str | None) → FieldContract | None`. Selecciona
  candidate fields por `(status==ACTIVE, can_propose, missing,
  gate_satisfied)`, ordena por `(section_order, -priority, path)`.
  Devuelve el contract; el caller decide cómo presentarlo.
- **LLM (formulación)**: el adapter web/chat toma el contract devuelto
  y formula la pregunta natural. En web: la card del form-runtime
  highlights el field. En chat: emite `human_question_es` directo
  (o LLM lo reformula en tono conversacional, leveraging contract
  metadata como `expects` + `notes`).

Razón: separar policy (qué preguntar siguiente) de presentation (cómo
preguntarlo). Algorithm puro = unit-testeable + reproducible.
LLM = naturalidad cross-channel.

**Q3.1** — ¿Cómo manejar `gate`?

`gate: str | None` apunta a un path precondición. `_gate_satisfied(gate,
state)` returns True si:
- `gate is None`, o
- valor en `state[gate]` es non-empty (string non-blank, list non-empty,
  dict non-empty, scalar non-None).

Si el field tiene `gate` pero el valor del gate todavía es vacío, el
algoritmo lo **omite del ranking**. La idea: `value_level` requiere
`archetype` set; mientras el archetype no esté seteado, `value_level`
no entra en candidates.

**Q3.2** — ¿`redo_if_changes` aplica acá?

No directamente en `next_question`. Es señal para el **persister** /
**state manager**: cuando un field marcado `redo_if_changes=("X",)`
cambia, el state manager invalida los fields cuyo redo apunta acá.
Fase 09 documenta el contract pero NO implementa invalidation
(scope futuro).

## Sección 4 — Compat web ↔ chat

**Q4.1** — ¿La web sigue usando form-runtime?

**Sí.** Form-runtime con autosave on-change (feedback memo
`feedback_form_runtime_autosave.md`) es no negociable. Schemas FE
(`frontend/src/features/{module}/schemas/*.schema.ts`) intactos
(INVARIANT 9).

**Q4.2** — ¿Cómo aprovecha la web `next_question`?

Modo "guiado" del copilot web (block_generator) puede consumir
`next_question` para emitir hints field-level dentro del bloque
("ahora preguntale por X"). El form-runtime sigue presentando todos
los fields del bloque; el copilot resalta cuál tiene mayor priority.

Decisión: integración mínima en web — `next_question` usado por
`advance_guided_setup` para enriquecer el bloque actual con un suggested
field. Fase 09.C lo implementa. Fallback: si algoritmo retorna None,
flow legacy continúa.

**Q4.3** — ¿El form-runtime cambia?

No. INVARIANT 9. Solo el copilot guided uses la metadata. Schemas FE
no se tocan.

## Sección 5 — Tests E2E disponibles

**Q5.1** — ¿Hay infraestructura E2E para chat?

Sales-agent tiene `tests/modules/sales_agent/` con tests unit (state,
message, semantic_router, conversation_context, tools, follow_up). No
hay E2E end-to-end webhook → chat → response. Existen tests del
ChatOrchestrator pero requieren Redis + buffer (out of scope este fase).

Para Fase 09 channel-agnostic E2E:
- Stub `BaseChannel` adapter (in-memory captura outbound).
- `next_question` → adapter render → assert formato esperado.
- Run en `tests/modules/copilot/test_conversational_questioning_e2e.py`.

**Q5.2** — ¿Tests acceptance copilot existentes?

52 tests en `tests/acceptance/copilot/` (Fase 08 baseline). Cubre
`propose_field_updates`, `extract_structured`, `field_paths_hint`. Fase
09 agrega tests acceptance del nuevo `next_question` que NO regresan
los 52 existentes.

## Sección 6 — Diferidos posibles

Per LEARNINGS Fase 05/07 + STATE.md:

- **Full data-driven `agent_identity.j2` loop**: requiere renderer
  Python custom + override metadata `prompt_label_es`. Tangencial a
  Fase 09. Decisión: **NO tomar** este sprint. Si emerge demanda real
  durante Fase 09 (ej. agent prompt necesita render desde contract),
  abrir sub-fase dedicada.
- **Completion ↔ contract semantic alignment**: requiere
  `completion_section: str | None` en override. Tangencial.
  **NO tomar**.
- **Landing aggregate migration**: drop raw-SQL en
  `landing_service.generate_landing_for_offer`. Tangencial. **NO tomar**.
- **Walker extension list[dict] item sub-keys**: pain_points/desires
  sub-keys. Tangencial. **NO tomar** salvo que Fase 09 directamente
  necesite expose esos paths como ask-able (poco probable).

Razón: Fase 09 ya es high-risk + multi-step. Mantener scope tight para
revertibilidad atómica.

## Sección 7 — Files que tocaré

Por sub-fase (definitivo en SPEC.md):

**09.B (algoritmo)**:
- `backend/src/modules/copilot/application/orchestrator/conversational_questioning.py` (NUEVO)
- `backend/tests/modules/copilot/test_conversational_questioning.py` (NUEVO)
- `backend/tests/architecture/test_field_contract_platform.py` (extender si aplica)

**09.C (web integration)**:
- `backend/src/modules/copilot/application/tools/guided/advance.py` (extender)
- `backend/tests/modules/copilot/test_guided_advance.py` (extender o crear)

**09.D (channel adapter port)**:
- `backend/src/shared/links/ports/conversational_channel.py` (NUEVO — abstract port)
- `backend/src/modules/copilot/infrastructure/channels/web_channel.py` (NUEVO — web in-memory adapter)
- `backend/tests/modules/copilot/test_conversational_channel_port.py` (NUEVO)

**09.E (E2E channel-agnostic)**:
- `backend/tests/modules/copilot/test_conversational_e2e.py` (NUEVO)

**09.F (human_question_es enrichment)**:
- `backend/src/modules/offer/domain/field_contract.py` (overrides)
- `backend/src/modules/brand/domain/field_contract.py` (overrides)
- `backend/src/modules/brand/domain/buyer_persona_field_contract.py` (overrides)
- Solo high-priority required fields (top ~30 paths cross-module).

**09.G (cierre)**:
- `docs/refactors/field-contract-platform/STATE.md`
- `docs/refactors/field-contract-platform/LEARNINGS.md`
- `docs/refactors/field-contract-platform/phases/09-multi-channel-projection/STATUS.md`
- `docs/refactors/field-contract-platform/HANDOFF.md` (opcional — refactor podría cerrar)

## Output checklist

- [x] Estado infra channel confirmado: adapters whatsapp/telegram/IG existen
      en connections/. Sales-agent los consume vía MessageHandlerPort.
      Copilot NO conectado a canales (out of scope wiring real).
- [x] Decisión algoritmo vs LLM: híbrido determinístico-asistido. Algoritmo
      puro selecciona candidate; adapter web/chat presenta usando
      `human_question_es` (LLM puede reformular para naturalidad).
- [x] Compat web confirmada: form-runtime + schemas FE intactos
      (INVARIANT 9). Solo copilot guided consume `next_question`.
- [x] Tests E2E plan: stub channel adapter in-memory + E2E tests en
      `tests/modules/copilot/test_conversational_e2e.py`. Sin webhook
      real (out of scope).
- [x] FieldContract meta auditada: 24/153 offer, 0/113 brand, 0/18 buyer.
      Sub-fase 09.F enriquece top required fields cross-module.
- [x] Diferidos posibles documentados como "NO tomar" para mantener scope
      tight (revertible atómico).
