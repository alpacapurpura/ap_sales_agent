# T-7 Audit Review — Tests audit: migrate per-provider mocks → LiteLLM canonical path

---
ticket_id: T-7
story_id: sales-agent-litellm-canonicalization
sprint: S1-eval-runner
pi: PI-12
audited_by: claude-opus-4-7 (auditor-be)
audited_at: 2026-05-05T10:15Z
push_commit_sha: 38f7e1b7
push_branch: development
verdict: APPROVED
audit_iteration: 1
---

## Verdict

**APPROVED**

## Resumen ejecutivo

T-7 cumple los 4 criterios A1..A4 sin desviación. Es un **tests-only commit**
quirúrgico (4 test files, +113/-651 = net -538 LOC obsoleto) que sanea la
suite pre-T-4/T-5 sin tocar código de runtime. Anti-default-flip-audit Step
1+2 ejecutados con evidencia documentada: zero band-aid mocks
`monkeypatch.setattr(LITELLM_PROXY_ENABLED=False)`, zero `# arch-bypass`
magic comments. La pieza más delicada (migración del reasoning-budget test
desde import-de-spec-de-adapter a `ChatModelSpec` inline) está correctamente
ejecutada — el contract bajo test (`_kwargs.normalize_openai_protocol_kwargs`)
permanece, el spec era sólo fixture. No hay cross-module imports, no hay
mocks que prueben paths muertos, no hay tests skipped/xfail.

Pre-existing failures `test_callback_handler.py::test_persists_row_with_sales_columns` +
`test_callback_handler_usage_fallbacks.py::test_response_metadata_token_usage_is_used`
verificadas como **NO causadas por T-7** (root cause T-1: fixture model
unslashed `"kimi-k2.6"` → `litellm.get_llm_provider` BadRequestError →
`cost_usd=None`). Recomendación: PM crea micro-ticket T-1-bis o lo absorbe
T-9.

## Verifier output (auditor re-ran independentemente)

### A1 — Zero legacy adapter imports en backend/tests/

```
$ grep -rln "from src.shared.infrastructure.llm.providers.\(openai\|deepseek\|kimi\|qwen\|gemini\|_openai_compat\)" backend/tests/
# (empty)
```

✅ A1 satisfied.

### Zero `LITELLM_PROXY_ENABLED` mock band-aids

```
$ grep -rn "monkeypatch.setattr.*LITELLM_PROXY\|setenv.*LITELLM_PROXY" backend/tests/
# (empty)
```

✅ Step 2 anti-flip-audit clean. Las 3 menciones residuales (1 en
`test_router_litellm_dispatch.py` line 4 docstring, 2 en
`test_llm_routing_ssot.py` lines 116/134 arch test docstring + assertion
text) son **texto explicativo histórico**, no son mocks ni setattrs.

### Pytest — T-7 scope (per audit task instructions)

```
$ cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/ tests/modules/sales_agent/test_specialist_provider_routing.py tests/modules/copilot/test_deep_agent_factory_wire.py --override-ini="addopts=" -q
75 passed in 12.06s
```

75/75 PASS. Breakdown:
- `tests/shared/infrastructure/llm/` (incl. simplified `test_router_litellm_dispatch.py` 2/2) — 58 tests
- `tests/modules/sales_agent/test_specialist_provider_routing.py` — 11 tests (TestSpecialistsRouteViaSSoT 4 + TestSettingsResolvesProviderPerRole 5 + TestReasoningBudgetReserveForReasoningSpec 2)
- `tests/modules/copilot/test_deep_agent_factory_wire.py` — 6 tests

### Pytest — full architecture fitness re-run

```
$ cd backend && .venv/bin/pytest tests/architecture/ --override-ini="addopts=" -q
823 passed in 23.78s
```

✅ 823 arch fitness gates verde. Allowlists no engordaron.

### Ruff lint + format on T-7 scope

```
$ cd backend && .venv/bin/ruff check tests/shared/infrastructure/llm/ tests/modules/sales_agent/test_specialist_provider_routing.py --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check tests/shared/infrastructure/llm/test_router_litellm_dispatch.py tests/modules/sales_agent/test_specialist_provider_routing.py
2 files already formatted
```

### Commit body audit (Step 1+2 evidence)

`git show 38f7e1b7 | head -100` confirma:
- ✅ "## Tests audited (anti-default-flip-audit Step 1+2 of 4)" present
- ✅ "Step 1 — grep tests path viejo" listing 7 archivos
- ✅ "Step 2 — migración aplicada" listing DELETED/SIMPLIFIED/MIGRATED actions
- ✅ "## Path old: …router.py::MultiRoleLLMRouter._resolve branch False…"
- ✅ "## Path new: …LiteLLMService singleton"
- ✅ "## Verification:" with 6 verifier outputs
- ✅ "0 tests migrados con monkeypatch.setattr(LITELLM_PROXY_ENABLED=True) band-aid"
- ✅ "0 tests con # arch-bypass: testing legacy capability magic comment"

