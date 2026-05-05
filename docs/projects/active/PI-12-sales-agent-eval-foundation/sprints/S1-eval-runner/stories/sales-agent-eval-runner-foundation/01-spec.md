---
story_id: sales-agent-eval-runner-foundation
type: service-story
module: sales-agent
capability: sales-conversational-engine
po_version: 2
last_modified: 2026-05-05T03:01:12Z
ratified_by_chris: true
links:
  story_yaml: "../../../../../../product/stories/sales-agent/sales-agent-eval-runner-foundation.yaml"
  story_md: "00-story.md"
  pi: "../../../PI.md"
  sprint: "../../sprint.md"
---

## Resumen ejecutivo

Construir el harness mínimo de evaluación agentica para `modules/sales_agent/` en
`backend/tests/agentic_evals/sales_agent/`. La salida es un suite pytest que carga **1 golden hardcoded multi-capa**, ejecuta el agente real (LangGraph + LiteLLM proxy) contra el tenant fijo **Visionarias** con DB real, y verifica simultáneamente **5 capas de aserción 2026-canónicas**: trayectoria (specialist routing), tool calls (required + forbidden), output (no-vacío + Spanish + menciona oferta del tenant), cost (`copilot_llm_call.cost_usd > 0`, captura el bug que Story A arregla) y latencia (p95 < 30s). Es **service-story foundation**: no toca runtime sales_agent (solo agrega `tests/`), pero descubre regresiones agenticas reales antes del merge — no shallow "hola/respuesta". Bloquea Story 2 (pass^k), Story 3 (budget cap), Story 5 (3-tenant goldens), Story 6 (personas), Story 7 (voice grader), Story 8 (CI gate), Story 9 (adversarial). Está protegido por flag pytest `--run-evals` para que CI default no consuma budget LLM. Costo esperado por corrida: **< $0.01** (1 turno DeepSeek V4-Flash).

## Acceptance Criteria (Gherkin AI-resistant)

> 4 scenarios obligatorios. Cada `then:` es medible. Graders explícitos.

### Scenario 1 — `smoke-multi-layer-pass` (`type: happy`)

**Given:**
- Tenant Visionarias seeded en DB con al menos 1 `offer` activo (no soft-deleted) — el harness consulta `offer` table filtrado `tenant_id=Visionarias_id` y elige el top-1 ordenado por `created_at desc`
- LiteLLM proxy reachable (env `LITELLM_PROXY_ENABLED=true` + `LITELLM_BASE_URL` válido)
- Tablas `sales_agent_trace_event` + `sales_agent_llm_call` reachable (post Story `sales-trace-persist-turn`)
- PersonalityProfile Visionarias compiled (`system_instruction` no vacío)
- Developer corre con flag `--run-evals` activo

**When:**
- `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py::test_smoke_multi_layer -v --run-evals`

**Then:**
- El golden de smoke (1 turno, input `"Hola, vi su publicidad sobre <oferta_real>. ¿Cuánto cuesta y cómo es la metodología?"` con oferta real Visionarias inyectada por fixture) se ejecuta contra `agent_app.ainvoke`
- **Capa 1 — Trajectory**: `state.specialist_history` (o equivalent post-redesign) incluye `qualifier` como primer specialist invocado; NO incluye `closer` en este turno (un cold lead no debe ir directo a closer sin calificar)
- **Capa 2 — Tool calls (required)**: `tool_calls` capturados incluyen al menos `intent_classifier` (entry point del router post-redesign 2026-04 — confirmar exact name al architect phase, ver Open Q4)
- **Capa 2 — Tool calls (forbidden)**: `tool_calls` NO incluyen `send_email`, `schedule_meeting`, ni `create_payment_link` (tool use prematuro en cold lead = regresión)
- **Capa 3 — Output**: response string `len > 50`, contiene marcadores Spanish (regex word-boundary count de [`que`, `de`, `la`, `el`, `los`, `las`, `con`, `por`, `para`] >= 3 ocurrencias en la respuesta), y menciona el nombre del tenant (regex case-insensitive `Visionarias` o `visionarias`) O el `offer.name` del golden (substring case-insensitive)
- **Capa 4 — Cost**: query a `sales_agent_llm_call` filtrado por `tenant_id=Visionarias` + `created_at >= test_start_ts` retorna `>= 1` row con `cost_usd > 0` AND `model` matchea `^deepseek-v4-flash` (provider Story A canonicaliza)
- **Capa 5 — Latencia**: tiempo `time.perf_counter()` desde antes `ainvoke` hasta after assertions < 30000 ms
- **Artifacts**: directorio `backend/tests/agentic_evals/sales_agent/_artifacts/{run_id}/` (run_id = UUID4 generado al inicio del test) creado con archivos `trace.json` (state machine snapshot serializable + tool_calls + specialist_history), `response.txt` (output del agente raw), `assertions.json` (resultado por capa: pass/fail + valor observado vs esperado)
- Test reporta `PASSED` solo si las 5 capas pasan; falla en cualquier capa marca el test como `FAILED` con mensaje del layer específico

