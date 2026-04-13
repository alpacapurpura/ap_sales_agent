import uuid

from sqlalchemy import select

from src.core.base_repository import BaseRepository
from src.modules.iam.domain.user import User
from src.modules.iam.infrastructure.models import UserModel


class UserRepository(BaseRepository):
    def get_by_id(self, user_id: str | uuid.UUID) -> User | None:
        """
        Fetch user by ID using UserModel (ORM) and return User (Domain).
        """
        if isinstance(user_id, str):
            try:
                user_id = uuid.UUID(user_id)
            except ValueError:
                return None

        user_orm = (
            self.db.execute(select(UserModel).where(UserModel.id == user_id))
            .scalars()
            .first()
        )
        if user_orm:
            return User.model_validate(user_orm)
        return None

    def get_by_email(self, email: str) -> User | None:
        """
        Fetch user by email.
        """
        user_orm = (
            self.db.execute(select(UserModel).where(UserModel.email == email))
            .scalars()
            .first()
        )
        if user_orm:
            return User.model_validate(user_orm)
        return None

    def get_by_clerk_id(self, clerk_id: str) -> User | None:
        """
        Fetch user by Clerk ID.
        """
        user_orm = (
            self.db.execute(select(UserModel).where(UserModel.clerk_id == clerk_id))
            .scalars()
            .first()
        )
        if user_orm:
            return User.model_validate(user_orm)
        return None

    def create_user(self, user: User) -> User:
        """
        Create a new user from Domain Model.
        """
        # Convert Domain -> ORM
        user_orm = UserModel(
            id=user.id,
            full_name=user.full_name,
            email=user.email,
            phone=user.phone,
            clerk_id=user.clerk_id,
            role=user.role,
            is_active=user.is_active,
            # tenant_id logic is handled via M2M relationship usually, or context
        )

        self.db.add(user_orm)
        self.db.commit()
        self.db.refresh(user_orm)

        return User.model_validate(user_orm)

    def update_user(self, user: User) -> User:
        """
        Update existing user from Domain Model.
        """
        user_orm = (
            self.db.execute(select(UserModel).where(UserModel.id == user.id))
            .scalars()
            .first()
        )
        if not user_orm:
            msg = f"User {user.id} not found"
            raise ValueError(msg)

        # Update fields
        user_orm.full_name = user.full_name
        user_orm.email = user.email
        user_orm.phone = user.phone
        user_orm.clerk_id = user.clerk_id
        user_orm.role = user.role
        user_orm.is_active = user.is_active

        self.db.commit()
        self.db.refresh(user_orm)

        return User.model_validate(user_orm)
