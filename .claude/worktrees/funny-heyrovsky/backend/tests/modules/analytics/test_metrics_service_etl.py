"""Tests confirming MetricsService reads from official ETL tables.

Verifies that get_attraction_metrics() uses:
- MetricsCache (check before DB query)
- OfficialMetricsRepository.get_channel_summary() (aggregated data)
- ChannelRegistry (dynamic channel list)
- ConnectionPort (connection status)

Instead of the old hardcoded channel definitions + journey_events.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.analytics.application.dto.attraction_dto import (
    AttractionDetailDTO,
    ChannelMetricDTO,
    TrafficGroupDTO,
)


@pytest.fixture
def test_tenant_id():
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_cache():
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    return cache


@pytest.fixture
def mock_connection_port():
    from src.modules.analytics.domain.ports import ConnectionCredentials

    port = AsyncMock()
    # Return some connected channels (meta and google_analytics)
    port.list_active_connections = AsyncMock(
        return_value=[
            ConnectionCredentials(
                channel_type="meta",
                credentials={"access_token": "tok"},
                config={},
            ),
            ConnectionCredentials(
                channel_type="google_analytics",
                credentials={"access_token": "tok2"},
                config={},
            ),
        ]
    )
    return port


@pytest.fixture
def sample_aggregations():
    """Simulate MetricAggregationModel rows returned by get_channel_summary."""
    agg1 = MagicMock()
    agg1.channel_slug = "ig-organic"
    agg1.metric_name = "visitors"
    agg1.value = 1500.0
    agg1.unit = "count"
    agg1.currency = None
    agg1.cost_type = "neutral"
    agg1.extraction_run_id = uuid.uuid4()
    agg1.computed_at = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

    agg2 = MagicMock()
    agg2.channel_slug = "meta-ads"
    agg2.metric_name = "clicks"
    agg2.value = 3200.0
    agg2.unit = "count"
    agg2.currency = "USD"
    agg2.cost_type = "investment"
    agg2.extraction_run_id = uuid.uuid4()
    agg2.computed_at = datetime(2026, 3, 15, 10, 0, 0, tzinfo=timezone.utc)

    return [agg1, agg2]


def _make_service(db, cache=None, connection_port=None):
    """Helper to build MetricsService with ETL dependencies."""
    from src.modules.analytics.application.services.metrics_service import (
        MetricsService,
    )

    return MetricsService(db, cache=cache, connection_port=connection_port)


# ---------------------------------------------------------------------------
# Test: ChannelRegistry provides dynamic channel list (not hardcoded)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_attraction_uses_channel_registry(
    mock_db, mock_cache, mock_connection_port, test_tenant_id
):
    """MetricsService delegates channel list to ChannelRegistry, not hardcoded defs."""
    service = _make_service(mock_db, cache=mock_cache, connection_port=mock_connection_port)

    with patch(
        "src.modules.analytics.application.services.metrics_service.OfficialMetricsRepository"
    ) as MockRepo:
        mock_repo_inst = MagicMock()
        mock_repo_inst.get_channel_summary.return_value = []
        MockRepo.return_value = mock_repo_inst

        with patch(
            "src.modules.analytics.application.services.metrics_service.ChannelRegistry"
        ) as MockReg:
            mock_reg_inst = AsyncMock()
            mock_reg_inst.get_available_channels = AsyncMock(
                return_value={
                    "connected": [
                        {"slug": "ig-organic", "name": "Instagram Organic", "channel_type": "social", "source_label": "Instagram", "provider_name": "meta"},
                    ],
                    "available": [
                        {"slug": "tiktok-organic", "name": "TikTok Organic", "channel_type": "social", "source_label": "TikTok", "provider_name": "tiktok", "badge_type": "configurar"},
                    ],
                }
            )
            MockReg.return_value = mock_reg_inst

            result = await service.get_attraction_metrics(test_tenant_id)

            # ChannelRegistry was used
            mock_reg_inst.get_available_channels.assert_called_once_with(
                test_tenant_id, "attraction"
            )

    assert isinstance(result, AttractionDetailDTO)


# ---------------------------------------------------------------------------
# Test: Populates channel values from OfficialMetricsRepository
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_attraction_populates_values_from_repo(
    mock_db, mock_cache, mock_connection_port, sample_aggregations, test_tenant_id
):
    """Channel metric values come from OfficialMetricsRepository.get_channel_summary()."""
    service = _make_service(mock_db, cache=mock_cache, connection_port=mock_connection_port)

    with patch(
        "src.modules.analytics.application.services.metrics_service.OfficialMetricsRepository"
    ) as MockRepo:
        mock_repo_inst = MagicMock()
        mock_repo_inst.get_channel_summary.return_value = sample_aggregations
        MockRepo.return_value = mock_repo_inst

        with patch(
            "src.modules.analytics.application.services.metrics_service.ChannelRegistry"
        ) as MockReg:
            mock_reg_inst = AsyncMock()
            mock_reg_inst.get_available_channels = AsyncMock(
                return_value={
                    "connected": [
                        {"slug": "ig-organic", "name": "Instagram Organic", "channel_type": "social", "source_label": "Instagram", "provider_name": "meta"},
                        {"slug": "meta-ads", "name": "Meta Ads", "channel_type": "paid", "source_label": "Meta Ads", "provider_name": "meta"},
                    ],
                    "available": [],
                }
            )
            MockReg.return_value = mock_reg_inst

            result = await service.get_attraction_metrics(test_tenant_id)

    # Find the ig-organic channel in organic group
    all_channels = result.organic_social.channels + result.paid.channels
    ig = next((ch for ch in all_channels if ch.slug == "ig-organic"), None)
    assert ig is not None
    assert ig.value == 1500.0

    meta_ads = next((ch for ch in all_channels if ch.slug == "meta-ads"), None)
    assert meta_ads is not None
    assert meta_ads.value == 3200.0


# ---------------------------------------------------------------------------
# Test: Cache hit returns cached result, skips DB
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_attraction_returns_cached_on_hit(
    mock_db, mock_connection_port, test_tenant_id
):
    """On cache hit, OfficialMetricsRepository is NOT called."""
    cached_data = {
        "organic_social": {"totals": {"visitors": 100.0}, "channels": []},
        "ga4_search": {"totals": {}, "channels": []},
        "paid": {"totals": {"spend": 50.0}, "channels": []},
        "outbound": {"totals": {}, "channels": []},
        "available": None,
        "period": "last_30_days",
        "last_updated": None,
    }

    mock_cache = AsyncMock()
    mock_cache.get = AsyncMock(return_value=cached_data)
    mock_cache.set = AsyncMock()

    service = _make_service(mock_db, cache=mock_cache, connection_port=mock_connection_port)

    with patch(
        "src.modules.analytics.application.services.metrics_service.OfficialMetricsRepository"
    ) as MockRepo:
        mock_repo_inst = MagicMock()
        MockRepo.return_value = mock_repo_inst

        result = await service.get_attraction_metrics(test_tenant_id)

        # Repository MUST NOT be called when cache hits
        mock_repo_inst.get_channel_summary.assert_not_called()

    assert isinstance(result, AttractionDetailDTO)
    assert result.organic_social.totals["visitors"] == 100.0


# ---------------------------------------------------------------------------
# Test: Sets cache after DB query
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_get_attraction_sets_cache_after_query(
    mock_db, mock_cache, mock_connection_port, test_tenant_id
):
    """After DB query, result is stored in cache."""
    service = _make_service(mock_db, cache=mock_cache, connection_port=mock_connection_port)

    with patch(
        "src.modules.analytics.application.services.metrics_service.OfficialMetricsRepository"
    ) as MockRepo:
        mock_repo_inst = MagicMock()
        mock_repo_inst.get_channel_summary.return_value = []
        MockRepo.return_value = mock_repo_inst

        with patch(
            "src.modules.analytics.application.services.metrics_service.ChannelRegistry"
        ) as MockReg:
            mock_reg_inst = AsyncMock()
            mock_reg_inst.get_available_channels = AsyncMock(
                return_value={"connected": [], "available": []}
            )
            MockReg.return_value = mock_reg_inst

            await service.get_attraction_metrics(test_tenant_id)

    # Cache set must have been called
    mock_cache.set.assert_called_once()
    call_args = mock_cache.set.call_args
    assert call_args[0][0] == str(test_tenant_id)
    assert call_args[0][1] == "attraction"
    assert call_args[0][2] == "last_30_days"


# ---------------------------------------------------------------------------
# Test: Channels with no data return value=0, connected=False
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_unconnected_channels_return_zero(
    mock_db, mock_cache, mock_connection_port, test_tenant_id
):
    """Available (unconnected) channels have value=0 and connected=False."""
    service = _make_service(mock_db, cache=mock_cache, connection_port=mock_connection_port)

    with patch(
        "src.modules.analytics.application.services.metrics_service.OfficialMetricsRepository"
    ) as MockRepo:
        mock_repo_inst = MagicMock()
        mock_repo_inst.get_channel_summary.return_value = []
        MockRepo.return_value = mock_repo_inst

        with patch(
            "src.modules.analytics.application.services.metrics_service.ChannelRegistry"
        ) as MockReg:
            mock_reg_inst = AsyncMock()
            mock_reg_inst.get_available_channels = AsyncMock(
                return_value={
                    "connected": [],
                    "available": [
                        {"slug": "tiktok-organic", "name": "TikTok Organic", "channel_type": "social", "source_label": "TikTok", "provider_name": "tiktok", "badge_type": "configurar"},
                    ],
                }
            )
            MockReg.return_value = mock_reg_inst

            result = await service.get_attraction_metrics(test_tenant_id)

    assert result.available is not None
    tiktok = next((ch for ch in result.available.channels if ch.slug == "tiktok-organic"), None)
    assert tiktok is not None
    assert tiktok.value == 0
    assert tiktok.connected is False


# ---------------------------------------------------------------------------
# Test: Connected channels include last_updated
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_connected_channels_include_last_updated(
    mock_db, mock_cache, mock_connection_port, sample_aggregations, test_tenant_id
):
    """Connected channels that have aggregation data include last_updated timestamp."""
    service = _make_service(mock_db, cache=mock_cache, connection_port=mock_connection_port)

    with patch(
        "src.modules.analytics.application.services.metrics_service.OfficialMetricsRepository"
    ) as MockRepo:
        mock_repo_inst = MagicMock()
        mock_repo_inst.get_channel_summary.return_value = sample_aggregations
        MockRepo.return_value = mock_repo_inst

        with patch(
            "src.modules.analytics.application.services.metrics_service.ChannelRegistry"
        ) as MockReg:
            mock_reg_inst = AsyncMock()
            mock_reg_inst.get_available_channels = AsyncMock(
                return_value={
                    "connected": [
                        {"slug": "ig-organic", "name": "Instagram Organic", "channel_type": "social", "source_label": "Instagram", "provider_name": "meta"},
                    ],
                    "available": [],
                }
            )
            MockReg.return_value = mock_reg_inst

            result = await service.get_attraction_metrics(test_tenant_id)

    ig = next((ch for ch in result.organic_social.channels if ch.slug == "ig-organic"), None)
    assert ig is not None
    assert ig.last_updated is not None
    assert ig.connected is True


# ---------------------------------------------------------------------------
# Test: No cache dependency still works (backward compatibility)
# ---------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_works_without_cache(mock_db, mock_connection_port, test_tenant_id):
    """When cache=None, service queries DB directly without caching."""
    service = _make_service(mock_db, cache=None, connection_port=mock_connection_port)

    with patch(
        "src.modules.analytics.application.services.metrics_service.OfficialMetricsRepository"
    ) as MockRepo:
        mock_repo_inst = MagicMock()
        mock_repo_inst.get_channel_summary.return_value = []
        MockRepo.return_value = mock_repo_inst

        with patch(
            "src.modules.analytics.application.services.metrics_service.ChannelRegistry"
        ) as MockReg:
            mock_reg_inst = AsyncMock()
            mock_reg_inst.get_available_channels = AsyncMock(
                return_value={"connected": [], "available": []}
            )
            MockReg.return_value = mock_reg_inst

            result = await service.get_attraction_metrics(test_tenant_id)

    assert isinstance(result, AttractionDetailDTO)
