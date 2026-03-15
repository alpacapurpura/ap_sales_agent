from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.analytics.application.services.metrics_service import MetricsService
from src.modules.analytics.application.dto.attraction_dto import AttractionDetailDTO

router = APIRouter(prefix="/metrics", tags=["Marketing Metrics"])

@router.get("/sankey")
async def get_marketing_sankey(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get Marketing Sankey Metrics (7 Nodes).
    """
    service = MetricsService(db)
    return service.get_marketing_sankey_metrics(user.tenant_id)


@router.get("/attraction", response_model=AttractionDetailDTO)
async def get_attraction_metrics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Get Attraction stage metrics: 13 channels (8 organic + 5 paid)
    with connection status and visitor/click counts.
    """
    service = MetricsService(db)
    return service.get_attraction_metrics(user.tenant_id)
