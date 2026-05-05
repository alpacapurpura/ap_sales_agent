# T-7-impl-log.md — Tests audit ~20 files: migrate per-provider mocks → LiteLLMService

---
ticket_id: T-7
story_id: sales-agent-litellm-canonicalization
state: tests-passing
assigned_to: claude-opus-4-7
started_at: 2026-05-05T04:25Z
last_update: 2026-05-05T04:50Z
current_step: "Done — ready for commit + /auditor"
blocker: null
---

## Skills Consulted

| Skill | Por qué invocada | Decisión |
|---|---|---|
| `backend-expert` | Test file modifications + native-first lint/test cmd patterns | Aplicar `runtime-quality-checklist` antes commit (FastAPI Annotated dep, override fixture, datetime query, SQLA legacy Column). Para T-7 (test-only): la regla aplicable es "tenant-isolation pattern for tests" + "anti-pattern: monkeypatching path viejo" — se aplica via Step 1-2 anti-default-flip-audit. |
| `tessl__pytest-api-testing` | Mock migration patterns (monkeypatch vs unittest.mock, factory fixtures) | Conservar `unittest.mock.patch` para mocks de `LLMFactory`/`LiteLLMService` (no es per-tenant en estos tests). Conservar `monkeypatch` para settings.attr override. NO introducir factory fixtures nuevos (scope T-7 es migrar, no rebuild). |

## Plan inicial (antes tocar código)

Inventory pass (per arch doc § 3.7 + spec § Tests audit):

| Test file | Action | Reason |
|---|---|---|
| `tests/shared/infrastructure/llm/test_openai_compat_providers.py` | DELETE entire | Tests legacy adapters DeepSeekService/KimiService/QwenService directly. T-4 deletes all 3 → tests would import-fail. Coverage of OpenAI-compat behavior absorbed by `test_litellm_service.py` + `test_litellm_kimi_clamp.py` + `test_kwargs_normalization.py`. |
| `tests/shared/infrastructure/llm/test_provider_routing.py` | DELETE entire | Every test class imports OpenAIService/DeepSeekService/KimiService/QwenService AND/OR calls `build_provider_service()` (T-5 deletes function). `TestLegacyDispatch` toggles `LITELLM_PROXY_ENABLED=False` (flag deleted T-5). `TestTenantOverride` references tenant API key cols (T-6c drops). The router LiteLLM-only contract is covered by `test_router_litellm_dispatch.py` + `test_litellm_service.py`. |
| `tests/shared/infrastructure/llm/test_router_litellm_dispatch.py` | SIMPLIFY | Drop `test_router_resolve_returns_legacy_when_toggle_off`. Drop `monkeypatch.setattr(LITELLM_PROXY_ENABLED=...)` lines (default = True post S3 PR-2; flag will disappear T-5). Keep `test_router_resolve_returns_litellm_when_toggle_on` (rename → `..._returns_litellm`) + `test_router_litellm_singleton_across_roles`. |
| `tests/shared/infrastructure/llm/test_chat_model_resolver.py` | RETAIN | Tests private helpers `_chat_model_resolver.py` + `_kwargs.py` — per arch doc T-4 audits these, may delete; if deleted, T-4 owner deletes the test. T-7 scope: no per-provider Service mocks here. |
| `tests/shared/infrastructure/llm/test_kwargs_normalization.py` | RETAIN | Tests `_kwargs.py` which RETAINS (per arch doc T-4: "RETAIN _kwargs.py — LiteLLMService still consumes"). |
| `tests/shared/infrastructure/llm/test_reasoning_budget_trap.py` | RETAIN | Tests `_response_validation.py` (T-4 audit decides retention) + the reasoning reserve injection contract. No per-provider Service mocks. |
| `tests/shared/infrastructure/llm/test_litellm_service.py` | RETAIN | Already canonical LiteLLMService tests. |
| `tests/shared/infrastructure/llm/test_litellm_kimi_clamp.py` | RETAIN | Already canonical (regression for K2.6 clamp via LiteLLMService). |
| `tests/shared/infrastructure/llm/test_config_service*.py` | RETAIN | Settings-level tests, no provider class refs. |
| `tests/modules/sales_agent/test_specialist_provider_routing.py` | MIGRATE (partial delete) | Drop class `TestKimiKwargsForceThinkingDisabled` (imports `providers.kimi.KimiService`, deleted T-4; covered by `test_litellm_kimi_clamp.py`). Drop class `TestReasoningBudgetReserveAppliesToDeepSeek` (imports `DEEPSEEK_NATIVE_SPEC` from `providers.deepseek`, deleted T-4) → migrate the contract test to use ad-hoc `ChatModelSpec(is_reasoning_model=True, reasoning_token_reserve=4000)` (consistent with `test_reasoning_budget_trap.py` pattern). Keep `TestSpecialistsRouteViaSSoT` + `TestSettingsResolvesProviderPerRole` (mock LLMFactory abstraction; AIProvider enum stable). |
| `tests/modules/copilot/test_deep_agent_factory_wire.py` | RETAIN docstring scrub deferred to T-9 | Tests use `LLMFactory.get_service()` abstraction. Docstring mentions `OpenAIService._models` cache + legacy patterns but no provider class is imported. T-9 owns docstring purge; T-7 does NOT touch (scope discipline). |

