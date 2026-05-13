"""Connections ``CopilotProvider`` — F1 shim."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from luana_core_copilot.domain.ports import BaseCopilotProvider, ModuleData

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_connections.infrastructure.repositories.channel_connection_repository import (
        ChannelConnectionRepository,
    )


def _connections_repo_factory(db: object) -> object:
    from luana_core_connections.infrastructure.repositories.channel_connection_repository import (
        ChannelConnectionRepository,
    )

    return ChannelConnectionRepository(db)


def _connections_read_fn(repo: object, tenant_id: UUID) -> list:
    return cast("ChannelConnectionRepository", repo).get_all_by_tenant(tenant_id)


class ConnectionsCopilotProvider(BaseCopilotProvider):
    """Connections module surface for the copilot."""

    @property
    def module_id(self) -> str:
        return "connections"

    @property
    def label(self) -> str:
        return "Conexiones"

    def module_data(self) -> ModuleData | None:
        return ModuleData(
            module_id="connections",
            label="Conexiones",
            description=(
                "Integraciones externas: Meta, Instagram, WhatsApp, Shopify,"
                " Google Calendar, Gmail, Mailerlite, YouTube, Google Analytics, Google Ads"
            ),
            route_prefix="connections",
            model_class=None,
            repo_factory=_connections_repo_factory,
            read_fn=_connections_read_fn,
            keywords=("conexión", "integración", "meta", "instagram", "whatsapp", "shopify"),
        )
