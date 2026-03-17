from typing import Optional
from sqlalchemy.orm import Session
from uuid import UUID

from src.modules.iam.domain.user import User
from src.modules.iam.infrastructure.models.user_model import UserModel

class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: UUID) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.id == user_id).first()
        if model:
            return User.model_validate(model)
        return None

    def get_by_email(self, email: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.email == email).first()
        if model:
            return User.model_validate(model)
        return None

    def get_by_clerk_id(self, clerk_id: str) -> Optional[User]:
        model = self.db.query(UserModel).filter(UserModel.clerk_id == clerk_id).first()
        if model:
            return User.model_validate(model)
        return None
    
    def create(self, user: User) -> User:
        db_user = UserModel(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            clerk_id=user.clerk_id,
            role=user.role,
            is_active=user.is_active
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return User.model_validate(db_user)

    def update(self, user: User) -> User:
        db_user = self.db.query(UserModel).filter(UserModel.id == user.id).first()
        if db_user:
            db_user.full_name = user.full_name
            db_user.email = user.email
            db_user.phone = user.phone
            db_user.clerk_id = user.clerk_id
            db_user.role = user.role
            db_user.is_active = user.is_active
            self.db.commit()
            self.db.refresh(db_user)
            return User.model_validate(db_user)
        return user # Or raise NotFound
