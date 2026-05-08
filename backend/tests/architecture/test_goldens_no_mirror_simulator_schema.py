"""Architecture fitness gate — goldens schema does NOT mirror simulator schema.

Parallel registries cement (Story D D-A-2 + D-A-13):
  - `goldens/_schema_migrations.py` is PARALLEL to Story B's
    `simulator/_internal/schema_migrations.py`.
  - They share conceptual pattern but are in distinct namespaces with
    distinct lifecycles:
      - simulator: code-side migrations (Pydantic state machine bumps)
      - goldens:   data-side migrations (YAML artifact format bumps)
  - Story D goldens must NOT import from simulator's schema_migrations.
  - This prevents tight coupling that would break cross-story independence.

Allowlist empty shrink-only (ratchet pattern).

# voseo-allowed: arch gate cites parallel registry pattern docs
"""

from __future__ import annotations

import ast
import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.no_eval

# ── Repository paths ─────────────────────────────────────────────────────────
_BACKEND_ROOT: Path = Path(__file__).resolve().parents[2]
_GOLDENS_SCHEMA: Path = _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "goldens" / "_schema.py"
_GOLDENS_SCHEMA_MIGRATIONS: Path = (
    _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "goldens" / "_schema_migrations.py"
)
_SIMULATOR_SCHEMA_MIGRATIONS: Path = (
    _BACKEND_ROOT / "tests" / "agentic_evals" / "sales_agent" / "simulator" / "_internal" / "schema_migrations.py"
)

# ── Allowlist (shrink-only ratchet — must stay EMPTY for Story D) ────────────
# Any cross-import from simulator/_internal/schema_migrations → MUST be listed
# here with explicit justification. Story D requires ZERO cross-imports.
_ALLOWED_SIMULATOR_SCHEMA_IMPORTS: frozenset[str] = frozenset()


def _get_imports_from_file(path: Path) -> list[str]:
    """Return all module paths imported in the given Python file."""
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(path))
    imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
    return imports


def _has_simulator_schema_migration_import(path: Path) -> list[str]:
    """Return list of import strings that reference simulator._internal.schema_migrations."""
    if not path.exists():
        return []
    imports = _get_imports_from_file(path)
    # Detect any import that touches the simulator's schema_migrations module
    forbidden_prefix = "tests.agentic_evals.sales_agent.simulator._internal"
    violations = [imp for imp in imports if imp.startswith(forbidden_prefix) and "schema_migrations" in imp]
    return violations


# ════════════════════════════════════════════════════════════════════════
# File existence pre-conditions
# ════════════════════════════════════════════════════════════════════════


def test_goldens_schema_file_exists() -> None:
    """goldens/_schema.py must exist (T-1 deliverable)."""
    assert _GOLDENS_SCHEMA.is_file(), f"goldens/_schema.py not found at {_GOLDENS_SCHEMA}. T-1 not yet implemented."


def test_goldens_schema_migrations_file_exists() -> None:
    """goldens/_schema_migrations.py must exist (T-1 deliverable)."""
    assert _GOLDENS_SCHEMA_MIGRATIONS.is_file(), (
        f"goldens/_schema_migrations.py not found at {_GOLDENS_SCHEMA_MIGRATIONS}."
    )


def test_simulator_schema_migrations_file_exists() -> None:
    """simulator/_internal/schema_migrations.py exists (Story B invariant)."""
    assert _SIMULATOR_SCHEMA_MIGRATIONS.is_file(), (
        f"simulator/_internal/schema_migrations.py not found at {_SIMULATOR_SCHEMA_MIGRATIONS}. "
        "Story B regression — this file must not be deleted."
    )


# ════════════════════════════════════════════════════════════════════════
# No cross-import from simulator schema migrations
# ════════════════════════════════════════════════════════════════════════


def test_goldens_schema_does_not_import_simulator_schema_migrations() -> None:
    """goldens/_schema.py must NOT import from simulator/_internal/schema_migrations.

    Parallel registries (D-A-2): goldens schema is self-contained. Any
    import from simulator's migration registry creates tight coupling.
    Allowlist empty — Story D requires zero cross-imports.
    """
    violations = _has_simulator_schema_migration_import(_GOLDENS_SCHEMA)
    unapproved = [v for v in violations if v not in _ALLOWED_SIMULATOR_SCHEMA_IMPORTS]
    assert not unapproved, (
        f"goldens/_schema.py imports from simulator's schema_migrations (parallel registries "
        f"MUST be independent — D-A-2):\n  {unapproved}\n"
        f"Allowlist: {sorted(_ALLOWED_SIMULATOR_SCHEMA_IMPORTS)}"
    )


