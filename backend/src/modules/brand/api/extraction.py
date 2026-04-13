import json
from datetime import UTC, datetime
from typing import Annotated, Literal
from uuid import UUID, uuid4

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from src.core.database import redis_client
from src.modules.brand.api.dto.extraction import (
    BrandVisualsResponse,
    ExtractFullBrandResponse,
    ExtractionStatusResponse,
    ExtractionTraceResponse,
    ExtractionTraceSummaryResponse,
    ExtractRequest,
)
from src.modules.brand.application.extraction_service import BrandExtractionService
from src.modules.brand.infrastructure.models.extraction_trace_model import (
    BrandExtractionTrace,
)
from src.modules.iam.api.dependencies import get_current_user, get_db
from src.modules.iam.domain.user import User
from src.shared.infrastructure.files.file_parsing_service import FileParsingService

logger = structlog.get_logger()
router = APIRouter()

# Removed FullBrandExtractionRequest as it's now handled via Form/File parameters


@router.post("/extract", response_model=BrandVisualsResponse)
async def extract_data(
    request: ExtractRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """
    Extracts structured data from a URL using the Web Extractor Subgraph.
    Currently supports: 'brand_identity'.
    """

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant.",
        )

    service = BrandExtractionService(db, current_user.tenant_id)
    try:
        data = await service.extract_visuals_only(request.url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal extraction error: {e!s}",
        ) from e

    if not data:
        raise HTTPException(
            status_code=422,
            detail="Extraction failed. Could not find relevant data on the page.",
        )

    return data


@router.post(
    "/extract-full-brand",
    response_model=ExtractFullBrandResponse,
    status_code=202,
)
async def extract_full_brand(
    request: Request,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    url: Annotated[str | None, Form()] = None,
    text: Annotated[str | None, Form()] = None,
    mode: Annotated[Literal["initial", "update"], Form()] = "initial",
    update_instructions: Annotated[str | None, Form()] = None,
    dry_run: Annotated[bool, Form()] = False,
    include_visuals: Annotated[bool, Form()] = False,
    include_assets: Annotated[bool, Form()] = False,
    files: Annotated[list[UploadFile], File()] = [],  # noqa: B006
):
    """
    Dispatches full brand extraction as an async job.
    Returns 202 with job_id for polling via GET /extract-full-brand/status/{job_id}.
    """
    # Parse uploaded files (UploadFile can't be serialized to ARQ)
    extracted_file_text = ""
    for file in files:
        content = await FileParsingService.parse_file(file)
        if content:
            extracted_file_text += f"\n--- Documento adjunto: {file.filename} ---\n{content}\n"

    combined_text = (text or "") + "\n" + extracted_file_text
    combined_text = combined_text.strip()

    if not url and not combined_text and not update_instructions:
        raise HTTPException(
            status_code=400,
            detail="Either 'url', 'text', 'files', or 'update_instructions' must be provided.",
        )

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant.",
        )

    if not redis_client:
        raise HTTPException(
            status_code=503,
            detail="Servicio temporalmente no disponible. Intenta en un momento.",
        )

    job_id = str(uuid4())
    tenant_id = str(current_user.tenant_id)

    logger.info(
        "extract_full_brand_request",
        tenant_id=tenant_id,
        job_id=job_id,
        has_url=bool(url),
        url=url,
        mode=mode,
        has_text=bool(combined_text),
        text_length=len(combined_text) if combined_text else 0,
        file_count=len(files),
        has_instructions=bool(update_instructions),
        dry_run=dry_run,
    )

    # Set initial status in Redis BEFORE enqueue (prevents race condition)
    if redis_client:
        redis_client.setex(
            f"brand_extract:{tenant_id}:{job_id}",
            3600,
            json.dumps(
                {
                    "status": "queued",
                    "progress": 0,
                    "stage": "Iniciando análisis...",
                    "started_at": datetime.now(UTC).isoformat(),
                },
            ),
        )

    # Enqueue ARQ job
    arq_pool = request.app.state.arq_pool
    if not arq_pool:
        raise HTTPException(status_code=503, detail="Background job queue unavailable")
    await arq_pool.enqueue_job(
        "run_brand_extraction",
        job_id=job_id,
        tenant_id=tenant_id,
        url=url,
        text=combined_text or None,
        mode=mode,
        update_instructions=update_instructions,
        include_visuals=include_visuals,
        include_assets=include_assets,
        dry_run=dry_run,
    )

    logger.info("extract_full_brand_dispatched", tenant_id=tenant_id, job_id=job_id)

    return ExtractFullBrandResponse(job_id=job_id, status="queued")


