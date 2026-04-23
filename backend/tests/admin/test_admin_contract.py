"""Contract tests for the admin panel.

These tests guard the wiring between `src/admin/app.py`, `src/admin/pages/`
and `src/admin/modules/`. They catch the most common regression pattern: a
new option in one layer missing from the other, or a renamed render
function that silently breaks a page. They run in `/test-backend` so any
external module refactor must keep the admin panel contract intact.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest

from src.admin.app import PAGE_SPECS, PageSpec

ADMIN_ROOT = Path(__file__).resolve().parents[2] / "src" / "admin"
PAGES_DIR = ADMIN_ROOT / "pages"
MODULES_DIR = ADMIN_ROOT / "modules"

# Modules that are helpers, not pages.
NON_PAGE_MODULES = frozenset({"__init__.py", "_shared.py"})


def _discovered_page_files() -> set[str]:
    return {p.stem for p in PAGES_DIR.glob("*.py") if p.name != "__init__.py"}


def _discovered_module_files() -> list[Path]:
    return [p for p in MODULES_DIR.glob("*.py") if p.name not in NON_PAGE_MODULES]


def _render_calls_in_page(path: Path) -> list[str]:
    """Return the names of top-level `render_*()` calls in a page file."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    calls: list[str] = []
    for node in tree.body:
        if (
            isinstance(node, ast.Expr)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Name)
            and node.value.func.id.startswith("render_")
        ):
            calls.append(node.value.func.id)
    return calls


def _render_functions_in_module(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    return [node.name for node in tree.body if isinstance(node, ast.FunctionDef) and node.name.startswith("render_")]


# ── Registry / file-system parity ───────────────────────────────────────────


def test_every_page_spec_has_a_matching_file() -> None:
    missing = [s.slug for s in PAGE_SPECS if not (PAGES_DIR / f"{s.slug}.py").exists()]
    assert not missing, f"PAGE_SPECS entries without a pages/*.py file: {missing}"


def test_every_page_file_is_registered() -> None:
    registered = {s.slug for s in PAGE_SPECS}
    orphaned = _discovered_page_files() - registered
    assert not orphaned, (
        f"Page files not registered in PAGE_SPECS: {sorted(orphaned)}. "
        "Add a PageSpec in src/admin/app.py or delete the file."
    )


def test_page_slugs_are_unique_and_url_safe() -> None:
    slugs = [s.slug for s in PAGE_SPECS]
    assert len(slugs) == len(set(slugs)), f"Duplicate slugs: {slugs}"
    pattern = re.compile(r"^[a-z][a-z0-9-]*$")
    bad = [s for s in slugs if not pattern.match(s)]
    assert not bad, f"Slugs must be kebab-case lowercase: {bad}"


def test_page_specs_are_frozen_dataclasses() -> None:
    for spec in PAGE_SPECS:
        assert isinstance(spec, PageSpec)
        assert spec.title, f"PageSpec {spec.slug} missing title"
        assert spec.icon, f"PageSpec {spec.slug} missing icon"


# ── Page → render function wiring ───────────────────────────────────────────


def test_every_page_calls_exactly_one_render_function() -> None:
    offenders: dict[str, list[str]] = {}
    for spec in PAGE_SPECS:
        page_file = PAGES_DIR / f"{spec.slug}.py"
        calls = _render_calls_in_page(page_file)
        if len(calls) != 1:
            offenders[spec.slug] = calls
    assert not offenders, f"Each page must call exactly one render_* function: {offenders}"


def test_every_module_exposes_a_render_function() -> None:
    missing: list[str] = []
    for module_path in _discovered_module_files():
        if not _render_functions_in_module(module_path):
            missing.append(module_path.name)
    assert not missing, (
        f"Admin modules without a render_* function: {missing}. "
        "Either add one or move the helper to modules/_shared.py."
    )


# ── Navigation build sanity ─────────────────────────────────────────────────


def test_build_pages_does_not_raise() -> None:
    """Detect navigation-level regressions (bad kwargs, missing st.Page attrs)."""
    from streamlit.navigation.page import StreamlitPage

    from src.admin.app import _build_pages

    pages = _build_pages()
    assert len(pages) == len(PAGE_SPECS)
    assert all(isinstance(p, StreamlitPage) for p in pages)


def test_page_specs_have_stable_order() -> None:
    """First entry is the default route — renaming it is a breaking change."""
    assert PAGE_SPECS[0].slug == "comando", (
        "Default landing page changed. If intentional, update this assertion "
        "and any documentation that references the default URL."
    )


# ── Cross-module import hygiene ─────────────────────────────────────────────


@pytest.mark.parametrize("module_path", _discovered_module_files(), ids=lambda p: p.name)
def test_modules_do_not_import_other_admin_modules(module_path: Path) -> None:
    """Admin modules must not depend on each other (except via _shared)."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    offenders: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith("src.admin.modules.")
            and not node.module.endswith("_shared")
        ):
            offenders.append(node.module)
    assert not offenders, (
        f"{module_path.name} imports from other admin modules: {offenders}. "
        "Shared helpers belong in src/admin/modules/_shared.py."
    )
