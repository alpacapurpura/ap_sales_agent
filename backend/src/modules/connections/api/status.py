"""Batch connection status endpoint.

Returns the connection status for ALL providers of a tenant in a single call.
Used by the Connections Hub to show status badges on each card.
"""

from typing import Annotated

import structlog
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.connections.infrastructure.repositories import (
    ChannelConnectionRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(tags=["connections-status"])
logger = structlog.get_logger()


class ConnectionStatusItem(BaseModel):
    """Status of a single connection for a tenant."""

    channel_type: str
    is_connected: bool
    display_name: str | None = None
    last_sync: str | None = None


class BatchConnectionStatusResponse(BaseModel):
    """Response model — explicit allowlist of fields (PII sanitisation rule)."""

    connections: list[ConnectionStatusItem]


# Maps channel_type -> config key for a human-readable display name
_DISPLAY_NAME_KEYS: dict[str, str] = {
    "meta": "name",
    "shopify": "shop_url",
    "whatsapp": "phone_number",
    "whatsapp_cloud": "phone_number",
    "google_analytics": "property_display_name",
    "youtube": "channel_title",
    "telegram": "bot_name",
    "manychat": "account_name",
    "mailerlite": "account_name",
    "gmail": "email",
    "google_calendar": "email",
}


def _mask_pii(value: str, channel_type: str) -> str:
    """Mask PII fields (email, phone) for safe display. Required by PII sanitisation rule."""
    if channel_type in ("gmail", "google_calendar") and "@" in value:
        local, domain = value.split("@", 1)
        masked_local = local[0] + "***" if local else "***"
        return f"{masked_local}@{domain}"
    if channel_type in ("whatsapp", "whatsapp_cloud"):
        if len(value) > 4:
            return value[:2] + "***" + value[-2:]
        return "***"
    return value


@router.get("/status", response_model=BatchConnectionStatusResponse)
async def get_all_connections_status(
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Return connection status for every channel type the tenant has."""
    repo = ChannelConnectionRepository(db)
    all_connections = repo.get_all_by_tenant(user.tenant_id)

    items: list[ConnectionStatusItem] = []
    for conn in all_connections:
        config = conn.config or {}
        display_key = _DISPLAY_NAME_KEYS.get(conn.channel_type)
        display_name = config.get(display_key) if display_key else None

        # Extract last_sync from config if stored by ETL
        last_sync = config.get("last_extraction_at") or config.get("last_sync")

        items.append(
            ConnectionStatusItem(
                channel_type=conn.channel_type,
                is_connected=conn.is_active,
                display_name=_mask_pii(str(display_name), conn.channel_type) if display_name else None,
                last_sync=str(last_sync) if last_sync else None,
            ),
        )

    return BatchConnectionStatusResponse(connections=items)