def test_goldens_schema_migrations_does_not_import_simulator_schema_migrations() -> None:
    """goldens/_schema_migrations.py must NOT import from simulator/_internal/schema_migrations.

    Parallel registries (D-A-2): goldens migration registry operates independently.
    Different lifecycle: goldens bumps = YAML data format changes;
    simulator bumps = Pydantic code state machine changes.
    """
    violations = _has_simulator_schema_migration_import(_GOLDENS_SCHEMA_MIGRATIONS)
    unapproved = [v for v in violations if v not in _ALLOWED_SIMULATOR_SCHEMA_IMPORTS]
    assert not unapproved, (
        f"goldens/_schema_migrations.py imports from simulator's schema_migrations "
        f"(parallel registries MUST be independent — D-A-2):\n  {unapproved}\n"
        f"Allowlist: {sorted(_ALLOWED_SIMULATOR_SCHEMA_IMPORTS)}"
    )


# ════════════════════════════════════════════════════════════════════════
# Distinct namespace verification
# ════════════════════════════════════════════════════════════════════════


def test_goldens_registry_is_distinct_from_simulator_registry() -> None:
    """GOLDEN_SCHEMA_MIGRATIONS is a distinct dict from simulator's SCHEMA_MIGRATIONS.

    Parallel registries must be separate Python objects — any shared reference
    would contaminate both (register on one would affect the other).
    """
    from tests.agentic_evals.sales_agent.goldens._schema_migrations import (
        GOLDEN_SCHEMA_MIGRATIONS,
    )
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        SCHEMA_MIGRATIONS,
    )

    assert GOLDEN_SCHEMA_MIGRATIONS is not SCHEMA_MIGRATIONS, (
        "GOLDEN_SCHEMA_MIGRATIONS and SCHEMA_MIGRATIONS are the SAME object! "
        "Parallel registries must be distinct dicts (D-A-2 violation)."
    )


def test_goldens_current_versions_is_distinct_from_simulator_current_versions() -> None:
    """CURRENT_GOLDEN_SCHEMA_VERSIONS is a distinct dict from simulator's CURRENT_SCHEMA_VERSIONS."""
    from tests.agentic_evals.sales_agent.goldens._schema_migrations import (
        CURRENT_GOLDEN_SCHEMA_VERSIONS,
    )
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        CURRENT_SCHEMA_VERSIONS,
    )

    assert CURRENT_GOLDEN_SCHEMA_VERSIONS is not CURRENT_SCHEMA_VERSIONS, (
        "CURRENT_GOLDEN_SCHEMA_VERSIONS and CURRENT_SCHEMA_VERSIONS are the SAME object! "
        "Parallel registries must be independent (D-A-2)."
    )


def test_goldens_schema_does_not_share_class_names_with_simulator_migrations_module() -> None:
    """goldens._schema_migrations must not reuse simulator's register/apply function names verbatim.

    Parallel == conceptually similar but distinctly named to avoid confusion.
    goldens uses 'register_golden_migration' + 'apply_golden_migrations' (suffixed _golden).
    """
    from tests.agentic_evals.sales_agent.goldens import _schema_migrations as goldens_mig

    # Goldens registry MUST use the _golden suffix
    assert hasattr(goldens_mig, "register_golden_migration"), (
        "goldens/_schema_migrations.py must export 'register_golden_migration' (not 'register_schema_migration')"
    )
    assert hasattr(goldens_mig, "apply_golden_migrations"), (
        "goldens/_schema_migrations.py must export 'apply_golden_migrations' (not 'apply_migrations')"
    )
    assert hasattr(goldens_mig, "GOLDEN_SCHEMA_MIGRATIONS"), (
        "goldens/_schema_migrations.py must export 'GOLDEN_SCHEMA_MIGRATIONS' (not 'SCHEMA_MIGRATIONS')"
    )

    # MUST NOT export the simulator function names without _golden prefix
    assert not hasattr(goldens_mig, "register_schema_migration") or (
        getattr(goldens_mig, "register_schema_migration", None)
        is not __import__(
            "tests.agentic_evals.sales_agent.simulator._internal.schema_migrations",
            fromlist=["register_schema_migration"],
        ).register_schema_migration
    ), "goldens/_schema_migrations.py must not re-export simulator's register_schema_migration"
