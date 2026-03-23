"""ARQ task for async brand extraction with Redis progress tracking."""

import json
import logging
from datetime import datetime, timezone
from uuid import UUID

logger = logging.getLogger(__name__)


async def run_brand_extraction(
    ctx: dict,
    job_id: str,
    tenant_id: str,
    url: str | None,
    text: str | None,
    mode: str,
    update_instructions: str | None,
    include_visuals: bool,
    dry_run: bool = False,
) -> dict:
    """Execute brand extraction as a background job.

    Writes progress to Redis at each extraction wave so the frontend
    can poll for real-time updates.
    """
    db_factory = ctx["db_factory"]
    db = db_factory()
    redis = ctx.get("redis")
    progress_key = f"brand_extract:{tenant_id}:{job_id}"

    def on_progress(progress_pct: int, stage: str):
        if redis:
            redis.setex(
                progress_key, 3600,
                json.dumps({
                    "status": "processing",
                    "progress": progress_pct,
                    "stage": stage,
                    "started_at": started_at,
                }),
            )

    started_at = datetime.now(timezone.utc).isoformat()

    try:
        # Late imports to avoid circular dependencies
        from src.modules.copilot.application.services.brand_ai_actions_service import (
            CopilotBrandAIActionsService,
        )

        on_progress(5, "Iniciando análisis...")

        service = CopilotBrandAIActionsService(db, UUID(tenant_id))
        await service.extract_full_brand(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            dry_run=dry_run,
            include_visuals=include_visuals,
            progress_callback=on_progress,
        )

        # Mark completed
        if redis:
            redis.setex(
                progress_key, 3600,
                json.dumps({
                    "status": "completed",
                    "progress": 100,
                    "stage": "¡Análisis completado!",
                }),
            )

        logger.info(
            "Brand extraction completed for tenant=%s job=%s",
            tenant_id, job_id,
        )
        return {"status": "success", "tenant_id": tenant_id, "job_id": job_id}

    except Exception as exc:
        logger.error(
            "Brand extraction failed for tenant=%s job=%s: %s",
            tenant_id, job_id, str(exc),
        )
        if redis:
            redis.setex(
                progress_key, 3600,
                json.dumps({
                    "status": "failed",
                    "progress": 0,
                    "error": f"{type(exc).__name__}: {str(exc)[:200]}",
                }),
            )
        return {"status": "failed", "tenant_id": tenant_id, "error": str(exc)}

    finally:
        db.close()
