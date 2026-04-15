"""Enforce file naming conventions and DDD folder structure compliance.

Fitness gates:
1. All .py files must be snake_case
2. Each module must have the 4 DDD layers (domain, infrastructure, application, api)
3. No stray .py files at module root (must be inside a DDD layer)
"""

import re
from pathlib import Path

MODULES_DIR = Path(__file__).resolve().parents[2] / "src" / "modules"
EXPECTED_LAYERS = {"domain", "infrastructure", "application", "api"}
SNAKE_CASE_RE = re.compile(r"^[a-z][a-z0-9_]*\.py$")

# Modules with non-standard structure (justified exceptions)
KNOWN_STRUCTURE_EXCEPTIONS: dict[str, set[str]] = {
    # Some modules don't need all 4 layers
    "core": {"domain", "infrastructure", "application", "api"},  # core is framework, not DDD module
    "shared": {"domain", "infrastructure", "application", "api"},  # shared is cross-cutting
    "iam": set(),  # may be thin
}

# Files at module root that are allowed (e.g., __init__.py)
ALLOWED_ROOT_FILES = {"__init__.py"}

# Known stray files (ratchet — shrink only, never grow)
KNOWN_STRAY_FILES: set[str] = set()


def test_all_python_files_snake_case():
    """All .py files in modules/ must use snake_case naming."""
    violations = []
    for py_file in sorted(MODULES_DIR.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        if not SNAKE_CASE_RE.match(py_file.name):
            violations.append(str(py_file.relative_to(MODULES_DIR)))

    assert not violations, f"Files not snake_case ({len(violations)}):\n" + "\n".join(f"  {v}" for v in violations)


def test_module_folders_have_ddd_layers():
    """Each module must have domain/, infrastructure/, application/, api/ directories."""
    violations = []
    for module_dir in sorted(MODULES_DIR.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue
        if module_dir.name in KNOWN_STRUCTURE_EXCEPTIONS:
            continue

        existing = {d.name for d in module_dir.iterdir() if d.is_dir() and not d.name.startswith("_")}
        missing = EXPECTED_LAYERS - existing

        if missing:
            violations.append(f"{module_dir.name}: missing {sorted(missing)}")

    assert not violations, f"DDD structure violations ({len(violations)}):\n" + "\n".join(f"  {v}" for v in violations)


def test_no_stray_py_files_at_module_root():
    """Python files must be inside DDD layer dirs, not at module root."""
    violations = []
    for module_dir in sorted(MODULES_DIR.iterdir()):
        if not module_dir.is_dir() or module_dir.name.startswith("_"):
            continue
        if module_dir.name in KNOWN_STRUCTURE_EXCEPTIONS:
            continue

        stray = [f.name for f in module_dir.glob("*.py") if f.name not in ALLOWED_ROOT_FILES]
        if stray:
            entry = f"{module_dir.name}: {stray}"
            if entry not in KNOWN_STRAY_FILES:
                violations.append(entry)

    assert not violations, f"Stray .py files at module root ({len(violations)}):\n" + "\n".join(
        f"  {v}" for v in violations
    )
