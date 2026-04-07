"""Shared helpers for architectural fitness tests."""

import ast
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
