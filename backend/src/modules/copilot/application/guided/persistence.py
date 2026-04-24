"""Guided setup persistence helpers.

Writes ``GuidedState`` into ``copilot_conversations.procedure_state`` JSONB.
Uses a short-lived ``SessionLocal`` session so tool functions don't need to
receive a ``Session`` through LangChain args. Mirrors the pattern used by
``_get_completion_snapshot`` in ``orchestrator/graph.py``.

All writes are best-effort: a failure logs a structured warning and returns
without raising — the guided flow continues even if persistence glitches, and
the next successful write re-sets the canonical state.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import text

from src.core.database import SessionLocal
from src.modules.copilot.application.guided.state import (
    GuidedState,
    load_guided_state,
    merge_guided_state,
)

if TYPE_CHECKING:
    from uuid import UUID

logger = structlog.get_logger()


def read_state(
    conversation_id: str | None,
    tenant_id: UUID | None,
) -> GuidedState | None:
    """Return the guided state stored for ``conversation_id`` (if any).

    Tenant-scoped by rule ``tenant-isolation.md`` — a missing or
    mismatched ``tenant_id`` short-circuits to ``None``.
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
        return load_guided_state(row if isinstance(row, dict) else None)
    except Exception as exc:  # noqa: BLE001 — orchestrator resilience
        logger.warning("guided_state_read_failed", conv_id=conversation_id, error=str(exc))
        return None
    finally:
        db.close()


def write_state(
    conversation_id: str | None,
    state: GuidedState | None,
    tenant_id: UUID | None,
) -> None:
    """Persist (or clear) the guided state on ``conversation_id``.

    Reads the current ``procedure_state`` first so sibling keys (e.g. the
    ``active_extraction_job`` sibling) are preserved. No-op when either
    ``conversation_id`` or ``tenant_id`` is empty.
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
        updated = merge_guided_state(current_dict, state)
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
        logger.warning("guided_state_write_failed", conv_id=conversation_id, error=str(exc))
    finally:
        db.close()


def _json_dumps(value: dict) -> str:
    """Local import of json to keep this module's imports minimal at module scope."""
    import json

    return json.dumps(value, default=str)


__all__ = ["read_state", "write_state"]
