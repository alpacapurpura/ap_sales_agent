"""test_consolidated_migration_idempotent.py — Story 10 arch fitness gate.

Parses `alembic/versions/001_initial_snapshot.py` (produced in T-10) raw SQL
strings and asserts every DDL statement uses IF NOT EXISTS / IF EXISTS pattern.

State during T-1 (pre-rewrite): SKIP — 001_initial_snapshot.py does not exist yet.
State post T-10 (alembic consolidation ticket): ACTIVE — fails if snapshot contains
non-idempotent DDL.

Per 03-arch.md §2 Feature 3 (Scenario 3.3) and .claude/rules/backend-migrations.md.
"""

import ast
import re
from pathlib import Path

import pytest

# Expected path of the consolidated alembic snapshot (created in T-10)
# Search in both AISALESHT and post-migration luana-platform locations
_AISALESHT_SNAPSHOT = Path("/home/chris/AISALESHT/backend/alembic/versions/001_initial_snapshot.py")
_NICOLIFY_SNAPSHOT = (
    Path.home() / "luana-platform" / "nicolify" / "backend" / "alembic" / "versions" / "001_initial_snapshot.py"
)

# Use whichever exists
_SNAPSHOT_PATH = (
    _AISALESHT_SNAPSHOT if _AISALESHT_SNAPSHOT.exists() else _NICOLIFY_SNAPSHOT if _NICOLIFY_SNAPSHOT.exists() else None
)

_SNAPSHOT_PRESENT = _SNAPSHOT_PATH is not None

# Patterns that MUST be present when creating/altering (idempotent DDL)
_MUST_HAVE_IDEMPOTENT = re.compile(
    r"CREATE\s+(TABLE|INDEX|UNIQUE\s+INDEX|SEQUENCE|TYPE)\s+IF\s+NOT\s+EXISTS"
    r"|ALTER\s+TABLE\s+\S+\s+ADD\s+COLUMN\s+IF\s+NOT\s+EXISTS"
    r"|DROP\s+(TABLE|INDEX|COLUMN|SEQUENCE|TYPE)\s+IF\s+EXISTS",
    re.IGNORECASE,
)

# Patterns that are NOT idempotent (forbidden in snapshot)
_FORBIDDEN_NONIDEMPOTENT = re.compile(
    r"CREATE\s+(TABLE|INDEX|UNIQUE\s+INDEX|SEQUENCE|TYPE)\s+(?!IF\s+NOT\s+EXISTS)(\w)",
    re.IGNORECASE,
)


def _extract_sql_strings_from_file(path: Path) -> list[tuple[int, str]]:
    """Extract SQL string literals from a Python file via AST.

    Returns list of (line_number, sql_string) tuples.
    Looks for:
    - op.execute("...") calls
    - String literals containing CREATE/ALTER/DROP keywords
    """
    source = path.read_text(encoding="utf-8")
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        pytest.fail(f"Cannot parse {path}: {exc}")

    sql_strings: list[tuple[int, str]] = []

    for node in ast.walk(tree):
        # op.execute("...") — primary pattern per backend-migrations.md
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "execute"
            and node.args
        ):
            first_arg = node.args[0]
            if isinstance(first_arg, ast.Constant) and isinstance(first_arg.value, str):
                sql_strings.append((first_arg.lineno, first_arg.value))

        # Standalone string constants with DDL keywords (joined multi-line SQL)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            val = node.value.upper()
            if any(kw in val for kw in ("CREATE TABLE", "CREATE INDEX", "ALTER TABLE", "DROP TABLE")):
                sql_strings.append((node.lineno, node.value))

    return sql_strings


