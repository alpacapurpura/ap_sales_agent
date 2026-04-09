"""Tests for LaunchEditionRepository CRUD operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.modules.offer.domain.launch_edition import EditionStatus
from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from tests.modules.offer.conftest import create_product_model


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    """Helper: create a product and return its id."""
    model = create_product_model(tenant_id, archetype="programa")
    db.add(model)
    db.flush()
    return model.id


class TestCreate:
    def test_create_and_auto_number(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)

        edition = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Cohorte #1",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.id is not None
        assert edition.edition_number == 1
        assert edition.edition_name == "Cohorte #1"
        assert edition.status == EditionStatus.DRAFT

    def test_auto_increment_number(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)

        e1 = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        e2 = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 10, 7, tzinfo=timezone.utc),
        )
        assert e1.edition_number == 1
        assert e2.edition_number == 2

    def test_auto_name_when_none(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)

        edition = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.edition_name == "Edición #1"


class TestGetById:
    def test_found(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        created = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Test",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        found = repo.get_by_id(created.id, tenant_a)
        assert found is not None
        assert found.edition_name == "Test"

    def test_wrong_tenant_returns_none(self, db: Session, tenant_a, tenant_b):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        created = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Test",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert repo.get_by_id(created.id, tenant_b) is None


class TestListByOffer:
    def test_ordered_by_start_date_desc(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Jan",
            start_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Jul",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        editions = repo.list_by_offer(offer_id, tenant_a)
        assert len(editions) == 2
        assert editions[0].edition_name == "Jul"  # newest first

    def test_excludes_cancelled(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        e1 = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        # Cancel first one
        repo.update(e1.id, tenant_a, {"status": "cancelled"})
        editions = repo.list_by_offer(offer_id, tenant_a)
        assert len(editions) == 1


class TestUpdate:
    def test_patch_fields(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        created = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Old Name",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        updated = repo.update(
            created.id,
            tenant_a,
            {
                "edition_name": "New Name",
                "capacity": 50,
                "status": "upcoming",
            },
        )
        assert updated.edition_name == "New Name"
        assert updated.capacity == 50
        assert updated.status == EditionStatus.UPCOMING


class TestSoftDelete:
    def test_delete_sets_cancelled(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        created = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        repo.soft_delete(created.id, tenant_a)
        edition = repo.get_by_id(created.id, tenant_a)
        assert edition is not None
        assert edition.status == EditionStatus.CANCELLED


class TestGetNextEditionNumber:
    def test_first_edition(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        assert repo.get_next_edition_number(offer_id) == 1

    def test_after_three_editions(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        for _ in range(3):
            repo.create(
                offer_id=offer_id,
                tenant_id=tenant_a,
                start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            )
        assert repo.get_next_edition_number(offer_id) == 4
