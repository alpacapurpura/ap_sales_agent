# IMPL-LOG — PR-1 Business Surface (nicolify-backend Sonnet)

> Session: 2026-05-04 | Builder: nicolify-backend (Sonnet 4.6) | Surface: business

---

## Skills Consulted

| Skill | Why invoked | Decision taken |
|---|---|---|
| `backend-expert` | Mandatory per system prompt Step 0 GATE. Anti-patterns FastAPI/SQLA/tests/migrations. | Verified singleton reset pattern (runtime-quality-checklist.md autouse fixture override pattern). Confirmed no Annotated dep anti-patterns introduced. |
| `tessl__pytest-api-testing` | Mandatory per system prompt. Fixture scoping, factory fixtures, monkeypatch vs mock. | Used patch.object(EventBusAdapter, "_is_outbox_enabled") for D2 Caso C migration (not monkeypatch settings). Autouse function-scope for singleton fixture per checklist. |
| `tessl__fastapi` | Mandatory per system prompt. | N/A to this PR (no API routes changed). Verified `redirect_slashes=False` untouched. |
| `tessl__graceful-degradation` | Called because LegacyEventBus deprecation warning wraps external config import. | Confirmed best-effort (try/except BLE001) — must not break caller (per pattern for observability writes). |
| `brand-expert` | Touching tests/modules/brand/. | Verified `test_brand_section_updated_event.py` tests BrandRepository event emission contract (Caso C). Migration correct. |

---

## Step 0 Grep Findings

### Singleton inventory (grep `_instance = None\|cls._instance\|@lru_cache\|@cache`)

```
backend/src/shared/infrastructure/llm/factory.py:31-33      → LLMFactory._instance (class-level)
backend/src/shared/application/progress_emitter.py:31       → @lru_cache(maxsize=128) — NOT class singleton, per-call cache; not reset
backend/src/shared/domain_events/outbox/application/event_bus_adapter.py:54 → @cache on _module_name_from_file; reset via _reset_module_inference_cache()
backend/src/modules/copilot/application/discovery.py:154    → @lru_cache(maxsize=1) — copilot scoped, NOT reset (agentic territory)
backend/src/modules/connections/infrastructure/channels/meta.py:303 → self._api_instance = None (per-instance, NOT class-level)
backend/src/modules/sales_agent/application/services/semantic_router.py:46-60 → SemanticRouter._instance (class-level)
backend/src/modules/sales_agent/application/orchestrator/chat.py:74-81 → ChatOrchestrator._instance (class-level)
backend/src/modules/campaigns/infrastructure/channels/registry.py:48-52 → ChannelRouterRegistry._instance (class-level, EXCLUDED per CONTRACT)
```

**Decision per singleton:**
1. LLMFactory._instance → RESET (stale router with prod settings)
2. ChatOrchestrator._instance → RESET (buffer_service + _initialized flag leak)
3. SemanticRouter._instance → RESET (tenant-scoped routing rules cache)
4. ChannelRouterRegistry._instance → EXCLUDED (bootstrap-once, reset breaks campaigns tests)
5. MetaAPI._api_instance → EXCLUDED (per-instance self., not class-level)
6. EventBus._handlers → CLEAR via EventBus.clear() (subscriber handler leak)
7. EventBusAdapter _module_name_from_file @cache → CLEAR via _reset_module_inference_cache()

### EventBus migration audit (grep `EventBus.publish` in tests)

