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

---

# IMPL-LOG — PR-1 Agentic Surface (nicolify-agentic Opus 4.7[1M])

> Session: 2026-05-04 (continuation post agente previo) | Builder: nicolify-agentic (Opus 4.7) | Surface: agentic
> Date captured Step 0: 2026-05-04

---

## Skills Consulted (agentic surface)

| Skill | Why invoked | Decision taken |
|---|---|---|
| `copilot-expert` | Mandatory per system prompt — touching `tests/modules/copilot/**` (offer_section_tools, voice_api, voice_combined, outbox_adapter_integration). | Confirmed PII sanitisation + 410 deprecation pattern + outbox flag isolation per `monkeypatch.setattr(MagicMock(USE_OUTBOX_PATTERN_COPILOT=False, ...))` (acceptable Caso B/E pattern — meta-test of adapter routing logic, not band-aid since validates adapter behavior under explicit flag). |
| `sales-agent-expert` | Mandatory per system prompt — touching `tests/modules/sales_agent/**` + `_chat_flow_snapshot_helpers.py`. Verified §3 NO-tocar list — snapshot helpers ARE test infra, NOT §3 protected (CONTRACT § 0 confirms). | Snapshot helper migration to `adapter_bus.publish` mock (Caso A — fake_db doesn't allow Caso B outbox table probe). CAMPAIGN_CONTEXT cacheable fragment expected ordering preserved per slot architecture. Voseo of agent output respected (no spanish-text rule application — agent OUTPUT is tenant voice). |
| `tessl__pytest-api-testing` | Snapshot helper monkeypatch pattern + fixture isolation. | Used `monkeypatch.setattr(event_bus_adapter.adapter_bus, "publish", ...)` to patch instance attribute. Belt-and-suspenders second patch on legacy `EventBus.publish` for any direct caller bypass (defense-in-depth). |

---

## Stash Files Audit (agentic-owned, 8 files unstaged from business iter 1)

| # | File | Stash content | Validation | Action |
|---|---|---|---|---|
| 1 | `tests/architecture/test_sales_agent_anchors.py` | `SALES-AGENT-OUTBOUND-PR7` registry entry | arch test PASS (7/7) | KEEP + COMMIT |
| 2 | `tests/architecture/test_sales_agent_system_prompt_order.py` | `CAMPAIGN_CONTEXT` cacheable fragment | arch test PASS — CACHEABLE_FRAGMENTS source matches | KEEP + COMMIT |
| 3 | `tests/integration/test_outbound_orchestrator_e2e.py` | Mock target rename `build_sales_agent_callback_handler` → `build_sales_agent_observability_context` | 2/2 PASS | KEEP + COMMIT |
| 4 | `tests/modules/copilot/test_offer_section_tools.py` | `next_step_hint` contract + `_engine_suggestions_for_context` mock isolation | suite PASS, prevents real DB leak via SuggestionEngine providers | KEEP + COMMIT |
| 5 | `tests/modules/copilot/test_outbox_adapter_integration.py` | `monkeypatch.setattr(settings, MagicMock(USE_OUTBOX_PATTERN_COPILOT=False, ...))` | Caso E (meta-test of adapter routing — validates flag-OFF branch contract). Pattern accepted per CONTRACT § 3 "test prueba la capability del adapter mismo". | KEEP + COMMIT |
| 6 | `tests/modules/copilot/test_voice_api.py` | 410 Gone assertions (deleted obsolete WhisperTranscriber mocks) | suite PASS — endpoint deprecated PR-2 PI-2 BE-side | KEEP + COMMIT |
| 7 | `tests/modules/copilot/test_voice_combined.py` | 410 Gone assertions | suite PASS | KEEP + COMMIT |
| 8 | `tests/modules/sales_agent/prompts/test_compose_system_prompt.py` | `CAMPAIGN_CONTEXT` in CACHEABLE_FRAGMENTS | suite PASS | KEEP + COMMIT |

**`test_chat_orchestrator_snapshot.py`** (band-aid removal target per workflow Step 4): VERIFIED — file is already clean (no `@pytest.mark.flaky` present). The polluter band-aid mentioned in PR.md/CONTRACT was never committed; only existed in stash discussion. **No action needed.**

---

## Snapshot Helpers Outbox-Aware Migration (CONTRACT § 4 D6 — Step 3)

**File touched:** `backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py` (line 215-227 → ~245)

### Problem (pre-migration)

`_capture_publish` patched `src.shared.domain.events.EventBus.publish` (legacy). Post outbox cutover (PR-6 PI-2, USE_OUTBOX_PATTERN_SALES_AGENT=True default):
- Production emitters route via `adapter_bus.publish` (canonical post-cutover entry point)
- `EventBus.publish` legacy is only invoked on fall-through (flag OFF, session=None, or _is_outbox_enabled returns False)
- In snapshot test fixture: `fake_db = MagicMock` is neither `Session` nor `AsyncSession`, so adapter takes sync path → `outbox.enqueue_sync(event, session=fake_db)` → calls `fake_db.execute(...)` swallowed in `try/except BLE001` (best-effort contract)
- Net result: real domain events DISAPPEARED silently → baseline file `telegram_new_lead_baseline.json` had `domain_events: []` (false negative reflecting fall-through misses, not real production behavior)

### Fix (CONTRACT § 4 Caso A — adapter_bus mock)

Replaced single `monkeypatch.setattr(EventBus.publish, ...)` with two patches:
1. **Primary:** `monkeypatch.setattr(event_bus_adapter.adapter_bus, "publish", _capture_publish)` — patches instance attribute on the canonical singleton (single entry point post-cutover)
2. **Belt-and-suspenders:** also patch legacy `EventBus.publish` to wrap the same `_capture_publish` (defense-in-depth in case any code path bypasses adapter and hits legacy bus directly)

`_capture_publish` signature accepts `module=None, idempotency_key=None` kwargs (adapter passes these), preserving back-compat for legacy emitters.

### Snapshot baseline diff

Pre-migration:
```json
"domain_events": []
```

Post-migration:
```json
"domain_events": [
  {
    "event_name": "lead_captured",
    "payload": {
      "channel_slug": "telegram-dm",
      "extracted_field": "external_id",
      "profile_id": "aaaaaaaa-1111-1111-1111-aaaaaaaaaaaa",
      "source_channel_type": "telegram"
    },
    "tenant_id": "44444444-4444-4444-4444-444444444444"
  }
]
```

Baseline file regenerated at `backend/tests/snapshots/orchestrator/telegram_new_lead_baseline.json`. Snapshot test `test_chat_flow_telegram_new_lead_snapshot` PASSES post-migration.

**Why Caso A vs Caso B:** Caso B (probe outbox table real DB) inapplicable — snapshot test fixture uses `fake_db = MagicMock` (no real DB session). Querying outbox table would require integration test infrastructure scope outside snapshot test purpose.

---

## Polluter Hunt Log (CONTRACT § 6 D5 — Step 4)

### Step 1 — Snapshot baseline isolation

```
.venv/bin/pytest tests/modules/sales_agent/orchestrator/test_chat_orchestrator_snapshot.py -v
→ 1 passed in 10.57s (test PASSES isolated)
```

### Step 2 — Reproduce in suite

```
.venv/bin/pytest tests/modules/sales_agent/ -v --tb=short -x -q
→ 675 passed, 3 deselected, 3 warnings (NO FAILURE)
```

**Result: polluter NO LONGER REPRODUCES.** Singleton fixture installed by business builder iter 1 (`tests/conftest.py`, commit `7652f1f8`) addressed root cause.

### Step 3 — Cross-module pollution validation (5x consecutive runs)

```
.venv/bin/pytest tests/modules/sales_agent/ tests/modules/copilot/ \
  --ignore=tests/modules/copilot/api/test_suggestions_endpoint_integration.py \
  -q --tb=no
```

| Run | Result |
|---|---|
| 1 | 2488 passed in 63.03s |
| 2 | 2488 passed in 64.76s |
| 3 | 2488 passed in 65.10s |
| 4 | 2488 passed in 63.78s |
| 5 | 2488 passed in 64.54s |

**5/5 deterministic — polluter eliminated.**

(Excluded test: `test_e2e_real_engine_real_offer_provider` requires Postgres DB resolution `postgres` hostname — Docker integration test, unrelated to PR-1. Out of agentic scope.)

### Polluter ROOT CAUSE confirmed

Per CONTRACT § 6 hypothesis matrix:
- **Primary suspect: `ChatOrchestrator._instance` + `SemanticRouter._instance` leak** — buffer_service state + tenant-scoped routing rules persisted cross-test → next test reused stale orchestrator with wrong tenant context
- **Secondary suspect: `EventBus._handlers` leak** — TestDomainSubscribersRegistration test left subscribers registered without teardown

### Fix at source (D4 — NO band-aid)

Singleton fixture `_reset_singletons_between_tests` (autouse function-scope) in `tests/conftest.py`:
- `LLMFactory._instance = None` (stale router with prod settings)
- `ChatOrchestrator._instance.buffer_service = None` then `_instance = None` (cleanup before drop)
- `SemanticRouter._instance = None`
- `EventBus.clear()` (subscriber leak)
- `_reset_module_inference_cache()` (lru_cache stale filename mappings)

Excluded (justified): `ChannelRouterRegistry._instance` (bootstrap-once design — reset breaks campaigns), `MetaAPI._api_instance` (per-instance not class-level).

**Hypothesis "uuid4 doble call routing OFF flag" from previous agent**: REJECTED. The flag is read at runtime via `getattr(settings, flag_attr)`, not cached at module load. uuid4 calls in `OutboxEntry.from_event` (id + idempotency_key) are independent invocations within `enqueue_sync` — they're consumed by INSERT to `domain_event_outbox`. They don't gate routing — `_is_outbox_enabled` precedes them. Real polluter was simpler: orchestrator singletons leaking buffer state/routing tables cross-test.

### `@pytest.mark.flaky(reruns=2)` band-aid (D4 enforcement)

VERIFIED: `test_chat_orchestrator_snapshot.py` is **CLEAN** — no flaky marker present. Band-aid never landed; only existed as stash hypothesis. No removal needed.

---

## Quality Gates (agentic surface)

| Gate | Result |
|---|---|
| `ruff check` agentic-touched files (9 files) | All checks passed |
| `ruff format --check` agentic-touched files | 9 files already formatted |
| `pytest tests/architecture/test_sales_agent_*.py --override-ini='addopts='` | 7/7 PASS |
| `pytest tests/integration/test_outbound_orchestrator_e2e.py` | 2/2 PASS |
| `pytest tests/modules/sales_agent/ tests/modules/copilot/` | 2488/2488 PASS (excl 1 Docker integ) |
| 5x consecutive runs determinism | 5/5 PASS @ 2488 each |
| Snapshot test isolation | 1/1 PASS post-regen baseline |

---

## EXTEND-vs-NEW Decisions (agentic surface)

All surfaces = EXTEND (zero new modules/files):
- `_chat_flow_snapshot_helpers.py` — EXTEND `_capture_publish` (replace mock target adapter_bus + belt-and-suspenders legacy)
- All other agentic files — KEEP stash content as-is, validated against test pass

Snapshot baseline file `telegram_new_lead_baseline.json` REGENERATED (not new — overwrite of existing).

---

## Cross-PR Coordination Signal (§ 13 — agentic side)

PR-3 arch fitness test `test_no_legacy_eventbus_mock_when_outbox_on.py` can now reduce its `KNOWN_LEGACY_MOCK_FILES` allowlist:
- `_chat_flow_snapshot_helpers.py` MIGRATED (Caso A adapter_bus mock) → REMOVE from allowlist
- All Caso A copilot files (test_extraction_event_handlers, observability/test_*, api/test_suggestions*, suggestions/test_*) NOT YET MIGRATED in this iter (out of scope agentic stash applied — these are agentic-owned but stash didn't include them per business builder Step 0 grep). Defer Caso A migration of those 6 files to FUTURE PR (not blocking PR-1 close).
- `test_outbox_adapter_integration.py` (copilot) — Caso E meta-test, magic comment `# arch-bypass: testing legacy capability` should be added to file header for PR-3 arch test bypass (deferred — not blocking PR-1).

Signal commits: see § Commits below.

---

## Commits (agentic surface — to be pushed)

| Order | Files | Conventional message |
|---|---|---|
| 1 | `tests/architecture/test_sales_agent_anchors.py` `tests/architecture/test_sales_agent_system_prompt_order.py` | `test(arch): register SALES-AGENT-OUTBOUND-PR7 anchor + CAMPAIGN_CONTEXT cacheable fragment (PI-11 PR-1 stash)` |
| 2 | `tests/modules/sales_agent/prompts/test_compose_system_prompt.py` | `test(sales_agent): expect CAMPAIGN_CONTEXT in cacheable fragments (PI-11 PR-1 stash)` |
| 3 | `tests/modules/copilot/test_offer_section_tools.py` `tests/modules/copilot/test_outbox_adapter_integration.py` `tests/modules/copilot/test_voice_api.py` `tests/modules/copilot/test_voice_combined.py` | `test(copilot): isolate offer suggestion engine, validate 410 voice deprecation, monkeypatch settings for outbox flag (D2)` |
| 4 | `tests/integration/test_outbound_orchestrator_e2e.py` | `test(integration): rename mock target to build_sales_agent_observability_context` |
| 5 | `tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py` `tests/snapshots/orchestrator/telegram_new_lead_baseline.json` | `test(sales_agent): outbox-aware snapshot capture via adapter_bus mock + regenerated baseline (PI-11 PR-1 Fase 5 D6)` |

---

## Open Questions resolved

1. **Polluter Fase 4** (pre-resolved by business iter 1): root cause = orchestrator singleton leaks; singleton fixture covers. NO band-aid needed; verified clean.
2. **Snapshot baseline regen** (CONTRACT § 10 Q5): committed within PR-1 per Q5 PM acceptance.
3. **Caso A migrations of 6 deferred copilot files** (test_extraction_event_handlers, etc.): Out of agentic stash scope — defer to FUTURE PR. PR-1 ship not blocked.

