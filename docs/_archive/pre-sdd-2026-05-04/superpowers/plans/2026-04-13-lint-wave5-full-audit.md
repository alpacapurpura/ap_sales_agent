# Wave 5: Lint Full Audit-Ready Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Activate FAST, E501, ANN, and D ruff categories — bringing the project from 49 to 53 active categories with 0 violations and full type annotation + docstring coverage in src/.

**Architecture:** Four independent phases executed sequentially. Each phase: activate rule → fix violations → verify → commit. Agents fix code in parallel by module, pyproject.toml is edited ONLY at the end of each phase (never by agents).

**Tech Stack:** ruff 0.11+, Python 3.11, FastAPI, Pydantic v2, structlog

**Decisions made:**
- E501: line-length raised from 88 → 120 (eliminates 93% of violations)
- ANN: src/ only — tests exempt via per-file-ignores
- D: format fixes + missing docstrings in src/ — tests exempt

---

## Critical execution rules (learned from Wave 4)

1. **NEVER `git stash`** during a wave execution — it reverts agent changes
2. **pyproject.toml edits go LAST** in each phase — agents overwrite it if they read it
3. **Every agent prompt MUST include:** "CRITICAL: DO NOT modify pyproject.toml. Only modify source code files."
4. **Verify BEFORE commit:** `ruff check + ruff format --check + pytest`
5. **One commit per phase** — clean git history
6. **Run from `backend/` directory:** `cd /home/chris/AISALESHT/backend`
7. **All commands native:** `.venv/bin/ruff`, `.venv/bin/pytest` — never Docker

---

## Pre-flight check

Before starting ANY phase, run:

```bash
cd /home/chris/AISALESHT/backend
git status --short && git branch --show-current && git log --oneline -3
.venv/bin/ruff check src/ tests/ --no-cache
.venv/bin/pytest -x -q --tb=short
```

Expected: clean working tree, `development` branch, 0 ruff violations, 2264+ tests passing.

---

## Phase 1: E501 — Line Length (88 → 120)

**Violations:** 853 at 88 → 59 at 120
**Strategy:** Change line-length, auto-format, fix 59 remaining manually
**Estimated time:** 30 minutes

### Task 1.1: Raise line-length and auto-format

**Files:**
- Modify: `pyproject.toml` (line-length setting)

- [ ] **Step 1: Change line-length in pyproject.toml**

In `[tool.ruff]` section, change:
```toml
line-length = 120
```

- [ ] **Step 2: Run ruff format to reflow all files**

```bash
.venv/bin/ruff format src/ tests/
```

Expected: many files reformatted (lines that were broken at 88 will be joined up to 120).

- [ ] **Step 3: Add E501 to select in pyproject.toml**

In the `select` list, add after the Wave 4 rules:
```toml
    # --- Wave 5 ---
    "E501",                    # line-too-long (line-length=120)
```

- [ ] **Step 4: Check remaining E501 violations**

```bash
.venv/bin/ruff check src/ tests/ --select E501 --no-cache --statistics
```

Expected: ~59 remaining violations (long strings, URLs, data structures).

### Task 1.2: Fix remaining E501 violations

**Files:** ~30 source files with lines >120 chars

- [ ] **Step 1: List the remaining violations**

```bash
.venv/bin/ruff check src/ tests/ --select E501 --no-cache --output-format=concise
```

- [ ] **Step 2: Dispatch agent to fix**

Prompt for agent:
```
Fix all E501 (line-too-long, max 120 chars) violations in /home/chris/AISALESHT/backend.
Run: cd /home/chris/AISALESHT/backend && .venv/bin/ruff check src/ tests/ --select E501 --no-cache --output-format=concise

For each line >120 chars:
- Long strings: break into multi-line with parentheses or implicit concat
- Long imports: break into multi-line import
- Long function signatures: one param per line
- Long dict/list literals: one entry per line
- URLs in comments: add # noqa: E501
- Data structures (metric_catalog, navigation_map): add # noqa: E501

CRITICAL: DO NOT modify pyproject.toml. Only modify source code files.

After fixing: .venv/bin/ruff check src/ tests/ --select E501 --no-cache → 0 violations.
```

- [ ] **Step 3: Verify all checks pass**

```bash
.venv/bin/ruff check src/ tests/ --no-cache
.venv/bin/ruff format --check src/ tests/
.venv/bin/pytest -x -q --tb=short
```

