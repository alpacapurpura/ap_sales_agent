"""F5 — CrmDataAccessProvider tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest

from luana_core_copilot.domain.ports import DataQueryPlan
from luana_core_crm.copilot_provider.data_access import CrmDataAccessProvider
from luana_core_platform.infrastructure.models.crm import LeadModel

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

TENANT_X = uuid.UUID("c001ab1e-0000-4000-8000-cc0000000001")


def _make_lead(
    *,
    last_interaction_date: datetime | None,
    channel: str = "whatsapp",
) -> LeadModel:
    kwargs: dict = {
        "id": uuid.uuid4(),
        "tenant_id": TENANT_X,
        "fit_score": 0,
        "intent_score": 0,
        "temperature": "COLD",
        "is_blacklisted": False,
        "last_interaction_date": last_interaction_date,
        "profile_data": {},
        "key_objections_history": [],
    }
    if channel == "whatsapp":
        kwargs["whatsapp_id"] = f"wa-{uuid.uuid4().hex[:8]}"
    elif channel == "telegram":
        kwargs["telegram_id"] = f"tg-{uuid.uuid4().hex[:8]}"
    return LeadModel(**kwargs)


@pytest.fixture
def access(db: Session) -> CrmDataAccessProvider:
    return CrmDataAccessProvider(db_factory=lambda: db)


def test_supports_lead_count_only(access: CrmDataAccessProvider) -> None:
    assert access.supports("lead_count") is True
    assert access.supports("offer_lookup") is False


@pytest.mark.asyncio
async def test_execute_counts_within_window(
    db: Session,
    access: CrmDataAccessProvider,
) -> None:
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            _make_lead(last_interaction_date=now - timedelta(days=1)),
            _make_lead(last_interaction_date=now - timedelta(days=3)),
            _make_lead(last_interaction_date=now - timedelta(days=30)),
        ],
    )
    db.flush()

    plan = DataQueryPlan(
        kind="lead_count",
        filters={
            "since": now - timedelta(days=7),
            "until": now,
        },
    )
    result = await access.execute(tenant_id=TENANT_X, plan=plan, context={"db": db})

    assert result.metadata["count"] == 2
    assert result.metadata["kind"] == "lead_count"
    assert result.rows == []  # counts return no rows by design


@pytest.mark.asyncio
async def test_execute_filters_by_channel(
    db: Session,
    access: CrmDataAccessProvider,
) -> None:
    now = datetime.now(timezone.utc)
    db.add_all(
        [
            _make_lead(last_interaction_date=now - timedelta(hours=1), channel="whatsapp"),
            _make_lead(last_interaction_date=now - timedelta(hours=2), channel="telegram"),
        ],
    )
    db.flush()

    plan = DataQueryPlan(
        kind="lead_count",
        filters={
            "since": now - timedelta(days=1),
            "until": now,
            "channel": "whatsapp",
        },
    )
    result = await access.execute(tenant_id=TENANT_X, plan=plan, context={"db": db})

    assert result.metadata["count"] == 1
    assert result.metadata["channel"] == "whatsapp"


@pytest.mark.asyncio
async def test_execute_requires_since_and_until(
    db: Session,
    access: CrmDataAccessProvider,
) -> None:
    plan = DataQueryPlan(kind="lead_count", filters={})
    with pytest.raises(ValueError, match="since"):
        await access.execute(tenant_id=TENANT_X, plan=plan, context={"db": db})