T-7 documenta explícitamente que **Step 3 + 4 son owned by T-5** (flag
deletion), porque hoy `LITELLM_PROXY_ENABLED` default ya es True y el
flag mismo se borra en T-5. Aceptable per `.claude/rules/anti-default-flip-audit.md`
§ "Special case flag deletion".

### Pre-existing failures verification (out-of-T-7-scope)

```
$ cd backend && .venv/bin/pytest tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py::TestUsageFallbacksFromResponseMetadata::test_response_metadata_token_usage_is_used --override-ini="addopts=" -v
2 failed in 10.75s
# stderr: cost_recorder.unknown_provider error_class=BadRequestError hint=kimi model=kimi-k2.6
```

Root cause confirmado: tests pasan `metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"}` (UNSLASHED) →
post-T-1 cost recorder llama `litellm.get_llm_provider("kimi-k2.6")` → BadRequestError → `cost_usd=None` →
asserts `cost_usd > 0` fallan. **NO es regresión de T-7** (T-7 sólo borró/migró tests
de adapter mocks; no toca callback handler tests ni cost recorder code). Es deuda T-1
que quedó stale: la fixture data debió migrarse `"kimi-k2.6" → "kimi/kimi-k2.6"` cuando
T-1 introdujo el cost recorder canonical.

## Category Summary

| # | Category | Status | Issues |
|---|---|---|---|
| 1 | DDD Compliance | PASS | 0 |
| 2 | Tenant Isolation | N/A | 0 (test-only commit, no queries) |
| 3 | Soft Deletes | N/A | 0 (no DB ops) |
| 4 | Code Quality | PASS | 0 |
| 5 | SQLAlchemy 2.0 | N/A | 0 |
| 6 | Async Consistency | N/A | 0 |
| 7 | Pydantic v2 / PII | N/A | 0 (no DTOs in scope) |
| 8 | Migration Quality | N/A | 0 |
| 9 | Security | PASS | 0 (no security surface touched) |
| 10 | Tests / TDD | PASS | 0 (TDD inverso correcto: tests removidos = path muerto) |
| 11 | Cross-cutting | PASS | 0 |
| 12 | Mirror detection | N/A | 0 (no new files; only deletions + edits) |
| 13 | Default flip side-effect coverage | PASS | Step 1+2 cumplido; Step 3+4 owned by T-5 |

## Findings detallados

### Cat 1 (DDD) — PASS

Tests-only commit. No DDD layers tocadas. Imports en test files respetan
boundaries: `_kwargs`, `_chat_model_resolver`, `LiteLLMService` viven en
`shared/infrastructure/llm/` (canonical surface); `SPECIALIST_TO_ROLE` vive
en `modules/sales_agent/domain/model_tier.py` (correcto — domain export).

### Cat 4 (Code Quality) — PASS

- Ruff check clean en T-7 scope
- Ruff format check clean
- No nuevos `# noqa`, no `# type: ignore`, no `Any`, no TODOs
- Docstrings actualizados explican migración + cross-references al canonical test
- Net -538 LOC = reducción de superficie

### Cat 9 (Security) — PASS

- No `tenant_id` filter rules apply (no queries)
- No PII en logs (test-only)
- No new dependencies
- pip-audit baseline preservada (no changes a requirements)

### Cat 10 (Tests / TDD) — PASS

TDD discipline correcta para deletion of dead-path tests:
- Tests deleted en T-7 cubrían path muerto post-S3 PR-2 (LITELLM_PROXY_ENABLED=False)
  o adapters cuya deletion ya está agendada en T-4. Mantenerlos sería tech debt.
- El único test migrado in-place (`TestReasoningBudgetReserveForReasoningSpec`)
  preserva el contract bajo test (`_kwargs.normalize_openai_protocol_kwargs` con
  reasoning specs) — fixture cambia (inline ChatModelSpec) pero invariant
  (`max_tokens=4700` para `max_output_tokens=700 + reserve=4000`) se mantiene.
- Coverage canonical modules preservada per result.md §A3:
  `litellm.py` 92%, `_kwargs.py` 100%, `_chat_model_resolver.py` 100%.
- Coverage backend-wide drop temporal expected (numerator drop pre-denominator
  drop in T-4); per arch doc § 3.7 acceptable.

### Cat 11 (Cross-cutting) — PASS

- No `git add .` / `-A` / `-u` evidence (commit limpio 7 archivos by name)
- Conventional Commit `test(pi-12-T7): ...` ✅
- Spanish neutro: commit body en español neutro LATAM (sin voseo)
- Native-first: `cd backend && .venv/bin/pytest ...` (no `docker exec`)
- Parallel-safety M8: dev session reportó files ajenos NO tocados
  (Story A T-2, Story B T-2, otras WIP) — verificable en T-7-result.md §
  "Files NOT touched"

