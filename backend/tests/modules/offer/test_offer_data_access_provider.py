"""F5 — OfferDataAccessProvider tests."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import pytest

from src.modules.copilot.domain.ports import DataQueryPlan
from src.modules.offer.copilot_provider.data_access import OfferDataAccessProvider
from tests.modules.offer.conftest import TENANT_A, create_product_model

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


@pytest.fixture
def access(db: Session) -> OfferDataAccessProvider:
    return OfferDataAccessProvider(db_factory=lambda: db)


def test_supports_offer_lookup_only(access: OfferDataAccessProvider) -> None:
    assert access.supports("offer_lookup") is True
    assert access.supports("lead_count") is False
    assert access.supports("conversation_count") is False
    assert access.supports("unknown") is False


@pytest.mark.asyncio
async def test_execute_returns_offers_for_tenant(
    db: Session,
    access: OfferDataAccessProvider,
) -> None:
    now = datetime.now(timezone.utc)
    offer = create_product_model(TENANT_A, name="Programa Propósito", status="active")
    offer.created_at = now - timedelta(days=2)
    db.add(offer)
    db.flush()

    plan = DataQueryPlan(kind="offer_lookup", filters={"name_query": "propósito"})
    result = await access.execute(tenant_id=TENANT_A, plan=plan, context={"db": db})

    assert result.metadata["count"] == 1
    assert result.metadata["kind"] == "offer_lookup"
    assert result.rows[0]["name"] == "Programa Propósito"
    assert result.rows[0]["status"] == "active"


@pytest.mark.asyncio
async def test_execute_uses_session_from_context_when_provided(
    db: Session,
) -> None:
    """Context db must be preferred over the default factory."""
    offer = create_product_model(TENANT_A, name="Mentoría", status="active")
    db.add(offer)
    db.flush()

    def _exploding_factory() -> Session:
        msg = "factory must not be called when context provides db"
        raise AssertionError(msg)

    access = OfferDataAccessProvider(db_factory=_exploding_factory)
    plan = DataQueryPlan(kind="offer_lookup", filters={})
    result = await access.execute(tenant_id=TENANT_A, plan=plan, context={"db": db})

    assert result.metadata["count"] >= 1


@pytest.mark.asyncio
async def test_execute_zero_results_returns_empty_metadata(
    access: OfferDataAccessProvider,
    db: Session,
) -> None:
    plan = DataQueryPlan(
        kind="offer_lookup",
        filters={"name_query": "no-existe-jamas-zzz"},
    )
    result = await access.execute(tenant_id=TENANT_A, plan=plan, context={"db": db})
    assert result.rows == []
    assert result.metadata["count"] == 0


@pytest.mark.asyncio
async def test_execute_rejects_unsupported_kind(
    access: OfferDataAccessProvider,
    db: Session,
) -> None:
    plan = DataQueryPlan(kind="lead_count", filters={})
    with pytest.raises(ValueError, match="offer_lookup"):
        await access.execute(tenant_id=TENANT_A, plan=plan, context={"db": db})