**Graders:**
- `contract_test` — path: `backend/tests/agentic_evals/sales_agent/test_eval_runner_smoke.py::test_smoke_multi_layer`
- `state_check` — target: db, query: `SELECT COUNT(*), MAX(cost_usd), STRING_AGG(model, ',') FROM sales_agent_llm_call WHERE tenant_id = :visionarias_id AND created_at >= :test_start_ts`, expect: `count >= 1 AND max_cost > 0 AND model LIKE '%deepseek-v4-flash%'`
- `state_check` — target: filesystem, path: `backend/tests/agentic_evals/sales_agent/_artifacts/{run_id}/assertions.json`, expect: archivo existe y contiene 5 keys (`trajectory`, `tools_required`, `tools_forbidden`, `output`, `cost`, `latency_ms`) todas con `passed: true`

---

### Scenario 2 — `flag-omitted-skips-eval-suite` (`type: negative`)

**Given:**
- Tenant Visionarias en DB (estado idéntico a Scenario 1)
- Developer corre **sin** flag `--run-evals` (ej. CI default por push no eval)

**When:**
- `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/ -v` (sin `--run-evals`)

**Then:**
- pytest reporta cada test del suite como `SKIPPED` (no `PASSED` ni `FAILED`)
- La razón skip que reporta pytest es `eval markers require --run-evals flag` (string exacto del decorador `@pytest.mark.eval` cuando el flag no está)
- Ningún row nuevo en `sales_agent_llm_call` para `tenant_id=Visionarias` durante la ventana del test (verificable con `created_at >= test_start_ts`)
- Ningún row nuevo en `sales_agent_trace_event` para `tenant_id=Visionarias` durante la ventana
- Exit code de pytest = 0 (skipped no falla el push CI)

**Graders:**
- `contract_test` — path: `backend/tests/agentic_evals/sales_agent/test_eval_runner_smoke.py::test_skip_without_flag`
- `state_check` — target: db, query: `SELECT COUNT(*) FROM sales_agent_llm_call WHERE tenant_id = :visionarias_id AND created_at >= :test_start_ts`, expect: `0`
- `state_check` — target: db, query: `SELECT COUNT(*) FROM sales_agent_trace_event WHERE tenant_id = :visionarias_id AND created_at >= :test_start_ts`, expect: `0`

---

### Scenario 3 — `agent-degraded-output-detected` (`type: edge`)

**Given:**
- Tenant Visionarias en DB (estado idéntico a Scenario 1)
- LiteLLM proxy reachable PERO el harness inyecta una respuesta degradada (mock `LiteLLMService.generate_response` para retornar payload con `tool_calls=[{"name": "send_email", ...}]` o output `"Hi"` (no Spanish, length 2)) — esto simula regresión real del agente sin gastar budget en una respuesta degradada genuina
- Flag `--run-evals` activo

**When:**
- `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py::test_degraded_output_caught -v --run-evals`

**Then:**
- Test `FAILS` (status `FAILED`, no `ERROR` ni `PASSED`)
- El mensaje de error nombra **el layer específico que falló** — ej. `"Layer 2 (tool_calls forbidden) FAILED: send_email present in tool_calls but is forbidden"` o `"Layer 3 (output) FAILED: Spanish marker count = 0 (expected >= 3); response='Hi'"`
- El error NO es un genérico `AssertionError` sin contexto (cada capa custom-asserts con mensaje accionable)
- Artifacts del run degradado se persisten igual: `_artifacts/{run_id}/{trace.json, response.txt, assertions.json}` con `assertions.json` mostrando `passed: false` en la capa fallida + valor observado
- El call al LLM (mocked) NO genera row real en `sales_agent_llm_call` (porque mockeamos `generate_response` antes del recorder); el harness documenta esto en el `assertions.json` con `cost_layer.skipped_reason = "llm_mocked"` para que el dev sepa que la capa cost no aplicó en este test específico
- Cleanup: la mock se desinstala al final del test; el siguiente test no hereda el monkeypatch

