"""Smart-debounce runner — protected timing logic for incoming messages.

Lifted out of :class:`ChatOrchestrator.smart_debounce_task` so the
orchestrator stays a thin facade. The body is **byte-equivalent** to the
pre-S11B implementation — every sleep duration, tolerance window, and
lock-acquisition order has been validated against real LATAM channels
(Telegram / WhatsApp / IG burst patterns) and is part of the §3 protected
surface (see ``00-vision-and-objectives.md``). Refactor preserves
behavior.

Caller side: ``ChatOrchestrator.smart_debounce_task`` is a 1-line
delegate kept on the class so FastAPI's ``background_tasks.add_task``
can target it without changes.

# [SALES-AGENT-SMART-DEBOUNCE-S11B] -> docs/domains/sales-agent/redesign-2026-04/phases/
# S11-shared-lift-orchestrator-decomp.md
"""

from __future__ import annotations

import asyncio
import time
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from sqlalchemy import select

from src.core.database import SessionLocal
from src.modules.iam.infrastructure.models.tenant_model import TenantModel
from src.modules.sales_agent.infrastructure.prompts.semantic import check_is_complete
from src.shared.domain.messages import IncomingMessage

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from src.modules.sales_agent.infrastructure.external.buffer_service import (
        SmartBufferService,
    )
    from src.shared.infrastructure.channels.base import BaseChannel

logger = structlog.get_logger()


async def run_smart_debounce(
    *,
    buffer_service: SmartBufferService,
    buffer_key: str,
    channel_adapter: BaseChannel,
    on_complete: Callable[[BaseChannel, IncomingMessage, str | None], Awaitable[None]],
) -> None:
    """Run the §3-protected dynamic debounce loop for a buffered conversation.

    On completion (final reset + lock acquired), calls ``on_complete`` with
    the reconstructed :class:`IncomingMessage` and the tenant_id recovered
    from buffer metadata.
    """
    try:
        # 1. Initial Buffer (Wait for fast interruptions)
        await asyncio.sleep(0.5)

        # 2. Check if new message arrived (Reset Logic)
        last_ts = buffer_service.get_last_timestamp(buffer_key)
        if time.time() - last_ts < 0.4:  # Tolerance
            # New message arrived recently, abort this task (let the new one handle it)
            return

        # Recover Metadata to get real user_id (for typing status)
        meta = buffer_service.get_metadata(buffer_key)
        real_user_id = meta.get("real_user_id", buffer_key)
        tenant_id = meta.get("tenant_id")

        # 3. Typing Indicator
        await channel_adapter.set_typing_status(real_user_id)

        # 3.5. Fetch tenant object for LLM service resolution
        tenant_obj = None
        if tenant_id:
            db_tmp = None
            try:
                db_tmp = SessionLocal()
                tenant_obj = (
                    db_tmp.execute(
                        select(TenantModel).where(
                            TenantModel.id == UUID(tenant_id),
                        ),
                    )
                    .scalars()
                    .first()
                )
            except Exception as e:  # noqa: BLE001 — orchestrator resilience
                logger.warning("Could not fetch tenant for semantic check", error=str(e))
            finally:
                if db_tmp:
                    db_tmp.close()

        # 4. Semantic Check (LLM)
        # Peek buffer to check completeness
        messages = buffer_service.peek_buffer(buffer_key)
        if not messages:
            return

        full_text = " ".join(messages)

        # Only check semantic if it's substantial enough
        is_complete = False
        if len(full_text) > 5:
            is_complete = await check_is_complete(full_text, tenant=tenant_obj)

        # 5. Dynamic Wait (short if complete, long otherwise)
        wait_time = 4.0 if is_complete else 6.0

        await asyncio.sleep(wait_time)

        # 6. Final Reset Check & Lock
        # If a new message came during the semantic wait, we abort.
        last_ts = buffer_service.get_last_timestamp(buffer_key)
        # Using a small buffer for timing discrepancies
        if time.time() - last_ts < (wait_time + 0.3):
            return

        # Try Acquire Lock
        if not buffer_service.acquire_lock(buffer_key):
            return  # Already being processed

        try:
            # 7. Process
            msgs = buffer_service.get_and_clear_buffer(buffer_key)
            if not msgs:
                return

            final_text = " ".join(msgs)
            # Re-fetch metadata just in case
            meta = buffer_service.get_metadata(buffer_key)
            channel_type = buffer_service.get_channel_type(buffer_key) or "unknown"

            # Reconstruct IncomingMessage with REAL user_id
            incoming = IncomingMessage(
                user_id=real_user_id,
                text=final_text,
                channel_type=channel_type,
                metadata=meta,
            )

            await on_complete(channel_adapter, incoming, tenant_id)

        finally:
            buffer_service.release_lock(buffer_key)

    except Exception as e:
        logger.exception("Error in smart debounce task", error=str(e))


__all__ = ["run_smart_debounce"]
