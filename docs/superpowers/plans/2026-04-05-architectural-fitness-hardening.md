# Architectural Fitness & Quality Hardening

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add automated architectural fitness tests that enforce DDD boundaries, tenant isolation, response_model presence, and SA 2.0 syntax — then integrate them into every development and deployment skill so no agent or human can ship code that degrades quality.

**Architecture:** "Ratchet" pattern — fitness tests have an allowlist of known violations. New violations FAIL the build. The allowlist only shrinks over time. Tests are plain pytest (no new tools), run inside Docker, and execute in <2 seconds.

**Tech Stack:** pytest (existing), AST parsing (stdlib), pathlib (stdlib). No new dependencies.

---

## File Map

| Action | File | Responsibility |
|--------|------|---------------|
| Create | `backend/tests/architecture/conftest.py` | Shared helpers for AST parsing and module discovery |
| Create | `backend/tests/architecture/test_ddd_boundaries.py` | No cross-module imports (except copilot/shared/core) |
| Create | `backend/tests/architecture/test_api_contracts.py` | All endpoints have response_model, PII patterns flagged |
| Create | `backend/tests/architecture/test_conventions.py` | No hard deletes, SA 2.0 only, no bare dict returns |
| Create | `.husky/pre-commit` | Run ruff lint+format on staged .py files |
| Modify | `Makefile` | Add `arch-test` target |
| Modify | `.claude/commands/test-backend.md` | Add arch tests step |
| Modify | `.claude/commands/test-all.md` | Add arch tests step |
| Modify | `.claude/skills/backend-expert/SKILL.md` | Reference arch tests in constraints |
| Modify | `.claude/skills/backend-expert/references/testing.md` | Add arch test documentation |
| Modify | `.claude/skills/nicolify-feature/SKILL.md` | Add arch tests to Phase 4 |
| Create | `.claude/rules/architectural-fitness.md` | Ratchet pattern rules for agents |
| Delete | `docs/plans/2026-04-05-quality-robustness-plan.md` | Superseded by this plan |

---

### Task 1: Shared architecture test helpers

**Files:**
- Create: `backend/tests/architecture/__init__.py`
- Create: `backend/tests/architecture/conftest.py`

- [ ] **Step 1: Create empty `__init__.py`**

```python
```

- [ ] **Step 2: Create conftest with module discovery and AST helpers**

```python
"""Shared helpers for architectural fitness tests."""
import ast
import os
from pathlib import Path

import pytest

MODULES_DIR = Path(__file__).resolve().parents[2] / "src" / "modules"

# Modules allowed to import from other modules
CROSS_IMPORT_ALLOWED_SOURCES = {"copilot"}

# Modules that any module may import from
CROSS_IMPORT_ALLOWED_TARGETS = {"shared", "core", "iam"}


@pytest.fixture(scope="session")
def all_module_names() -> list[str]:
    """Return all module directory names under src/modules/."""
    return sorted(
        d.name
        for d in MODULES_DIR.iterdir()
        if d.is_dir() and not d.name.startswith("__")
    )


@pytest.fixture(scope="session")
def all_python_files() -> list[Path]:
    """Return all .py files under src/modules/."""
    return sorted(MODULES_DIR.rglob("*.py"))


def parse_imports(filepath: Path) -> list[str]:
    """Extract all import module paths from a Python file."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
    return imports


def module_name_from_path(filepath: Path) -> str:
    """Extract the module name from a file path like src/modules/brand/api/routes.py -> brand."""
    parts = filepath.relative_to(MODULES_DIR).parts
    return parts[0] if parts else ""
```

- [ ] **Step 3: Verify the file structure**

Run: `ls -la backend/tests/architecture/`
Expected: `__init__.py` and `conftest.py`

- [ ] **Step 4: Commit**

```bash
git add backend/tests/architecture/__init__.py backend/tests/architecture/conftest.py
git commit -m "test(architecture): add shared helpers for fitness tests

Ratchet-pattern architectural fitness tests. Shared AST parsing
and module discovery helpers.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: DDD boundary fitness test

**Files:**
- Create: `backend/tests/architecture/test_ddd_boundaries.py`

- [ ] **Step 1: Write the cross-module import test**

```python
"""Architectural fitness: DDD boundary enforcement.

Ratchet pattern — known violations are allowlisted. The test ensures
NO NEW cross-module imports are introduced. To fix a violation, remove
it from the allowlist and refactor the import.
"""
from pathlib import Path

