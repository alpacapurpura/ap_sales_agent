"""Regression tests for OfferReadPortImpl.get_offers_by_tenant.

Bug: after the archive lifecycle refactor (commit f972faa5), archival is
tracked via ``archived_at`` (and legacy ``status='archived'`` rows were
backfilled to ``status='draft'`` by migration 040). The port still filtered
on ``status != 'archived'``, so archived offers leaked into every caller
that used this port — including
``/api/v1/advertising/offers`` (Offer Assignment drawer in the Meta Ads
Campaigns tab).
"""

import asyncio
import uuid

import pytest
from sqlalchemy.orm import Session

from luana_core_offer_studio.application.services.offer_read_port_impl import (
    OfferReadPortImpl,
)
from tests.modules.offer.conftest import create_product_model


@pytest.mark.asyncio
async def test_get_offers_by_tenant_excludes_archived(
    db: Session,
    tenant_a: uuid.UUID,
) -> None:
    """Archived offers (archived_at IS NOT NULL) must not appear."""
    from datetime import UTC, datetime

    active = create_product_model(tenant_a, name="Active Offer", status="active")
    archived = create_product_model(
        tenant_a,
        name="Archived Offer",
        status="active",  # status preserved on archive — refactor semantics
        archived_at=datetime.now(UTC),
    )
    db.add_all([active, archived])
    db.flush()

    port = OfferReadPortImpl(db)
    offers = await port.get_offers_by_tenant(tenant_a)

    names = {o.public_name for o in offers}
    assert "Active Offer" in names
    assert "Archived Offer" not in names


@pytest.mark.asyncio
async def test_get_offers_by_tenant_excludes_soft_deleted(
    db: Session,
    tenant_a: uuid.UUID,
) -> None:
    """Soft-deleted offers (deleted_at IS NOT NULL) must not appear."""
    from datetime import UTC, datetime

    active = create_product_model(tenant_a, name="Active", status="active")
    deleted = create_product_model(
        tenant_a,
        name="Deleted",
        status="active",
        deleted_at=datetime.now(UTC),
    )
    db.add_all([active, deleted])
    db.flush()

    port = OfferReadPortImpl(db)
    offers = await port.get_offers_by_tenant(tenant_a)

    names = {o.public_name for o in offers}
    assert "Active" in names
    assert "Deleted" not in names


@pytest.mark.asyncio
async def test_get_offers_by_tenant_includes_draft(
    db: Session,
    tenant_a: uuid.UUID,
) -> None:
    """Draft offers should still be returned (they are not archived).

    This guards against regressing back to the old ``status in {archived, draft}``
    filter that was in the advertising endpoint — draft offers are legitimate
    assignment targets.
    """
    draft = create_product_model(tenant_a, name="Draft Offer", status="draft")
    db.add(draft)
    db.flush()

    port = OfferReadPortImpl(db)
    offers = await port.get_offers_by_tenant(tenant_a)

    names = {o.public_name for o in offers}
    assert "Draft Offer" in names


def test_sync_wrappers_work(db: Session, tenant_a: uuid.UUID) -> None:
    """Smoke: ensure the async port runs under asyncio.run in tests."""
    active = create_product_model(tenant_a, name="Smoke", status="active")
    db.add(active)
    db.flush()

    port = OfferReadPortImpl(db)
    offers = asyncio.run(port.get_offers_by_tenant(tenant_a))
    assert any(o.public_name == "Smoke" for o in offers)
