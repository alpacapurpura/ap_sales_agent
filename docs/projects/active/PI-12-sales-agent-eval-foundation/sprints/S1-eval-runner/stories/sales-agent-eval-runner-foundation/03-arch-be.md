# 03-arch-be.md — Eval Runner Foundation (BE harness)

---
story_id: sales-agent-eval-runner-foundation
surface: BE
sub_architect: /architect (acting BE+Agentic — no recursion per /pm prompt)
arch_version: 1
last_modified: 2026-05-05T03:30Z
links:
  spec: "01-spec.md"
  story_yaml: "../../../../../../product/stories/sales-agent/sales-agent-eval-runner-foundation.yaml"
  pi: "../../../PI.md"
  rules:
    - ".claude/rules/tdd-mandatory.md"
    - ".claude/rules/tenant-isolation.md"
    - ".claude/rules/anti-duplication.md"
    - ".claude/rules/sales-agent-brand-voice.md"
    - ".claude/rules/copilot-observability.md"
    - ".claude/rules/parallel-safety.md"
---

## Decisión arquitectónica clave

El harness vive en una **directorio nuevo aislado** `backend/tests/agentic_evals/sales_agent/` que es **fuera del coverage tree** (`tool.coverage.run.source = ["src/modules", "src/shared"]` no lo incluye), agrega cero deuda al código `src/`, y se gatea con un nuevo flag `pytest --run-evals` + marker `@pytest.mark.eval` registrado al **root del eval suite** (`backend/tests/agentic_evals/conftest.py`). Esto preserva el SLA de tiempo CI (suite default sin evals < 60s) mientras habilita evals on-demand y el cron nightly de Story 8.

Se usa el **canonical entry point `agent_app.ainvoke(initial_state, config=...)`** definido en `src/modules/sales_agent/application/orchestrator/graph.py:52` — no se levanta FastAPI. El harness compone el `initial_state` reusando `create_initial_state(...)` (state.py) + `ConversationPipeline.build_agent_identity` + `ConversationPipeline.build_brand_voice` para no mockear voz (B6 honra `PersonalityProfile.system_instruction`).

DB real (dev Postgres del compose) + LiteLLM proxy real (`visionarias_litellm:4000`) son requisitos del flag `--run-evals`. Costo real esperado: ~$0.005 por corrida del smoke (1 turno DeepSeek V4-Flash).

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] Self-run greps (Path B — no CONTEXT-BRIEF.md presente para esta story)

### Audit cross-module ejecutado
```bash
# 1. ¿Existe ya algún harness de evals para sales_agent?
ls backend/tests/agentic_evals/                          # → MISSING (greenfield)
# 2. Existe SalesAgentJudge + GOLDEN_CONVERSATIONS para weekly cron?
ls backend/tests/quality/sales_agent_goldens/            # → exists: weekly-judge stub goldens (S10)
# 3. Existe BaseAgentCallbackHandler shared?
grep -n "class BaseAgentCallbackHandler" backend/src/shared/agent_observability/recording/base_callback_handler.py  # → 80
# 4. Existe SalesAgentCallbackHandler subclass para sales_agent?
grep -n "class SalesAgentCallbackHandler" backend/src/modules/sales_agent/observability/recording/callback_handler.py  # → 49
# 5. Existe SalesAgentObservabilityContext + factory?
ls backend/src/modules/sales_agent/observability/recording/  # → callback_handler.py + factory.py + turn_envelope.py
# 6. Existe FXResolver.default() shared?
grep -n "def default" backend/src/shared/agent_observability/cost/fx_resolver.py  # → exists
# 7. Existe el canonical entry point del agente?
grep -n "agent_app = " backend/src/modules/sales_agent/application/orchestrator/graph.py  # → 52
```

### Sistemas existentes encontrados

| Sistema | Path | Enum/Config | Factory/Router | Providers/Adapters | Estado |
|---|---|---|---|---|---|
| Agentic eval root | `backend/tests/agentic_evals/` | n/a | n/a | n/a | **MISSING** (greenfield, T1 crea) |
| Sales-agent quality stub goldens (weekly-judge) | `backend/tests/quality/sales_agent_goldens/` | RUN_LLM_JUDGE env | `SalesAgentJudge` | stub LLM | active (S10 — judge-style, no end-to-end agent invoke) |
| Shared callback handler | `shared/agent_observability/recording/base_callback_handler.py:80` | n/a | Template Method base | n/a | active (T3 EXTENDS) |
| SalesAgent callback handler | `sales_agent/observability/recording/callback_handler.py:49` | n/a | concrete subclass | wires lead_id+channel_type | active (T3 reuses via observability_context factory) |
| SalesAgent observability context factory | `sales_agent/observability/recording/factory.py:113` | n/a | `build_sales_agent_observability_context(...)` | n/a | active (T3 invokes verbatim) |
| Sales agent canonical entrypoint | `sales_agent/application/orchestrator/graph.py:52` (`agent_app`) | n/a | LangGraph `compile()` | n/a | active (T2 fixture invokes `agent_app.ainvoke`) |

