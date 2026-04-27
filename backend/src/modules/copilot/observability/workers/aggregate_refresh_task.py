"""ARQ task — hourly REFRESH of the daily-cost MV.

Phase 3, T3.4. Registered in ``backend/src/workers/settings.py``
(``SchedulerSettings.cron_jobs``) at minute 5 of every hour. The minute
offset avoids stacking with on-the-hour ETL workers.

Best-effort: failure logs structlog ``aggregate_refresh_failed`` and
returns ``{"ok": False}``; the dashboard simply reads slightly stale
data until the next successful refresh.

``REFRESH MATERIALIZED VIEW CONCURRENTLY`` requires the unique index
created in migration ``077_copilot_daily_llm_cost_mv``. CONCURRENT is
critical because the dashboard read path SELECTs from the MV; without
CONCURRENT a refresh would block readers for the duration of the
re-aggregate.
"""

from __future__ import annotations

import time
from typing import Any

import structlog
from sqlalchemy import text

from src.core.database import SessionLocal

logger = structlog.get_logger()

_REFRESH_SQL: str = "REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_llm_cost_per_tenant"


async def refresh_daily_cost_mv(_ctx: dict[str, Any]) -> dict[str, Any]:
    """Refresh ``mv_daily_llm_cost_per_tenant`` concurrently."""
    session = SessionLocal()
    started = time.monotonic()
    try:
        session.execute(text(_REFRESH_SQL))
        session.commit()
    except Exception as exc:
        logger.exception("aggregate_refresh_failed", error=str(exc))
        session.rollback()
        session.close()
        return {"ok": False, "error": str(exc)}

    duration_ms = int((time.monotonic() - started) * 1000)
    session.close()
    logger.info("aggregate_refresh_complete", duration_ms=duration_ms)
    return {"ok": True, "duration_ms": duration_ms}
