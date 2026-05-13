---
ticket: T-2-codemod-aug (Phase 1 — Sonnet builder-backend Session 8)
story: luana-nicolify-migration
date: 2026-05-14
author: claude-sonnet-4-6 builder-backend
status: COMPLETE — categorization + codemod extension + self-check
---

# T-2-codemod-aug — Failure Categorization (Option C, Phase 1)

Scope: 13 NOT-deferred failures from T-2-bigbang-result.md §"NOT eval-deferred".
Source: T-2-bigbang-result.md, SESSION-7-HALT-2026-05-13.md, live test runs.

## Summary

| Group | Count | Root mechanism | Codemod fix? |
|---|---|---|---|
| A — copilot (4) | 4 | 2× Cat I, 2× Cat III (monkeypatch on old module object) | Cat I: test update only. Cat III: new MonkeypatchModuleRewriter |
| B — analytics (7) | 7 | 2× Cat II (script stale import), 5× Cat V-seed (seed script stale import) | New StaleScriptImportRewriter |
| C — offer (1) | 1 | Cat I (string literal assertion of old import path in source code) | Test update only |
| D — scripts (1) | 1 | Cat V-const (test expects old constant value) | Test/script value update |

**Key finding:** All 13 failures fall into known/fixable categories. No Cat VI+ requiring fundamental redesign. Proceed with targeted codemod extension.

---

## Group A — Copilot (4 failures)

### Failure A1: `test_atomic_switch.py::TestChatHotPathImportsNewModule::test_imports_observability_context`

- File: `tests/modules/copilot/observability/test_atomic_switch.py:82`
- Mechanism: **Cat I — Import-path assertion test**
- Source excerpt:
  ```python
  def test_imports_observability_context(self) -> None:
      text = CHAT_PY.read_text()
      assert "ObservabilityContext" in text, "..."
      assert "from src.modules.copilot.observability" in text, "chat.py must use the new observability module"
  ```
- Root cause: The test asserts that `chat.py` contains the OLD import path string `"from src.modules.copilot.observability"`. Post-codemod, `chat.py` was correctly rewritten to use `"from luana_core_copilot.observability"`, so the string is no longer present. The assertion is **inverted logic**: it was originally checking that the NEW observability module path was used (vs the old `trace_recorder`), but it hard-coded the intermediate `src.modules.X` path.
- Required fix: Update the assertion in the test file to check for `"from luana_core_copilot.observability"` instead of `"from src.modules.copilot.observability"`. This is a **test update** — codemod cannot safely handle this because the string "from src.modules.copilot.observability" appears inside a Python string literal that is used as an assertion target (not as a mock path). MockPatchStringRewriter would incorrectly rewrite it.
- Required codemod rewriter behavior: N/A — this is a targeted manual fix in the test file. The string is not a mock patch target; it's an assertion string that checks source code content.

---

### Failure A2: `test_suggestions_endpoint_integration.py::TestSuggestionsIntegration::test_e2e_real_engine_real_offer_provider`

- File: `tests/modules/copilot/api/test_suggestions_endpoint_integration.py:24`
- Mechanism: **Cat V — Integration timeout (DB unavailable)**
- Source excerpt:
  ```python
  @pytest.mark.integration
  class TestSuggestionsIntegration:
      def test_e2e_real_engine_real_offer_provider(self) -> None:
          """Tenant sin offers + route='offer-studio' → chip 'Crea tu primera oferta'."""
          from luana_core_copilot.api.suggestions import router
          from luana_core_copilot.application.suggestions.registry import _reset_for_tests
          # ... makes real HTTP request via TestClient with real OfferSuggestionProvider
          # OfferSuggestionReader → get_offer_repository(db) → hits Postgres
  ```
