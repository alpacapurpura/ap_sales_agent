from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.brand.api.dto.extraction import ExtractRequest
from src.modules.brand.domain.aggregates import BrandSettings
from src.modules.copilot.api.dto import BrandExtractResponse
from src.modules.copilot.application.services.brand_ai_actions_service import (
    CopilotBrandAIActionsService,
)
from src.modules.copilot.application.services.offer_psychology_service import (
    CopilotOfferPsychologyService,
)
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context
from src.modules.iam.domain.user import User
from src.modules.offer.domain.offer_ai_schemas import (
    PsychologyGenerationRequest,
    PsychologyGenerationResponse,
)
from src.shared.infrastructure.files.file_parsing_service import FileParsingService

router = APIRouter()


@router.post("/brand/extract", response_model=BrandExtractResponse)
async def extract_brand_data(
    request: ExtractRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if not current_user.tenant_id:
        raise HTTPException(
            status_code=400,
            detail="User is not associated with a tenant.",
        )

    service = CopilotBrandAIActionsService(db, current_user.tenant_id)
    try:
        data = await service.extract_brand_identity(request.url, request.type)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Internal extraction error: {error!s}",
        ) from error

    if not data:
        raise HTTPException(
            status_code=422,
            detail="Extraction failed. Could not find relevant data on the page.",
        )

    return data


@router.post("/brand/extract-full", response_model=BrandSettings)
async def extract_full_brand_data(
    url: str | None = Form(None),
    text: str | None = Form(None),
    mode: Literal["initial", "update"] = Form("initial"),
    update_instructions: str | None = Form(None),
    dry_run: bool = Form(default=False),
    include_visuals: bool = Form(default=False),
    files: list[UploadFile] = File(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    extracted_file_text = ""
    for file in files:
        content = await FileParsingService.parse_file(file)
        if content:
            extracted_file_text += (
                f"\n--- Documento adjunto: {file.filename} ---\n{content}\n"
            )

    combined_text = f"{text or ''}\n{extracted_file_text}".strip()

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

    service = CopilotBrandAIActionsService(db, current_user.tenant_id)
    return await service.extract_full_brand(
        url=url,
        text=combined_text or None,
        mode=mode,
        update_instructions=update_instructions,
        dry_run=dry_run,
        include_visuals=include_visuals,
    )


@router.post("/offer/psychology", response_model=PsychologyGenerationResponse)
async def generate_offer_psychology(
    request: PsychologyGenerationRequest,
    db: Session = Depends(get_db),
    tenant_id: UUID | None = Depends(get_tenant_context),
):
    if not tenant_id:
        raise HTTPException(status_code=401, detail="Tenant ID required")

    service = CopilotOfferPsychologyService(db)
    try:
        return await service.generate_psychology(request, tenant_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"AI Generation failed: {error!s}",
        ) from error
