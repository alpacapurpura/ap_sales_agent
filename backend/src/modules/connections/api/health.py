"""Connection health endpoint.

Evaluates token expiry status for a given channel connection.
Returns health status: healthy, expiring_soon, expired, not_connected.
"""

from datetime import datetime, timedelta, timezone

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["connections-health"])
logger = structlog.get_logger()

# Threshold for "expiring soon" status
_EXPIRY_WARNING_DAYS = 7


class ConnectionHealthResponse(BaseModel):
    """Health status of a single channel connection."""

    model_config = ConfigDict(from_attributes=True)

    status: str  # healthy | expiring_soon | expired | not_connected
    channel_slug: str
    expires_at: str | None = None
    message: str


# Maps URL slugs to ChannelType enum values
_SLUG_TO_CHANNEL_TYPE: dict[str, ChannelType] = {
    "meta": ChannelType.META,
    "meta-ads": ChannelType.META,
    "google-analytics": ChannelType.GOOGLE_ANALYTICS,
    "google-calendar": ChannelType.GOOGLE_CALENDAR,
    "gmail": ChannelType.GMAIL,
    "shopify": ChannelType.SHOPIFY,
    "telegram": ChannelType.TELEGRAM,
    "whatsapp": ChannelType.WHATSAPP,
    "whatsapp-cloud": ChannelType.WHATSAPP_CLOUD,
    "youtube": ChannelType.YOUTUBE,
    "youtube-analytics": ChannelType.YOUTUBE_ANALYTICS,
    "manychat": ChannelType.MANYCHAT,
    "mailerlite": ChannelType.MAILERLITE,
}


def _parse_expires_at(raw_value: str) -> datetime | None:
    """Parse expires_at from ISO 8601 or unix timestamp string."""
    # Try ISO 8601 first
    try:
        dt = datetime.fromisoformat(raw_value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        pass

    else:
        return dt
    # Try unix timestamp (int or float as string)
    try:
        ts = float(raw_value)
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (ValueError, TypeError):
        pass

    return None


def evaluate_connection_health(
    credentials: dict | None,
    channel_slug: str,
) -> ConnectionHealthResponse:
    """Pure function: evaluate token health from credentials dict.

    Logic:
    - None credentials -> not_connected
    - No expires_at field -> healthy (token without expiry)
    - expires_at > now + 7 days -> healthy
    - expires_at <= now + 7 days and > now -> expiring_soon
    - expires_at <= now -> expired
    - Unparseable expires_at -> healthy (graceful fallback)
    """
    if credentials is None:
        return ConnectionHealthResponse(
            status="not_connected",
            channel_slug=channel_slug,
            expires_at=None,
            message="No hay conexión activa para este canal.",
        )

    raw_expires = credentials.get("expires_at")
    if raw_expires is None:
        return ConnectionHealthResponse(
            status="healthy",
            channel_slug=channel_slug,
            expires_at=None,
            message="Conexión activa. El token no tiene fecha de expiración.",
        )

    expires_dt = _parse_expires_at(str(raw_expires))
    if expires_dt is None:
        # Cannot parse -> treat as healthy with warning
        logger.warning(
            "unparseable_expires_at",
            channel_slug=channel_slug,
            raw_value=str(raw_expires),
        )
        return ConnectionHealthResponse(
            status="healthy",
            channel_slug=channel_slug,
            expires_at=str(raw_expires),
            message="Conexión activa. No se pudo interpretar la fecha de expiración.",
        )

    now = datetime.now(timezone.utc)
    expires_iso = expires_dt.isoformat()

    if expires_dt <= now:
        return ConnectionHealthResponse(
            status="expired",
            channel_slug=channel_slug,
            expires_at=expires_iso,
            message="El token ha expirado. Reconecta el canal para renovarlo.",
        )

    warning_threshold = now + timedelta(days=_EXPIRY_WARNING_DAYS)
    if expires_dt <= warning_threshold:
        days_left = (expires_dt - now).days
        return ConnectionHealthResponse(
            status="expiring_soon",
            channel_slug=channel_slug,
            expires_at=expires_iso,
            message=f"El token vence en {days_left} día(s). Recomendamos reconectar pronto.",
        )

    return ConnectionHealthResponse(
        status="healthy",
        channel_slug=channel_slug,
        expires_at=expires_iso,
        message="Conexión activa y saludable.",
    )


@router.get("/{channel_slug}/health", response_model=ConnectionHealthResponse)
async def get_connection_health(
    channel_slug: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ConnectionHealthResponse:
    """Return health status for a specific channel connection."""
    channel_type = _SLUG_TO_CHANNEL_TYPE.get(channel_slug)
    if channel_type is None:
        raise HTTPException(
            status_code=404,
            detail=f"Canal no reconocido: {channel_slug}",
        )

    repo = ChannelConnectionRepository(db)
    connection = repo.get_by_tenant_and_type(user.tenant_id, channel_type)

    if connection is None or not connection.is_active:
        return evaluate_connection_health(credentials=None, channel_slug=channel_slug)

    credentials = connection.credentials or {}
    logger.info(
        "connection_health_checked",
        channel_slug=channel_slug,
        tenant_id=str(user.tenant_id),
    )

    return evaluate_connection_health(
        credentials=credentials,
        channel_slug=channel_slug,
    )
