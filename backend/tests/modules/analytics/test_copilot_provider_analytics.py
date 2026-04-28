"""Tests for AnalyticsCopilotProvider."""


class TestAnalyticsCopilotProvider:
    def _make(self):
        from src.modules.analytics.copilot_provider.provider import AnalyticsCopilotProvider

        return AnalyticsCopilotProvider()

    def test_module_id(self):
        assert self._make().module_id == "analytics"

    def test_label(self):
        assert self._make().label == "Growth Studio"

    def test_module_data_returns_module_data(self):
        from src.modules.copilot.domain.ports import ModuleData

        result = self._make().module_data()
        assert isinstance(result, ModuleData)

    def test_module_data_fields(self):
        result = self._make().module_data()
        assert result.module_id == "analytics"
        assert result.label == "Growth Studio"
        assert result.route_prefix == "growth-studio"
        assert result.model_class is None
        assert result.repo_factory is None
        assert result.read_fn is None

    def test_module_data_has_keywords(self):
        result = self._make().module_data()
        assert "funnel" in result.keywords
        assert "analytics" in result.keywords
