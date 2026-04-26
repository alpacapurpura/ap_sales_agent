# TP5 — Workflows Runtime Unification (F6)

**F# que valida:** F6 (`Workflow` declarative + `WorkflowEngine` + dual-read fallback `procedure_state ↔ workflow_state`).
**Tiempo estimado:** 2 hs.
**Pre-req hard:** TP0 + TP4 + tenant test con data + dev DB con migración 071 aplicada.

---

## Reality check (post sanity-check 2026-04-26)

**F6 ship:** declarative skeleton + engine + persistence + arch tests + 2 pilots con handlers PLACEHOLDER (return `NodeOutput()` shape correcto, NO lógica viva).

**F6 NO ship:**

- `WorkflowEngine` invocado desde el chat orchestrator. Cero call sites en `copilot/application/orchestrator/chat.py` ni `copilot/api/`. F-pos cutover lo hará.
- Tools que disparen workflows desde el agent loop (no hay tool `start_workflow` ni equivalente).
- Lógica live de los pilots — siguen corriendo en paralelo `guided/block_generator.py` (brand) + `extraction_card_flow.py` (offer).

**Implicancia:**

> Los workflows F6 son **zombies** desde el punto de vista del runtime API. No se pueden testear via `POST /copilot/chat` end-to-end UI/API. Phase doc original asumía F-pos terminado.

TP5 reframado: validar la **superficie real** F6 entrega — engine end-to-end via direct invocation + persistence layer live + arch fitness + coexistence regression del legacy path. Scenarios UI/end-to-end agent quedan deferred a TP post-F-pos cutover.

---

## Misión (reframe)

Confirmar que:

1. `WorkflowEngine.run()` ejecuta los 2 pilots end-to-end via direct invocation (handlers placeholder) — engine + handler resolver + state transitions + termination correctos.
2. `workflow_state` JSONB roundtrip persiste contra Postgres live (dev container) — no solo el conftest in-memory.
3. Dual-read fallback `procedure_state` retorna payload legacy cuando `workflow_state IS NULL` — verificado contra DB live.
4. Migración `071_copilot_workflow_state` aplicada en dev + backfill respetó `procedure_state` existente + idempotente.
5. Chat turn legacy en `/brand-studio` o `/sales` sigue corriendo sin tocar `workflow_state` (regresión coexistencia).
6. Handler raise → `WorkflowExecutionError` propagado + structured log + state queda en `current_node` (no avanza).
7. **Provider routing per-role correcto bajo F6 (heredado TP4 gate Sprint 0)** — chat turn coexistencia mantiene AGENT=Kimi K2.6 + NANO+FAST=OpenAI (validado por ausencia 400 errors + container env diff).

---

## Research mandate (ejecutado 2026-04-26 inicio)

Queries:

- `"langgraph multi-step workflow state persistence resume 2026 checkpointer pattern"` → LangGraph PostgresSaver async + thread state per super-step. F6 reinventa equivalente con JSONB column + Pydantic state. **Decisión sigue defensible** — no hay razón para subir a LangGraph subgraph (overhead 2-4× + LLM-driven dispatch innecesario para domain enumerable).
- `"agent workflow declarative vs imperative tradeoffs python 2026"` → "Real systems mix". F6 elige declarativo (Workflow data) + handlers imperativos (async fns). Match con LangGraph "low floor + high ceiling". **Decisión defensible**.
- `"workflow engine python lazy handler resolution importlib pattern 2026"` → PEP 810 lazy imports llega Python 3.15a7 (Oct 2026). F6 usa `importlib.import_module` runtime per step. F4 documented bug: "provider scan opens DB connections in module-import time" → lazy resolution previene. **Decisión defensible**, futuro PEP 810 simplifica cuando 3.15 lande.

Tessl tiles: `tessl__langgraph` ya en repo, no nuevo necesario.

---

## Scenarios (reframed)

### S5.1 — `setup_brand_minimal` engine end-to-end (direct invocation)

`WorkflowEngine.run(SETUP_BRAND_MINIMAL, initial_data={"tenant_id": ..., "pending_sections": ["narrative", "voice_tone"]}, context={})` desde Python script en container. Handlers placeholder ejecutan synthetically.

Expected: `final.is_complete=True`, `final.completed_nodes=["probe_brand", "ask_next_section", "finalize_summary"]`, `final.data["next_question"]` populated, `final.data["summary_after"]` populated.

**Pass:** terminal alcanzado + nodes en orden + state hidratable via `WorkflowExecutionState.to_jsonb_dict()`.

### S5.2 — `design_offer_from_url` engine end-to-end

`WorkflowEngine.run(DESIGN_OFFER_FROM_URL, initial_data={"source_url": "https://example.com/landing"}, context={})`. Branching node `ask_clarifications` con `pending_questions=[]` salta a `propose_offer`.

**Pass:** terminal alcanzado + completed_nodes incluye `extract_url`, `ask_clarifications`, `propose_offer` (3 nodes en orden).

### S5.3 — Persistence roundtrip live Postgres

Crear conv en `visionarias_postgres`. `repo.update_workflow_state(...)` con state mid-flow. Re-leer via `repo.get_workflow_state(...)`. Comparar payload.

**Pass:** payload idéntico (workflow_id + current_node + completed_nodes + data).

