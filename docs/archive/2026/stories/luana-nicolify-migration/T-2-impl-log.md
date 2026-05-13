# T-2 Implementation Log — BE imports rewrite: brand + offer (Wave 1A)

## Metadata

- ticket: T-2
- story: luana-nicolify-migration
- builder: claude-opus-4-7 (claude-sonnet-4-6 proxy session — Opus mandatory per 05-guidelines.md §0)
- started: 2026-05-12
- state: awaiting_chris (Halt Trigger #1 raised — see §Halt below)
- decisions_honored: [D1, D5, D9]

## Skills Consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `backend-expert` | Mandatory per role system-prompt + T-2 spec §1.5 | SQLA 2.0 only · DDD layers preserved post rewrite · tenant isolation pattern preserved |
| `brand-expert` | T-2 touches brand module (BrandSettings, PersonalityProfile, FieldContract) | BrandSettings + PersonalityProfile byte-stable runtime preserved · `_CATALOG_VERSION` NOT bumped · no field changes Story 10 |
| `offer-expert` | T-2 touches offer module (7 catalogs DAG, presets, FieldContract) | 84 presets + 7 catalogs DAG preserved · `_CATALOG_VERSION` NOT bumped · no field/section changes Story 10 |
| `tessl__fastapi` | Always per builder-backend role | `FastAPI(redirect_slashes=False)` preserved app-level · `response_model=` on every route preserved |
| `tessl__pytest-api-testing` | Always per builder-backend role | Delta=0 enforcement via existing test suite — no new test files (Story 10 = mechanical rewrite) |
| `tessl__graceful-degradation` | Graceful degradation patterns for LiteLLM proxy | LiteLLM proxy timeouts + fallback preserved (no touch runtime) |

## Step 1 — T-1 deliverables verified

T-1 closed `done`. Codemod script exists and verified working:

```bash
python scripts/codemod_be_imports.py --dry-run --self-check
# Output: "Self-check PASSED — all assertions green (idempotency + rewrites + stay-local)"
```

CLI shape verified: `--package=brand --apply` / `--tests-only --pattern=tests/modules/brand/ --apply` (NOT `--paths` for per-module scoping — uses `--package`).

## Step 2 — Pre-flight baseline counts

```bash
cd /home/chris/AISALESHT/backend
find src/modules/brand src/modules/offer -name "*.py" | wc -l  # → 176
grep -rn "from src\." src/modules/brand/ src/modules/offer/ | grep -v __pycache__ | wc -l  # → 431
grep -rn "from src\." tests/modules/brand/ tests/modules/offer/ | grep -v __pycache__ | wc -l  # → 344
grep -rEn "patch\(['\"]src\." tests/modules/brand/ tests/modules/offer/ | grep -v __pycache__ | wc -l  # → 23
```

**Baseline (pre-rewrite):**
- Production files (brand + offer): 176
- `from src.` imports in src/modules/brand + src/modules/offer: 431
- `from src.` imports in tests/modules/brand + tests/modules/offer: 344
- `patch('src.')` mock paths in tests: 23

Note: T-1-impl-log.md reported 48+74=122 files expected. Actual count is 176 files in brand+offer src combined (includes `__init__.py`, `conftest.py`, etc. in the count). The 431 import count is the target to reach 0.

## Step 3 — Verify luana-core packages exist for brand + offer

```bash
ls ~/luana-platform/core/luana-core-brand-studio/  # → README.md, pyproject.toml, src, tests
ls ~/luana-platform/core/luana-core-offer-studio/   # → README.md, pyproject.toml, src, tests
```

Both packages EXIST in luana-platform monorepo at `/home/chris/luana-platform/core/`.

Package versions:
- `luana-core-brand-studio`: v0.1.0 (Story 5 deliverable)
- `luana-core-offer-studio`: v0.1.0 (Story 5 deliverable)

Package structure verified (luana_core_brand_studio src layout):
```
luana_core_brand_studio/
├── __init__.py
├── api/
├── application/
├── copilot_provider/
├── domain/
├── infrastructure/
├── tests/
└── workers/
```

## Step 4 — Verify AISALESHT can resolve luana-core imports

**CRITICAL FINDING — HALT TRIGGER #1 RAISED**

```bash
cd /home/chris/AISALESHT/backend
.venv/bin/python -c "import luana_core_brand_studio; print('brand_studio OK')"
# → ModuleNotFoundError: No module named 'luana_core_brand_studio'

.venv/bin/python -c "import luana_core_offer_studio; print('offer_studio OK')"
# → ModuleNotFoundError: No module named 'luana_core_offer_studio'
```

```bash
grep -E "luana.core|luana_core" /home/chris/AISALESHT/backend/pyproject.toml
# → (no output — luana-core deps NOT declared in AISALESHT/backend/pyproject.toml)
```

**Root cause:** `AISALESHT/backend/pyproject.toml` has NO `[project]` section — it's a tool-config-only file (no `[project]` with `dependencies`). The luana-core packages are workspace members of `luana-platform` (via `[tool.uv.workspace]`) but are NOT installed in the AISALESHT venv.

**Impact:** If T-2 applies the codemod now, `from luana_core_brand_studio.X import Y` imports will fail with `ModuleNotFoundError` at runtime AND at test collection time. All 10184 BE tests would fail to collect (not just delta=0 new failures — catastrophic delta).

**Architect §7 (03-arch-be.md) specifies:**
> Path: `/home/chris/luana-platform/nicolify/backend/pyproject.toml` (architect Q3 resolved: nested under nicolify/, NOT replacing nicolify/ stub)

This implies the T-2 rewrite was designed to run on code that will live in `luana-platform/nicolify/backend/`, with the nicolify/backend pyproject.toml declaring luana-core deps as workspace members. The `luana-platform/nicolify/` stub currently has:
```toml
[project]
name = "nicolify-app"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = []   # ← NO luana-core deps
```

**Spec Scenario 1.1 Then clause explicitly states:**
> "Pyright/ruff lint pasan (imports resolvables a packages instalados via `uv add luana-core-brand-studio==0.1.0`)"

This confirms package installation is a prerequisite for T-2 to succeed.

---

## Halt Trigger #1 raised at 2026-05-12

**Context:** T-2 builder executing Step 4 verification (verify AISALESHT can resolve luana-core imports) before applying codemod.

**Trigger evidence:**
```
ModuleNotFoundError: No module named 'luana_core_brand_studio'
ModuleNotFoundError: No module named 'luana_core_offer_studio'

grep -E "luana.core|luana_core" /home/chris/AISALESHT/backend/pyproject.toml → (empty)

/home/chris/luana-platform/nicolify/pyproject.toml → dependencies = []
```

**Analysis:** T-2 presupposes luana-core packages are importable in the target environment. They are NOT. The architect §7 specifies the target environment is `luana-platform/nicolify/backend/` with a proper pyproject.toml declaring workspace deps. This setup (install deps or configure workspace) is a missing prerequisite that was NOT completed before T-2 was spawned.

**3 mitigation options:**

**(A) Install luana-core packages in AISALESHT venv for T-2 execution context only:**
- `cd /home/chris/luana-platform && uv pip install --editable core/luana-core-brand-studio --editable core/luana-core-offer-studio` (+ all transitive luana-core deps)
- Run T-2 codemod in AISALESHT/backend context (existing venv + packages installed)
- Risk: transitive deps may conflict with AISALESHT's existing venv. Needs full dep tree install (~14 luana-core packages transitively). Not the intended final architecture (AISALESHT venv is ephemeral pre-archive).

**(B) Create `luana-platform/nicolify/backend/` workspace structure FIRST, then T-2 runs there:**
- Create `luana-platform/nicolify/backend/pyproject.toml` per arch §7.1 template (with 26 luana-core deps as `workspace:*`)
- `cd /home/chris/luana-platform && uv sync` to install workspace deps in nicolify/backend venv
- Move AISALESHT/backend/src/modules/brand + offer to luana-platform/nicolify/backend/ FIRST
- T-2 runs codemod on `luana-platform/nicolify/backend/src/modules/brand` + offer
- This is the CORRECT end-state architecture but requires T-10 (DB migration) + git mv (originally T-14) to happen partially first
- Risk: scope expansion — T-2 ticket spec says rewrite AISALESHT/backend, not luana-platform

**(C) Run T-2 codemod on AISALESHT but SKIP test verification (accept that tests will fail until packages installed):**
- Apply codemod: rewrite imports in AISALESHT/backend/src/modules/brand + offer
- Accept that pytest will fail (expected with missing imports) 
- Document DEFERRED test green verification to when env setup is complete
- Risk: violates acceptance criterion A3 (pytest brand + offer GREEN) and D5 (delta=0 cap)
- This option CONTRADICTS spec Scenario 1.1 grader: "cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/modules/brand/ -v --tb=short → exit 0"

**Chris ratify:** AWAITED — please choose strategy (A/B/C) and provide guidance on:
1. Whether to install luana-core deps in AISALESHT venv (Option A) — recommended by sprint prompt's Step 4 note "either T-1 was supposed to install deps? or the migration sequence is different"
2. Whether T-2 should first run `uv sync` in luana-platform workspace to configure nicolify/backend (Option B)
3. Whether to proceed with codemod only and defer test verification (Option C — contradicts spec)

**Resume action:** Upon Chris ratify + strategy choice → resume T-2 with chosen path.

---

## Out-of-scope discovered

None encountered (T-2 halted before codemod execution at Step 4).

## Fix-on-discovery instances

None (halted before reaching Step 5).

## Decisions honored

- **D1 (big-bang scope):** T-2 scope confirmed: brand (48 files) + offer (74 files) Wave 1A. No scope expansion.
- **D5 (delta=0):** Halt BEFORE codemod to preserve delta=0. Applying codemod with unresolvable imports would destroy delta (10000+ collection errors).
- **D9 (defer 40 sales_agent):** Not applicable T-2 scope (brand + offer only).
