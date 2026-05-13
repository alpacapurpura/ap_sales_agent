"""ARQ task — daily cross-agent cost-alert scan.

Wraps :func:`check_cost_alerts` with session lifecycle + best-effort
error handling. Cron 12:00 UTC (daytime in LATAM working hours so the
alert lands in front of someone who can act on it).
"""

from __future__ import annotations

from typing import Any

import structlog
from luana_core_observability.application.cost_alert_service import (
    check_cost_alerts,
)
from luana_core_platform.core.database import SessionLocal

logger = structlog.get_logger()


async def run_cost_alerts(_ctx: dict[str, Any]) -> dict[str, Any]:
    """Daily cost-alert scan."""
    session = SessionLocal()
    try:
        result = check_cost_alerts(session)
        session.commit()
    except Exception as exc:
        logger.exception("cost_alert_task_failed", error=str(exc))
        session.rollback()
        session.close()
        return {"ok": False, "error": str(exc)}

    session.close()
    return {"ok": True, **result}
