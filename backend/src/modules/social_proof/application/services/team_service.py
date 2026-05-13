"""TeamMember service — orchestrates persistence and event publishing."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from luana_core_platform.domain.events import EventBus
from luana_core_social_proof.domain.events import (
    TeamMemberCreated,
    TeamMemberSoftDeleted,
    TeamMemberUpdated,
)
from luana_core_social_proof.domain.team_member import TeamMember
from luana_core_social_proof.infrastructure.repositories.team_member_repository import (
    TeamMemberRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class TeamService:
    """Application service for TeamMember CRUD with event publishing."""

    def __init__(self, db: Session) -> None:
        """Store the database session for subsequent queries."""
        self.db = db
        self.repo = TeamMemberRepository(db)

    def create(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        name: str,
        **fields: object,
    ) -> TeamMember:
        """Create a TeamMember and emit ``team_member_created``."""
        entity = TeamMember(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            name=name,
            **fields,  # type: ignore[arg-type]
        )
        created = self.repo.create(entity)
        EventBus.publish(
            TeamMemberCreated.create(
                tenant_id=tenant_id,
                team_member_id=created.id,
            ),
            session=self.db,
        )
        return created

    def update(
        self,
        tenant_id: UUID,
        member_id: UUID,
        updates: dict,
    ) -> TeamMember | None:
        """Patch a TeamMember and emit ``team_member_updated``."""
        result = self.repo.update(tenant_id, member_id, updates)
        if result is not None:
            EventBus.publish(
                TeamMemberUpdated.create(
                    tenant_id=tenant_id,
                    team_member_id=member_id,
                    changed_fields=list(updates.keys()),
                ),
                session=self.db,
            )
        return result

    def soft_delete(self, tenant_id: UUID, member_id: UUID) -> bool:
        """Soft-delete a TeamMember, cascade placements, emit event."""
        from luana_core_social_proof.domain.enums import SourceTable
        from luana_core_social_proof.infrastructure.repositories.placement_repository import (
            PlacementRepository,
        )

        ok = self.repo.soft_delete(tenant_id, member_id)
        if ok:
            PlacementRepository(self.db).cascade_soft_delete_for_source(
                tenant_id,
                SourceTable.TEAM_MEMBER,
                member_id,
            )
            EventBus.publish(
                TeamMemberSoftDeleted.create(
                    tenant_id=tenant_id,
                    team_member_id=member_id,
                ),
                session=self.db,
            )
        return ok

    def get(self, tenant_id: UUID, member_id: UUID) -> TeamMember | None:
        """Return a single TeamMember by id."""
        return self.repo.get_by_id(tenant_id, member_id)

    def list_tenant(self, tenant_id: UUID) -> list[TeamMember]:
        """List all team members for a tenant ordered by sort_order."""
        return self.repo.list_by_tenant(tenant_id)

    def clone(
        self,
        tenant_id: UUID,
        source_id: UUID,
        user_id: UUID,
    ) -> TeamMember | None:
        """Clone an existing TeamMember for targeted customization."""
        original = self.repo.get_by_id(tenant_id, source_id)
        if original is None:
            return None
        data = original.model_dump(
            exclude={"id", "tenant_id", "created_at", "updated_at", "deleted_at", "user_id"},
        )
        # Clones are never the primary voice — the original keeps that title.
        data["is_primary_voice"] = False
        return self.create(tenant_id=tenant_id, user_id=user_id, **data)