### Cat 13 (Default flip side-effect coverage) — PASS

Per `.claude/rules/anti-default-flip-audit.md`:

- ✅ Step 1 — grep tests path viejo ejecutado (7 archivos identificados,
  outputs en T-7-impl-log.md § "Anti-default-flip-audit Step 1+2 evidence")
- ✅ Step 2 — migración aplicada (DELETE 2 + SIMPLIFY 1 + MIGRATE 1)
- ✅ Step 3 — owned by T-5 (Chris flag deletion ticket); T-7 no flipea
  defaults sino que prepara la suite. Aceptable per rule § "Inventario flags
  side-effect" ("LITELLM_PROXY_ENABLED" row será REMOVED en T-5)
- ✅ Step 4 — commit body documenta sections "## Tests audited",
  "## Path old", "## Path new", "## Verification" per template
- ✅ Zero band-aid `monkeypatch.setattr(LITELLM_PROXY_ENABLED=True)` (verifié grep)
- ✅ Zero `# arch-bypass` magic comments

## Cross-scope flags

| File | Module | Action |
|---|---|---|
| `backend/tests/modules/sales_agent/test_specialist_provider_routing.py` | sales_agent | **NOT escalated** — el archivo es **test del router seam** (mocks `LLMFactory.get_service` para verificar `model_type` kwarg per role). NO toca agentic graph state, slot architecture, voice fidelity, prompt templates, ni LangGraph nodes. Tests preservan abstract `LLMFactory` mock — no cambia comportamiento agentic. T-7 scope = LLM routing infrastructure tests only. |

## Allowlist Movement

- ✅ No allowlists growth en arch fitness (823/823 unchanged baseline)
- ✅ No nuevos magic comments / bypasses
- ✅ Net -538 LOC (allowlist effectively shrinks via test code reduction)

## Native-First Audit

- ✅ No `docker exec ... ruff|pytest` en commit body ni en evidence
- ✅ No `git add .` / `-A` / `-u` (7 archivos by name en commit stat)
- ✅ Push directo a `development` (no main) — `make ci-parity` no requerido
- ✅ Co-Authored-By footer presente

## Verdict math

- ✅ No FAIL en categorías 1 / 2 / 8 / 9 / 12
- ✅ No allowlist growth
- ✅ No `/test-backend` gate FAIL (no gate-output.json porque T-7 es scope-quirúrgico
  test-only y el audit task dirige verificación ad-hoc; runner ejecutado manualmente
  por auditor)
- ✅ IMPL-LOG.md § Skills Consulted no-vacío (backend-expert + tessl__pytest-api-testing)
- ⚠️ `runtime-quality-checklist.md` no citado explícitamente en IMPL-LOG (T-7 es
  test-only, ningún anti-pattern del checklist aplica: no FastAPI deps, no override
  fixtures, no 501 stubs, no datetime query, no SQLA legacy). **WARN soft** —
  next step: revisé los anti-patterns que el checklist warns about y ninguno está
  presente → no escalación a FAIL
- ✅ Cero category WARNs verdaderas
- → **PASS**

## Recomendaciones (no bloqueantes)

### Para PM

1. **Micro-ticket T-1-bis (o absorber en T-9)** para fix fixture data en
   2 callback handler tests:
   - `tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns`
   - `tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py::TestUsageFallbacksFromResponseMetadata::test_response_metadata_token_usage_is_used`
   Fix: cambiar `"kimi-k2.6"` → `"kimi/kimi-k2.6"` en metadata fixture (1-2 lines each).
   Root cause: T-1 introdujo cost recorder que llama
   `litellm.get_llm_provider(model)` exigiendo formato slashed; fixture data
   no migrada simultáneamente. NO es regresión de T-7.

2. **T-4 desbloqueado** — gemini.py audit checklist 6/6 + delete 6 archivos legacy
   (per checkpoint critical path). T-7 ✅ no añade pre-condiciones nuevas.

### Para T-9 (docstring purge)

Confirmar que la nueva docstring de `test_specialist_provider_routing.py`
(que menciona "KimiService, DeepSeekService, … are deleted") sea conservada
hasta T-4 ejecute. Después de T-4, el texto se puede simplificar a "per-provider
adapters were deleted in PI-12 S1 T-4".

## Output al orchestrator

```
verdict: APPROVED
ticket: T-7
unblocks: T-4 (legacy adapter deletion + gemini.py audit 6/6)
followup_recommended: PM micro-ticket fixture migration "kimi-k2.6 → kimi/kimi-k2.6"
                      en 2 callback handler tests (T-1 leftover, NOT T-7 caused)
ready_for_t4_builder: YES
```