**Graders:**
- `contract_test` — path: `backend/tests/agentic_evals/sales_agent/test_eval_runner_smoke.py::test_degraded_output_caught`
- `state_check` — target: filesystem, path: `backend/tests/agentic_evals/sales_agent/_artifacts/{run_id}/assertions.json`, expect: archivo existe + al menos una key con `passed: false` + `failed_layer_name` populated

---

### Scenario 4 — `cross-tenant-leak-on-mock-tenant` (`type: adversarial`)

> AI-resistant: regresión de tenant isolation en fixtures. Si un fixture lee `offer.tenant_id != Visionarias` (bug copy-paste, falta filter, etc.), el harness debe fallar explícito — no silenciar.

**Given:**
- Dos tenants seeded en DB: `Visionarias` (T1, target del smoke) y `T2_synthetic` (segundo tenant fixture-only con su propia oferta `offer_T2`)
- Tenant T2 tiene una oferta `offer_T2` activa (creada por fixture de setup)
- Flag `--run-evals` activo
- Test parametrizado: invoca el smoke harness con `tenant_id=Visionarias`

**When:**
- `cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py::test_no_cross_tenant_leak -v --run-evals`

**Then:**
- El harness fixture (que selecciona la oferta golden) consulta `offer` table filtrando explícitamente `WHERE tenant_id = :visionarias_id` (per `.claude/rules/tenant-isolation.md`)
- El golden generado contiene `offer_T1.name` (Visionarias), nunca `offer_T2.name`
- La invocación del agente (`agent_app.ainvoke`) recibe `tenant_id=Visionarias_id`; cualquier query interna del agente a DB también filtra por ese tenant_id
- En `sales_agent_trace_event` post-test: `SELECT DISTINCT tenant_id FROM sales_agent_trace_event WHERE created_at >= :test_start_ts` retorna **únicamente** `Visionarias_id` (no T2)
- En `sales_agent_llm_call` post-test: idem, sólo `Visionarias_id`
- En el `trace.json` artifact: NO aparece `offer_T2.id`, `offer_T2.name`, ni T2 tenant_id en ningún campo del state serializado
- Si la fixture rompe (bug introducido) y trae oferta de T2 al golden, el test FAILS con mensaje explícito: `"Cross-tenant leak detected: golden offer.tenant_id=T2 does not match harness tenant_id=Visionarias"`
- Audit log entry escrita (structlog `eval_cross_tenant_check` con tenant_id_expected + tenant_id_observed)

**Graders:**
- `contract_test` — path: `backend/tests/agentic_evals/sales_agent/test_eval_runner_smoke.py::test_no_cross_tenant_leak` (parametrizado con el segundo tenant T2_synthetic creado por fixture)
- `state_check` — target: db, query: `SELECT COUNT(DISTINCT tenant_id) FROM sales_agent_trace_event WHERE created_at >= :test_start_ts AND tenant_id IN (:visionarias_id, :t2_synthetic_id)`, expect: `1` (sólo Visionarias)
- `state_check` — target: db, query: `SELECT COUNT(DISTINCT tenant_id) FROM sales_agent_llm_call WHERE created_at >= :test_start_ts AND tenant_id IN (:visionarias_id, :t2_synthetic_id)`, expect: `1`
- `state_check` — target: filesystem, path: `_artifacts/{run_id}/trace.json`, expect: archivo no contiene strings `T2_synthetic` ni `offer_T2`

---

## Service contract

