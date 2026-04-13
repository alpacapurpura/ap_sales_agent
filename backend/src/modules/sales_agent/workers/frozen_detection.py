"""Scheduled task: detect frozen conversations (no activity > 72h).

Runs every 4 hours via ARQ cron. Scans active checkpoints and marks
conversations as frozen when the last message is older than 72 hours.
"""

import contextlib
import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select

from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import (
    AgentStateCheckpointModel,
)
from src.modules.sales_agent.infrastructure.models.message_model import MessageModel

logger = logging.getLogger(__name__)

FROZEN_THRESHOLD_HOURS = 72


async def run_frozen_detection(ctx: dict) -> None:
    """Detect and mark conversations with no activity > 72h as frozen."""
    db_factory = ctx["db_factory"]
    db = db_factory()
    frozen_count = 0

    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=FROZEN_THRESHOLD_HOURS)

        # Find active, non-frozen checkpoints
        stmt = select(AgentStateCheckpointModel).where(
            AgentStateCheckpointModel.is_active.is_(True),
            AgentStateCheckpointModel.deleted_at.is_(None),
            AgentStateCheckpointModel.frozen_at.is_(None),
            AgentStateCheckpointModel.handler_mode == "ai",
        )
        checkpoints = db.execute(stmt).scalars().all()

        for cp in checkpoints:
            # Find last message for this lead
            last_msg_at = db.execute(
                select(func.max(MessageModel.created_at)).where(
                    MessageModel.user_id == cp.lead_id,
                    MessageModel.tenant_id == cp.tenant_id,
                ),
            ).scalar()

            if not last_msg_at:
                continue

            # Normalize timezone
            if last_msg_at.tzinfo is None:
                last_msg_at = last_msg_at.replace(tzinfo=timezone.utc)

            if last_msg_at < cutoff:
                cp.frozen_at = datetime.now(timezone.utc)
                cp.frozen_reason = f"No activity for {FROZEN_THRESHOLD_HOURS}+ hours"
                cp.frozen_diagnosis = {
                    "lead_score": cp.lead_score,
                    "funnel_stage": cp.current_stage,
                    "turn_count": cp.turn_count,
                    "last_specialist": cp.last_specialist,
                    "hours_inactive": round(
                        (datetime.now(timezone.utc) - last_msg_at).total_seconds()
                        / 3600,
                        1,
                    ),
                }
                frozen_count += 1

        if frozen_count:
            db.commit()
            logger.info("frozen_detection_complete", frozen_count=frozen_count)
        else:
            logger.debug("frozen_detection_complete", frozen_count=0)

    except Exception as e:
        logger.error("frozen_detection_failed", error=str(e), exc_info=True)
        with contextlib.suppress(Exception):
            db.rollback()
    finally:
        db.close()