### Decisión por sistema
- **Agentic eval root**: **NEW** — directory tree no existe. T1 crea estructura definida en spec B3.
- **Sales-agent stub goldens (S10)**: **CO-EXIST**. Distinto propósito: weekly-judge LLM-as-judge sobre conversaciones canned vs. eval-runner end-to-end agente real + multi-capa. README.md de T6 documenta la diferencia para evitar confusión futura.
- **Shared callback handler**: **EXTEND** vía composición — T3 NO subclassea ni mirror. Usa el `SalesAgentObservabilityContext` ya existente (que ya extiende `BaseAgentCallbackHandler` por la cadena copilot+sales_agent), y agrega un **trajectory spy decorator** que envuelve el handler nativo para capturar `state.next_node` history + `tool_calls` por turn sin tocar shared. Anti-duplication satisfecho — no se crea un cuarto handler.
- **SalesAgent callback/factory/context**: **REUSE verbatim**. T3 llama `build_sales_agent_observability_context(...)` para tener el handler que escribe a DB real (Capa 4 del spec). El spy es un wrapper local del harness, no replaces.
- **Canonical entrypoint `agent_app`**: **REUSE** verbatim — T2 fixture `sales_agent_entrypoint` retorna closure que llama `agent_app.ainvoke(initial_state, config=ctx.langchain_config())`.

## Surface diff (BE)

### Endpoints nuevos / modificados

n/a — eval-runner es `tests/agentic_evals/`. No toca `src/`. No HTTP. No DTOs Pydantic. No migrations.

### Estructura de directorio (T1 crea)

```
backend/tests/agentic_evals/
├── __init__.py                                    # T1 (empty)
├── conftest.py                                    # T2 — root: registra @pytest.mark.eval + addoption --run-evals
└── sales_agent/
    ├── __init__.py                                # T1
    ├── README.md                                  # T6 — cómo agregar goldens, fixtures disponibles, run local
    ├── conftest.py                                # T2 — fixtures: visionarias_tenant_session, eval_run_id,
    │                                                       sales_agent_entrypoint, trajectory_spy
    ├── runner/
    │   ├── __init__.py                            # T1
    │   ├── golden_loader.py                       # T5 — YAML loader + GoldenSpec dataclass
    │   ├── trajectory_spy.py                      # T3 — TrajectorySpy: capture state.next_node history + tool_calls
    │   ├── assertions.py                          # T4 — 5 assertion funcs returning named-failure exceptions
    │   ├── artifacts.py                           # T3 — write trace.json, response.txt, assertions.json
    │   └── regenerate_golden.py                   # T5 — script CLI: python regenerate_golden.py <golden_id>
    ├── goldens/
    │   └── visionarias-smoke-golden.yaml          # T5 — 1 hardcoded golden
    ├── fixtures/
    │   ├── __init__.py                            # T1
    │   └── synthetic_tenant.py                    # T2 — create T2_synthetic tenant + offer for Scenario 4
    ├── _artifacts/                                # T1 — gitignored runtime
    │   └── .gitignore                             # T1 — `*` (entire dir)
    ├── test_eval_runner_fixtures.py               # T2 — meta-tests of the fixtures (TDD baseline)
    └── test_eval_runner_smoke.py                  # T5 — 4 scenarios from spec
```

### Pytest plumbing (T2)

**Marker registration** (`backend/tests/agentic_evals/conftest.py` — root del eval suite):
```python
import pytest

def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--run-evals",
        action="store_true",
        default=False,
        help="Run agentic evaluation suite (real LLM calls, ~$0.005/run).",
    )

def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "eval: agentic eval suite — requires --run-evals flag (real LLM cost).",
    )

def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip @pytest.mark.eval-decorated tests when --run-evals not passed."""
    if config.getoption("--run-evals"):
        return
    skip_marker = pytest.mark.skip(reason="eval markers require --run-evals flag")
    for item in items:
        if "eval" in item.keywords:
            item.add_marker(skip_marker)
```