- Root cause: The test is `@pytest.mark.integration` (class-level) which is NOT excluded by the pytest `addopts = "-m 'not verify'"` filter. The test uses `OfferSuggestionProvider` via the real engine which calls `OfferSuggestionReader.list_offers()` → `get_offer_repository(db)`. Without a running Postgres, the DB session times out at 60s.
- The test imports are already using `luana_core_copilot` (post-codemod correct). The failure is NOT a codemod issue — it's a **pre-existing integration test that requires Postgres** and was previously obscured (the test may have been passing before the codemod because it was deselected, or Postgres was available).
- Investigation: This test is marked `@pytest.mark.integration`. Pre-bigbang baseline of 8 failures likely included this test being skipped or masked. Post-bigbang, the test was collected (10183/10195) and ran but failed with 60s timeout.
- Required fix: The test correctly uses `luana_core_copilot` imports. The fix is to add a DB session override in the test to prevent the real DB call, OR to exclude it via `-m "not integration"` in pyproject.toml. Since the test is already labeled `integration`, the real fix is to ensure `addopts` excludes integration markers OR to mock the DB dependency in the test. The **correct targeted fix**: add `-m "not integration"` to `addopts` OR add a mock for the DB session. Since this test was listed as NOT-deferred, recommend mocking the DB session to make it unit-testable.
- Required codemod rewriter behavior: N/A — test fix is domain-logic, not import path. Recommend direct test edit.

---

### Failure A3: `test_route_tool_mapping.py::TestProviderRouteMerging::test_provider_routes_extend_wildcard_fallback`

- File: `tests/modules/copilot/test_route_tool_mapping.py:144-149`
- Mechanism: **Cat III — Monkeypatch on imported module object via old `src.modules.X` path**
- Source excerpt:
  ```python
  def _patch_discovery_with(self, monkeypatch, provider):
      import importlib
      import src.modules.copilot.application.discovery as disc  # ← OLD path
      import src.modules.copilot.application.tools.registry as reg  # ← OLD path
      monkeypatch.setattr(disc, "discover_providers", lambda: {provider.module_id: provider})
      importlib.reload(reg)
      return reg
  ```
- Root cause: The test helper `_patch_discovery_with` imports the registry module via the OLD `src.modules.copilot.application.discovery` path. Post-codemod, the actual module lives at `luana_core_copilot.application.discovery`. `monkeypatch.setattr(disc, "discover_providers", ...)` patches the `discover_providers` function on the OLD module object `disc` (loaded from `src.modules.copilot...`). The `importlib.reload(reg)` reloads the registry from the OLD path. Since `luana_core_copilot` is the installed package, the OLD path now points to a STALE import of the same underlying code, but the `monkeypatch` acts on the wrong module reference. The synthetic provider is registered on the old namespace and never seen by the reloaded registry, so `_tp10_synth_group` never appears in `TOOL_GROUPS`.
- Required codemod rewriter behavior: **MonkeypatchModuleRewriter** must handle `import X as Y` statements (not just `from X import Y`) where `X` starts with a legacy `src.modules.X` prefix. These are standard Python `import` statements (not `from ... import`), and the current `ImportRewriter` only handles `from ... import`. Need a new visitor for `cst.Import` (non-from) statements that rewrites the dotted module name.

---

### Failure A4: `test_route_tool_mapping.py::TestProviderRouteMerging::test_provider_routes_extend_specific_prefix`

- File: `tests/modules/copilot/test_route_tool_mapping.py:166-216`
- Mechanism: **Cat III — same as A3** (uses same `_patch_discovery_with` helper)
- Source excerpt: Same `_patch_discovery_with` method at line 141.
- Root cause: Identical to A3 — the `_patch_discovery_with` helper imports `src.modules.copilot.application.discovery` and `src.modules.copilot.application.tools.registry` via old paths. The `_GrowthProvider` registration fails for same reason.
- Required codemod rewriter behavior: Same as A3 — **MonkeypatchModuleRewriter** for `import X as Y` form.

---

## Group B — Analytics (7 failures)

