"""Outbox dispatcher — ARQ worker task.

Runs as a cron job (1 tick/second) per Q1 PM resolution.
Latency p50 0.5s, p99 1.5s between DB commit and dispatch.

Claim semantics: SELECT ... FOR UPDATE SKIP LOCKED.
Multiple worker instances are safe — no duplicate claims.

Retry policy (PR-1):
- Immediate retry on next cron tick (1s).
- max_retries = OUTBOX_MAX_RETRIES (env, default 5).
- After max_retries → status='failed' (manual ops via DB).
- Exponential backoff deferred to PR-2.

See CONTRACT.md §1.A.6 D8 for LISTEN/NOTIFY rejection rationale.
"""

from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any

import structlog
from luana_core_events.outbox.infrastructure.repository import OutboxRepositoryImpl

if TYPE_CHECKING:
    from luana_core_events.outbox.domain.outbox_entry import OutboxEntry

logger = structlog.get_logger(__name__)

_BATCH_SIZE = 50


async def dispatch_outbox(ctx: dict[str, Any]) -> None:
    """ARQ task — claim pending outbox entries and dispatch via in-memory bus.

    Registration in ``WorkerSettings.functions`` and ``SchedulerSettings.cron_jobs``:
        cron(dispatch_outbox, second=set(range(60)))  # 1 tick/second

    Args:
        ctx: ARQ worker context dict with ``db_factory`` async session factory.
    """
    from luana_core_platform.domain.events import EventBus as LegacyEventBus

    # Support both ARQ-style ctx (has db_factory) and test injection (has session)
    db_factory = ctx.get("db_factory")
    if db_factory is None:
        logger.warning("dispatch_outbox_no_db_factory")
        return

    async with db_factory() as session:
        repo = OutboxRepositoryImpl()
        try:
            entries = await repo.claim_pending(batch_size=_BATCH_SIZE, session=session)
        except Exception:  # noqa: BLE001 — best-effort worker, claim failure = skip tick
            logger.warning("dispatch_outbox_claim_failed", exc_info=True)
            return

        dispatched_count = 0
        failed_count = 0

        for entry in entries:
            t_start = time.monotonic()
            try:
                event = _entry_to_event(entry)
                LegacyEventBus._dispatch(event)
                await repo.mark_dispatched(entry.id, entry.tenant_id, session=session)
                duration_ms = int((time.monotonic() - t_start) * 1000)
                logger.info(
                    "outbox_dispatched",
                    entry_id=str(entry.id),
                    event_name=entry.event_name,
                    tenant_id=str(entry.tenant_id),
                    duration_ms=duration_ms,
                )
                dispatched_count += 1
            except Exception as exc:  # noqa: BLE001 — per-entry failure, continue batch
                error_str = str(exc)[:500]
                await repo.mark_failed(
                    entry.id,
                    entry.tenant_id,
                    error=error_str,
                    session=session,
                )
                failed_count += 1

        if dispatched_count > 0 or failed_count > 0:
            logger.info(
                "outbox_batch_complete",
                dispatched=dispatched_count,
                failed=failed_count,
            )

        await session.commit()


def _entry_to_event(entry: OutboxEntry) -> Any:  # noqa: ANN401
    """Reconstruct a DomainEvent from an OutboxEntry for in-memory dispatch."""
    from luana_core_events.outbox.domain.event import DomainEvent

    return DomainEvent(
        event_name=entry.event_name,
        tenant_id=entry.tenant_id,
        payload=entry.payload,
    )