**Coverage exclusion** — `backend/pyproject.toml` `[tool.coverage.run].omit` already lists `*/__init__.py` + `*/workers/*`; eval suite vive en `tests/agentic_evals/**` y NO está en `source = ["src/modules", "src/shared"]`. Coverage gate (43%) no afectado.

**Backwards-compat con default `addopts = "-m 'not verify'"`**: el `eval` marker NO está en `not verify` exclusion, pero `pytest_collection_modifyitems` añade `skip` cuando `--run-evals` ausente. CI default → todos `eval`-marked tests SKIP. Suite verde en push CI sin gastar budget.

### Fixtures (T2 detail)

#### `visionarias_tenant_session`

```python
@pytest.fixture
def visionarias_tenant_session(db_session, env_config) -> dict:
    """Real DB session bound to Visionarias tenant. Precondition-checks
    that the tenant exists + has at least one active offer.

    NEVER seeds. If precondition fails the fixture skips with reason —
    explicit failure mode (per /architect spec § sales_agent_entrypoint).
    """
    visionarias_id = UUID(env_config.get("VISIONARIAS_TENANT_ID",
                                          "00000000-0000-0000-0000-000000000001"))
    # Tenant existence
    tenant_row = db_session.execute(
        select(TenantModel).where(TenantModel.id == visionarias_id)
    ).scalar_one_or_none()
    if tenant_row is None:
        pytest.skip(f"Visionarias tenant {visionarias_id} not seeded in DB. "
                    f"Run `make seed-visionarias` then retry.")
    # Active offer
    offer_row = db_session.execute(
        select(OfferModel)
        .where(OfferModel.tenant_id == visionarias_id, OfferModel.deleted_at.is_(None))
        .order_by(OfferModel.created_at.desc())
        .limit(1)
    ).scalar_one_or_none()
    if offer_row is None:
        pytest.skip(f"Visionarias has 0 active offers. Required for smoke golden.")
    # PersonalityProfile
    knowledge_builder = TenantKnowledgeBuilder(db_session)
    brand_voice = knowledge_builder.build_brand_voice(visionarias_id)
    if not brand_voice:
        pytest.skip(f"Visionarias has no compiled PersonalityProfile.system_instruction.")
    return {
        "tenant_id": visionarias_id,
        "offer": offer_row,
        "brand_voice": brand_voice,
        "db_session": db_session,
    }
```

**Decision:** option (a) precondition-check + skip (NOT seed-if-missing). Aligns spec scenario 1 + ratified Decision B2 ("hardcoded offer_id... if offer disappears → fail explicit ('regenerate golden'), NOT silent shift"). Smoke goldens reference offer_id directly; seed accountability is on the dev environment, not the harness.

#### `eval_run_id`

```python
@pytest.fixture
def eval_run_id() -> UUID:
    """One UUID4 per test invocation. Used as artifacts subdir name."""
    return uuid4()
```

#### `sales_agent_entrypoint`

```python
@pytest.fixture
async def sales_agent_entrypoint(visionarias_tenant_session, eval_run_id):
    """Async closure invoking sales_agent without FastAPI startup.

    Composes initial_state via ConversationPipeline helpers (NOT mocked),
    builds SalesAgentObservabilityContext via factory (NOT mocked — writes
    real rows to sales_agent_trace_event + sales_agent_llm_call), and
    invokes agent_app.ainvoke with the bound observability context.
    """
    tenant_id = visionarias_tenant_session["tenant_id"]
    db = visionarias_tenant_session["db_session"]

    # Synthetic lead — eval-only, marked is_eval=True for filtering in admin Streamlit
    lead_id = create_synthetic_eval_lead(db, tenant_id=tenant_id, run_id=eval_run_id)

    # Build observability context (real recorder → real DB writes — Capa 4)
    obs_ctx = build_sales_agent_observability_context(
        db=db, tenant_id=tenant_id, lead_id=lead_id,
        channel_type="eval_harness", turn_id=uuid4(), role="agent",
    )

    async def _invoke(user_message: str) -> dict:
        # Build minimal initial_state honoring B6 (no voice override)
        knowledge_builder = TenantKnowledgeBuilder(db)
        agent_identity = knowledge_builder.build_identity(tenant_id)
        brand_voice = knowledge_builder.build_brand_voice(tenant_id)
        initial_state = create_initial_state(
            user_id=str(lead_id),
            tenant_id=str(tenant_id),
            agent_identity=agent_identity,
            brand_voice=brand_voice,
            channel_type="eval_harness",
            history=[],
        )
        initial_state["messages"] = [{"role": "user", "content": user_message}]
        # Invoke — agent_app already wraps trace_node decorator on supervisor
        if obs_ctx is not None:
            async with obs_ctx.observe_turn(message=user_message, route="sales_agent"):
                result = await agent_app.ainvoke(
                    initial_state, config=obs_ctx.langchain_config()
                )
        else:
            result = await agent_app.ainvoke(initial_state, config={})
        return {"result": result, "lead_id": lead_id, "turn_id": obs_ctx.turn_id if obs_ctx else None}

    return _invoke
```