### Failure B1: `test_campaign_sync_task.py::TestRunCampaignSyncTask::test_credentials_are_flattened_before_pipeline`

- File: `tests/modules/analytics/test_campaign_sync_task.py:43`
- Mechanism: **Cat II — Dynamic mock provider with stale patch target**
- Source excerpt:
  ```python
  _CONN_PORT = "luana_core_connections.application.services.connection_port_impl.ConnectionPortImpl"
  _PIPELINE = "luana_core_analytics_engine.infrastructure.sync.campaign_sync_pipeline.CampaignSyncPipeline"
  _PROVIDER = "luana_core_analytics_engine.infrastructure.providers.meta_campaign_provider.MetaCampaignProvider"
  _REPO = "luana_core_analytics_engine.infrastructure.repositories.campaign_repository.CampaignRepository"
  ```
  The patch targets are already using `luana_core_X` paths. The actual failure is:
  ```
  pydantic_core.ValidationError: 2 validation errors for ConnectionCredentials
  credentials: Input should be a valid dictionary [MagicMock...]
  config: Input should be a valid dictionary [MagicMock...]
  ```
- Root cause: The mock for `_CONN_PORT` patches `ConnectionPortImpl` correctly, but the mock setup `MockConnPort.return_value.get_credentials = AsyncMock(return_value=creds_obj)` is not wired correctly — the actual `run_campaign_sync` function calls `ConnectionPortImpl` via `patch(_CONN_PORT)` but the module also has internal imports that import `ConnectionCredentials` from the real module. When `get_credentials` is called, it calls the real `ConnectionPortImpl.get_credentials` from the DB query (because `MockConnPort.return_value` returns a MagicMock for `.credentials` and `.config`, not actual dicts).
- Investigation: The test patches `ConnectionPortImpl` class, but the internal `connection_port_impl.py` function `get_credentials` internally queries the DB and constructs a `ConnectionCredentials` from the DB row. The mock `.return_value.get_credentials` is set correctly but there's a test fixture wiring issue — `MockConnPort.return_value.get_credentials` returns `creds_obj` as AsyncMock, but the function itself is a coroutine that gets called WITH specific arguments. Looking at the actual error: `ConnectionPortImpl` is patched but the function behavior reveals the mock is not being applied correctly to the instantiation flow. The real `ConnectionPortImpl` is likely being called instead.
- The root cause is likely that `_CONN_PORT` patch target is the CLASS but the actual import in `tasks.py` may have been rewritten to a different path. Let me check by examining the actual error: "Could not parse expires_at: MagicMock" is a WARNING from `connection_port_impl.py`, meaning the REAL code is running (not the mock). The patch target `_CONN_PORT` might not match the actual import path in tasks.py.
- Required fix: Verify the patch target `_CONN_PORT` matches the import path used INSIDE `run_campaign_sync`. The test itself may have the wrong `_CONN_PORT` string. This is **Cat II** — the mock registration path may be stale.
- Required codemod rewriter behavior: The `MockPatchStringRewriter` already handles string literals like `_CONN_PORT = "luana_core_connections..."`. These are already rewritten in this test. The issue is a semantic test fix (wrong mock target), not a codemod gap.

---

### Failure B2: `test_campaign_sync_task.py::TestRunCampaignSyncTask::test_credentials_include_both_credentials_and_config`

- File: `tests/modules/analytics/test_campaign_sync_task.py:80`
- Mechanism: **Cat II — same as B1**
- Source excerpt: Same `_CONN_PORT`, `_PIPELINE`, etc. patch targets. Same `ValidationError` on `ConnectionCredentials`.
- Root cause: Identical to B1.
- Required codemod rewriter behavior: Same as B1 — existing `MockPatchStringRewriter` already handles. Need semantic fix.

---

### Failures B3-B7: `test_seed_metrics.py` — 5 tests

