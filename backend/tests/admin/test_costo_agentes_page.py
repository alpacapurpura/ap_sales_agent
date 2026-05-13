"""Costo Agentes admin page — render contract + tabs invariants (S2)."""

from __future__ import annotations

import pytest


class TestCostoAgentesPage:
    def test_module_exposes_render_function(self) -> None:
        from src.admin.modules.costo_agentes import render_costo_agentes

        assert callable(render_costo_agentes)

    def test_page_wrapper_thin_call(self) -> None:
        """The page file must only call render_*; admin-panel rule §pages."""
        from pathlib import Path

        page_path = Path(__file__).resolve().parents[2] / "src" / "admin" / "pages" / "costo-agentes.py"
        body = page_path.read_text(encoding="utf-8")
        assert "render_costo_agentes()" in body
        # No SessionLocal / SQLAlchemy in pages — those live in modules/.
        assert "SessionLocal" not in body
        assert "select(" not in body

    def test_page_registered_in_app(self) -> None:
        from src.admin.app import PAGE_SPECS

        slugs = [spec.slug for spec in PAGE_SPECS]
        assert "costo-agentes" in slugs

    def test_uses_cross_agent_aggregator(self, monkeypatch) -> None:
        """The module imports CrossAgentCostAggregator (registry-based)."""
        from src.admin.modules import costo_agentes

        assert hasattr(costo_agentes, "CrossAgentCostAggregator")

    def test_renders_without_raising(self) -> None:
        """Streamlit AppTest renders the page headless without exceptions."""
        from streamlit.testing.v1 import AppTest

        page_path = "src/admin/pages/costo-agentes.py"
        at = AppTest.from_file(page_path)
        at.run()
        assert not at.exception, f"page raised: {at.exception}"


class TestCrossAgentRegistryWiring:
    def test_registry_known_to_admin(self) -> None:
        """Adding an agent to the registry surfaces it in the page caption."""
        from luana_core_observability.registry import (
            agent_observability_registry,
        )

        kinds = [spec.agent_kind for spec in agent_observability_registry()]
        assert "copilot" in kinds
        assert "sales_agent" in kinds


class TestSharedHelpers:
    def test_render_agent_kind_selector_exposed(self) -> None:
        from src.admin.modules._shared import render_agent_kind_selector

        assert callable(render_agent_kind_selector)

    def test_render_dual_read_banner_exposed(self) -> None:
        from src.admin.modules._shared import render_dual_read_banner

        assert callable(render_dual_read_banner)


@pytest.mark.parametrize(
    "agent_kind",
    ["copilot", "sales_agent"],
)
def test_registry_spec_consistency(agent_kind: str) -> None:
    """Each registered agent has matching env-var names + table names."""
    from luana_core_observability.registry import get_spec

    spec = get_spec(agent_kind)
    assert spec.agent_kind == agent_kind
    assert spec.trace_event_table.endswith("_trace_event")
    assert spec.llm_call_table.endswith("_llm_call")
    assert spec.trace_retention_env_var.endswith("_TRACE_RETENTION_DAYS")
    assert spec.llm_call_retention_env_var.endswith("_LLM_CALL_RETENTION_DAYS")
