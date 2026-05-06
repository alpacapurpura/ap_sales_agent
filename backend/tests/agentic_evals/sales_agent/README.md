# Agentic Eval Harness — sales_agent

> Documentación operativa del eval runner end-to-end de `sales_agent`
> (PI-12 S1, story `sales-agent-eval-runner-foundation`). Esta es la
> referencia humana — para detalle arquitectónico ver
> `docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-eval-runner-foundation/03-arch-be.md`.

---

## 1. Qué es esta carpeta

Harness de evaluaciones **end-to-end** del agente `sales_agent` (módulo
`backend/src/modules/sales_agent/`). Cada smoke invoca `agent_app.ainvoke`
real contra un tenant real (Visionarias) con un golden YAML versionado y
verifica múltiples capas (trayectoria, herramientas, output, costo,
latencia) usando `TrajectorySpy` + asserts multilayer.

**Alcance:** este harness cubre únicamente `sales_agent`. Otros agentes
(p. ej. `copilot`) tendrían su propio harness hermano si fuera necesario
en el futuro, NO se mezclan en esta carpeta.

**Diferencia con `tests/quality/sales_agent_goldens/`** — ver sección 5
abajo. TL;DR: aquel directorio (S10 weekly judge stub, abril 2026) NO
invoca al agente real; este harness sí.

---

## 2. Cómo correr local

### Pre-condiciones runtime

Las fixtures hacen `pytest.skip` con razón explícita si falta cualquier
pre-condición (no auto-seedean — contrato fail-explicit, decision B6 del
spec). Antes de correr, asegura que:

| Pre-condición | Verificación | Fix |
|---|---|---|
| `VISIONARIAS_TENANT_ID` env var presente | `echo $VISIONARIAS_TENANT_ID` | `export VISIONARIAS_TENANT_ID=<UUID>` (ver `.env.dev`) |
| DB de dev seedeada (tenant Visionarias + 1 oferta activa + PersonalityProfile compilado) | `make seed-visionarias` (desde root) | Re-correr seed si tabla está vacía |
| LiteLLM proxy levantado en `visionarias_litellm:4000` | `docker ps \| grep litellm` | `make dev` (desde root) trae el stack completo |
| Container `visionarias_brain_dev` UP (fixture probe DB) | `docker ps \| grep brain` | `make dev` (desde root) |

Si falta cualquier item, los 4 scenarios del smoke quedan **SKIPPED** con
razón Spanish-neutro en el output de pytest (no FAIL — esa es la
distinción clave del contrato fail-explicit B6 vs auto-seed, que fue
rechazado en spec § Decisions).

### Comandos

```bash
# Atajo Make (target T-6):
cd backend && make eval-smoke

# Equivalente directo:
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py -v --run-evals

# Suite por defecto (sin --run-evals): los smokes SKIP, no consumen budget LLM
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/

# Solo meta-tests del runner (siempre corren, no necesitan brain UP):
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py -v
```

### Qué esperar

Run exitoso del smoke:

- 4 scenarios PASS (Scenario 1 happy path + Scenarios 2-4 negative).
- Artifacts en `_artifacts/<eval_run_id>/` (trace.json + response.txt
  + assertions.json — gitignored, regenerados cada run).
- Cada smoke ~3-8s wall clock, costo ~$0.001-0.005 USD por turno
  (DeepSeek V4-Flash vía LiteLLM proxy).
- Logs estructurados vía `structlog` mostrando `trace_event` /
  `llm_call` / asserts por capa.

Run con falla downstream (e.g. brain DOWN): los 4 scenarios quedan
SKIPPED con mensaje explícito (no FAIL). Esto preserva señales
honestas — un test rojo significa regresión, no entorno roto.

---

## 3. Cómo agregar un golden

### Schema YAML (SSoT en `runner/golden_loader.py::GoldenSpec`)

Los goldens viven en `goldens/` como YAML versionado (decision B7 del
spec — checkeados en git, no generados runtime). Ubicación:

