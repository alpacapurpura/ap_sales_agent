"""F5 — LeadRepository.count_inbound (date window + channel filter) tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest

from src.modules.crm.infrastructure.repositories.lead_repository import LeadRepository
from src.shared.infrastructure.models.crm import LeadModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

TENANT_X = uuid.UUID("0bb15bb1-0000-4000-8000-000000000001")
TENANT_Y = uuid.UUID("0bb15bb1-0000-4000-8000-000000000002")


def _make_lead(
    *,
    tenant_id: uuid.UUID,
    last_interaction_date: datetime | None,
    channel: str = "whatsapp",
    channel_id: str | None = None,
) -> LeadModel:
    kwargs: dict = {
        "id": uuid.uuid4(),
        "tenant_id": tenant_id,
        "fit_score": 0,
        "intent_score": 0,
        "temperature": "COLD",
        "is_blacklisted": False,
        "last_interaction_date": last_interaction_date,
        "profile_data": {},
        "key_objections_history": [],
    }
    cid = channel_id or f"id-{uuid.uuid4().hex[:8]}"
    if channel == "whatsapp":
        kwargs["whatsapp_id"] = cid
    elif channel == "telegram":
        kwargs["telegram_id"] = cid
    elif channel == "instagram":
        kwargs["instagram_id"] = cid
    return LeadModel(**kwargs)


@pytest.fixture
def leads_seed(db: Session) -> dict[str, uuid.UUID]:
    now = datetime.now(timezone.utc)
    inside_window = _make_lead(
        tenant_id=TENANT_X,
        last_interaction_date=now - timedelta(days=2),
        channel="whatsapp",
    )
    inside_telegram = _make_lead(
        tenant_id=TENANT_X,
        last_interaction_date=now - timedelta(hours=1),
        channel="telegram",
    )
    outside_window = _make_lead(
        tenant_id=TENANT_X,
        last_interaction_date=now - timedelta(days=30),
        channel="whatsapp",
    )
    other_tenant = _make_lead(
        tenant_id=TENANT_Y,
        last_interaction_date=now - timedelta(days=1),
        channel="whatsapp",
    )
    no_interaction = _make_lead(
        tenant_id=TENANT_X,
        last_interaction_date=None,
        channel="whatsapp",
    )
    db.add_all(
        [inside_window, inside_telegram, outside_window, other_tenant, no_interaction],
    )
    db.flush()
    return {
        "inside_window": inside_window.id,
        "inside_telegram": inside_telegram.id,
        "outside_window": outside_window.id,
        "other_tenant": other_tenant.id,
        "no_interaction": no_interaction.id,
    }


def test_count_inbound_within_window(
    db: Session,
    leads_seed: dict[str, uuid.UUID],
) -> None:
    repo = LeadRepository(db)
    now = datetime.now(timezone.utc)
    count = repo.count_inbound(
        tenant_id=TENANT_X,
        since=now - timedelta(days=7),
        until=now,
    )
    assert count == 2  # inside_window + inside_telegram


def test_count_inbound_filters_by_tenant(
    db: Session,
    leads_seed: dict[str, uuid.UUID],
) -> None:
    repo = LeadRepository(db)
    now = datetime.now(timezone.utc)
    count_y = repo.count_inbound(
        tenant_id=TENANT_Y,
        since=now - timedelta(days=7),
        until=now,
    )
    assert count_y == 1


def test_count_inbound_channel_whatsapp(
    db: Session,
    leads_seed: dict[str, uuid.UUID],
) -> None:
    repo = LeadRepository(db)
    now = datetime.now(timezone.utc)
    count = repo.count_inbound(
        tenant_id=TENANT_X,
        since=now - timedelta(days=7),
        until=now,
        channel="whatsapp",
    )
    assert count == 1  # inside_window only (telegram excluded)


def test_count_inbound_channel_telegram(
    db: Session,
    leads_seed: dict[str, uuid.UUID],
) -> None:
    repo = LeadRepository(db)
    now = datetime.now(timezone.utc)
    count = repo.count_inbound(
        tenant_id=TENANT_X,
        since=now - timedelta(days=7),
        until=now,
        channel="telegram",
    )
    assert count == 1


def test_count_inbound_zero_when_window_empty(
    db: Session,
    leads_seed: dict[str, uuid.UUID],
) -> None:
    repo = LeadRepository(db)
    now = datetime.now(timezone.utc)
    count = repo.count_inbound(
        tenant_id=TENANT_X,
        since=now - timedelta(hours=1, minutes=30),
        until=now - timedelta(hours=1, minutes=10),
    )
    assert count == 0


def test_count_inbound_excludes_null_last_interaction(
    db: Session,
    leads_seed: dict[str, uuid.UUID],
) -> None:
    repo = LeadRepository(db)
    now = datetime.now(timezone.utc)
    count = repo.count_inbound(
        tenant_id=TENANT_X,
        since=now - timedelta(days=365),
        until=now,
    )
    # 3 leads with non-null interaction in TENANT_X (inside_window + inside_telegram + outside_window)
    assert count == 3
