from typing import Optional
from sqlalchemy import desc
from src.services.db.models.user import User
from src.services.db.models.business import Enrollment, Product
from src.services.db.models.observability import Message
from .base import BaseRepository
import uuid

class UserRepository(BaseRepository):
    def get_by_id(self, user_id: str | uuid.UUID) -> Optional[User]:
        """
        Robustly fetch user by ID, handling string/UUID conversion.
        """
        if isinstance(user_id, str):
            try:
                # Validate and convert UUID
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None
                
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_channel_id(self, channel: str, user_id: str) -> Optional[User]:
        if channel == "telegram":
            return self.db.query(User).filter(User.telegram_id == user_id).first()
        elif channel == "whatsapp":
            return self.db.query(User).filter(User.whatsapp_id == user_id).first()
        elif channel == "instagram":
            return self.db.query(User).filter(User.instagram_id == user_id).first()
        elif channel == "tiktok":
            return self.db.query(User).filter(User.tiktok_id == user_id).first()
        return None

    def create_user(self, full_name: str, channel: str, channel_user_id: str) -> User:
        user = User(full_name=full_name)
        if channel == "telegram":
            user.telegram_id = channel_user_id
        elif channel == "whatsapp":
            user.whatsapp_id = channel_user_id
        elif channel == "instagram":
            user.instagram_id = channel_user_id
        elif channel == "tiktok":
            user.tiktok_id = channel_user_id
            
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_profile(self, user_id, psychographics_update: dict) -> Optional[User]:
        user = self.get_by_id(user_id)
        if user:
            current = dict(user.profile_data) if user.profile_data else {}
            
            # Smart merge for lists
            for k, v in psychographics_update.items():
                if isinstance(v, list) and k in current and isinstance(current[k], list):
                    current[k] = list(set(current[k] + v))
                else:
                    current[k] = v
                    
            user.profile_data = current
            
            if "email" in psychographics_update and psychographics_update["email"]:
                user.email = psychographics_update["email"]
            if "phone" in psychographics_update and psychographics_update["phone"]:
                user.phone = psychographics_update["phone"]
                
            self.db.commit()
            self.db.refresh(user)
        return user
