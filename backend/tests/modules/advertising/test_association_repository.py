"""Tests for AssociationRepository."""

from __future__ import annotations

from typing import TYPE_CHECKING

from src.modules.advertising.domain.enums import (
    AssociationTargetType,
    AssociationType,
)
from src.modules.advertising.infrastructure.repositories.association_repository import (
    AssociationRepository,
)

if TYPE_CHECKING:
    from uuid import UUID


class TestAssociationRepository:
    def test_create_manual_association(self, db, tenant_id: UUID, offer_id: UUID):
        repo = AssociationRepository(db)
        row = repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="1111",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        assert row.id is not None
        assert row.tenant_id == tenant_id
        assert row.offer_id == offer_id
        assert row.association_type == "manual"
        assert row.deleted_at is None

    def test_create_soft_deletes_previous_active(
        self, db, tenant_id: UUID, offer_id: UUID
    ):
        repo = AssociationRepository(db)
        first = repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="1111",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        second = repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="1111",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        # Reload first from DB to verify soft-delete.
        reloaded = repo.get_by_id(tenant_id, first.id)
        assert reloaded is not None
        assert reloaded.deleted_at is not None
        # The newer row is the active one.
        active = repo.get_active_by_target(
            tenant_id, AssociationTargetType.CAMPAIGN, "1111"
        )
        assert active is not None
        assert active.id == second.id

    def test_list_active_excludes_soft_deleted(
        self, db, tenant_id: UUID, offer_id: UUID
    ):
        repo = AssociationRepository(db)
        a = repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="1111",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        repo.soft_delete(tenant_id, a.id)
        assert repo.list_active(tenant_id) == []

    def test_list_active_filters_by_target_type(
        self, db, tenant_id: UUID, offer_id: UUID
    ):
        repo = AssociationRepository(db)
        repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="1111",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.AD_SET,
            target_external_id="2222",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        assert (
            len(repo.list_active(tenant_id, target_type=AssociationTargetType.CAMPAIGN))
            == 1
        )
        assert (
            len(repo.list_active(tenant_id, target_type=AssociationTargetType.AD_SET))
            == 1
        )

    def test_tenant_isolation(
        self, db, tenant_id: UUID, other_tenant_id: UUID, offer_id: UUID
    ):
        repo = AssociationRepository(db)
        repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="1111",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        assert repo.list_active(other_tenant_id) == []
        assert repo.list_active(tenant_id) != []

    def test_excluded_branding_allows_null_offer(self, db, tenant_id: UUID):
        repo = AssociationRepository(db)
        row = repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="BRAND1",
            offer_id=None,
            association_type=AssociationType.EXCLUDED_BRANDING,
            notes="Branding-only campaign",
        )
        assert row.offer_id is None
        assert row.association_type == "excluded_branding"

    def test_soft_delete_returns_false_when_not_found(self, db, tenant_id: UUID):
        repo = AssociationRepository(db)
        import uuid

        assert not repo.soft_delete(tenant_id, uuid.uuid4())

    def test_get_by_id_scoped_to_tenant(
        self, db, tenant_id: UUID, other_tenant_id: UUID, offer_id: UUID
    ):
        repo = AssociationRepository(db)
        row = repo.create(
            tenant_id=tenant_id,
            target_type=AssociationTargetType.CAMPAIGN,
            target_external_id="1111",
            offer_id=offer_id,
            association_type=AssociationType.MANUAL,
        )
        # Same ID, wrong tenant → None.
        assert repo.get_by_id(other_tenant_id, row.id) is None
        assert repo.get_by_id(tenant_id, row.id) is not None
