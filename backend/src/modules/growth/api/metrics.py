from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.shared.infrastructure.db.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.marketing.application.services.metrics_service import MetricsService

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
