"""Tests for ChannelRegistry — validates stage-channel mapping and slug uniqueness.

Tests the static STAGE_CHANNEL_MAP data and the ChannelRegistry class logic
for connected vs. available channel classification.
"""

import uuid
from unittest.mock import AsyncMock

import pytest

from src.modules.analytics.application.services.channel_registry import (
    STAGE_CHANNEL_MAP,
    ChannelRegistry,
    get_stage_channels,
)
from src.modules.analytics.domain.ports import ConnectionCredentials


class TestStageChannelMapStructure:
    """Validate the static STAGE_CHANNEL_MAP data."""

    def test_attraction_has_channels(self):
        """Attraction stage must have at least one channel."""
        channels = STAGE_CHANNEL_MAP.get("attraction", [])
        assert len(channels) > 0, "attraction stage has no channels"

    def test_all_stages_have_channels(self):
        """Every stage in the map must have at least one channel."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            assert len(channels) > 0, f"Stage '{stage}' has no channels"

    def test_all_channels_have_slugs(self):
        """Every channel definition must have a 'slug' key."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            for ch in channels:
                assert "slug" in ch, f"Channel in stage '{stage}' missing slug: {ch.get('name', 'unknown')}"
                assert ch["slug"], f"Channel in stage '{stage}' has empty slug"

    def test_no_duplicate_slugs_per_stage(self):
        """Within each stage, slug values must be unique."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            slugs = [ch["slug"] for ch in channels]
            duplicates = [s for s in set(slugs) if slugs.count(s) > 1]
            assert not duplicates, f"Stage '{stage}' has duplicate slugs: {duplicates}"

    def test_all_channels_have_name(self):
        """Every channel must have a 'name' key."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            for ch in channels:
                assert ch.get("name"), f"Channel slug='{ch.get('slug')}' in stage '{stage}' missing name"

    def test_all_channels_have_channel_type(self):
        """Every channel must have a 'channel_type' key."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            for ch in channels:
                assert ch.get("channel_type"), (
                    f"Channel slug='{ch.get('slug')}' in stage '{stage}' missing channel_type"
                )

    def test_all_channels_have_provider_name(self):
        """Every channel must have a 'provider_name' key."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            for ch in channels:
                assert ch.get("provider_name"), (
                    f"Channel slug='{ch.get('slug')}' in stage '{stage}' missing provider_name"
                )

    def test_all_channels_have_source_label(self):
        """Every channel must have a 'source_label' key."""
        for stage, channels in STAGE_CHANNEL_MAP.items():
            for ch in channels:
                assert ch.get("source_label"), (
                    f"Channel slug='{ch.get('slug')}' in stage '{stage}' missing source_label"
                )


class TestGetStageChannelsFunction:
    """Tests for the module-level get_stage_channels() helper."""

    def test_valid_stage_returns_channels(self):
        """Known stage returns its channel list."""
        channels = get_stage_channels("attraction")
        assert isinstance(channels, list)
        assert len(channels) > 0

    def test_unknown_stage_returns_empty_list(self):
        """Unknown stage returns an empty list, not None or an error."""
        channels = get_stage_channels("nonexistent_stage")
        assert channels == []

    def test_returns_same_data_as_map(self):
        """get_stage_channels mirrors STAGE_CHANNEL_MAP exactly."""
        for stage in STAGE_CHANNEL_MAP:
            assert get_stage_channels(stage) == STAGE_CHANNEL_MAP[stage]


class TestChannelRegistryGetStageChannels:
    """Tests for ChannelRegistry.get_stage_channels (async wrapper)."""

    @pytest.mark.asyncio
    async def test_returns_channels_for_valid_stage(self):
        """get_stage_channels returns the channel list for a known stage."""
        mock_conn_port = AsyncMock()
        registry = ChannelRegistry(connection_port=mock_conn_port)

        channels = await registry.get_stage_channels("capture")
        assert isinstance(channels, list)
        assert len(channels) > 0


class TestChannelRegistryAvailableChannels:
    """Tests for ChannelRegistry.get_available_channels — connected vs. available."""

    @pytest.mark.asyncio
    async def test_internal_providers_always_connected(self):
        """Channels with provider_name='internal' should always be connected."""
        mock_conn_port = AsyncMock()
        mock_conn_port.list_active_connections.return_value = []

        registry = ChannelRegistry(connection_port=mock_conn_port)
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

        result = await registry.get_available_channels(tenant_id, "capture")

        connected_slugs = [ch["slug"] for ch in result["connected"]]
        # "landing-form" is internal in capture stage
        internal_channels = [ch["slug"] for ch in STAGE_CHANNEL_MAP["capture"] if ch.get("provider_name") == "internal"]
        for slug in internal_channels:
            assert slug in connected_slugs, f"Internal channel '{slug}' should be connected"

    @pytest.mark.asyncio
    async def test_connected_provider_shows_connected(self):
        """If tenant has a Meta connection, meta channels show as connected."""
        mock_conn_port = AsyncMock()
        mock_conn_port.list_active_connections.return_value = [
            ConnectionCredentials(
                channel_type="meta",
                credentials={"access_token": "tok"},
                config={"page_id": "123"},
            ),
        ]

        registry = ChannelRegistry(connection_port=mock_conn_port)
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

        result = await registry.get_available_channels(tenant_id, "attraction")

        connected_slugs = [ch["slug"] for ch in result["connected"]]
        # ig-organic uses provider_name="meta" so it should be connected
        assert "ig-organic" in connected_slugs

    @pytest.mark.asyncio
    async def test_disconnected_provider_shows_available(self):
        """If tenant has no TikTok connection, tiktok channels show as available."""
        mock_conn_port = AsyncMock()
        mock_conn_port.list_active_connections.return_value = []

        registry = ChannelRegistry(connection_port=mock_conn_port)
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

        result = await registry.get_available_channels(tenant_id, "attraction")

        available_slugs = [ch["slug"] for ch in result["available"]]
        assert "tiktok-organic" in available_slugs

    @pytest.mark.asyncio
    async def test_available_channels_have_badge_type(self):
        """Available channels should have badge_type='configurar'."""
        mock_conn_port = AsyncMock()
        mock_conn_port.list_active_connections.return_value = []

        registry = ChannelRegistry(connection_port=mock_conn_port)
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

        result = await registry.get_available_channels(tenant_id, "attraction")

        for ch in result["available"]:
            assert ch.get("badge_type") == "configurar", (
                f"Available channel '{ch['slug']}' missing badge_type='configurar'"
            )

    @pytest.mark.asyncio
    async def test_result_has_connected_and_available_keys(self):
        """Result dict must have 'connected' and 'available' keys."""
        mock_conn_port = AsyncMock()
        mock_conn_port.list_active_connections.return_value = []

        registry = ChannelRegistry(connection_port=mock_conn_port)
        tenant_id = uuid.UUID("11111111-1111-1111-1111-111111111111")

        result = await registry.get_available_channels(tenant_id, "attraction")

        assert "connected" in result
        assert "available" in result
        assert isinstance(result["connected"], list)
        assert isinstance(result["available"], list)
