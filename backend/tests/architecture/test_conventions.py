"""Architectural fitness: coding convention enforcement.

Validates project-wide conventions that Ruff cannot catch:
- No hard deletes (session.delete)
- SA 2.0 syntax only (no session.query)
"""

import re

from tests.architecture.conftest import MODULES_DIR

# ──────────────────────────────────────────────────────────────
# KNOWN VIOLATIONS — ratchet: only remove lines, never add.
# ──────────────────────────────────────────────────────────────
KNOWN_HARD_DELETE_FILES: set[str] = set()

KNOWN_SA1X_VIOLATIONS: set[str] = set()


def test_no_hard_deletes():
    """No repository uses session.delete() — only soft delete via deleted_at.

    Hard deletes violate data retention policy and break audit trails.
    Use: obj.deleted_at = datetime.utcnow() instead.
    """
    delete_pattern = re.compile(r"(?:session|db|self\.db|self\.session)\.delete\s*\(")
    violations: list[str] = []

    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        if "migrations" in py_file.parts or "alembic" in py_file.parts:
            continue
        rel = py_file.relative_to(MODULES_DIR)
        if str(rel) in KNOWN_HARD_DELETE_FILES:
            continue
        content = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(content.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if delete_pattern.search(line):
                violations.append(f"{rel}:{i}: {stripped.strip()}")

    assert violations == [], (
        "Hard deletes detected. Use soft delete (deleted_at) instead.\n\n"
        "Violations:\n" + "\n".join(f"  - {v}" for v in violations)
    )


def test_no_sqlalchemy_1x_query_syntax():
    """No new code uses session.query() — must use select(Model).where(...).

    SA 2.0 select() is required for async compatibility and type safety.
    """
    query_pattern = re.compile(r"(?:session|db|self\.db|self\.session)\.query\s*\(")
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
