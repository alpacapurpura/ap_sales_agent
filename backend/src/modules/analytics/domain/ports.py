"""Domain ports (ABCs) for analytics provider infrastructure.

ConnectionPort defines how the analytics module obtains credentials
from the connections bounded context without coupling to it directly.
"""

from abc import ABC, abstractmethod
from typing import List
from uuid import UUID

from pydantic import BaseModel


class ConnectionCredentials(BaseModel):
    """Value object carrying credentials and config for a single connection."""

    channel_type: str
    credentials: dict
    config: dict


class ConnectionPort(ABC):
    """Port for accessing connection credentials across bounded contexts.

    Implemented by an adapter in the infrastructure layer that queries
    the connections module's ChannelConnectionModel.
    """

    @abstractmethod
    async def get_credentials(
        self, tenant_id: UUID, channel_type: str
    ) -> ConnectionCredentials:
        """Retrieve credentials for a specific channel type and tenant."""
        ...

    @abstractmethod
    async def list_active_connections(
        self, tenant_id: UUID
    ) -> List[ConnectionCredentials]:
        """List all active connections for a tenant."""
        ...
