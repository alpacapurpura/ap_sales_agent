"""CRM ``CopilotProvider`` — F1 shim."""

from __future__ import annotations

from src.modules.copilot.domain.ports import BaseCopilotProvider, ModuleData


class CrmCopilotProvider(BaseCopilotProvider):
    """CRM module surface for the copilot."""

    @property
    def module_id(self) -> str:
        return "crm"

    @property
    def label(self) -> str:
        return "CRM"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="crm",
            label="CRM",
            description=("Leads, clientes y ventas: pipeline, scoring, temperatura, historial de compras"),
            route_prefix="sales",
            model_class=None,
            repo_factory=None,
            read_fn=None,
            keywords=("lead", "cliente", "venta", "pipeline", "CRM"),
        )
