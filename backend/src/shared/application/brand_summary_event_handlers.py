"""F3 — wire ``BrandSectionUpdatedEvent`` to the regen ARQ task.

# [COPILOT-BRAND-SUMMARY-F3] -> docs/domains/copilot/redesign-2026-04/phases/F3-brand-summary-lighthouse.md

The handler is split in two concerns so each is independently testable:

* ``handle_brand_section_updated`` — pure dispatcher. Reads the shared
  ARQ pool (None when ARQ is unreachable), builds the dedupe key, and
  enqueues the regen with a 30s debounce so flurry-saves coalesce into
  a single regen.
* ``register_brand_summary_event_handlers`` — idempotent subscription
  registration, mirrors the F0 ``register_extraction_event_handlers``
  pattern. Wired from both FastAPI startup and the ARQ worker startup.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import structlog

from src.shared.domain.events import EventBus

if TYPE_CHECKING:
    from src.shared.domain.events import DomainEvent

logger = structlog.get_logger(__name__)


# 30s window: collapse fast successive Brand Studio saves (autosave can
# fire every couple seconds while the user types) into one regen call.
_DEBOUNCE_SECONDS = 30


def _build_job_id(tenant_id: str) -> str:
    """Stable per-tenant job id for the regen task.

    ARQ rejects duplicate enqueues while a job with the same
    ``_job_id`` is queued or running, so flurry-saves coalesce.
    """
    return f"brand_summary_regen:{tenant_id}"


async def _enqueue_regen(event: DomainEvent) -> None:
    """Async tail — enqueue the regen job."""
    from src.core.arq_pool import get_arq_pool

    pool = get_arq_pool()
    if pool is None:
        logger.warning(
            "brand_summary_regen_arq_unavailable",
            tenant_id=str(event.tenant_id),
        )
        return

    section = event.payload.get("section") if isinstance(event.payload, dict) else None
    job_id = _build_job_id(str(event.tenant_id))
    try:
        await pool.enqueue_job(
            "regen_brand_summary",
            str(event.tenant_id),
            section,
            _job_id=job_id,
            _defer_by=_DEBOUNCE_SECONDS,
        )
    except Exception:
        logger.exception(
            "brand_summary_regen_enqueue_failed",
            tenant_id=str(event.tenant_id),
            job_id=job_id,
        )


def handle_brand_section_updated(event: DomainEvent) -> None:
    """Synchronous EventBus subscriber. Schedules the async enqueue.

    The bus dispatch is sync (after-commit listeners run on the request
    thread) but ARQ ``enqueue_job`` is awaitable. We schedule the coro
    on the running loop when one exists, and fall back to ``asyncio.run``
    when called from a sync context (admin Streamlit button).
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop is not None and loop.is_running():
        loop.create_task(_enqueue_regen(event))
    else:
        try:
            asyncio.run(_enqueue_regen(event))
        except Exception:
            logger.exception(
                "brand_summary_regen_sync_enqueue_failed",
                tenant_id=str(event.tenant_id),
            )


def register_brand_summary_event_handlers() -> None:
    """Subscribe ``handle_brand_section_updated`` once per process."""
    already = handle_brand_section_updated in EventBus._handlers.get(
        "brand_section_updated",
        [],
    )
    if not already:
        EventBus.subscribe("brand_section_updated", handle_brand_section_updated)
        logger.info(
            "brand_summary_event_handlers_registered",
            event_name="brand_section_updated",
        )


__all__ = [
    "handle_brand_section_updated",
    "register_brand_summary_event_handlers",
]
