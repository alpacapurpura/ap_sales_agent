"""Phase 2 — edition placeholder lifecycle + publish/unpublish service tests."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text

from src.modules.offer.application.launch_edition_service import LaunchEditionService
from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.domain.enums import OfferArchetype, VariantStructure
from src.modules.offer.domain.launch_edition import EditionStatus, EditionVisibility

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


class TestOfferServiceAutoPlaceholder:
    """``OfferService.create_offer`` auto-creates a DRAFT + PRIVATE placeholder
    edition for archetypes that support editions.
    """

    def test_edition_supporting_archetype_spawns_placeholder(self, db: Session, tenant_a: uuid.UUID) -> None:
        svc = OfferService(db)
        offer = svc.create_offer(
            name="Mi cohorte",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()

        editions_svc = LaunchEditionService(db)
        editions = editions_svc.list_editions(offer.id, tenant_a)

        assert len(editions) == 1
        ed = editions[0]
        assert ed.edition_number == 1
        assert ed.edition_name == "Edición #1"
        assert ed.start_date is None
        assert ed.status is EditionStatus.DRAFT
        assert ed.visibility is EditionVisibility.PRIVATE
        assert ed.variant_structure is VariantStructure.TEMPORAL_COHORT

    def test_servicio_placeholder_uses_recurring_intake_structure(self, db: Session, tenant_a: uuid.UUID) -> None:
        """Regression: SERVICIO placeholder must carry RECURRING_INTAKE,
        not the column-default ``temporal_cohort`` lottery. Hard-coded
        archetype→structure mappings live exclusively in
        ``ARCHETYPE_CATALOG.default_variant_structure``.
        """
        offer = OfferService(db).create_offer(name="Consultoría", tenant_id=tenant_a, archetype=OfferArchetype.SERVICIO)
        db.flush()
        editions = LaunchEditionService(db).list_editions(offer.id, tenant_a)
        assert len(editions) == 1
        assert editions[0].variant_structure is VariantStructure.RECURRING_INTAKE

    def test_experiencia_placeholder_uses_temporal_single_date_structure(
        self, db: Session, tenant_a: uuid.UUID
    ) -> None:
        offer = OfferService(db).create_offer(name="Webinar", tenant_id=tenant_a, archetype=OfferArchetype.EXPERIENCIA)
        db.flush()
        editions = LaunchEditionService(db).list_editions(offer.id, tenant_a)
        assert len(editions) == 1
        assert editions[0].variant_structure is VariantStructure.TEMPORAL_SINGLE_DATE

    def test_producto_archetype_does_not_spawn_placeholder(self, db: Session, tenant_a: uuid.UUID) -> None:
        """Rule: PRODUCTO and MEMBRESIA don't support editions — no placeholder."""
        svc = OfferService(db)
        offer = svc.create_offer(
            name="Mi ebook",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PRODUCTO,
        )
        db.flush()

        editions = LaunchEditionService(db).list_editions(offer.id, tenant_a)
        assert editions == []

    def test_experiencia_archetype_spawns_placeholder(self, db: Session, tenant_a: uuid.UUID) -> None:
        svc = OfferService(db)
        offer = svc.create_offer(
            name="Masterclass",
            tenant_id=tenant_a,
            archetype=OfferArchetype.EXPERIENCIA,
        )
        db.flush()

        editions = LaunchEditionService(db).list_editions(offer.id, tenant_a)
        assert len(editions) == 1
        assert editions[0].visibility is EditionVisibility.PRIVATE

    def test_placeholder_creation_is_idempotent(self, db: Session, tenant_a: uuid.UUID) -> None:
        """Re-creating the placeholder on an offer that already has one is a no-op."""
        svc = OfferService(db)
        offer = svc.create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()

        # Manually re-run placeholder creation — should not duplicate.
        svc._ensure_placeholder_edition(offer)
        db.flush()

        editions = LaunchEditionService(db).list_editions(offer.id, tenant_a)
        assert len(editions) == 1