from tests.architecture.conftest import (
    CROSS_IMPORT_ALLOWED_SOURCES,
    CROSS_IMPORT_ALLOWED_TARGETS,
    MODULES_DIR,
    module_name_from_path,
    parse_imports,
)

# ──────────────────────────────────────────────────────────────
# KNOWN VIOLATIONS — ratchet: only remove lines, never add.
# Format: "source_module -> target_module | file_relative_path"
# ──────────────────────────────────────────────────────────────
KNOWN_CROSS_MODULE_IMPORTS: set[str] = {
    # scheduling -> crm (agenda uses LeadModel, AppointmentEvent)
    "scheduling -> crm | scheduling/api/agenda.py",
    # offer -> crm (domain references AvatarPersona, FinancialCapacity enums)
    "offer -> crm | offer/domain/offer.py",
    "offer -> crm | offer/api/definitions.py",
    "offer -> crm | offer/api/product_mappings.py",
    # offer -> landing (LandingPageConfig in domain)
    "offer -> landing | offer/domain/offer.py",
    # connections -> crm (calendar adapter uses LeadModel)
    "connections -> crm | connections/api/calendar.py",
    # connections -> scheduling (calendar adapter uses scheduling services)
    "connections -> scheduling | connections/api/calendar.py",
    # connections -> sales_agent (meta/whatsapp webhook forwards to ChatOrchestrator)
    "connections -> sales_agent | connections/api/meta.py",
    "connections -> sales_agent | connections/api/whatsapp.py",
    # connections -> analytics (channel_info uses extraction/metrics)
    "connections -> analytics | connections/api/channel_info.py",
    # analytics -> sales_agent (frozen detection worker)
    "analytics -> sales_agent | analytics/workers/settings.py",
}


