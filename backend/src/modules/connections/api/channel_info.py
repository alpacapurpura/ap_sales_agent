"""Channel info endpoint for Growth Studio source attribution.

Returns enriched connection details, extraction status, and data range
for a given provider. Used by the ChannelDetailSidebar in the frontend.
"""

from datetime import date

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["channel-info"])
logger = structlog.get_logger()

# Maps provider slug (from channel_registry) to ChannelType(s) used for lookup
_PROVIDER_CHANNEL_TYPES: dict[str, list[ChannelType]] = {
    "google_analytics": [ChannelType.GOOGLE_ANALYTICS],
    "youtube": [ChannelType.YOUTUBE, ChannelType.YOUTUBE_ANALYTICS],
    "meta": [ChannelType.META],
    "google_ads": [ChannelType.GOOGLE_ANALYTICS],
    "mailerlite": [ChannelType.MAILERLITE],
    "manychat": [ChannelType.MANYCHAT],
    "shopify": [ChannelType.SHOPIFY],
    "meta_pixel": [ChannelType.META_PIXEL],
    "search_console": [ChannelType.GOOGLE_ANALYTICS],
}

# Maps provider -> config keys that indicate it's fully configured
_CONFIG_REQUIRED: dict[str, list[str]] = {
    "google_analytics": ["property_id"],
    "youtube": ["channel_id"],
    "meta": [],  # Just needs active connection
    "google_ads": ["property_id"],
    "meta_pixel": [],  # Just needs active connection (child of Meta OAuth)
    "search_console": ["site_url"],
}

# Maps provider -> config keys for display name
_DISPLAY_NAME_KEYS: dict[str, str] = {
    "google_analytics": "property_display_name",
    "youtube": "channel_title",
    "meta": "name",
    "google_ads": "property_display_name",
    "shopify": "shop_name",
    "mailerlite": "account_name",
    "meta_pixel": "pixel_name",
}

# Maps provider -> config keys for account name
_ACCOUNT_NAME_KEYS: dict[str, str] = {
    "google_analytics": "account_name",
    "youtube": "customUrl",
    "meta": "name",
}


class ChannelInfoResponse(BaseModel):
    provider: str
    is_connected: bool
    is_configured: bool = False
    display_name: str | None = None
    account_name: str | None = None
    details: dict = {}
    children: list[dict] = []
    last_extraction: dict | None = None
    data_range: dict | None = None


def _get_repo(db: Session = Depends(get_db)) -> ChannelConnectionRepository:
    return ChannelConnectionRepository(db)


def _build_details(provider: str, config: dict, credentials: dict) -> dict:
    """Build provider-specific detail dict from connection config/credentials."""
    if provider == "google_analytics":
        return {
            "property_id": config.get("property_id"),
            "property_display_name": config.get("property_display_name"),
            "account_name": config.get("account_name"),
        }
    if provider == "youtube":
        return {
            "channel_id": config.get("channel_id"),
            "channel_title": config.get("channel_title"),
            "customUrl": config.get("customUrl"),
            "statistics": config.get("statistics", {}),
        }
    if provider == "meta":
        return {
            "name": config.get("name"),
            "user_id": config.get("user_id"),
            "tracked_page_name": config.get("tracked_page_name"),
            "tracked_ig_username": config.get("tracked_ig_username"),
            "tracked_ad_account_name": config.get("tracked_ad_account_name"),
            "granted_permissions": config.get("granted_permissions", []),
        }
    if provider == "google_ads":
        return {
            "property_id": config.get("property_id"),
            "property_display_name": config.get("property_display_name"),
            "developer_token_configured": bool(credentials.get("developer_token")),
        }
    if provider == "shopify":
        return {
            "shop_url": config.get("shop_url"),
            "shop_name": (config.get("shop_info") or {}).get("name"),
        }
    if provider == "meta_pixel":
        return {
            "pixel_id": config.get("asset_id"),
            "pixel_name": config.get("pixel_name"),
            "linked_ad_account_id": config.get("linked_ad_account_id"),
        }
    return {}


