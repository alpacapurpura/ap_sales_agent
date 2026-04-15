"""Shared helpers for architectural fitness tests."""

import ast
from pathlib import Path

import pytest

MODULES_DIR = Path(__file__).resolve().parents[2] / "src" / "modules"

# Modules allowed to import from other modules.
# - copilot: AI orchestrator that needs access to all module data for tools.
# - advertising: cross-cuts analytics (campaigns, ad_sets, ads, official_metrics models)
#   and offer (OfferReadPort) to associate campaigns with offers and aggregate
#   per-offer metrics. Documented exception from the offer-campaign-association feature.
CROSS_IMPORT_ALLOWED_SOURCES = {"copilot", "advertising"}

# Modules that any module may import from
CROSS_IMPORT_ALLOWED_TARGETS = {"shared", "core", "iam"}


@pytest.fixture(scope="session")
def all_module_names() -> list[str]:
    """Return all module directory names under src/modules/."""
    return sorted(d.name for d in MODULES_DIR.iterdir() if d.is_dir() and not d.name.startswith("__"))


@pytest.fixture(scope="session")
def all_python_files() -> list[Path]:
    """Return all .py files under src/modules/."""
    return sorted(MODULES_DIR.rglob("*.py"))


def _type_checking_line_ranges(tree: ast.Module) -> list[tuple[int, int]]:
    """Return (start, end) line ranges for `if TYPE_CHECKING:` blocks."""
    ranges: list[tuple[int, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.If) and isinstance(node.test, ast.Name) and node.test.id == "TYPE_CHECKING":
            start = node.lineno
            end = max(getattr(n, "end_lineno", start) for n in ast.walk(node))
            ranges.append((start, end))
    return ranges


def parse_imports(filepath: Path) -> list[str]:
    """Extract runtime import module paths (skips TYPE_CHECKING blocks)."""
    try:
        tree = ast.parse(filepath.read_text(encoding="utf-8"))
    except SyntaxError:
        return []
    tc_ranges = _type_checking_line_ranges(tree)
    imports: list[str] = []
    for node in ast.walk(tree):
        if not hasattr(node, "lineno"):
            continue
        if any(start <= node.lineno <= end for start, end in tc_ranges):
            continue
        if isinstance(node, ast.ImportFrom) and node.module:
            imports.append(node.module)
        elif isinstance(node, ast.Import):
            imports.extend(alias.name for alias in node.names)
    return imports


def module_name_from_path(filepath: Path) -> str:
    """Extract the module name from a file path like src/modules/brand/api/routes.py -> brand."""
    parts = filepath.relative_to(MODULES_DIR).parts
    return parts[0] if parts else ""
