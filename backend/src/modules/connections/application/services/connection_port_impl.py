"""ConnectionPort implementation — bridges analytics and connections modules.

Lives in the connections module because it accesses ChannelConnectionRepository
directly. Implements the ConnectionPort ABC defined in the analytics domain
so analytics never imports from connections directly.

Transparently refreshes expired OAuth tokens before returning credentials.
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List
from uuid import UUID

import httpx
from sqlalchemy.orm import Session

from src.modules.analytics.domain.exceptions import (
    ConnectionRevokedException,
    TokenRefreshFailed,
)
from src.modules.analytics.domain.ports import ConnectionCredentials, ConnectionPort
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository,
)

logger = logging.getLogger(__name__)

# Channel types that use Meta OAuth token exchange
META_CHANNEL_TYPES = {
    ChannelType.META.value,
    ChannelType.FACEBOOK_PAGE.value,
    ChannelType.INSTAGRAM_ACCOUNT.value,
    ChannelType.META_ADS_ACCOUNT.value,
}

# Channel types that use Google OAuth refresh tokens
GOOGLE_CHANNEL_TYPES = {
    ChannelType.GOOGLE_ANALYTICS.value,
    ChannelType.YOUTUBE_ANALYTICS.value,
    ChannelType.GMAIL.value,
    ChannelType.GOOGLE_CALENDAR.value,
}

# Buffer before actual expiry to proactively refresh (5 minutes)
EXPIRY_BUFFER_SECONDS = 300


# Provider name → actual ChannelType value for credential resolution.
# Some providers (e.g. google_ads) share OAuth credentials with another
# channel type (google_analytics). This map resolves the alias before lookup.
PROVIDER_TO_CHANNEL_TYPE_ALIAS = {
    "google_ads": "google_analytics",  # Google Ads uses same Google OAuth as GA4
}


class ConnectionPortImpl(ConnectionPort):
    """Adapter implementing ConnectionPort for the connections bounded context.

    Retrieves decrypted credentials from ChannelConnectionRepository and
    transparently refreshes expired OAuth tokens, persisting the new tokens.
    """

    def __init__(self, db: Session):
        self.db = db
        self.repo = ChannelConnectionRepository(db)

    async def get_credentials(
        self, tenant_id: UUID, channel_type: str
    ) -> ConnectionCredentials:
        """Retrieve credentials for a specific channel, refreshing expired tokens."""
        # Resolve provider alias → actual ChannelType value
        resolved = PROVIDER_TO_CHANNEL_TYPE_ALIAS.get(channel_type, channel_type)
        try:
            channel_enum = ChannelType(resolved)
        except ValueError:
            raise ConnectionRevokedException(
                f"Unknown channel type: {channel_type}",
                channel_type=channel_type,
            )

        conn = await asyncio.to_thread(
            self.repo.get_active, tenant_id, channel_enum
        )

        if conn is None:
            raise ConnectionRevokedException(
                f"No active connection for {channel_type}",
                channel_type=channel_type,
            )

        # Check if token needs refresh
        credentials = conn.credentials or {}
        if self._is_token_expired(credentials):
            logger.info(
                "Token expired for tenant=%s channel=%s, attempting refresh",
                tenant_id,
                channel_type,
            )
            try:
                refreshed = await self._refresh_token(conn)
                # Persist refreshed credentials
                conn.credentials = refreshed
                await asyncio.to_thread(
                    self.repo.update_credentials, conn, refreshed
                )
                credentials = refreshed
            except TokenRefreshFailed:
                raise
            except Exception as exc:
                raise TokenRefreshFailed(
                    f"Token refresh failed for {channel_type}: {exc}",
                    provider=channel_type,
                ) from exc

        return ConnectionCredentials(
            channel_type=channel_type,
            credentials=credentials,
            config=conn.config or {},
        )

    async def list_active_connections(
        self, tenant_id: UUID
    ) -> List[ConnectionCredentials]:
        """List all active connections for a tenant."""
        connections = await asyncio.to_thread(
            self.repo.get_all_by_tenant, tenant_id
        )

        return [
            ConnectionCredentials(
                channel_type=conn.channel_type,
                credentials=conn.credentials or {},
                config=conn.config or {},
            )
            for conn in connections
            if conn.is_active
        ]

    def _is_token_expired(self, credentials: dict) -> bool:
        """Check if the access token is expired or about to expire."""
        expires_at_str = credentials.get("expires_at")
        if not expires_at_str:
            return False

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            buffer = timedelta(seconds=EXPIRY_BUFFER_SECONDS)
            return datetime.now(timezone.utc) >= (expires_at - buffer)
        except (ValueError, TypeError):
            logger.warning("Could not parse expires_at: %s", expires_at_str)
            return False

    async def _refresh_token(self, conn) -> dict:
        """Refresh the OAuth token for the given connection.

        Supports Meta (token exchange) and Google (refresh_token grant).
        """
        channel_type = conn.channel_type
        credentials = conn.credentials or {}
        config = conn.config or {}

        if channel_type in META_CHANNEL_TYPES:
            return await self._refresh_meta_token(credentials, config)
        elif channel_type in GOOGLE_CHANNEL_TYPES:
            return await self._refresh_google_token(credentials, config)
        else:
            raise TokenRefreshFailed(
                f"Token refresh not implemented for {channel_type}",
                provider=channel_type,
            )

    async def _refresh_meta_token(
        self, credentials: dict, config: dict
    ) -> dict:
        """Refresh a Meta/Facebook access token via token exchange."""
        access_token = credentials.get("access_token")
        client_id = config.get("client_id") or config.get("app_id")
        client_secret = config.get("client_secret") or config.get("app_secret")

        if not access_token:
            raise TokenRefreshFailed(
                "No access_token for Meta refresh", provider="meta"
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                "https://graph.facebook.com/v24.0/oauth/access_token",
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "fb_exchange_token": access_token,
                },
            )

        if response.status_code != 200:
            raise TokenRefreshFailed(
                f"Meta token refresh failed: {response.status_code} {response.text}",
                provider="meta",
            )

        data = response.json()
        new_credentials = {**credentials}
        new_credentials["access_token"] = data["access_token"]
        if "expires_in" in data:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=data["expires_in"]
            )
            new_credentials["expires_at"] = expires_at.isoformat()

        return new_credentials

    async def _refresh_google_token(
        self, credentials: dict, config: dict
    ) -> dict:
        """Refresh a Google OAuth token via refresh_token grant."""
        refresh_token = credentials.get("refresh_token")
        client_id = config.get("client_id")
        client_secret = config.get("client_secret")

        if not refresh_token:
            raise TokenRefreshFailed(
                "No refresh_token for Google refresh", provider="google"
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "refresh_token",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                },
            )

        if response.status_code != 200:
            raise TokenRefreshFailed(
                f"Google token refresh failed: {response.status_code} {response.text}",
                provider="google",
            )

        data = response.json()
        new_credentials = {**credentials}
        new_credentials["access_token"] = data["access_token"]
        if "expires_in" in data:
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=data["expires_in"]
            )
            new_credentials["expires_at"] = expires_at.isoformat()

        return new_credentials
