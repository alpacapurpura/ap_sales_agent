"""Tests for ConnectionPortImpl — the bridge between analytics and connections.

Tests cover:
- Credential retrieval for active connections
- ConnectionRevokedException for missing connections
- Token refresh detection and execution for expired tokens
- TokenRefreshFailed when refresh fails
- list_active_connections for multiple/empty connections
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.analytics.domain.exceptions import (
    ConnectionRevokedException,
    TokenRefreshFailed,
)
from src.modules.analytics.domain.ports import ConnectionCredentials


# Fixed test UUIDs
TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _make_connection_model(
    channel_type: str = "meta",
    credentials: dict | None = None,
    config: dict | None = None,
    is_active: bool = True,
):
    """Create a mock ChannelConnectionModel."""
    model = MagicMock()
    model.id = uuid.uuid4()
    model.tenant_id = TENANT_ID
    model.channel_type = channel_type
    model.credentials = credentials or {"access_token": "valid-token"}
    model.config = config or {"page_id": "123"}
    model.is_active = is_active
    return model


class TestConnectionPortImplGetCredentials:
    """Tests for get_credentials()."""

    def test_returns_credentials_for_active_connection_with_valid_token(self):
        """Happy path: active connection exists with non-expired token."""
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        mock_db = MagicMock()
        port = ConnectionPortImpl(mock_db)

        conn = _make_connection_model(
            channel_type="meta",
            credentials={"access_token": "valid-token"},
        )
        port.repo = MagicMock()
        port.repo.get_active = MagicMock(return_value=conn)

        with patch("asyncio.to_thread", new_callable=lambda: _sync_to_thread):
            result = asyncio.get_event_loop().run_until_complete(
                port.get_credentials(TENANT_ID, "meta")
            )

        assert isinstance(result, ConnectionCredentials)
        assert result.channel_type == "meta"
        assert result.credentials["access_token"] == "valid-token"

    def test_raises_connection_revoked_when_no_active_connection(self):
        """No active connection -> ConnectionRevokedException."""
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        mock_db = MagicMock()
        port = ConnectionPortImpl(mock_db)

        port.repo = MagicMock()
        port.repo.get_active = MagicMock(return_value=None)

        with patch("asyncio.to_thread", new_callable=lambda: _sync_to_thread):
            with pytest.raises(ConnectionRevokedException):
                asyncio.get_event_loop().run_until_complete(
                    port.get_credentials(TENANT_ID, "meta")
                )

    def test_detects_expired_token_and_refreshes(self):
        """Expired token triggers _refresh_token, persists, returns refreshed credentials."""
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        mock_db = MagicMock()
        port = ConnectionPortImpl(mock_db)

        # Token expired 10 minutes ago
        expired_at = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        conn = _make_connection_model(
            channel_type="meta",
            credentials={
                "access_token": "expired-token",
                "refresh_token": "valid-refresh",
                "expires_at": expired_at,
            },
        )
        port.repo = MagicMock()
        port.repo.get_active = MagicMock(return_value=conn)
        port.repo.update_credentials = MagicMock(return_value=conn)

        # Mock the refresh to return new credentials
        refreshed_creds = {
            "access_token": "new-token",
            "refresh_token": "valid-refresh",
            "expires_at": (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
        }

        async def mock_refresh(c):
            return refreshed_creds

        port._refresh_token = mock_refresh

        with patch("asyncio.to_thread", new_callable=lambda: _sync_to_thread):
            result = asyncio.get_event_loop().run_until_complete(
                port.get_credentials(TENANT_ID, "meta")
            )

        assert isinstance(result, ConnectionCredentials)
        # Verify update_credentials was called to persist
        port.repo.update_credentials.assert_called_once()

    def test_raises_token_refresh_failed_on_refresh_error(self):
        """When _refresh_token fails, raises TokenRefreshFailed."""
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        mock_db = MagicMock()
        port = ConnectionPortImpl(mock_db)

        expired_at = (datetime.now(timezone.utc) - timedelta(minutes=10)).isoformat()
        conn = _make_connection_model(
            channel_type="meta",
            credentials={
                "access_token": "expired-token",
                "refresh_token": "bad-refresh",
                "expires_at": expired_at,
            },
        )
        port.repo = MagicMock()
        port.repo.get_active = MagicMock(return_value=conn)

        async def mock_refresh_fail(c):
            raise TokenRefreshFailed("Token refresh failed", provider="meta")

        port._refresh_token = mock_refresh_fail

        with patch("asyncio.to_thread", new_callable=lambda: _sync_to_thread):
            with pytest.raises(TokenRefreshFailed):
                asyncio.get_event_loop().run_until_complete(
                    port.get_credentials(TENANT_ID, "meta")
                )


class TestConnectionPortImplListActive:
    """Tests for list_active_connections()."""

    def test_returns_list_of_credentials_for_active_connections(self):
        """Two active connections -> two ConnectionCredentials."""
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        mock_db = MagicMock()
        port = ConnectionPortImpl(mock_db)

        conn1 = _make_connection_model(channel_type="meta", is_active=True)
        conn2 = _make_connection_model(channel_type="google_analytics", is_active=True)
        port.repo = MagicMock()
        port.repo.get_all_by_tenant = MagicMock(return_value=[conn1, conn2])

        with patch("asyncio.to_thread", new_callable=lambda: _sync_to_thread):
            result = asyncio.get_event_loop().run_until_complete(
                port.list_active_connections(TENANT_ID)
            )

        assert len(result) == 2
        assert all(isinstance(c, ConnectionCredentials) for c in result)
        channel_types = {c.channel_type for c in result}
        assert channel_types == {"meta", "google_analytics"}

    def test_returns_empty_list_when_no_connections(self):
        """No connections -> empty list."""
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        mock_db = MagicMock()
        port = ConnectionPortImpl(mock_db)

        port.repo = MagicMock()
        port.repo.get_all_by_tenant = MagicMock(return_value=[])

        with patch("asyncio.to_thread", new_callable=lambda: _sync_to_thread):
            result = asyncio.get_event_loop().run_until_complete(
                port.list_active_connections(TENANT_ID)
            )

        assert result == []

    def test_filters_inactive_connections(self):
        """Only active connections are returned."""
        from src.modules.connections.application.services.connection_port_impl import (
            ConnectionPortImpl,
        )

        mock_db = MagicMock()
        port = ConnectionPortImpl(mock_db)

        active = _make_connection_model(channel_type="meta", is_active=True)
        inactive = _make_connection_model(channel_type="google_analytics", is_active=False)
        port.repo = MagicMock()
        port.repo.get_all_by_tenant = MagicMock(return_value=[active, inactive])

        with patch("asyncio.to_thread", new_callable=lambda: _sync_to_thread):
            result = asyncio.get_event_loop().run_until_complete(
                port.list_active_connections(TENANT_ID)
            )

        assert len(result) == 1
        assert result[0].channel_type == "meta"


# Helper: makes asyncio.to_thread execute synchronously for tests
def _sync_to_thread():
    """Returns an async function that calls the sync fn directly."""

    async def _to_thread(fn, *args, **kwargs):
        return fn(*args, **kwargs)

    return _to_thread
