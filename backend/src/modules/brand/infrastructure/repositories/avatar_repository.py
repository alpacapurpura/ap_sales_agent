"""Brand avatar repository."""

from uuid import UUID

from luana_core_brand_studio.domain import Avatar
from luana_core_brand_studio.infrastructure.models.avatar_model import AvatarModel
from luana_core_platform.domain.datetime_utils import utc_now
from sqlalchemy import select, update
from sqlalchemy.orm import Session


class AvatarRepository:
    """Repository for avatar persistence."""

    def __init__(self, db: Session) -> None:
        """Initialize avatar repository."""
        self.db = db

    def get_by_tenant(self, tenant_id: UUID, scope: str | None = None) -> list[Avatar]:
        """Return by tenant."""
        stmt = select(AvatarModel).where(
            AvatarModel.tenant_id == tenant_id,
            AvatarModel.deleted_at.is_(None),
        )
        if scope:
            stmt = stmt.where(AvatarModel.scope == scope)
        result = self.db.execute(stmt)
        models = result.scalars().all()
        return [Avatar.model_validate(m) for m in models]

    def get_by_id(self, avatar_id: UUID, tenant_id: UUID) -> Avatar | None:
        """Return by id."""
        stmt = select(AvatarModel).where(
            AvatarModel.id == avatar_id,
            AvatarModel.tenant_id == tenant_id,
            AvatarModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalars().first()
        if model:
            return Avatar.model_validate(model)
        return None

    def create(self, avatar: Avatar) -> Avatar:
        """Execute create operation."""
        db_avatar = AvatarModel(
            id=avatar.id,
            tenant_id=avatar.tenant_id,
            user_id=avatar.user_id,
            name=avatar.name,
            scope=avatar.scope,
            icp_description=avatar.icp_description,
            anti_avatar=avatar.anti_avatar,
            voice_tone_config=avatar.voice_tone_config,
            is_default=avatar.is_default,
        )
        self.db.add(db_avatar)
        self.db.commit()
        self.db.refresh(db_avatar)
        return Avatar.model_validate(db_avatar)

    def update(self, avatar_id: UUID, data: dict) -> Avatar | None:
        """Execute update operation."""
        stmt = select(AvatarModel).where(
            AvatarModel.id == avatar_id,
            AvatarModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalars().first()
        if not model:
            return None

        for key, value in data.items():
            # Only update if value is provided (not None) and field exists
            if hasattr(model, key) and value is not None:
                setattr(model, key, value)

        self.db.commit()
        self.db.refresh(model)
        return Avatar.model_validate(model)

    def delete(self, avatar_id: UUID) -> bool:
        """Execute delete operation."""
        stmt = select(AvatarModel).where(
            AvatarModel.id == avatar_id,
            AvatarModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt)
        model = result.scalars().first()
        if not model:
            return False

        model.deleted_at = utc_now()
        self.db.flush()
        self.db.commit()
        return True

    def set_global_default(self, tenant_id: UUID, avatar_id: UUID) -> Avatar | None:
        """Set global default."""
        # Unset all defaults for this tenant using SA 2.0 update()
        stmt_unset = (
            update(AvatarModel)
            .where(
                AvatarModel.tenant_id == tenant_id,
                AvatarModel.is_default.is_(True),
                AvatarModel.deleted_at.is_(None),
            )
            .values(is_default=False)
        )
        self.db.execute(stmt_unset)

        # Set the new default
        stmt_get = select(AvatarModel).where(
            AvatarModel.id == avatar_id,
            AvatarModel.deleted_at.is_(None),
        )
        result = self.db.execute(stmt_get)
        model = result.scalars().first()
        if not model:
            self.db.rollback()
            return None

        model.is_default = True
        self.db.commit()
        self.db.refresh(model)
        return Avatar.model_validate(model)