Files detected (23 total):
- `tests/modules/copilot/test_extraction_event_handlers.py` → Caso A (AGENTIC owns)
- `tests/modules/copilot/observability/test_domain_subscribers.py` → Caso A (AGENTIC owns)
- `tests/modules/copilot/observability/test_register.py` → Caso A (AGENTIC owns)
- `tests/modules/copilot/api/test_suggestions_endpoint.py` → Caso A (AGENTIC owns)
- `tests/modules/copilot/api/test_suggestions_accept_endpoint.py` → Caso A (AGENTIC owns)
- `tests/modules/copilot/suggestions/test_suggestion_event_recorded.py` → Caso A (AGENTIC owns)
- `tests/modules/brand/test_brand_section_updated_event.py` → Caso C **MIGRATED** (business builder)
- `tests/modules/brand/test_outbox_adapter_integration.py` → Caso E (meta-test, already correct via patch.object)
- `tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py` → Caso B (AGENTIC owns)
- `tests/modules/sales_agent/orchestrator/test_audit_emitter.py` → Caso A (AGENTIC owns)
- `tests/modules/sales_agent/tools/payment/test_grant_access_idempotent.py` → Caso A (AGENTIC owns)
- `tests/modules/crm/test_sale_lifecycle.py` → Caso A (AGENTIC owns)
- `tests/shared/application/test_brand_summary_event_handlers.py` → Caso A (AGENTIC owns)
- `tests/shared/domain_events/test_event_bus_adapter.py` → Caso D/E (already correct, meta-test via monkeypatch settings)
- `tests/shared/domain_events/test_event_bus_adapter_infers_module.py` → Caso E (AGENTIC/shared)
- `tests/shared/test_event_bus.py` → Caso D (capability test, unchanged)
- `tests/integration/test_outbox_cutover_e2e.py` → Caso B (AGENTIC owns)
- `tests/modules/brand/integration/test_outbox_cutover.py` → Caso B (real DB integration)
- `tests/modules/copilot/integration/test_outbox_cutover.py` → Caso B (AGENTIC owns)
- `tests/modules/sales_agent/integration/test_outbox_cutover.py` → Caso B (AGENTIC owns)
- `tests/modules/sales_agent/test_outbox_adapter_integration.py` → Caso E (AGENTIC owns)
- `tests/architecture/test_no_legacy_event_bus_publish.py` → capability test (not consuming EventBus)
- `tests/architecture/test_social_proof_invariants.py` → event reference, not mock

**Business builder migrated: 1 file** (test_brand_section_updated_event.py, Caso C)
**Agentic builder owns: 15+ files** (per CONTRACT § 11 surface mapping)

---

## Stash Apply Audit (16 archivos)

| # | File | Stash content | Action taken |
|---|---|---|---|
| 1 | `tests/architecture/test_ddd_boundaries.py` | 3 KNOWN_CROSS_MODULE_IMPORTS entries | KEEP + COMMITTED |
| 2 | `tests/architecture/test_folder_naming.py` | copilot/api/_dependencies.py exception | KEEP + COMMITTED |
| 3 | `tests/architecture/test_sales_agent_anchors.py` | SALES-AGENT-OUTBOUND-PR7 | KEEP, LEFT UNSTAGED (agentic builder) |
| 4 | `tests/architecture/test_sales_agent_system_prompt_order.py` | CAMPAIGN_CONTEXT | KEEP, LEFT UNSTAGED (agentic builder) |
| 5 | `tests/conftest.py` | Singleton fixture initial (3 singletons) | EXTENDED to exhaustive (5 singletons + 2 caches) + COMMITTED |
| 6 | `tests/integration/test_outbound_orchestrator_e2e.py` | Mock target rename | LEFT UNSTAGED (agentic builder) |
| 7 | `tests/modules/brand/test_brand_section_updated_event.py` | monkeypatch.setattr(USE_OUTBOX_PATTERN_BRAND=False) | **MIGRATED** to patch.object Caso C + COMMITTED |
| 8 | `tests/modules/brand/test_outbox_adapter_integration.py` | patch.object(_is_outbox_enabled) | KEEP (already Caso E correct) + COMMITTED |
| 9 | `tests/modules/copilot/test_offer_section_tools.py` | next_step_hint contract | LEFT UNSTAGED (agentic builder) |
| 10 | `tests/modules/copilot/test_outbox_adapter_integration.py` | USE_OUTBOX_PATTERN_COPILOT=False | LEFT UNSTAGED (agentic builder to migrate) |
| 11 | `tests/modules/copilot/test_voice_api.py` | 410 Gone | LEFT UNSTAGED (agentic builder) |
| 12 | `tests/modules/copilot/test_voice_combined.py` | 410 Gone | LEFT UNSTAGED (agentic builder) |
| 13 | `tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py` | @pytest.mark.flaky band-aid | LEFT UNSTAGED (agentic builder — polluter hunt Fase 4) |
| 14 | `tests/modules/sales_agent/prompts/test_compose_system_prompt.py` | CAMPAIGN_CONTEXT | LEFT UNSTAGED (agentic builder) |
| 15 | `tests/shared/domain_events/test_event_bus_adapter.py` | monkeypatch settings (Caso D/E correct) | KEEP + COMMITTED |
| 16 | `src/shared/infrastructure/llm/providers/litellm.py` | kimi clamp | VALIDATED vs § 7 spec + COMMITTED |
| 17 | `frontend/closer-studio/CampaignTag.test.tsx` | /campañas/ → /campanas/ | KEEP + COMMITTED |