```
backend/tests/agentic_evals/sales_agent/goldens/<golden_id>.yaml
```

### Campos obligatorios

| Campo | Tipo | Descripción |
|---|---|---|
| `id` | str | ID único del golden (e.g. `visionarias-smoke-001`) |
| `version` | int | Versión del golden (incrementa al regenerar) |
| `schema_version` | int | Versión del schema YAML (actualmente `1`) |
| `tenant_id` | str (UUID) | Tenant del que se ejecuta (binding fail-explicit B2) |
| `offer_id` | str (UUID) | Oferta hardcoded — falla explícito si soft-deleted (B2) |
| `input_message` | str (Spanish neutro) | Primer turno del lead simulado |
| `expected_specialists` | list[str] | Trayectoria esperada — Capa 1 (`assert_trajectory mode=includes`) |
| `required_tools` | list[str] | Tools que DEBEN dispararse (Capa 2) — vacío si single-turn cold-lead |
| `forbidden_tools` | list[str] | Tools que NO DEBEN dispararse (Capa 2) — unión de `STAGE_TOOL_SCOPE` por etapa prohibida |
| `must_mention` | list[str] | Substrings case-insensitive que deben aparecer en output (Capa 3) |
| `language` | str | Prefix ISO-639-1 esperado (e.g. `"es"` tolera `"es"` y `"es-AR"`) |
| `max_cost_usd` | float | Cap de costo por turno (Capa 4) |
| `max_latency_ms` | int | Cap de latencia wall clock (Capa 5) |
| `metadata` | dict | `created_at`, `regenerated_from`, `trial_policy` (extensible) |

### Walkthrough — agregar un golden nuevo

```bash
# 1. Copia el smoke existente como template:
cp backend/tests/agentic_evals/sales_agent/goldens/visionarias-smoke-golden.yaml \
   backend/tests/agentic_evals/sales_agent/goldens/<nuevo-golden>.yaml

# 2. Edita campos: id, input_message, expected_specialists, required/forbidden_tools, etc.

# 3. Resuelve offer_id real desde DB (dry-run primero — solo imprime diff):
cd backend
.venv/bin/python tests/agentic_evals/sales_agent/runner/regenerate_golden.py \
    <golden_id> --dry-run

# 4. Si el diff luce correcto, escribe el archivo:
.venv/bin/python tests/agentic_evals/sales_agent/runner/regenerate_golden.py \
    <golden_id>

# 5. Verifica que loadea:
.venv/bin/python -c "from tests.agentic_evals.sales_agent.runner.golden_loader import load_yaml; \
    print(load_yaml('<golden_id>'))"

# 6. Commit con `feat(pi-N-T-X): add <golden_id> golden ...`
```

### Por qué offer_id hardcoded (B2)

La oferta vive como UUID literal en el YAML — si admin la soft-deletea,
el smoke FALLA EXPLÍCITO en la pre-condición de la fixture (no shift
silencioso a otra oferta). Esto previene drift invisible cuando
catálogos rotan. Para refrescar: re-ejecuta `regenerate_golden.py` y
commit el delta.

---

## 4. Fixtures disponibles

Las 4 fixtures canónicas viven en `fixtures/` y se exportan vía
`conftest.py` para consumo directo por nombre (sin import manual —
pytest las descubre).

| Fixture | Scope | Propósito |
|---|---|---|
| `visionarias_tenant_session` | function | Sesión DB real + tenant Visionarias resuelto (UUID + offer + PersonalityProfile compilado). **SKIP explícito** si DB unreachable o tenant ausente. NO seedea — fail-explicit B6. |
| `sales_agent_entrypoint` | function | Harness async que invoca `agent_app.ainvoke` con `RunnableConfig.callbacks` componiendo `TrajectorySpy` + el callback handler de producción. Honra el compiler v2 de personality (sin override de voz). |
| `eval_run_id` | function | UUID único por invocación — usado como subdirectorio dentro de `_artifacts/` para no colisionar entre tests siblings. |
| `synthetic_tenant` | function | Seedea un tenant `T2_synthetic` paralelo a Visionarias para Scenario 4 (cross-tenant leak). Upsert idempotente por UUID determinístico — re-runs no duplican filas. |

