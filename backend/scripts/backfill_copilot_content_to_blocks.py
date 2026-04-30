"""Backfill ``copilot_conversations.messages`` v1→v2 (content → blocks).

Migration 056 (20260422_1200_copilot_multimodal.py) introduced the v2 message
shape with ``blocks`` arrays. Legacy messages carry only ``content`` (v1). This
script scans conversations with v1 messages, converts each via the existing
``decode_message`` + ``encode_message`` codec path, and persists the enriched
``messages`` JSONB back to Postgres.

**Data shape:**
  v1: ``{role, content, tool_calls?, tool_call_id?, name?}``
  v2: ``{id, role, content, blocks, status, created_at, ...}``

The backfill synthesises a ``TextBlock`` from ``content`` — the same path
``decode_message`` already follows at read-time. No new transformation logic.

**Safety guarantees:**
  - Dry-run default: ``--apply`` required to persist.
  - Optimistic lock: UPDATE only if ``messages`` unchanged since SELECT.
  - Per-conv try/except: one corrupt conv does not abort the batch.
  - Abort if ``failure_rate > --max-failure-rate`` (default 5%).
  - ``--confirm-prod`` guard when DATABASE_URL points to prod.
  - Idempotent: re-run on a completed backfill = 0 updates.

**Audit trail:**
  Writes a row to ``copilot_backfill_runs`` (created by migration 111).
  Soft-fail on audit write — never aborts backfill for observability failure.

Usage::

    # Dry-run (default — no writes):
    cd backend && .venv/bin/python scripts/backfill_copilot_content_to_blocks.py

    # Full apply (dev DB):
    cd backend && .venv/bin/python scripts/backfill_copilot_content_to_blocks.py --apply

    # Single tenant:
    cd backend && .venv/bin/python scripts/backfill_copilot_content_to_blocks.py --apply --tenant-id <UUID>

    # Prod guard:
    cd backend && .venv/bin/python scripts/backfill_copilot_content_to_blocks.py --apply --confirm-prod

Design decisions: D1-D8 in CONTRACT.md (PR-3, PI-2, S1, 2026-04-29).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog
from sqlalchemy import text
from sqlalchemy.orm import Session  # noqa: TC002

# Repo root on sys.path so ``src.*`` imports work when invoked directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.repositories.message_codec import (
    decode_message,
    encode_message,
)
from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger(__name__)


# ── domain stats ─────────────────────────────────────────────────────────────


@dataclass(slots=True)
class BackfillStats:
    """Aggregated counters for a single backfill run.

    Emitted as structlog event on every batch + final summary. Counters are
    monotonic — re-running on top of a partial run accumulates correctly.

    convs_updated: successful DB writes (0 in dry-run by contract).
    convs_would_update: would-be updates in dry-run mode.
    """

    convs_scanned: int = 0
    convs_already_v2: int = 0
    convs_with_legacy_msgs: int = 0
    convs_updated: int = 0  # actual DB writes (0 in dry-run)
    convs_would_update: int = 0  # dry-run projection
    convs_skipped_corrupt: int = 0
    msgs_total: int = 0
    msgs_legacy_converted: int = 0
    msgs_already_v2: int = 0
    msgs_skipped_corrupt: int = 0
    tenants_touched: set[uuid.UUID] = field(default_factory=set)
    duration_ms: int = 0
    failed_conv_ids: list[uuid.UUID] = field(default_factory=list)


# ── core logic ────────────────────────────────────────────────────────────────


def _message_is_v2(msg: dict) -> bool:
    """Return True if message already has a non-empty blocks list."""
    blocks = msg.get("blocks")
    return bool(blocks)


def _message_needs_backfill(msg: dict) -> bool:
    """Return True if message is v1 shape (has content but no blocks)."""
    content = msg.get("content")
    blocks = msg.get("blocks")
    return bool(content) and not blocks


def _message_is_corrupt(msg: dict) -> bool:
    """Return True if message is unusable: missing role AND content AND blocks.

    Distinguishes from valid pass-through (role present, content empty/None,
    no blocks — common for tool messages with empty payloads).
    """
    role = msg.get("role")
    content = msg.get("content")
    blocks = msg.get("blocks")
    return not role and not content and not blocks


def _transform_message(msg: dict, *, conv_id: uuid.UUID) -> dict:
    """Apply decode_message → encode_message to produce v2 shape.

    Uses the canonical codec path — no reimplementation of TextBlock synthesis.
    Raises on corrupt message so callers can skip-and-log.
    """
    domain_msg = decode_message(msg, conversation_id=conv_id)
    return encode_message(domain_msg)


def _run_batch(
    db: Session,
    *,
    batch: list[dict],
    dry_run: bool,
    stats: BackfillStats,
) -> None:
    """Process a batch of conversation rows.

    Each conv is processed independently (D1: per-conv atomic UPDATE).
    On error: skip + log + count, continue with remaining batch (D2).
    Optimistic lock: UPDATE WHERE messages = :original (D3).
    """
    for row in batch:
        conv_id = uuid.UUID(str(row["id"]))
        tenant_id = uuid.UUID(str(row["tenant_id"]))
        raw_messages = row["messages"]

        # Parse JSONB — SQLite returns string, Postgres returns list
        if isinstance(raw_messages, str):
            try:
                messages: list[dict] = json.loads(raw_messages)
            except json.JSONDecodeError as exc:
                logger.warning(
                    "conv_backfill_json_decode_error",
                    conv_id=str(conv_id),
                    error=str(exc),
                )
                stats.convs_skipped_corrupt += 1
                stats.msgs_skipped_corrupt += 1
                stats.failed_conv_ids.append(conv_id)
                continue
        else:
            messages = raw_messages or []

        stats.convs_scanned += 1
        stats.msgs_total += len(messages)

        # Corrupt detection: any msg missing role+content+blocks is unusable.
        # Codec will fail on these, so skip the whole conv with audit.
        if any(_message_is_corrupt(m) for m in messages):
            stats.convs_skipped_corrupt += 1
            stats.msgs_skipped_corrupt += sum(1 for m in messages if _message_is_corrupt(m))
            stats.failed_conv_ids.append(conv_id)
            continue

        # Idempotency: conv done if no message needs backfill.
        # Done state = every msg is either v2 (has blocks) OR pass-through (role
        # present, content empty/None, no blocks — e.g. tool_call). Re-runs
        # short-circuit here without classifying valid pass-through as corrupt.
        needs_backfill = any(_message_needs_backfill(m) for m in messages)
        if not needs_backfill:
            stats.convs_already_v2 += 1
            stats.msgs_already_v2 += sum(1 for m in messages if _message_is_v2(m))
            continue

        stats.convs_with_legacy_msgs += 1

        # Transform each message
        try:
            new_messages: list[dict] = []
            legacy_count = 0
            for msg in messages:
                if _message_is_v2(msg):
                    new_messages.append(msg)
                    stats.msgs_already_v2 += 1
                elif _message_needs_backfill(msg):
                    transformed = _transform_message(msg, conv_id=conv_id)
                    new_messages.append(transformed)
                    legacy_count += 1
                    stats.msgs_legacy_converted += 1
                else:
                    # Message has neither content nor blocks — pass through as-is
                    new_messages.append(msg)
        except Exception as exc:  # noqa: BLE001 — skip corrupt conv
            logger.warning(
                "conv_backfill_transform_error",
                conv_id=str(conv_id),
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            stats.convs_skipped_corrupt += 1
            stats.msgs_skipped_corrupt += len(messages)
            stats.failed_conv_ids.append(conv_id)
            continue

        if dry_run:
            stats.convs_would_update += 1  # projection only — no DB write
            stats.tenants_touched.add(tenant_id)
            continue

        # Persist — optimistic lock: UPDATE only if messages unchanged (D3)
        try:
            original_json = json.dumps(raw_messages) if isinstance(raw_messages, list) else raw_messages
            new_json = json.dumps(new_messages)

            result = db.execute(
                text(
                    """
                    UPDATE copilot_conversations
                    SET messages = :new_messages
                    WHERE id = :conv_id
                      AND tenant_id = :tenant_id
                      AND deleted_at IS NULL
                      AND messages = :original_messages
                    """
                ),
                {
                    "new_messages": new_json,
                    "conv_id": str(conv_id),
                    "tenant_id": str(tenant_id),
                    "original_messages": original_json,
                },
            )
            if result.rowcount == 0:
                # Optimistic lock collision — conv was written mid-flight
                logger.info(
                    "conv_backfill_optimistic_lock_miss",
                    conv_id=str(conv_id),
                    hint="Messages changed mid-flight; will be picked up on re-run",
                )
                # Don't count as error — count as skip (idempotent re-run handles)
                stats.convs_already_v2 += 1  # approximation
            else:
                stats.convs_updated += 1
                stats.tenants_touched.add(tenant_id)
        except Exception as exc:  # noqa: BLE001 — skip corrupt conv
            db.rollback()
            logger.warning(
                "conv_backfill_update_error",
                conv_id=str(conv_id),
                tenant_id=str(tenant_id),
                error=str(exc),
            )
            stats.convs_skipped_corrupt += 1
            stats.failed_conv_ids.append(conv_id)


def _query_batch(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    batch_size: int,
    offset: int,
) -> list[dict]:
    """Fetch a batch of conversations for a given tenant that need backfill.

    Filters: deleted_at IS NULL, tenant_id = :tenant_id.
    Idempotent filter: no SQL-level filter on blocks presence (Python-side
    per-message check handles mixed convs). We fetch all non-deleted convs
    and let _run_batch skip already-v2 ones efficiently.
    """
    rows = db.execute(
        text(
            """
            SELECT id, tenant_id, messages
            FROM copilot_conversations
            WHERE tenant_id = :tenant_id
              AND deleted_at IS NULL
            ORDER BY id
            LIMIT :limit
            OFFSET :offset
            """
        ),
        {"tenant_id": str(tenant_id), "limit": batch_size, "offset": offset},
    ).fetchall()
    return [dict(r._mapping) for r in rows]


def _get_all_tenant_ids(db: Session) -> list[uuid.UUID]:
    """Return all distinct tenant_ids that have copilot conversations."""
    rows = db.execute(
        text(
            """
            SELECT DISTINCT tenant_id
            FROM copilot_conversations
            WHERE deleted_at IS NULL
            ORDER BY tenant_id
            """
        )
    ).fetchall()
    return [uuid.UUID(str(r[0])) for r in rows]


def _write_audit_row(
    db: Session,
    *,
    run_id: uuid.UUID,
    tenant_id: uuid.UUID | None,
    mode: str,
    status: str,
    stats: BackfillStats,
    error_message: str | None = None,
) -> None:
    """Write / update audit row in copilot_backfill_runs. Best-effort: never aborts backfill."""
    try:
        now = utc_now().isoformat()
        row_id = str(uuid.uuid4())
        failed_json = json.dumps([str(fid) for fid in stats.failed_conv_ids])

        db.execute(
            text(
                """
                INSERT INTO copilot_backfill_runs
                    (id, run_id, tenant_id, started_at, ended_at, mode,
                     convs_scanned, convs_updated, msgs_legacy_converted,
                     convs_skipped_corrupt, failed_conv_ids, status, error_message)
                VALUES
                    (:id, :run_id, :tenant_id, :now, :now, :mode,
                     :convs_scanned, :convs_updated, :msgs_legacy_converted,
                     :convs_skipped_corrupt, :failed_conv_ids, :status, :error_message)
                """
            ),
            {
                "id": row_id,
                "run_id": str(run_id),
                "tenant_id": str(tenant_id) if tenant_id else None,
                "now": now,
                "mode": mode,
                "convs_scanned": stats.convs_scanned,
                "convs_updated": stats.convs_updated,
                "msgs_legacy_converted": stats.msgs_legacy_converted,
                "convs_skipped_corrupt": stats.convs_skipped_corrupt,
                "failed_conv_ids": failed_json,
                "status": status,
                "error_message": error_message,
            },
        )
        db.commit()
    except Exception as exc:  # noqa: BLE001 — best-effort observability
        logger.warning(
            "backfill_audit_write_failed",
            run_id=str(run_id),
            error=str(exc),
            hint="Audit write failed but backfill continues",
        )
        import contextlib

        with contextlib.suppress(Exception):
            db.rollback()


# ── main entry ────────────────────────────────────────────────────────────────


def run(
    *,
    db: Session | None = None,
    dry_run: bool = True,
    tenant_id: uuid.UUID | None = None,
    batch_size: int = 100,
    run_id: uuid.UUID | None = None,
    max_failure_rate: float = 0.05,
    max_convs: int | None = None,
) -> BackfillStats:
    """Execute the backfill and return aggregated stats.

    Args:
        db: SQLAlchemy session. If None, creates one from SessionLocal.
        dry_run: If True, compute stats without persisting (default: True).
        tenant_id: Restrict to single tenant. If None, all tenants processed sequentially.
        batch_size: Conversations per batch (default 100). D1 decision.
        run_id: UUID for audit trail. Auto-generated if None.
        max_failure_rate: Abort if corrupt-conv rate exceeds this. Default 5%. D2 decision.
        max_convs: Stop after N convs total (smoke testing). None = no limit.

    Returns:
        BackfillStats with final counters.
    """
    if run_id is None:
        run_id = uuid.uuid4()

    mode = "dry_run" if dry_run else "apply"
    stats = BackfillStats()
    _own_session = db is None

    if _own_session:
        db = SessionLocal()

    try:
        # Determine tenant list to process
        if tenant_id is not None:
            tenant_ids = [tenant_id]
        else:
            tenant_ids = _get_all_tenant_ids(db)

        logger.info(
            "backfill_started",
            run_id=str(run_id),
            mode=mode,
            tenant_count=len(tenant_ids),
            batch_size=batch_size,
            max_failure_rate=max_failure_rate,
        )

        total_processed = 0
        batch_num = 0

        for tid in tenant_ids:
            offset = 0
            while True:
                batch_start = utc_now()
                batch = _query_batch(db, tenant_id=tid, batch_size=batch_size, offset=offset)
                if not batch:
                    break

                _run_batch(db, batch=batch, dry_run=dry_run, stats=stats)

                if not dry_run:
                    try:
                        db.commit()
                    except Exception as exc:  # noqa: BLE001
                        db.rollback()
                        logger.warning(
                            "backfill_batch_commit_failed",
                            run_id=str(run_id),
                            tenant_id=str(tid),
                            batch_num=batch_num,
                            error=str(exc),
                        )

                batch_duration_ms = int((utc_now() - batch_start).total_seconds() * 1000)
                batch_num += 1
                total_processed += len(batch)

                logger.info(
                    "backfill_batch_completed",
                    run_id=str(run_id),
                    tenant_id=str(tid),
                    batch_num=batch_num,
                    batch_size=len(batch),
                    convs_updated=stats.convs_updated if not dry_run else stats.convs_would_update,
                    msgs_legacy_converted=stats.msgs_legacy_converted,
                    convs_skipped_corrupt=stats.convs_skipped_corrupt,
                    duration_ms=batch_duration_ms,
                    cumulative_scanned=stats.convs_scanned,
                    mode=mode,
                )

                # D2: abort if failure_rate > threshold (after n>=100 convs)
                if stats.convs_scanned >= 100:
                    failure_rate = stats.convs_skipped_corrupt / stats.convs_scanned
                    if failure_rate > max_failure_rate:
                        logger.error(
                            "backfill_aborted_high_failure_rate",
                            run_id=str(run_id),
                            failure_rate=failure_rate,
                            threshold=max_failure_rate,
                            scanned=stats.convs_scanned,
                        )
                        _write_audit_row(
                            db,
                            run_id=run_id,
                            tenant_id=tenant_id,
                            mode=mode,
                            status="aborted",
                            stats=stats,
                            error_message="failure_rate_exceeded",
                        )
                        return stats

                if max_convs is not None and total_processed >= max_convs:
                    break

                offset += batch_size

            if max_convs is not None and total_processed >= max_convs:
                break

        # Write final audit row
        _write_audit_row(
            db,
            run_id=run_id,
            tenant_id=tenant_id,
            mode=mode,
            status="completed",
            stats=stats,
        )

        logger.info(
            "backfill_completed",
            run_id=str(run_id),
            mode=mode,
            convs_scanned=stats.convs_scanned,
            convs_already_v2=stats.convs_already_v2,
            convs_updated=stats.convs_updated,
            convs_skipped_corrupt=stats.convs_skipped_corrupt,
            msgs_legacy_converted=stats.msgs_legacy_converted,
            tenants_touched=len(stats.tenants_touched),
        )

    except Exception as exc:  # noqa: BLE001
        logger.error(
            "backfill_failed",
            run_id=str(run_id),
            error=str(exc),
        )
        _write_audit_row(
            db,
            run_id=run_id,
            tenant_id=tenant_id,
            mode=mode,
            status="failed",
            stats=stats,
            error_message=str(exc),
        )
        raise
    finally:
        if _own_session and db is not None:
            db.close()

    return stats


# ── CLI ───────────────────────────────────────────────────────────────────────


def _parse_args() -> argparse.Namespace:
    """Parse CLI arguments per D8 decision."""
    parser = argparse.ArgumentParser(description="Backfill copilot_conversations.messages v1→v2 (content→blocks).")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Actually persist changes. Default = dry-run.",
    )
    parser.add_argument(
        "--confirm-prod",
        action="store_true",
        help="REQUIRED if DATABASE_URL points to *.prod.* — typo guard.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Conversations per batch (default 100).",
    )
    parser.add_argument(
        "--tenant-id",
        type=str,
        default=None,
        help="Restrict to a single tenant UUID.",
    )
    parser.add_argument(
        "--run-id",
        type=str,
        default=None,
        help="UUID for audit trail. Auto-generated if omitted.",
    )
    parser.add_argument(
        "--max-failure-rate",
        type=float,
        default=0.05,
        help="Abort if failure_rate exceeds threshold (0..1). Default 5%%.",
    )
    parser.add_argument(
        "--max-convs",
        type=int,
        default=None,
        help="Stop after N conversations total (smoke testing).",
    )
    return parser.parse_args()


def _check_prod_guard(database_url: str, confirm_prod: bool) -> None:
    """D8: require --confirm-prod if DATABASE_URL contains prod substring."""
    if re.search(r"\.prod\.|prod\.", database_url) and not confirm_prod:
        print(
            "[backfill] ERROR: DATABASE_URL parece apuntar a producción. Agrega --confirm-prod para confirmar.",
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    """CLI entry point."""
    args = _parse_args()

    from src.core.config import settings

    _check_prod_guard(settings.database_url, args.confirm_prod)

    tenant_id: uuid.UUID | None = None
    if args.tenant_id:
        try:
            tenant_id = uuid.UUID(args.tenant_id)
        except ValueError:
            print(f"[backfill] ERROR: --tenant-id inválido: {args.tenant_id}", file=sys.stderr)
            sys.exit(1)

    run_id: uuid.UUID | None = None
    if args.run_id:
        try:
            run_id = uuid.UUID(args.run_id)
        except ValueError:
            print(f"[backfill] ERROR: --run-id inválido: {args.run_id}", file=sys.stderr)
            sys.exit(1)

    dry_run = not args.apply

    print(f"[backfill] mode: {'dry_run' if dry_run else 'apply'} | run_id: {run_id or '(auto)'}")
    if args.tenant_id:
        print(f"[backfill] tenant-id filter: {args.tenant_id}")

    stats = run(
        dry_run=dry_run,
        tenant_id=tenant_id,
        batch_size=args.batch_size,
        run_id=run_id,
        max_failure_rate=args.max_failure_rate,
        max_convs=args.max_convs,
    )

    print(f"[backfill] escaneadas: {stats.convs_scanned} conversaciones")
    if dry_run:
        print(f"[backfill] would_update: {stats.convs_would_update} (mensajes legacy encontrados)")
        print(f"[backfill] would_skip_already_v2: {stats.convs_already_v2}")
        print(f"[backfill] would_skip_corrupt: {stats.convs_skipped_corrupt}")
        if stats.failed_conv_ids:
            sample = [str(x) for x in stats.failed_conv_ids[:10]]
            print(f"[backfill] sample failed_conv_ids (first 10): {sample}")
        print("[backfill] DRY RUN — sin escrituras. Ejecuta con --apply para persistir.")
    else:
        print(f"[backfill] actualizadas: {stats.convs_updated}")
        print(f"[backfill] ya v2: {stats.convs_already_v2}")
        print(f"[backfill] omitidas (corruptas): {stats.convs_skipped_corrupt}")
        print(f"[backfill] mensajes convertidos: {stats.msgs_legacy_converted}")
        print(f"[backfill] committed {stats.convs_updated} updates.")


if __name__ == "__main__":
    main()


__all__ = ["BackfillStats", "_run_batch", "run"]
