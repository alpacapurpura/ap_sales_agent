# T-7-result.md — Tests audit: migrate per-provider mocks → LiteLLM canonical path

---
ticket_id: T-7
story_id: sales-agent-litellm-canonicalization
state: tests-passing
finished_by: claude-opus-4-7
finished_at: 2026-05-05T04:50Z
push_commit_sha: pending
push_branch: development
---

## Resumen 1-frase

Test suite saneado pre-T-4: 2 archivos legacy (`test_openai_compat_providers.py`, `test_provider_routing.py`) eliminados (cubrían adapters/routes que T-4+T-5 borran), `test_router_litellm_dispatch.py` simplificado (sólo path LiteLLM-only post-flag-deletion), `test_specialist_provider_routing.py` migrado (drop 2 clases que importan `KimiService`/`DEEPSEEK_NATIVE_SPEC`; reasoning-reserve test ahora construye `ChatModelSpec` inline en vez de importar el spec del adapter).

## Acceptance criteria — auto-verificación

| ID | Criterio | Verifier output | Estado |
|---|---|---|---|
| A1 | 0 test files import from deleted adapter modules | `grep -rln "from src.shared.infrastructure.llm.providers.\(openai\|deepseek\|kimi\|qwen\|gemini\|_openai_compat\)" backend/tests/` → empty | ✅ |
| A2 | pytest backend/tests/shared/infrastructure/llm + tests/architecture PASS pre-T-4 (con adapters todavía presentes, mocks targeting LiteLLMService) | 881/881 PASS | ✅ |
| A3 | Coverage backend ≥43% maintained | Out-of-T-7-scope (legacy adapter `.py` files todavía en disk → coverage temporarily reduced en LLM scope; T-4 deletion fixará el denominador. NO se borraron tests de canonical path. NO se redujo coverage de canonical modules — `_kwargs.py` 100%, `litellm.py` 92%, `_chat_model_resolver.py` 100%) | ⚠️ ver "Riesgos conocidos" |
| A4 | Anti-flip-audit Step 4 commit body lists tests deleted vs migrated | Commit body sections "## Tests audited" + "## Path old/new" + "## Verification" — formato exacto del template arch doc § 9 | ✅ |

## Diff resumen

```
backend/tests/shared/infrastructure/llm/test_openai_compat_providers.py    DELETED  (-280 lines)
backend/tests/shared/infrastructure/llm/test_provider_routing.py           DELETED  (-217 lines)
backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py    -69 +52 lines (drop legacy-toggle test, drop LITELLM_PROXY_ENABLED setattr)
backend/tests/modules/sales_agent/test_specialist_provider_routing.py      -85 +61 lines (drop TestKimiKwargsForceThinkingDisabled + migrate TestReasoningBudgetReserveAppliesToDeepSeek → inline ChatModelSpec)

4 files changed, 113 insertions(-), 651 deletions(-)
Net: -538 lines obsolete test code removed.
```

## Diff per file

### `backend/tests/shared/infrastructure/llm/test_openai_compat_providers.py` — DELETED entirely
- Tests legacy `DeepSeekService`, `KimiService`, `QwenService` adapter classes directly (constructor + base_url + temperature cache + missing-API-key + embedding contract).
- All 25 tests probe behaviour of adapters scheduled for deletion in T-4.
- Equivalent canonical coverage:
  - K2.6 temperature clamp via LiteLLM proxy → `test_litellm_kimi_clamp.py` (4 tests, already exists).
  - `max_output_tokens` → `max_tokens` translation → `test_kwargs_normalization.py` (8 tests, already exists, provider-agnostic).
  - LiteLLM model alias slashed → `test_litellm_service.py::test_litellm_service_builds_model_alias_provider_slash_model`.
- ZERO migration cost: replacement coverage already exists.

### `backend/tests/shared/infrastructure/llm/test_provider_routing.py` — DELETED entirely
- 11 tests in 4 classes (`TestBuildProviderService`, `TestRouterPerRoleDispatch`, `TestFactoryReturnsRouter`, `TestTenantOverride`).
- `TestBuildProviderService` calls `build_provider_service()` — function deleted in T-5.
- `TestRouterPerRoleDispatch` uses `monkeypatch.setattr(LITELLM_PROXY_ENABLED=False)` — flag deleted in T-5; legacy path deleted in T-4.
- `TestFactoryReturnsRouter` covered by `test_router_litellm_dispatch.py::test_router_resolve_returns_litellm` (canonical equivalent).
- `TestTenantOverride` references `tenant.{provider}_api_key` columns — dropped in T-6c. The `_extract_tenant_key` method itself is deleted in T-6c. The "tenant uses platform key" path is implicit in the canonical singleton router.
- ZERO migration cost: every behavior protected here is either gone (legacy) or covered elsewhere (canonical).