### Ejemplo de uso

```python
@pytest.mark.eval  # gate por --run-evals flag
async def test_my_scenario(
    visionarias_tenant_session,  # tenant + DB
    sales_agent_entrypoint,      # invoke harness
    eval_run_id,                 # artifacts dir
):
    spec = load_yaml("my-golden-id")
    response = await sales_agent_entrypoint(
        tenant_id=visionarias_tenant_session["tenant_id"],
        message=spec.input_message,
    )
    assert_trajectory(response.spy.specialists, spec.expected_specialists, mode="includes")
    assert_tool_calls(response.spy.tool_calls, required=spec.required_tools, forbidden=spec.forbidden_tools)
    # ... assertions Capas 3/4/5
```

---

## 5. Diferencia vs tests/quality/sales_agent_goldens/

Ambas carpetas conviven con propósitos complementarios — co-existencia
ratificada en spec, no se eliminará una para favorecer la otra.

| Aspecto | `tests/agentic_evals/sales_agent/` (esta) | `tests/quality/sales_agent_goldens/` (S10 stub) |
|---|---|---|
| Invoca al agente real | **SÍ** — `agent_app.ainvoke` end-to-end vía LangGraph + LiteLLM proxy + DB | NO — solo evalúa outputs canned con LLM-as-judge |
| Costo por run | Real (~$0.005/turno LLM) | Stub default + `RUN_LLM_JUDGE=1` opt-in semanal |
| Qué mide | Trayectoria + tools + output + costo + latencia (5 capas observables) | Calidad subjetiva del output (4-dim multi-rubric NANO single JSON) |
| Cuando corre | Manual local + Story 8 (CI cron nightly futura) | Weekly cron lunes 05:00 UTC (`weekly_sales_agent_quality_eval`) |
| Origen | PI-12 S1 (mayo 2026) | sales-agent redesign abril 2026 (S10) |

**Por qué ambos:** el stub LLM-judge cubre quality drift (la voz del
tenant se pierde? las respuestas se vuelven genéricas?), mientras que
este harness cubre regresión estructural (rompimos la trayectoria de
specialists? un tool prohibido empezó a dispararse? el costo subió
10x?). Las dos preguntas son ortogonales y necesitan instrumentación
distinta.

---

## 6. Cleanup `_artifacts/`

El directorio `_artifacts/` está **gitignored** completamente (solo se
trackea su `.gitignore`). Cada run del harness escribe ahí:

```
_artifacts/<eval_run_id>/
├── trace.json        # Eventos LangChain capturados por TrajectorySpy
├── response.txt      # Output final del agente (sanitizado por sanitize_payload)
└── assertions.json   # Resultado de las 5 capas de asserts
```

Borrar contenido cuando ocupe espacio, sin temor de perder historia
versionada — los goldens (input + expectativas) viven en `goldens/`,
los artifacts son ephemeral por run:

```bash
rm -rf backend/tests/agentic_evals/sales_agent/_artifacts/
```

CI nightly futura (Story 8) subirá artifacts a S3 con retention 30d
para forensic — los locales NO necesitan archivar.

---

## 7. Cost budget

**Target por run: < $0.01 USD.**

Cada smoke single-turn con DeepSeek V4-Flash vía LiteLLM proxy ronda
$0.001-0.005 USD (depende de tier de cache hit y largo de la respuesta).
El cap declarado en el golden (`max_cost_usd: 0.01`) absorbe spikes
ocasionales por miss de prefix cache.

### Alerta de regresión

Si un run sostiene **> $0.05 USD/run** = señal clara de regresión
upstream. Causas típicas:

