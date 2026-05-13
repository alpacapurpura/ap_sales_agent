"""Offer ``CopilotProvider`` — F1 shim, full migration is follow-up."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luana_core_copilot.domain.ports import (
    BaseCopilotProvider,
    DataAccessProvider,
    ModuleData,
    WorkflowProvider,
)
from luana_core_offer_studio.copilot_provider.data_access import OfferDataAccessProvider
from luana_core_offer_studio.copilot_provider.workflows import OfferWorkflowProvider

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_offer_studio.infrastructure.repositories.offer_repository import OfferRepository


def _offer_repo_factory(db: object) -> object:
    from luana_core_offer_studio.infrastructure.repositories.offer_repository import (
        OfferRepository,
    )

    return OfferRepository(db)


def _offer_read_fn(repo: object, tenant_id: UUID) -> list:
    return cast("OfferRepository", repo).get_all_by_tenant(tenant_id)


class OfferCopilotProvider(BaseCopilotProvider):
    """Offer Studio module surface for the copilot."""

    def __init__(self) -> None:
        """Eagerly construct the data accessor — its constructor is cheap."""
        self._data_access = OfferDataAccessProvider()

    @property
    def module_id(self) -> str:
        return "offer"

    @property
    def label(self) -> str:
        return "Offer Studio"

    def data_access(self) -> DataAccessProvider | None:
        return self._data_access  # type: ignore[return-value]

    def workflow_provider(self) -> WorkflowProvider | None:
        return OfferWorkflowProvider()

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="offer",
            label="Offer Studio",
            description=(
                "Escalera de ofertas: productos/servicios con precio,"
                " psicología de venta, avatar, objeciones, knowledge base"
            ),
            route_prefix="offer-studio",
            model_class=None,
            repo_factory=_offer_repo_factory,
            read_fn=_offer_read_fn,
            keywords=("oferta", "producto", "servicio", "precio", "escalera"),
        )
