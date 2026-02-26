from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.modules.iam.api.dependencies import get_current_user
from src.shared.infrastructure.db.database import get_db
from src.modules.iam.domain.user import User
from src.modules.brand.domain import BrandSettings
from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository
import structlog

logger = structlog.get_logger()

router = APIRouter()

@router.get("/brand", response_model=BrandSettings)
async def get_brand_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get Global Brand Settings for the user's tenant.
    """
    if not current_user.tenant_id:
        logger.error("get_brand_settings_error", error="no_tenant_id", user_id=str(current_user.id))
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
    
    repo = BrandRepository(db)
    settings = repo.get_settings(current_user.tenant_id)
    
    # Validation/Defaulting handled by Pydantic
    return settings

@router.patch("/brand", response_model=BrandSettings)
async def update_brand_settings(
    settings: BrandSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update Global Brand Settings for the user's tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User is not associated with a tenant")
        
    repo = BrandRepository(db)
    
    # We might want to merge with existing settings here if the frontend sends partial updates
    # But for now assuming full replacement of sub-objects as per Pydantic behavior
    updated_settings = repo.save_settings(current_user.tenant_id, settings)
    
    return updated_settings
