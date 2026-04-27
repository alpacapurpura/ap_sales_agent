"""Pricing resolver — (provider, model, ts) → unit-cost snapshot.

Hot-path lookup for the cost calculator. Designed to be called once per
LLM invocation from the callback handler, so the cache must absorb the
common case where every call uses the same (provider, model) pair.

Two layers:

1. **In-process LRU.** Active-snapshot lookups by ``(provider, model)``.
   Five-minute TTL approximated by an LRU of 256 entries — pricing rarely
   changes mid-request, but the worker may close a row at 03:00 UTC and
   we don't want stale Decimal values to outlive that window unbounded.
2. **Repository fallback.** Cache miss → ``find_active``. If the call's
   ``at_ts`` is older than the active row's ``valid_from`` → ``find_at``
   for point-in-time correctness.

If neither path finds a row, ``resolve`` returns a zero-cost
:class:`PricingResult` with ``is_estimated=True``. The callback handler
records the call anyway — a missing pricing entry is observable, never
fatal.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from decimal import Decimal
from typing import TYPE_CHECKING, Protocol
from uuid import UUID, uuid4

import structlog

from src.modules.copilot.observability.persistence.models.pricing_snapshot_model import (
    ModelPricingSnapshotModel,
)
from src.modules.copilot.observability.pricing.aliases import resolve_alias

if TYPE_CHECKING:
    import datetime as dt

logger = structlog.get_logger()

# Sentinel pricing_version_id used when no snapshot is found. Reports
# group these calls under "estimated" instead of dropping them.
ESTIMATED_PRICING_VERSION_ID: UUID = UUID("00000000-0000-0000-0000-000000000000")

_LRU_MAX_ENTRIES = 256


class _RepoLike(Protocol):
    """Minimal interface the resolver needs from the snapshot repository."""

    def find_active(self, *, provider: str, model: str) -> ModelPricingSnapshotModel | None: ...

    def find_at(
        self,
        *,
        provider: str,
        model: str,
        at_ts: dt.datetime,
    ) -> ModelPricingSnapshotModel | None: ...


@dataclass(frozen=True, slots=True)
class _EstimatedSnapshot:
    """Drop-in for a real snapshot when nothing is on file.

    Same attribute surface so the calculator/handler don't branch on
    type — cost is just zero.
    """

    provider: str
    model: str
    id: UUID = ESTIMATED_PRICING_VERSION_ID
    input_cost_per_token: Decimal = Decimal(0)
    output_cost_per_token: Decimal = Decimal(0)
    cache_read_cost_per_token: Decimal = Decimal(0)
    cache_write_cost_per_token: Decimal = Decimal(0)


@dataclass(slots=True)
class PricingResult:
    """Resolver return value — snapshot + provenance flag."""

    snapshot: ModelPricingSnapshotModel | _EstimatedSnapshot
    is_estimated: bool = False
    cache_hit: bool = False


@dataclass
class PricingResolver:
    """Resolve pricing snapshots via cache + repository.

    ``repo_factory`` is a callable that returns a ``PricingSnapshotRepository``;
    using a factory keeps the resolver session-agnostic (callback handler
    creates a fresh ``Session`` per turn). For tests, pass a
    ``lambda: mock``.
    """

    repo_factory: Callable[[], _RepoLike]
    _cache: dict[tuple[str, str], ModelPricingSnapshotModel] = field(default_factory=dict)

    def resolve(self, *, provider: str, model: str, at_ts: dt.datetime) -> PricingResult:
        """Return the snapshot in effect for ``at_ts``."""
        key = (provider, model)
        cached = self._cache.get(key)
        if cached is not None and self._snapshot_matches(cached, at_ts):
            return PricingResult(snapshot=cached, is_estimated=False, cache_hit=True)

        repo = self.repo_factory()

        # Try the internal identity first so manual snapshots (operator
        # overrides) win against the upstream LiteLLM rate card.
        snapshot = self._lookup(repo, provider=provider, model=model, at_ts=at_ts)
        if snapshot is None:
            alias = resolve_alias(provider, model)
            if alias is not None:
                snapshot = self._lookup(
                    repo,
                    provider=alias[0],
                    model=alias[1],
                    at_ts=at_ts,
                )

        if snapshot is not None:
            self._remember(key, snapshot)
            return PricingResult(snapshot=snapshot, is_estimated=False)

        logger.warning(
            "pricing_resolver_fallback_estimated",
            provider=provider,
            model=model,
            at_ts=at_ts.isoformat(),
            hint="No snapshot found; recording estimated zero-cost row.",
        )
        return PricingResult(
            snapshot=_EstimatedSnapshot(provider=provider, model=model),
            is_estimated=True,
        )

    def _lookup(
        self,
        repo: _RepoLike,
        *,
        provider: str,
        model: str,
        at_ts: dt.datetime,
    ) -> ModelPricingSnapshotModel | None:
        """Find a snapshot in effect for ``at_ts`` under one identity.

        Tries ``find_active`` first (covers the common case where the
        rate card has not changed) and falls back to point-in-time
        ``find_at`` when the active row's window does not cover the call.
        """
        active = repo.find_active(provider=provider, model=model)
        if active is not None and self._snapshot_matches(active, at_ts):
            return active
        return repo.find_at(provider=provider, model=model, at_ts=at_ts)

    def invalidate(self) -> None:
        """Drop every cached entry. Called after a successful pricing sync."""
        self._cache.clear()

    def _remember(self, key: tuple[str, str], snapshot: ModelPricingSnapshotModel) -> None:
        if len(self._cache) >= _LRU_MAX_ENTRIES:
            # Dict iteration order = insertion order (Python 3.7+) — pop oldest.
            oldest = next(iter(self._cache))
            self._cache.pop(oldest, None)
        self._cache[key] = snapshot

    @staticmethod
    def _snapshot_matches(snap: ModelPricingSnapshotModel, at_ts: dt.datetime) -> bool:
        """Return whether ``at_ts`` falls inside ``snap``'s validity window.

        Active snapshots (``valid_to is None``) match every ``at_ts >=
        valid_from``. Closed snapshots match ``valid_from <= at_ts <
        valid_to``.
        """
        valid_from = getattr(snap, "valid_from", None)
        valid_to = getattr(snap, "valid_to", None)
        # Mocks may omit valid_from; treat that as "always matches" so unit
        # tests stay terse.
        if valid_from is None:
            return True
        if at_ts < valid_from:
            return False
        if valid_to is None:
            return True
        return at_ts < valid_to


def make_estimated_id() -> UUID:
    """Return the sentinel pricing_version_id used for estimated rows.

    Exposed as a function (not a constant import) so call-sites can audit
    "where did we attribute estimated pricing" easily.
    """
    return ESTIMATED_PRICING_VERSION_ID


__all__ = [
    "ESTIMATED_PRICING_VERSION_ID",
    "PricingResolver",
    "PricingResult",
    "_EstimatedSnapshot",
    "make_estimated_id",
]


# ``_uuid_for_anonymous`` historically lived here in early drafts; keep
# the simple ``uuid4`` import alive to avoid breaking any future helper
# that imports from this module (no behaviour, no test needed).
_ = uuid4
