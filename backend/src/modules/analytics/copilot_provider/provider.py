"""Analytics ``CopilotProvider`` — F1 shim."""

from __future__ import annotations

from luana_core_copilot.domain.ports import BaseCopilotProvider, ModuleData


class AnalyticsCopilotProvider(BaseCopilotProvider):
    """Growth Studio (analytics) module surface for the copilot."""

    @property
    def module_id(self) -> str:
        return "analytics"

    @property
    def label(self) -> str:
        return "Growth Studio"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="analytics",
            label="Growth Studio",
            description=("Métricas de marketing y ventas: funnel bowtie, conversión, revenue, leads por etapa"),
            route_prefix="growth-studio",
            model_class=None,
            repo_factory=None,
            read_fn=None,
            keywords=("funnel", "bowtie", "métricas", "analytics", "growth", "conversión"),
        )