def _get_meta_children(repo: ChannelConnectionRepository, tenant_id) -> list[dict]:
    """Get Meta child assets (pages, IG, ads) for display in sidebar."""
    asset_types = [
        ChannelType.FACEBOOK_PAGE,
        ChannelType.INSTAGRAM_ACCOUNT,
        ChannelType.META_ADS_ACCOUNT,
    ]
    children = repo.get_all_by_tenant_and_types(tenant_id, asset_types)
    result = []
    for child in children:
        cfg = child.config or {}
        result.append(
            {
                "channel_type": child.channel_type,
                "asset_id": cfg.get("asset_id"),
                "name": cfg.get("page_name")
                or cfg.get("ig_username")
                or cfg.get("ad_account_name"),
                "is_active": child.is_active,
                "details": {
                    k: v for k, v in cfg.items() if k != "parent_connection_id"
                },
            }
        )
    return result


@router.get("/{provider}", response_model=ChannelInfoResponse)
async def get_channel_info(
    provider: str,
    user: User = Depends(get_current_user),
    repo: ChannelConnectionRepository = Depends(_get_repo),
    db: Session = Depends(get_db),
):
    """Get enriched connection info for a provider, used by ChannelDetailSidebar."""
    channel_types = _PROVIDER_CHANNEL_TYPES.get(provider)
    if not channel_types:
        raise HTTPException(
            status_code=400, detail=f"Proveedor desconocido: {provider}"
        )

    # Find active connection
    connection = None
    for ct in channel_types:
        conn = repo.get_active(user.tenant_id, ct)
        if conn:
            connection = conn
            break

    if not connection:
        return ChannelInfoResponse(provider=provider, is_connected=False)

    config = connection.config or {}
    credentials = connection.credentials or {}

    # Check if configured
    required_keys = _CONFIG_REQUIRED.get(provider, [])
    is_configured = all(config.get(k) for k in required_keys) if required_keys else True

    # Display name
    display_name_key = _DISPLAY_NAME_KEYS.get(provider)
    display_name = config.get(display_name_key) if display_name_key else None

    # Account name
    account_name_key = _ACCOUNT_NAME_KEYS.get(provider)
    account_name = config.get(account_name_key) if account_name_key else None

    # Details
    details = _build_details(provider, config, credentials)

    # Children (Meta only)
    children = _get_meta_children(repo, user.tenant_id) if provider == "meta" else []

    # Cross-module read: latest extraction run
    last_extraction = None
    try:
        from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
            ExtractionRunRepository,
        )

        run_repo = ExtractionRunRepository(db)
        latest_run = run_repo.get_latest(user.tenant_id, provider)
        if latest_run:
            last_extraction = {
                "status": latest_run.status,
                "started_at": latest_run.started_at.isoformat()
                if latest_run.started_at
                else None,
                "completed_at": latest_run.completed_at.isoformat()
                if latest_run.completed_at
                else None,
                "metrics_count": latest_run.metrics_count,
                "error": latest_run.error,
                "duration_seconds": latest_run.duration_seconds,
            }
    except Exception as e:
        logger.warning("channel_info_extraction_lookup_failed", error=str(e))

    # Cross-module read: data range from official_metrics
    data_range = None
    try:
        from src.modules.analytics.infrastructure.models.official_metrics_model import (
            OfficialMetricModel,
        )

        stmt = select(
            func.min(OfficialMetricModel.metric_date),
            func.max(OfficialMetricModel.metric_date),
            func.count(OfficialMetricModel.id),
        ).where(
            OfficialMetricModel.tenant_id == user.tenant_id,
            OfficialMetricModel.provider == provider,
        )
        row = db.execute(stmt).first()
        if row and row[0]:
            data_range = {
                "min_date": row[0].isoformat()
                if isinstance(row[0], date)
                else str(row[0]),
                "max_date": row[1].isoformat()
                if isinstance(row[1], date)
                else str(row[1]),
                "total_records": row[2],
            }
    except Exception as e:
        logger.warning("channel_info_data_range_lookup_failed", error=str(e))

    return ChannelInfoResponse(
        provider=provider,
        is_connected=True,
        is_configured=is_configured,
        display_name=display_name,
        account_name=account_name,
        details=details,
        children=children,
        last_extraction=last_extraction,
        data_range=data_range,
    )