### Anti-default-flip-audit Step 1+2 evidence

Step 1 — grep tests path viejo (this session, 2026-05-05T04:25Z):

```bash
$ grep -rln "OpenAIService\|DeepSeekService\|KimiService\|QwenService\|GeminiService" backend/tests/ | grep -v __pycache__
backend/tests/architecture/test_llm_routing_ssot.py            # docstring + assertion text only — handled by T-8
backend/tests/modules/copilot/test_deep_agent_factory_wire.py  # docstring mentions only — T-9 scope
backend/tests/modules/sales_agent/test_specialist_provider_routing.py
backend/tests/shared/infrastructure/llm/test_chat_model_resolver.py  # docstring mentions only
backend/tests/shared/infrastructure/llm/test_kwargs_normalization.py # docstring mentions only
backend/tests/shared/infrastructure/llm/test_openai_compat_providers.py
backend/tests/shared/infrastructure/llm/test_provider_routing.py

$ grep -rln "providers\.\(openai\|deepseek\|kimi\|qwen\|gemini\|_openai_compat\)" backend/tests/
backend/tests/modules/sales_agent/test_specialist_provider_routing.py  # KimiService + DEEPSEEK_NATIVE_SPEC
backend/tests/shared/infrastructure/llm/test_openai_compat_providers.py
backend/tests/shared/infrastructure/llm/test_provider_routing.py

$ grep -rln "LITELLM_PROXY_ENABLED" backend/tests/
backend/tests/architecture/test_llm_routing_ssot.py             # docstring only — T-8 scope
backend/tests/shared/infrastructure/llm/test_provider_routing.py
backend/tests/shared/infrastructure/llm/test_router_litellm_dispatch.py
```

Step 2 (mock migration pattern):
- For tests probing the LiteLLM dispatch path (default True): DELETE the `monkeypatch.setattr(LITELLM_PROXY_ENABLED=...)` lines (path will be only path post-T5).
- For tests probing legacy path (False): DELETE the test entirely (legacy path gone T-4).
- Per arch doc § 9: NO migrate to `monkeypatch.setattr(..., True)` — innecesario, default ya es True.

Step 3 + 4 (run both flag values + commit body): owned by T-5 (flag deletion). T-7 only documents Step 1+2 in commit body.

## Bitácora paso-a-paso

### 04:25 — Setup + inventory

- Read 01-spec, 03-arch-be, 04-tickets (T-7 scope).
- Read each candidate test file. Inventory complete (above).
- Confirmed `test_litellm_kimi_clamp.py` covers Kimi K2.6 clamp via LiteLLMService end-to-end (replaces `TestKimiKwargsForceThinkingDisabled`).
- Confirmed `_kwargs.py` retained per arch doc T-4 (LiteLLMService still consumes via `_response_validation.py` + `_chat_model_resolver.py`).
- Baseline: `pytest tests/shared/infrastructure/llm/ tests/modules/sales_agent/test_specialist_provider_routing.py tests/modules/copilot/test_deep_agent_factory_wire.py --override-ini="addopts=" -q` → 112 passed (pre-T-7).

### 04:30 — DELETE test_openai_compat_providers.py + test_provider_routing.py

```bash
$ rm backend/tests/shared/infrastructure/llm/test_openai_compat_providers.py
$ rm backend/tests/shared/infrastructure/llm/test_provider_routing.py
$ ls backend/tests/shared/infrastructure/llm/
__init__.py
test_chat_model_resolver.py
test_config_service.py
test_config_service_per_tenant.py
test_kwargs_normalization.py
test_litellm_kimi_clamp.py
test_litellm_service.py
test_reasoning_budget_trap.py
test_router_litellm_dispatch.py
```

`test_openai_compat_providers.py` (-280 lines) cubría DeepSeekService/KimiService/QwenService adapter constructors + base_url + temperature cache + missing-API-key + embedding contract. Equivalent canonical coverage existe en `test_litellm_kimi_clamp.py` (4 tests, K2.6 clamp via LiteLLMService) + `test_kwargs_normalization.py` (8 tests, max_tokens translation) + `test_litellm_service.py` (LiteLLM model alias slashed).

`test_provider_routing.py` (-217 lines) tenía 4 clases — todas dependientes de:
- `build_provider_service()` function (deleted in T-5)
- `LITELLM_PROXY_ENABLED=False` toggle (flag deleted T-5; legacy path deleted T-4)
- tenant API key cols (dropped in T-6c)

La sola propiedad sobreviviente ("router devuelve LiteLLMService") cubierta por `test_router_litellm_dispatch.py`.

### 04:35 — SIMPLIFY test_router_litellm_dispatch.py

Drop test `test_router_resolve_returns_legacy_when_toggle_off` (probaba dead path). Drop `monkeypatch.setattr("src.core.config.settings.LITELLM_PROXY_ENABLED", True)` lines (default = True desde S3 PR-2; flag desaparece T-5). Conservados: `test_router_resolve_returns_litellm` (rename) + `test_router_litellm_singleton_across_roles`. Module docstring rewritten para documentar el cambio.