---

## Singleton Fixture Inventory (exhaustive)

**Validated via grep 2026-05-04:**

| # | Class | Path:line | Reset reason | In fixture |
|---|---|---|---|---|
| 1 | LLMFactory._instance | factory.py:31-33 | Stale MultiRoleLLMRouter with prod settings | YES — `LLMFactory._instance = None` |
| 2 | ChatOrchestrator._instance | chat.py:74-81 | buffer_service state + _initialized flag | YES — cleanup buffer_service first, then `_instance = None` |
| 3 | SemanticRouter._instance | semantic_router.py:46-60 | Tenant-scoped routing rules cache | YES — `_instance = None` |
| 4 | ChannelRouterRegistry._instance | registry.py:48-52 | EXCLUDED: bootstrap-once, reset breaks campaigns | EXCLUDED (documented) |
| 5 | MetaAPI._api_instance | meta.py:303 | EXCLUDED: per-instance self., not class-level | EXCLUDED (documented) |
| 6 | EventBus._handlers | events.py class-level | Subscriber leak PI.md § Origen point 2 | YES — `EventBus.clear()` |
| 7 | EventBusAdapter @cache | event_bus_adapter.py:54 | Stale filename→module mappings | YES — `_reset_module_inference_cache()` |

---

## litellm.py Kimi Clamp Validation (§ 7 spec vs stash)

| Spec requirement | Stash implementation | Status |
|---|---|---|
| Clamp in `_get_chat_model` | ✓ Line 115 after effective_temp calculation | PASS |
| Detection covers `kimi/kimi-k2.6` (LiteLLM convention) | ✓ `"kimi/kimi-k2" in litellm_model.lower()` | PASS |
| Logger via structlog | ✓ `logger.warning("kimi_k2_temperature_clamped", ...)` | PASS |
| Mirror of kimi.py:79-92 semantics | ✓ Same pattern: `temperature != _K2_REQUIRED_TEMPERATURE → clamp` | PASS |
| `_K2_REQUIRED_TEMPERATURE = 0.6` constant | ✓ Module-level constant with docstring | PASS |
| 4 regression tests | ✓ Created test_litellm_kimi_clamp.py | PASS |

