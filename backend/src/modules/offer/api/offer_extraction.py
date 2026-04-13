import json
from datetime import UTC, datetime
from typing import Literal
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from src.core.database import redis_client
from src.modules.iam.api.dependencies import get_current_user, get_db
from src.modules.iam.domain.user import User
from src.modules.offer.api.dto.extraction import (
    ExtractFullOfferResponse,
    OfferExtractionStatusResponse,
)
from src.shared.infrastructure.files.file_parsing_service import FileParsingService

logger = structlog.get_logger()
router = APIRouter()


@router.post(
    "/extract-full-offer",
    response_model=ExtractFullOfferResponse,
    status_code=202,
)
async def extract_full_offer(
    request: Request,
    offer_id: str = Form(...),
    url: str | None = Form(None),
    text: str | None = Form(None),
    mode: Literal["initial", "update"] = Form("initial"),
    update_instructions: str | None = Form(None),
    files: list[UploadFile] = File(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Parse files
    extracted_file_text = ""
    for file in files:
        content = await FileParsingService.parse_file(file)
        if content:
            extracted_file_text += (
                f"\n--- Documento adjunto: {file.filename} ---\n{content}\n"
            )

    combined_text = (text or "") + "\n" + extracted_file_text
    combined_text = combined_text.strip()

    if not url and not combined_text and not update_instructions:
        raise HTTPException(
            status_code=400,
            detail="Se requiere 'url', 'text', 'files', o 'update_instructions'.",
        )

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400, detail="User is not associated with a tenant."
        )

    if not redis_client:
        raise HTTPException(
            status_code=503, detail="Servicio temporalmente no disponible."
        )

    job_id = str(uuid4())
    tenant_id = str(current_user.tenant_id)

    logger.info(
        "extract_full_offer_request",
        tenant_id=tenant_id,
        job_id=job_id,
        offer_id=offer_id,
        has_url=bool(url),
        mode=mode,
        has_text=bool(combined_text),
    )

    # Set initial Redis status
    if redis_client:
        redis_client.setex(
            f"offer_extract:{tenant_id}:{job_id}",
            3600,
            json.dumps(
                {
                    "status": "queued",
                    "progress": 0,
                    "stage": "Iniciando análisis de oferta...",
                    "started_at": datetime.now(UTC).isoformat(),
                }
            ),
        )

    # Enqueue ARQ job
    arq_pool = request.app.state.arq_pool
    if not arq_pool:
        raise HTTPException(status_code=503, detail="Background job queue unavailable")

    await arq_pool.enqueue_job(
        "run_offer_extraction",
        job_id=job_id,
        tenant_id=tenant_id,
        offer_id=offer_id,
        url=url,
        text=combined_text or None,
        mode=mode,
        update_instructions=update_instructions,
    )

    return ExtractFullOfferResponse(job_id=job_id, status="queued")


@router.get(
    "/extract-full-offer/status/{job_id}",
    response_model=OfferExtractionStatusResponse,
)
async def get_offer_extraction_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
):
    try:
        UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format") from None

    progress_key = f"offer_extract:{current_user.tenant_id}:{job_id}"
    raw = redis_client.get(progress_key) if redis_client else None

    if not raw:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    data = json.loads(raw)

    # Stale job detection
    if data.get("status") in ("processing", "queued") and data.get("started_at"):
        try:
            started = datetime.fromisoformat(data["started_at"])
            if (datetime.now(UTC) - started).total_seconds() > 180:
                data["status"] = "failed"
                data["error"] = "El análisis tardó demasiado. Intenta de nuevo."
        except (ValueError, TypeError):
            pass

    return OfferExtractionStatusResponse(**data)
