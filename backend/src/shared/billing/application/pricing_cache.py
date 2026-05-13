"""In-process LRU+TTL cache for ``model_pricing_snapshot`` lookups.

Wraps ``PricingSnapshotRepoAsync.find_active`` with a
``cachetools.TTLCache`` so repeated pre-call cost-estimation lookups
within the same process hit in-memory instead of Postgres.

Cache parameters:
- maxsize=256 entries (covers all known provider/model combos + future growth)
- ttl=300s (5 minutes) — pricing syncs daily via LiteLLM cron, so 5-min
  staleness is safe.  Any pricing update between syncs is acceptable
  (over-estimate by old cheaper rate = safe; under-estimate by old pricier
  rate = BudgetGuard over-conservative, which is acceptable).

Thread-safety: single ``threading.Lock`` guards both read and write to
the ``TTLCache`` (cachetools TTLCache is NOT thread-safe by default).

PR-6 / PI-1 S2.
"""

from __future__ import annotations

from threading import Lock
from typing import TYPE_CHECKING

from cachetools import TTLCache

if TYPE_CHECKING:
    from luana_core_billing.infrastructure.pricing_snapshot_repo_async import (
        PricingSnapshotRepoAsync,
    )
    from luana_core_observability.persistence.models.pricing_snapshot_model import (
        ModelPricingSnapshotModel,
    )

_cache: TTLCache[tuple[str, str], ModelPricingSnapshotModel | None] = TTLCache(
    maxsize=256,
    ttl=300,
)
_cache_lock: Lock = Lock()


async def resolve_pricing_cached(
    repo: PricingSnapshotRepoAsync,
    provider: str,
    model: str,
) -> ModelPricingSnapshotModel | None:
    """Return cached snapshot or fetch from DB on miss.

    Thread-safe read-through cache.  If the repo raises (e.g. DB down),
    the exception propagates — callers should handle gracefully.
    """
    key = (provider, model)
    with _cache_lock:
        if key in _cache:
            return _cache[key]
    snapshot = await repo.find_active(provider=provider, model=model)
    with _cache_lock:
        _cache[key] = snapshot
    return snapshot


def invalidate_pricing_cache() -> None:
    """Clear the in-process cache.

    Called by tests or after pricing sync worker runs to force a fresh
    fetch on next estimation call.
    """
    with _cache_lock:
        _cache.clear()
