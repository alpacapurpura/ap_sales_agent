"""Pricing resolver consults the alias registry before estimating.

Conv 0d64c4a9 (2026-04-27) recorded every Kimi K2.6 turn under
``provider="kimi", model="kimi-k2.6"`` while the LiteLLM-synced rate
card lives under ``provider="moonshot", model="moonshot/kimi-k2-0905-
preview"``. The resolver missed both lookups, fell back to the
estimated zero-cost snapshot, and the cycle aggregator silently
under-counted spend.

The fix lives in ``observability/pricing/aliases.py``: a SSoT mapping
from the in-process identity to the upstream LiteLLM identity. The
resolver must consult it on miss and only declare a row estimated when
neither identity finds a snapshot.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock


def _kimi_snapshot() -> MagicMock:
    snap = MagicMock()
    snap.provider = "moonshot"
    snap.model = "moonshot/kimi-k2-0905-preview"
    snap.input_cost_per_token = Decimal("0.0000006")
    snap.output_cost_per_token = Decimal("0.0000025")
    snap.cache_read_cost_per_token = Decimal(0)
    snap.cache_write_cost_per_token = Decimal(0)
    snap.valid_from = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    snap.valid_to = None
    snap.id = "snap-kimi"
    return snap


class TestAliasResolutionFallsThroughOnInternalMiss:
    def test_kimi_internal_identity_resolves_via_alias(self) -> None:
        from src.modules.copilot.observability.pricing.resolver import PricingResolver

        upstream = _kimi_snapshot()

        def find_active(*, provider: str, model: str):
            if (provider, model) == ("kimi", "kimi-k2.6"):
                return None
            if (provider, model) == ("moonshot", "moonshot/kimi-k2-0905-preview"):
                return upstream
            return None

        repo = MagicMock()
        repo.find_active.side_effect = find_active
        repo.find_at.return_value = None

        resolver = PricingResolver(repo_factory=lambda: repo)
        result = resolver.resolve(
            provider="kimi",
            model="kimi-k2.6",
            at_ts=dt.datetime(2026, 4, 27, tzinfo=dt.UTC),
        )

        assert result.is_estimated is False
        assert result.snapshot is upstream

    def test_alias_hit_is_cached_for_subsequent_calls(self) -> None:
        from src.modules.copilot.observability.pricing.resolver import PricingResolver

        upstream = _kimi_snapshot()

        repo = MagicMock()
        repo.find_active.side_effect = lambda *, provider, model: (
            upstream if (provider, model) == ("moonshot", "moonshot/kimi-k2-0905-preview") else None
        )
        repo.find_at.return_value = None

        resolver = PricingResolver(repo_factory=lambda: repo)
        first = resolver.resolve(
            provider="kimi",
            model="kimi-k2.6",
            at_ts=dt.datetime(2026, 4, 27, tzinfo=dt.UTC),
        )
        second = resolver.resolve(
            provider="kimi",
            model="kimi-k2.6",
            at_ts=dt.datetime(2026, 4, 27, 12, 0, tzinfo=dt.UTC),
        )

        assert first.snapshot is upstream
        assert second.snapshot is upstream
        assert second.cache_hit is True
        # Repository was consulted twice on the first call (internal +
        # alias), then never again — the alias hit must populate the LRU.
        assert repo.find_active.call_count == 2

    def test_unknown_internal_identity_still_estimates(self) -> None:
        from src.modules.copilot.observability.pricing.resolver import PricingResolver

        repo = MagicMock()
        repo.find_active.return_value = None
        repo.find_at.return_value = None

        resolver = PricingResolver(repo_factory=lambda: repo)
        result = resolver.resolve(
            provider="brand-new-vendor",
            model="some-model",
            at_ts=dt.datetime(2026, 4, 27, tzinfo=dt.UTC),
        )
        assert result.is_estimated is True

    def test_internal_snapshot_takes_precedence_over_alias(self) -> None:
        """Manual snapshots written under the internal identity win.

        Operators occasionally insert ``source='manual'`` rows under the
        internal identity to override LiteLLM (incident response, custom
        contracts). Those rows must beat the alias path.
        """
        from src.modules.copilot.observability.pricing.resolver import PricingResolver

        manual = MagicMock()
        manual.provider = "kimi"
        manual.model = "kimi-k2.6"
        manual.input_cost_per_token = Decimal("0.0000010")
        manual.output_cost_per_token = Decimal("0.0000040")
        manual.cache_read_cost_per_token = Decimal(0)
        manual.cache_write_cost_per_token = Decimal(0)
        manual.valid_from = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
        manual.valid_to = None
        manual.id = "snap-manual"

        repo = MagicMock()
        repo.find_active.side_effect = lambda *, provider, model: (
            manual if (provider, model) == ("kimi", "kimi-k2.6") else None
        )
        repo.find_at.return_value = None

        resolver = PricingResolver(repo_factory=lambda: repo)
        result = resolver.resolve(
            provider="kimi",
            model="kimi-k2.6",
            at_ts=dt.datetime(2026, 4, 27, tzinfo=dt.UTC),
        )

        assert result.snapshot is manual
        assert result.is_estimated is False