### S5.4 — Dual-read fallback live

Conv legacy con solo `procedure_state` populated (no `workflow_state`). `repo.get_workflow_state(..., fallback_to_procedure=True)` retorna procedure_state payload.

**Pass:** retorna legacy payload (no None).

### S5.5 — Migración 071 aplicada + idempotente

SQL probe: confirmar columna `workflow_state JSONB` existe + Postgres `\d copilot_conversations`. Re-correr migration → 0 errors. Backfill: rows con `procedure_state NOT NULL` + `workflow_state IS NULL` posterior al primer run = 0 (todas las rows fueron backfilled o son posteriores).

**Pass:** columna existe + tipo JSONB + re-run no error + backfill consistente.

### S5.6 — Coexistencia regression: chat turn legacy sigue OK

Real chat turn via API contra Visionarias `/brand-studio`. Confirmar:
- Trace events normales (turn_start/turn_end/llm_call/tool_call) emiten.
- `procedure_state` puede o no escribirse (depende del flow), `workflow_state` queda `NULL`.
- Provider routing AGENT=Kimi (gate TP4 heredado).
- Sin regresión vs baseline TP4 (turn completes, response visible).

**Pass:** turn responde + provider routing OK + workflow_state intacto NULL.

### S5.7 — Handler raise propaga `WorkflowExecutionError`

Crear workflow custom con handler que `raise RuntimeError("boom")`. `engine.step()` debe envolver en `WorkflowExecutionError` + emitir `structlog.exception` con `workflow_id` + `node_id`. State NO avanza (queda en `current_node`).

**Pass:** raise correcto + state preservado.

### S5.8 — Arch fitness suite F6 verde

Correr suite arch + unit F6:
```bash
cd backend && .venv/bin/pytest \
  tests/architecture/test_workflow_compliance.py \
  tests/modules/copilot/test_workflow_dataclass.py \
  tests/modules/copilot/test_workflow_engine.py \
  tests/modules/copilot/test_workflow_registry.py \
  tests/modules/copilot/test_workflow_state_persistence.py \
  -x -q --tb=short
```

**Pass:** 100% verde post-fixes B1+B3+B4 TP4.

---

## Eje UX (post reframe)

**N/A salvo S5.6.** F6 sin UI. Pilots zombies. UX consistency S5.6-original (Chrome DevTools live) movido a TP futuro post-F-pos cutover. En TP5 medimos UX solo en S5.6 (chat turn legacy regression — sin parpadeo cards, console clean, latencia normal vs TP4 baseline).

---

## Tools / queries

- Engine direct: `cd backend && .venv/bin/python -c "import asyncio; from src.modules.copilot.application.workflows.engine import WorkflowEngine; from src.modules.brand.copilot_provider.workflows import SETUP_BRAND_MINIMAL; print(asyncio.run(WorkflowEngine().run(SETUP_BRAND_MINIMAL, initial_data={'pending_sections': ['narrative']}, context={})))"`
- SQL probes:
  - `\d copilot_conversations` (verifica columna workflow_state)
  - `SELECT workflow_state, procedure_state FROM copilot_conversations WHERE id=:cid;`
  - `SELECT COUNT(*) FROM copilot_conversations WHERE workflow_state IS NULL AND procedure_state IS NOT NULL;` (post-backfill expected: 0)
- Chat turn: idem TP4 patrón curl `POST /copilot/chat`.

---

## Targets (post reframe)

| Métrica | Target | Hard fail |
|---|---|---|
| Engine end-to-end pilots run sin crash | 2/2 pilots OK | cualquier pilot crash |
| Persistence roundtrip live | byte-equal payload | divergence |
| Dual-read fallback returns legacy | OK | None |
| Migration 071 aplicada + idempotente | OK + 0 backfill orphans | column missing / orphans >0 |
| Coexistencia: chat turn legacy OK | turn completes + workflow_state NULL | regression vs TP4 |
| Handler raise → ExecutionError | wrapped + log + state preserved | unwrapped exception |
| Arch fitness F6 suite | 100% green | cualquier fail |
| Provider routing per-role | AGENT=Kimi via 400-vanish | 400 returns |

---

## Failure playbook (post reframe)

| Síntoma | Investigar | Root cause | Fix |
|---|---|---|---|
| Engine crash en pilot | handler resolution | `application/workflows/engine.py:_resolve_handler` | verificar handler_ref dotted path |
| Persistence roundtrip no match | SQLA JSONB serialization | `WorkflowExecutionState.to_jsonb_dict()` | check Pydantic mode="json" |
| Migration 071 no aplicada | dev DB stale | `alembic current` | `alembic upgrade head` |
| Coexistencia regression | chat.py invoca workflow_state path | greps en `chat.py` | revertir cambios |
| Handler raise unwrapped | engine `_resolve_handler` swallow | engine.py error handling | wrap `try/except` |
| Routing per-role 400 | Kimi clamp evade | grep `_get_chat_model` | confirm B4 clamp aplicado |

---

## Lo que necesito de Chris

- [x] Tenant test con data — Visionarias `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` (heredado TP4).
- [x] Dev DB con migración 071 aplicada — verificar pre-flight.
- [N/A en TP5 reframed] URL real para S5.2 — handler placeholder no fetcha URL, default value en initial_data alcanza.
