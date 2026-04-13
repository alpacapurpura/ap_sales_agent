"""Scheduled task: automated follow-up nudges for stalled conversations.

Runs every 1 hour via ARQ cron. Checks active checkpoints with pending
follow_up_cadence, and sends value-driven nudges at the configured delays.

Modeled on frozen_detection.py but sends outbound messages.
"""

import contextlib
import logging
from datetime import datetime, timezone

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


async def run_follow_up_engine(ctx: dict) -> None:
    """Send automated follow-up nudges for eligible conversations."""
    db_factory = ctx["db_factory"]
    db = db_factory()
    sent_count = 0

    try:
        now = datetime.now(timezone.utc)

        # Find active checkpoints with pending follow-up cadence
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
                cadence = cp.follow_up_cadence or {}
                delays = cadence.get("delays_hours", [])
                follow_ups_sent = cadence.get("follow_ups_sent", 0)
                last_follow_up_at = cadence.get("last_follow_up_at")
                cadence_started_at = cadence.get("started_at")

                if not delays or not cadence_started_at:
                    continue

                # Hard cap: never more than FOLLOW_UP_MAX_TOTAL
                if follow_ups_sent >= FOLLOW_UP_MAX_TOTAL:
                    continue

                # Already exhausted all delays
                if follow_ups_sent >= len(delays):
                    cp.frozen_reason = "follow_up_exhausted"
                    cp.frozen_at = now
                    cp.frozen_diagnosis = {
                        "lead_score": cp.lead_score,
                        "funnel_stage": cp.current_stage,
                        "turn_count": cp.turn_count,
                        "follow_ups_sent": follow_ups_sent,
                    }
                    continue

                # Calculate next follow-up time
                reference_time = last_follow_up_at or cadence_started_at
                if isinstance(reference_time, str):
                    reference_time = datetime.fromisoformat(reference_time)
                if reference_time.tzinfo is None:
                    reference_time = reference_time.replace(tzinfo=timezone.utc)

                next_delay_hours = delays[follow_ups_sent]
                next_follow_up_at = reference_time.replace(
                    tzinfo=timezone.utc
                ) + __import__("datetime").timedelta(hours=next_delay_hours)

                if now < next_follow_up_at:
                    continue  # Not time yet

                # Skip weekends
                if now.weekday() >= 5:
                    continue

                # Generate follow-up message
                session_summary = (cp.lead_data or {}).get("session_summary", "")
                offer_name = None
                if cp.lead_data and cp.lead_data.get("active_product_name"):
                    offer_name = cp.lead_data["active_product_name"]

                nudge_prompt = prompt_loader.render(
                    "follow_up_nudge",
                    follow_up_number=follow_ups_sent + 1,
                    session_summary=session_summary,
                    qualification_answers=cp.qualification_answers or {},
                    offer_name=offer_name,
                    channel_type=cp.channel_type,
                )

                nudge_text = LLMFactory.get_service().generate_response(
                    messages=[],
                    system_prompt=nudge_prompt,
                    model_type=ModelRole.FAST,
                    temperature=0.4,
                    max_output_tokens=150,
                    metadata={"prompt_template": "follow_up_nudge"},
                )
                nudge_text = nudge_text.strip()

                if not nudge_text:
                    logger.warning("follow_up_empty_response", lead_id=str(cp.lead_id))
                    continue

                # Send via channel resolver
                from src.modules.crm.infrastructure.repositories.lead_metrics_repository import (
                    LeadRepository,
                )

                lead_repo = LeadRepository(db)
                lead = lead_repo.get_active_lead_by_id(cp.lead_id)
                if not lead:
                    continue

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
                    continue

                # Log in audit trail
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

                # Update cadence state
                cadence["follow_ups_sent"] = follow_ups_sent + 1
                cadence["last_follow_up_at"] = now.isoformat()
                cp.follow_up_cadence = cadence
                sent_count += 1

                # Mark exhausted if this was the last one
                if cadence["follow_ups_sent"] >= len(delays):
                    cp.frozen_reason = "follow_up_exhausted"
                    cp.frozen_at = now
                    cp.frozen_diagnosis = {
                        "lead_score": cp.lead_score,
                        "funnel_stage": cp.current_stage,
                        "turn_count": cp.turn_count,
                        "follow_ups_sent": cadence["follow_ups_sent"],
                    }

            except Exception as e:
                logger.error(
                    "follow_up_single_failed",
                    lead_id=str(cp.lead_id),
                    error=str(e),
                    exc_info=True,
                )
                continue

        if sent_count:
            db.commit()
            logger.info("follow_up_engine_complete", sent_count=sent_count)
        else:
            db.commit()  # persist any exhaustion marks
            logger.debug("follow_up_engine_complete", sent_count=0)

    except Exception as e:
        logger.error("follow_up_engine_failed", error=str(e), exc_info=True)
        with contextlib.suppress(Exception):
            db.rollback()
    finally:
        db.close()
