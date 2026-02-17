from fastapi import APIRouter, HTTPException, Depends, File, UploadFile, Form
from pydantic import BaseModel, Field
from typing import Literal, Optional, List
from sqlalchemy.orm import Session
from src.core.services.web_extractor_adapter import extract_from_url
from src.core.services.brand_extraction_service import BrandExtractionService
from src.core.services.file_parsing_service import FileParsingService
from src.core.domain.schema import BrandIdentity
from src.core.domain.brand_schema import BrandSettings
from src.api.dependencies import get_current_user, get_db
from src.services.db.models.user import User

router = APIRouter()

class ExtractRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    type: Literal["brand_identity"] = Field("brand_identity", description="Type of extraction to perform")

# Removed FullBrandExtractionRequest as it's now handled via Form/File parameters

@router.post("/extract")
async def extract_data(
    request: ExtractRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Extracts structured data from a URL using the Web Extractor Subgraph.
    Currently supports: 'brand_identity'.
    """
    
    # Select schema based on type
    if request.type == "brand_identity":
        schema = BrandIdentity
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported extraction type: {request.type}")

    # Invoke the extractor graph
    try:
        data = await extract_from_url(request.url, schema)
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
    files: List[UploadFile] = File(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Extracts full Brand Settings (Identity, Story, Team) from URL, Text, or Files.
    Updates the Tenant's config_json with the merged results.
    """
    
    # Parse uploaded files
    extracted_file_text = ""
    if files:
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

    service = BrandExtractionService(db, current_user.tenant_id)
    return await service.extract_all(
        url=url, 
        text=combined_text if combined_text else None, 
        mode=mode, 
        update_instructions=update_instructions,
        dry_run=dry_run
    )
