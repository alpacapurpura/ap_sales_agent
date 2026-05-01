# CONTRACT — PR-2-shared-agent-observability

> Owner: `nicolify-architect` Opus. Producido 2026-05-01. PR-folder: `docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S2-shared-observability/prs/PR-2-shared-agent-observability/`.

## § 0 — Context summary + surface mapping

| Campo | Valor |
|---|---|
| Architect run on | 2026-05-01 |
| Modules tocados | `shared/agent_observability/`, `modules/copilot/observability/`, `modules/copilot/application/orchestrator/`, `modules/sales_agent/observability/`, `modules/sales_agent/application/orchestrator/` |
| Tipo | Refactor LIFT-TO-SHARED + EXTEND. Anti-duplication primer enforcement test (rule `.claude/rules/anti-duplication.md`). |
| Skills consultados | `copilot-expert`, `sales-agent-expert`, `tessl__langgraph`, `tessl__graceful-degradation` |
| CONTEXT-BRIEF source | None — fallback Path B self-run greps (Step 0.2 evidence below). |
| pm-nico/current-state files afectados | `docs/pm-nico/current-state/sales_agent.md` (append capability "Observability traces persistence — live"), `docs/pm-nico/current-state/copilot.md` (append note "Observability lifecycle refactored to shared base — no user-facing change") |
| Architecture gates that must keep passing | `tests/architecture/test_sales_agent_observability_invariants.py`, `tests/architecture/test_shared_agent_observability_purity.py`, `tests/architecture/test_copilot_anchors.py`, `tests/architecture/test_no_new_copilot_module_imports.py`, `tests/architecture/test_ddd_boundaries.py` |

### Surface → builder → auditor mapping

PM uses this table to spawn correct agents:

| Surface | Path | Builder | Auditor |
|---|---|---|---|
| Shared base envelope (NEW abstract) | `backend/src/shared/agent_observability/recording/turn_envelope.py` | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |
| Shared FX factory (EXTEND classmethod) | `backend/src/shared/agent_observability/cost/fx_resolver.py` | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |
| Copilot concrete context (EXTRACT subclass) | `backend/src/modules/copilot/observability/recording/turn_envelope.py` (refactor in place — class becomes subclass; module re-export preserved for back-compat) | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |
| Sales agent concrete context (NEW subclass) | `backend/src/modules/sales_agent/observability/recording/turn_envelope.py` (NEW — NOT mirror of copilot; minimal subclass that adds `lead_id` + `channel_type` fields) | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |
| Copilot orchestrator integration | `backend/src/modules/copilot/application/orchestrator/chat.py` (replace inline `FXResolver(http_client_factory=...)` with `FXResolver.default()`; import path unchanged via `from src.modules.copilot.observability import ObservabilityContext`) | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |
| Sales agent orchestrator integration | `backend/src/modules/sales_agent/application/orchestrator/chat.py` + `outbound_orchestrator.py` + `conversation_pipeline.py::invoke_agent_with_typing` (wire envelope `observe_turn` lifecycle around `ainvoke`) | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |
| Sales agent factory bug fix (Bug #8) | `backend/src/modules/sales_agent/observability/recording/factory.py` line 78 — `FXResolver()` → `FXResolver.default()` | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |
| Tests (real DB persistence + regression + base contract + arch ratchet) | `backend/tests/{shared/agent_observability,modules/copilot/observability,modules/sales_agent/observability,architecture}/...` | `nicolify-agentic` (Opus) | `nicolify-agentic-auditor` (Opus) |

**No FE surface.** Refactor invisible al cliente. No copilot tools. No new endpoints — `response_model=` invariant N/A.

### Skill decisions referenced

- **`copilot-expert` § 0 (anti-duplication cardinal)**: shared abstractions must live in `shared/agent_observability/`. Decisión: lift `ObservabilityContext` semantics a `shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext`; copilot existing class becomes thin subclass.
- **`copilot-expert` "Best-effort observability"**: every persistence path wraps `try/except` + `structlog warning` + session rollback. Base envelope MUST preserve this — already canonical en copilot file.
- **`sales-agent-expert` § 0 (anti-duplication cardinal)**: mirror prohibido. Lift `turn_envelope` PRIMERO, después sales_agent + copilot consumen.
- **`sales-agent-expert` § 3 surface protected**: `BufferService.smart_debounce`, `OutputManager.process_response` chunking, `enrollment_*`, webhook adapters, `follow_up_engine` cadence, `tool_call_dedup.py` — NO se tocan en este PR. Sólo se agrega `observe_turn` lifecycle alrededor de `agent_app.ainvoke` en `conversation_pipeline.invoke_agent_with_typing`.
- **`tessl__langgraph` "State management"**: callback handler propaga via `RunnableConfig(callbacks=[...])` — wiring ya existe (chat.py:343, outbound_orchestrator.py:237). Lifecycle envelope sólo necesita envolver el `ainvoke` con `async with ctx.observe_turn(...)`.
- **`tessl__graceful-degradation` Rule 1+2**: every external call (Frankfurter FX, DB persist) requires timeout + fallback. `FXResolver.default()` encapsula `httpx.Client(timeout=10)` + ya retorna `(Decimal(1), "fx_unavailable")` on failure. Persistence writes ya wrap try/except + logger.warning. Patrón canónico preservado.

---

## § 1 — Existing systems audit (NO-NEW-LAYER rule, real grep evidence)

### Source of evidence

- [x] Self-run greps (Path B — fallback). `CONTEXT-BRIEF.md` no producido por Haiku para este PR (PR.md routea directo al architect Opus).
- [x] Cross-validated contra `.claude/rules/anti-duplication.md` Inventario canónico shared abstractions.

### 1.1 Anti-duplication inventory consulta

```text
$ cat .claude/rules/anti-duplication.md | grep -E "Observability turn envelope|FX resolver factory"

| **Observability turn envelope** | shared/agent_observability/recording/turn_envelope.py::BaseObservabilityContext (PR-2 pendiente) | copilot/observability/recording/context.py · sales_agent/observability/recording/context.py · futuros agentes |
| **FX resolver factory** | shared/agent_observability/cost/fx_resolver.py::FXResolver.default() (PR-2 pendiente — actual requiere http_client_factory arg) | todos agentes que registran cost |
```

Inventario explícitamente menciona ambos subsystems como "PR-2 pendiente". Esta PR ES PR-2 — entrega exactamente lo prometido.

### 1.2 Cross-codebase greps — turn envelope subsystem

```text
$ find /home/chris/AISALESHT/backend/src -name "turn_envelope.py" 2>/dev/null
/home/chris/AISALESHT/backend/src/modules/copilot/observability/recording/turn_envelope.py
```

Sólo existe en copilot. Sales_agent NO tiene `turn_envelope.py` (post-revert commit `03f5462c` 2026-05-01).

```text
$ grep -rn "class.*ObservabilityContext\|class.*Envelope" \
    /home/chris/AISALESHT/backend/src/shared/ \
    /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null

backend/src/modules/copilot/observability/__init__.py:6:here except for the single entrypoint :class:`turn_envelope.ObservabilityContext`.
backend/src/modules/copilot/observability/__init__.py:29:* :class:`ObservabilityContext` — per-turn handle imported by the
backend/src/modules/copilot/observability/recording/domain_subscribers.py:9:by :class:`turn_envelope.ObservabilityContext.observe_turn` because the
backend/src/modules/copilot/observability/recording/turn_envelope.py:78:class ObservabilityContext:
```

Sólo una `ObservabilityContext` cross-codebase, en copilot. **NO existe `BaseObservabilityContext` ni equivalente en `shared/`.**

```text
$ grep -rn "async def observe_turn\|@asynccontextmanager" \
    /home/chris/AISALESHT/backend/src/shared/agent_observability/ \
    /home/chris/AISALESHT/backend/src/modules/copilot/observability/ \
    /home/chris/AISALESHT/backend/src/modules/sales_agent/observability/ 2>/dev/null

backend/src/modules/copilot/observability/recording/turn_envelope.py:174:    @asynccontextmanager
backend/src/modules/copilot/observability/recording/turn_envelope.py:175:    async def observe_turn(
```

Único callsite del lifecycle async ctx mgr es copilot. Sales_agent NO tiene observe_turn → confirma bug #2 root cause: `turn_start` / `turn_end` rows nunca se escriben para sales_agent porque no hay envelope que los emita. Callback handler sólo escribe `llm_call` / `tool_call` (en LangChain events) — turns sin LLM call escriben **0 rows**.

### 1.3 Cross-codebase greps — FX resolver factory

```text
$ grep -rn "FXResolver(" /home/chris/AISALESHT/backend/src/ 2>/dev/null | grep -v "class FXResolver"

backend/src/modules/copilot/application/orchestrator/chat.py:647:            fx_resolver=FXResolver(
backend/src/modules/sales_agent/observability/recording/factory.py:78:        fx_resolver = FXResolver()

$ grep -rn "http_client_factory" /home/chris/AISALESHT/backend/src/ 2>/dev/null

backend/src/shared/agent_observability/cost/fx_resolver.py:41:    ``http_client_factory`` returns a fresh client per call. In production
backend/src/shared/agent_observability/cost/fx_resolver.py:47:    http_client_factory: Callable[[], _HttpClientLike]
backend/src/shared/agent_observability/cost/fx_resolver.py:84:            client = self.http_client_factory()
backend/src/modules/copilot/application/orchestrator/chat.py:648:                http_client_factory=lambda: httpx.Client(timeout=10),
```

**Findings (corrects PR.md claim of "factory.py:116, 168"):**

| Call site | Status | Bug |
|---|---|---|
| `copilot/application/orchestrator/chat.py:647-649` | OK — `FXResolver(http_client_factory=lambda: httpx.Client(timeout=10))` | none |
| `sales_agent/observability/recording/factory.py:78` | BROKEN — `FXResolver()` no-arg → dataclass missing required `http_client_factory` field → `TypeError` at construct time → `except` block at `factory.py:94` swallows it → `logger.warning("sales_agent_callback_handler_factory_failed")` → `return None` → orchestrator gets `handler=None` → `config={}` empty → ZERO observability writes for sales_agent. **This is bug #2 enabling root cause.** |

**PR.md said "factory.py:116, 168" — incorrect. Only one bad call site at `factory.py:78`.** Architect corrects PR.md scope. Builder must verify before edit.

### 1.4 Cross-codebase greps — callback handler base + shared inventory

```text
$ find /home/chris/AISALESHT/backend/src -name "callback_handler.py" 2>/dev/null
backend/src/modules/copilot/observability/recording/callback_handler.py
backend/src/modules/sales_agent/observability/recording/callback_handler.py

$ grep -rn "class.*CallbackHandler" /home/chris/AISALESHT/backend/src/shared/ /home/chris/AISALESHT/backend/src/modules/ 2>/dev/null

backend/src/shared/agent_observability/recording/base_callback_handler.py:80:class BaseAgentCallbackHandler(BaseCallbackHandler, ABC):
backend/src/modules/copilot/observability/recording/callback_handler.py:48:class ObservabilityCallbackHandler(BaseAgentCallbackHandler):
backend/src/modules/sales_agent/observability/recording/callback_handler.py:49:class SalesAgentCallbackHandler(BaseAgentCallbackHandler):
```

**Excelente patrón canónico: callback handler ALREADY uses Template Method** — `BaseAgentCallbackHandler` (ABC en shared) + 2 concrete subclasses (one per agent). Este PR replica el mismo patrón para envelope: `BaseObservabilityContext` (ABC en shared) + 2 concrete subclasses.

### 1.5 Cross-codebase greps — full shared/agent_observability inventory

```text
$ find /home/chris/AISALESHT/backend/src/shared/agent_observability -type f -name "*.py" | sort

backend/src/shared/agent_observability/__init__.py
backend/src/shared/agent_observability/application/__init__.py
backend/src/shared/agent_observability/application/cost_alert_service.py
backend/src/shared/agent_observability/channels/__init__.py
backend/src/shared/agent_observability/channels/format.py
backend/src/shared/agent_observability/channels/format_for_channel.py
backend/src/shared/agent_observability/channels/intent_detector.py
backend/src/shared/agent_observability/cost/__init__.py
backend/src/shared/agent_observability/cost/calculator.py
backend/src/shared/agent_observability/cost/fx_resolver.py            ← extender .default()
backend/src/shared/agent_observability/persistence/...                ← repos base ya existen
backend/src/shared/agent_observability/pricing/aliases.py
backend/src/shared/agent_observability/pricing/litellm_sync.py
backend/src/shared/agent_observability/pricing/resolver.py
backend/src/shared/agent_observability/recording/__init__.py
backend/src/shared/agent_observability/recording/base_callback_handler.py  ← Template Method canónico
backend/src/shared/agent_observability/recording/sanitization.py
backend/src/shared/agent_observability/registry.py
backend/src/shared/agent_observability/reporting/billing_cycle_service.py
backend/src/shared/agent_observability/reporting/cost_aggregator.py
backend/src/shared/agent_observability/reporting/cycle_window.py
backend/src/shared/agent_observability/workers/aggregate_refresh_task.py
backend/src/shared/agent_observability/workers/cost_alert_task.py
backend/src/shared/agent_observability/workers/pricing_sync_task.py
backend/src/shared/agent_observability/workers/retention_task.py
```

**`shared/agent_observability/recording/turn_envelope.py` MISSING** — confirma este PR debe crearlo.

### 1.6 PI-5 PR-2 cross-session overlap check (Step 0.4)

```text
$ git status --short backend/src/modules/copilot/observability/
(empty — no working tree changes)

$ git log --oneline -5 -- backend/src/modules/copilot/observability/
0ea0f48e feat(copilot): suggestions-engine + provider pattern (PI-2 S1 PR-2)
64738354 refactor(copilot): switch emisores to outbox event bus adapter (flag OFF)
8cc9ea2c feat(sales-agent-redesign-s11a): lift 8 callbacks + Template Method skeleton al base
30ef49e7 feat(sales-agent-redesign-s11a): copilot retrofit + helpers delegation
a5dbf3ab feat(sales-agent-redesign-s2): cost guardrails cross-agent + costo-agentes admin

$ git show --stat d09799b9 -- backend/src/modules/copilot/observability/
(empty — PI-5 PR-2 main commit did NOT touch copilot/observability/)
```

**Veredicto**: PI-5 PR-2 (commits `d09799b9`, `a6c6ad3d` landed) modificó `modules/copilot/application/orchestrator/{chat.py, deep_agent.py, graph.py}` + `domain/context_window.py` + `infrastructure/repositories/conversation_repository.py` + `infrastructure/workers/telegram_worker.py` — **NO tocó `modules/copilot/observability/`**.

**Light overlap risk**: ambos PRs editan `copilot/application/orchestrator/chat.py`. Este PR sólo cambia 3 líneas (line 647-649: replace inline `FXResolver(http_client_factory=lambda: ...)` with `FXResolver.default()`) — append-only-style change que no rompe lógica PI-5 PR-2 introdujo. Aplicable parallel-safety M8: extend, no destroy. PI-5 PR-2 está `in-progress` pero commits ya en `development`.

### 1.7 Decisión EXTEND/LIFT/NEW per subsystem

| Subsystem | Existing canonical? | Decisión | Justificación |
|---|---|---|---|
| **Turn envelope lifecycle** | NO en `shared/`. Copilot tiene concrete monolithic `ObservabilityContext` (`copilot/observability/recording/turn_envelope.py:78`). | **LIFT-TO-SHARED + EXTEND** | Anti-duplication inventory promete shared base. Copilot's existing logic (lifecycle + sanitization + aggregation + commit + best-effort guards + `_TurnSummary` + `_TurnErrorFlag` + `_legacy_compat_keys`) se levanta a abstract base; copilot becomes subclass. Sales_agent crea NEW subclass para emit `turn_start` + `turn_end` (bug #2 fix). |
| **FX resolver factory** | `shared/agent_observability/cost/fx_resolver.py::FXResolver` exists (line 38), requires `http_client_factory: Callable[[], _HttpClientLike]` (line 47). NO `default()` classmethod. | **EXTEND existing class** — add `@classmethod def default(cls) -> FXResolver` | Encapsula `lambda: httpx.Client(timeout=10)` boilerplate (4 LOC) que duplica 1 vez ya (copilot/chat.py:648) y 1 vez incorrectamente (sales_agent/factory.py:78 → no-arg crash). Tests pueden seguir usando `FXResolver(http_client_factory=mock)` directo (ya hacen — `test_fx_resolver.py:29,44,66,82,97`). |
| **Concrete copilot context** | `copilot/observability/recording/turn_envelope.py::ObservabilityContext` (lines 77-372). | **REFACTOR in place to subclass** of `BaseObservabilityContext`. Module file path **does NOT change** — `__init__.py` re-export at line 43 preserved. External imports (chat.py:74 `from src.modules.copilot.observability import ObservabilityContext`) unchanged. | Change is internal: rename to `CopilotObservabilityContext`, add public alias `ObservabilityContext = CopilotObservabilityContext` for back-compat, inherit lifecycle from base, override agent-specific fields (`conversation_id`, `user_id`) + agent-specific aggregation (`CopilotLlmCallModel`-targeted SQL) + `_legacy_compat_keys` (copilot-only — sales_agent doesn't have legacy JSONB consumers). |
| **Concrete sales_agent context** | NO existe (post-revert). | **NEW subclass** of `BaseObservabilityContext` at `modules/sales_agent/observability/recording/turn_envelope.py::SalesAgentObservabilityContext` | Adds `lead_id: UUID` + `channel_type: str` fields. Aggregation hits `SalesAgentLlmCallModel`. NO `_legacy_compat_keys` (no legacy JSONB consumer en sales_agent — observability rebuild went straight to columnar). Filename `turn_envelope.py` matches copilot convention; class name distinct (anti-mirror — different concrete subclass, NOT byte-identical mirror file). |
| **Sales agent factory currency resolution + handler wiring** | `sales_agent/observability/recording/factory.py` exists (105 LOC). Currently constructs `SalesAgentCallbackHandler` only — does NOT construct an envelope. | **EXTEND** — add new factory `build_sales_agent_observability_context()` returning `SalesAgentObservabilityContext` (envelope + bound handler). Existing `build_sales_agent_callback_handler()` stays (back-compat); new builder calls existing one internally. Fix `FXResolver()` line 78 → `FXResolver.default()`. | Single source for handler/envelope construction. Currency resolution + repo wiring stays where it is — DRY preserved. |

**Decisión final: 1 LIFT + 1 EXTEND-method + 1 REFACTOR-in-place + 1 NEW-subclass + 1 EXTEND-factory.** Zero new shared layers. Zero parallel hierarchies.

---

## § 2 — `BaseObservabilityContext` interface (abstract base)

**Path**: `backend/src/shared/agent_observability/recording/turn_envelope.py` (NEW FILE)

**Class**: `BaseObservabilityContext` — abstract base class. ABC, dataclass.

**Lifecycle contract (preserved from copilot's existing class verbatim — DO NOT redesign)**:

- `@classmethod start(cls, *, tenant_id, turn_id=None, ..., agent_specific_kwargs)` — concrete subclass overrides to build its callback handler + repos, then calls `super().__init__(...)`.
- `langchain_config() -> dict` — returns `{"callbacks": [self.callback_handler]}`. Concrete in base.
- `set_turn_summary(*, response_length, message_count, block_count) -> None` — concrete in base.
- `set_turn_error(*, error_kind, error_message=None) -> None` — concrete in base.
- `@asynccontextmanager async def observe_turn(self, *, message, route, attachments=None)` — concrete in base. Calls `_write_turn_start` on enter, `_write_turn_end` on `finally` (so `asyncio.CancelledError` from FE drop still lands `turn_end`). All errors caught + logged via `logger.warning("obs_turn_*_failed")` — best-effort.
- `_write_turn_start(...) -> None` — concrete in base. Calls `self._add_trace_event(event_type='turn_start', ...)` + `self._commit_session()`.
- `_write_turn_end(...) -> None` — concrete in base. Calls abstract `_aggregate_totals()` + abstract `_legacy_compat_keys_or_empty()` + `self._add_trace_event(event_type='turn_end', ...)` + `self._commit_session()`.
- `_commit_session() -> None` — concrete in base. Reads `getattr(self.trace_repo, 'db', None)` + `with contextlib.suppress(Exception): session.commit()`. Best-effort.

**Abstract methods (subclasses MUST implement)**:

```python
@abstractmethod
def _add_trace_event(
    self,
    *,
    event_type: str,
    name: str,
    data: dict[str, Any],
    duration_ms: int | None = None,
    status: str = "ok",
    span_id: UUID | None = None,
) -> None:
    """Persist one row to the agent-specific trace event table.

    Concrete impls call ``self.trace_repo.add(tenant_id=..., turn_id=...,
    span_id=..., event_type=..., name=..., data=..., duration_ms=...,
    status=..., **agent_specific_kwargs)`` where ``agent_specific_kwargs``
    is e.g. ``conversation_id=..., user_id=...`` (copilot) or
    ``lead_id=..., channel_type=...`` (sales_agent).

    Best-effort: wrap in ``try/except`` + ``logger.warning``.
    """

@abstractmethod
def _aggregate_totals(self) -> dict[str, Any]:
    """Sum the agent-specific ``*_llm_call`` rows for this turn.

    Returns dict with keys ``llm_call_count``, ``total_input_tokens``,
    ``total_output_tokens``, ``total_cached_read_tokens``,
    ``total_cost_usd`` (str), ``model_responded`` (str). Used by base
    ``_write_turn_end`` to populate the ``turn_end.data`` JSONB.

    Best-effort: return ``_empty_totals()`` on failure.
    """

@abstractmethod
def _legacy_compat_keys_or_empty(self, totals: dict[str, Any]) -> dict[str, Any]:
    """Return legacy JSONB keys for back-compat consumers.

    Copilot impl: returns full ``_legacy_compat_keys`` dict (model,
    prompt_tokens, completion_tokens, cache_hit_rate, response_length,
    ...). Required because Streamlit ``/trazas`` + ``/copilot-routing``
    still read JSONB.

    Sales_agent impl: returns ``{}`` empty dict — no legacy consumers.
    """
```

**Shared composition fields (instantiated by base via `__init__` / `start`)**:

```python
tenant_id: UUID
turn_id: UUID
callback_handler: BaseAgentCallbackHandler  # concrete handler injected by subclass
trace_repo: Any                              # protocol — has .db + .add(...)
llm_call_repo: Any                           # protocol — has .db
_summary: _TurnSummary                       # field(default_factory=...)
_turn_start_monotonic: float                 # field(default_factory=time.monotonic)
_error_flag: _TurnErrorFlag | None = None
```

**Concrete fields per subclass (defined in subclass, set via `start` kwargs)**:

- Copilot: `conversation_id: UUID | None`, `user_id: UUID | None`
- Sales_agent: `lead_id: UUID`, `channel_type: str`

**`_TurnSummary` + `_TurnErrorFlag` + `_empty_totals()` helpers**: lifted from copilot file verbatim. Same module.

**Anti-duplication invariant (enforced by arch test §5.4)**: subclasses MUST NOT redefine `observe_turn`, `_write_turn_start`, `_write_turn_end`, `set_turn_summary`, `set_turn_error`, `langchain_config`, `_commit_session`. Override only abstract methods + agent-specific concrete fields. AST scan via arch test fails if subclass defines any of the locked-base method names.

---

## § 3 — `FXResolver.default()` factory

**Path**: `backend/src/shared/agent_observability/cost/fx_resolver.py` (EXTEND existing class — add classmethod ~5 LOC)

```python
@classmethod
def default(cls) -> FXResolver:
    """Production default: httpx client with 10s timeout per fetch.

    Encapsulates the ``lambda: httpx.Client(timeout=10)`` boilerplate
    duplicated across orchestrators. Tests bypass this and instantiate
    via ``FXResolver(http_client_factory=mock)`` directly.

    Per ``tessl__graceful-degradation`` Rule 1: explicit timeout on every
    external call. ``_fetch`` already swallows exceptions and returns
    ``None`` → ``resolve()`` falls back to ``Decimal(1), "fx_unavailable"``.
    """
    import httpx  # local import — ``httpx`` only needed in this prod path
    return cls(http_client_factory=lambda: httpx.Client(timeout=10))
```

**Why `default()` not `production()` or `build()`**: matches Python idiom (e.g. `dict.fromkeys`, factory classmethods named `default` in stdlib `email.policy`). Single canonical entry point — readable.

**Why local import**: keeps `fx_resolver.py` import time clean for tests that don't exercise the prod factory (most tests inject mock).

**Anti-duplication invariant (arch test §5.5)**: grep test bans `FXResolver()` (no-arg) and `FXResolver(http_client_factory=lambda: httpx.Client(timeout=10))` literal across `backend/src/`. Only `FXResolver.default()` (production), `FXResolver(http_client_factory=...)` non-lambda (tests with explicit mock), and the class definition itself permitted.

---

## § 4 — Migration plan (sequenced, atomic per step)

Each step is a logical unit. Builder commits per step OR groups commits 1-3 (lift+extend) and 4-7 (concrete subclasses + integration) — at most **2 commits**. Tests RED before each impl.

**Step 1 — Lift `BaseObservabilityContext` to shared (TDD RED first)**
- 1a. Write `tests/shared/agent_observability/recording/test_turn_envelope_base.py` (§5.1) — assertions fail (file doesn't exist yet).
- 1b. Create `backend/src/shared/agent_observability/recording/turn_envelope.py` per § 2 spec. Lift verbatim from copilot's existing file (lines 54-372 except aggregation SQL + `_legacy_compat_keys` → become abstract). Preserve: imports `sanitize_payload`/`truncate`, `_TurnSummary`, `_TurnErrorFlag`, `_empty_totals`, `_commit_session`.
- 1c. Tests GREEN.

**Step 2 — Add `FXResolver.default()` (TDD)**
- 2a. Write `tests/shared/agent_observability/cost/test_fx_resolver_default.py` (§5.5).
- 2b. Add 5-LOC classmethod per § 3.
- 2c. Tests GREEN.

**Step 3 — Refactor copilot concrete subclass in place (regression test FIRST)**
- 3a. Write `tests/modules/copilot/observability/test_envelope_inheritance.py` (§5.2) — lifecycle parity with current behavior. Run against current monolithic class — must PASS (baseline).
- 3b. Refactor `modules/copilot/observability/recording/turn_envelope.py`:
  - Add `class CopilotObservabilityContext(BaseObservabilityContext)` with `conversation_id`, `user_id` fields.
  - Override `_add_trace_event` → calls `self.trace_repo.add(..., conversation_id=self.conversation_id, user_id=self.user_id)`.
  - Override `_aggregate_totals` → SQL targeting `CopilotLlmCallModel` (lift verbatim from current `_aggregate_totals` body lines 286-322).
  - Override `_legacy_compat_keys_or_empty` → returns dict per current `_legacy_compat_keys` body lines 345-372.
  - Add module-level alias: `ObservabilityContext = CopilotObservabilityContext` (back-compat for `from src.modules.copilot.observability import ObservabilityContext`).
- 3c. Step 3a tests GREEN against refactored class. No FE change. No DB change.

**Step 4 — Migrate copilot orchestrator to use `FXResolver.default()` (3 LOC)**
- 4a. `modules/copilot/application/orchestrator/chat.py` line 647-649:

  Before:
  ```python
  fx_resolver=FXResolver(
      http_client_factory=lambda: httpx.Client(timeout=10),
  ),
  ```
  After:
  ```python
  fx_resolver=FXResolver.default(),
  ```

  Plus drop the now-unused `import httpx` at line 614 (verify no other use in `_build_observability_context`; `httpx` only appears once).
- 4b. Existing `tests/modules/copilot/observability/test_turn_envelope.py` + `test_fx_resolver.py` continue passing. No new test needed — covered by §5.5 anti-regression grep.

**Step 5 — Create sales_agent concrete subclass (TDD)**
- 5a. Write `tests/modules/sales_agent/observability/test_observability_context.py` (§5.3) — lifecycle, persistence, aggregation against `SalesAgentLlmCallModel`.
- 5b. Create `modules/sales_agent/observability/recording/turn_envelope.py`:
  - `class SalesAgentObservabilityContext(BaseObservabilityContext)` with `lead_id: UUID`, `channel_type: str` fields.
  - Override `_add_trace_event` → calls `self.trace_repo.add(..., lead_id=self.lead_id, channel_type=self.channel_type)`.
  - Override `_aggregate_totals` → SQL targeting `SalesAgentLlmCallModel`. Same shape as copilot but different model.
  - Override `_legacy_compat_keys_or_empty(totals)` → returns `{}` (no legacy consumers).
- 5c. Tests GREEN.

**Step 6 — Migrate sales_agent factory + orchestrators (Bug #8 + bug #2 fix integrated)**
- 6a. `modules/sales_agent/observability/recording/factory.py`:
  - Line 78: `FXResolver()` → `FXResolver.default()`. (Bug #8 single-callsite fix — corrects PR.md "116, 168" claim.)
  - Add new factory `build_sales_agent_observability_context(*, db, tenant_id, lead_id, channel_type, turn_id, role='agent') -> SalesAgentObservabilityContext | None`. Wraps existing `build_sales_agent_callback_handler` + builds repos + bills currency + returns envelope. Returns `None` on missing identity (best-effort).
- 6b. `modules/sales_agent/application/orchestrator/conversation_pipeline.py::invoke_agent_with_typing`:
  - Change signature: `observability_handler` → `observability_context: SalesAgentObservabilityContext | None`.
  - Wrap `await agent_app.ainvoke(...)`:
    ```python
    if observability_context is not None:
        async with observability_context.observe_turn(
            message=incoming.text or "",
            route="sales_agent",
            attachments=getattr(incoming, "attachments", []) or [],
        ):
            result = await agent_app.ainvoke(initial_state, config=observability_context.langchain_config())
    else:
        result = await agent_app.ainvoke(initial_state, config={})
    ```
  - Note: `set_turn_summary` post-graph is OPTIONAL for sales_agent (no legacy JSONB consumers) — defer to follow-up if metric needed. **NOT required for bug #2 fix.**
- 6c. `modules/sales_agent/application/orchestrator/chat.py` line 327-333: replace `build_sales_agent_callback_handler(...)` call with `build_sales_agent_observability_context(...)`. Pass to `invoke_agent_with_typing` as `observability_context=...`.
- 6d. `modules/sales_agent/application/orchestrator/outbound_orchestrator.py` line 226-233: identical migration. Replace `build_sales_agent_callback_handler` with `build_sales_agent_observability_context`. Replace `config = {"callbacks": [handler]} if handler is not None else {}` + `result = await agent_app.ainvoke(initial_state, config=config)` with `async with observability_context.observe_turn(...): result = await agent_app.ainvoke(...)` pattern.

**Step 7 — Real DB persistence smoke test (TDD)**
- 7a. Write `tests/modules/sales_agent/observability/test_real_trace_persistence.py` (§5.6). Marker `@pytest.mark.verify` (excluded from default fast suite, runs in `/test-all`).
- 7b. Test asserts ≥3 rows post-mock-turn (turn_start + ≥1 llm_call from callback handler + turn_end).

**Step 8 — Anti-regression arch tests + ratchet**
- 8a. Add `tests/architecture/test_anti_duplication_envelope.py` (§5.4): scans cross-codebase for forbidden patterns (no-arg `FXResolver()`, mirror class names).
- 8b. Update existing `tests/architecture/test_sales_agent_observability_invariants.py` if needed: add invariant "`SalesAgentObservabilityContext` extends `BaseObservabilityContext`" + "no parallel observe_turn implementation in sales_agent".

**Step 9 — Manual Chris-mediated Telegram smoke**
- Builder reports "ready for smoke" → Chris sends message via Telegram bot to tenant `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` (visionarias) with lead `cb711aea-e0a5-42c0-b276-7a63570207bd` (Christian Revilla).
- Builder runs verification SQL:
  ```sql
  SELECT event_type, status, created_at FROM sales_agent_trace_event
  WHERE tenant_id = '6347e21e-8112-4aa1-80d3-6adaa73bf6f9'
    AND created_at > NOW() - INTERVAL '5 minutes'
  ORDER BY created_at;
  ```
  Expected: ≥3 rows (turn_start, ≥1 llm_call, turn_end). Status all `ok`. PASS = bug #2 closed.

**Why this order**: shared base FIRST (Step 1) so copilot regression in Step 3 only touches inheritance + lift body — no behavior change. Sales_agent NEW work (Steps 5-7) builds on validated base. Bug fixes (Step 6 line 78 + envelope wire) happen together — atomic from sales_agent's perspective. Tests precede each impl per `.claude/rules/tdd-mandatory.md`.

---

## § 5 — Tests strategy (TDD-mandatory, RED before GREEN per layer)

### 5.1 Base contract — `tests/shared/agent_observability/recording/test_turn_envelope_base.py` (NEW)

```python
class TestBaseObservabilityContext:
    def test_abstract_methods_enforced(self):
        # Cannot instantiate ABC directly
        with pytest.raises(TypeError):
            BaseObservabilityContext(...)

    def test_concrete_minimal_subclass_lifecycle(self):
        # Subclass implementing the 3 abstracts works end-to-end.
        # Mock trace_repo, mock llm_call_repo. Verify:
        # - observe_turn enter writes turn_start (single _add_trace_event call)
        # - observe_turn exit (clean) writes turn_end (status='ok')
        # - observe_turn exit (raise) writes turn_end (status='error') + re-raises
        # - asyncio.CancelledError still lands turn_end (BaseException finally)

    def test_set_turn_error_persists_status_error(self):
        # Body returns clean (orchestrator caught) but set_turn_error called
        # → turn_end row status='error', data['error_kind'] populated.

    def test_best_effort_writes_swallow_exceptions(self):
        # trace_repo.add raises → logger.warning called, observe_turn body still proceeds
        # → no exception bubbles to caller.

    def test_locked_methods_not_overridable_compile_time(self):
        # AST inspection: subclass cannot define observe_turn / _write_turn_*
        # (validated via arch test §5.4 — kept here as smoke).
```

### 5.2 Copilot regression — `tests/modules/copilot/observability/test_envelope_inheritance.py` (NEW)

```python
class TestCopilotEnvelopeInheritance:
    def test_copilot_context_extends_base(self):
        assert issubclass(CopilotObservabilityContext, BaseObservabilityContext)

    def test_observability_context_alias_back_compat(self):
        # ``from src.modules.copilot.observability import ObservabilityContext`` still works
        from src.modules.copilot.observability import ObservabilityContext
        assert ObservabilityContext is CopilotObservabilityContext

    def test_lifecycle_parity_with_pre_refactor(self):
        # Same trace_event rows as before refactor (turn_start + turn_end shape).
        # Use a recorded snapshot from current behavior.

    def test_legacy_compat_keys_present(self):
        # turn_end.data still has model/prompt_tokens/completion_tokens/...
        # (Streamlit /trazas + /copilot-routing depend on this.)

    def test_aggregate_totals_targets_copilot_llm_call_model(self):
        # SQL inspection: SELECT FROM copilot_llm_call WHERE turn_id=... AND tenant_id=...
```

### 5.3 Sales agent context — `tests/modules/sales_agent/observability/test_observability_context.py` (NEW)

```python
class TestSalesAgentObservabilityContext:
    def test_extends_base(self):
        assert issubclass(SalesAgentObservabilityContext, BaseObservabilityContext)

    def test_persists_turn_start_with_lead_id_and_channel_type(self):
        # _add_trace_event injects lead_id=, channel_type= into trace_repo.add
        # call kwargs.

    def test_aggregate_totals_targets_sales_agent_llm_call_model(self):
        # SQL inspection.

    def test_legacy_compat_keys_returns_empty(self):
        # Sales_agent has no legacy JSONB consumers.

    def test_factory_build_observability_context_returns_none_on_missing_identity(self):
        # tenant_id=None or lead_id=None → None (best-effort).

    def test_factory_uses_fx_resolver_default(self):
        # No FXResolver() no-arg construction. Patch FXResolver.default
        # and verify called.
```

### 5.4 Architecture ratchet — `tests/architecture/test_anti_duplication_envelope.py` (NEW)

Anti-duplication enforcement (corresponds to `.claude/rules/anti-duplication.md` Layer 3 — auditor Cat 12 mirror detection):

```python
def test_no_parallel_turn_envelope_files_outside_canonical():
    """Only canonical paths may define turn envelope."""
    canonical = {
        REPO / "src/shared/agent_observability/recording/turn_envelope.py",
        REPO / "src/modules/copilot/observability/recording/turn_envelope.py",
        REPO / "src/modules/sales_agent/observability/recording/turn_envelope.py",
    }
    found = set(REPO.rglob("**/turn_envelope.py"))
    found = {p for p in found if "site-packages" not in str(p) and "__pycache__" not in str(p)}
    assert found == canonical

def test_no_class_observability_context_outside_subclasses():
    """ObservabilityContext alias only at copilot module __init__ + canonical files."""
    # AST scan all *.py — `class .*ObservabilityContext` only in canonical files.

def test_subclass_does_not_override_locked_lifecycle_methods():
    """Subclasses MUST NOT redefine observe_turn / _write_turn_* / set_turn_*."""
    # AST inspection of CopilotObservabilityContext + SalesAgentObservabilityContext.

def test_no_no_arg_fxresolver_calls():
    """Forbid FXResolver() in src/. Only .default() or explicit http_client_factory= kwarg."""
    # Scan src/ for `FXResolver()` literal (anchor by `(`+`)` adjacency, not just symbol).

def test_no_inline_httpx_client_factory_lambda():
    """Forbid the encapsulated pattern in src/ outside FXResolver itself."""
    # grep `lambda: httpx.Client(timeout=` → must be 0 hits in src/ outside default().
```

### 5.5 FX factory — `tests/shared/agent_observability/cost/test_fx_resolver_default.py` (NEW)

```python
class TestFXResolverDefault:
    def test_default_returns_fxresolver_instance(self):
        resolver = FXResolver.default()
        assert isinstance(resolver, FXResolver)

    def test_default_uses_httpx_client_with_timeout(self):
        # Capture http_client_factory call → assert returns httpx.Client with timeout
        resolver = FXResolver.default()
        client = resolver.http_client_factory()
        # Smoke: client has .get callable + closes cleanly.
        # Don't assert on internals (timeout); httpx version-agnostic.

    def test_default_passthrough_for_usd(self):
        resolver = FXResolver.default()
        rate, source = resolver.resolve(currency_code="USD", at_ts=datetime.now(UTC))
        assert rate == Decimal(1)
        assert source == "passthrough"
```

### 5.6 Real DB persistence — `tests/modules/sales_agent/observability/test_real_trace_persistence.py` (NEW, marker `verify`)

```python
@pytest.mark.verify  # excluded from default fast suite; included in /test-all
class TestRealTracePersistence:
    """Real Postgres DB persistence — no mocks. Bug #2 regression guard."""

    @pytest.fixture
    def real_db_session(self, postgres_test_db):
        # Real AsyncSession or sync Session bound to test Postgres
        ...

    def test_observe_turn_inserts_turn_start_and_turn_end(self, real_db_session):
        # tenant_id = visionarias (or test tenant), lead_id = test lead
        # Build SalesAgentObservabilityContext via factory
        # async with ctx.observe_turn(message="hola", route="sales_agent"):
        #     pass  # no graph call — just lifecycle
        # Assert: SELECT count FROM sales_agent_trace_event WHERE turn_id=... → 2
        # Rows have event_type='turn_start' and 'turn_end', status='ok'.

    def test_observe_turn_with_callback_handler_persists_llm_call_row(self, real_db_session, mock_llm):
        # Run a real ainvoke against agent_app with a stub LLM that emits one
        # on_chat_model_start/on_llm_end pair.
        # Assert: ≥1 row in sales_agent_llm_call + 3 rows in sales_agent_trace_event
        # (turn_start + llm_call mirror + turn_end).
```

### 5.7 Existing tests — must keep GREEN

- `tests/modules/copilot/observability/test_turn_envelope.py` — exercises `ObservabilityContext` class. Refactor preserves public API via alias → all assertions hold.
- `tests/modules/copilot/observability/test_fx_resolver.py` — uses `FXResolver(http_client_factory=...)` directly → unaffected.
- `tests/architecture/test_sales_agent_observability_invariants.py` — append new invariant: `SalesAgentObservabilityContext` extends `BaseObservabilityContext`.
- `tests/architecture/test_shared_agent_observability_purity.py` — verify new file `shared/agent_observability/recording/turn_envelope.py` doesn't import from `modules/`. Likely already covered (purity test scans imports).

---

## § 6 — Coordination con PI-5 PR-2 active session

### Status check (Step 0.4 grep evidence)

- PI-5 PR-2 PR.md state: `in-progress` (header line 9).
- PI-5 PR-2 main commits: `d09799b9`, `a6c6ad3d` — landed in `development` 2026-05-01.
- PI-5 PR-2 modified: `modules/copilot/{api/dto.py, application/{memory,orchestrator}/{...}, domain/context_window.py, infrastructure/{repositories,workers}/...}`. Summary: 27 files +3083/-96.
- **`modules/copilot/observability/` UNTOUCHED** by PI-5 PR-2 commits (`git show --stat` empty for that path).

### Overlap surface

Single shared file: `modules/copilot/application/orchestrator/chat.py`. PI-5 PR-2 added 251 lines around channel-aware logic (lines 600+ rewrite of `_apply_channel_window`, `invoke_text`, etc). **This PR touches lines 622-650 only** — replace inline `FXResolver(http_client_factory=lambda: ...)` (3 lines) with `FXResolver.default()` (1 line) and drop unused `import httpx` (1 line).

### Coordination plan

**Path A — PI-5 PR-2 ships first (preferred)**:
- If PM signals PI-5 PR-2 audit PASS + RESULT.md before this PR builder spawns → no coordination needed. This PR's chat.py edit is 3-4 LOC append-style change, won't conflict.

**Path B — PI-5 PR-2 still active when this PR builder runs (current state)**:
- Apply parallel-safety M8: extend, no destroy. Builder reads chat.py current state, modifies only `_build_observability_context` body lines 622-650. Builder MUST NOT touch any other section of chat.py.
- If builder finds local edit conflict (PI-5 PR-2 mid-flight reshapes `_build_observability_context` itself) → STOP, report PM. PM decides: (a) wait for PI-5 PR-2 to land, then resume; or (b) proceed if conflict trivial.
- Pre-commit check: `git diff backend/src/modules/copilot/application/orchestrator/chat.py` should show ONLY 4-5 lines diff. If wider → builder error or conflict.

**Path C — overlap escalation**: 
- If during execution PI-5 PR-2 spawns auditor that requests changes to `_build_observability_context`, this PR's builder pauses + escalates. PM coordinates lock-step: PI-5 PR-2 auditor changes land → this PR rebases mentally + applies its 4-line edit on top.

### Recommendation

**Proceed Path B** — overlap is trivial (4-5 lines, append-style, far from PI-5 PR-2's mutation surface). Builder must verify single-region diff pre-commit. Risk: low.

---

## § 7 — Out of scope

- **Bug #7** `PersonalityProfileModel.model_dump` type mismatch in `brand/application/services/brand_data_adapter.py:46` — separate PR backend negocio module.
- **Bug #9** LiteLLM container exited / config.yaml mount conflict — separate PR infra.
- **Bug #6** tenant switch non-persist Clerk publicMetadata — separate PR FE Clerk session.
- **Bug #5** FE max update depth — out of scope until reproduced.
- **Backfill traces históricos sales_agent** (pre-PR-2 turns) — defer post-PR-2 ship + Chris discussion.
- **Channel registry, PII regex, cost calculator, pricing aliases** — already in shared, NOT touched by this PR.
- **`redirect_slashes` invariant** — refactor doesn't add API routes. App-level config unchanged.
- **`response_model=` invariant** — no new endpoints. N/A.
- **Sales agent voice** — refactor invisible al output. `personality_profiles.system_instruction` SSoT untouched.
- **Subagent isolation, plan_card, mutation journal, channel format dispatch** — all preserved as-is.
- **`set_turn_summary` per-turn metric for sales_agent** — defer to follow-up. `turn_end` row will have `_summary` defaulted to zeros; no consumer breaks.
- **Migration alembic** — no DB schema change. `sales_agent_trace_event` table already exists (created in S0/S1 of sales-agent-redesign-2026-04). `copilot_trace_event` unchanged.

---

## § 8 — Acceptance criteria (builder pre-commit + auditor pre-PASS checklist)

Builder verifies all before requesting auditor spawn. Auditor verifies all to issue PASS.

- [ ] **Step 1**: `backend/src/shared/agent_observability/recording/turn_envelope.py` exists, contains `BaseObservabilityContext` ABC with abstract methods `_add_trace_event`, `_aggregate_totals`, `_legacy_compat_keys_or_empty`. Imports `sanitize_payload` from sibling `sanitization.py`. No imports from `modules/`.
- [ ] **Step 2**: `FXResolver.default()` classmethod exists in `shared/agent_observability/cost/fx_resolver.py`. Local `import httpx` inside method.
- [ ] **Step 3**: `modules/copilot/observability/recording/turn_envelope.py::CopilotObservabilityContext` extends `BaseObservabilityContext`. Module-level alias `ObservabilityContext = CopilotObservabilityContext` preserved. `from src.modules.copilot.observability import ObservabilityContext` still works (test §5.2).
- [ ] **Step 4**: `modules/copilot/application/orchestrator/chat.py::_build_observability_context` calls `FXResolver.default()`. `import httpx` removed if unused. Diff ≤5 lines.
- [ ] **Step 5**: `modules/sales_agent/observability/recording/turn_envelope.py::SalesAgentObservabilityContext` exists. Class is NEW (not copy of copilot — verify via diff: ≤80 LOC, only overrides 3 abstract methods + declares 2 fields). `_legacy_compat_keys_or_empty` returns `{}`.
- [ ] **Step 6 — Bug #8 fix**: `factory.py:78` reads `FXResolver.default()` not `FXResolver()`. Single edit, 1 LOC. New factory `build_sales_agent_observability_context` exists.
- [ ] **Step 6 — Bug #2 fix**: `conversation_pipeline.invoke_agent_with_typing` wraps `agent_app.ainvoke` in `async with observability_context.observe_turn(...)`. `chat.py` + `outbound_orchestrator.py` callers updated to pass `observability_context=`.
- [ ] **Step 7 — Real DB test**: `tests/modules/sales_agent/observability/test_real_trace_persistence.py` exists with `@pytest.mark.verify` marker. Asserts ≥2 rows (turn_start + turn_end) post `observe_turn` exit; ≥3 rows when one mock LLM call fires.
- [ ] **Step 8 — Arch ratchet**: `tests/architecture/test_anti_duplication_envelope.py` exists with 5 invariants (§5.4). Updated `test_sales_agent_observability_invariants.py` includes new envelope inheritance check.
- [ ] **Step 9 — Smoke**: Chris-mediated Telegram message → SQL count `≥3 rows in sales_agent_trace_event WHERE tenant_id='6347e21e-8112-4aa1-80d3-6adaa73bf6f9' AND created_at > NOW() - INTERVAL '5 minutes'`. Builder appends SQL output to IMPL-LOG-agentic.md.
- [ ] **Quality gates green** (native execution per CLAUDE.md):
  - `cd backend && .venv/bin/ruff check` — 0 errors
  - `cd backend && .venv/bin/ruff format --check` — clean
  - `cd backend && .venv/bin/pytest tests/shared/agent_observability/ tests/modules/copilot/observability/ tests/modules/sales_agent/observability/ tests/architecture/test_*observability*.py tests/architecture/test_anti_duplication_envelope.py tests/architecture/test_ddd_boundaries.py -q` — all green
  - `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short` — full arch suite green, allowlists shrink only
- [ ] **Tenant isolation**: every new query in `_aggregate_totals` (copilot + sales_agent subclass) filters `Model.tenant_id == self.tenant_id`. `get_by_id`-style methods include tenant_id.
- [ ] **Best-effort writes**: every `_add_trace_event` impl wraps `try/except` + `logger.warning`. Verified by grep scan in arch test.
- [ ] **PII sanitization**: every `data=` arg passed to `_add_trace_event` runs through `sanitize_payload(...)`. Already encoded in base `_write_turn_start` / `_write_turn_end`.
- [ ] **Anti-duplication grep evidence in IMPL-LOG**: builder pastes `find ... -name turn_envelope.py` output post-commit. Auditor verifies output matches canonical 3-file set.
- [ ] **No FXResolver() no-arg** anywhere in `backend/src/` post-PR (verified by §5.4 arch test).
- [ ] **PI-5 PR-2 coordination note** in IMPL-LOG-agentic.md: builder pasted git diff stat showing chat.py edit is 4-5 lines + confirms no overlap with PI-5 PR-2 surface.
- [ ] **pm-nico/current-state updates** committed with code: `current-state/sales_agent.md` appends "Observability traces persistence — live, lineage PR-2 PI-1.1"; `current-state/copilot.md` appends "Observability lifecycle refactored to shared base — capability unchanged".
- [ ] **Spanish neutro**: docstrings + log messages in Spanish neutro (no voseo). Sales_agent agent output untouched.
- [ ] **No cross-module imports** introduced (DDD boundary: shared base imports nothing from modules/; copilot subclass + sales_agent subclass each import only their own module + shared).

---

## § 9 — Risks

| Riesgo | P × I | Mitigación |
|---|---|---|
| **Cross-session collision PI-5 PR-2** edita `chat.py` mismo bloque `_build_observability_context` | Low × High | Pre-commit `git diff` muestra ≤5 LOC. Builder STOP + escalate si diff cruza función. PR.md says proceed Path B. |
| **Refactor copilot rompe 4260 traces existing** (regression `_legacy_compat_keys`) | Low × Critical | Test §5.2 includes snapshot lifecycle parity. `ObservabilityContext` alias preserves import. `_legacy_compat_keys_or_empty` impl in copilot subclass returns full dict (not stub). |
| **Real DB test flaky in CI** | Med × Low | `@pytest.mark.verify` marker excludes from default fast suite; included in `/test-all`. Required for ship — manual run pre-merge if CI skips. |
| **Bug #8 single-callsite assumption wrong** (other `FXResolver()` no-arg buried somewhere) | Low × Med | Arch test §5.4 grep scans entire `backend/src/`. Test fails if any new no-arg call appears. |
| **`async with observe_turn` swallows exception orchestrator wanted to handle** | Med × Med | Base `observe_turn` re-raises in `except BaseException` block (preserved verbatim from copilot). Orchestrator's outer try/except at `chat.py:369-379` (sales_agent) still catches + sends fallback msg + logs. |
| **`SalesAgentObservabilityContext` without `_legacy_compat_keys` breaks future Streamlit consumer** | Low × Low | Sales agent observability went straight to columnar (`sales_agent_llm_call`); no JSONB consumer documented. If a consumer emerges, override `_legacy_compat_keys_or_empty` then. |
| **`turn_id` propagation**: callback handler turn_id MUST match envelope turn_id for aggregation SQL to find rows | Med × High | Factory `build_sales_agent_observability_context` builds handler + envelope sharing same `turn_id`. Test §5.3 asserts handler.turn_id == ctx.turn_id. |
| **`session.commit()` after `turn_end` flushes uncommitted data from earlier orchestrator code** | Low × Med | Already current copilot behavior. `_commit_session` uses `contextlib.suppress(Exception)`. Sales_agent already does explicit `db.commit()` in checkpoint save (line 503). Net: no new commit semantics. |
| **`asyncio.CancelledError` from FE drop** (Telegram client times out) doesn't land turn_end | Low × Med | Base `observe_turn` uses `try / except BaseException as exc / finally:` — finally branch runs even on `CancelledError`. Verified test §5.1. |
| **Architect Opus paused mid-CONTRACT (cap caché)** | Low × Med | This CONTRACT is single-file output, ~95% complete in this turn. Re-spawn fresh resumes from disk. |
| **Builder agentic Step 0 grep gate falla detectar** new mirror | Very low × Critical | Triple-layer: (1) builder Step 0 mandatory grep gate per `prompts/02-builder-agentic.md`; (2) auditor Cat 12 mirror detection; (3) arch test §5.4. Three independent enforcement layers. |
| **Tier pricing >200k tokens (Kimi K2.6, S12 cementado) ignored by `_aggregate_totals`** | Low × Low | Aggregation reads `cost_usd` already computed by callback handler; pricing tier already applied per `sales-agent-expert §3` `cost_calculator` cementado. No duplicate pricing logic in envelope. |

---

## § 10 — File structure summary

| Status | Path | LOC est. | Owner |
|---|---|---|---|
| NEW | `backend/src/shared/agent_observability/recording/turn_envelope.py` | 250 (lift from copilot, abstract 3 methods) | nicolify-agentic |
| MOD | `backend/src/shared/agent_observability/cost/fx_resolver.py` | +5 (`default()` classmethod) | nicolify-agentic |
| REFACTOR | `backend/src/modules/copilot/observability/recording/turn_envelope.py` | -200 +80 (becomes thin subclass + alias) | nicolify-agentic |
| MOD | `backend/src/modules/copilot/application/orchestrator/chat.py` | +1 -4 (FXResolver.default + drop httpx import) | nicolify-agentic |
| NEW | `backend/src/modules/sales_agent/observability/recording/turn_envelope.py` | 80 (concrete subclass) | nicolify-agentic |
| MOD | `backend/src/modules/sales_agent/observability/recording/factory.py` | +25 -1 (new builder + Bug #8 line 78) | nicolify-agentic |
| MOD | `backend/src/modules/sales_agent/application/orchestrator/conversation_pipeline.py::invoke_agent_with_typing` | +8 -2 (envelope wrap) | nicolify-agentic |
| MOD | `backend/src/modules/sales_agent/application/orchestrator/chat.py` | +3 -3 (factory swap) | nicolify-agentic |
| MOD | `backend/src/modules/sales_agent/application/orchestrator/outbound_orchestrator.py` | +6 -3 (factory + envelope wrap) | nicolify-agentic |
| NEW | `backend/tests/shared/agent_observability/recording/test_turn_envelope_base.py` | 200 | nicolify-agentic |
| NEW | `backend/tests/shared/agent_observability/cost/test_fx_resolver_default.py` | 60 | nicolify-agentic |
| NEW | `backend/tests/modules/copilot/observability/test_envelope_inheritance.py` | 120 | nicolify-agentic |
| NEW | `backend/tests/modules/sales_agent/observability/test_observability_context.py` | 200 | nicolify-agentic |
| NEW | `backend/tests/modules/sales_agent/observability/test_real_trace_persistence.py` | 150 | nicolify-agentic |
| NEW | `backend/tests/architecture/test_anti_duplication_envelope.py` | 120 | nicolify-agentic |
| MOD | `backend/tests/architecture/test_sales_agent_observability_invariants.py` | +20 (new invariant) | nicolify-agentic |
| MOD | `docs/pm-nico/current-state/sales_agent.md` | +5 (capability append) | `/pm` |
| MOD | `docs/pm-nico/current-state/copilot.md` | +3 (lineage note) | `/pm` |

**Total**: ~1500 LOC (impl + tests + docs). Builder estimated turns: 50-70 (Opus, with TDD per step).

---

## § 11 — Research notes

No novel external patterns introduced. Observability lift uses Template Method (GoF) — same pattern already canonical for `BaseAgentCallbackHandler` (lifted in S0 of sales-agent-redesign-2026-04). FX factory `default()` classmethod is Python idiomatic.

**Anchors**:
- Anthropic prompt caching: not touched by this PR (callback handler unchanged).
- LangGraph callback propagation via `RunnableConfig(callbacks=[...])`: existing pattern (sales_agent's `sales_agent_node` already declares `config: RunnableConfig` per arch test `test_sales_agent_observability_invariants.py::TestSubgraphCallbackForwarding`). Confirmed via canonical docs accessed 2026-05-01: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (LangGraph 2.0 — handlers propagate through subgraph nodes when `config` declared in node signature).
- `tessl__graceful-degradation` Rule 1: timeout explicit at `httpx.Client(timeout=10)`. Rule 2: fallback `(Decimal(1), "fx_unavailable")` already implemented in `FXResolver._fetch` (line 90 `except Exception` swallows + returns `None` → `resolve()` line 73 returns fallback).

**Knowledge cutoff disclosure**: Opus 4.7 cutoff Jan 2026; pattern decisions (Template Method lift, classmethod factory) are stable Python idioms unaffected by cutoff. No post-cutoff library API used.

---

## § 12 — Open questions for PM

None blocking. Decisions taken:

1. **Filename `turn_envelope.py` for sales_agent vs `context.py`?** → Decided `turn_envelope.py` (matches copilot convention; the file name matches ROLE not class name; class name `SalesAgentObservabilityContext` distinguishes; arch test §5.4 enforces canonical 3-file set). PR.md mentioned `context.py` — overruled because callback handler subsystem already uses `callback_handler.py` (not `handler.py`) per agent — same convention applies here. NOT a mirror because each file has its own concrete subclass with different class name + different fields.

2. **Should sales_agent envelope call `set_turn_summary` post-graph?** → Deferred. No legacy JSONB consumer for sales_agent. `_summary` will be all zeros in `turn_end.data`. Future sprint can add stream-shape tracking if a Streamlit page demands it. Not blocking bug #2 fix.

3. **Real DB persistence test marker?** → `@pytest.mark.verify`. Already exists per backend `pyproject.toml` markers (per CLAUDE.md "Pytest asyncio auto, markers: integration, verify"). Confirms path B fits — included in `/test-all`, excluded from default fast suite.

4. **Should we backfill historical sales_agent traces (pre-PR-2 turns)?** → Out of scope per PR.md. Defer post-ship + Chris discussion. No data exists to backfill — bug #2 = zero rows.

---

<!-- @pm: architect done. CONTRACT.md ready. Próximo paso: ejecutar /pm "PR-2 architect done — spawn builder" o pegar prompts/02-builder-agentic.md -->
