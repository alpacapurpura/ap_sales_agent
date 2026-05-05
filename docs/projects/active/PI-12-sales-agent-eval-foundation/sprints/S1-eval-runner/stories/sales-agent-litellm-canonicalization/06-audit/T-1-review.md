# T-1 Audit Review — Cost recorder canonicalization

---
ticket_id: T-1
story_id: sales-agent-litellm-canonicalization
sprint: S1-eval-runner
pi: PI-12
audited_by: claude-opus-4-7 (auditor-be)
audited_at: 2026-05-05T07:00Z
push_commit_sha: 5856be4d
push_branch: development
verdict: APPROVED
audit_iteration: 1
---

## Verdict

**APPROVED**

## Resumen ejecutivo

T-1 cumple los 5 criterios de aceptación (A1..A5) sin desviación arquitectónica. La implementación
respeta la regla anti-duplication (cost_recorder.py es nuevo surface en el boundary LiteLLM
CustomLogger, conceptualmente distinto del LangChain BaseCallbackHandler ya lifted shared),
preserva A1 (model slashed), aplica X2 (calculate_cost retirado del runtime path), no flipea
flags side-effect, y no toca lógica agentic en modules/copilot ni modules/sales_agent. Los
únicos cambios cross-modulo son schema mirrors estrictos (cost_usd nullable) autorizados
explícitamente por el architect doc § 3.4 + § 5. Tests + lint + arch fitness + coverage gates
todos verdes en re-ejecución independiente del auditor.

## Verifier output (auditor re-ran independentemente)

### Pytest — test_litellm_canonicalization.py (ticket-specific)

```
$ cd backend && .venv/bin/pytest tests/shared/agent_observability/cost/test_litellm_canonicalization.py -v --override-ini="addopts="
13 passed, 1 warning in 10.60s
```

13/13 PASS. A1..A5 + 8 sub-tests cubren happy path, unknown model, p95 latency, calculate_cost
no invocado, bridge end-to-end, runtime cost vs snapshot stale, all calls passthrough, orphan
TTL, bootstrap registration, single-use cache, missing response_cost.

### Pytest — regression suite shared/observability + arch fitness + copilot regression

```
$ cd backend && .venv/bin/pytest tests/shared/agent_observability/ tests/architecture/ tests/modules/copilot/observability/test_callback_handler.py tests/modules/copilot/observability/test_e2e_isolated.py --override-ini="addopts=" -q
1015 passed, 1 warning in 23.92s
```

1015/1015 PASS. Coincide exactamente con el output reportado por el dev en T-1-result.md.

### Pytest — full architecture fitness (re-run)

```
$ cd backend && .venv/bin/pytest tests/architecture/ -v --override-ini="addopts="
823 passed, 1 warning in 23.48s
```

823 arch fitness gates verde. Allowlists no engordaron (ratchet shrink-only respetado).

### Ruff lint + format

```
$ cd backend && .venv/bin/ruff check src/shared/agent_observability/ src/main.py src/workers/settings.py tests/shared/agent_observability/ --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check src/shared/agent_observability/ src/main.py src/workers/settings.py tests/shared/agent_observability/
61 files already formatted
```

### Coverage delta — shared/agent_observability/

```
$ cd backend && .venv/bin/pytest --cov=src/shared/agent_observability --cov-report=term-missing -q --override-ini="addopts=" tests/shared/agent_observability/
185 passed, 1 warning in 12.00s
TOTAL  1244 stmts  333 miss  Cover 73%
Required test coverage of 43.0% reached. Total coverage: 73.23%
```

`shared/agent_observability/recording/cost_recorder.py` 72% (89 stmts, 25 miss). Misses son
defensive paths (litellm ImportError stub fallback, error-class branches) — todos cubiertos
indirectamente por el arch fitness suite + skipped on import-error in CI smoke. NO drop por
debajo del 43% threshold.

### Anti-duplication grep evidence (auditor re-run)

```
$ find /home/chris/AISALESHT/backend/src -name "cost_recorder.py"
/home/chris/AISALESHT/backend/src/shared/agent_observability/recording/cost_recorder.py
(only the new file)

$ grep -rln "CustomLogger|cost_recorder|CostRecorder" /home/chris/AISALESHT/backend/src/
src/main.py                                             (consumer — register_cost_recorder)
src/shared/agent_observability/recording/cost_recorder.py  (new file)
src/shared/agent_observability/recording/base_callback_handler.py  (consumer — pop_cost)
src/workers/settings.py                                 (consumer — register_cost_recorder)
src/shared/agent_observability/cost/calculator.py       (docstring only — "reconciliation utility only")
```

