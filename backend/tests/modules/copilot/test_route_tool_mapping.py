"""
Tests for copilot route-based tool selection.

Validates that:
- Every route in ROUTE_TOOL_MAP resolves to at least one tool
- Known routes resolve to expected tool groups
- Fallback ("*") is used for unknown routes
- get_tools_for_route returns callable LangChain tools (have .name attribute)
- None route uses the "*" fallback
"""


class TestRouteToolMapping:
    def test_all_routes_resolve_to_at_least_one_tool(self):
        """Every route entry in ROUTE_TOOL_MAP yields at least 1 tool."""
        from src.modules.copilot.application.tools.registry import (
            ROUTE_TOOL_MAP,
            get_tools_for_route,
        )

        for route_prefix in ROUTE_TOOL_MAP:
            if route_prefix == "*":
                continue
            tools = get_tools_for_route(f"/tenant-123/{route_prefix}/something")
            assert tools, f"Route '{route_prefix}' resolved to 0 tools"

    def test_brand_studio_includes_mutation_and_awareness(self):
        """brand-studio route includes both mutation and awareness tool groups."""
        from src.modules.copilot.application.tools.registry import ROUTE_TOOL_MAP

        groups = ROUTE_TOOL_MAP.get("brand-studio", [])
        assert "mutation" in groups
        assert "awareness" in groups

    def test_growth_studio_includes_analytics_tools(self):
        """growth-studio route includes the analytics tool group."""
        from src.modules.copilot.application.tools.registry import ROUTE_TOOL_MAP

        groups = ROUTE_TOOL_MAP.get("growth-studio", [])
        assert "analytics" in groups
        assert "crm" in groups

    def test_unknown_route_uses_fallback(self):
        """An unrecognised route uses the '*' fallback group list."""
        from src.modules.copilot.application.tools.registry import get_tools_for_route

        tools_unknown = get_tools_for_route("/tenant/totally-unknown-page")
        tools_fallback = get_tools_for_route(None)  # None also hits fallback

        assert len(tools_unknown) > 0
        assert len(tools_fallback) > 0

    def test_none_route_equals_fallback(self):
        """get_tools_for_route(None) == get_tools_for_route on an unknown route."""
        from src.modules.copilot.application.tools.registry import get_tools_for_route

        none_tools = {t.name for t in get_tools_for_route(None)}
        unknown_tools = {t.name for t in get_tools_for_route("/totally/unknown")}
        assert none_tools == unknown_tools

    def test_tools_have_name_attribute(self):
        """All resolved tools expose a .name attribute (LangChain tool contract)."""
        from src.modules.copilot.application.tools.registry import get_all_tools

        tools = get_all_tools()
        assert tools, "No tools registered at all"
        for t in tools:
            assert hasattr(t, "name"), f"Tool {t!r} is missing .name"
            assert t.name, f"Tool {t!r} has empty .name"


class TestDocumentToolAlwaysPresent:
    """read_document must be available on every route — uploads happen anywhere."""

    def test_read_document_in_brand_studio(self) -> None:
        from src.modules.copilot.application.tools.registry import get_tool_names_for_route

        names = get_tool_names_for_route("/tenant/brand-studio")
        assert "read_document" in names

    def test_read_document_in_growth_studio(self) -> None:
        from src.modules.copilot.application.tools.registry import get_tool_names_for_route

        names = get_tool_names_for_route("/tenant/growth-studio/metrics")
        assert "read_document" in names

    def test_read_document_on_fallback_route(self) -> None:
        from src.modules.copilot.application.tools.registry import get_tool_names_for_route

        names = get_tool_names_for_route(None)
        assert "read_document" in names


