"""ARQ task for async offer extraction with Redis progress tracking."""

import json
import logging
import traceback
from datetime import UTC, datetime
from uuid import UUID

logger = logging.getLogger(__name__)


def _fail_progress(redis: object, progress_key: str, error_msg: str, log_detail: str) -> None:
    logger.error("Offer extraction task error: %s", log_detail)
    if redis:
        redis.setex(
            progress_key,
            3600,
            json.dumps({"status": "failed", "progress": 0, "error": error_msg}),
        )


async def run_offer_extraction(
    ctx: dict,
    job_id: str,
    tenant_id: str,
    offer_id: str,
    url: str | None,
    text: str | None,
    mode: str,
    update_instructions: str | None = None,
    **_extra_kwargs: object,
) -> dict:
    """Run offer extraction."""
    redis = ctx.get("redis_cache")
    progress_key = f"offer_extract:{tenant_id}:{job_id}"

    if _extra_kwargs:
        logger.warning(
            "Offer extraction received unexpected kwargs: %s",
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
            "Error interno al conectar con la base de datos.",
            f"DB factory failed for tenant={tenant_id} job={job_id}: {exc}\n{traceback.format_exc()}",
        )
        return {"status": "failed", "tenant_id": tenant_id, "error": str(exc)}

    started_at = datetime.now(UTC).isoformat()

    def on_progress(progress_pct: int, stage: str) -> None:
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

    try:
        from src.modules.offer.application.offer_extraction_service import (
            OfferExtractionService,
        )

        on_progress(5, "Iniciando análisis de oferta...")

        service = OfferExtractionService(db, UUID(tenant_id), UUID(offer_id))

        await service.extract_all(
            url=url,
            text=text,
            mode=mode,
            update_instructions=update_instructions,
            progress_callback=on_progress,
        )

        if redis:
            redis.setex(
                progress_key,
                3600,
                json.dumps(
                    {
                        "status": "completed",
                        "progress": 100,
                        "stage": "¡Análisis de oferta completado!",
                    },
                ),
            )

        logger.info(
            "Offer extraction completed for tenant=%s job=%s",
            tenant_id,
            job_id,
        )

    except Exception as exc:  # noqa: BLE001 — worker task error boundary
        _fail_progress(
            redis,
            progress_key,
            "Ocurrió un error durante el análisis. Intenta de nuevo.",
            f"Offer extraction failed for tenant={tenant_id} job={job_id}: {exc}\n{traceback.format_exc()}",
        )
        return {"status": "failed", "tenant_id": tenant_id, "error": str(exc)}

    else:
        return {"status": "success", "tenant_id": tenant_id, "job_id": job_id}
    finally:
        if db:
            db.close()
