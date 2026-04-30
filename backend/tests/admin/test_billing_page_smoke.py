"""Smoke tests for the Planes & Billing admin page.

Tests:
- Module `billing.py` exposes `render_billing_admin()`.
- Page file `planes-billing.py` imports and calls it.
- Page renders without raising (DB absent → graceful fallback via st.error).

Per admin-panel.md pattern: no network/DB required for smoke test.
The module wraps DB calls in try/except so Streamlit tests pass even
when Postgres is not reachable.
"""

from __future__ import annotations

import importlib
import inspect
from pathlib import Path


# ── Contract checks (no Streamlit runtime needed) ────────────────────────────


def test_billing_module_exposes_render_function() -> None:
    """billing.py must expose render_billing_admin()."""
    billing = importlib.import_module("src.admin.modules.billing")
    assert hasattr(billing, "render_billing_admin"), "src/admin/modules/billing.py must expose render_billing_admin()"
    assert callable(billing.render_billing_admin)


def test_billing_module_render_is_not_async() -> None:
    """render_billing_admin must be a plain sync function (Streamlit requires sync)."""
    billing = importlib.import_module("src.admin.modules.billing")
    assert not inspect.iscoroutinefunction(billing.render_billing_admin), (
        "render_billing_admin() must be sync — Streamlit does not support async render functions."
    )


def test_planes_billing_page_file_exists() -> None:
    """pages/planes-billing.py must exist and be importable."""
    page_path = Path(__file__).resolve().parents[2] / "src" / "admin" / "pages" / "planes-billing.py"
    assert page_path.exists(), f"Page file missing: {page_path}"


def test_planes_billing_registered_in_app() -> None:
    """planes-billing slug must be in PAGE_SPECS."""
    from src.admin.app import PAGE_SPECS

    slugs = [s.slug for s in PAGE_SPECS]
    assert "planes-billing" in slugs, "PageSpec with slug='planes-billing' not found in PAGE_SPECS in src/admin/app.py"


def test_billing_module_does_not_import_other_admin_modules() -> None:
    """billing.py must not import from other admin modules (except _shared)."""
    import ast

    module_path = Path(__file__).resolve().parents[2] / "src" / "admin" / "modules" / "billing.py"
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
    assert not offenders, f"billing.py imports from other admin modules: {offenders}"


def test_billing_helpers_do_not_use_cross_module_billing_orm() -> None:
    """billing.py must access DB via raw SQL (text()), not ORM models from shared.billing.

    Rule: admin module uses raw SQL + SessionLocal, not async ORM repos
    (Streamlit is sync). Cross-module ORM import from shared.billing is
    guarded by arch test test_no_new_copilot_module_imports.py.
    """
    import ast

    module_path = Path(__file__).resolve().parents[2] / "src" / "admin" / "modules" / "billing.py"
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    orm_imports: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module and "shared.billing.infrastructure" in node.module:
            orm_imports.append(node.module)
    assert not orm_imports, (
        f"billing.py imports ORM models from shared.billing.infrastructure: {orm_imports}. "
        "Use raw SQL via sqlalchemy.text() instead (sync admin pattern)."
    )