**Knowledge cutoff disclosure:** Opus 4.7 cutoff Jan 2026; LangGraph `astream` patterns + LiteLLM proxy stripping are post-cutoff in Nicolify codebase but already cemented in `BaseAgentCallbackHandler._extract_provider_and_model` (line 542 D-7). I researched live on 2026-05-05 by reading the source — no WebSearch needed for in-house patterns.

#### `trajectory_spy` (see `03-arch-agentic.md` for state-machine detail)

Yields a `TrajectorySpy` instance bound to the same observability context. Captures `state.next_node` after each LangGraph node execution + tool_call name list. Persists to `_artifacts/{run_id}/trace.json` at test teardown.

### Golden YAML schema (T5)

```yaml
# backend/tests/agentic_evals/sales_agent/goldens/visionarias-smoke-golden.yaml
---
id: visionarias-smoke-001
version: 1
schema_version: 1
tenant_id_env: "VISIONARIAS_TENANT_ID"     # resolved by fixture, NOT hardcoded UUID
offer_id: "<<UUID hardcoded — see regenerate_golden.py output>>"
input_message: |
  Hola, vi su publicidad sobre {{offer_name}}. ¿Cuánto cuesta y cómo es la metodología?
expected_assertions:
  trajectory:
    first_specialist: qualifier                # state.next_node[0] after supervisor
    forbidden_specialists: [closer]             # never present in next_node history
  required_tools: []                            # entry point invokes specialist nodes, NOT tool calls
  forbidden_tools:                              # B4 mapping → see 03-arch-agentic.md
    - send_payment_link                         # closer-finalize family
    - generate_payment_link
    - create_payment_link
    - mark_enrollment_paid_manual
    - grant_access
    - create_booking_link                       # scheduling family — premature for cold lead
  output:
    min_length: 50
    spanish_marker_min_count: 3                 # custom assertion (Capa 3) — see langdetect note
    must_mention_one_of: ["Visionarias", "{{offer_name}}"]
  cost:
    min_cost_usd: 0.0001                        # > 0 (Story A canonicalization gate)
    expected_provider: deepseek
    model_pattern: "deepseek-v4-flash"          # regex-anchored prefix
  latency:
    max_ms: 30000                               # p95 spec
metadata:
  created_at: "2026-05-05T03:30:00Z"
  regenerated_from: null                        # populated by regenerate_golden.py
  trial_policy:
    trials_per_scenario: 1                      # Story 2 → 3
```

**`regenerate_golden.py`** (T5 companion, B2): CLI script that queries Visionarias DB, picks top-1 offer by `created_at desc`, rewrites the YAML with new `offer_id` + `metadata.regenerated_from = <previous_offer_id>` + `metadata.created_at = now()`. Run only when previous offer is soft-deleted (deliberate human action — never automatic).

### `langdetect` integration (T4 / B5)

**Decision (B5 ratified):** add `langdetect==1.0.9` (MIT, last 2014 release on PyPI; mature, stable, pure-Python, ~1MB) to `backend/pyproject.toml` under a new `[project.optional-dependencies].evals` group so production install is unaffected. The `eval` marker fixtures import it lazily inside the assertion module to keep cold-import zero on default CI.

```toml
[project.optional-dependencies]
evals = [
    "langdetect==1.0.9",
]
```

**Wrapper** (`runner/assertions.py`):
```python
def _detect_language_safe(text: str) -> str:
    """Return ISO 639-1 code or 'unknown' on LangDetectException.

    langdetect throws on inputs <2 chars or pure punctuation. The smoke
    output is always ≥50 chars (assert_output_min_length runs first), so
    in practice this guard is for defensive correctness only.
    """
    try:
        from langdetect import detect, LangDetectException  # lazy
        return detect(text)
    except (LangDetectException, ImportError):
        return "unknown"
```