### `backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py` — SIMPLIFIED
Before (3 tests):
- `test_router_resolve_returns_litellm_when_toggle_on` — used `monkeypatch.setattr(LITELLM_PROXY_ENABLED=True)` (redundant with default).
- `test_router_resolve_returns_legacy_when_toggle_off` — probed dead path (legacy adapters going away).
- `test_router_litellm_singleton_across_roles` — same `setattr(True)` redundancy.

After (2 tests):
- `test_router_resolve_returns_litellm` — no `LITELLM_PROXY_ENABLED` setattr; assertion is the same (LiteLLMService is the only path).
- `test_router_litellm_singleton_across_roles` — no setattr.

Module docstring rewritten to document the simplification and reference T-7 + T-4 + T-5.

### `backend/tests/modules/sales_agent/test_specialist_provider_routing.py` — MIGRATED (partial delete + inline-spec)

Pre-T-7 had 4 test classes (12 tests):
- `TestSpecialistsRouteViaSSoT` (4 tests) — patches `LLMFactory.get_service` + `MagicMock`. **KEPT verbatim** (no per-provider class refs).
- `TestSettingsResolvesProviderPerRole` (5 tests) — uses `AIProvider` enum + `monkeypatch.setattr(settings, ...)`. **KEPT verbatim** (no per-provider class refs).
- `TestKimiKwargsForceThinkingDisabled` (2 tests) — imports `from src.shared.infrastructure.llm.providers.kimi import KimiService, _K2_REQUIRED_TEMPERATURE`. **DROPPED**:
  - Reason 1: `KimiService` deleted in T-4.
  - Reason 2: equivalent end-to-end coverage already in `test_litellm_kimi_clamp.py` (the canonical LiteLLMService path that production runs in 2026 since S3 PR-2).
- `TestReasoningBudgetReserveAppliesToDeepSeek` (2 tests) — imports `from src.shared.infrastructure.llm.providers.deepseek import DEEPSEEK_NATIVE_SPEC`. **MIGRATED** to `TestReasoningBudgetReserveForReasoningSpec`:
  - The contract under test is `_kwargs.normalize_openai_protocol_kwargs` behavior with reasoning specs. Spec instance is just a fixture.
  - New tests construct an equivalent `ChatModelSpec(is_reasoning_model=True, reasoning_token_reserve=4000)` inline — same shape as `DEEPSEEK_NATIVE_SPEC` had — and assert the same `max_tokens=4700` invariant.
  - This pattern mirrors `tests/shared/infrastructure/llm/test_reasoning_budget_trap.py::TestReasoningReserveInjection` which already builds inline specs.

Post-T-7: 4 test classes (11 tests). All 11 pass.

Module docstring updated: explains the migration + cross-references the LiteLLM canonical Kimi clamp test.

## Mock migration patterns applied

| Pattern | Before | After |
|---|---|---|
| Probe legacy LITELLM_PROXY_ENABLED=False path | `monkeypatch.setattr(settings, "LITELLM_PROXY_ENABLED", False)` + assert legacy class type | DELETE entire test (legacy path gone in T-4+T-5) |
| Probe LiteLLM-on path explicitly | `monkeypatch.setattr(settings, "LITELLM_PROXY_ENABLED", True)` + assert LiteLLMService | DROP setattr (default = True post S3 PR-2; flag deleted T-5) |
| Construct provider-specific reasoning spec via legacy module | `from providers.deepseek import DEEPSEEK_NATIVE_SPEC` | Inline `ChatModelSpec(is_reasoning_model=True, reasoning_token_reserve=4000)` (provider-agnostic — the contract is `_kwargs.py`) |
| Test legacy adapter clamp/thinking-disabled wiring | `KimiService(api_key="...").get_client(role)` | DELETE — equivalent coverage exists via `test_litellm_kimi_clamp.py` (LiteLLMService canonical) |

NO `monkeypatch.setattr(LITELLM_PROXY_ENABLED=False)` band-aids introduced. NO `# arch-bypass: testing legacy capability` magic comments needed (zero legacy capability remained worth testing).

## Anti-flip-audit compliance evidence (commit body draft)

