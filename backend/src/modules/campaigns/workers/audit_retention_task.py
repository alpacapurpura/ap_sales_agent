"""ARQ cron — daily 04:30 UTC retention purge for campaign_audit table.

Hard deletes audit rows older than retention window. Bounded delete:
WHERE created_at < cutoff LIMIT 5000 per batch, loop until rowcount=0
or job_timeout (10 min). Uses ix_campaign_audit_created index — cheap scan.

campaign_audit table uses HARD DELETE (append-only table — soft-delete over
100K rows/day would be unsustainable). Single architecture exception documented
in test_no_hard_deletes.py allowlist entry: 'campaign_audit'.

Env:
  CAMPAIGNS_AUDIT_RETENTION_DAYS=90   (default; min=7, max=365)

Mirror pattern: purge_expired_trace_rows (copilot observability, runs 04:00 UTC).
PR-5 runs at 04:30 UTC to offset the copilot purge.

PR-5 PI-1 S2.
"""

from __future__ import annotations

import datetime as dt
import os
from typing import TYPE_CHECKING

import structlog

if TYPE_CHECKING:
    from collections.abc import Callable
    from contextlib import AbstractAsyncContextManager

    from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.datetime_utils import utc_now

logger = structlog.get_logger(__name__)

CAMPAIGNS_AUDIT_RETENTION_DAYS = "CAMPAIGNS_AUDIT_RETENTION_DAYS"
CAMPAIGN_AUDIT_TABLE = "campaign_audit"

_DEFAULT_RETENTION_DAYS = 90
_MIN_RETENTION_DAYS = 7
_MAX_RETENTION_DAYS = 365
_BATCH_SIZE = 5_000


def _retention_days() -> int:
    """Read retention days from env with safety clamp."""
    raw = int(os.environ.get(CAMPAIGNS_AUDIT_RETENTION_DAYS, str(_DEFAULT_RETENTION_DAYS)))
    return max(_MIN_RETENTION_DAYS, min(_MAX_RETENTION_DAYS, raw))


async def purge_old_campaigns_audit(ctx: dict) -> dict[str, int]:
    """ARQ cron entry — purge audit rows older than retention window.

    Args:
        ctx: ARQ context with ``db_factory`` key.

    Returns:
        Dict with ``deleted`` (total rows deleted) and ``batches`` (batch count).
    """
    db_factory = ctx["db_factory"]
    retention = _retention_days()
    cutoff = utc_now() - dt.timedelta(days=retention)

    total_deleted = 0
    batches = 0

    logger.info(
        "audit_retention_purge_start",
        retention_days=retention,
        cutoff=cutoff.isoformat(),
        table=CAMPAIGN_AUDIT_TABLE,
    )

    # Bounded delete loop: batch until rowcount=0 or job_timeout
    while True:
        deleted = await _delete_batch(db_factory, cutoff)
        if deleted == 0:
            break
        total_deleted += deleted
        batches += 1

        logger.info(
            "audit_retention_purge_batch",
            batch=batches,
            deleted_this_batch=deleted,
            total_so_far=total_deleted,
        )

    logger.info(
        "audit_retention_purge_complete",
        rows_deleted=total_deleted,
        batches=batches,
    )
    return {"deleted": total_deleted, "batches": batches}


async def _delete_batch(
    db_factory: Callable[[], AbstractAsyncContextManager[AsyncSession]],
    cutoff: dt.datetime,
) -> int:
    """Delete one batch of stale audit rows. Returns rows deleted."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from src.modules.campaigns.infrastructure.repositories.audit_log_repo_impl import (
        AuditLogRepositoryImpl,
    )

    assert isinstance(cutoff, dt.datetime)  # noqa: S101

    async with db_factory() as session:
        assert isinstance(session, AsyncSession)  # noqa: S101

        repo = AuditLogRepositoryImpl()
        deleted = await repo.purge_older_than(
            cutoff=cutoff,
            batch_size=_BATCH_SIZE,
            session=session,
        )
        await session.commit()
        return deleted
