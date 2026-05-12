---
story_id: luana-copilot-engine
ticket: T-7
owner: builder-agentic (claude-opus-4-7)
started_at: 2026-05-11
completed_at: 2026-05-11
status: GREEN
---

# T-7 — Lift copilot infrastructure persisters (5 files)

## Skills consulted
- `copilot-expert` — persister registry pattern (F0-F11 baseline)
- `tessl__pytest-api-testing` — patch string-literal handling for unittest.mock

## Scope
Lift `infrastructure/persisters/` (5 files: brand_persister + buyer_persona_persister + offer_persister + persister_registry + __init__) verbatim per 05-guidelines.md §1.3.

### Source (AISALESHT — READ-ONLY)
- `backend/src/modules/copilot/infrastructure/persisters/{__init__,brand_persister,buyer_persona_persister,offer_persister,persister_registry}.py`
- `backend/tests/modules/copilot/test_brand_persister.py + test_buyer_persona_persister.py + test_offer_persister.py` (3 of 4 — test_persister_registry.py absent)

### Target (luana-platform — CREATED)
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/persisters/` (5 files)
- `core/luana-core-copilot/tests/test_*_persister.py` (3 files)

## Execution

### Step 1 — cp -r lift
```bash
cp -r /home/chris/AISALESHT/backend/src/modules/copilot/infrastructure/persisters \
      core/luana-core-copilot/src/luana_core_copilot/infrastructure/
```

### Step 2 — sed substitutions
Applied per 05-guidelines.md §1.3 on both src/ and tests/. Plus targeted additional sed for string-literal mock paths (`patch("src.modules.brand...")` in test_brand_persister.py:37,60).

### Step 3 — Verification
- ✅ Zero `from src.*` / `import src.*` leaks
- ✅ Zero string-literal `"src.modules.*"` patches remaining (2 fixes in test_brand_persister.py)
- ✅ Class declarations preserved: `BrandPersister`, `BuyerPersonaPersister`, `OfferPersister`, `get_persister` function in registry
- ✅ Ruff check: 3 I001 (import order) auto-fixed (sed reorder)
- ✅ Ruff format check: 5 files already formatted

### Step 4 — Isolated test run
```bash
POSTGRES_USER=postgres ... (full env set) uv run pytest \
  core/luana-core-copilot/tests/test_brand_persister.py \
  core/luana-core-copilot/tests/test_buyer_persona_persister.py \
  core/luana-core-copilot/tests/test_offer_persister.py -x -q
```
**Result: 34 passed in 0.30s GREEN** (env vars required because conftest.py with `os.environ.setdefault(...)` lifts T-15 per ticket DAG; manual env supply confirms lift mechanically correct).

### String-literal sed gap discovered
Sed mapping in 05-guidelines.md §1.3 covers `from src.modules.*` / `import src.modules.*` but does NOT cover `"src.modules.*"` string literals used by `unittest.mock.patch("dotted.path")`. Detected 2 instances in `test_brand_persister.py`. Applied targeted sed:
```bash
sed -i 's|"src\.modules\.brand\.|"luana_core_brand_studio.|g' tests/test_brand_persister.py
```

**Recommendation for T-8 onward:** include patch-string sed variants in the standard substitution pass. Documented as guideline drift for /pm to incorporate into 05-guidelines.md §1.3 (or auditor catches and architects in next iteration).

## Anti-duplication
Persisters consume brand-studio + offer-studio domain aggregates. No mirrors. Per cross-module audit: existing pattern (persister → studio domain → infrastructure write) preserved.

## D-T1 / D-T6 / [COPILOT-*]
- D-T1: no registry public APIs touched
- D-T6: no callback handler / turn envelope (lift T-13)
- Anchors: 0 in persisters layer (anchors in orchestrator/domain)

## Files touched
### Created
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/persisters/__init__.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/persisters/brand_persister.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/persisters/buyer_persona_persister.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/persisters/offer_persister.py`
- `core/luana-core-copilot/src/luana_core_copilot/infrastructure/persisters/persister_registry.py`
- `core/luana-core-copilot/tests/test_brand_persister.py`
- `core/luana-core-copilot/tests/test_buyer_persona_persister.py`
- `core/luana-core-copilot/tests/test_offer_persister.py`

### Modified
None.

## Validators addressed
- V-NF-2 (pyproject 0.0.6-alpha preserved)

## Verdict
done — Persisters lifted GREEN. 34/34 tests PASS with env vars supplied (conftest.py env defaults land T-15).