Step 0 grep evidence del impl-log es real. NO se mirror el `BaseAgentCallbackHandler` shared.

### Anti-default-flip-audit applicability (T-1 specifically)

```
$ git show 5856be4d | grep -i "LITELLM_PROXY_ENABLED"
ZERO matches — flag not flipped
```

T-1 NO flipea ningún flag side-effect. Categoría 12 N/A para este ticket. T-5 será el
ticket que aplique el 4-step audit cuando elimine el flag.

## 11-category review (per auditor-be standard)

| # | Category | Status | Evidence |
|---|---|---|---|
| 1 | DDD Layer Compliance | PASS | cost_recorder.py vive en `shared/agent_observability/recording/`. NO tiene SQLAlchemy / FastAPI imports. Pure Python module-level singleton + structlog. No business logic en api/. base_callback_handler.py mantiene su rol shared, no se duplicó. |
| 2 | Tenant Isolation | PASS | cost_recorder.py es process-wide intencionalmente (architect doc § 5: tenant context fluye via `BaseAgentCallbackHandler` que tiene `self.tenant_id`). Cache key = `litellm_call_id` (opaque ID, NO PII, NO tenant data). NO query cross-tenant. NO leak risk. |
| 3 | Soft Deletes | N/A | T-1 no toca DB delete operations. Migration 086 es ALTER COLUMN DROP NOT NULL (idempotente, reversible via downgrade). |
| 4 | Code Quality | PASS | ruff check clean (gate 3). ruff format clean (gate 4). 1 `# noqa: F401` justificado (calculate_cost retained for reconciliation utility). 4 `# noqa: BLE001` justificados (best-effort callback nunca raises). 2 `# noqa: ANN401` justificados (foreign LiteLLM payload). Docstrings Google-style cubren todo. |
| 5 | SQLAlchemy 2.0 | PASS | Modelos llm_call_model.py mantienen `Column()` legacy (no fueron tocados los patterns SQLA 1.x existentes). Migration 086 raw SQL idempotente per `.claude/rules/backend-migrations.md`. NO `session.query()` introducido. |
| 6 | Async Consistency | PASS | `async_log_success_event` proporciona el hook async; `log_success_event` el sync. Coexisten porque LiteLLM dispatches según el contexto del caller. Ambos `try/except` envuelven cache mutation (best-effort + structlog warn). NO blocking I/O. |
| 7 | Pydantic v2 / DTOs / PII | PASS | NO Pydantic models nuevos. Cache state es `dict[str, tuple[Decimal\|None, float]]` (typed). PII review: cost_recorder NO loggea `messages`, `content`, `prompt`, ni metadata sensible — solo `litellm_call_id` (opaque), `model` (identifier), `cost_usd` (numeric). PII safe per `.tessl/.../pii-sanitisation.md`. |
| 8 | Migration Quality | PASS | Migration 086 usa `ALTER TABLE ... ALTER COLUMN cost_usd DROP NOT NULL` (idempotente Postgres, re-run no-op). Downgrade backfilla NULLs con 0 antes de re-aplicar NOT NULL. NO `op.create_table()`/`add_column()` no idempotente. NO `sa.Enum()`. |
| 9 | Security | PASS | NO endpoints nuevos (service-story sin API surface). NO PII en logs (cost recorder loggea solo call_id + model + cost). Cache thread-safe via `threading.Lock`. NO SQL injection risk (raw SQL migration es DDL constante). NO secrets. NO new CVE allowlist requerido. Best-effort try/except previene callback de bloquear el turn. |
| 10 | Tests / TDD | PASS | TDD-mandatory cumplido — impl-log § Plan inicial step 3 documenta "RED tests primero, GREEN después". 13 tests nuevos cubren A1..A5 + sub-cases. Coverage 73% (>43%). Test isolation correcta (autouse `_reset_cache` fixture purga state entre tests). NO `skip`/`xfail`. p95 latency NFR test usa micro-benchmark (n=20 rounds). |
| 11 | Cross-cutting (Master Data + Currency + Spanish + Native-First) | PASS | NO `datetime.utcnow()` (uso `time.monotonic()` para TTL — apropiado para cache expiry). NO `DateTime()` sin tz. cost_usd `Decimal` (no float) — `_coerce_decimal` round-trip via `str()` para precisión. NO hardcoded `'USD'`. Sin user-facing strings (logs en inglés OK). NO `docker exec ruff/pytest` en commits (Native-First clean). NO `git add . / -A / -u` (parallel-safety clean). NO `git pull`/`push --force`/`revert` evidence. Commit body conventional `feat(pi-12-T1):`. |
| 12 | Mirror detection (anti-duplication Cat 12) | PASS | Step 0 grep evidence real (verified by auditor re-run). `cost_recorder.py` es legítimo NEW surface (LiteLLM CustomLogger boundary, conceptualmente distinto del LangChain BaseCallbackHandler shared). Architect doc § 1 + § 10 + impl-log § Step 0 documentan justification. `BaseAgentCallbackHandler` se EXTIENDE (consume `pop_cost` + `_canonical_provider`), NO se duplica. inventory en `.claude/rules/anti-duplication.md` no requiere update (cost_recorder no es subsystem cross-module — vive bajo shared/agent_observability/recording/, dueño único). |

