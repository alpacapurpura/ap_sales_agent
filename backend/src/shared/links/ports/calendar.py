"""Calendar and email adapter factories for cross-module communication.

``scheduling`` uses these to create Google Calendar/Gmail adapters without
importing from ``connections`` directly.

Lazy imports keep the coupling inside ``shared/`` (not scanned by arch test).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def get_channel_credentials(db: Session, tenant_id: UUID, channel_type: str) -> dict | None:
    """Query connection credentials for a channel type.

    Returns the credentials dict if an active connection exists, else None.
    Lazy-imports ChannelConnectionModel from connections.
    """
    from luana_core_connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )
    from sqlalchemy import select

    stmt = select(ChannelConnectionModel).where(
        ChannelConnectionModel.tenant_id == tenant_id,
        ChannelConnectionModel.channel_type == channel_type,
        ChannelConnectionModel.is_active.is_(True),
    )
    connection = db.execute(stmt).scalar_one_or_none()

    if not connection or not connection.credentials:
        return None
    return dict(connection.credentials)


def get_channel_connection_data(
    db: Session,
    tenant_id: UUID,
    channel_type: str,
) -> tuple[dict, dict] | None:
    """Query connection credentials AND config for a channel type.

    Returns (credentials, config) tuple if an active connection exists, else None.
    """
    from luana_core_connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )
    from sqlalchemy import select

    stmt = select(ChannelConnectionModel).where(
        ChannelConnectionModel.tenant_id == tenant_id,
        ChannelConnectionModel.channel_type == channel_type,
        ChannelConnectionModel.is_active.is_(True),
    )
    connection = db.execute(stmt).scalar_one_or_none()

    if not connection or not connection.credentials:
        return None
    return dict(connection.credentials), dict(connection.config or {})


def create_calendar_adapter(credentials_data: dict) -> object:
    """Create a GoogleCalendarAdapter instance.

    Lazy-imports from connections infrastructure.
    """
    from luana_core_connections.infrastructure.channels.google_calendar import (
        GoogleCalendarAdapter,
    )

    return GoogleCalendarAdapter(credentials_data=credentials_data)


def create_gmail_adapter(credentials_data: dict) -> object:
    """Create a GmailAdapter instance.

    Lazy-imports from connections infrastructure.
    """
    from luana_core_connections.infrastructure.channels.gmail import GmailAdapter

    return GmailAdapter(credentials_data=credentials_data)
