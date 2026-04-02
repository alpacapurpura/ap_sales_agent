"""ARQ task for soft-deleting copilot events older than 90 days."""

import sentry_sdk
from datetime import datetime, timedelta, timezone
from sentry_sdk.crons import MonitorStatus, capture_checkin

import structlog

from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.repositories.event_repository import (
    CopilotEventRepository,
)

logger = structlog.get_logger()


async def cleanup_old_events(ctx):
    """Soft-delete copilot events older than 90 days. Runs daily via ARQ."""
    check_in_id = capture_checkin(
        monitor_slug="copilot-event-cleanup",
        status=MonitorStatus.IN_PROGRESS,
        monitor_config={
            "schedule": {"type": "crontab", "value": "30 3 * * *"},
            "checkin_margin": 5,
            "max_runtime": 15,
        },
    )

    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    db = SessionLocal()
    try:
        repo = CopilotEventRepository(db)
        count = repo.soft_delete_before(cutoff)
        db.commit()
        logger.info("copilot_events_cleanup", deleted_count=count)
        capture_checkin(
            monitor_slug="copilot-event-cleanup",
            check_in_id=check_in_id,
            status=MonitorStatus.OK,
        )
    except Exception as exc:
        sentry_sdk.capture_exception(exc)
        capture_checkin(
            monitor_slug="copilot-event-cleanup",
            check_in_id=check_in_id,
            status=MonitorStatus.ERROR,
        )
        raise
    finally:
        db.close()
