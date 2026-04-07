"""Tests for the scheduler tick function.

Validates timezone-aware 3am matching, extraction_priority ordering,
and proper job enqueue behavior.
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.analytics.workers.scheduler import run_tick_scheduler


def _make_tenant(tenant_id, tz_name, priority, is_active=True):
    """Create a mock tenant with the given timezone and priority."""
    tenant = MagicMock()
    tenant.id = tenant_id
    tenant.timezone = tz_name
    tenant.extraction_priority = priority
    tenant.is_active = is_active
    tenant.weekly_start_day = 0
    tenant.fiscal_year_start_month = 1
    tenant.fiscal_year_start_day = 1
    return tenant


@pytest.fixture
def tenants():
    """Three tenants across different timezones with different priorities."""
    return [
        # Ordered by extraction_priority DESC (as the query returns them)
        _make_tenant(uuid.uuid4(), "America/Bogota", 10),  # UTC-5, highest priority
        _make_tenant(uuid.uuid4(), "Asia/Tokyo", 5),  # UTC+9
        _make_tenant(uuid.uuid4(), "UTC", 0),  # UTC
    ]


@pytest.fixture
def mock_ctx():
    """Mock ARQ context with DB factory and redis."""
    mock_db = MagicMock()
    mock_db_factory = MagicMock(return_value=mock_db)
    mock_redis = AsyncMock()

    ctx = {
        "db_factory": mock_db_factory,
        "redis": mock_redis,
    }
    return ctx, mock_db, mock_redis


@pytest.mark.asyncio
async def test_tick_enqueues_tenant_at_3am_local(tenants, mock_ctx):
    """When UTC is 08:00, it's 3:00 AM in America/Bogota (UTC-5).

    Only the Bogota tenant should be enqueued.
    """
    ctx, mock_db, mock_redis = mock_ctx

    # 08:00 UTC = 3:00 AM America/Bogota (UTC-5)
    # 08:00 UTC = 17:00 Asia/Tokyo (UTC+9)
    # 08:00 UTC = 08:00 UTC
    fixed_utc = datetime(2026, 3, 15, 8, 0, 0, tzinfo=timezone.utc)

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = tenants
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch("src.modules.analytics.workers.scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_utc
        mock_datetime.side_effect = datetime

        await run_tick_scheduler(ctx)

    # Only Bogota tenant (3am match) should be enqueued
    assert mock_redis.enqueue_job.await_count == 1
    call_args = mock_redis.enqueue_job.await_args
    assert call_args[0][0] == "run_tenant_extraction"
    assert call_args[0][1] == str(tenants[0].id)  # Bogota tenant


@pytest.mark.asyncio
async def test_tick_no_enqueue_when_no_3am_match(tenants, mock_ctx):
    """When UTC is 12:00, no tenant is at 3:00 AM local time."""
    ctx, mock_db, mock_redis = mock_ctx

    # 12:00 UTC = 7:00 AM Bogota, 21:00 Tokyo, 12:00 UTC — none at 3am
    fixed_utc = datetime(2026, 3, 15, 12, 0, 0, tzinfo=timezone.utc)

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = tenants
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    with patch("src.modules.analytics.workers.scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_utc
        mock_datetime.side_effect = datetime

        await run_tick_scheduler(ctx)

    assert mock_redis.enqueue_job.await_count == 0


@pytest.mark.asyncio
async def test_tick_tenants_ordered_by_priority(mock_ctx):
    """Verify the SQL query orders by extraction_priority DESC."""
    ctx, mock_db, _mock_redis = mock_ctx

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = []
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    fixed_utc = datetime(2026, 3, 15, 8, 0, 0, tzinfo=timezone.utc)

    with patch("src.modules.analytics.workers.scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_utc
        mock_datetime.side_effect = datetime

        await run_tick_scheduler(ctx)

    # Verify execute was called (the query contains the ORDER BY)
    assert mock_db.execute.called
    # Extract the compiled query to verify ordering
    stmt = mock_db.execute.call_args[0][0]
    compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
    assert "extraction_priority" in compiled.lower()
    assert "desc" in compiled.lower()


@pytest.mark.asyncio
async def test_tick_multiple_tenants_at_3am(mock_ctx):
    """When multiple tenants share a timezone that's at 3am, all are enqueued."""
    ctx, mock_db, mock_redis = mock_ctx

    # Two tenants in Bogota timezone
    tenants_bogota = [
        _make_tenant(uuid.uuid4(), "America/Bogota", 10),
        _make_tenant(uuid.uuid4(), "America/Bogota", 5),
    ]

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = tenants_bogota
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    # 08:00 UTC = 3:00 AM Bogota
    fixed_utc = datetime(2026, 3, 15, 8, 0, 0, tzinfo=timezone.utc)

    with patch("src.modules.analytics.workers.scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_utc
        mock_datetime.side_effect = datetime

        await run_tick_scheduler(ctx)

    assert mock_redis.enqueue_job.await_count == 2


@pytest.mark.asyncio
async def test_tick_handles_invalid_timezone(mock_ctx):
    """Invalid timezone on a tenant is skipped without crashing."""
    ctx, mock_db, mock_redis = mock_ctx

    tenants_mixed = [
        _make_tenant(uuid.uuid4(), "Invalid/Timezone", 10),
        _make_tenant(uuid.uuid4(), "America/Bogota", 5),
    ]

    mock_result = MagicMock()
    mock_scalars = MagicMock()
    mock_scalars.all.return_value = tenants_mixed
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    # 08:00 UTC = 3:00 AM Bogota
    fixed_utc = datetime(2026, 3, 15, 8, 0, 0, tzinfo=timezone.utc)

    with patch("src.modules.analytics.workers.scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_utc
        mock_datetime.side_effect = datetime

        await run_tick_scheduler(ctx)

    # Only the Bogota tenant should be enqueued (invalid tz skipped)
    assert mock_redis.enqueue_job.await_count == 1