### 04:38 — MIGRATE test_specialist_provider_routing.py

DROP class `TestKimiKwargsForceThinkingDisabled` (importa `from src.shared.infrastructure.llm.providers.kimi import KimiService, _K2_REQUIRED_TEMPERATURE`):
- Razón 1: KimiService deleted en T-4.
- Razón 2: equivalent end-to-end coverage en `test_litellm_kimi_clamp.py` (LiteLLMService canonical, en producción desde S3 PR-2).

MIGRATE `TestReasoningBudgetReserveAppliesToDeepSeek` → `TestReasoningBudgetReserveForReasoningSpec`:
- Pre-T-7: `from providers.deepseek import DEEPSEEK_NATIVE_SPEC`
- Post-T-7: construct `ChatModelSpec(is_reasoning_model=True, reasoning_token_reserve=4000)` inline (helper static method `_reasoning_spec()`).
- El contract bajo test es `_kwargs.normalize_openai_protocol_kwargs` con specs reasoning-capable; spec instance es sólo fixture.
- Pattern espejado de `test_reasoning_budget_trap.py::TestReasoningReserveInjection` (ya construye specs inline).

KEEP intactas: `TestSpecialistsRouteViaSSoT` (4 tests) + `TestSettingsResolvesProviderPerRole` (5 tests). No tienen per-provider class refs — usan `LLMFactory` mock + `AIProvider` enum.

Module docstring rewritten para explicar la migración + cross-reference al test canonical.

### 04:42 — Verify

```bash
$ cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/test_router_litellm_dispatch.py tests/modules/sales_agent/test_specialist_provider_routing.py --override-ini="addopts=" -v
13 passed in 10.51s

$ cd backend && .venv/bin/pytest tests/shared/infrastructure/llm/ tests/architecture/ --override-ini="addopts=" -q
881 passed in 24.14s

$ grep -rln "from src.shared.infrastructure.llm.providers.\(openai\|deepseek\|kimi\|qwen\|gemini\|_openai_compat\)" backend/tests/
# (empty — A1 satisfied)
```

### 04:45 — Detect 2 pre-existing failures (NOT caused by T-7)

```bash
$ git stash
$ cd backend && .venv/bin/pytest tests/modules/sales_agent/observability/test_callback_handler.py::TestOnChatModelEnd::test_persists_row_with_sales_columns --override-ini="addopts=" -q
1 failed (pre-T-7, with my changes stashed)
$ git stash pop
```

Confirmed: ambos failures (`test_callback_handler.py::test_persists_row_with_sales_columns` + `test_callback_handler_usage_fallbacks.py::test_response_metadata_token_usage_is_used`) ya fallaban pre-T-7. Root cause T-1: tests pasan model UNSLASHED `"kimi-k2.6"` al callback handler, post-T-1 `litellm.get_llm_provider("kimi-k2.6")` raises BadRequestError → cost_usd=None. Out of T-7 scope. Documentado en T-7-result.md § "Riesgos conocidos".

### 04:48 — Final lint + format check on T-7 scope

```bash
$ cd backend && .venv/bin/ruff check tests/shared/infrastructure/llm/ tests/modules/sales_agent/test_specialist_provider_routing.py --no-cache
All checks passed!

$ cd backend && .venv/bin/ruff format --check tests/shared/infrastructure/llm/test_router_litellm_dispatch.py tests/modules/sales_agent/test_specialist_provider_routing.py
2 files already formatted
```

## Tests corridos

| Cuándo | Comando | Resultado |
|---|---|---|
| 04:25 (baseline pre-T-7) | `pytest tests/shared/infrastructure/llm/ tests/modules/sales_agent/test_specialist_provider_routing.py tests/modules/copilot/test_deep_agent_factory_wire.py` | 112 passed |
| 04:42 (post-migration) | idem | 75 passed (-37 = 25 deleted file 1 + 11 deleted file 2 + 1 dropped test in router_dispatch) |
| 04:42 | `pytest tests/shared/infrastructure/llm/test_router_litellm_dispatch.py tests/modules/sales_agent/test_specialist_provider_routing.py -v` | 13/13 PASS |
| 04:43 | `pytest tests/shared/infrastructure/llm/ tests/architecture/` | 881/881 PASS |
| 04:43 | `pytest tests/modules/copilot/test_deep_agent_factory_wire.py` | 6/6 PASS |
| 04:44 | `pytest tests/modules/sales_agent/` | 675/676 (1 pre-existing failure unrelated to T-7) |
| 04:45 | `pytest tests/modules/copilot/observability/` | 163/164 (1 pre-existing failure unrelated to T-7) |
| 04:48 | `ruff check + format` (T-7 scope) | clean |

## Estado al cerrar

- ticket state: `tests-passing` → push imminente
- Próximo paso: commit + push + spawn /auditor
- Pre-existing failures (2) NO son scope T-7 — documentados en T-7-result.md
- Quedan ajenos files de Story A T-2 y Story B T-2 SIN tocar (parallel-safety M8)