Expected: 0 violations, format clean, all tests pass.

- [ ] **Step 4: Commit**

```bash
git add backend/pyproject.toml backend/src/ backend/tests/
git commit -m "refactor: Wave 5 Phase 1 — E501 line-length 88→120, 853 fixes

- Raised line-length from 88 to 120 (industry standard for FastAPI)
- Auto-formatted all files via ruff format
- Fixed 59 remaining long lines manually
- Activated E501 rule enforcement

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Phase 2: FAST — FastAPI Annotated Migration

**Violations:** 787 (756 FAST002 + 31 FAST001)
**Strategy:** Auto-fix 603 with `--unsafe-fixes`, fix remaining ~153 manually, handle FAST001 separately
**Estimated time:** 1-2 hours

### Understanding the violations

- **FAST002 (756):** `db: Session = Depends(get_db)` should be `db: Annotated[Session, Depends(get_db)]`
  - 603 auto-fixable with `--unsafe-fixes`
  - 153 require manual fix (complex default values, nested Depends)
- **FAST001 (31):** Endpoint has both return type annotation AND `response_model=` — redundant
  - Fix: remove `response_model=` when return annotation matches

### FAST002 distribution by module (for parallel agents)

| Module | Count | Agent batch |
|--------|-------|-------------|
| connections | 212 | Agent A |
| offer | 135 | Agent B |
| analytics | 113 | Agent C |
| copilot (45) + sales_agent (38) + brand (37) | 120 | Agent D |
| crm (33) + iam (28) + advertising (24) | 85 | Agent E |
| scheduling (22) + landing (22) + assets (18) + commercial_calendar (15) + tenant_domains (14) | 91 | Agent F |

### Task 2.1: Auto-fix FAST002 with ruff

- [ ] **Step 1: Run ruff auto-fix for FAST002**

```bash
.venv/bin/ruff check src/ --select FAST002 --no-cache --fix --unsafe-fixes
```

Expected: ~603 auto-fixed. Note how many remain.

- [ ] **Step 2: Run ruff format to clean up any formatting changes**

```bash
.venv/bin/ruff format src/
```

- [ ] **Step 3: Count remaining FAST002**

```bash
.venv/bin/ruff check src/ --select FAST002 --no-cache --statistics
```

Expected: ~153 remaining (complex signatures that auto-fix couldn't handle).

### Task 2.2: Fix remaining FAST002 manually (parallel agents)

- [ ] **Step 1: Dispatch parallel agents by module batch**

For each agent batch (A through F), use this prompt template:

```
Fix all remaining FAST002 violations in /home/chris/AISALESHT/backend/{module_paths}.

Run: cd /home/chris/AISALESHT/backend && .venv/bin/ruff check {module_paths} --select FAST002 --no-cache --output-format=concise

The pattern is:
# WRONG:
def endpoint(db: Session = Depends(get_db)):

# CORRECT:
from typing import Annotated
def endpoint(db: Annotated[Session, Depends(get_db)]):

For parameters with Query/Header/Path/Body:
# WRONG:
def endpoint(page: int = Query(default=1)):
# CORRECT:
def endpoint(page: Annotated[int, Query(default=1)]):

For parameters with complex defaults that ruff couldn't auto-fix:
- Read the file to understand the parameter type
- Apply the Annotated pattern manually
- Make sure to add `from typing import Annotated` if not already imported

CRITICAL: DO NOT modify pyproject.toml. Only modify source code files.

After fixing: .venv/bin/ruff check {module_paths} --select FAST002 --no-cache → 0.
```

Module paths per agent:
- **Agent A:** `src/modules/connections/`
- **Agent B:** `src/modules/offer/`
- **Agent C:** `src/modules/analytics/`
- **Agent D:** `src/modules/copilot/ src/modules/sales_agent/ src/modules/brand/`
- **Agent E:** `src/modules/crm/ src/modules/iam/ src/modules/advertising/`
- **Agent F:** `src/modules/scheduling/ src/modules/landing/ src/modules/assets/ src/modules/commercial_calendar/ src/modules/tenant_domains/`

### Task 2.3: Fix FAST001 (redundant response_model)

**31 violations across 10 files.**

- [ ] **Step 1: Dispatch agent for FAST001**

```
Fix all FAST001 (redundant response_model) violations in /home/chris/AISALESHT/backend.