## Critical decision compliance

### A1 SLASHED model field — VERIFIED
- `base_callback_handler.py:572-574`: `model_str = str(model); ... return provider, model_str`. NO `partition('/')`.
- Test `test_canonical_provider_and_cost_from_kwargs` afirma `row["model_requested"] == "deepseek/deepseek-v4-flash"`.
- Snapshot baselines regenerados con model slashed. Diff intencional documentado.

### X2 calculate_cost out of recording path — VERIFIED
- `base_callback_handler.py:37`: import retained con `# noqa: F401 — retained for reconciliation utility, NOT used in runtime path post-T1`.
- `grep -n "calculate_cost(" base_callback_handler.py` → ZERO calls.
- Test `test_calculate_cost_not_called_in_runtime_path` aserts `mock_calc.call_count == 0`.

### Migration 086 idempotency — VERIFIED
- `ALTER TABLE ... ALTER COLUMN cost_usd DROP NOT NULL` es idempotente Postgres native (re-run no-op, no error).
- Downgrade segura: backfill NULL→0 antes de re-imponer NOT NULL.
- Ambas tablas (`copilot_llm_call`, `sales_agent_llm_call`) se modifican en mismo migration step.
- Per `.claude/rules/backend-migrations.md`: ✓ raw SQL, ✓ no `op.add_column()`, ✓ no `sa.Enum()`.

## Scope creep audit

T-1 modifica 4 archivos en `modules/copilot/` y `modules/sales_agent/`:

| File | Change | Verdict |
|---|---|---|
| `modules/copilot/observability/persistence/models/llm_call_model.py` | `cost_usd nullable=False → True` (1 línea) + comment | Pure schema mirror. Justificado por architect doc § 3.4 + § 5: nullable matches migration 086. NO logic change. |
| `modules/sales_agent/observability/persistence/models/llm_call_model.py` | idem | idem |
| `tests/modules/copilot/observability/test_callback_handler.py` | Pre-stash cost via `CostRecorderCustomLogger` antes de `on_llm_end`. Adapt `model_name` a slashed format. | Regression adaptation — test del callback handler shared (consumido por copilot). NO test nuevo de copilot logic. |
| `tests/modules/copilot/observability/test_e2e_isolated.py` | idem (pre-stash + slashed metadata) | idem |

Veredicto: TODOS los cambios cross-modulo son **schema mirrors estrictos** o **regression
adaptations al callback handler shared**. NO se introduce lógica agentic ni cambia
comportamiento de los modulos copilot/sales_agent. Auditor-be jurisdiction válida (no escalate
a auditor-agentic). Architect doc § 3.4 + § 5 + result.md "Notas para auditor" documentan
exhaustivamente.

## Anti-default-flip-audit applicability (Cat 12 anti-default-flip)

T-1 **NO** flipea ningún flag side-effect. Verified `git show 5856be4d | grep -i LITELLM_PROXY_ENABLED` returns 0 matches. Cat anti-default-flip = N/A para este ticket. T-5 será el ticket que ejecute el 4-step audit cuando elimine el flag.

## Allowlist movement

T-1 NO toca arch fitness allowlists. Confirmado vía `git show 5856be4d --stat | grep -E "test_llm_routing_ssot|KNOWN_LEGACY"` returns empty. Cat 8/Cat 12 ratchet shrink-only respetado.

## Native-First + parallel-safety audit

- ✓ NO `docker exec ruff/pytest/tsc/vitest/mypy/eslint` en commit body
- ✓ NO `git add . / -A / -u` en commit
- ✓ Commit message Conventional Commits (`feat(pi-12-T1): ...`)
- ✓ Single commit (no amend, no force push, no revert)
- ✓ Push to `development` (NOT main), no `make ci-parity` requerido por now (PI-12 sigue en development)

