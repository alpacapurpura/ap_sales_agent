from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.connections.domain.channel import ChannelConnection
from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository as ChannelRepository,
)
from src.shared.domain.enums import ChannelType


class ChannelService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repository = ChannelRepository(db)

    def get_active_channel(
        self,
        tenant_id: UUID,
        channel_type: ChannelType,
    ) -> ChannelConnection | None:
        return self.repository.get_active_connection(tenant_id, channel_type)

    def register_channel(
        self,
        tenant_id: UUID,
        channel_type: ChannelType,
        credentials: dict,
        config: dict | None = None,
    ) -> ChannelConnection:
        import uuid

        # Check if exists and update or create new? For now simple create
        # In real app, we might want to deactivate old one or update it.
        new_channel = ChannelConnection(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            channel_type=channel_type,
            credentials=credentials,
            config=config or {},
            is_active=True,
        )
        return self.repository.create(new_channel)