| Campo | Valor |
|---|---|
| type | `scheduled_job` (eval suite es on-demand, no endpoint público) |
| trigger | `pytest --run-evals` (manual local + nightly cron post Story 8) |
| auth | `internal` (no Clerk JWT — corre dentro pytest, accede DB local con creds de dev) |
| idempotency | `natural-key` — `run_id = uuid4()` por invocación (cada corrida es un experimento independiente) |
| rate_limit_per_tenant | `null` (single-tenant Visionarias por run, single-developer; no hay multitenancy aquí) |
| request_schema | n/a (CLI args pytest) |
| response_schema | n/a (filesystem artifacts + pytest exit code) |

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Latencia | p95 < 30000 ms por scenario smoke (1 LLM call DeepSeek + assertions overhead) | `time.perf_counter()` wrapping `agent_app.ainvoke` + assertions; falla scenario si excede |
| Cost | < $0.01 por corrida del smoke (1 turno DeepSeek V4-Flash, ~500 tokens prompt + ~300 tokens output) | `sales_agent_llm_call.cost_usd` capturado en Capa 4; documentado en spec; alert si >$0.05 (probablemente hay loop o tier wrong) |
| Mobile | n/a (backend-only, no UI) | n/a |
| Accesibilidad | n/a | n/a |
| i18n | Output del agente respeta voz tenant Visionarias (puede tener voseo si el tenant lo configuró — `.claude/rules/spanish-text.md` NO aplica al output sales_agent per `sales-agent-brand-voice.md` § "Excepción"). El harness sólo valida densidad Spanish (Capa 3), no estilo. | Capa 3 regex marker count |
| PII | Artifacts (`trace.json`, `response.txt`, `assertions.json`) NO contienen PII de prospects reales — el golden usa input genérico ("Hola, vi su publicidad...") y no consulta leads reales. Si en el futuro se incorporan goldens con PII (Story 5), aplicar `sanitize_payload` antes de escribir artifacts. | Code review en architect phase + sanitize_payload helper en harness |
| Tenant isolation | Toda query DB filtrada por `tenant_id=Visionarias`. Scenario 4 verifica regresión. | `state_check` graders Scenario 4 |
| Reproducibilidad | Mismo input + mismo PersonalityProfile + mismo offer + mismo modelo (DeepSeek V4-Flash temp default) → mismas trayectorias dentro del rango trial_policy noise. Foundation acepta `trials_per_scenario=1`; Story 2 sube a `pass^k=3`. | Story 2 |
| Failure mode | Falla del smoke = pytest reporta layer específico fallido + path al `_artifacts/{run_id}/` para diagnóstico humano. NO output críptico. | Scenario 3 grader |
| Best-effort observability | Si el recorder de `sales_agent_trace_event`/`_llm_call` falla (DB transient down), el harness captura el warning structlog pero NO falsea Capa 4 — falla explícito con mensaje `"Cost layer un-verifiable: trace recorder warning at <ts>"` para distinguir bug del recorder vs bug del agente. | Capa 4 logic |

## Constraints técnicos heredados

- **TDD obligatorio** (`.claude/rules/tdd-mandatory.md`): el harness fixture (`conftest.py` + `runner/`) tiene su **propio test suite** `test_eval_runner_fixtures.py` que valida (a) la fixture selecciona oferta correcta filtrada por tenant, (b) el callback handler captura tool_calls, (c) los artifacts se escriben al filesystem path esperado. Estos meta-tests RED → GREEN antes de los goldens.
- **Tenant isolation** (`.claude/rules/tenant-isolation.md`): toda query DB en fixtures filtra por `tenant_id=Visionarias`. Scenario 4 enforce.
- **Anti-duplication** (`.claude/rules/anti-duplication.md`): el callback handler del harness **NO mirror** patterns de `modules/sales_agent/observability/` o `modules/copilot/observability/`. Hereda `shared/agent_observability/recording/base_callback_handler.py::BaseAgentCallbackHandler` (Step 0 grep obligatorio en architect phase). Si hay capability nueva (ej. capturar `state.specialist_history` en formato eval-friendly) y no está en shared → LIFT-TO-SHARED, no duplicar.
- **Brand voice SSoT** (`.claude/rules/sales-agent-brand-voice.md`): el smoke **NO override** `PersonalityProfile.system_instruction` del tenant Visionarias. Usa el compiler v2 prod path. El harness NO mockea voz — testear voz es Story 7 (voice fidelity grader), no esta foundation.
- **Observability best-effort** (`.claude/rules/copilot-observability.md`): writes a `sales_agent_trace_event`/`_llm_call` están envueltos en try/except (recorder shared). El harness verifica Capa 4 con query DB; si la query retorna 0 rows + structlog warning capturado → fallar Capa 4 con mensaje explícito (no silencio).
- **Cost real** (Decisión Chris 2026-05-04): mock LLM cost recorder NO es aceptable para Scenario 1. Cost real verifica que Story A (LiteLLM canonicalization) está mergeado y `cost_usd > 0` real. Scenario 3 sí mockea para inyectar respuesta degradada (es un test del harness, no del agente).
- **Frozen golden set + parametrize-ready** (industry pattern 2026): este story commit-ea **1 golden hardcoded** en `tests/agentic_evals/sales_agent/goldens/visionarias-smoke-golden.yaml`. La estructura del runner soporta `pytest.mark.parametrize` sobre N goldens vía YAML loader — lo que habilita Story 5 (3-tenant dataset) sin tocar el harness.
- **Trial policy** (industry pattern, Anthropic + LangChain agentevals): el runner acepta param `trials_per_scenario: int = 1` por golden. Story 2 lo sube a 3 (pass^k=3 floor). Foundation: `1` (fast feedback, ~$0.005 por run).
- **Reference framework — custom Nicolify, NOT agentevals dep**: el harness implementa custom multi-layer evaluator. `langchain/agentevals` evaluado como alternativa pero descartado para foundation (adds dep, pinea LangChain version, overlap parcial con `shared/agent_observability/`). Reabrir en Story 7 si voice grader requiere LLM-as-judge built-in patterns.
- **Marker pytest `--run-evals`**: registrado vía `pytest_addoption` en `tests/agentic_evals/conftest.py` (root level del eval suite). El marker `@pytest.mark.eval` aplica a todos los tests del suite; cuando flag ausente, fixture autouse skip-ea con razón explícita.
- **Skills a cargar al implementar**: `sales-agent-expert` (invariants voz/specialists/recorder), `tessl__pytest-api-testing` (fixture patterns), `tessl__langgraph` (state machine introspection), `claude-api` / `tessl__graceful-degradation` (LLM call resilience).
- **Ruff/ESLint**: aplica como cualquier código BE — line 120, 0 errors.