Run: cd /home/chris/AISALESHT/backend && .venv/bin/ruff check src/ --select FAST001 --no-cache --output-format=concise

FAST001 fires when an endpoint has BOTH a return type annotation AND response_model=.
The fix depends on which is correct:

Option A — If the return annotation matches response_model, remove response_model:
# BEFORE:
@router.get("/items", response_model=list[ItemDTO])
async def list_items() -> list[ItemDTO]:
# AFTER:
@router.get("/items")
async def list_items() -> list[ItemDTO]:

Option B — If they differ, keep response_model and remove/fix the return annotation:
# BEFORE:
@router.get("/items", response_model=list[ItemDTO])
async def list_items():
# AFTER (add return annotation to match):
@router.get("/items")
async def list_items() -> list[ItemDTO]:

IMPORTANT: The project has an architectural fitness test that requires ALL endpoints to have response_model.
Check: does the endpoint's arch test allowlist include it? If so, keep response_model AND add matching return type.
If NOT in the allowlist, prefer removing response_model and keeping the return annotation.

When in doubt: keep response_model AND add matching return annotation, then add # noqa: FAST001.

CRITICAL: DO NOT modify pyproject.toml. Only modify source code files.

After fixing: .venv/bin/ruff check src/ --select FAST001 --no-cache → 0.
```

### Task 2.4: Activate FAST and verify

- [ ] **Step 1: Add FAST to select in pyproject.toml**

```toml
    "FAST",                    # fastapi: Annotated dependencies
```

- [ ] **Step 2: Full verification**

```bash
.venv/bin/ruff check src/ tests/ --no-cache
.venv/bin/ruff format --check src/ tests/
.venv/bin/pytest -x -q --tb=short
```

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml backend/src/
git commit -m "refactor: Wave 5 Phase 2 — FAST Annotated migration, 787 fixes

- Migrated 756 FastAPI Depends/Query/Header/Body to Annotated[] pattern
- Fixed 31 redundant response_model declarations (FAST001)
- Activated FAST rule enforcement

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Phase 3: ANN — Type Annotations (src/ only)

**Violations:** 974 in src/ (tests exempt)
**Strategy:** Tests get per-file-ignores, src/ gets annotated by module via parallel agents
**Estimated time:** 2-3 hours

### ANN distribution by module

| Module | Count | Agent batch |
|--------|-------|-------------|
| sales_agent | 184 | Agent A |
| analytics | 175 | Agent B |
| connections | 151 | Agent C |
| copilot | 106 | Agent D |
| offer (63) + brand (53) | 116 | Agent E |
| crm (35) + iam (26) + scheduling (17) | 78 | Agent F |
| admin (35) + shared (20) + assets (16) + landing (13) + core (6) + advertising (9) + commercial_calendar (8) + workers (8) + tenant_domains (3) | 131 | Agent G |

### Task 3.1: Add ANN per-file-ignores for tests

- [ ] **Step 1: Note — this goes into pyproject.toml AT THE END of Phase 3**

Add to `tests/**/*.py` per-file-ignores:
```toml
    "ANN",     # type annotations not required in tests
```

Also add to `src/tests/**/*.py`.

### Task 3.2: Fix ANN violations via parallel agents

- [ ] **Step 1: Dispatch 7 parallel agents**

Use this prompt template for each agent:

```
Add missing type annotations to all Python files in /home/chris/AISALESHT/backend/{module_paths}.

Run: cd /home/chris/AISALESHT/backend && .venv/bin/ruff check {module_paths} --select ANN --no-cache --output-format=concise

Violation types and fixes:

ANN001 (missing arg type): Add type to function arguments
  def process(data):  →  def process(data: dict[str, Any]):

ANN002 (missing *args type): Add type to *args
  def func(*args):  →  def func(*args: Any):

ANN003 (missing **kwargs type): Add type to **kwargs
  def func(**kwargs):  →  def func(**kwargs: Any):

ANN201 (missing public return type): Add return type
  def get_name(self):  →  def get_name(self) -> str:

ANN202 (missing private return type): Add return type
  def _helper(self):  →  def _helper(self) -> None:

ANN204 (missing __init__ return): Add -> None
  def __init__(self, x):  →  def __init__(self, x: int) -> None:

ANN205 (missing staticmethod return): Add return type
ANN206 (missing classmethod return): Add return type

