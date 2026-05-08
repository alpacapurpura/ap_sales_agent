"""Architecture fitness gate: PII patterns single source of truth.

Enforces DRY threshold = 2 consumers (anti-duplication.md).

Invariants:
  1. `scan_seed_pii.py` imports PATTERNS from `_pii_patterns` module
     (not a local duplicate dict literal).
  2. `scan_goldens_pii.py` imports PATTERNS from `_pii_patterns` module.
  3. Neither consumer file contains a local `PATTERNS = {` dict literal.
  4. `_pii_patterns.py` exports both `PATTERNS` and `DNI_PE_GUARD_PREFIXES`.

Allowlist: empty (shrink-only ratchet per architectural-fitness.md).
"""

from __future__ import annotations

import ast
import types
from pathlib import Path
from typing import Any

import pytest

BACKEND_ROOT = Path(__file__).resolve().parents[2]  # backend/
SCRIPTS_DIR = BACKEND_ROOT / "scripts"

SCAN_SEED_PATH = SCRIPTS_DIR / "scan_seed_pii.py"
SCAN_GOLDENS_PATH = SCRIPTS_DIR / "scan_goldens_pii.py"
PII_PATTERNS_PATH = SCRIPTS_DIR / "_pii_patterns.py"

# ---------------------------------------------------------------------------
# Allowlist — empty, shrink-only per ratchet pattern
# ---------------------------------------------------------------------------

# Files that are ALLOWED to define a local PATTERNS dict (zero exceptions).
PATTERNS_DICT_ALLOWLIST: frozenset[str] = frozenset()


def _read_source(path: Path) -> str:
    """Read source file, skipping if not found (pre-LIFT state fails test)."""
    assert path.is_file(), f"Expected file not found: {path}. T-2 LIFT not yet done?"
    return path.read_text(encoding="utf-8")


def _has_local_patterns_dict(source: str) -> bool:
    """Return True if source defines a top-level PATTERNS = { dict literal."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Assign)
            and len(node.targets) == 1
            and isinstance(node.targets[0], ast.Name)
            and node.targets[0].id == "PATTERNS"
            and isinstance(node.value, ast.Dict)
        ):
            return True
    return False


def _imports_from_pii_patterns(source: str, name: str) -> bool:
    """Return True if source imports `name` from `_pii_patterns`."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            module = node.module or ""
            if "_pii_patterns" in module:
                imported = [alias.name for alias in node.names]
                if name in imported:
                    return True
    return False


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_pii_patterns_module_exists() -> None:
    """_pii_patterns.py must exist as the LIFT module."""
    assert PII_PATTERNS_PATH.is_file(), (
        f"_pii_patterns.py not found at {PII_PATTERNS_PATH}. "
        "T-2 LIFT not yet done. Create backend/scripts/_pii_patterns.py "
        "with PATTERNS dict + DNI_PE_GUARD_PREFIXES tuple."
    )


def test_pii_patterns_exports_patterns_and_guard() -> None:
    """_pii_patterns.py must export PATTERNS dict and DNI_PE_GUARD_PREFIXES tuple."""
    source = _read_source(PII_PATTERNS_PATH)

    assert "PATTERNS" in source, "_pii_patterns.py must define PATTERNS"
    assert "DNI_PE_GUARD_PREFIXES" in source, "_pii_patterns.py must define DNI_PE_GUARD_PREFIXES"


def test_scan_seed_pii_imports_patterns_from_pii_patterns() -> None:
    """scan_seed_pii.py must import PATTERNS from _pii_patterns (LIFT refactor)."""
    source = _read_source(SCAN_SEED_PATH)
    assert _imports_from_pii_patterns(source, "PATTERNS"), (
        "scan_seed_pii.py must import PATTERNS from _pii_patterns. "
        "Refactor: replace local PATTERNS dict literal with "
        "`from _pii_patterns import PATTERNS, DNI_PE_GUARD_PREFIXES`."
    )


def test_scan_goldens_pii_imports_patterns_from_pii_patterns() -> None:
    """scan_goldens_pii.py must import PATTERNS from _pii_patterns (DRY)."""
    source = _read_source(SCAN_GOLDENS_PATH)
    assert _imports_from_pii_patterns(source, "PATTERNS"), (
        "scan_goldens_pii.py must import PATTERNS from _pii_patterns. "
        "Create scan_goldens_pii.py with "
        "`from _pii_patterns import DNI_PE_GUARD_PREFIXES, PATTERNS`."
    )


def test_scan_goldens_pii_imports_guard_prefixes_from_pii_patterns() -> None:
    """scan_goldens_pii.py must also import DNI_PE_GUARD_PREFIXES from _pii_patterns."""
    source = _read_source(SCAN_GOLDENS_PATH)
    assert _imports_from_pii_patterns(source, "DNI_PE_GUARD_PREFIXES"), (
        "scan_goldens_pii.py must import DNI_PE_GUARD_PREFIXES from _pii_patterns."
    )


@pytest.mark.parametrize(
    "scanner_path",
    [SCAN_SEED_PATH, SCAN_GOLDENS_PATH],
    ids=["scan_seed_pii", "scan_goldens_pii"],
)
def test_no_duplicate_patterns_dict_in_consumers(scanner_path: Path) -> None:
    """Consumer scanner files must NOT define a local PATTERNS dict literal.

    After the LIFT, the dict must live only in _pii_patterns.py.
    Allowlist is empty — zero exceptions permitted.
    """
    if scanner_path.name in PATTERNS_DICT_ALLOWLIST:
        pytest.skip(f"{scanner_path.name} is in allowlist (justified exception)")

    if not scanner_path.is_file():
        pytest.skip(f"{scanner_path.name} not yet created — will fail once created")

    source = _read_source(scanner_path)
    assert not _has_local_patterns_dict(source), (
        f"{scanner_path.name} defines a local PATTERNS = {{...}} dict literal. "
        "After T-2 LIFT, PATTERNS must only live in _pii_patterns.py. "
        "Replace with `from _pii_patterns import PATTERNS`."
    )


def test_pii_patterns_has_nine_categories() -> None:
    """_pii_patterns.py must define exactly 9 canonical PII categories."""
    # Import the module dynamically to check the dict contents
    import importlib.util

    spec = importlib.util.spec_from_file_location("_pii_patterns", PII_PATTERNS_PATH)
    assert spec is not None and spec.loader is not None
    mod: types.ModuleType = importlib.util.module_from_spec(spec)
    loader = spec.loader
    assert hasattr(loader, "exec_module")
    loader.exec_module(mod)

    patterns: dict[str, Any] = mod.PATTERNS
    expected_categories = {
        "email",
        "phone_intl",
        "dni_ar",
        "cuit_ar",
        "rut_cl",
        "dni_pe",
        "curp_mx",
        "rfc_mx",
        "url_internal_nicolify",
    }
    actual = set(patterns.keys())
    assert actual == expected_categories, (
        f"PATTERNS must have exactly 9 categories. "
        f"Expected: {sorted(expected_categories)}. "
        f"Got: {sorted(actual)}. "
        f"Missing: {sorted(expected_categories - actual)}. "
        f"Extra: {sorted(actual - expected_categories)}."
    )
