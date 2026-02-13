from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Literal
from src.core.services.web_extractor_adapter import extract_from_url
from src.core.domain.schema import BrandIdentity
from src.api.dependencies import get_current_user
from src.services.db.models.user import User

router = APIRouter()

class ExtractRequest(BaseModel):
    url: str = Field(..., description="URL to scrape")
    type: Literal["brand_identity"] = Field("brand_identity", description="Type of extraction to perform")

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
