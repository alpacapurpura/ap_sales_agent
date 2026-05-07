# T-1 Implementation Log — Schema + Loader + Dialect Catalog + Tests baseline

> Story: eval-foundation-tenant-seed-data
> Ticket: T-1 (1 of 4)
> Builder: claude-sonnet (builder-backend)
> Date: 2026-05-06

## Skills Consulted

- `backend-expert` — invoked Step 0 SOP routing. Loaded `runtime-quality-checklist.md` before commit. Confirmed: no FastAPI/SQLA patterns in scope (test infrastructure only, no routes/session/DTOs).
- `brand-expert` — invoked to understand PersonalityProfile structure. Decision: validate brand YAML against BrandSettings (extra="ignore"), validate personality sub-models (PersonalityDimensions, LinguisticPatterns, SampleExchange) without UUID-required top-level PersonalityProfile.
- `offer-expert` — invoked to understand offer ladder structure. Decision: OfferLadder is test-infra only (no runtime Pydantic model for offer ladder at the YAML level). Use simple dict-based OfferLadderContext dataclass with `has_lead_magnet` property.
- `offer-type-preset-expert` — skipped (no preset catalog changes in T-1 scope).
- `metrics-expert` — skipped (no analytics changes).
- `tessl__fastapi` — loaded. Noted: no FastAPI routes in T-1 (test infra only). Confirmed `response_model=` not applicable here.
- `tessl__pytest-api-testing` — loaded for conftest.py fixture scoping, parametrize patterns, and structlog.testing.capture_logs usage. Decision: use pytest_generate_tests hook only for archetype_slug x yaml_filename combinations (realism smoke); standalone parametrize for single-dimension tests.
- `tessl__graceful-degradation` — skipped (no external HTTP calls in loader or tests).

## Faithfulness gap note (§11 from CONTEXT-BRIEF.md)

MEDIUM gap cited: `docs/product/modules/sales-agent.md` not found. Non-blocking per validator. Loader.py correctly avoids importing from `modules/sales_agent/` (per 05-guidelines.md restriction).

## Decision log

