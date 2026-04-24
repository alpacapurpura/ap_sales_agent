"""Active extraction job persistence helpers.

Writes ``ActiveExtractionJob`` into ``copilot_conversations.procedure_state``
JSONB under the ``active_extraction_job`` key. Mirrors
``guided.persistence`` so both flows share a single SSoT column.

Uses a short-lived ``SessionLocal`` session so tool functions don't need to
receive a ``Session`` through LangChain args.

All writes are best-effort: a failure logs a structured warning and returns
without raising — a failed state write must not revert a successful
extraction dispatch.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import text

from src.core.database import SessionLocal
from src.modules.copilot.application.extraction.active_job_state import (
    ActiveExtractionJob,
    load_active_job,
    merge_active_job,
)

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


def read_active_job(
    conversation_id: str | None,
    tenant_id: UUID | None,
) -> ActiveExtractionJob | None:
    """Return the active extraction job stored for ``conversation_id`` (if any).

    Tenant-scoped by rule ``tenant-isolation.md`` — both a mismatched
    tenant and a missing ``tenant_id`` short-circuit to ``None`` rather
    than risking a cross-tenant read.
    """
    if not conversation_id or tenant_id is None:
        return None
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT procedure_state FROM copilot_conversations WHERE id = :id AND tenant_id = :tenant_id",
            ),
            {"id": conversation_id, "tenant_id": str(tenant_id)},
        ).scalar()
        return load_active_job(row if isinstance(row, dict) else None)
    except Exception as exc:  # noqa: BLE001 — orchestrator resilience
        logger.warning(
            "active_job_state_read_failed",
            conv_id=conversation_id,
            error=str(exc),
        )
        return None
    finally:
        db.close()


def write_active_job(
    conversation_id: str | None,
    job: ActiveExtractionJob | None,
    tenant_id: UUID | None,
) -> None:
    """Persist (or clear) the active extraction job on ``conversation_id``.

    Reads the current ``procedure_state`` first so sibling keys (e.g. the
    ``guided`` state) are preserved. No-op when ``conversation_id`` or
    ``tenant_id`` is empty. Passing ``job=None`` clears the key — used on
    job completion to resume guided prompts from the paused block.
    """
    if not conversation_id or tenant_id is None:
        return
    db = SessionLocal()
    try:
        current = db.execute(
            text(
                "SELECT procedure_state FROM copilot_conversations WHERE id = :id AND tenant_id = :tenant_id",
            ),
            {"id": conversation_id, "tenant_id": str(tenant_id)},
        ).scalar()
        current_dict = current if isinstance(current, dict) else {}
        updated = merge_active_job(current_dict, job)
        db.execute(
            text(
                "UPDATE copilot_conversations "
                "SET procedure_state = CAST(:state AS JSONB) "
                "WHERE id = :id AND tenant_id = :tenant_id",
            ),
            {
                "state": _json_dumps(updated),
                "id": conversation_id,
                "tenant_id": str(tenant_id),
            },
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 — orchestrator resilience
        db.rollback()
        logger.warning(
            "active_job_state_write_failed",
            conv_id=conversation_id,
            error=str(exc),
        )
    finally:
        db.close()


def _json_dumps(value: dict) -> str:
    """Local import of json to keep this module's imports minimal at module scope."""
    import json

    return json.dumps(value, default=str)


__all__ = ["read_active_job", "write_active_job"]