class TestPublishUnpublish:
    """Publish flow — uses SERVICIO archetype for the base case because
    SERVICIO does not require end_date or location (only start_date).
    Archetype-specific publish constraints (PROGRAMA → end_date,
    EXPERIENCIA → location) are covered by test_edition_publish_archetype_rules.
    """

    def _setup(self, db: Session, tenant_a: uuid.UUID):
        offer = OfferService(db).create_offer(name="Servicio", tenant_id=tenant_a, archetype=OfferArchetype.SERVICIO)
        db.flush()
        edition = LaunchEditionService(db).list_editions(offer.id, tenant_a)[0]
        return edition

    def test_publish_rejected_without_start_date(self, db: Session, tenant_a: uuid.UUID) -> None:
        edition = self._setup(db, tenant_a)
        svc = LaunchEditionService(db)
        with pytest.raises(ValueError, match="requires start_date"):
            svc.publish_edition(edition.id, tenant_a)

    def test_publish_succeeds_when_start_date_set(self, db: Session, tenant_a: uuid.UUID) -> None:
        edition = self._setup(db, tenant_a)
        svc = LaunchEditionService(db)
        # Set a start date — SERVICIO requires only this to publish.
        svc.update_edition(
            edition.id,
            tenant_a,
            {"start_date": datetime(2026, 5, 15, 19, tzinfo=timezone.utc)},
        )
        published = svc.publish_edition(edition.id, tenant_a)
        assert published.status is EditionStatus.UPCOMING
        assert published.visibility is EditionVisibility.PUBLIC

    def test_unpublish_keeps_status_changes_visibility(self, db: Session, tenant_a: uuid.UUID) -> None:
        edition = self._setup(db, tenant_a)
        svc = LaunchEditionService(db)
        svc.update_edition(
            edition.id,
            tenant_a,
            {"start_date": datetime(2026, 5, 15, 19, tzinfo=timezone.utc)},
        )
        svc.publish_edition(edition.id, tenant_a)
        unpublished = svc.unpublish_edition(edition.id, tenant_a)
        assert unpublished.visibility is EditionVisibility.PRIVATE
        # Status is preserved — only visibility flips.
        assert unpublished.status is EditionStatus.UPCOMING


class TestListPublicEditions:
    """``list_public_editions`` returns only UPCOMING/ACTIVE + PUBLIC, soonest first."""

    def test_excludes_draft_private_placeholders(self, db: Session, tenant_a: uuid.UUID) -> None:
        OfferService(db).create_offer(
            name="Prog",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        # There's a placeholder DRAFT+PRIVATE edition — must be hidden.
        offers = list(db.execute(text("SELECT id FROM products")).all())
        assert len(offers) == 1
        offer_id = offers[0][0]

        public = LaunchEditionService(db).list_public_editions(offer_id, tenant_a)
        assert public == []

    def test_includes_only_upcoming_or_active_public_editions(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer = OfferService(db).create_offer(name="Svc", tenant_id=tenant_a, archetype=OfferArchetype.SERVICIO)
        db.flush()
        svc = LaunchEditionService(db)
        editions = svc.list_editions(offer.id, tenant_a)
        placeholder = editions[0]

        # Promote placeholder to UPCOMING + PUBLIC.
        svc.update_edition(
            placeholder.id,
            tenant_a,
            {"start_date": datetime(2026, 5, 15, 19, tzinfo=timezone.utc)},
        )
        svc.publish_edition(placeholder.id, tenant_a)

        # Create a second edition but leave DRAFT + PRIVATE.
        svc.create_edition(
            offer_id=offer.id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 8, 15, tzinfo=timezone.utc),
        )
        db.flush()

        public = svc.list_public_editions(offer.id, tenant_a)
        assert len(public) == 1
        assert public[0].id == placeholder.id

    def test_orders_ascending_by_start_date(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer = OfferService(db).create_offer(name="Svc", tenant_id=tenant_a, archetype=OfferArchetype.SERVICIO)
        db.flush()
        svc = LaunchEditionService(db)
        # Placeholder became PUBLIC on Aug
        placeholder = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            placeholder.id,
            tenant_a,
            {"start_date": datetime(2026, 8, 15, tzinfo=timezone.utc)},
        )
        svc.publish_edition(placeholder.id, tenant_a)
        # A second one on May — earlier
        new = svc.create_edition(
            offer_id=offer.id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 5, 15, tzinfo=timezone.utc),
        )
        svc.publish_edition(new.id, tenant_a)
        db.flush()

        public = svc.list_public_editions(offer.id, tenant_a)
        assert [e.start_date.month for e in public] == [5, 8]


class TestUpdateRevalidatesInvariants:
    def test_patch_invalid_transition_raises_value_error(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer = OfferService(db).create_offer(name="Prog", tenant_id=tenant_a, archetype=OfferArchetype.PROGRAMA)
        db.flush()
        svc = LaunchEditionService(db)
        ed = svc.list_editions(offer.id, tenant_a)[0]
        # Trying to jump DRAFT+PRIVATE → UPCOMING without start_date is invalid.
        with pytest.raises(ValueError, match="requires start_date"):
            svc.update_edition(ed.id, tenant_a, {"status": EditionStatus.UPCOMING})