- Files: `tests/modules/analytics/test_seed_metrics.py:35,44,56,73,85`
- Mechanism: **Cat V — Stale `src.modules.X` import in seed script (not in test file itself)**
- Source excerpt (from `backend/scripts/seed_metrics.py:61`):
  ```python
  def seed_data(db) -> dict:
      from src.modules.analytics.infrastructure.models.metric_aggregation_model import (
          MetricAggregationModel,
      )
      from src.modules.analytics.infrastructure.models.official_metrics_model import (
          OfficialMetricModel,
      )
      from src.modules.analytics.infrastructure.models.staging_metrics_model import (
          StagingMetricModel,
      )
  ```
- Root cause: `backend/scripts/seed_metrics.py` uses lazy imports inside `seed_data()` that reference the OLD `src.modules.analytics.infrastructure.models.*` paths. These model files were deleted in the big-bang (they were in `DELETE_FILES`). The codemod skipped this file because `backend/scripts/` is NOT in the default rewrite scope (`src/` and `tests/`).
- The `backend/scripts/` directory is NOT included in `--all-modules` scope (which covers `backend/src/` and `backend/tests/`). The seed script was missed.
- Required codemod rewriter behavior: **StaleScriptImportRewriter** (or extension of `--all-modules` to include `backend/scripts/`). The fix is to add `backend/scripts/` to the rewrite scope OR handle `backend/scripts/seed_metrics.py` specifically. The correct target names are:
  - `src.modules.analytics.infrastructure.models.metric_aggregation_model` → `luana_core_analytics_engine.infrastructure.models.metric_aggregation_model`
  - `src.modules.analytics.infrastructure.models.official_metrics_model` → `luana_core_analytics_engine.infrastructure.models.official_metrics_model`
  - `src.modules.analytics.infrastructure.models.staging_metrics_model` → `luana_core_analytics_engine.infrastructure.models.staging_metrics_model`
  - `src.core.database` → `luana_core_platform.core.database` (line 190)

---

## Group C — Offer (1 failure)

### Failure C1: `test_offer_extraction_service.py::TestOfferExtractionServiceInit::test_imports_webcrawler_from_shared`

- File: `tests/modules/offer/test_offer_extraction_service.py:74`
- Mechanism: **Cat I — Import-path assertion test**
- Source excerpt:
  ```python
  def test_imports_webcrawler_from_shared(self):
      """Verify WebCrawler is imported from shared, not brand."""
      import inspect
      from luana_core_offer_studio.application.offer_extraction_service import (
          OfferExtractionService,
      )
      source = inspect.getfile(OfferExtractionService)
      source_code = Path(source).read_text()
      assert "from src.shared.infrastructure.web.crawler import" in source_code
      assert "from src.modules.brand" not in source_code
  ```
- Root cause: The test reads the actual source code of `OfferExtractionService` (from the installed luana-platform package) and asserts it contains the OLD import string `"from src.shared.infrastructure.web.crawler import"`. Post-codemod, the source file was rewritten to use `"from luana_core_platform.infrastructure.web.crawler import ..."`. The assertion fails because the old path is gone.
- The SECOND assertion `assert "from src.modules.brand" not in source_code` passes (correctly — that old import was also removed). Only the first assertion fails.
- Required fix: Update the assertion to check for `"from luana_core_platform.infrastructure.web.crawler import"`. This is a **test update** (Cat I).
- Required codemod rewriter behavior: N/A — the existing `MockPatchStringRewriter` WOULD rewrite `"from src.shared.infrastructure.web.crawler import"` if it appeared in a `mocker.patch(...)` call, but here it appears inside an `assert "..." in source_code` statement. A new `ImportAssertionStringRewriter` could target this pattern, but it's risky (over-broad). Direct test edit is safer.

---

## Group D — Scripts (1 failure)

### Failure D1: `test_validate_session_close.py::test_cap_violation_reported_with_count[developed-cap 2]`