def test_no_new_cross_module_imports():
    """No module imports from another module (except copilot, shared, core, iam).

    This is the single most important DDD constraint. Violations create
    hidden coupling that makes modules impossible to extract or test independently.
    """
    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        source_module = module_name_from_path(py_file)
        if source_module in CROSS_IMPORT_ALLOWED_SOURCES:
            continue

        for imp in parse_imports(py_file):
            if not imp.startswith("src.modules."):
                continue
            target_module = imp.split("src.modules.")[1].split(".")[0]

            # Same module or allowed target — OK
            if target_module == source_module:
                continue
            if target_module in CROSS_IMPORT_ALLOWED_TARGETS:
                continue

            rel_path = str(py_file.relative_to(MODULES_DIR))
            violation_key = f"{source_module} -> {target_module} | {rel_path}"

            if violation_key not in KNOWN_CROSS_MODULE_IMPORTS:
                violations.append(violation_key)

    assert violations == [], (
        "NEW cross-module imports detected (DDD boundary violation).\n"
        "These imports were NOT in the allowlist.\n\n"
        "Options:\n"
        "  1. Refactor: move shared types to src/shared/ or use domain events\n"
        "  2. If truly necessary, add to KNOWN_CROSS_MODULE_IMPORTS in this file\n"
        "     (requires code review justification)\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_domain_layer_has_no_framework_imports():
    """Domain layer must be pure Python — no SQLAlchemy, FastAPI, or httpx imports.

    The domain layer defines business rules. Framework imports in domain/
    create coupling to infrastructure and make the domain untestable.
    """
    forbidden_prefixes = (
        "sqlalchemy",
        "fastapi",
        "httpx",
        "aiohttp",
        "redis",
        "qdrant_client",
        "alembic",
    )

    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        rel = py_file.relative_to(MODULES_DIR)
        parts = rel.parts
        # Only check files inside domain/ subdirectory
        if len(parts) < 2 or parts[1] != "domain":
            continue

        for imp in parse_imports(py_file):
            for prefix in forbidden_prefixes:
                if imp.startswith(prefix):
                    violations.append(f"{rel}: imports {imp}")

    assert violations == [], (
        "Domain layer files import framework code.\n"
        "Domain must be pure Python (Pydantic, stdlib, typing only).\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )
```

- [ ] **Step 2: Run the test to verify it passes with the allowlist**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/test_ddd_boundaries.py -v"`

Expected: 2 tests PASS. If any fail, adjust the `KNOWN_CROSS_MODULE_IMPORTS` allowlist to match the actual violations found (add missing entries, but never invent entries — only add what the test reports).

- [ ] **Step 3: Commit**

```bash
git add backend/tests/architecture/test_ddd_boundaries.py
git commit -m "test(architecture): add DDD boundary fitness tests

Ratchet-pattern tests: cross-module imports and domain layer purity.
Known violations are allowlisted — new ones fail the build.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: API contract fitness test

**Files:**
- Create: `backend/tests/architecture/test_api_contracts.py`

- [ ] **Step 1: Write the response_model and PII tests**

```python
"""Architectural fitness: API contract enforcement.

Every FastAPI endpoint MUST declare response_model= (PII allowlist pattern).
Exceptions: webhooks, redirects, 204 No Content, SSE/streaming.
"""
import ast
import re
from pathlib import Path

from tests.architecture.conftest import MODULES_DIR

# ──────────────────────────────────────────────────────────────
# KNOWN VIOLATIONS — ratchet: only remove lines, never add.
# Format: "module/api/filename.py::function_name"
# ──────────────────────────────────────────────────────────────
KNOWN_MISSING_RESPONSE_MODEL: set[str] = set()
# This will be populated on first run based on actual violations found.
# After initial population, the set is frozen — new endpoints MUST have response_model.

# Endpoints that legitimately don't need response_model
EXEMPT_PATTERNS: set[str] = set()
# Will be populated with webhook handlers, SSE streams, OAuth callbacks, etc.


def _find_route_decorators(filepath: Path) -> list[dict]:
    """Parse a Python file and find all FastAPI route decorators with metadata."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    routes: list[dict] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            # Match @router.get(...), @router.post(...), etc.
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute):
                continue
            if func.attr not in ("get", "post", "put", "patch", "delete"):
                continue

            has_response_model = False
            status_code = None
            for kw in decorator.keywords:
                if kw.arg == "response_model":
                    has_response_model = True
                if kw.arg == "status_code":
                    if isinstance(kw.value, ast.Constant):
                        status_code = kw.value.value
                    elif isinstance(kw.value, ast.Attribute):
                        # status.HTTP_204_NO_CONTENT → extract from name
                        attr_name = kw.value.attr
                        match = re.search(r"(\d+)", attr_name)
                        if match:
                            status_code = int(match.group(1))

            routes.append({
                "function": node.name,
                "method": func.attr.upper(),
                "has_response_model": has_response_model,
                "status_code": status_code,
                "line": node.lineno,
            })
    return routes


def test_all_endpoints_have_response_model():
    """Every endpoint must declare response_model= unless exempt.

    Exempt: status_code 204 (no content), 202 (accepted), 301/302 (redirect).
    Known violations are allowlisted with the ratchet pattern.
    """
    exempt_status_codes = {204, 202, 301, 302}
    violations: list[str] = []

    for api_dir in sorted(MODULES_DIR.rglob("api")):
        if not api_dir.is_dir():
            continue
        for py_file in sorted(api_dir.glob("*.py")):
            if py_file.name.startswith("__"):
                continue
            rel_path = str(py_file.relative_to(MODULES_DIR))

            for route in _find_route_decorators(py_file):
                if route["has_response_model"]:
                    continue
                if route["status_code"] in exempt_status_codes:
                    continue

                violation_key = f"{rel_path}::{route['function']}"
                if violation_key in KNOWN_MISSING_RESPONSE_MODEL:
                    continue
                if violation_key in EXEMPT_PATTERNS:
                    continue

                violations.append(
                    f"{violation_key} (line {route['line']}, "
                    f"{route['method']}, no response_model)"
                )

    assert violations == [], (
        "NEW endpoints without response_model= detected.\n"
        "Every endpoint MUST declare response_model= to prevent PII leaks.\n\n"
        "Options:\n"
        "  1. Add response_model=YourResponseSchema to the decorator\n"
        "  2. If this is a webhook/redirect/SSE, add to EXEMPT_PATTERNS\n"
        "  3. If legacy, add to KNOWN_MISSING_RESPONSE_MODEL (requires justification)\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )
```

- [ ] **Step 2: Run the test — it will likely fail with ~47 violations**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/test_api_contracts.py -v 2>&1 | tail -60"`

Expected: FAIL with a list of violations. Copy the violation keys from the output.

- [ ] **Step 3: Populate the allowlist with current violations**

Take the violation keys from step 2 output and add them to `KNOWN_MISSING_RESPONSE_MODEL` and `EXEMPT_PATTERNS` (webhooks, OAuth callbacks go in EXEMPT_PATTERNS; the rest in KNOWN_MISSING_RESPONSE_MODEL).

Use this classification:
- **EXEMPT_PATTERNS**: functions with "webhook" or "callback" or "auth_url" in name, SSE endpoints
- **KNOWN_MISSING_RESPONSE_MODEL**: everything else

- [ ] **Step 4: Re-run to verify PASS**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/test_api_contracts.py -v"`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/architecture/test_api_contracts.py
git commit -m "test(architecture): add API contract fitness tests

Ratchet-pattern test: all endpoints must have response_model=.
47 known violations allowlisted — new endpoints must comply.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Convention fitness tests

**Files:**
- Create: `backend/tests/architecture/test_conventions.py`

- [ ] **Step 1: Write convention enforcement tests**

```python
"""Architectural fitness: coding convention enforcement.

Validates project-wide conventions that Ruff cannot catch:
- No hard deletes (session.delete)
- SA 2.0 syntax only (no session.query)
- No print() in production code
"""
import re
from pathlib import Path

from tests.architecture.conftest import MODULES_DIR

# ──────────────────────────────────────────────────────────────
# KNOWN VIOLATIONS — ratchet: only remove lines, never add.
# ──────────────────────────────────────────────────────────────
KNOWN_SA1X_VIOLATIONS: set[str] = set()
# Will be populated on first run with files using session.query() syntax.


def test_no_hard_deletes():
    """No repository uses session.delete() — only soft delete via deleted_at.

    Hard deletes violate data retention policy and break audit trails.
    Use: obj.deleted_at = datetime.utcnow() instead.
    """
    # Pattern: .delete( but NOT in comments, strings, or migration files
    delete_pattern = re.compile(r"(?:session|db|self\.db|self\.session)\.delete\s*\(")
    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        # Skip migration files
        if "migrations" in py_file.parts or "alembic" in py_file.parts:
            continue
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if delete_pattern.search(line):
                rel = py_file.relative_to(MODULES_DIR)
                violations.append(f"{rel}:{i}: {stripped.strip()}")

    assert violations == [], (
        "Hard deletes detected. Use soft delete (deleted_at) instead.\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_no_sqlalchemy_1x_query_syntax():
    """No new code uses session.query() — must use select(Model).where(...).

    SA 2.0 select() is required for async compatibility and type safety.
    """
    query_pattern = re.compile(
        r"(?:session|db|self\.db|self\.session)\.query\s*\("
    )
    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        if "migrations" in py_file.parts:
            continue
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if query_pattern.search(line):
                rel = py_file.relative_to(MODULES_DIR)
                violation_key = str(rel)
                if violation_key in KNOWN_SA1X_VIOLATIONS:
                    continue
                violations.append(f"{rel}:{i}: {stripped.strip()}")

    assert violations == [], (
        "SA 1.x session.query() detected. Use SA 2.0 select(Model).where(...).\n\n"
        "Options:\n"
        "  1. Refactor to: result = await session.execute(select(Model).where(...))\n"
        "  2. If legacy code you can't touch now, add file to KNOWN_SA1X_VIOLATIONS\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )
```

- [ ] **Step 2: Run the test**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/test_conventions.py -v 2>&1 | tail -30"`

Expected: `test_no_hard_deletes` PASS. `test_no_sqlalchemy_1x_query_syntax` may fail if there are SA 1.x files.

- [ ] **Step 3: If SA 1.x test fails, populate the allowlist**

Take file paths from the output and add to `KNOWN_SA1X_VIOLATIONS`. These are files that still use `session.query()` — they get migrated when we touch them.

- [ ] **Step 4: Re-run to verify all PASS**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/test_conventions.py -v"`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add backend/tests/architecture/test_conventions.py
git commit -m "test(architecture): add convention fitness tests

No hard deletes, SA 2.0 syntax enforcement. Ratchet pattern
with allowlist for known legacy SA 1.x files.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Run full architecture test suite

- [ ] **Step 1: Run all fitness tests together**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/ -v"`

Expected: ALL PASS (5 tests total: cross_module_imports, domain_purity, response_model, hard_deletes, sa1x_syntax)

- [ ] **Step 2: Verify they run fast**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/ -v --durations=5"`

Expected: Total <3 seconds (they're just AST parsing, no I/O)

- [ ] **Step 3: Verify they don't break the full test suite**

Run: `docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short 2>&1 | tail -10"`

Expected: All tests pass including the new architecture tests.

- [ ] **Step 4: Commit (if any adjustments were needed)**

```bash
git add backend/tests/architecture/
git commit -m "test(architecture): finalize fitness test allowlists

Verified all 5 fitness tests pass with correct allowlists.
Total runtime: <3s.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Pre-commit hook for ruff

**Files:**
- Create: `.husky/pre-commit`

- [ ] **Step 1: Check if .husky directory exists and what's in it**

Run: `ls -la .husky/`

- [ ] **Step 2: Create the pre-commit hook**

```bash
#!/bin/sh

# Frontend: ESLint + TypeScript (handled by lint-staged in package.json if configured)

# Backend: Ruff lint + format check on staged Python files
STAGED_PY=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | head -50)
if [ -n "$STAGED_PY" ]; then
  echo "🐍 Running ruff on staged Python files..."

  # Check if the backend container is running
  if ! docker ps --format '{{.Names}}' | grep -q visionarias_brain_dev; then
    echo "⚠️  Backend container not running. Skipping Python lint."
    echo "   Start with: make dev"
    exit 0
  fi

  # Lint check (errors only, not auto-fix)
  docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check $STAGED_PY --no-cache --no-fix" || {
    echo "❌ Ruff lint failed. Fix errors before committing."
    exit 1
  }

  # Format check (report only)
  docker exec -t visionarias_brain_dev bash -c "cd /app && ruff format --check $STAGED_PY --no-cache" || {
    echo "❌ Ruff format check failed. Run: docker exec -t visionarias_brain_dev bash -c 'cd /app && ruff format $STAGED_PY'"
    exit 1
  }
fi
```

- [ ] **Step 3: Make it executable**

Run: `chmod +x .husky/pre-commit`

- [ ] **Step 4: Test the hook manually**

Create a temp file with bad formatting, stage it, and try to commit:

Run: `echo "x=1" > /tmp/test_ruff.py && cp /tmp/test_ruff.py backend/src/test_ruff_temp.py && git add backend/src/test_ruff_temp.py`

Try commit (should fail or warn): `git commit -m "test" --dry-run`

Clean up: `git reset backend/src/test_ruff_temp.py && rm backend/src/test_ruff_temp.py`

- [ ] **Step 5: Commit**

```bash
git add .husky/pre-commit
git commit -m "chore: add pre-commit hook for ruff lint+format on Python files

Runs ruff check and ruff format --check on staged .py files.
Gracefully skips if backend container is not running.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Add Makefile target

**Files:**
- Modify: `Makefile`

- [ ] **Step 1: Add `arch-test` target after `pytest-cov` in Makefile**

Add this block after the `pytest-cov` target (around line 133):

```makefile
arch-test:
	docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/ -v"
```

- [ ] **Step 2: Add to .PHONY list**

Add `arch-test` to the `.PHONY` line at the top of the Makefile.

- [ ] **Step 3: Verify the target works**

Run: `make arch-test`

Expected: 5 tests PASS

- [ ] **Step 4: Commit**

```bash
git add Makefile
git commit -m "chore: add make arch-test target for architectural fitness tests

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 8: Update `/test-backend` command

**Files:**
- Modify: `.claude/commands/test-backend.md`

- [ ] **Step 1: Add architecture tests step between lint and unit tests**

After step 2 (Lint) and before step 3 (Unit tests), insert:

```markdown
### 3. Architectural fitness tests
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/ -v"
```
These validate DDD boundaries (no cross-module imports), API contracts (response_model present),
and coding conventions (no hard deletes, SA 2.0 syntax). Failures here mean a structural
regression — fix before proceeding.
```

Renumber the old step 3 (Unit tests) to step 4, and old step 4 (Report) to step 5.

In the Report section, add a row:

```markdown
| Step | Result | Coverage |
|---|---|---|
| Lint | pass/fail | — |
| Arch fitness | pass/fail (N tests) | — |
| Tests | pass/fail count | XX% (min 60%) |
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/test-backend.md
git commit -m "docs(skills): add arch fitness tests to /test-backend command

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: Update `/test-all` command

**Files:**
- Modify: `.claude/commands/test-all.md`

- [ ] **Step 1: Add architecture tests step after backend lint (step 1)**

After step 1 (Backend lint) and before step 2 (Backend tests), insert:

```markdown
### 2. Backend architectural fitness tests
```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/ -v"
```
Validates DDD boundaries, API contracts, and coding conventions. If this fails,
a structural rule was violated — fix before continuing with unit tests.
```

Renumber all subsequent steps (old step 2 becomes 3, etc.). The new order:
1. Backend lint (ruff)
2. **Backend arch fitness tests** ← NEW
3. Backend tests with coverage (pytest)
4. Frontend types (tsc)
5. Frontend lint (ESLint)
6. Frontend tests with coverage (vitest)
7. E2E Smoke (Playwright)
8. Migration verification
9. Summary

In the Summary table, add a row for arch fitness:

```markdown
| Step | Result | Coverage |
|---|---|---|
| Backend lint | PASS/FAIL | — |
| Arch fitness | PASS/FAIL (5 tests) | — |
| Backend tests | X passed | XX% (min 60%) |
| Frontend types | PASS/FAIL | — |
| Frontend lint | PASS/FAIL (N warnings) | — |
| Frontend tests | X passed | XX% (min 20%) |
| E2E Smoke | X passed | — |
| Migrations (fresh DB) | PASS/FAIL | — |
```

- [ ] **Step 2: Commit**

```bash
git add .claude/commands/test-all.md
git commit -m "docs(skills): add arch fitness tests to /test-all command

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: Update `backend-expert` skill

**Files:**
- Modify: `.claude/skills/backend-expert/SKILL.md`
- Modify: `.claude/skills/backend-expert/references/testing.md`

- [ ] **Step 1: Add arch test reference to SKILL.md constraints**

At the end of the **Constraints** section in `SKILL.md` (after line ~82), add:

```markdown
- **Fitness tests:** New code must pass `pytest tests/architecture/ -v`. These enforce DDD boundaries (no cross-module imports), API contracts (response_model= required), and conventions (no hard deletes, SA 2.0). Run `make arch-test` to verify.
```

- [ ] **Step 2: Add architecture test section to testing.md**

At the end of `references/testing.md` (after the Rules section), add:

```markdown
## Architectural Fitness Tests

Located at `backend/tests/architecture/`. These run as part of the regular pytest suite.

### What they enforce
| Test | Rule | Ratchet |
|---|---|---|
| `test_no_new_cross_module_imports` | Module A cannot import from Module B (except copilot, shared, core) | Allowlist in test file |
| `test_domain_layer_has_no_framework_imports` | domain/ must be pure Python (no SQLAlchemy, FastAPI) | No allowlist — zero tolerance |
| `test_all_endpoints_have_response_model` | Every @router endpoint needs response_model= | Allowlist in test file |
| `test_no_hard_deletes` | No session.delete() — use soft delete | No allowlist — zero tolerance |
| `test_no_sqlalchemy_1x_query_syntax` | No session.query() — use select().where() | Allowlist in test file |

### Ratchet pattern
Tests with allowlists have a `KNOWN_*` set listing legacy violations. The test passes if
all violations are in the allowlist. **New violations fail the build.** To fix a violation:
1. Refactor the code
2. Remove the entry from the allowlist
3. The allowlist can only shrink — never add new entries without code review justification

### When to run
- `make arch-test` — standalone
- `make pytest` — included automatically (they're in `tests/architecture/`)
- `/test-backend` — runs as step 3
- `/test-all` — runs as step 2
```

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/backend-expert/SKILL.md .claude/skills/backend-expert/references/testing.md
git commit -m "docs(skills): document arch fitness tests in backend-expert skill

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: Update `nicolify-feature` pipeline

**Files:**
- Modify: `.claude/skills/nicolify-feature/SKILL.md`

- [ ] **Step 1: Add arch tests to Phase 4**

In Phase 4 (Testing), add an arch test step after backend lint (around line 162). Insert between the ruff and pytest commands:

```bash
# Architectural fitness (DDD boundaries, API contracts, conventions)
docker exec -it visionarias_brain_dev bash -c "cd /app && pytest tests/architecture/ -v"
```

Also add the arch fitness row to the Final Output test results table:

```markdown
| Step | Result | Coverage |
|---|---|---|
| Backend lint | PASS/FAIL | — |
| Arch fitness | PASS/FAIL | — |
| Backend tests | X passed | XX% (min 60%) |
| Frontend types | PASS/FAIL | — |
| Frontend lint | PASS/FAIL | — |
| Frontend tests | X passed | XX% (min 20%) |
| E2E Smoke | X passed | — |
```

- [ ] **Step 2: Commit**

```bash
git add .claude/skills/nicolify-feature/SKILL.md
git commit -m "docs(skills): add arch fitness tests to nicolify-feature Phase 4

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: Create architectural fitness rule

**Files:**
- Create: `.claude/rules/architectural-fitness.md`

- [ ] **Step 1: Write the rule**

```markdown
# Architectural Fitness Tests

## What
Automated tests in `backend/tests/architecture/` that enforce structural rules
Ruff and ESLint cannot catch: DDD boundaries, API contracts, coding conventions.

## Ratchet Pattern
- Tests have allowlists (`KNOWN_*` sets) of legacy violations
- **New violations fail the build** — you cannot ship code that adds a new cross-module import
- Allowlists only shrink (fix violations, remove from list)
- Adding to an allowlist requires explicit justification in the commit message

## When to Run
- `make arch-test` — standalone
- Included automatically in `pytest`, `/test-backend`, `/test-all`, `/pase-produccion`

## What to Do When a Fitness Test Fails

### `test_no_new_cross_module_imports`
You imported from another module's domain/infrastructure/application. Fix:
1. Move shared types/enums to `src/shared/`
2. Use domain events for cross-module communication
3. Create a port/interface in `src/shared/links/`

### `test_domain_layer_has_no_framework_imports`
You imported SQLAlchemy/FastAPI/httpx in a `domain/` file. Fix:
1. Domain must be pure Python + Pydantic only
2. Move framework code to `infrastructure/`

### `test_all_endpoints_have_response_model`
You created an endpoint without `response_model=`. Fix:
1. Create a Pydantic response DTO
2. Add `response_model=YourDTO` to the decorator

### `test_no_hard_deletes`
You used `session.delete()`. Fix:
1. Use `obj.deleted_at = datetime.utcnow()` instead
2. Update queries to filter `WHERE deleted_at IS NULL`

### `test_no_sqlalchemy_1x_query_syntax`
You used `session.query()`. Fix:
1. Use `session.execute(select(Model).where(...))` instead
2. Use `result.scalars().all()` for the result
```

- [ ] **Step 2: Commit**

```bash
git add .claude/rules/architectural-fitness.md
git commit -m "docs(rules): add architectural fitness test rule for agents

Explains ratchet pattern and fix strategies for each fitness test.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: Delete superseded plan

**Files:**
- Delete: `docs/plans/2026-04-05-quality-robustness-plan.md`

- [ ] **Step 1: Remove the old plan**

Run: `rm docs/plans/2026-04-05-quality-robustness-plan.md`

- [ ] **Step 2: Commit**

```bash
git add -u docs/plans/2026-04-05-quality-robustness-plan.md
git commit -m "chore: remove superseded quality-robustness plan

Replaced by architectural fitness tests (implemented) + this plan.
Items like Pyright, Semgrep, mutation testing were deemed premature.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: Update memory

**Files:**
- Create or update: `/home/chris/.claude/projects/-home-chris-AISALESHT/memory/project_arch_fitness_tests.md`
- Update: `/home/chris/.claude/projects/-home-chris-AISALESHT/memory/MEMORY.md`

- [ ] **Step 1: Create memory file**

```markdown
---
name: Architectural Fitness Tests
description: Ratchet-pattern pytest tests in backend/tests/architecture/ that enforce DDD boundaries, API contracts, and coding conventions. Integrated into /test-backend, /test-all, nicolify-feature, and all agent workflows.
type: project
---

Architectural fitness tests implemented 2026-04-05. Located at `backend/tests/architecture/`.

**5 tests:**
- `test_no_new_cross_module_imports` — DDD boundary enforcement (allowlist)
- `test_domain_layer_has_no_framework_imports` — domain purity (zero tolerance)
- `test_all_endpoints_have_response_model` — PII prevention (allowlist)
- `test_no_hard_deletes` — soft delete only (zero tolerance)
- `test_no_sqlalchemy_1x_query_syntax` — SA 2.0 enforcement (allowlist)

**Why:** Agentic development produces structural regressions that runtime tests don't catch. These tests catch cross-module imports, missing response_model, hard deletes, and SA 1.x syntax at build time.

**How to apply:** Run `make arch-test` standalone, or rely on `/test-backend` / `/test-all` which include them. When a fitness test fails during development, fix the structural violation — never add to the allowlist without explicit justification.
```

- [ ] **Step 2: Add pointer to MEMORY.md**

Add to MEMORY.md under the appropriate section:
```
- [project_arch_fitness_tests.md](project_arch_fitness_tests.md) - 2026-04-05: Ratchet-pattern arch fitness tests (DDD boundaries, API contracts, conventions) integrated into all test skills
```

- [ ] **Step 3: Remove the old quality tools audit memory reference if redundant**

The `project_quality_tools_audit.md` memory should be kept since it covers Ruff rule expansion which is separate.

---

## Verification Plan

After all tasks are complete, run the full suite to verify nothing broke:

```bash
# 1. Arch tests standalone
make arch-test
# Expected: 5 passed in <3s

# 2. Full backend suite (arch tests included)
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"
# Expected: All pass (existing + 5 new)

# 3. Pre-commit hook test
echo "import os" > /tmp/test.py
cp /tmp/test.py backend/src/test_hook_temp.py
git add backend/src/test_hook_temp.py
git commit -m "test hook" --dry-run
git reset backend/src/test_hook_temp.py
rm backend/src/test_hook_temp.py
# Expected: ruff runs on staged file

# 4. Full /test-all (optional but recommended)
# Invoke /test-all skill
```

---

## Summary of Skill/Command Changes

| File | Change | Effect |
|------|--------|--------|
| `.claude/commands/test-backend.md` | +1 step (arch fitness) | Every `/test-backend` run validates structure |
| `.claude/commands/test-all.md` | +1 step (arch fitness) | Every `/test-all` and `/pase-produccion` validates structure |
| `.claude/skills/backend-expert/SKILL.md` | +1 constraint line | Agents know arch tests exist |
| `.claude/skills/backend-expert/references/testing.md` | +1 section | Agents know how to run and fix arch test failures |
| `.claude/skills/nicolify-feature/SKILL.md` | +1 command in Phase 4 | Feature pipeline validates structure |
| `.claude/rules/architectural-fitness.md` | New rule | All agents learn the ratchet pattern |
| `.husky/pre-commit` | New hook | Human commits get ruff validation |
| `Makefile` | +1 target | `make arch-test` available |

**Not modified (already covered):**
- `.claude/skills/pase-produccion/SKILL.md` — Calls `/test-all` which now includes arch tests
- `.github/workflows/deploy-prod.yml` — Arch tests run inside `pytest` which CI already executes
- `.claude/commands/test-frontend.md` — Arch tests are backend-only
