"""Resolves the correct channel adapter + user_id for outbound messages to a lead."""

from __future__ import annotations

from typing import TYPE_CHECKING

import structlog
from sqlalchemy import select

from src.modules.connections.infrastructure.models.channel_connection_model import (
    ChannelConnectionModel,
)
from src.shared.domain.enums import ChannelType
from src.shared.domain.messages import OutgoingMessage

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.crm.infrastructure.models.lead_model import LeadModel
    from src.shared.infrastructure.channels.base import BaseChannel

logger = structlog.get_logger()

# Map channel_type string → (ChannelType enum, lead field for user_id)
_CHANNEL_MAP = {
    "telegram": (ChannelType.TELEGRAM, "telegram_id"),
    "whatsapp": (ChannelType.WHATSAPP, "whatsapp_id"),
    "instagram": (ChannelType.META, "instagram_id"),
}


class ChannelResolver:
    """Resolves and instantiates the channel adapter for outbound messaging."""

    def __init__(self, db: Session) -> None:
        self.db = db

    def resolve(
        self,
        tenant_id: UUID,
        lead: LeadModel,
        preferred_channel: str | None = None,
    ) -> tuple[BaseChannel, str] | None:
        """
        Return (adapter, channel_user_id) for the lead's channel.

        Priority: preferred_channel > checkpoint channel > first available.
        """
        channels_to_try = []

        if preferred_channel and preferred_channel in _CHANNEL_MAP:
            channels_to_try.append(preferred_channel)

        # Add all channels the lead has IDs for
        for ch_type, (_, id_field) in _CHANNEL_MAP.items():
            if ch_type not in channels_to_try and getattr(lead, id_field, None):
                channels_to_try.append(ch_type)

        for ch_type in channels_to_try:
            result = self._try_channel(tenant_id, lead, ch_type)
            if result:
                return result

        logger.warning(
            "no_channel_resolved",
            lead_id=str(lead.id),
            tenant_id=str(tenant_id),
        )
        return None

    def _try_channel(
        self,
        tenant_id: UUID,
        lead: LeadModel,
        ch_type: str,
    ) -> tuple[BaseChannel, str] | None:
        enum_type, id_field = _CHANNEL_MAP[ch_type]
        user_id = getattr(lead, id_field, None)
        if not user_id:
            return None

        # Get connection credentials
        conn = (
            self.db.execute(
                select(ChannelConnectionModel).where(
                    ChannelConnectionModel.tenant_id == tenant_id,
                    ChannelConnectionModel.channel_type == enum_type.value,
                    ChannelConnectionModel.is_active.is_(True),
                ),
            )
            .scalars()
            .first()
        )
        if not conn:
            return None

        adapter = self._create_adapter(ch_type, conn, tenant_id)
        if adapter:
            return adapter, user_id
        return None

    def _create_adapter(
        self,
        ch_type: str,
        conn: ChannelConnectionModel,
        tenant_id: UUID,
    ) -> BaseChannel | None:
        try:
            if ch_type == "telegram":
                from src.modules.connections.infrastructure.channels.telegram import (
                    TelegramChannel,
                )

                token = conn.credentials.get("token") if conn.credentials else None
                return TelegramChannel(token=token)

            if ch_type == "whatsapp":
                from src.modules.connections.infrastructure.channels.whatsapp import (
                    WhatsAppChannel,
                )

                return WhatsAppChannel(tenant_id=str(tenant_id))

            if ch_type == "instagram":
                from src.modules.connections.infrastructure.channels.instagram import (
                    InstagramChannel,
                )

                return InstagramChannel(
                    client_config=conn.config or {},
                    credentials_data=conn.credentials or {},
                )
        except Exception as e:
            logger.exception(
                "channel_adapter_creation_failed",
                ch_type=ch_type,
                error=str(e),
            )
        return None

    async def send_to_lead(
        self,
        tenant_id: UUID,
        lead: LeadModel,
        text: str,
        preferred_channel: str | None = None,
    ) -> bool:
        """Convenience: resolve channel and send message in one call."""
        resolved = self.resolve(tenant_id, lead, preferred_channel)
        if not resolved:
            return False

        adapter, user_id = resolved
        try:
            msg = OutgoingMessage(user_id=user_id, text=text)
            await adapter.send_message(msg)
        except Exception as e:
            logger.exception("send_to_lead_failed", lead_id=str(lead.id), error=str(e))
            return False
        else:
            return True
