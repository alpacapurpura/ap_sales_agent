"""Tests for ChannelRegistry — stage-contextual channel mapping and connected/available split.

Validates that:
- get_stage_channels returns the correct channels for each stage
- get_available_channels splits into connected + available with badge_type
- Disconnected channels show badge_type="configurar"
- Different stages return different channel lists
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.modules.analytics.application.services.channel_registry import (
    ChannelRegistry,
    get_stage_channels,
)
from src.modules.analytics.domain.ports import ConnectionCredentials, ConnectionPort


@pytest.fixture
def mock_connection_port():
    """Mock ConnectionPort that simulates connected providers."""
    port = AsyncMock(spec=ConnectionPort)
    return port


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


@pytest.fixture
def registry(mock_connection_port):
    return ChannelRegistry(connection_port=mock_connection_port)


class TestGetStageChannels:
    """Tests for the static stage-to-channel mapping."""

    def test_attraction_returns_organic_and_paid(self):
        """Attraction stage includes both organic and paid channels."""
        channels = get_stage_channels("attraction")
        slugs = [ch["slug"] for ch in channels]

        # Organic channels
        assert "ig-organic" in slugs
        assert "yt-organic" in slugs
        assert "google-organic" in slugs

        # Paid channels
        assert "meta-ads" in slugs
        assert "google-ads" in slugs

    def test_capture_returns_capture_channels(self):
        """Capture stage returns landing, messaging, and email channels."""
        channels = get_stage_channels("capture")
        slugs = [ch["slug"] for ch in channels]

        assert "landing-form" in slugs
        assert "mailerlite" in slugs
        assert "ig-dm" in slugs

    def test_different_stages_return_different_channels(self):
        """Attraction and capture stages have different channel lists."""
        attraction = get_stage_channels("attraction")
        capture = get_stage_channels("capture")

        attraction_slugs = {ch["slug"] for ch in attraction}
        capture_slugs = {ch["slug"] for ch in capture}

        # They should not be identical
        assert attraction_slugs != capture_slugs

    def test_unknown_stage_returns_empty_list(self):
        """An unknown stage returns an empty list."""
        channels = get_stage_channels("nonexistent-stage")
        assert channels == []

    def test_channel_has_required_fields(self):
        """Each channel definition includes required metadata fields."""
        channels = get_stage_channels("attraction")
        assert len(channels) > 0

        for ch in channels:
            assert "slug" in ch
            assert "name" in ch
            assert "channel_type" in ch


class TestGetAvailableChannels:
    """Tests for the connected/available split based on ConnectionPort."""

    @pytest.mark.asyncio
    async def test_connected_channels_listed_first(
        self, registry, mock_connection_port, tenant_id
    ):
        """Connected channels appear in the 'connected' list."""
        mock_connection_port.list_active_connections.return_value = [
            ConnectionCredentials(
                channel_type="meta-ads",
                credentials={"access_token": "tok123"},
                config={},
            ),
        ]

        result = await registry.get_available_channels(tenant_id, "attraction")

        connected_slugs = [ch["slug"] for ch in result["connected"]]
        assert "meta-ads" in connected_slugs

    @pytest.mark.asyncio
    async def test_disconnected_channels_have_configurar_badge(
        self, registry, mock_connection_port, tenant_id
    ):
        """Channels not connected show badge_type='configurar'."""
        # No connections at all
        mock_connection_port.list_active_connections.return_value = []

        result = await registry.get_available_channels(tenant_id, "attraction")

        assert len(result["available"]) > 0
        for ch in result["available"]:
            assert ch["connected"] is False
            assert ch["badge_type"] == "configurar"

    @pytest.mark.asyncio
    async def test_connected_channels_marked_true(
        self, registry, mock_connection_port, tenant_id
    ):
        """Connected channels have connected=True."""
        mock_connection_port.list_active_connections.return_value = [
            ConnectionCredentials(
                channel_type="ig-organic",
                credentials={"access_token": "tok"},
                config={},
            ),
        ]

        result = await registry.get_available_channels(tenant_id, "attraction")

        connected = result["connected"]
        assert len(connected) >= 1
        for ch in connected:
            assert ch["connected"] is True

    @pytest.mark.asyncio
    async def test_all_channels_accounted_for(
        self, registry, mock_connection_port, tenant_id
    ):
        """Total of connected + available equals total stage channels."""
        mock_connection_port.list_active_connections.return_value = [
            ConnectionCredentials(
                channel_type="meta-ads",
                credentials={},
                config={},
            ),
        ]

        result = await registry.get_available_channels(tenant_id, "attraction")

        total_stage = len(get_stage_channels("attraction"))
        total_result = len(result["connected"]) + len(result["available"])
        assert total_result == total_stage
