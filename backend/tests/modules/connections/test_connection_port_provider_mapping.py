"""Tests for ConnectionPortImpl provider→channel_type alias resolution.

Verifies that get_credentials("google_ads") resolves to ChannelType.GOOGLE_ANALYTICS
without raising ValueError, since Google Ads shares OAuth with GA4.
"""

import pytest
from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.connections.application.services.connection_port_impl import (
    ConnectionPortImpl,
    PROVIDER_TO_CHANNEL_TYPE_ALIAS,
)
from src.modules.connections.domain.enums import ChannelType


TENANT_ID = uuid4()


class TestProviderToChannelTypeMapping:
    def test_google_ads_alias_exists(self):
        """google_ads should map to google_analytics."""
        assert PROVIDER_TO_CHANNEL_TYPE_ALIAS["google_ads"] == "google_analytics"

    def test_google_analytics_resolves_directly(self):
        """google_analytics is a valid ChannelType, no alias needed."""
        assert ChannelType("google_analytics") == ChannelType.GOOGLE_ANALYTICS

    def test_google_ads_resolves_via_alias(self):
        """google_ads resolves to google_analytics ChannelType via alias."""
        resolved = PROVIDER_TO_CHANNEL_TYPE_ALIAS.get("google_ads", "google_ads")
        assert ChannelType(resolved) == ChannelType.GOOGLE_ANALYTICS

    def test_unknown_provider_passes_through(self):
        """Unknown providers pass through unmodified."""
        assert PROVIDER_TO_CHANNEL_TYPE_ALIAS.get("meta", "meta") == "meta"

    @pytest.mark.asyncio
    async def test_get_credentials_google_ads_does_not_raise(self):
        """get_credentials('google_ads') should not raise ValueError."""
        mock_db = MagicMock()
        port = ConnectionPortImpl(mock_db)

        # Mock repo to return a connection
        mock_conn = MagicMock()
        mock_conn.credentials = {"access_token": "test", "refresh_token": "test"}
        mock_conn.config = {}
        mock_conn.channel_type = "google_analytics"

        with patch.object(port.repo, "get_active", return_value=mock_conn):
            creds = await port.get_credentials(TENANT_ID, "google_ads")
            assert creds.credentials["access_token"] == "test"