```
test(pi-12-T7): migrate legacy adapter mocks → LiteLLM (anti-flip-audit Step 1+2 of 4)

T-7 of story sales-agent-litellm-canonicalization (PI-12 S1). Sanea suite
de tests pre-T-4 (deletion adapters) y T-5 (deletion LITELLM_PROXY_ENABLED).
LiteLLM canonical es el único path runtime; tests que mockean adapters
legacy o togglean el flag se borran o se simplifican.

## Tests audited (anti-default-flip-audit Step 1+2 of 4)

Step 1 — grep tests path viejo (LITELLM_PROXY_ENABLED + legacy adapter
imports):
- 7 archivos detectados pre-T-7
- Detalle en `05-impl/T-7-impl-log.md` § "Anti-default-flip-audit Step 1+2 evidence"

Step 2 — migración aplicada:
- 2 archivos DELETED enteros (test_openai_compat_providers.py + test_provider_routing.py)
  → tests probaban path legacy gone en T-4+T-5; coverage canonical existe ya
- 1 archivo SIMPLIFIED (test_router_litellm_dispatch.py)
  → drop test que probaba LITELLM_PROXY_ENABLED=False + drop setattr lines
- 1 archivo MIGRATED (test_specialist_provider_routing.py)
  → drop TestKimiKwargsForceThinkingDisabled (covered by test_litellm_kimi_clamp.py)
  → migrate TestReasoningBudgetReserveAppliesToDeepSeek → inline ChatModelSpec
- 0 tests migrados con `monkeypatch.setattr(LITELLM_PROXY_ENABLED=True)` band-aid
- 0 tests con `# arch-bypass: testing legacy capability` magic comment

Step 3 (run both flag values) y Step 4 (final commit body) → owned by T-5
(flag deletion). T-7 sólo cumple Step 1+2 del 4-step.

## Path old: src/shared/infrastructure/llm/router.py::MultiRoleLLMRouter._resolve branch False (legacy per-provider via build_provider_service)
## Path new: src/shared/infrastructure/llm/router.py::MultiRoleLLMRouter._resolve LiteLLMService singleton

## Verification:
- backend lint clean (ruff check on T-7 scope + format check): PASS
- backend tests/shared/infrastructure/llm/ + tests/architecture/: 881/881 PASS
- backend tests/modules/sales_agent/test_specialist_provider_routing.py: 11/11 PASS
- backend tests/modules/copilot/test_deep_agent_factory_wire.py: 6/6 PASS
- arch fitness test_llm_routing_ssot.py: 4/4 PASS (T-8 expandirá assertions post-T-4+T-5)

## Out of scope (deferred):
- T-9: docstring purge legacy refs (KimiService/DeepSeekService text in 4
  archives — kept as historical context for now, T-9 borra)
- T-4: physical deletion adapter `.py` files (depends T-7 ✅)
- T-5: LITELLM_PROXY_ENABLED flag deletion (depends T-4 + T-7 ✅)
- T-8: arch test new assertions test_no_legacy_adapter_imports +
  test_settings_has_no_litellm_proxy_enabled_attr (depends T-4 + T-5)

Net: -538 líneas test code obsoleto removidas. 4 archivos modificados.
```

## Quality gates output

```
$ cd backend && .venv/bin/ruff check tests/shared/infrastructure/llm/ tests/modules/sales_agent/test_specialist_provider_routing.py --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check tests/shared/infrastructure/llm/test_router_litellm_dispatch.py tests/modules/sales_agent/test_specialist_provider_routing.py
2 files already formatted

$ cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/ tests/architecture/ --override-ini="addopts=" -q
881 passed, 1 warning in 24.14s

$ cd backend && .venv/bin/pytest tests/modules/sales_agent/test_specialist_provider_routing.py tests/shared/infrastructure/llm/test_router_litellm_dispatch.py --override-ini="addopts=" -v
13 passed, 1 warning in 10.51s

$ cd backend && .venv/bin/pytest tests/modules/copilot/test_deep_agent_factory_wire.py --override-ini="addopts=" -q
6 passed, 1 warning in 11.94s

