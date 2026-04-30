"""Campaigns API routers."""

from src.modules.campaigns.api.routers.campaigns_router import router as campaigns_router
from src.modules.campaigns.api.routers.segments_router import router as segments_router
from src.modules.campaigns.api.routers.templates_router import router as templates_router

__all__ = ["campaigns_router", "segments_router", "templates_router"]
