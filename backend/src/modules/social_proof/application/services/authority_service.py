"""AuthorityItem service — orchestrates persistence and event publishing."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from luana_core_platform.domain.events import EventBus
from luana_core_social_proof.domain.authority_item import AuthorityItem
from luana_core_social_proof.domain.events import (
    AuthorityItemCreated,
    AuthorityItemSoftDeleted,
    AuthorityItemUpdated,
)
from luana_core_social_proof.infrastructure.repositories.authority_item_repository import (
    AuthorityItemRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from luana_core_social_proof.domain.enums import AuthorityType
    from sqlalchemy.orm import Session


class AuthorityService:
    """Application service for AuthorityItem CRUD with event publishing."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db
        self.repo = AuthorityItemRepository(db)

    def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        entity_name: str,
        authority_type: AuthorityType,
        **fields: object,
    ) -> AuthorityItem:
        """Create an AuthorityItem and emit ``authority_item_created``."""
        entity = AuthorityItem(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            entity_name=entity_name,
            authority_type=authority_type,
            **fields,  # type: ignore[arg-type]
        )
        created = self.repo.create(entity)
        EventBus.publish(
            AuthorityItemCreated.create(
                tenant_id=tenant_id,
                authority_item_id=created.id,
            ),
            session=self.db,
        )
        return created

    def update(
        self,
        tenant_id: UUID,
        item_id: UUID,
        updates: dict,
    ) -> AuthorityItem | None:
        """Patch an AuthorityItem and emit ``authority_item_updated``."""
        result = self.repo.update(tenant_id, item_id, updates)
        if result is not None:
            EventBus.publish(
                AuthorityItemUpdated.create(
                    tenant_id=tenant_id,
                    authority_item_id=item_id,
                    changed_fields=list(updates.keys()),
                ),
                session=self.db,
            )
        return result

    def soft_delete(self, tenant_id: UUID, item_id: UUID) -> bool:
        """Soft-delete an AuthorityItem, cascade placements, emit event."""
        from luana_core_social_proof.domain.enums import SourceTable
        from luana_core_social_proof.infrastructure.repositories.placement_repository import (
            PlacementRepository,
        )

        ok = self.repo.soft_delete(tenant_id, item_id)
        if ok:
            PlacementRepository(self.db).cascade_soft_delete_for_source(
                tenant_id,
                SourceTable.AUTHORITY_ITEM,
                item_id,
            )
            EventBus.publish(
                AuthorityItemSoftDeleted.create(
                    tenant_id=tenant_id,
                    authority_item_id=item_id,
                ),
                session=self.db,
            )
        return ok

    def get(self, tenant_id: UUID, item_id: UUID) -> AuthorityItem | None:
        """Return a single AuthorityItem by id."""
        return self.repo.get_by_id(tenant_id, item_id)

    def list_tenant(self, tenant_id: UUID) -> list[AuthorityItem]:
        """List all authority items for a tenant."""
        return self.repo.list_by_tenant(tenant_id)

    def clone(
        self,
        tenant_id: UUID,
        source_id: UUID,
        user_id: UUID,
    ) -> AuthorityItem | None:
        """Clone an existing AuthorityItem for targeted customization."""
        original = self.repo.get_by_id(tenant_id, source_id)
        if original is None:
            return None
        data = original.model_dump(
            exclude={"id", "tenant_id", "created_at", "updated_at", "deleted_at", "user_id"},
        )
        return self.create(tenant_id=tenant_id, user_id=user_id, **data)