ANN401 (using Any): Replace with specific type if possible, or add # noqa: ANN401

RULES FOR CHOOSING TYPES:
- Read the function body to infer correct types
- FastAPI endpoints: check Pydantic DTOs for param/return types
- Repository methods: params are usually UUID, str, int; returns are Model | None or list[Model]
- Service methods: check what the repo returns and what the DTO expects
- Use `from __future__ import annotations` if needed for forward refs
- For genuinely dynamic types, use `Any` with `# noqa: ANN401 — dynamic type`
- Prefer specific types over Any: dict[str, str] not dict[str, Any]
- Use `from uuid import UUID` for tenant_id params
- Use `from sqlalchemy.orm import Session` for db params
- Use `-> None` for functions that don't return

CRITICAL: DO NOT modify pyproject.toml. Only modify source code files.

After fixing: .venv/bin/ruff check {module_paths} --select ANN --no-cache → 0.
```

Module paths per agent:
- **Agent A:** `src/modules/sales_agent/`
- **Agent B:** `src/modules/analytics/`
- **Agent C:** `src/modules/connections/`
- **Agent D:** `src/modules/copilot/`
- **Agent E:** `src/modules/offer/ src/modules/brand/`
- **Agent F:** `src/modules/crm/ src/modules/iam/ src/modules/scheduling/`
- **Agent G:** `src/admin/ src/shared/ src/modules/assets/ src/modules/landing/ src/core/ src/modules/advertising/ src/modules/commercial_calendar/ src/workers/ src/modules/tenant_domains/ src/main.py`

### Task 3.3: Activate ANN and verify

- [ ] **Step 1: Add ANN to select and per-file-ignores in pyproject.toml**

Add to select:
```toml
    "ANN",                     # type annotations (src/ only)
```

Add `"ANN"` to `tests/**/*.py` and `src/tests/**/*.py` per-file-ignores.

- [ ] **Step 2: Full verification**

```bash
.venv/bin/ruff check src/ tests/ --no-cache
.venv/bin/ruff format --check src/ tests/
.venv/bin/pytest -x -q --tb=short
```

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml backend/src/
git commit -m "refactor: Wave 5 Phase 3 — ANN type annotations, 974 fixes in src/

- Added type annotations to all functions/methods in src/ (974 violations)
- Tests exempt via per-file-ignores (3,888 test violations intentionally skipped)
- Activated ANN rule enforcement

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Phase 4: D — Docstrings (src/ only)

**Violations:** ~2,581 in src/ (tests exempt)
**Strategy:** Auto-fix format issues (464), then write docstrings by module via parallel agents
**Estimated time:** 3-4 hours

### Sub-phases

| Sub-phase | What | Count | Auto-fixable |
|-----------|------|-------|--------------|
| 4A | Format fixes (D200, D202, D205, D209, D212, D401, D413) | ~688 | Yes (464 auto, 224 manual) |
| 4B | Missing module/package docstrings (D100, D104) | ~429 | No — 1-line docstrings |
| 4C | Missing class docstrings (D101, D107) | ~668 | No — requires reading class |
| 4D | Missing function/method docstrings (D102, D103) | ~631 | No — requires reading function |

### Task 4.1: Configure pydocstyle and add test per-file-ignores

- [ ] **Step 1: Note — these go into pyproject.toml AT THE END of Phase 4**

Add to `[tool.ruff.lint]` section:
```toml
[tool.ruff.lint.pydocstyle]
convention = "google"
```

Add `"D"` to `tests/**/*.py` and `src/tests/**/*.py` per-file-ignores.

Add D106 (undocumented-public-nested-class) to global ignore:
```toml
    "D106",     # undocumented nested class — Pydantic Config, Meta classes
```

### Task 4.2: Auto-fix docstring format issues

- [ ] **Step 1: Run ruff auto-fix for D format rules**

```bash
.venv/bin/ruff check src/ --select D200,D202,D205,D209,D212,D401,D413 --no-cache --fix --unsafe-fixes
```

- [ ] **Step 2: Run ruff format**

```bash
.venv/bin/ruff format src/
```

- [ ] **Step 3: Check remaining format violations**

```bash
.venv/bin/ruff check src/ --select D200,D202,D205,D209,D212,D400,D401,D413,D415 --no-cache --statistics
```

Fix any remaining manually (D400 trailing period, D415 terminal punctuation, D401 imperative mood).

### Task 4.3: Write module/package docstrings (D100, D104)

**~429 violations: D100 (module docstrings) + D104 (package __init__.py docstrings)**

- [ ] **Step 1: Dispatch agent**

```
Add missing module and package docstrings to all Python files in /home/chris/AISALESHT/backend/src/.

