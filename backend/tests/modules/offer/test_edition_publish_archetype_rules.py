"""Publish-time archetype rules enforced by LaunchEditionService.publish_edition."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest

from src.modules.offer.application.launch_edition_service import LaunchEditionService
from src.modules.offer.application.offer_service import OfferService
from src.modules.offer.domain.enums import OfferArchetype

if TYPE_CHECKING:
    import uuid

    from sqlalchemy.orm import Session


class TestProgramPublishRequiresEndDate:
    """PROGRAMA = COHORT structure → requires_end_date_on_publish is True."""

    def test_publish_without_end_date_raises(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer = OfferService(db).create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        svc = LaunchEditionService(db)
        ed = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            ed.id,
            tenant_a,
            {"start_date": datetime(2026, 5, 15, tzinfo=timezone.utc)},
        )

        with pytest.raises(ValueError, match="requires end_date to publish"):
            svc.publish_edition(ed.id, tenant_a)

    def test_publish_with_end_date_succeeds(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer = OfferService(db).create_offer(
            name="Bootcamp",
            tenant_id=tenant_a,
            archetype=OfferArchetype.PROGRAMA,
        )
        db.flush()
        svc = LaunchEditionService(db)
        ed = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            ed.id,
            tenant_a,
            {
                "start_date": datetime(2026, 5, 15, tzinfo=timezone.utc),
                "end_date": datetime(2026, 7, 15, tzinfo=timezone.utc),
            },
        )
        published = svc.publish_edition(ed.id, tenant_a)
        assert published.visibility.value == "public"


class TestExperienciaPublishRequiresLocation:
    """EXPERIENCIA → requires_location_on_publish is True."""

    def test_publish_without_location_raises(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer = OfferService(db).create_offer(
            name="Retiro",
            tenant_id=tenant_a,
            archetype=OfferArchetype.EXPERIENCIA,
        )
        db.flush()
        svc = LaunchEditionService(db)
        ed = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            ed.id,
            tenant_a,
            {"start_date": datetime(2026, 5, 15, tzinfo=timezone.utc)},
        )

        with pytest.raises(ValueError, match="requires location to publish"):
            svc.publish_edition(ed.id, tenant_a)

    def test_publish_with_location_succeeds(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer = OfferService(db).create_offer(
            name="Retiro",
            tenant_id=tenant_a,
            archetype=OfferArchetype.EXPERIENCIA,
        )
        db.flush()
        svc = LaunchEditionService(db)
        ed = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            ed.id,
            tenant_a,
            {
                "start_date": datetime(2026, 5, 15, tzinfo=timezone.utc),
                "location_override": {"type": "virtual", "url": "https://zoom"},
            },
        )
        published = svc.publish_edition(ed.id, tenant_a)
        assert published.visibility.value == "public"


class TestServicioPublishIsPermissive:
    """SERVICIO (RECURRING) does not require end_date or location."""

    def test_publish_with_only_start_date_succeeds(self, db: Session, tenant_a: uuid.UUID) -> None:
        offer = OfferService(db).create_offer(
            name="Consultoría",
            tenant_id=tenant_a,
            archetype=OfferArchetype.SERVICIO,
        )
        db.flush()
        svc = LaunchEditionService(db)
        ed = svc.list_editions(offer.id, tenant_a)[0]
        svc.update_edition(
            ed.id,
            tenant_a,
            {"start_date": datetime(2026, 5, 15, tzinfo=timezone.utc)},
        )
        published = svc.publish_edition(ed.id, tenant_a)
        assert published.visibility.value == "public"