1. Prefix cache roto (slot 5 BRAND_VOICE invalidado por interpolación
   accidental — ver `sales-agent-expert` referencia).
2. Tier pricing incorrecto (Kimi K2.6 supera 200k tokens y el
   calculator no está dividiendo en `TIER_THRESHOLD = 200_000` —
   ver S12 cementado).
3. Specialist nuevo sin `tools=[]` explícito heredando toolset parent
   = mas calls al LLM por turno.
4. Loop infinito sin anti-loop guard (`tool_call_dedup` deshabilitado
   o threshold subido).

### Verificación post-run

Cada run escribe métricas a la tabla `sales_agent_llm_call` (Capa 4
del observability stack). Query:

```sql
SELECT model, SUM(cost_usd) AS total_usd, COUNT(*) AS calls
FROM sales_agent_llm_call
WHERE conversation_id = '<eval_run_id>'
GROUP BY model;
```

El smoke verifica `assert_cost_recorded(spec.max_cost_usd)` por
default (Capa 4) — si la tabla muestra > cap, el test falla.

---

## 8. Future story scope (S2-S9)

Lo que **NO** está en S1 foundation pero llega en stories futuras del
PI:

| Story | Alcance | Dependencias |
|---|---|---|
| Story 2 | **pass^k** aggregation across N trials por golden (capacidad de medir reliability cross-runs, no solo single-shot) | S1 cierre |
| Story 3 | **Budget cap** abort: si runs acumulados superan $5 USD por sesión CI, abortar la suite | S2 |
| Story 5 | **Multi-tenant goldens** (10+ tenants tipo Visionarias con personality + voice + offers diversos) | S2, S3 |
| Story 6 | **Personas como simulators** (LLMs adversariales que actúan como buyers reales con objeciones, dudas, intent shifts) | S5 |
| Story 7 | **Voice fidelity grader** (placeholder `assert_voice_fidelity` actual lanza `NotImplementedError`; implementación mide fidelidad slot 5 BRAND_VOICE cache prefix vs output) | S5 |
| Story 8 | **CI cron** nightly smoke run + Slack alert on regression (linkea Story 3 budget cap) | S5, S7 |
| Story 9 | **Jailbreak suite** adversarial (prompt injection + system prompt extraction + role bypass) | S6, S8 |

Ver `docs/projects/active/PI-12-sales-agent-eval-foundation/PI.md` y el
roadmap del story para fechas/orden definitivo.

---

## Anti-patterns prohibidos en este harness

- ❌ Auto-seed del tenant en la fixture si la pre-condición falla.
  **SKIP explícito** es el contrato fail-explicit (decision B6).
- ❌ Mock del callback handler de producción. El spy se compone vía
  `RunnableConfig.callbacks=[spy, production_handler]` — no reemplaza.
- ❌ Override de la voz del tenant en `sales_agent_entrypoint`. El
  harness honra el compiler v2 — la voz es parte de lo que se mide.
- ❌ Hardcodear `tenant_id` o `offer_id` en el código del test. Vienen
  del YAML golden.
- ❌ Borrar `_artifacts/` mid-run (corrompe el assertion writer). Solo
  cleanup post-run o pre-run.
- ❌ Subir `_artifacts/` al git (gitignored — si aparece en `git status`
  hay un bug en el `.gitignore`).
- ❌ Ejecutar `regenerate_golden.py` automático como parte del test. Es
  CLI exclusivamente humana — re-bind de `offer_id` es acción
  deliberada.

---

## Referencias cruzadas

- Spec: `01-spec.md` (gherkin AI-resistant)
- Arquitectura BE: `03-arch-be.md` (golden YAML schema, 5 capas de
  asserts, fixture lifecycle)
- Arquitectura agentic: `03-arch-agentic.md` (TrajectorySpy contract,
  sanitize_payload reuse)
- Skill SSoT: `.claude/skills/sales-agent-expert/SKILL.md`
- Anti-duplication: `.claude/rules/anti-duplication.md` § shared abstractions inventory