@pytest.mark.skipif(
    not _SNAPSHOT_PRESENT,
    reason="Story 10 T-10 not run yet — 001_initial_snapshot.py absent. "
    "This test becomes an active gate post T-10 merge.",
)
def test_snapshot_ddl_is_idempotent():
    """001_initial_snapshot.py DDL must use IF NOT EXISTS / IF EXISTS everywhere.

    Per .claude/rules/backend-migrations.md: idempotent migrations mandatory.
    op.execute() with raw SQL + IF NOT EXISTS pattern required.
    """
    assert _SNAPSHOT_PATH is not None
    sql_strings = _extract_sql_strings_from_file(_SNAPSHOT_PATH)

    assert len(sql_strings) > 0, (
        f"No op.execute() SQL strings found in {_SNAPSHOT_PATH}. "
        "Snapshot must use op.execute() pattern per backend-migrations.md."
    )

    violations: list[str] = []
    for lineno, sql in sql_strings:
        sql_upper = sql.upper().strip()

        # Check for non-idempotent CREATE statements
        # Look for CREATE TABLE/INDEX/etc. NOT followed by IF NOT EXISTS
        create_matches = re.findall(
            r"CREATE\s+(TABLE|INDEX|UNIQUE\s+INDEX|SEQUENCE|TYPE)\s+(\S+)",
            sql_upper,
        )
        for obj_type, obj_name in create_matches:
            # Ensure IF NOT EXISTS is present
            if "IF NOT EXISTS" not in sql_upper:
                violations.append(f"  Line {lineno}: CREATE {obj_type} {obj_name!r} missing IF NOT EXISTS")

        # Check for non-idempotent ADD COLUMN
        add_col_matches = re.findall(
            r"ADD\s+COLUMN\s+(\S+)",
            sql_upper,
        )
        for col_name in add_col_matches:
            if "ADD COLUMN IF NOT EXISTS" not in sql_upper:
                violations.append(f"  Line {lineno}: ADD COLUMN {col_name!r} missing IF NOT EXISTS")

        # Check for DROP without IF EXISTS
        drop_matches = re.findall(
            r"DROP\s+(TABLE|INDEX|COLUMN|SEQUENCE|TYPE)\s+(\S+)",
            sql_upper,
        )
        for obj_type, obj_name in drop_matches:
            if "IF EXISTS" not in sql_upper:
                violations.append(f"  Line {lineno}: DROP {obj_type} {obj_name!r} missing IF EXISTS")

    assert len(violations) == 0, (
        f"Found {len(violations)} non-idempotent DDL statement(s) in {_SNAPSHOT_PATH}.\n"
        "Per .claude/rules/backend-migrations.md all DDL must use IF NOT EXISTS / IF EXISTS.\n"
        "Violations:\n" + "\n".join(violations)
    )


@pytest.mark.skipif(
    not _SNAPSHOT_PRESENT,
    reason="Story 10 T-10 not run yet — 001_initial_snapshot.py absent.",
)
def test_snapshot_uses_op_execute_not_sa_create_table():
    """001_initial_snapshot.py must use op.execute() raw SQL, NOT op.create_table().

    Per .claude/rules/backend-migrations.md: op.create_table() is non-idempotent.
    op.add_column() / op.create_index() are also forbidden.
    """
    assert _SNAPSHOT_PATH is not None
    source = _SNAPSHOT_PATH.read_text(encoding="utf-8")

    forbidden_patterns = [
        ("op.create_table(", "Use op.execute('CREATE TABLE IF NOT EXISTS ...') instead"),
        ("op.add_column(", "Use op.execute('ALTER TABLE ... ADD COLUMN IF NOT EXISTS ...') instead"),
        ("op.create_index(", "Use op.execute('CREATE INDEX IF NOT EXISTS ...') instead"),
        ("sa.Enum(", "Never use sa.Enum() in migrations (broken SA 2.0.27). Use raw SQL type reference."),
    ]

    violations: list[str] = []
    for pattern, message in forbidden_patterns:
        if pattern in source:
            occurrences = source.count(pattern)
            violations.append(f"  Found {occurrences}x '{pattern}' — {message}")

    assert len(violations) == 0, f"Non-idempotent migration patterns found in {_SNAPSHOT_PATH}:\n" + "\n".join(
        violations
    )