Run: cd /home/chris/AISALESHT/backend && .venv/bin/ruff check src/ --select D100,D104 --no-cache --output-format=concise

D100: Every .py file needs a module docstring (first line of file).
D104: Every __init__.py needs a package docstring.

PATTERN FOR MODULE DOCSTRINGS:
"""Brief one-line description of what this module does."""

PATTERN FOR __init__.py:
"""Package name — brief description."""

RULES:
- Read the file content to understand its purpose
- Module docstring goes at the very top of the file (line 1), before any imports
- For __init__.py that only re-exports, use: """Module name package."""
- For __init__.py that are empty, use: """Module name package."""
- Keep it to ONE LINE when possible
- Use Google docstring convention (imperative mood): "Process X" not "Processes X"
- Language: English for technical modules, Spanish acceptable for user-facing strings

EXAMPLES BY LAYER:
- domain/models.py: """Brand domain model definitions."""
- infrastructure/repositories/brand_repository.py: """SQLAlchemy repository for brand persistence."""
- application/services/brand_service.py: """Brand service — orchestrates brand creation and updates."""
- api/router.py: """Brand API endpoints."""
- domain/__init__.py: """Brand domain package."""

CRITICAL: DO NOT modify pyproject.toml. Only modify source code files.

After fixing: .venv/bin/ruff check src/ --select D100,D104 --no-cache → 0.
```

### Task 4.4: Write class docstrings (D101, D107)

**~668 violations: D101 (class docstrings) + D107 (__init__ docstrings)**

- [ ] **Step 1: Dispatch parallel agents by module**

Use this prompt template:

```
Add missing class and __init__ docstrings to all Python files in /home/chris/AISALESHT/backend/{module_paths}.

Run: cd /home/chris/AISALESHT/backend && .venv/bin/ruff check {module_paths} --select D101,D107 --no-cache --output-format=concise

D101: Every public class needs a docstring.
D107: Every __init__ method needs a docstring.

PATTERN FOR CLASS DOCSTRINGS:
class BrandService:
    """Orchestrate brand CRUD operations and extraction workflows."""

PATTERN FOR __init__:
def __init__(self, db: Session, tenant_id: UUID) -> None:
    """Initialize with database session and tenant context."""