- AD2 enforcement: `test_schema_alignment.py` imports brand models read-only. BrandSettings uses `extra="ignore"` so seed YAMLs don't need all fields. PersonalityProfile top-level has required UUID fields (id, tenant_id) — we validate sub-models (dimensions, linguistic_patterns, sample_exchanges) instead to avoid fixture-bootstrapping complexity.
- AD3: `TenantContext` and `OfferLadderContext` are `@dataclass(frozen=True)` — test infra only. NOT exported from src/.
- AD4: `dialect_code` read from `personality_profile.yaml` top-level field (not a runtime Pydantic field). Falls back to `ARCHETYPE_DIALECT_MAP` if absent.
- AD6: Missing L0 → `structlog.warning("offer_ladder_missing_lead_magnet", ...)` + `has_lead_magnet=False`.
- AD7: `dialect_catalog.yaml` 15 entries, SSoT. All 5 archetype dialect codes present.
- AD9: Zero src/ changes. Verified via `git diff --name-only HEAD -- backend/src/`.
- REPO_ROOT pattern from test_pre_commit_hook.py: `Path(__file__).resolve().parents[N]`. For loader.py in `tests/fixtures/eval/tenants/`, `parents[0]` = tenants dir, used as `_THIS_DIR`.
- `structlog.testing.capture_logs()` used in test_loader.py for warning capture (confirmed: works with structlog's testing module, not caplog).
- `conftest.py pytest_generate_tests` only activates when BOTH `archetype_slug` AND `yaml_filename` are in fixturenames (avoids duplicate parametrization conflict with @pytest.mark.parametrize).

## Files created

| File | Lines | Status |
|------|-------|--------|
| `tests/fixtures/eval/tenants/__init__.py` | 7 | NEW |
| `tests/fixtures/eval/tenants/conftest.py` | 63 | NEW |
| `tests/fixtures/eval/tenants/loader.py` | ~255 | NEW |
| `tests/fixtures/eval/tenants/dialect_catalog.yaml` | 62 | NEW |
| `tests/fixtures/eval/tenants/test_loader.py` | ~145 | NEW |
| `tests/fixtures/eval/tenants/test_realism_smoke.py` | ~65 | NEW |
| `tests/fixtures/eval/tenants/test_schema_alignment.py` | ~100 | NEW |
| `tests/fixtures/eval/tenants/test_dialect_catalog.py` | ~80 | NEW |

## Tests output verbatim

### test_dialect_catalog.py — 4/4 GREEN

```
collected 4 items
tests/fixtures/eval/tenants/test_dialect_catalog.py::test_each_entry_has_required_fields PASSED
tests/fixtures/eval/tenants/test_dialect_catalog.py::test_invalid_dialect_code_raises PASSED
tests/fixtures/eval/tenants/test_dialect_catalog.py::test_catalog_has_min_13_entries PASSED
tests/fixtures/eval/tenants/test_dialect_catalog.py::test_catalog_contains_all_archetype_dialects PASSED
4 passed, 1 warning in 10.87s
```

### test_loader.py — 1/22 GREEN (expected RED baseline)

```
21 failed, 1 passed, 1 warning
PASSED: test_loader_raises_on_missing_archetype_slug
FAILED (all others): FileNotFoundError: Tenant directory not found (no YAMLs yet)
```

### test_schema_alignment.py — 1/16 GREEN (15 SKIPPED until T-3)

```
1 passed, 15 skipped, 1 warning
PASSED: test_loader_raises_on_missing_required_field
SKIPPED (15): Seed YAML not yet created — Unblocked by T-3
```

### test_realism_smoke.py — 30 tests collected (RED until T-3)

```
30 tests collected, 0 run (collected-only verified)
```

### Architecture fitness — 827/827 GREEN

```
827 passed, 1 warning in 26.15s (no regressions)
```

## RED tests confirmed (T-3 unblocks)

The following tests are intentionally RED in T-1 and will turn GREEN in T-3 when the 30 seed YAML files are created:

- `test_loader.py::test_loads_all_5_archetype_slugs[*]` (5 parametrized cases)
- `test_loader.py::test_dialect_code_per_archetype_matches_table[*]` (5 cases)
- `test_loader.py::test_offer_ladder_no_lead_magnet_emits_warning_proceeds_load`
- `test_loader.py::test_buyer_personas_count_3_per_tenant[*]` (5 cases)
- `test_loader.py::test_pricing_currency_pen_for_all[*]` (5 cases)
- `test_realism_smoke.py::test_yaml_has_min_nonnull_fields[*]` (30 cases — all FAIL with FileNotFoundError)
- `test_schema_alignment.py::test_brand_yaml_validates_against_brand_settings[*]` (5 SKIPPED)
- `test_schema_alignment.py::test_personality_profile_yaml_validates_sub_models[*]` (5 SKIPPED)
- `test_schema_alignment.py::test_offer_ladder_yaml_has_offers_list[*]` (5 SKIPPED)

## Acceptance verification

- A1: PASS — `load_eval_tenant`, `@dataclass(frozen=True)`, `has_lead_magnet` all present in loader.py
- A2: PASS — dialect_catalog.yaml has 15 entries; all archetype dialect codes present; required fields validated
- A3: PASS — 22 tests running (21 FAILED + 1 PASSED in test_loader.py) — RED baseline confirmed
- A4: PASS — ruff lint 0 errors, format 0 diff
- A5: PASS — `git diff HEAD -- backend/src/ frontend/src/ | wc -l` = 0

## Iteration log

- Iter 1: Created all 8 files.
- Iter 1 fix: Ruff lint caught 16 issues (EM102 f-strings in exceptions, TRY003 long messages, RUF002 × symbol, RUF043 unescaped regex, RUF100 unused noqa, B007 unused loop var, PLR1714 merge comparisons). All fixed.
- Iter 1 fix: conftest.py `pytest_generate_tests` caused duplicate parametrization conflict. Fixed to only activate when BOTH `archetype_slug` AND `yaml_filename` in fixturenames.
- Final: All validators pass.
