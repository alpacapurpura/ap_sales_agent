from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.core.database import get_db, redis_client
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.analytics.application.services.metrics_service import MetricsService
from src.modules.analytics.application.dto.attraction_dto import AttractionDetailDTO
from src.modules.analytics.infrastructure.cache.metrics_cache import MetricsCache
from src.modules.connections.application.services.connection_port_impl import ConnectionPortImpl

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
    Get Attraction stage metrics with dynamic channel list from ETL tables.
    Channels are sourced from ChannelRegistry; values from official_metrics.
    """
    cache = MetricsCache(redis_client)
    connection_port = ConnectionPortImpl(db)
    service = MetricsService(db, cache=cache, connection_port=connection_port)
    return await service.get_attraction_metrics(user.tenant_id)
