from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import uuid

from src.api.dependencies import get_db, get_current_tenant_id
from src.services.dashboard_service import DashboardService
from src.core.domain.dashboard_schema import DashboardResponse

router = APIRouter()

@router.get("/summary", response_model=DashboardResponse)
async def get_dashboard_summary(
    tenant_id: str = Depends(get_current_tenant_id),
    db: Session = Depends(get_db)
):
    """
    Get high-level dashboard metrics and action items.
    """
    service = DashboardService(db)
    # Ensure tenant_id is UUID
    try:
        tenant_uuid = uuid.UUID(tenant_id)
    except ValueError:
        # Should be handled by dependency but safety check
        tenant_uuid = uuid.UUID(int=0) # Invalid or handle error
        
    return service.get_summary(tenant_uuid)
