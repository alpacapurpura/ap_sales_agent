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

import structlog
from sqlalchemy import text

from src.core.database import SessionLocal
from src.modules.copilot.application.extraction.active_job_state import (
    ActiveExtractionJob,
    load_active_job,
    merge_active_job,
)

logger = structlog.get_logger()


def read_active_job(conversation_id: str | None) -> ActiveExtractionJob | None:
    """Return the active extraction job stored for ``conversation_id`` (if any)."""
    if not conversation_id:
        return None
    db = SessionLocal()
    try:
        row = db.execute(
            text(
                "SELECT procedure_state FROM copilot_conversations WHERE id = :id",
            ),
            {"id": conversation_id},
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
) -> None:
    """Persist (or clear) the active extraction job on ``conversation_id``.

    Reads the current ``procedure_state`` first so sibling keys (e.g. the
    ``guided`` state) are preserved. No-op when ``conversation_id`` is empty.
    Passing ``job=None`` clears the key — used on job completion to resume
    guided prompts from the paused block.
    """
    if not conversation_id:
        return
    db = SessionLocal()
    try:
        current = db.execute(
            text(
                "SELECT procedure_state FROM copilot_conversations WHERE id = :id",
            ),
            {"id": conversation_id},
        ).scalar()
        current_dict = current if isinstance(current, dict) else {}
        updated = merge_active_job(current_dict, job)
        db.execute(
            text(
                "UPDATE copilot_conversations SET procedure_state = CAST(:state AS JSONB) WHERE id = :id",
            ),
            {"state": _json_dumps(updated), "id": conversation_id},
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
