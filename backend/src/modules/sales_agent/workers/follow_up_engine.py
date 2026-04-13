"""Scheduled task: automated follow-up nudges for stalled conversations.

Runs every 1 hour via ARQ cron. Checks active checkpoints with pending
follow_up_cadence, and sends value-driven nudges at the configured delays.

Modeled on frozen_detection.py but sends outbound messages.
"""

import contextlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select

from src.core.enums import ModelRole
from src.modules.sales_agent.application.services.channel_resolver import (
    ChannelResolver,
)
from src.modules.sales_agent.domain.tuning import FOLLOW_UP_MAX_TOTAL
from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from src.modules.sales_agent.infrastructure.prompts.base import prompt_loader
from src.shared.infrastructure.llm.factory import LLMFactory

logger = logging.getLogger(__name__)


def _mark_exhausted(cp, now: datetime, follow_ups_sent: int) -> None:
    """Mark a checkpoint as follow-up exhausted (frozen)."""
    cp.frozen_reason = "follow_up_exhausted"
    cp.frozen_at = now
    cp.frozen_diagnosis = {
        "lead_score": cp.lead_score,
        "funnel_stage": cp.current_stage,
        "turn_count": cp.turn_count,
        "follow_ups_sent": follow_ups_sent,
    }


def _is_ready_for_follow_up(cadence: dict, follow_ups_sent: int, now: datetime) -> bool:
    """Check if enough time has elapsed for the next follow-up."""
    last_follow_up_at = cadence.get("last_follow_up_at")
    cadence_started_at = cadence.get("started_at")

    reference_time = last_follow_up_at or cadence_started_at
    if isinstance(reference_time, str):
        reference_time = datetime.fromisoformat(reference_time)
    if reference_time.tzinfo is None:
        reference_time = reference_time.replace(tzinfo=timezone.utc)

    delays = cadence.get("delays_hours", [])
    next_delay_hours = delays[follow_ups_sent]
    next_follow_up_at = reference_time.replace(tzinfo=timezone.utc) + timedelta(
        hours=next_delay_hours,
    )

    return now >= next_follow_up_at


def _generate_nudge_text(cp, follow_ups_sent: int) -> str:
    """Generate the follow-up nudge message via LLM."""
    session_summary = (cp.lead_data or {}).get("session_summary", "")
    offer_name = (
        cp.lead_data["active_product_name"]
        if cp.lead_data and cp.lead_data.get("active_product_name")
        else None
    )

    nudge_prompt = prompt_loader.render(
        "follow_up_nudge",
        follow_up_number=follow_ups_sent + 1,
        session_summary=session_summary,
        qualification_answers=cp.qualification_answers or {},
        offer_name=offer_name,
        channel_type=cp.channel_type,
    )

    return (
        LLMFactory.get_service()
        .generate_response(
            messages=[],
            system_prompt=nudge_prompt,
            model_type=ModelRole.FAST,
            temperature=0.4,
            max_output_tokens=150,
            metadata={"prompt_template": "follow_up_nudge"},
        )
        .strip()
    )


async def _send_and_log_nudge(db, cp, nudge_text: str, follow_ups_sent: int) -> bool:
    """Send the nudge via channel resolver and log in audit trail. Returns True if sent."""
    from src.modules.crm.infrastructure.repositories.lead_metrics_repository import (
        LeadRepository,
    )

    lead_repo = LeadRepository(db)
    lead = lead_repo.get_active_lead_by_id(cp.lead_id)
    if not lead:
        return False

    resolver = ChannelResolver(db)
    sent = await resolver.send_to_lead(
        tenant_id=cp.tenant_id,
        lead=lead,
        text=nudge_text,
        preferred_channel=cp.channel_type,
    )

    if not sent:
        logger.warning(
            "follow_up_channel_unavailable",
            lead_id=str(cp.lead_id),
            channel=cp.channel_type,
        )
        return False

    from src.modules.sales_agent.infrastructure.memory.audit_repository import (
        AuditRepository,
    )

    audit_repo = AuditRepository(db)
    audit_repo.log_message(
        user_id=cp.lead_id,
        role="assistant",
        content=nudge_text,
        channel=cp.channel_type,
        tenant_id=cp.tenant_id,
        metadata={
            "source": "auto_follow_up",
            "follow_up_number": follow_ups_sent + 1,
        },
    )
    return True


def _should_skip_checkpoint(cp, now: datetime) -> bool:
    """Return True if this checkpoint should be skipped for follow-up."""
    cadence = cp.follow_up_cadence or {}
    delays = cadence.get("delays_hours", [])
    follow_ups_sent = cadence.get("follow_ups_sent", 0)

    if not delays or not cadence.get("started_at"):
        return True
    if follow_ups_sent >= FOLLOW_UP_MAX_TOTAL:
        return True
    if follow_ups_sent >= len(delays):
        _mark_exhausted(cp, now, follow_ups_sent)
        return True
    if not _is_ready_for_follow_up(cadence, follow_ups_sent, now):
        return True
    # Skip weekends
    return now.weekday() >= 5


async def _process_single_checkpoint(db, cp, now: datetime) -> bool:
    """Process a single checkpoint for follow-up. Returns True if a nudge was sent."""
    if _should_skip_checkpoint(cp, now):
        return False

    cadence = cp.follow_up_cadence or {}
    follow_ups_sent = cadence.get("follow_ups_sent", 0)

    nudge_text = _generate_nudge_text(cp, follow_ups_sent)
    if not nudge_text:
        logger.warning("follow_up_empty_response", lead_id=str(cp.lead_id))
        return False

    sent = await _send_and_log_nudge(db, cp, nudge_text, follow_ups_sent)
    if not sent:
        return False

    # Update cadence state
    cadence["follow_ups_sent"] = follow_ups_sent + 1
    cadence["last_follow_up_at"] = now.isoformat()
    cp.follow_up_cadence = cadence

    # Mark exhausted if this was the last one
    if cadence["follow_ups_sent"] >= len(cadence.get("delays_hours", [])):
        _mark_exhausted(cp, now, cadence["follow_ups_sent"])

    return True


async def run_follow_up_engine(ctx: dict) -> None:
    """Send automated follow-up nudges for eligible conversations."""
    db_factory = ctx["db_factory"]
    db = db_factory()
    sent_count = 0

    try:
        now = datetime.now(timezone.utc)

        stmt = select(AgentStateCheckpointModel).where(
            AgentStateCheckpointModel.is_active.is_(True),
            AgentStateCheckpointModel.deleted_at.is_(None),
            AgentStateCheckpointModel.frozen_at.is_(None),
            AgentStateCheckpointModel.handler_mode == "ai",
            AgentStateCheckpointModel.follow_up_cadence.isnot(None),
        )
        checkpoints = db.execute(stmt).scalars().all()

        for cp in checkpoints:
            try:
                if await _process_single_checkpoint(db, cp, now):
                    sent_count += 1
            except Exception as e:
                logger.error(
                    "follow_up_single_failed",
                    lead_id=str(cp.lead_id),
                    error=str(e),
                    exc_info=True,
                )
                continue

        db.commit()
        if sent_count:
            logger.info("follow_up_engine_complete", sent_count=sent_count)
        else:
            logger.debug("follow_up_engine_complete", sent_count=0)

    except Exception as e:
        logger.error("follow_up_engine_failed", error=str(e), exc_info=True)
        with contextlib.suppress(Exception):
            db.rollback()
    finally:
        db.close()
