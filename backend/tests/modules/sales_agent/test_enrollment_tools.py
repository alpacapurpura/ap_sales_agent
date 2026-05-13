"""Tests for the sales-agent enrollment tools (Phase 6)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

import pytest

from luana_core_offer_studio.domain.enums import VariantStructure
from luana_core_offer_studio.domain.launch_edition import (
    EditionStatus,
    EditionVisibility,
)
from luana_core_offer_studio.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from luana_core_sales_agent.application.agents.sales.enrollment_tools import (
    ENROLLMENT_TOOL_REGISTRY,
    tool_create_enrollment,
    tool_generate_payment_link,
    tool_list_public_editions,
    tool_list_waitlist,
    tool_promote_waitlist_to_edition,
)
from luana_core_sales_agent.domain.enrollment import EnrollmentStatus
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


_TENANT = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")


@pytest.fixture
def offer_id(db: Session) -> uuid.UUID:
    model = create_product_model(_TENANT, archetype="programa")
    db.add(model)
    db.flush()
    return model.id


@pytest.fixture
def public_edition(db: Session, offer_id: uuid.UUID) -> uuid.UUID:
    repo = LaunchEditionRepository(db)
    edition = repo.create(
        offer_id=offer_id,
        tenant_id=_TENANT,
        variant_structure=VariantStructure.TEMPORAL_COHORT,
        start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        status=EditionStatus.UPCOMING,
        visibility=EditionVisibility.PUBLIC,
    )
    return edition.id


def _state(offer_id: uuid.UUID | None = None, **extra: object) -> dict:
    base = {
        "tenant_id": _TENANT,
        "lead_id": uuid.uuid4(),
        "active_product": {"id": offer_id, "checkout_page_url": "https://pay.stripe.com/test"},
    }
    base.update(extra)
    return base


class TestRegistry:
    def test_all_seven_tools_registered(self) -> None:
        assert set(ENROLLMENT_TOOL_REGISTRY) == {
            "list_public_editions",
            "create_enrollment",
            "generate_payment_link",
            "mark_enrollment_paid_manual",
            "list_waitlist",
            "promote_waitlist_to_edition",
            "check_payment_status",
        }


class TestListPublicEditions:
    def test_returns_public_only(
        self,
        db: Session,
        offer_id: uuid.UUID,
        public_edition: uuid.UUID,
    ) -> None:
        # Add a DRAFT edition — must be excluded.
        LaunchEditionRepository(db).create(
            offer_id=offer_id,
            tenant_id=_TENANT,
            variant_structure=VariantStructure.TEMPORAL_COHORT,
            start_date=datetime(2026, 10, 7, tzinfo=timezone.utc),
            status=EditionStatus.DRAFT,
            visibility=EditionVisibility.PRIVATE,
        )
        result = tool_list_public_editions(_state(offer_id), db)
        assert result["status"] == "success"
        ids = [e["id"] for e in result["editions"]]
        assert str(public_edition) in ids
        assert len(ids) == 1


class TestCreateEnrollment:
    def test_without_edition_becomes_waitlist(
        self,
        db: Session,
        offer_id: uuid.UUID,
    ) -> None:
        state = _state(offer_id)
        state["_tool_args"] = {
            "offer_id": str(offer_id),
            "contact_id": str(uuid.uuid4()),
        }
        result = tool_create_enrollment(state, db)
        assert result["status"] == "success"
        assert result["enrollment_status"] == EnrollmentStatus.WAITLIST.value

    def test_with_edition_is_intent(
        self,
        db: Session,
        offer_id: uuid.UUID,
        public_edition: uuid.UUID,
    ) -> None:
        state = _state(offer_id)
        state["_tool_args"] = {
            "offer_id": str(offer_id),
            "contact_id": str(uuid.uuid4()),
            "edition_id": str(public_edition),
        }
        result = tool_create_enrollment(state, db)
        assert result["enrollment_status"] == EnrollmentStatus.INTENT.value


class TestGeneratePaymentLink:
    def test_returns_fallback_url(
        self,
        db: Session,
        offer_id: uuid.UUID,
        public_edition: uuid.UUID,
    ) -> None:
        # Create the enrollment first.
        state = _state(offer_id)
        state["_tool_args"] = {
            "offer_id": str(offer_id),
            "contact_id": str(uuid.uuid4()),
            "edition_id": str(public_edition),
        }
        created = tool_create_enrollment(state, db)
        eid = created["enrollment_id"]

        # Now generate link.
        state["_tool_args"] = {"enrollment_id": eid}
        result = tool_generate_payment_link(state, db)
        assert result["status"] == "success"
        assert result["url"] == "https://pay.stripe.com/test"


class TestWaitlistFlow:
    def test_list_and_promote(
        self,
        db: Session,
        offer_id: uuid.UUID,
        public_edition: uuid.UUID,
    ) -> None:
        # Put one lead in waitlist.
        state = _state(offer_id)
        state["_tool_args"] = {
            "offer_id": str(offer_id),
            "contact_id": str(uuid.uuid4()),
        }
        created = tool_create_enrollment(state, db)
        waitlist_id = created["enrollment_id"]

        # List should contain it.
        listing = tool_list_waitlist(state, db)
        assert len(listing["waitlist"]) == 1

        # Promote to edition.
        state["_tool_args"] = {
            "enrollment_ids": [waitlist_id],
            "target_edition_id": str(public_edition),
        }
        promoted = tool_promote_waitlist_to_edition(state, db)
        assert promoted["status"] == "success"
        assert waitlist_id in promoted["promoted_ids"]
