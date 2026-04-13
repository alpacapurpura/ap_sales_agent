"""
YouTube Analytics API Router.

Exposes channel overview, daily views, top videos, demographics,
and traffic sources for the Growth Studio and Sales Studio.
"""

import datetime
from typing import Annotated

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.api.dto.common import (
    ConnectionTestResponse,
    YouTubeAnalyticsDataResponse,
    YouTubeAnalyticsStatusResponse,
)
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.channels.youtube_analytics import (
    YouTubeAnalyticsAdapter,
)
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.shared.domain.datetime_utils import utc_today

router = APIRouter(tags=["youtube-analytics"])


class VideoDetail(BaseModel):
    """Enriched video detail combining Analytics + Data API data."""

    video_id: str
    title: str
    thumbnail_url: str
    duration: str  # ISO 8601
    published_at: str
    views: int
    likes: int
    watch_time_minutes: float
    avg_view_duration: float


class TopVideosResponse(BaseModel):
    status: str
    data: list[VideoDetail]
    start_date: str
    end_date: str


logger = structlog.get_logger()


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


def _get_adapter(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
) -> YouTubeAnalyticsAdapter:
    """Resolve credentials and return an initialised adapter."""
    # Try YouTube Analytics connection first, fall back to YouTube Data connection
    connection = repo.get_active(user.tenant_id, ChannelType.YOUTUBE_ANALYTICS)
    if not connection or not connection.credentials:
        connection = repo.get_active(user.tenant_id, ChannelType.YOUTUBE)
    if not connection or not connection.credentials:
        raise HTTPException(
            status_code=400,
            detail="YouTube no conectado. Conecta tu cuenta de Google primero.",
        )

    return YouTubeAnalyticsAdapter(connection.credentials)


def _default_dates(
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, str]:
    """Defaults to last 30 days if no dates provided."""
    today = utc_today()
    if not end_date:
        end_date = today.isoformat()
    if not start_date:
        start_date = (today - datetime.timedelta(days=30)).isoformat()
    return start_date, end_date


# ── Endpoints ──────────────────────────────────────────────────────────────


@router.get("/status", response_model=YouTubeAnalyticsStatusResponse)
async def get_status(
    user: Annotated[User, Depends(get_current_user)],
    repo: Annotated[ChannelConnectionRepository, Depends(_get_repo)],
) -> dict[str, bool | str | None]:
    """Check if YouTube Analytics is connected and retrieve channel info."""
    connection = repo.get_active(user.tenant_id, ChannelType.YOUTUBE_ANALYTICS)
    if not connection:
        connection = repo.get_active(user.tenant_id, ChannelType.YOUTUBE)

    if not connection or not connection.credentials:
        return {"is_connected": False}

    # Try to get channel info
    try:
        adapter = YouTubeAnalyticsAdapter(connection.credentials)
        channel_id = adapter.get_channel_id()
    except Exception as e:  # noqa: BLE001 — API error boundary
        logger.warning("youtube_analytics_status_failed", error=str(e))
        return {"is_connected": True, "channel_id": None}

    else:
        return {
            "is_connected": True,
            "channel_id": channel_id,
        }


