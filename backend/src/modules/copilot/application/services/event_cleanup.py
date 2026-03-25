"""ARQ task for soft-deleting copilot events older than 90 days."""

from datetime import datetime, timedelta, timezone

import structlog

from src.core.database import SessionLocal
from src.modules.copilot.infrastructure.repositories.event_repository import (
    CopilotEventRepository,
)

logger = structlog.get_logger()


async def cleanup_old_events(ctx):
    """Soft-delete copilot events older than 90 days. Runs daily via ARQ."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    db = SessionLocal()
    try:
        repo = CopilotEventRepository(db)
        count = repo.soft_delete_before(cutoff)
        db.commit()
        logger.info("copilot_events_cleanup", deleted_count=count)
    finally:
        db.close()
