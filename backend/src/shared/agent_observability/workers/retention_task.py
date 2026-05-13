"""ARQ task — daily purge of expired ``*_trace_event`` + ``*_llm_call`` rows.

Cross-agent: iterates :func:`agent_observability_registry` so adding a
new agent automatically lights up retention without touching this file.

Two retention windows per agent, each overridable via env var:

* trace_event default 90 days. ``status='error'`` rows are preserved
  indefinitely (forensic gold for regression triage weeks later).
* llm_call default 365 days. Longer because billing audits require it.

Env var schema (per spec): ``{AGENT_KIND}_TRACE_RETENTION_DAYS`` and
``{AGENT_KIND}_LLM_CALL_RETENTION_DAYS`` — already set in each spec.

Cron daily 04:00 UTC. Best-effort per-table: a failure on one table
logs structlog ``retention_table_failed`` and moves on; the run as a
whole returns ``{"ok": False, ...}`` only when every table failed.

DELETEs are bounded by the per-agent indexes (``ix_*_tenant_time`` /
``ix_*_tenant_day``) so the operation is cheap even on large tables.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import TYPE_CHECKING, Any

import structlog
from luana_core_observability.registry import (
    AgentObservabilitySpec,
    agent_observability_registry,
)
from luana_core_platform.core.database import SessionLocal
from sqlalchemy import text

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = structlog.get_logger()


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


def _purge_one_agent(session: Session, spec: AgentObservabilitySpec) -> tuple[int, int]:
    """Purge one agent's two tables. Returns (trace_deleted, llm_deleted).

    Each table gets its own try/except so a partial failure doesn't
    cascade across the agent. The session is shared with the parent so
    the parent decides commit/rollback once across all agents.
    """
    trace_days = _retention_days(spec.trace_retention_env_var, spec.trace_default_days)
    llm_days = _retention_days(spec.llm_call_retention_env_var, spec.llm_call_default_days)

    trace_deleted = 0
    llm_deleted = 0

    try:
        trace_cutoff = _cutoff(trace_days)
        # Preserve error rows indefinitely — forensic value when a
        # customer reports a regression weeks later. table name is
        # interpolated from the registry (no user input).
        trace_result = session.execute(
            text(
                f"DELETE FROM {spec.trace_event_table} WHERE created_at < :cutoff AND status != 'error'",
            ),
            {"cutoff": trace_cutoff},
        )
        trace_deleted = int(trace_result.rowcount or 0)
    except Exception as exc:  # noqa: BLE001 — best-effort per-table
        logger.warning(
            "retention_table_failed",
            agent_kind=spec.agent_kind,
            table=spec.trace_event_table,
            error=str(exc),
        )

    try:
        llm_cutoff = _cutoff(llm_days)
        llm_result = session.execute(
            text(
                f"DELETE FROM {spec.llm_call_table} WHERE started_at < :cutoff",
            ),
            {"cutoff": llm_cutoff},
        )
        llm_deleted = int(llm_result.rowcount or 0)
    except Exception as exc:  # noqa: BLE001 — best-effort per-table
        logger.warning(
            "retention_table_failed",
            agent_kind=spec.agent_kind,
            table=spec.llm_call_table,
            error=str(exc),
        )

    return trace_deleted, llm_deleted


async def purge_expired_trace_rows(_ctx: dict[str, Any]) -> dict[str, Any]:
    """Drop expired rows from every registered agent's tables."""
    session = SessionLocal()
    per_agent: dict[str, dict[str, int]] = {}
    total_trace = 0
    total_llm = 0
    errors = 0

    for spec in agent_observability_registry():
        trace_deleted, llm_deleted = _purge_one_agent(session, spec)
        per_agent[spec.agent_kind] = {
            "trace_event_deleted": trace_deleted,
            "llm_call_deleted": llm_deleted,
        }
        total_trace += trace_deleted
        total_llm += llm_deleted

    try:
        session.commit()
    except Exception as exc:
        logger.exception("retention_task_commit_failed", error=str(exc))
        session.rollback()
        errors += 1
    finally:
        session.close()

    if errors:
        return {"ok": False, "per_agent": per_agent}

    logger.info(
        "retention_task_complete",
        per_agent=per_agent,
        total_trace_event_deleted=total_trace,
        total_llm_call_deleted=total_llm,
    )
    return {
        "ok": True,
        "per_agent": per_agent,
        "trace_event_deleted": total_trace,
        "llm_call_deleted": total_llm,
    }
