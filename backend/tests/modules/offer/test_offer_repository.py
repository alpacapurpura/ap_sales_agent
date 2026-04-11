"""Tests for OfferRepository CRUD and domain mapping."""

import uuid

from sqlalchemy.orm import Session

from src.modules.offer.domain.enums import OfferArchetype, OfferValueLevel
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)
from src.shared.domain.datetime_utils import utc_now
from tests.modules.offer.conftest import create_product_model


class TestCreateAndRetrieveRoundtrip:
    def test_roundtrip(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(
            tenant_a,
            name="Roundtrip",
            archetype="programa",
            value_level="transformacion",
            headline_promise="Transform",
        )
        db.add(model)
        db.flush()
        result = repo.get_by_id(model.id, tenant_a)
        assert result is not None
        assert result.public_name == "Roundtrip"
        assert result.archetype == OfferArchetype.PROGRAMA


class TestListActiveExcludesArchivedAndDeleted:
    def test_list_active_only_returns_non_archived_non_deleted(
        self, db: Session, tenant_a
    ):
        repo = OfferRepository(db)
        db.add_all(
            [
                create_product_model(tenant_a, name="Active"),
                create_product_model(tenant_a, name="Archived", archived_at=utc_now()),
                create_product_model(tenant_a, name="Deleted", deleted_at=utc_now()),
            ]
        )
        db.flush()
        names = [o.public_name for o in repo.list_active(tenant_a)]
        assert names == ["Active"]

    def test_get_all_by_tenant_delegates_to_list_active(self, db: Session, tenant_a):
        """Backward-compat wrapper: get_all_by_tenant returns only active offers."""
        repo = OfferRepository(db)
        db.add_all(
            [
                create_product_model(tenant_a, name="Active"),
                create_product_model(tenant_a, name="Archived", archived_at=utc_now()),
            ]
        )
        db.flush()
        names = [o.public_name for o in repo.get_all_by_tenant(tenant_a)]
        assert "Active" in names and "Archived" not in names


class TestListArchived:
    def test_list_archived_only_returns_archived(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        db.add_all(
            [
                create_product_model(tenant_a, name="Active"),
                create_product_model(tenant_a, name="Archived1", archived_at=utc_now()),
                create_product_model(tenant_a, name="Archived2", archived_at=utc_now()),
                create_product_model(tenant_a, name="Deleted", deleted_at=utc_now()),
            ]
        )
        db.flush()
        names = {o.public_name for o in repo.list_archived(tenant_a)}
        assert names == {"Archived1", "Archived2"}

    def test_list_archived_respects_tenant_isolation(
        self, db: Session, tenant_a, tenant_b
    ):
        repo = OfferRepository(db)
        db.add_all(
            [
                create_product_model(
                    tenant_a, name="A Archived", archived_at=utc_now()
                ),
                create_product_model(
                    tenant_b, name="B Archived", archived_at=utc_now()
                ),
            ]
        )
        db.flush()
        names_a = [o.public_name for o in repo.list_archived(tenant_a)]
        assert names_a == ["A Archived"]


class TestArchiveAndRestore:
    def test_archive_sets_archived_at(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, name="ToArchive")
        db.add(model)
        db.flush()

        offer = repo.archive(model.id, tenant_a)
        assert offer is not None
        assert offer.archived_at is not None
        assert offer.is_archived is True

        # No longer visible in active list
        names = [o.public_name for o in repo.list_active(tenant_a)]
        assert "ToArchive" not in names
        # But present in archived list
        names_arch = [o.public_name for o in repo.list_archived(tenant_a)]
        assert "ToArchive" in names_arch

    def test_archive_is_idempotent(self, db: Session, tenant_a):
        """Archiving an already-archived offer does not reset the timestamp."""
        repo = OfferRepository(db)
        model = create_product_model(tenant_a)
        db.add(model)
        db.flush()

        first = repo.archive(model.id, tenant_a)
        second = repo.archive(model.id, tenant_a)
        assert first.archived_at == second.archived_at

    def test_restore_clears_archived_at(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, name="Restorable", archived_at=utc_now())
        db.add(model)
        db.flush()

        restored = repo.restore(model.id, tenant_a)
        assert restored is not None
        assert restored.archived_at is None
        assert restored.is_archived is False

        names = [o.public_name for o in repo.list_active(tenant_a)]
        assert "Restorable" in names

    def test_archive_tenant_isolation(self, db: Session, tenant_a, tenant_b):
        repo = OfferRepository(db)
        model = create_product_model(tenant_b, name="TenantB")
        db.add(model)
        db.flush()

        # tenant_a cannot archive tenant_b's offer
        result = repo.archive(model.id, tenant_a)
        assert result is None

    def test_archive_missing_offer_returns_none(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        assert repo.archive(uuid.uuid4(), tenant_a) is None


class TestSoftDelete:
    def test_soft_delete_sets_deleted_at_and_hides_everywhere(
        self, db: Session, tenant_a
    ):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, name="ToDelete", archived_at=utc_now())
        db.add(model)
        db.flush()

        assert repo.soft_delete(model.id, tenant_a) is True

        # Not visible in active or archived lists
        assert "ToDelete" not in [o.public_name for o in repo.list_active(tenant_a)]
        assert "ToDelete" not in [o.public_name for o in repo.list_archived(tenant_a)]

        # Default get_by_id hides soft-deleted rows
        assert repo.get_by_id(model.id, tenant_a) is None

    def test_soft_delete_tenant_isolation(self, db: Session, tenant_a, tenant_b):
        repo = OfferRepository(db)
        model = create_product_model(tenant_b, name="TenantB", archived_at=utc_now())
        db.add(model)
        db.flush()

        assert repo.soft_delete(model.id, tenant_a) is False
        # Still visible for tenant_b (include_archived because it is archived)
        assert repo.get_by_id(model.id, tenant_b, include_archived=True) is not None


class TestGetByIdIncludeArchived:
    def test_get_by_id_hides_archived_by_default(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, archived_at=utc_now())
        db.add(model)
        db.flush()

        assert repo.get_by_id(model.id, tenant_a) is None

    def test_get_by_id_include_archived_returns_archived(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, archived_at=utc_now())
        db.add(model)
        db.flush()

        result = repo.get_by_id(model.id, tenant_a, include_archived=True)
        assert result is not None
        assert result.is_archived is True

    def test_get_by_id_include_deleted_returns_deleted(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, deleted_at=utc_now())
        db.add(model)
        db.flush()

        result = repo.get_by_id(
            model.id, tenant_a, include_archived=True, include_deleted=True
        )
        assert result is not None
        assert result.is_deleted is True


class TestUpdatePersistsChanges:
    def test_update(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a)
        db.add(model)
        db.flush()
        offer = repo.get_by_id(model.id, tenant_a)
        offer.headline_promise = "Updated"
        updated = repo.update(offer, tenant_a)
        assert updated.headline_promise == "Updated"

    def test_update_preserves_archived_at(self, db: Session, tenant_a):
        """Generic update() must not clobber lifecycle columns."""
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, archived_at=utc_now())
        db.add(model)
        db.flush()

        offer = repo.get_by_id(model.id, tenant_a, include_archived=True)
        assert offer.archived_at is not None
        offer.headline_promise = "Updated"
        updated = repo.update(offer, tenant_a)
        assert updated.archived_at is not None
        assert updated.is_archived is True


class TestToDomainNormalization:
    def test_uppercase_value_level(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, value_level="ACTIVACION")
        db.add(model)
        db.flush()
        assert (
            repo.get_by_id(model.id, tenant_a).value_level == OfferValueLevel.ACTIVACION
        )

    def test_legacy_guarantee(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(tenant_a, guarantee_type="NO_REFUNDS")
        db.add(model)
        db.flush()
        assert repo.get_by_id(model.id, tenant_a).guarantee_type == "none"

    def test_legacy_pricing(self, db: Session, tenant_a):
        repo = OfferRepository(db)
        model = create_product_model(
            tenant_a,
            pricing=[{"plan_type": "PAY_IN_FULL", "label": "x", "total_amount": 997}],
        )
        db.add(model)
        db.flush()
        assert (
            repo.get_by_id(model.id, tenant_a).pricing_options[0].plan_type
            == "one_time"
        )
