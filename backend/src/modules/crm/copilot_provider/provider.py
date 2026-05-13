"""CRM ``CopilotProvider`` — F1 shim + F5 data_access surface."""

from __future__ import annotations

from luana_core_copilot.domain.ports import (
    BaseCopilotProvider,
    DataAccessProvider,
    ModuleData,
)
from luana_core_crm.copilot_provider.data_access import CrmDataAccessProvider


class CrmCopilotProvider(BaseCopilotProvider):
    """CRM module surface for the copilot."""

    def __init__(self) -> None:
        """Eagerly construct the data accessor — its constructor is cheap."""
        self._data_access = CrmDataAccessProvider()

    @property
    def module_id(self) -> str:
        return "crm"

    @property
    def label(self) -> str:
        return "CRM"

    def data_access(self) -> DataAccessProvider | None:
        return self._data_access  # type: ignore[return-value]

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
