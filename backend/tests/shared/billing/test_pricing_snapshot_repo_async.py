"""Tests for PricingSnapshotRepoAsync and pricing_cache.

Tests use SQLite in-memory via async engine (aiosqlite) — mirroring the
pattern used in copilot observability tests.

PR-6 / PI-1 S2 Sub-A.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from luana_core_billing.application.pricing_cache import (
    invalidate_pricing_cache,
    resolve_pricing_cached,
)


# ---------------------------------------------------------------------------
# PricingSnapshotRepoAsync — unit tests with AsyncMock
# ---------------------------------------------------------------------------


class TestPricingSnapshotRepoAsync:
    """Unit tests: repo logic using mocked AsyncSession."""

    @pytest.mark.asyncio
    async def test_find_active_returns_snapshot(self) -> None:
        """find_active returns the scalar result from DB."""
        from luana_core_billing.infrastructure.pricing_snapshot_repo_async import (
            PricingSnapshotRepoAsync,
        )

        # Build a mock snapshot
        snapshot = MagicMock()
        snapshot.provider = "openai"
        snapshot.model = "gpt-4o-mini"
        snapshot.valid_to = None

        # Mock async session
        session = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = snapshot
        session.execute = AsyncMock(return_value=result_mock)

        repo = PricingSnapshotRepoAsync(db=session)
        found = await repo.find_active(provider="openai", model="gpt-4o-mini")

        assert found is snapshot
        session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_active_returns_none_when_no_row(self) -> None:
        """find_active returns None when no active snapshot found."""
        from luana_core_billing.infrastructure.pricing_snapshot_repo_async import (
            PricingSnapshotRepoAsync,
        )

        session = MagicMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        session.execute = AsyncMock(return_value=result_mock)

        repo = PricingSnapshotRepoAsync(db=session)
        found = await repo.find_active(provider="deepseek", model="deepseek-v4-flash")

        assert found is None

    @pytest.mark.asyncio
    async def test_find_active_cross_tenant_no_tenant_filter(self) -> None:
        """Query must NOT include a tenant_id filter (cross-tenant reference data)."""
        from luana_core_billing.infrastructure.pricing_snapshot_repo_async import (
            PricingSnapshotRepoAsync,
        )
        from sqlalchemy import select

        calls = []

        session = MagicMock()

        async def capture_execute(stmt, *a, **kw):
            calls.append(str(stmt.compile(compile_kwargs={"literal_binds": False})))
            result = MagicMock()
            result.scalar_one_or_none.return_value = None
            return result

        session.execute = capture_execute

        repo = PricingSnapshotRepoAsync(db=session)
        await repo.find_active(provider="openai", model="gpt-4o-mini")

        # Should have exactly 1 SQL call
        assert len(calls) == 1
        # No tenant_id column should appear in the query
        assert "tenant_id" not in calls[0].lower()


# ---------------------------------------------------------------------------
# pricing_cache
# ---------------------------------------------------------------------------


class TestPricingCache:
    """Unit tests for in-process LRU+TTL pricing cache."""

    def setup_method(self) -> None:
        """Clear cache before each test."""
        invalidate_pricing_cache()

    @pytest.mark.asyncio
    async def test_cache_miss_fetches_from_repo(self) -> None:
        """Cache miss → calls repo.find_active once."""
        snapshot = MagicMock()
        snapshot.provider = "openai"
        snapshot.model = "gpt-4o-mini"

        repo = MagicMock()
        repo.find_active = AsyncMock(return_value=snapshot)

        result = await resolve_pricing_cached(repo, "openai", "gpt-4o-mini")

        assert result is snapshot
        repo.find_active.assert_called_once_with(provider="openai", model="gpt-4o-mini")

    @pytest.mark.asyncio
    async def test_cache_hit_skips_repo(self) -> None:
        """Cache hit → repo.find_active NOT called on second fetch."""
        snapshot = MagicMock()

        repo = MagicMock()
        repo.find_active = AsyncMock(return_value=snapshot)

        # First fetch populates cache
        r1 = await resolve_pricing_cached(repo, "openai", "gpt-4o-mini")
        # Second fetch → cache hit
        r2 = await resolve_pricing_cached(repo, "openai", "gpt-4o-mini")

        assert r1 is snapshot
        assert r2 is snapshot
        assert repo.find_active.call_count == 1  # Only called once

    @pytest.mark.asyncio
    async def test_different_model_not_confused(self) -> None:
        """Different (provider, model) keys have separate cache entries."""
        snap1 = MagicMock()
        snap2 = MagicMock()

        repo = MagicMock()
        repo.find_active = AsyncMock(side_effect=[snap1, snap2])

        r1 = await resolve_pricing_cached(repo, "openai", "gpt-4o-mini")
        r2 = await resolve_pricing_cached(repo, "deepseek", "deepseek-v4-flash")

        assert r1 is snap1
        assert r2 is snap2

    @pytest.mark.asyncio
    async def test_invalidate_clears_cache(self) -> None:
        """invalidate_pricing_cache forces re-fetch."""
        snapshot = MagicMock()

        repo = MagicMock()
        repo.find_active = AsyncMock(return_value=snapshot)

        await resolve_pricing_cached(repo, "openai", "gpt-4o-mini")
        invalidate_pricing_cache()
        await resolve_pricing_cached(repo, "openai", "gpt-4o-mini")

        assert repo.find_active.call_count == 2  # Re-fetched after invalidation

    @pytest.mark.asyncio
    async def test_none_result_is_cached(self) -> None:
        """None (no active snapshot) is also cached — avoids repeated misses."""
        repo = MagicMock()
        repo.find_active = AsyncMock(return_value=None)

        r1 = await resolve_pricing_cached(repo, "unknown", "unknown-model")
        r2 = await resolve_pricing_cached(repo, "unknown", "unknown-model")

        assert r1 is None
        assert r2 is None
        assert repo.find_active.call_count == 1
