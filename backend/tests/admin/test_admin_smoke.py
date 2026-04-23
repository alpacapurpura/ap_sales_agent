"""Headless smoke tests for every admin page.

Regression net: whenever *any* module the admin depends on changes — a repo
rename, a DTO shape shift, a removed helper — these tests re-render each
page with stubbed I/O and fail if it raises. They do not assert on the
panel's visual output, only that the render pipeline stays callable.

Runs in `/test-backend`. Each page has ~30s budget; total suite is fast.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from src.admin.app import PAGE_SPECS, PageSpec

PAGES_DIR = Path(__file__).resolve().parents[2] / "src" / "admin" / "pages"


def _render_page(spec: PageSpec) -> AppTest:
    page_path = PAGES_DIR / f"{spec.slug}.py"
    at = AppTest.from_file(str(page_path), default_timeout=30)
    return at.run()


@pytest.mark.parametrize("spec", PAGE_SPECS, ids=lambda s: s.slug)
def test_page_renders_without_raising(spec: PageSpec) -> None:
    """Every registered page runs its render_* call to completion."""
    at = _render_page(spec)
    # `at.exception` surfaces uncaught errors. Each render wraps work in
    # try/except to turn failures into st.error() — that's acceptable.
    # What we guard against is a hard crash that breaks the whole panel.
    assert not at.exception, f"Page '{spec.slug}' raised: {[str(e.value) for e in at.exception]}"


@pytest.mark.parametrize("spec", PAGE_SPECS, ids=lambda s: s.slug)
def test_page_renders_a_title(spec: PageSpec) -> None:
    """Each page should render its own title — otherwise the menu has a dead entry."""
    at = _render_page(spec)
    if at.exception:
        pytest.fail(f"Page '{spec.slug}' failed before rendering: {at.exception}")
    assert at.title or at.header, (
        f"Page '{spec.slug}' produced no st.title()/st.header(). Add one to the matching module's render_* function."
    )


def test_entrypoint_boots() -> None:
    """`app.py` itself must run without crashing (navigation build + imports)."""
    app_path = Path(__file__).resolve().parents[2] / "src" / "admin" / "app.py"
    at = AppTest.from_file(str(app_path), default_timeout=30).run()
    assert not at.exception, f"app.py crashed on boot: {[str(e.value) for e in at.exception]}"