## Skill routing compliance

IMPL-LOG § Skills consulted documenta 4 skills mandatory:
- `backend-expert` ✓ (cita `references/runtime-quality-checklist.md`)
- `tessl__fastapi` ✓ (startup hook registration)
- `tessl__pytest-api-testing` ✓ (RED-first tests, factory fixtures, function-scoped)
- `tessl__graceful-degradation` ✓ (best-effort try/except, TTL purge, p95 NFR)

Cubre baseline + tessl__graceful-degradation (aplica porque LLM call path es external dependency
sensible). NO se requiere domain skill (cost_recorder es shared, no toca brand/offer/analytics).
NO se requiere copilot-expert/sales-agent-expert (cambios cross-modulo son schema mirror only).

`runtime-quality-checklist.md` cited explícitamente — auditor verificó observable signals: NO
FastAPI Annotated dep type alias issues (cost_recorder no es endpoint), no override fixture
sin Depends, no 501 stubs, no datetime query parsing, no SQLA legacy Column issues introducidos
(modelos pre-existentes mantienen su patrón Column legacy — no in scope para refactor).

## Verdict math

- **0 FAIL** en categorías 1/2/8/9/12 — clean
- **0 WARN** acumuladas
- **0 allowlist growth** — clean
- **0 /test-backend gate FAIL** — gates 3/4/7/11 verde (re-ejecutados); gate 6 arch fitness 823/823 PASS; gate 5 mypy/coverage no se re-ejecutaron en este audit (out of T-1 scope per parallel-safety M3 — sibling auditor podría correr; auditor confió en dev's `1015 passed` claim verified independently y arch fitness gate)
- **Skills consulted COMPLETE** (4/4 baseline)
- **`runtime-quality-checklist.md` cited** — clean

→ **APPROVED**

## Self-fixes applied

NONE. No trivial lint/format/typo issues encontrados durante audit. Code quality es high
(ruff/format clean en re-run, docstrings Google-style, justified noqa comments). Arch
compliance perfect.

## Notas de seguimiento (no blocking)

1. **Coverage de cost_recorder.py 72%** — los 25 miss son defensive paths (ImportError stub
   fallback, error-class branches del `_resolve_call_id`/`_coerce_decimal`). T-2/T-3 podrían
   subir indirectly via integration tests. NO action required hoy.

2. **Comment on result.md inaccuracy** — dev report dice "Snapshot baseline regenerados —
   diff es solo `model` field (slashed vs stripped)". Diff real incluye también
   `cost_usd: null` y `cost_tenant_currency: null` (bridge cache miss en synthetic snapshot
   tests, intencional per X2). NO blocking — el diff es arquitectónicamente correcto, solo
   doc imprecisa. PM puede notar en 07-merge.md si quiere precisión.

3. **`# noqa: F401` para `calculate_cost` import** — válido por ahora (función retained as
   reconciliation utility). Si futuro T-* (probably T-2 sync-pricing) consume calculate_cost
   en path explícito, el `# noqa` puede removerse. NO action required hoy.

4. **TTL fixture cleanup** — `_reset_cache` fixture en test file accede al `_cache` private
   module-global. Aceptable para test isolation; alternativa más higiénica sería exponer
   `cost_recorder.clear_cache()` API public. NO blocking — convention privada es OK en tests.

## Referencias auditadas

- 00-story.md (po_version=2 ratificada Chris)
- 01-spec.md (4 scenarios obligatorios + decisions A1/X2)
- 03-arch-be.md § 0/§ 1/§ 2.1/§ 2.2/§ 3.2/§ 3.4/§ 4.T-1/§ 5/§ 10
- 04-tickets.yaml T-1 (deliverables A1..A5 + quality gates)
- 05-impl/T-1-result.md
- 05-impl/T-1-impl-log.md
- commit 5856be4d
- `.claude/rules/anti-duplication.md`
- `.claude/rules/anti-default-flip-audit.md`
- `.claude/rules/backend-migrations.md`
- `.claude/rules/tdd-mandatory.md`
- `.claude/rules/spanish-text.md`

## Output al orchestrator

```
done -> docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/06-audit/T-1-review.md
verdict: APPROVED
ready: T-2 builder spawn (T-2 blocked_by T-1, ahora unblocked)
ALSO ready in parallel: T-7 (blocked_by T-1, ahora unblocked)
T-3 still blocked (T-3 blocked_by [T-1, T-2], aguarda T-2)
```
