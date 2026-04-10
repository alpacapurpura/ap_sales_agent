"""Fixtures for advertising module tests."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from uuid import UUID

import pytest

# Import models so Base.metadata registers them before create_all runs.
from src.modules.advertising.infrastructure.models.ad_campaign_template_model import (  # noqa: F401
    AdCampaignTemplateModel,
)
from src.modules.advertising.infrastructure.models.ad_offer_association_model import (  # noqa: F401
    AdOfferAssociationModel,
)
from src.modules.analytics.infrastructure.models.ad_campaign_model import (
    AdCampaignModel,
)
from src.modules.analytics.infrastructure.models.ad_model import (
    AdModel,
)
from src.modules.analytics.infrastructure.models.ad_set_model import (
    AdSetModel,
)
from src.modules.analytics.infrastructure.models.official_metrics_model import (
    OfficialMetricModel,
)
from src.modules.offer.infrastructure.models.product_model import (
    ProductModel,
)
from src.shared.domain.base_entity import Base


@pytest.fixture(autouse=True)
def _ensure_tables(db_engine):
    """Ensure all advertising+analytics+offer tables exist for each test session."""
    Base.metadata.create_all(bind=db_engine)


@pytest.fixture
def tenant_id() -> UUID:
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def offer_id() -> UUID:
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def other_tenant_id() -> UUID:
    return uuid.UUID("99999999-9999-9999-9999-999999999999")


def _make_offer(
    db,
    *,
    tenant_id: UUID,
    name: str = "Masterclass de Marketing",
    archetype: str = "PRODUCTO",
    is_lead_magnet: bool = False,
    onboarding_action: str | None = None,
    checkout_page_url: str | None = None,
    landing_url: str | None = None,
    status: str = "active",
    internal_sku: str | None = None,
    offer_id: UUID | None = None,
    currency: str = "USD",
) -> ProductModel:
    product = ProductModel(
        id=offer_id or uuid.uuid4(),
        tenant_id=tenant_id,
        name=name,
        status=status,
        archetype=archetype,
        is_lead_magnet=is_lead_magnet,
        onboarding_action=onboarding_action,
        checkout_page_url=checkout_page_url,
        landing_page_config={"url": landing_url} if landing_url else {},
        internal_sku=internal_sku,
        pricing=[],
        currency=currency,
    )
    db.add(product)
    db.flush()
    return product


def _make_campaign(
    db,
    *,
    tenant_id: UUID,
    external_id: str,
    name: str,
    objective: str | None = "OUTCOME_SALES",
    status: str = "ACTIVE",
    effective_status: str = "ACTIVE",
) -> AdCampaignModel:
    campaign = AdCampaignModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        provider="meta",
        external_id=external_id,
        name=name,
        objective=objective,
        status=status,
        effective_status=effective_status,
    )
    db.add(campaign)
    db.flush()
    return campaign


def _make_ad_set(
    db,
    *,
    tenant_id: UUID,
    external_id: str,
    campaign_external_id: str,
    name: str,
    optimization_goal: str | None = "OFFSITE_CONVERSIONS",
) -> AdSetModel:
    ad_set = AdSetModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        provider="meta",
        external_id=external_id,
        campaign_external_id=campaign_external_id,
        name=name,
        status="ACTIVE",
        effective_status="ACTIVE",
        optimization_goal=optimization_goal,
    )
    db.add(ad_set)
    db.flush()
    return ad_set


def _make_ad(
    db,
    *,
    tenant_id: UUID,
    external_id: str,
    campaign_external_id: str,
    ad_set_external_id: str,
    name: str,
    creative_link_url: str | None = None,
) -> AdModel:
    ad = AdModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        provider="meta",
        external_id=external_id,
        campaign_external_id=campaign_external_id,
        ad_set_external_id=ad_set_external_id,
        name=name,
        creative_link_url=creative_link_url,
        status="ACTIVE",
    )
    db.add(ad)
    db.flush()
    return ad


def _make_metric(
    db,
    *,
    tenant_id: UUID,
    metric_name: str,
    value: float,
    unit: str = "count",
    currency: str | None = "USD",
    metric_date: date,
    campaign_id: str | None = None,
    ad_set_id: str | None = None,
    ad_id: str | None = None,
) -> OfficialMetricModel:
    metric = OfficialMetricModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        provider="meta",
        channel_slug="meta-ads",
        metric_name=metric_name,
        value=value,
        unit=unit,
        currency=currency,
        metric_date=metric_date,
        campaign_id=campaign_id,
        ad_set_id=ad_set_id,
        ad_id=ad_id,
        created_at=datetime.now(timezone.utc),
    )
    db.add(metric)
    db.flush()
    return metric


@pytest.fixture
def make_offer():
    return _make_offer


@pytest.fixture
def make_campaign():
    return _make_campaign


@pytest.fixture
def make_ad_set():
    return _make_ad_set


@pytest.fixture
def make_ad():
    return _make_ad


@pytest.fixture
def make_metric():
    return _make_metric