@router.get(
    "/extract-full-brand/status/{job_id}",
    response_model=ExtractionStatusResponse,
)
async def get_extraction_status(
    job_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Poll extraction job progress. Returns status, progress %, and current stage."""

    # Validate job_id format
    try:
        UUID(job_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid job ID format") from None

    progress_key = f"brand_extract:{current_user.tenant_id}:{job_id}"
    raw = redis_client.get(progress_key) if redis_client else None

    if not raw:
        raise HTTPException(status_code=404, detail="Job not found or expired")

    data = json.loads(raw)

    # Stale job detection: if no progress for >3 minutes, mark as failed
    if data.get("status") in ("processing", "queued") and data.get("started_at"):
        try:
            started = datetime.fromisoformat(data["started_at"])
            if (datetime.now(UTC) - started).total_seconds() > 180:
                data["status"] = "failed"
                data["error"] = "El análisis tardó demasiado o no pudo completarse. Intenta de nuevo."
        except (ValueError, TypeError):
            pass

    return ExtractionStatusResponse(**data)


@router.get(
    "/extraction-traces",
    response_model=list[ExtractionTraceSummaryResponse],
)
async def list_extraction_traces(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    limit: int = 20,
):
    """List recent brand extraction traces for the current tenant."""

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant.",
        )

    stmt = (
        select(BrandExtractionTrace)
        .where(BrandExtractionTrace.tenant_id == current_user.tenant_id)
        .order_by(desc(BrandExtractionTrace.created_at))
        .limit(min(limit, 50))
    )
    rows = db.execute(stmt).scalars().all()

    return [
        ExtractionTraceSummaryResponse(
            id=str(r.id),
            job_id=r.job_id,
            mode=r.mode,
            profile_name=r.profile_name,
            url=r.url,
            status=r.status,
            sections_total=r.sections_total,
            sections_succeeded=r.sections_succeeded,
            total_duration_s=r.total_duration_s,
            content_length=r.content_length,
            error_message=r.error_message,
            created_at=r.created_at.isoformat() if r.created_at else None,
        )
        for r in rows
    ]


@router.get("/extraction-traces/{trace_id}", response_model=ExtractionTraceResponse)
async def get_extraction_trace(
    trace_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get full trace detail including all events."""

    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant.",
        )

    try:
        UUID(trace_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid trace ID format") from None

    stmt = select(BrandExtractionTrace).where(
        BrandExtractionTrace.id == trace_id,
        BrandExtractionTrace.tenant_id == current_user.tenant_id,
    )
    row = db.execute(stmt).scalar_one_or_none()
    if not row:
        raise HTTPException(status_code=404, detail="Trace not found")

    return ExtractionTraceResponse(
        id=str(row.id),
        job_id=row.job_id,
        mode=row.mode,
        profile_name=row.profile_name,
        url=row.url,
        include_visuals=row.include_visuals,
        include_assets=row.include_assets,
        status=row.status,
        sections_total=row.sections_total,
        sections_succeeded=row.sections_succeeded,
        total_duration_s=row.total_duration_s,
        content_length=row.content_length,
        error_message=row.error_message,
        events=row.events or [],
        created_at=row.created_at.isoformat() if row.created_at else None,
    )
