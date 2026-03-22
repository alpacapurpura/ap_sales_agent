import asyncio

from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from typing import Literal, Optional
from sqlalchemy.orm import Session
from src.modules.copilot.application.services.brand_ai_actions_service import CopilotBrandAIActionsService
from src.shared.infrastructure.files.file_parsing_service import FileParsingService
from src.modules.brand.domain.aggregates import BrandSettings
from src.modules.iam.api.dependencies import get_current_user, get_db
from src.modules.iam.domain.user import User
from src.modules.brand.api.dto.extraction import ExtractRequest
import structlog

logger = structlog.get_logger()
router = APIRouter()

# Removed FullBrandExtractionRequest as it's now handled via Form/File parameters

@router.post("/extract")
async def extract_data(
    request: ExtractRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Extracts structured data from a URL using the Web Extractor Subgraph.
    Currently supports: 'brand_identity'.
    """
    
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant.")

    service = CopilotBrandAIActionsService(db, current_user.tenant_id)
    try:
        data = await service.extract_brand_identity(request.url, request.type)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal extraction error: {str(e)}")

    if not data:
        raise HTTPException(status_code=422, detail="Extraction failed. Could not find relevant data on the page.")
        
    return data

@router.post("/extract-full-brand", response_model=BrandSettings)
async def extract_full_brand(
    url: Optional[str] = Form(None),
    text: Optional[str] = Form(None),
    mode: Literal["initial", "update"] = Form("initial"),
    update_instructions: Optional[str] = Form(None),
    dry_run: bool = Form(False),
    include_visuals: bool = Form(False),
    files: list[UploadFile] = File(default_factory=list),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extracts full Brand Settings (Identity, Story, Team) from URL, Text, or Files.
    Updates the Tenant's config_json with the merged results.
    """
    
    # Parse uploaded files
    extracted_file_text = ""
    for file in files:
        content = await FileParsingService.parse_file(file)
        if content:
            extracted_file_text += f"\n--- Documento adjunto: {file.filename} ---\n{content}\n"
    
    # Combine with raw text
    combined_text = (text or "") + "\n" + extracted_file_text
    combined_text = combined_text.strip()

    if not url and not combined_text and not update_instructions:
        raise HTTPException(status_code=400, detail="Either 'url', 'text', 'files', or 'update_instructions' must be provided.")
        
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant.")

    logger.info("extract_full_brand_request",
                tenant_id=str(current_user.tenant_id),
                has_url=bool(url),
                url=url,
                mode=mode,
                has_text=bool(combined_text),
                text_length=len(combined_text) if combined_text else 0,
                file_count=len(files),
                has_instructions=bool(update_instructions),
                dry_run=dry_run)

    service = CopilotBrandAIActionsService(db, current_user.tenant_id)
    try:
        result = await asyncio.wait_for(
            service.extract_full_brand(
                url=url,
                text=combined_text if combined_text else None,
                mode=mode,
                update_instructions=update_instructions,
                dry_run=dry_run,
                include_visuals=include_visuals,
            ),
            timeout=480.0
        )
    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="La extracción tardó demasiado. Intenta con menos contenido o sube la información como texto."
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("extract_full_brand_error",
                     tenant_id=str(current_user.tenant_id),
                     error=str(e),
                     error_type=type(e).__name__)
        raise HTTPException(
            status_code=500,
            detail=f"Error interno en la extracción: {type(e).__name__}: {str(e)[:200]}"
        )

    # Log response summary
    result_dict = result if isinstance(result, dict) else (result.model_dump(mode='json') if result else {})
    logger.info("extract_full_brand_response",
                tenant_id=str(current_user.tenant_id),
                has_identity=bool((result_dict.get("identity") or {}).get("brand_name")),
                has_story=bool((result_dict.get("story") or {}).get("origin_story")),
                has_strategy=bool((result_dict.get("strategy") or {}).get("value_proposition")),
                team_count=len(result_dict.get("team") or []),
                testimonials_count=len(result_dict.get("testimonials") or []),
                authority_count=len(result_dict.get("authority_vault") or []),
                response_keys=list(result_dict.keys()))

    return result
