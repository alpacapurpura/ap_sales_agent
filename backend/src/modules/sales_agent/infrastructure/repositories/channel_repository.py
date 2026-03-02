from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID
from src.modules.connections.domain.channel import ChannelConnection
from src.modules.connections.domain.enums import ChannelType
from src.modules.sales_agent.infrastructure.models.channel_model import ChannelConnectionModel

class ChannelRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: ChannelConnectionModel) -> ChannelConnection:
        return ChannelConnection(
            id=model.id,
            tenant_id=model.tenant_id,
            channel_type=ChannelType(model.channel_type),
            credentials=model.credentials or {},
            config=model.config or {},
            is_active=model.is_active,
            created_at=model.created_at,
            updated_at=model.updated_at
        )

    def _to_model(self, channel: ChannelConnection) -> ChannelConnectionModel:
        return ChannelConnectionModel(
            id=channel.id,
            tenant_id=channel.tenant_id,
            channel_type=channel.channel_type.value,
            credentials=channel.credentials,
            config=channel.config,
            is_active=channel.is_active
        )

    def get_active_connection(self, tenant_id: UUID, channel_type: ChannelType) -> Optional[ChannelConnection]:
        model = self.db.query(ChannelConnectionModel).filter(
            ChannelConnectionModel.tenant_id == tenant_id,
            ChannelConnectionModel.channel_type == channel_type.value,
            ChannelConnectionModel.is_active == True
        ).first()
        if model:
            return self._to_domain(model)
        return None

    def create(self, channel: ChannelConnection) -> ChannelConnection:
        model = self._to_model(channel)
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)
