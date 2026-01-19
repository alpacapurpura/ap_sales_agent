from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from src.services.db.models.business import AvatarDefinition
from .base import BaseRepository
import uuid

class AvatarRepository(BaseRepository):
    def get_by_id(self, avatar_id: str | uuid.UUID) -> Optional[AvatarDefinition]:
        if isinstance(avatar_id, str):
            try:
                avatar_id = uuid.UUID(avatar_id)
            except ValueError:
                return None
        return self.db.query(AvatarDefinition).filter(AvatarDefinition.id == avatar_id).first()
    
    def list_avatars(self, scope: str = "GLOBAL") -> List[AvatarDefinition]:
        """List avatars by scope. Default is GLOBAL which are the reusable ones."""
        query = self.db.query(AvatarDefinition)
        if scope:
            query = query.filter(AvatarDefinition.scope == scope)
        return query.order_by(AvatarDefinition.is_default.desc(), AvatarDefinition.name).all()

    def create_avatar(self, name: str, scope: str = "GLOBAL", icp_description: str = "", anti_avatar: str = "", voice_tone_config: Dict = {}) -> AvatarDefinition:
        avatar = AvatarDefinition(
            name=name,
            scope=scope,
            icp_description=icp_description,
            anti_avatar=anti_avatar,
            voice_tone_config=voice_tone_config,
            is_default=False
        )
        self.db.add(avatar)
        self.db.commit()
        self.db.refresh(avatar)
        return avatar

    def update_avatar(self, avatar_id: str | uuid.UUID, update_data: Dict[str, Any]) -> Optional[AvatarDefinition]:
        avatar = self.get_by_id(avatar_id)
        if not avatar:
            return None

        # Direct fields
        for field in ["name", "icp_description", "anti_avatar", "scope"]:
            if field in update_data:
                setattr(avatar, field, update_data[field])

        # JSONB fields
        if "voice_tone_config" in update_data:
            current_voice = dict(avatar.voice_tone_config) if avatar.voice_tone_config else {}
            current_voice.update(update_data["voice_tone_config"])
            avatar.voice_tone_config = current_voice

        self.db.commit()
        self.db.refresh(avatar)
        return avatar
    
    def delete_avatar(self, avatar_id: str | uuid.UUID) -> bool:
        avatar = self.get_by_id(avatar_id)
        if not avatar:
            return False
        self.db.delete(avatar)
        self.db.commit()
        return True

    def set_default(self, avatar_id: str | uuid.UUID) -> Optional[AvatarDefinition]:
        avatar = self.get_by_id(avatar_id)
        if not avatar:
            return None
            
        # Unset all others
        self.db.query(AvatarDefinition).filter(
            AvatarDefinition.scope == "GLOBAL",
            AvatarDefinition.is_default == True
        ).update({"is_default": False})
        
        # Set this one
        avatar.is_default = True
        
        self.db.commit()
        self.db.refresh(avatar)
        return avatar
