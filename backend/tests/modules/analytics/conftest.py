import uuid
from datetime import date
from unittest.mock import AsyncMock, MagicMock

import pytest
from uuid import UUID


@pytest.fixture
def test_tenant_id() -> UUID:
    """Fixed tenant UUID for test determinism."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_credentials() -> dict:
    """Simulated OAuth credentials dict."""
    return {
        "access_token": "test-access-token-abc123",
        "refresh_token": "test-refresh-token-xyz789",
    }


@pytest.fixture
def mock_connection_credentials():
    """ConnectionCredentials instance for testing."""
    from src.modules.analytics.domain.ports import ConnectionCredentials

    return ConnectionCredentials(
        channel_type="meta",
        credentials={"access_token": "test-token"},
        config={"page_id": "123456"},
    )


@pytest.fixture
def sample_offer_id() -> UUID:
    """Fixed offer UUID for test determinism."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def sample_customer_id() -> UUID:
    """Fixed customer UUID for test determinism."""
    return uuid.UUID("33333333-3333-3333-3333-333333333333")


# ── New fixtures ─────────────────────────────────────────────────────────────


@pytest.fixture
def date_range() -> tuple[date, date]:
    """Fixed 14-day date range for test determinism."""
    return (date(2026, 3, 1), date(2026, 3, 14))


@pytest.fixture
def mock_db_session() -> MagicMock:
    """MagicMock DB session with async execute/commit/rollback."""
    session = MagicMock()
    session.execute = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    return session


@pytest.fixture
def mock_cache() -> AsyncMock:
    """AsyncMock cache that always returns None (cache miss)."""
    cache = AsyncMock()
    cache.get = AsyncMock(return_value=None)
    cache.set = AsyncMock()
    cache.invalidate_tenant = AsyncMock()
    return cache


@pytest.fixture
def make_extracted_metric():
    """Factory fixture for ExtractedMetric objects."""
    from src.modules.analytics.infrastructure.providers.base import ExtractedMetric

    def _factory(**overrides):
        defaults = {
            "provider": "meta",
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 1000.0,
            "unit": "count",
            "date": date(2026, 3, 10),
        }
        defaults.update(overrides)
        return ExtractedMetric(**defaults)

    return _factory


@pytest.fixture
def make_extraction_result():
    """Factory fixture for ExtractionResult objects."""
    from src.modules.analytics.domain.extraction_result import ExtractionResult

    def _factory(metrics=None, failures=None):
        return ExtractionResult(
            metrics=metrics or [],
            failures=failures or [],
        )

    return _factory


@pytest.fixture
def sample_official_metrics(test_tenant_id) -> list[dict]:
    """Sample official_metrics row dicts for aggregation tests."""
    return [
        {
            "tenant_id": test_tenant_id,
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 1000.0,
            "unit": "count",
            "currency": None,
            "cost_type": "investment",
            "metric_date": date(2026, 3, 1),
        },
        {
            "tenant_id": test_tenant_id,
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 1500.0,
            "unit": "count",
            "currency": None,
            "cost_type": "investment",
            "metric_date": date(2026, 3, 2),
        },
        {
            "tenant_id": test_tenant_id,
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "value": 800.0,
            "unit": "count",
            "currency": None,
            "cost_type": "investment",
            "metric_date": date(2026, 3, 3),
        },
    ]