The Capa 3 assertion combines `_detect_language_safe(response) == "es"` AND `spanish_marker_count >= 3` (regex word-boundary count of [`que`, `de`, `la`, `el`, `los`, `las`, `con`, `por`, `para`]) — defense-in-depth: langdetect catches genuine regression to English, marker count catches edge-case English with code-switching.

### Assertion library (T4 detail)

Each assertion function returns nothing on pass + raises a named exception subclass on fail with diagnostic context. All exceptions inherit from `LayerAssertionError` for unified error reporting in `assertions.json` artifact.

```python
class LayerAssertionError(AssertionError):
    """Base — every layer failure raises a subclass with .layer_name + .observed + .expected."""
    layer_name: str

class TrajectoryAssertionError(LayerAssertionError):
    layer_name = "trajectory"

class ToolCallsAssertionError(LayerAssertionError):
    layer_name = "tool_calls"

class OutputAssertionError(LayerAssertionError):
    layer_name = "output"

class CostAssertionError(LayerAssertionError):
    layer_name = "cost"

class LatencyAssertionError(LayerAssertionError):
    layer_name = "latency"

# Public API
def assert_trajectory(spy: TrajectorySpy, *, first_specialist: str,
                      forbidden_specialists: list[str]) -> None: ...
def assert_tool_calls(spy: TrajectorySpy, *, required: list[str],
                      forbidden: list[str]) -> None: ...
def assert_output(text: str, *, min_length: int, spanish_marker_min_count: int,
                  must_mention_one_of: list[str]) -> None: ...
def assert_cost_recorded(db: Session, *, tenant_id: UUID, turn_id: UUID,
                         min_cost_usd: Decimal, model_pattern: str) -> None: ...
def assert_latency(start_ts: float, end_ts: float, *, max_ms: int) -> None: ...

# Story 7 future-proof slot — placeholder, NOT invoked in smoke
def assert_voice_fidelity(response: str, *, threshold: float = 0.7) -> None:
    """Reserved for Story 7 voice fidelity grader (LLM-as-judge).
    Smoke MUST NOT call this — see Decision B6.
    """
    raise NotImplementedError("Voice fidelity grader is Story 7 scope. "
                              "Do not invoke in foundation harness.")
```

### Migrations

**None.** Eval suite uses real DB tables (`sales_agent_trace_event`, `sales_agent_llm_call`, `tenants`, `offers`, `personality_profiles`) all created by prior PI/sprint migrations. Synthetic eval lead created via repository helper, soft-deleted at test teardown.

### Tests requeridos

- `tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py` — **TDD baseline (T2 RED first)**:
  - `test_visionarias_tenant_session_returns_dict_with_tenant_offer_brand_voice` — fixture happy
  - `test_visionarias_tenant_session_skips_if_no_offer` — preconditioncheck negative
  - `test_eval_run_id_is_unique_uuid4` — basic
  - `test_sales_agent_entrypoint_returns_async_callable` — basic
  - `test_trajectory_spy_captures_first_specialist_and_tool_calls` — anti-mock-only design
  - `test_artifacts_writer_creates_run_id_subdir_with_3_files` — filesystem layer
- `tests/agentic_evals/sales_agent/test_eval_runner_smoke.py` — **4 scenarios from spec** (T5 RED → GREEN):
  - `test_smoke_multi_layer` (Scenario 1, happy)
  - `test_skip_without_flag` (Scenario 2, negative — uses `pytest.runpytest_subprocess`)
  - `test_degraded_output_caught` (Scenario 3, edge — monkeypatches `LiteLLMService.generate_response`)
  - `test_no_cross_tenant_leak` (Scenario 4, adversarial — uses `synthetic_tenant` fixture)
- Coverage gate **not affected**: eval suite outside `[tool.coverage.run].source`.

## Cross-cutting concerns

