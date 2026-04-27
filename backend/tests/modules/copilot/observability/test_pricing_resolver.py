"""Tests for the pricing resolver.

The resolver caches active snapshots in-memory (LRU) for hot-path
lookups, falls back to point-in-time queries on cache miss, and
returns an estimated zero-cost snapshot when no row exists at all
(best-effort: cost stays observable, never blocks a call).
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock

import pytest


@pytest.fixture
def fake_repo() -> MagicMock:
    """Mocked PricingSnapshotRepository so tests don't hit DB."""
    return MagicMock()


def _snapshot(
    *,
    valid_from: dt.datetime | None = None,
    valid_to: dt.datetime | None = None,
) -> MagicMock:
    snap = MagicMock()
    snap.provider = "openai"
    snap.model = "gpt-4o"
    snap.input_cost_per_token = Decimal("0.0000025")
    snap.output_cost_per_token = Decimal("0.000010")
    snap.cache_read_cost_per_token = Decimal("0.00000125")
    snap.cache_write_cost_per_token = Decimal(0)
    # ``valid_from`` must be a real datetime so the resolver's
    # window-matching comparison doesn't crash against a MagicMock.
    snap.valid_from = valid_from or dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.UTC)
    snap.valid_to = valid_to
    snap.id = "snap-id"
    return snap


class TestPricingResolverCacheHit:
    def test_active_snapshot_returned(self, fake_repo) -> None:
        from src.modules.copilot.observability.pricing.resolver import PricingResolver

        snap = _snapshot()
        fake_repo.find_active.return_value = snap

        resolver = PricingResolver(repo_factory=lambda: fake_repo)
        result = resolver.resolve(
            provider="openai",
            model="gpt-4o",
            at_ts=dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC),
        )
        assert result.snapshot is snap
        assert result.is_estimated is False

    def test_cache_skips_repo_on_second_call(self, fake_repo) -> None:
        from src.modules.copilot.observability.pricing.resolver import PricingResolver

        snap = _snapshot()
        fake_repo.find_active.return_value = snap

        resolver = PricingResolver(repo_factory=lambda: fake_repo)
        resolver.resolve(
            provider="openai",
            model="gpt-4o",
            at_ts=dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC),
        )
        resolver.resolve(
            provider="openai",
            model="gpt-4o",
            at_ts=dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC),
        )
        # Active lookup should fire once thanks to the LRU cache.
        assert fake_repo.find_active.call_count == 1


class TestPricingResolverPointInTime:
    def test_old_call_uses_find_at_when_active_doesnt_match(self, fake_repo) -> None:
        from src.modules.copilot.observability.pricing.resolver import PricingResolver

        # Active row exists but the call we resolve is older than valid_from.
        active_snap = _snapshot()
        active_snap.valid_from = dt.datetime(2026, 4, 1, 0, 0, tzinfo=dt.UTC)
        fake_repo.find_active.return_value = active_snap

        old_snap = _snapshot(valid_to=dt.datetime(2026, 4, 1, 0, 0, tzinfo=dt.UTC))
        old_snap.valid_from = dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.UTC)
        fake_repo.find_at.return_value = old_snap

        resolver = PricingResolver(repo_factory=lambda: fake_repo)
        result = resolver.resolve(
            provider="openai",
            model="gpt-4o",
            at_ts=dt.datetime(2026, 2, 15, 0, 0, tzinfo=dt.UTC),
        )
        assert result.snapshot is old_snap
        assert result.is_estimated is False
        fake_repo.find_at.assert_called_once()


class TestPricingResolverFallback:
    def test_unknown_model_returns_zero_estimated(self, fake_repo) -> None:
        from src.modules.copilot.observability.pricing.resolver import PricingResolver

        fake_repo.find_active.return_value = None
        fake_repo.find_at.return_value = None

        resolver = PricingResolver(repo_factory=lambda: fake_repo)
        result = resolver.resolve(
            provider="openai",
            model="gpt-99-future",
            at_ts=dt.datetime(2026, 4, 26, 12, 0, tzinfo=dt.UTC),
        )
        # Resolver MUST never block a call: fallback is a zero-cost
        # estimated snapshot with a sentinel pricing_version_id and
        # ``is_estimated=True`` so reports can flag it.
        assert result.is_estimated is True
        assert result.snapshot.input_cost_per_token == Decimal(0)
        assert result.snapshot.output_cost_per_token == Decimal(0)
