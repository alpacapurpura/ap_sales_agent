"""Payment connection port — lazy-import facade over connections module.

Provides payment-channel queries without coupling ``sales_agent`` directly to
``connections`` infrastructure.  Mirror of ``calendar.py`` for payment context.

Lazy imports inside function bodies ensure the coupling is confined to
``shared/`` (not scanned by the sales_agent → connections arch ratchet).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


def get_payment_connection_provider(db: Session, tenant_id: UUID) -> str | None:
    """Return the active payment provider_id for a tenant, or None."""
    from sqlalchemy import select

    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    row = db.execute(
        select(ChannelConnectionModel).where(
            ChannelConnectionModel.tenant_id == tenant_id,
            ChannelConnectionModel.channel_type == "payment",
            ChannelConnectionModel.is_active.is_(True),
        )
    ).scalar_one_or_none()
    return str(row.provider) if row else None


def get_payment_webhook_secret(
    db: Session,
    tenant_id: UUID,
    provider_id: str,
) -> str:
    """Return the webhook signing secret for a tenant's payment connection.

    Returns ``""`` if no connection or no secret configured.
    """
    from sqlalchemy import select

    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    row = db.execute(
        select(ChannelConnectionModel).where(
            ChannelConnectionModel.tenant_id == tenant_id,
            ChannelConnectionModel.channel_type == "payment",
            ChannelConnectionModel.provider == provider_id,
            ChannelConnectionModel.is_active.is_(True),
        )
    ).scalar_one_or_none()
    if row is None:
        return ""
    return str((row.config or {}).get("webhook_secret", ""))