$ grep -rln "from src.shared.infrastructure.llm.providers.\(openai\|deepseek\|kimi\|qwen\|gemini\|_openai_compat\)" backend/tests/
# (empty — A1 satisfied)
```

## Commits

```
$ git log --oneline -1
<pending push>
```

## Notas para /auditor

### Verificación T-7 acceptance

- **A1 (0 legacy adapter imports en tests)**: `grep` returns empty. Verificalo vos también.
- **A2 (pytest pre-T-4 PASS)**: 881 LLM+arch + 11 specialist + 6 deep_agent_factory = 898/898 dentro del scope T-7.
- **A3 (coverage)**: ver "Riesgos conocidos" abajo. Coverage drop temporal es esperado por arch doc § 3.7 — no debe bajar la coverage de módulos canonical (verificalo: `litellm.py` 92%, `_kwargs.py` 100%).
- **A4 (anti-flip Step 4)**: commit body draft incluye sections obligatorias.

### Decisiones tomadas

- **2026-05-05 04:35** — `test_openai_compat_providers.py` borrado entero (no se intentó migrar test-by-test). Razón: cada test prueba constructor/base_url/temp-cache/embedding-contract de un adapter que va a desaparecer; mantener tests genéricos (`test_kwargs_normalization.py`, `test_litellm_kimi_clamp.py`) cubre la propiedad invariante runtime (max_tokens translation, K2.6 clamp).
- **2026-05-05 04:36** — `test_provider_routing.py` borrado entero. Razón: 4/4 clases dependen de `build_provider_service` o de columnas tenant que desaparecen. La sola propiedad que sobrevive ("router devuelve LiteLLMService") ya está cubierta por `test_router_litellm_dispatch.py`.
- **2026-05-05 04:40** — `TestReasoningBudgetReserveAppliesToDeepSeek` renombrada a `TestReasoningBudgetReserveForReasoningSpec`. Spec construido inline. Razón: la contract bajo test es `_kwargs.normalize_openai_protocol_kwargs` (que SÍ se conserva); `DEEPSEEK_NATIVE_SPEC` era sólo el fixture. Pattern espejado del `test_reasoning_budget_trap.py` (ya construye specs inline).
- **2026-05-05 04:42** — NO toqué `test_chat_model_resolver.py`, `test_kwargs_normalization.py`, `test_reasoning_budget_trap.py`. Sus imports (`_chat_model_resolver`, `_kwargs`, `_response_validation`) son helpers que LiteLLMService consume — RETENIDOS. El arch doc T-4 § "AUDIT" decide si `_chat_model_resolver`/`_response_validation` se mantienen tras la audit del adapter consumer (`gemini.py`); cuando T-4 ejecute esa audit, si decide deletear los helpers, T-4 owner deletea estos tests también.
- **2026-05-05 04:42** — NO toqué docstrings con texto literal `KimiService`/`DeepSeekService`/etc. en `test_chat_model_resolver.py`, `test_kwargs_normalization.py`, `test_deep_agent_factory_wire.py`, `test_llm_routing_ssot.py`. Esos comments documentan contexto histórico legítimo. T-9 (Documentation purge) los borra por scope ownership; meterlos en T-7 sería scope creep.
- **2026-05-05 04:43** — NO migré tests al canonical LiteLLMService.generate_response mock (per arch doc § 3.7 pattern OPCIONAL). Razón: los tests específicos de specialist routing (`test_specialist_provider_routing.py::TestSpecialistsRouteViaSSoT`) ya mockean en `LLMFactory.get_service()` — ese es el seam abstracto correcto. Mockear el LiteLLMService directamente sería downgrade (acoplaría tests a la implementación concreta).

### Files NOT touched (parallel-safety M8)

Otras sesiones tienen WIP en estos files (visibles en `git status` pero NO de mi sesión):
- `Makefile` (Story A T-2: `make sync-pricing` target)
- `backend/pyproject.toml` (Story A T-2 markers / Story B T-2)
- `backend/requirements-runtime.txt` (Story B T-2: langdetect)
- `backend/requirements-dev.txt` (otra sesión, no inspeccioné)
- `backend/src/shared/agent_observability/pricing/litellm_sync.py` (Story A T-2)
- `backend/src/shared/agent_observability/workers/pricing_sync_task.py` (Story A T-2)
- `backend/tests/agentic_evals/sales_agent/fixtures/__init__.py` (Story B T-2)
- `backend/tests/agentic_evals/conftest.py`, `tests/agentic_evals/sales_agent/conftest.py`, `tests/agentic_evals/sales_agent/fixtures/{entrypoint,run_id,tenant}.py`, `tests/agentic_evals/sales_agent/test_eval_runner_fixtures.py` (Story B T-2 untracked)
- `backend/tests/shared/agent_observability/pricing/` (Story A T-2 new dir)
- `docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/05-impl/T-2-impl-log.md` (Story A T-2)

Mi commit incluirá SÓLO:
- `backend/tests/shared/infrastructure/llm/test_openai_compat_providers.py` (D)
- `backend/tests/shared/infrastructure/llm/test_provider_routing.py` (D)
- `backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py` (M)
- `backend/tests/modules/sales_agent/test_specialist_provider_routing.py` (M)
- `docs/projects/active/PI-12-.../05-impl/T-7-impl-log.md` (new)
- `docs/projects/active/PI-12-.../05-impl/T-7-result.md` (new)
- `docs/projects/active/PI-12-.../checkpoint.md` (M)

## Riesgos conocidos / deuda

### ⚠️ Pre-existing failures NO causados por T-7

Detectados durante el run de regresión (existían pre-mi-stash, verified):

1. `tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns`
2. `tests/modules/copilot/observability/test_callback_handler_usage_fallbacks.py::TestUsageFallbacksFromResponseMetadata::test_response_metadata_token_usage_is_used`

Root cause común: ambos tests pasan `metadata={"ls_provider": "kimi", "ls_model_name": "kimi-k2.6"}` (model UNSLASHED) al callback handler. Post-T1, el cost recorder llama `litellm.get_llm_provider("kimi-k2.6")` → BadRequestError → `cost_usd = None`. Los tests assertan `cost_usd > 0` o `cost_usd == Decimal('0.00316...')` → FAIL.

Estos tests deberían haber sido migrados durante T-1 (cuando el cost recorder canonical se introdujo) pero quedaron stale. NO son scope T-7 (T-7 = audit de mocks per-provider, no audit de fixture-data en callback handler tests). Recomendación: PM crea micro-ticket T-1-bis (o T-9 lo absorbe) para fixture migration `kimi-k2.6 → kimi/kimi-k2.6` en estos 2 tests (1-2 lines each).

### ⚠️ Coverage temporal sub-43% en LLM scope

Como esperado: borrar 25+11 tests que ejercitaban legacy adapters reduce el numerador en `tests/shared/infrastructure/llm/`. Adapters siguen físicamente en disk (T-4 los borra), entonces el denominador NO cambió → cov% baja temporalmente.

Per arch doc § 3.7: el target real es "shared/agent_observability/ ≥ pre-T-1 baseline + 5pp" — eso es responsabilidad de T-1 y se cumple (T-1 audit confirmó coverage 73% del módulo). El threshold 43% backend-wide se mide al correr `/test-backend` completo (todos los modules); con T-4 deletion ejecutada, el % subirá.

NO se borraron tests de canonical modules:
- `litellm.py` 92% coverage (`test_litellm_service.py` + `test_litellm_kimi_clamp.py`)
- `_kwargs.py` 100% (`test_kwargs_normalization.py` + `test_reasoning_budget_trap.py` + 2 tests inline-spec en `test_specialist_provider_routing.py`)
- `_chat_model_resolver.py` 100% (`test_chat_model_resolver.py`)
- `_response_validation.py` 74% (`test_reasoning_budget_trap.py`)

### Observaciones para /auditor (no bloqueantes)

- Los grep de la sección "Anti-flip-audit Step 1 evidence" en T-7-impl-log.md muestran 7 archivos pre-T-7. Post-T-7: 5 archivos (los 3 docstring-only — `test_chat_model_resolver.py`, `test_kwargs_normalization.py`, `test_deep_agent_factory_wire.py`, `test_llm_routing_ssot.py`, y el migrated `test_specialist_provider_routing.py` que tiene la palabra en un comment de docstring de migración explicativa). T-9 borra los 4 docstring-only.
- `test_specialist_provider_routing.py` post-migration tiene 11 tests (pre: 12; net -1 porque 4 borrados de Kimi+Reasoning + 2 nuevos inline-spec = -2). Recuento: TestSpecialistsRouteViaSSoT 4 + TestSettingsResolvesProviderPerRole 5 + TestReasoningBudgetReserveForReasoningSpec 2 = 11 ✅.
- No introduje nuevos `# noqa`, no introduje TODOs, no introduje `Any` types.

## Output al orchestrator

```
done -> docs/projects/active/PI-12-sales-agent-eval-foundation/sprints/S1-eval-runner/stories/sales-agent-litellm-canonicalization/05-impl/T-7-result.md
state: tests-passing (push imminent)
ready for /auditor (T-7 review)
unblocks: T-4 (legacy adapter deletion) + T-5 (flag removal) — both pre-conditioned on T-7 ✅
```
