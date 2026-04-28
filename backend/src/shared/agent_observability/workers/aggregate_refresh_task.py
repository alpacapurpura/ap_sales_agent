"""ARQ task — hourly REFRESH of the daily-cost MVs.

Refreshes both:

* ``mv_daily_llm_cost_per_tenant``    (legacy, copilot-only, rolled up
  per ``model_responded`` / ``provider`` / ``role``).
* ``mv_daily_llm_cost_per_tenant_v2`` (cross-agent, rolled up to the
  ``(agent_kind, tenant_id, occurred_on)`` grain — backs the
  ``costo-agentes`` admin page).

Each MV refreshes independently in its own try/except so a failure on
one doesn't block the other. Best-effort: structlog ``warning`` per
table that fails; the dashboard simply reads slightly stale data until
the next successful refresh.

``REFRESH MATERIALIZED VIEW CONCURRENTLY`` requires a unique index on
the MV. Both MVs declare one. CONCURRENT keeps the dashboard read path
unblocked during refresh.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import text

from src.core.database import SessionLocal

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()

_MV_LEGACY: str = "mv_daily_llm_cost_per_tenant"
_MV_V2: str = "mv_daily_llm_cost_per_tenant_v2"


def _refresh_one(session: Session, mv_name: str) -> tuple[bool, int]:
    """Refresh one MV. Returns (ok, duration_ms)."""
    started = time.monotonic()
    try:
        session.execute(text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {mv_name}"))
        session.commit()
    except Exception as exc:  # noqa: BLE001 — best-effort observability worker
        logger.warning("aggregate_refresh_table_failed", mv=mv_name, error=str(exc))
        session.rollback()
        return False, int((time.monotonic() - started) * 1000)
    return True, int((time.monotonic() - started) * 1000)


async def refresh_daily_cost_mv(_ctx: dict[str, Any]) -> dict[str, Any]:
    """Refresh both daily-cost MVs concurrently."""
    session = SessionLocal()
    legacy_ok, legacy_ms = _refresh_one(session, _MV_LEGACY)
    v2_ok, v2_ms = _refresh_one(session, _MV_V2)
    session.close()

    logger.info(
        "aggregate_refresh_complete",
        legacy_ok=legacy_ok,
        legacy_ms=legacy_ms,
        v2_ok=v2_ok,
        v2_ms=v2_ms,
    )
    return {
        "ok": legacy_ok and v2_ok,
        "legacy_ok": legacy_ok,
        "legacy_ms": legacy_ms,
        "v2_ok": v2_ok,
        "v2_ms": v2_ms,
    }