class TestProviderRouteMerging:
    """F1 promise (TP10): provider.routes() merges into ROUTE_TOOL_MAP at boot.

    Without this, a discovered provider can declare ``tool_groups()`` and have
    its tools land in ``TOOL_GROUPS``, but the route map keeps using its
    static base — the tool never reaches the LLM unless someone edits
    ``copilot/application/tools/registry.py`` to whitelist the group. That
    breaks the "add a tool without touching ``copilot/``" promise of F1.
    """

    def _synth_provider(self):
        from langchain_core.tools import tool

        from src.modules.copilot.domain.ports import (
            BaseCopilotProvider,
            ProviderRoute,
        )

        @tool
        def _tp10_synth_tool(query: str) -> str:
            """Synthetic tool used by TestProviderRouteMerging only."""
            return f"synth:{query}"

        class _SynthToolProvider:
            def tool_groups(self):
                return {"_tp10_synth_group": [_tp10_synth_tool]}

            def tools(self):
                return (_tp10_synth_tool,)

        class _SynthProvider(BaseCopilotProvider):
            @property
            def module_id(self) -> str:
                return "_tp10_synth"

            @property
            def label(self) -> str:
                return "Synth"

            def routes(self):
                return (ProviderRoute(prefix="*", groups=("_tp10_synth_group",)),)

            def tool_provider(self):
                return _SynthToolProvider()

        return _SynthProvider(), _tp10_synth_tool

    def _patch_discovery_with(self, monkeypatch, provider):
        import importlib

        import src.modules.copilot.application.discovery as disc
        import src.modules.copilot.application.tools.registry as reg

        monkeypatch.setattr(disc, "discover_providers", lambda: {provider.module_id: provider})
        importlib.reload(reg)
        return reg

    def test_provider_routes_extend_wildcard_fallback(self, monkeypatch):
        """Provider declaring ProviderRoute(prefix='*', groups=('X',)) makes
        every route resolution include X's tools — without editing registry.py.
        """
        provider, synth_tool = self._synth_provider()
        reg = self._patch_discovery_with(monkeypatch, provider)

        assert "_tp10_synth_group" in reg.TOOL_GROUPS, "tool_groups merge already worked pre-fix"
        # The architectural fix: routes() must extend ROUTE_TOOL_MAP['*'].
        assert "_tp10_synth_group" in reg.ROUTE_TOOL_MAP["*"], (
            "ROUTE_TOOL_MAP['*'] does not include provider-declared group"
        )
        names = [t.name for t in reg.get_tools_for_route("/copilot")]
        assert synth_tool.name in names, f"{synth_tool.name} missing from {names}"

    def test_provider_routes_extend_specific_prefix(self, monkeypatch):
        """Provider declaring ProviderRoute(prefix='growth-studio', groups=('X',))
        extends the growth-studio route entry without touching the wildcard.
        """
        from langchain_core.tools import tool

        from src.modules.copilot.domain.ports import (
            BaseCopilotProvider,
            ProviderRoute,
        )

        @tool
        def _tp10_growth_tool(query: str) -> str:
            """Synthetic growth-studio tool."""
            return query

        class _GrowthToolProvider:
            def tool_groups(self):
                return {"_tp10_growth_group": [_tp10_growth_tool]}

            def tools(self):
                return (_tp10_growth_tool,)

        class _GrowthProvider(BaseCopilotProvider):
            @property
            def module_id(self) -> str:
                return "_tp10_growth"

            @property
            def label(self) -> str:
                return "Growth Synth"

            def routes(self):
                return (ProviderRoute(prefix="growth-studio", groups=("_tp10_growth_group",)),)

            def tool_provider(self):
                return _GrowthToolProvider()

        provider = _GrowthProvider()
        reg = self._patch_discovery_with(monkeypatch, provider)

        assert "_tp10_growth_group" in reg.ROUTE_TOOL_MAP["growth-studio"]
        # Wildcard fallback NOT polluted:
        assert "_tp10_growth_group" not in reg.ROUTE_TOOL_MAP["*"]

        growth_names = [t.name for t in reg.get_tools_for_route("/tenant/growth-studio/metrics")]
        assert "_tp10_growth_tool" in growth_names

        # Other route does not see the group:
        brand_names = [t.name for t in reg.get_tools_for_route("/tenant/brand-studio/identity")]
        assert "_tp10_growth_tool" not in brand_names

    def test_provider_routes_dedup_on_existing_group(self, monkeypatch):
        """Provider declaring an already-present group on the same prefix is
        a no-op — no duplicate group entry in the route list.
        """
        from src.modules.copilot.domain.ports import (
            BaseCopilotProvider,
            ProviderRoute,
        )

        class _NavExtender(BaseCopilotProvider):
            @property
            def module_id(self) -> str:
                return "_tp10_nav_extender"

            @property
            def label(self) -> str:
                return "Nav Extender"

            def routes(self):
                # 'navigation' is already in ROUTE_TOOL_MAP['brand-studio'] base.
                return (ProviderRoute(prefix="brand-studio", groups=("navigation",)),)

            def tool_provider(self):
                return None

        reg = self._patch_discovery_with(monkeypatch, _NavExtender())
        groups_for_brand = reg.ROUTE_TOOL_MAP["brand-studio"]
        assert groups_for_brand.count("navigation") == 1, f"Duplicate: {groups_for_brand}"