**Stash vs spec diff:** Stash uses `"kimi/kimi-k2"` (more specific than CONTRACT's `"kimi/k2"` but catches same models). No adjustment needed.

---

## LegacyEventBus Deprecation Pattern (§ 5)

- `_is_internal_caller_or_test()` helper: walks call stack 10 frames, detects `shared/domain_events/` + `shared/domain/events.py` + `/tests/` paths
- `EventBus.publish()`: best-effort warning in try/except BLE001
- Imports: `import warnings` + `import structlog` added to events.py header
- Warning message: `"EventBus.publish called when outbox cutover active. Migrate emitter to EventBusAdapter or wrap with magic comment '# arch-bypass: testing legacy capability'."`
- 4 test cases created in `tests/shared/test_legacy_event_bus_deprecation_warning.py`

---

## Quality Gates Output

| Gate | Result |
|---|---|
| ruff check src/ tests/ | 0 errors |
| ruff format --check | 0 files to reformat |
| brand tests (11) | 11/11 PASS |
| shared/domain_events tests (8) | 8/8 PASS |
| kimi clamp tests (4) | 4/4 PASS |
| deprecation warning tests (4) | 4/4 PASS |
| architecture tests (811) | 811/811 PASS |
| shared module tests (total 1210) | 1210/1210 PASS |
| frontend closer-studio vitest | 10/10 PASS |
| mypy src/shared/domain/events.py | 0 errors (existing overrides) |

---

## EXTEND-vs-NEW Decisions

All surfaces = EXTEND (zero new modules/files except test regression files):
- conftest.py singleton fixture → EXTEND existing conftest (never new file)
- litellm.py kimi clamp → EXTEND _get_chat_model method (no new provider)
- events.py deprecation warning → EXTEND EventBus.publish (no new class)
- test files → NEW regression tests (fixture pattern per tessl__pytest-api-testing)

---

## Commits (business surface)

| Hash | Message |
|---|---|
| 7652f1f8 | test(conftest): add exhaustive singleton isolation fixture (PI-11 PR-1 Fase 3) |
| 10b71ca5 | fix(llm): clamp kimi K2.6 temperature in litellm provider (PI-11 PR-1 § 7) |
| 03cfd727 | feat(events): emit DeprecationWarning when LegacyEventBus.publish called with outbox on |
| ee26d5c2 | test(arch): add allowlist entries for known cross-module imports + private file exception |
| 37e0b794 | test(brand,shared): migrate EventBus band-aid to adapter mock pattern (D2, PI-11 PR-1 Fase 2) |
| a3f4e85d | test(closer-studio): fix CampaignTag URL slug to ASCII /campanas/ |
| 9f89b65d | docs(pm): add CONTRACT.md + CONTEXT-BRIEF.md for PR-1 + PR-3 (PI-11 S1) |

---

## Agentic Files Remaining (unstaged — agentic builder owns)

Per CONTRACT.md § 11 surface mapping:
- `tests/architecture/test_sales_agent_anchors.py` (SALES-AGENT-OUTBOUND-PR7)
- `tests/architecture/test_sales_agent_system_prompt_order.py` (CAMPAIGN_CONTEXT)
- `tests/integration/test_outbound_orchestrator_e2e.py` (mock target rename)
- `tests/modules/copilot/test_offer_section_tools.py` (next_step_hint)
- `tests/modules/copilot/test_outbox_adapter_integration.py` (MIGRATE Caso B/E — agentic)
- `tests/modules/copilot/test_voice_api.py` (410 Gone)
- `tests/modules/copilot/test_voice_combined.py` (410 Gone)
- `tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py` (polluter hunt Fase 4)
- `tests/modules/sales_agent/prompts/test_compose_system_prompt.py` (CAMPAIGN_CONTEXT)

These files contain valid stash fixes but require agentic builder (nicolify-agentic) to commit per parallel-safety M3.

---

## Open Questions from CONTRACT.md § 10

1. **LiteLLM proxy extra_body thinking disabled** — not addressed in litellm.py. kimi.py injects `{"thinking": {"type": "disabled"}}` at line 94-97. litellm.py does NOT. Needs PM decision: is this managed proxy-side via litellm_config.yaml or must adapter mirror it? Deferred — not in PR-1 scope.
2. **Polluter Fase 4** — owned by agentic builder. test_chat_orchestrator_snapshot.py still has @pytest.mark.flaky stash content (unstaged). Singleton fixture (PR-1 Fase 3) likely addresses ChatOrchestrator._instance polluter root cause.

---

## Cross-PR Coordination Signal (§ 13)

PR-3 (anti-default-flip enforcement) can launch after PR-1 business PASS. Business EventBus migration complete (1 file migrated, all others either agentic or already Caso D/E). PR-3 arch fitness test `test_no_legacy_eventbus_mock_when_outbox_on.py` baseline allowlist needed if agentic builder hasn't finished Caso A migrations.

Signal commit: this commit hash `37e0b794` = "EventBus migration complete (business surface)".
