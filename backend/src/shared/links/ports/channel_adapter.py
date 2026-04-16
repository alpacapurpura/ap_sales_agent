"""Channel adapter factories for cross-module communication.

``sales_agent`` uses these to create messaging channel adapters and resolve
connection credentials without importing from ``connections`` directly.

Lazy imports keep the coupling inside ``shared/`` (not scanned by arch test).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.shared.domain.ports import ConnectionPort


def create_telegram_adapter(*, token: str | None = None) -> object:
    """Create a TelegramChannel adapter. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.channels.telegram import (
        TelegramChannel,
    )

    return TelegramChannel(token=token)


def create_whatsapp_adapter(*, tenant_id: str) -> object:
    """Create a WhatsAppChannel adapter. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.channels.whatsapp import (
        WhatsAppChannel,
    )

    return WhatsAppChannel(tenant_id=tenant_id)


def create_instagram_adapter(*, client_config: dict, credentials_data: dict) -> object:
    """Create an InstagramChannel adapter. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.channels.instagram import (
        InstagramChannel,
    )

    return InstagramChannel(
        client_config=client_config,
        credentials_data=credentials_data,
    )


def create_connection_port(db: Session) -> ConnectionPort:
    """Create a ConnectionPortImpl instance. Lazy-imports from connections."""
    from src.modules.connections.application.services.connection_port_impl import (
        ConnectionPortImpl,
    )

    return ConnectionPortImpl(db)


def get_channel_connection_model() -> type:
    """Return the ChannelConnectionModel class. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    return ChannelConnectionModel


def create_manychat_connector() -> type:
    """Return the ManyChatConnector class. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.marketing_connectors.manychat import (
        ManyChatConnector,
    )

    return ManyChatConnector


def create_mailerlite_connector(*, api_key: str) -> object:
    """Create a MailerLiteConnector instance. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.marketing_connectors.mailerlite import (
        MailerLiteConnector,
    )

    return MailerLiteConnector(api_key=api_key)


def create_google_ads_adapter() -> object:
    """Create a GoogleAdsAdapter instance. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.channels.google_ads import (
        GoogleAdsAdapter,
    )

    return GoogleAdsAdapter()


def create_tiktok_adapter() -> object:
    """Create a TikTokAdapter instance. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.channels.tiktok import TikTokAdapter

    return TikTokAdapter()


def create_youtube_adapter(*, credentials_data: dict) -> object:
    """Create a YouTubeAnalyticsAdapter instance. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.channels.youtube_analytics import (
        YouTubeAnalyticsAdapter,
    )

    return YouTubeAnalyticsAdapter(credentials_data=credentials_data)


def create_google_analytics_adapter(*, client_config: dict, credentials_data: dict) -> object:
    """Create a GoogleAnalyticsAdapter instance. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.channels.google_analytics import (
        GoogleAnalyticsAdapter,
    )

    return GoogleAnalyticsAdapter(
        client_config=client_config,
        credentials_data=credentials_data,
    )


def create_search_console_adapter(*, credentials_data: dict) -> object:
    """Create a SearchConsoleAdapter instance. Lazy-imports from connections."""
    from src.modules.connections.infrastructure.channels.search_console import (
        SearchConsoleAdapter,
    )

    return SearchConsoleAdapter(credentials_data=credentials_data)


def get_active_connections_by_type(db: Session, channel_type: str) -> list:
    """Query all active connections of a given type across all tenants.

    Returns list of connection model instances.
    Lazy-imports ChannelConnectionModel from connections.
    """
    from sqlalchemy import and_, select

    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    result = db.execute(
        select(ChannelConnectionModel).where(
            and_(
                ChannelConnectionModel.channel_type == channel_type,
                ChannelConnectionModel.is_active == True,
            ),
        ),
    )
    return result.scalars().all()