RULES:
- Read the class to understand its purpose
- ONE LINE for simple classes, multi-line for complex ones
- For Pydantic models/DTOs: """DTO for brand creation request."""
- For SQLAlchemy models: """SQLAlchemy model for the brands table."""
- For repositories: """Repository for brand persistence operations."""
- For services: """Service that orchestrates brand {purpose}."""
- For FastAPI routers: skip (they're module-level, not classes)
- Google convention: imperative mood
- D107 (__init__): can be skipped if the class docstring is sufficient — add # noqa: D107

CRITICAL: DO NOT modify pyproject.toml. Only modify source code files.

After fixing: .venv/bin/ruff check {module_paths} --select D101,D107 --no-cache → 0.
```

Agent distribution — same as Phase 3 (7 agents by module).

### Task 4.5: Write function/method docstrings (D102, D103)

**~631 violations: D102 (public methods) + D103 (public functions)**

- [ ] **Step 1: Dispatch parallel agents by module**

Use this prompt template:

```
Add missing function and method docstrings to all Python files in /home/chris/AISALESHT/backend/{module_paths}.

Run: cd /home/chris/AISALESHT/backend && .venv/bin/ruff check {module_paths} --select D102,D103 --no-cache --output-format=concise

D102: Every public method needs a docstring.
D103: Every public function needs a docstring.

PATTERN:
def get_brand(self, brand_id: UUID, tenant_id: UUID) -> Brand | None:
    """Retrieve a brand by ID within tenant scope."""

RULES:
- ONE LINE for simple functions/methods
- Multi-line with Args/Returns for complex ones (Google convention):
  def create_brand(self, data: BrandCreate, tenant_id: UUID) -> Brand:
      """Create a new brand for the given tenant.

      Args:
          data: Brand creation payload.
          tenant_id: Owning tenant identifier.

      Returns:
          The persisted brand entity.
      """
- Read the function body to understand what it does
- FastAPI endpoint functions: """List all brands for the current tenant."""
- Repository methods: """Fetch brand by primary key.""" / """Persist a new brand."""
- Service methods: """Create brand from extraction data."""
- For trivial getters/setters: one-line docstring
- Google convention: imperative mood ("Return" not "Returns", "Fetch" not "Fetches")

CRITICAL: DO NOT modify pyproject.toml. Only modify source code files.

After fixing: .venv/bin/ruff check {module_paths} --select D102,D103 --no-cache → 0.
```

Agent distribution — same as Phase 3 (7 agents by module).

### Task 4.6: Activate D and verify

- [ ] **Step 1: Update pyproject.toml**

Add to select:
```toml
    "D",                       # pydocstyle: docstrings (src/ only, Google convention)
```

Add pydocstyle config:
```toml
[tool.ruff.lint.pydocstyle]
convention = "google"
```

Add to global ignore:
```toml
    "D106",     # undocumented nested class — Pydantic Config, Meta classes
```

Add `"D"` to `tests/**/*.py` and `src/tests/**/*.py` per-file-ignores.

- [ ] **Step 2: Full verification**

```bash
.venv/bin/ruff check src/ tests/ --no-cache
.venv/bin/ruff format --check src/ tests/
.venv/bin/pytest -x -q --tb=short
```

- [ ] **Step 3: Commit**

```bash
git add backend/pyproject.toml backend/src/
git commit -m "refactor: Wave 5 Phase 4 — D docstrings, ~2,581 fixes in src/

- Auto-fixed 464 docstring format issues (D200, D202, D205, D209, D212, D413)
- Added module/package docstrings to all files (D100, D104)
- Added class docstrings to all public classes (D101, D107)
- Added function/method docstrings to all public functions (D102, D103)
- Configured Google docstring convention
- Tests exempt via per-file-ignores
- Activated D rule enforcement

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Phase 5: Final update — plan and docs

### Task 5.1: Update plan with results

- [ ] **Step 1: Update the Wave 5 plan file with execution results**
- [ ] **Step 2: Update CLAUDE.md if category count changed**
- [ ] **Step 3: Final commit**

```bash
git add docs/ CLAUDE.md
git commit -m "docs: Wave 5 execution results — 53 active ruff categories

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Expected final metrics

| Metric | Pre-Wave 5 | Post-Wave 5 |
|--------|-----------|-------------|
| Ruff categories active | 49 | **53** |
| Ruff violations | 0 | **0** |
| line-length | 88 | **120** |
| mccabe max-complexity | 15 | 15 |
| Type annotation coverage (src/) | ~30% | **100%** |
| Docstring coverage (src/) | ~20% | **100%** |
| Tests passing | 2264 | 2264+ |
| Global ignores | 30 | ~32 |

---

## Troubleshooting

### Agent overwrites pyproject.toml
If an agent modifies pyproject.toml despite instructions:
1. `git checkout -- backend/pyproject.toml` to restore
2. Re-apply only YOUR config changes at the end of the phase
3. The code fixes from agents are fine — only the config needs restoration

### FAST002 auto-fix breaks imports
The auto-fix adds `from typing import Annotated` but may conflict with existing `TYPE_CHECKING` imports:
1. Run `ruff check --select F811,F401` after auto-fix to catch duplicates
2. Fix any import conflicts before proceeding

### ANN — genuinely dynamic types
Some functions (especially in copilot/sales_agent) use truly dynamic types:
1. Use `Any` with `# noqa: ANN401 — dynamic type from LLM response`
2. Goal is <10 ANN401 suppressions across the entire src/

### D — docstrings for generated code
Some files in `components/ui/` or `shared/infrastructure/model_registry.py` are auto-generated:
1. Add per-file-ignores for auto-generated files rather than writing docstrings
2. `"src/shared/infrastructure/model_registry.py" = ["D"]`

### Tests fail after FAST migration
The Annotated pattern changes how FastAPI resolves dependencies:
1. Run the full test suite after FAST auto-fix (before manual fixes)
2. If tests fail, the issue is likely a `= Depends()` that became `Annotated[T, Depends()]` losing its default
3. Check if the parameter was optional — `Annotated[T | None, Depends()]` may be needed
