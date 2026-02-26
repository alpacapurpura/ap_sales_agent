from typing import List, Optional
from sqlalchemy.orm import Session
from uuid import UUID

from src.modules.brand.domain import Avatar
from src.modules.brand.infrastructure.models.avatar_model import AvatarModel

class AvatarRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_tenant(self, tenant_id: UUID) -> List[Avatar]:
        models = self.db.query(AvatarModel).filter(AvatarModel.tenant_id == tenant_id).all()
        return [Avatar.model_validate(m) for m in models]

    def get_by_id(self, avatar_id: UUID) -> Optional[Avatar]:
        model = self.db.query(AvatarModel).filter(AvatarModel.id == avatar_id).first()
        if model:
            return Avatar.model_validate(model)
        return None

    def create(self, avatar: Avatar) -> Avatar:
        db_avatar = AvatarModel(
            id=avatar.id,
            tenant_id=avatar.tenant_id,
            user_id=avatar.user_id,
            name=avatar.name,
            scope=avatar.scope,
            icp_description=avatar.icp_description,
            anti_avatar=avatar.anti_avatar,
            voice_tone_config=avatar.voice_tone_config,
            is_default=avatar.is_default
        )
        self.db.add(db_avatar)
        self.db.commit()
        self.db.refresh(db_avatar)
        return Avatar.model_validate(db_avatar)
