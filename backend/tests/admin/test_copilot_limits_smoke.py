"""Smoke test for copilot_limits admin page.

Verifies render_copilot_limits_view() doesn't crash with mocked DB.
Pattern: existing admin smoke tests (test_admin_smoke.py).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pytest


def test_copilot_limits_renders_without_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    """render_copilot_limits_view() completes without raising exceptions.

    DB and Streamlit are mocked via autouse fixture in conftest.py.
    This test exercises the real render code path.
    """
    from src.admin.modules.copilot_limits import render_copilot_limits_view

    # _mock_admin_dependencies autouse fixture (conftest.py) stubs:
    # - SessionLocal → stub session (returns empty results)
    # - render_tenant_selector → returns None (no tenant selected)
    # The page should render gracefully in "no tenant selected" state.
    render_copilot_limits_view()  # Should not raise


def test_copilot_limits_module_has_render_function() -> None:
    """Verify the module exposes render_copilot_limits_view (contract test)."""
    import importlib

    mod = importlib.import_module("src.admin.modules.copilot_limits")
    assert hasattr(mod, "render_copilot_limits_view"), (
        "src/admin/modules/copilot_limits.py must expose render_copilot_limits_view()"
    )
    assert callable(mod.render_copilot_limits_view)
