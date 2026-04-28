"""ARQ task — daily LiteLLM pricing sync.

Registered in ``backend/src/workers/settings.py`` (cron 03:00 UTC). The
task opens its own session, runs :func:`sync_pricing`, commits and logs.
Best-effort: the copilot does not depend on this task running for any
single turn — pricing is denormalised at write time, so even if pricing
is stale for a day, in-flight calls just record the previous snapshot's
unit cost.
"""

from __future__ import annotations

from typing import Any

import httpx
import structlog

from src.core.database import SessionLocal
from src.shared.agent_observability.pricing.litellm_sync import sync_pricing

logger = structlog.get_logger()


async def sync_litellm_pricing(_ctx: dict[str, Any]) -> dict[str, Any]:
    """ARQ task: pull LiteLLM JSON, reconcile against snapshots."""
    session = SessionLocal()
    try:
        with httpx.Client(timeout=30.0) as client:
            result = sync_pricing(session, http_client=client)
        session.commit()
    except Exception as exc:
        logger.exception("pricing_sync_task_failed", error=str(exc))
        session.rollback()
        return {"ok": False, "error": str(exc)}
    finally:
        session.close()

    return {
        "ok": True,
        "rows_added": result.rows_added,
        "rows_updated": result.rows_updated,
        "rows_skipped": result.rows_skipped,
    }