## Cross-module impact

- **Lee de**:
  - `sales_agent` (invoca `agent_app.ainvoke`, lee `personality_profiles`, `sales_agent_trace_event`, `sales_agent_llm_call`)
  - `brand` (lee `offer` table para seleccionar el offer del golden — read-only)
- **Es leído por**: ninguno directo. Las stories siguientes del PI-12 (S2/S3/S4) **extienden** este harness pero no lo importan como módulo (es `tests/`).
- **Eventos emitidos**: ninguno (el harness no emite events de dominio; sólo escribe artifacts en filesystem y depende de los traces que el agente real ya escribe vía recorder shared)
- **Eventos consumidos**: ninguno

## Decisiones ratificadas (/po 2026-05-04)

> Chris delegó las 13 open questions al /po con criterio "robustez/escalabilidad > costo hoy". Las decisiones quedaron lockeadas. Cualquier challenge técnico durante /architect debe escalarse explícitamente — los defaults aquí son binding.

| # | Decisión | Razón |
|---|---|---|
| B1 | Harness exposes configurable `trials_per_scenario`. Smoke default = 1. Story 2 (pass^k) extends to 3. | General foundation; not hardcoded. |
| B2 | Hardcoded `offer_id` in `goldens/visionarias-smoke-golden.yaml` + companion `regenerate_golden.py` script. If offer disappears → fail explicit ("regenerate golden"), NOT silent shift. | Reproducibility for regression detection > dynamic flexibility. |
| B3 | Subdirs confirmed: `runner/` (harness code), `goldens/` (yaml goldens), `fixtures/` (pytest), `_artifacts/` (gitignored runtime artifacts). | Pytest agentic standard. |
| B4 | Spec captures INTENT only: `required: [entry intent classifier tool]`, `forbidden: [payment_*, scheduling_*, closer_finalize_*]` (glob patterns). architect-agentic maps to actual tool name strings against post-redesign-2026-04 tool registry at /architect phase. | Tool string names volatile; intent stable. |
| B5 | `langdetect` library (MIT, ~1MB, mature). Add to backend dev deps. NOT keyword count. | Robust regression detection if voice profile bug regresses agent to English. |
| B6 | Smoke does NOT validate `cache_hit_rate`. Story 7 voice fidelity grader covers cache invariants (multi-turn). | Single-turn smoke cannot measure rate. |
| B7 | Goldens checked-in as YAML files in `tests/agentic_evals/sales_agent/goldens/`. NOT DB-stored. | Industry standard (agentevals, fasteval, deepeval); versionable + cross-env reproducible. |

## Próximo paso

Spec ratificada. Hand off `/architect` (skip /ux porque service-story).
/architect lee 01-spec.md + 00-story.md → spawnea /architect-be (+ /architect-agentic si Story B harness toca sales_agent state) → produce 03-arch-be.md + 04-tickets.yaml con sub-tickets ordenados (T1..T9 para Story A; harness scaffolding para Story B).

## Changelog

- v1 2026-05-04 — `/po` draft inicial. Spec multi-capa rico (5 layers) + 4 scenarios + cost real + tenant fijo Visionarias. 7 open questions para Chris.
- v2 2026-05-04 — Chris delegó decisiones; /po lockeó las 13+2 decisions, ratificó.