- **Tenant isolation:** `visionarias_tenant_session` filters every query by `tenant_id == VISIONARIAS_TENANT_ID`. Scenario 4 explicit regression. `synthetic_tenant.py` fixture creates `T2_synthetic` with its own `offer_T2` to validate the harness does NOT leak. Audit log entry: `structlog.info("eval_cross_tenant_check", tenant_id_expected=..., tenant_id_observed=...)` per spec NFR.
- **Idempotency:** `eval_run_id = uuid4()` per invocation. Each run is independent. No idempotency key needed.
- **Rate limiting:** none — eval is internal pytest, not HTTP.
- **Caching:** none.
- **Backwards compatibility:** harness is additive. CI default = SKIP. No existing test affected. No `src/` touched.
- **PII:** smoke golden uses generic input ("Hola, vi su publicidad sobre <oferta>...") — no PII of real prospects. `sales_agent_entrypoint` creates synthetic lead (no real WhatsApp/Telegram identifier). Future stories with real conversations (Story 5) MUST apply `sanitize_payload` to artifacts before write — documented in T6 README.
- **Spanish neutro:** docs (00, 01, 03, README) en español neutro LATAM. Code symbols in English. **EXCEPTION applies:** the agent's output may contain voseo if Visionarias `PersonalityProfile.system_instruction` does — `assert_output` only validates Spanish density, never style (per `.claude/rules/sales-agent-brand-voice.md` § "Excepción").
- **Native-first dev:** all commands native WSL — `cd backend && .venv/bin/pytest`. No `docker exec`. Confirmed in T6 README.

## ARQ-vs-CI question (resolved)

**This story does NOT add ARQ scheduling.** The eval runs:
- **on-demand** via `make eval-smoke` (T6) for dev work,
- **nightly cron** added in **Story 8** (`sales-agent-eval-ci-gate`, future PI-12 sprint),
- **never** as part of the default `pytest` invocation (skipped via `pytest_collection_modifyitems`).

No `backend/src/modules/sales_agent/workers/` change. No ARQ task. No `weekly_*` cron addition.

## Architecture Fitness Impact

Gates that must keep passing post-merge:
- `tests/architecture/` — full suite (no `src/` touched, low risk)
- `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` — n/a (we don't mock EventBus)
- `tests/architecture/test_no_cross_module_imports.py` — VERIFY: harness imports allowed (`tests/` not in module ratchet)
- Coverage 43% gate — unaffected (eval not in source tree)

**Allowlist updates:** none expected.

## pm-nico/current-state Updates Required

- **None for runtime user-facing capability** — eval suite is dev-internal infrastructure. No user-visible feature added.
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` already updated by /po (gap "Eval suite agentic faltante" addressed). Post-merge `/pm` flips story status `planned → done`.

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Visionarias sin offer en dev DB → smoke skip (NO falla) | medium | Fixture explícito skip con reason `"Run make seed-visionarias"`. T6 README documenta. CI nocturna debe seedear pre-run (Story 8 scope). |
| LiteLLM proxy down → smoke fails Capa 4 | medium | `tessl__graceful-degradation` Rule 1 — `httpx` timeout 5s en LiteLLM client (ya cementado en `providers/litellm.py`). Fallback: si todos los rows `cost_usd == 0`, fail con mensaje `"Cost layer un-verifiable: LiteLLM proxy may be down or Story A not merged"`. |
| `langdetect` dependency 2014 sin updates | low | Mature, stable port of Google's java lib. Has known unicode quirks for very short inputs (mitigated by min_length=50 precondition). Reabrir `fast-langdetect` solo si langdetect breaks Python 3.12+. |
| Trajectory spy decorator interactúa con `trace_node` decorator existente (`infrastructure/monitoring/tracing.py`) | medium | Spy es **post-execution observer** (lee state delta de `node_exit` event en `BaseAgentCallbackHandler.on_chain_end`), NO subclassea `trace_node`. Cohabitación documentada en `03-arch-agentic.md`. |

## Decisiones registradas

- **2026-05-05 — pytest-style flag gate (vs env var):** `--run-evals` CLI flag elegido over `EVAL_SUITE=1` env var. Razón: pytest-native, integra con `pytest --collect-only --run-evals` para auditar qué corre, evita pollución del shell env. Pattern análogo: `RUN_LLM_JUDGE=1` (env var) en `quality/sales_agent_goldens/` — diferenciamos: judge corre offline sobre conv canned, eval-runner gasta budget LLM real, justifica flag explícita.
- **2026-05-05 — option (a) precondition skip vs (b) seed-if-missing:** Decisión B2 ratificó "fail explicit, NO silent shift" → harness skips, no seed. Burden de seed en make target o Story 8 cron.
- **2026-05-05 — `langdetect` lazy import:** importamos dentro de `_detect_language_safe` para que ImportError (faltante en venv eval) NO rompe collection del default test suite. Evita acoplar suite default al optional-dep.
- **2026-05-05 — coverage exclusion**: `tests/agentic_evals/**` ya está outside `tool.coverage.run.source = ["src/modules", "src/shared"]` del pyproject — sin acción adicional, gate 43% intacto.

## Próximo paso

`done -> 03-arch-be.md` (devuelvo referencia al orchestrator /architect).
