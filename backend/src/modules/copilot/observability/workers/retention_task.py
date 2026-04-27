"""ARQ task — daily purge of expired trace + LLM-call rows.

Phase 3, T3.9. Two retention windows configurable via env vars:

* ``COPILOT_TRACE_RETENTION_DAYS`` (default 90) — drop ``copilot_trace_event``
  rows older than the cutoff, **preserving rows with ``status='error'``**
  for indefinite forensic access.
* ``COPILOT_LLM_CALL_RETENTION_DAYS`` (default 365) — drop ``copilot_llm_call``
  rows older than the cutoff. Longer retention because billing
  audits require it.

Cron daily 04:00 UTC. Best-effort: failure logs structlog
``retention_task_failed`` and returns ``{"ok": False}``; the rows simply
linger one more day until the next run succeeds.

Both DELETEs are bounded by the index ``ix_copilot_trace_event_tenant_time``
(or ``ix_llm_call_tenant_day`` for the call table) so the operation is
cheap even on large tables.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import Any

import structlog
from sqlalchemy import text

from src.core.database import SessionLocal

logger = structlog.get_logger()

_DEFAULT_TRACE_DAYS: int = 90
_DEFAULT_LLM_CALL_DAYS: int = 365


def _retention_days(env_var: str, default: int) -> int:
    raw = os.environ.get(env_var)
    if raw is None:
        return default
    try:
        days = int(raw)
    except ValueError:
        logger.warning(
            "retention_invalid_env_var",
            env_var=env_var,
            value=raw,
            using_default=default,
        )
        return default
    return max(1, days)


def _cutoff(days: int) -> dt.datetime:
    return dt.datetime.now(tz=dt.UTC) - dt.timedelta(days=days)


async def purge_expired_trace_rows(_ctx: dict[str, Any]) -> dict[str, Any]:
    """Drop expired rows from copilot_trace_event + copilot_llm_call."""
    trace_days = _retention_days("COPILOT_TRACE_RETENTION_DAYS", _DEFAULT_TRACE_DAYS)
    llm_call_days = _retention_days(
        "COPILOT_LLM_CALL_RETENTION_DAYS",
        _DEFAULT_LLM_CALL_DAYS,
    )

    session = SessionLocal()
    try:
        trace_cutoff = _cutoff(trace_days)
        trace_result = session.execute(
            text(
                # Preserve error rows indefinitely — they're forensic gold
                # when a customer reports a regression weeks later.
                "DELETE FROM copilot_trace_event WHERE created_at < :cutoff AND status != 'error'",
            ),
            {"cutoff": trace_cutoff},
        )
        trace_deleted = int(trace_result.rowcount or 0)

        llm_cutoff = _cutoff(llm_call_days)
        llm_result = session.execute(
            text("DELETE FROM copilot_llm_call WHERE started_at < :cutoff"),
            {"cutoff": llm_cutoff},
        )
        llm_deleted = int(llm_result.rowcount or 0)

        session.commit()
    except Exception as exc:
        logger.exception("retention_task_failed", error=str(exc))
        session.rollback()
        session.close()
        return {"ok": False, "error": str(exc)}

    session.close()
    logger.info(
        "retention_task_complete",
        trace_event_deleted=trace_deleted,
        llm_call_deleted=llm_deleted,
        trace_retention_days=trace_days,
        llm_call_retention_days=llm_call_days,
    )
    return {
        "ok": True,
        "trace_event_deleted": trace_deleted,
        "llm_call_deleted": llm_deleted,
    }