@router.get("/overview", response_model=YouTubeAnalyticsDataResponse)
async def get_overview(
    adapter: Annotated[YouTubeAnalyticsAdapter, Depends(_get_adapter)],
    start_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
) -> dict[str, str | dict]:
    """
    Aggregate channel metrics: views, watch time, subscribers, avg duration.
    Defaults to last 30 days.
    """
    sd, ed = _default_dates(start_date, end_date)
    try:
        data = adapter.get_channel_overview(sd, ed)
    except Exception as e:
        logger.exception("youtube_analytics_overview_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    else:
        return {"status": "ok", "data": data, "start_date": sd, "end_date": ed}


@router.get("/daily-views", response_model=YouTubeAnalyticsDataResponse)
async def get_daily_views(
    adapter: Annotated[YouTubeAnalyticsAdapter, Depends(_get_adapter)],
    start_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
) -> dict[str, str | list[dict]]:
    """Daily time-series of views and watch time."""
    sd, ed = _default_dates(start_date, end_date)
    try:
        data = adapter.get_daily_views(sd, ed)
    except Exception as e:
        logger.exception("youtube_analytics_daily_views_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    else:
        return {"status": "ok", "data": data, "start_date": sd, "end_date": ed}


@router.get("/top-videos", response_model=YouTubeAnalyticsDataResponse)
async def get_top_videos(
    adapter: Annotated[YouTubeAnalyticsAdapter, Depends(_get_adapter)],
    start_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    max_results: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict[str, str | list[dict]]:
    """Top videos by views in the date range."""
    sd, ed = _default_dates(start_date, end_date)
    try:
        data = adapter.get_top_videos(sd, ed, max_results=max_results)
    except Exception as e:
        logger.exception("youtube_analytics_top_videos_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    else:
        return {"status": "ok", "data": data, "start_date": sd, "end_date": ed}


@router.get("/demographics", response_model=YouTubeAnalyticsDataResponse)
async def get_demographics(
    adapter: Annotated[YouTubeAnalyticsAdapter, Depends(_get_adapter)],
    start_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
) -> dict[str, str | list[dict]]:
    """Audience demographics (age group + gender)."""
    sd, ed = _default_dates(start_date, end_date)
    try:
        data = adapter.get_demographics(sd, ed)
    except Exception as e:
        logger.exception("youtube_analytics_demographics_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    else:
        return {"status": "ok", "data": data, "start_date": sd, "end_date": ed}


@router.get("/traffic-sources", response_model=YouTubeAnalyticsDataResponse)
async def get_traffic_sources(
    adapter: Annotated[YouTubeAnalyticsAdapter, Depends(_get_adapter)],
    start_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
) -> dict[str, str | list[dict]]:
    """Views by traffic source (search, suggested, external, etc.)."""
    sd, ed = _default_dates(start_date, end_date)
    try:
        data = adapter.get_traffic_sources(sd, ed)
    except Exception as e:
        logger.exception("youtube_analytics_traffic_sources_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    else:
        return {"status": "ok", "data": data, "start_date": sd, "end_date": ed}


@router.get("/countries", response_model=YouTubeAnalyticsDataResponse)
async def get_countries(
    adapter: Annotated[YouTubeAnalyticsAdapter, Depends(_get_adapter)],
    start_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    max_results: Annotated[int, Query(ge=1, le=50)] = 10,
) -> dict[str, str | list[dict]]:
    """Views by country."""
    sd, ed = _default_dates(start_date, end_date)
    try:
        data = adapter.get_countries(sd, ed, max_results=max_results)
    except Exception as e:
        logger.exception("youtube_analytics_countries_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e

    else:
        return {"status": "ok", "data": data, "start_date": sd, "end_date": ed}


@router.get("/top-videos-enriched")
async def get_top_videos_enriched(
    adapter: Annotated[YouTubeAnalyticsAdapter, Depends(_get_adapter)],
    start_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    end_date: Annotated[str | None, Query(description="YYYY-MM-DD")] = None,
    max_results: Annotated[int, Query(ge=1, le=50)] = 10,
) -> TopVideosResponse:
    """Top videos enriched with title, thumbnail, duration from Data API v3."""
    sd, ed = _default_dates(start_date, end_date)
    try:
        data = adapter.get_top_videos_enriched(sd, ed, max_results=max_results)
        videos = [VideoDetail(**v) for v in data]
        return TopVideosResponse(status="ok", data=videos, start_date=sd, end_date=ed)
    except Exception as e:
        logger.exception("youtube_analytics_top_videos_enriched_failed", error=str(e))
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.post("/test", response_model=ConnectionTestResponse)
async def test_connection(
    adapter: Annotated[YouTubeAnalyticsAdapter, Depends(_get_adapter)],
) -> dict[str, str | dict | None]:
    """Test the connection by fetching the last 7 days overview."""
    today = utc_today()
    start = (today - datetime.timedelta(days=7)).isoformat()
    end = today.isoformat()
    try:
        overview = adapter.get_channel_overview(start, end)
        channel_id = adapter.get_channel_id()
    except Exception as e:
        logger.exception("youtube_analytics_test_failed", error=str(e))
        return {"status": "error", "message": str(e)}
    else:
        return {
            "status": "ok",
            "message": "Conexión con YouTube Analytics exitosa",
            "data": {
                "channel_id": channel_id,
                "period": f"{start} — {end}",
                **overview,
            },
        }
