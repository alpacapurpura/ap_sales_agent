"""Sales agent ``CopilotProvider`` — F1 shim."""

from __future__ import annotations

from src.modules.copilot.domain.ports import BaseCopilotProvider, ModuleData


class SalesAgentCopilotProvider(BaseCopilotProvider):
    """Sales agent module surface for the copilot."""

    @property
    def module_id(self) -> str:
        return "sales_agent"

    @property
    def label(self) -> str:
        return "Sales Agent"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="sales_agent",
            label="Sales Agent",
            description="Agente de ventas IA: conversaciones activas, mensajes, rendimiento",
            route_prefix="sales",
            model_class=None,
            repo_factory=None,
            read_fn=None,
            keywords=("agente", "ventas", "conversación", "chat", "SDR"),
        )
