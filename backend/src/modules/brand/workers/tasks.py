"""ARQ task for async brand extraction with Redis progress tracking."""

import json
import logging
import traceback
from datetime import UTC, datetime
from uuid import UUID

logger = logging.getLogger(__name__)


def _fail_progress(redis, progress_key: str, error_msg: str, log_detail: str):
    """Write a user-friendly failure to Redis and log the full detail for debugging."""
    logger.error("Brand extraction task error: %s", log_detail)
    if redis:
        redis.setex(
            progress_key,
            3600,
            json.dumps(
                {
                    "status": "failed",
                    "progress": 0,
                    "error": error_msg,
                },
            ),
        )


async def run_brand_extraction(
    ctx: dict,
    job_id: str,
    tenant_id: str,
    url: str | None,
    text: str | None,
    mode: str,
    update_instructions: str | None,
    include_visuals: bool = False,
    include_assets: bool = False,
    dry_run: bool = False,
    **_extra_kwargs,
) -> dict:
    """Execute brand extraction as a background job.

    Writes progress to Redis at each extraction wave so the frontend
    can poll for real-time updates.

    The **_extra_kwargs catch-all prevents TypeError crashes when the API
    sends new parameters that this worker version doesn't know about yet
    (e.g. after a deploy where the API reloaded but the worker didn't).
    """
    redis = ctx.get("redis_cache")
    progress_key = f"brand_extract:{tenant_id}:{job_id}"

    if _extra_kwargs:
        logger.warning(
            "Brand extraction received unexpected kwargs (API/worker version mismatch?): %s",
            list(_extra_kwargs.keys()),
        )

    db = None
    try:
        db_factory = ctx["db_factory"]
        db = db_factory()
    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        _fail_progress(
            redis,
            progress_key,
            "Error interno al conectar con la base de datos. Intenta de nuevo.",
            f"DB factory failed for tenant={tenant_id} job={job_id}: {exc}\n{traceback.format_exc()}",
        )
        return {"status": "failed", "tenant_id": tenant_id, "error": str(exc)}

    started_at = datetime.now(UTC).isoformat()

    def on_progress(progress_pct: int, stage: str):
        if redis:
            redis.setex(
                progress_key,
                3600,
                json.dumps(
                    {
                        "status": "processing",
                        "progress": progress_pct,
                        "stage": stage,
                        "started_at": started_at,
                    },
                ),
            )

    # Create trace collector for this job
    trace = None
    try:
        from src.modules.brand.application.extraction_trace import (
            ExtractionTraceCollector,
        )

        trace = ExtractionTraceCollector(
            db=db,
            tenant_id=UUID(tenant_id),
            job_id=job_id,
            mode=mode,
            profile_name="safe",  # will be overridden by service profile
            url=url,
            include_visuals=include_visuals,
            include_assets=include_assets,
        )
    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        logger.warning("Could not create trace collector: %s", exc)

    try:
        from src.modules.brand.application.extraction_service import (
            BrandExtractionService,
        )

        on_progress(5, "Iniciando análisis...")

        service = BrandExtractionService(db, UUID(tenant_id))

        # Update trace with actual profile name from service
        if trace:
            trace._profile_name = service.profile.name

        await service.extract_all(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            dry_run=dry_run,
            include_visuals=include_visuals,
            include_assets=include_assets,
            progress_callback=on_progress,
            trace=trace,
        )

        if redis:
            redis.setex(
                progress_key,
                3600,
                json.dumps(
                    {
                        "status": "completed",
                        "progress": 100,
                        "stage": "¡Análisis completado!",
                    },
                ),
            )

        logger.info(
            "Brand extraction completed for tenant=%s job=%s",
            tenant_id,
            job_id,
        )

    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        # Save trace even on failure
        if trace:
            try:
                trace.finish(status="failed", error_message=str(exc))
            except Exception:  # noqa: BLE001 — worker task error boundary
                logger.warning("Could not save failure trace", exc_info=True)

        _fail_progress(
            redis,
            progress_key,
            "Ocurrió un error durante el análisis. Intenta de nuevo.",
            f"Brand extraction failed for tenant={tenant_id} job={job_id}: {exc}\n{traceback.format_exc()}",
        )
        return {"status": "failed", "tenant_id": tenant_id, "error": str(exc)}

    else:
        return {"status": "success", "tenant_id": tenant_id, "job_id": job_id}
    finally:
        if db:
            db.close()