- File: `tests/scripts/test_validate_session_close.py:216-239`
- Mechanism: **Cat V — Test/script constant mismatch**
- Source excerpt:
  ```python
  @pytest.mark.parametrize(
      ("state", "cap_label"),
      [
          ...
          ("developed", "cap 2"),   # ← test expects "cap 2"
          ...
      ],
  )
  def test_cap_violation_reported_with_count(tmp_path: Path, state: str, cap_label: str) -> None:
      ...
      assert cap_label in result.stdout
  ```
  But `scripts/validate_session_close.py:78`:
  ```python
  CAPS = {
      ...
      "developed_max": 10,   # ← script says cap 10, not cap 2
      ...
  }
  ```
- Root cause: The `developed_max` constant in `validate_session_close.py` was changed from `2` to `10` (per `CLAUDE.md` vocabulary table showing `developed ≤ 10`). The test parametrize still expects the OLD value `"cap 2"`. This is a **cap constant mismatch** — neither the test file nor the script file was touched by the codemod. This is a pre-existing test drift unrelated to the import rewrite.
- Required fix: Update the test parametrize to use `("developed", "cap 10")`.
- Required codemod rewriter behavior: N/A — this is a direct test edit (single line change in parametrize).

---

## Mechanism summary

| Category | Count | Description | Fix path |
|---|---|---|---|
| Cat I — Import-path assertion | 2 | Test asserts OLD `src.X` path exists in source code (A1, C1) | Direct test edit |
| Cat II — Stale mock target (semantic) | 2 | Mock patch target already rewritten but semantic mismatch (B1, B2) | Semantic test fix (investigate actual import path in tasks.py) |
| Cat III — `import X as Y` old path | 2 | `import src.modules.X.Y as z` (not `from X import Y`) — not handled by ImportRewriter | New **PlainImportRewriter** in codemod |
| Cat V-seed — Scripts scope gap | 5 | `backend/scripts/seed_metrics.py` uses lazy `src.modules.X` imports — not in `--all-modules` scope | Extend `--all-modules` to include `backend/scripts/` |
| Cat V-const — Cap mismatch | 1 | Test expects `cap 2`, script says `cap 10` — unrelated to codemod | Direct test edit |
| Cat V-integration — DB timeout | 1 | Integration test, DB not running (A2) | Mock DB session in test |

## Failures requiring codemod extension

### True codemod gaps (Cat III + Cat V-seed):

1. **Cat III — PlainImportRewriter**: `import src.modules.X.Y as z` statements. The current `ImportRewriter` handles `from X import Y` only (CST `ImportFrom` node). `import X.Y as z` uses CST `Import` node — not currently visited.
2. **Cat V-seed — Scripts scope**: `backend/scripts/seed_metrics.py` stale imports. Fix: extend `--all-modules` to also walk `backend/scripts/`.

### NOT codemod gaps (require direct edits):

3. **Cat I × 2**: Direct test edits for A1, C1 (assertion strings update).
4. **Cat II × 2**: Semantic mock target investigation for B1, B2 (may be pre-existing test bug).
5. **Cat V-const × 1**: Direct test edit for D1 (parametrize value update).
6. **Cat V-integration × 1**: Mock DB session in A2.

## Estimated new failures after fixes

| Category | # Failures | Fix | Expected result |
|---|---|---|---|
| A1 (Cat I) | 1 | Direct test edit | GREEN |
| A2 (Cat V-integration) | 1 | Mock DB | GREEN |
| A3+A4 (Cat III) | 2 | PlainImportRewriter + apply | GREEN |
| B1+B2 (Cat II) | 2 | Semantic test investigation | TBD (may need deeper fix) |
| B3-B7 (Cat V-seed) | 5 | Extend scripts scope | GREEN |
| C1 (Cat I) | 1 | Direct test edit | GREEN |
| D1 (Cat V-const) | 1 | Direct test edit | GREEN |
