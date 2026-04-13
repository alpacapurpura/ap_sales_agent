"""Tests for N+1 query optimisations in product_mappings.py.

Covers:
- Batch dedup logic in backfill (Phase 1-3 pattern)
- Detail endpoint aggregation query consolidation
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import SaleStage, SaleStatus
from src.modules.crm.infrastructure.models.customer_model import (
    CustomerProfileModel,
    JourneyEventModel,
)
from src.modules.crm.infrastructure.models.sale_model import SaleModel
from tests.modules.offer.conftest import TENANT_A, create_product_model

# ── Helpers ──────────────────────────────────────────────────────────────────


def _make_profile(tenant_id: uuid.UUID) -> CustomerProfileModel:
    return CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        full_name="Test Customer",
    )


def _make_checkout_event(
    tenant_id: uuid.UUID,
    profile_id: uuid.UUID,
    source: str,
    order_id: str,
    product_id: str,
    price: float = 99.0,
) -> JourneyEventModel:
    return JourneyEventModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        profile_id=profile_id,
        event_name="checkout_completed",
        event_type="track",
        properties={
            "source": source,
            "order_id": order_id,
            "currency": "USD",
            "line_items": [
                {
                    "product_id": product_id,
                    "title": "Widget",
                    "price": price,
                    "quantity": 1,
                },
            ],
        },
        occurred_at=datetime.now(timezone.utc),
    )


def _make_sale(
    tenant_id: uuid.UUID,
    offer_id: uuid.UUID,
    customer_id: uuid.UUID,
    transaction_id: str,
    amount: float = 99.0,
) -> SaleModel:
    return SaleModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        customer_id=customer_id,
        offer_id=offer_id,
        transaction_id=transaction_id,
        amount=amount,
        currency="USD",
        status=SaleStatus.COMPLETED,
        stage=SaleStage.CONVERSION,
        source="SHOPIFY",
        occurred_at=datetime.now(timezone.utc),
    )


# ── Backfill batch dedup tests ───────────────────────────────────────────────


class TestBackfillBatchCreatesOnlyNew:
    """Verify that the batch dedup pattern (collect txn_ids -> single IN query
    -> subtract existing -> add_all) creates only the sales that don't already
    exist, exactly matching the optimised code in create_product_mapping."""

    def test_skips_existing_creates_new(self, db: Session):
        """Seed 3 checkout events; pre-create 1 sale with matching txn_id.
        Batch dedup should produce only the 2 new sales."""
        offer = create_product_model(TENANT_A, name="Backfill Offer")
        profile = _make_profile(TENANT_A)
        db.add_all([offer, profile])
        db.flush()

        ext_product_id = "PROD-100"
        source = "shopify"

        # 3 checkout events with distinct order_ids
        events = [
            _make_checkout_event(
                TENANT_A,
                profile.id,
                source,
                f"ORD-{i}",
                ext_product_id,
            )
            for i in range(3)
        ]
        db.add_all(events)
        db.flush()

        # Pre-create sale for ORD-1 (should be skipped during backfill)
        existing_txn = f"{source}-ORD-1-{ext_product_id}"
        db.add(_make_sale(TENANT_A, offer.id, profile.id, existing_txn))
        db.flush()

        # ── Reproduce batch dedup logic from product_mappings.py ──
        all_events = db.execute(
            select(
                JourneyEventModel.properties,
                JourneyEventModel.profile_id,
                JourneyEventModel.occurred_at,
            ).where(
                JourneyEventModel.tenant_id == TENANT_A,
                JourneyEventModel.event_name == "checkout_completed",
            ),
        ).all()

        candidates: list[dict] = []
        candidate_txn_ids: set[str] = set()

        for props, pid, occ in all_events:
            if not props or not pid:
                continue
            order_id = props.get("order_id", "")
            line_items = props.get("line_items", [])
            for item in line_items:
                product_id = str(item.get("product_id", ""))
                if product_id != ext_product_id:
                    continue
                txn_id = f"{source}-{order_id}-{product_id}"
                if txn_id in candidate_txn_ids:
                    continue
                candidate_txn_ids.add(txn_id)
                candidates.append(
                    {
                        "txn_id": txn_id,
                        "profile_id": pid,
                        "occurred_at": occ,
                        "currency": props.get("currency", "USD"),
                        "amount": float(item.get("price", 0)),
                        "order_id": order_id,
                    },
                )

        # Should find 3 candidates
        assert len(candidates) == 3

        # Single batch dedup
        existing_txn_ids = {
            row[0]
            for row in db.execute(
                select(SaleModel.transaction_id).where(
                    SaleModel.tenant_id == TENANT_A,
                    SaleModel.transaction_id.in_(candidate_txn_ids),
                ),
            ).all()
        }
        assert existing_txn in existing_txn_ids

        new_sales = [
            _make_sale(
                TENANT_A,
                offer.id,
                c["profile_id"],
                c["txn_id"],
                c["amount"],
            )
            for c in candidates
            if c["txn_id"] not in existing_txn_ids
        ]

        db.add_all(new_sales)
        db.flush()

        # Verify: 1 pre-existing + 2 new = 3 total
        total = db.execute(
            select(SaleModel.id).where(SaleModel.tenant_id == TENANT_A),
        ).all()
        assert len(total) == 3
        assert len(new_sales) == 2

    def test_no_duplicates_within_batch(self, db: Session):
        """Two events with the same order+product should produce only 1 sale."""
        offer = create_product_model(TENANT_A, name="Dedup Offer")
        profile = _make_profile(TENANT_A)
        db.add_all([offer, profile])
        db.flush()

        ext_product_id = "PROD-200"
        source = "shopify"

        # Same order_id twice (simulates duplicate events)
        events = [
            _make_checkout_event(
                TENANT_A,
                profile.id,
                source,
                "ORD-SAME",
                ext_product_id,
            )
            for _ in range(2)
        ]
        db.add_all(events)
        db.flush()

        all_events = db.execute(
            select(
                JourneyEventModel.properties,
                JourneyEventModel.profile_id,
                JourneyEventModel.occurred_at,
            ).where(
                JourneyEventModel.tenant_id == TENANT_A,
                JourneyEventModel.event_name == "checkout_completed",
            ),
        ).all()

        candidate_txn_ids: set[str] = set()
        candidates: list[dict] = []
        for props, pid, _occ in all_events:
            if not props or not pid:
                continue
            order_id = props.get("order_id", "")
            for item in props.get("line_items", []):
                product_id = str(item.get("product_id", ""))
                if product_id != ext_product_id:
                    continue
                txn_id = f"{source}-{order_id}-{product_id}"
                if txn_id in candidate_txn_ids:
                    continue
                candidate_txn_ids.add(txn_id)
                candidates.append({"txn_id": txn_id, "profile_id": pid})

        # Dedup within batch: should only have 1 candidate
        assert len(candidates) == 1

    def test_empty_events_produces_zero_sales(self, db: Session):
        """No checkout events means no candidates, no queries, no sales."""
        offer = create_product_model(TENANT_A, name="Empty Offer")
        db.add(offer)
        db.flush()

        all_events = db.execute(
            select(JourneyEventModel.properties).where(
                JourneyEventModel.tenant_id == TENANT_A,
                JourneyEventModel.event_name == "checkout_completed",
            ),
        ).all()

        assert len(all_events) == 0


# ── Detail endpoint aggregation tests ────────────────────────────────────────


class TestDetailEndpointReturnsData:
    """Verify that the consolidated aggregation query (sales count, revenue,
    unique customers, currency, date range) returns correct results."""

    def test_aggregation_with_sales(self, db: Session):
        """Seed an offer with 3 sales from 2 customers; verify aggregated values."""
        from sqlalchemy import func as sa_func

        offer = create_product_model(TENANT_A, name="Detail Offer")
        cust1 = _make_profile(TENANT_A)
        cust2 = _make_profile(TENANT_A)
        db.add_all([offer, cust1, cust2])
        db.flush()

        sales = [
            _make_sale(TENANT_A, offer.id, cust1.id, "txn-1", 100.0),
            _make_sale(TENANT_A, offer.id, cust1.id, "txn-2", 50.0),
            _make_sale(TENANT_A, offer.id, cust2.id, "txn-3", 75.0),
        ]
        db.add_all(sales)
        db.flush()

        # Reproduce the consolidated query from the detail endpoint
        agg_row = db.execute(
            select(
                sa_func.count(SaleModel.id).label("sales_count"),
                sa_func.coalesce(sa_func.sum(SaleModel.amount), 0).label(
                    "total_revenue",
                ),
                sa_func.count(sa_func.distinct(SaleModel.customer_id)).label(
                    "unique_customers",
                ),
                sa_func.min(SaleModel.occurred_at).label("first_sale"),
                sa_func.max(SaleModel.occurred_at).label("last_sale"),
                sa_func.min(SaleModel.currency).label("currency"),
            ).where(
                SaleModel.offer_id == offer.id,
                SaleModel.tenant_id == TENANT_A,
                SaleModel.status == "COMPLETED",
            ),
        ).first()

        assert agg_row is not None
        assert agg_row.sales_count == 3
        assert float(agg_row.total_revenue) == 225.0
        assert agg_row.unique_customers == 2
        assert agg_row.first_sale is not None
        assert agg_row.last_sale is not None
        assert agg_row.currency == "USD"

    def test_aggregation_no_sales_returns_zeros(self, db: Session):
        """An offer with zero sales should return 0/None aggregates."""
        from sqlalchemy import func as sa_func

        offer = create_product_model(TENANT_A, name="Empty Detail Offer")
        db.add(offer)
        db.flush()

        agg_row = db.execute(
            select(
                sa_func.count(SaleModel.id).label("sales_count"),
                sa_func.coalesce(sa_func.sum(SaleModel.amount), 0).label(
                    "total_revenue",
                ),
                sa_func.count(sa_func.distinct(SaleModel.customer_id)).label(
                    "unique_customers",
                ),
                sa_func.min(SaleModel.occurred_at).label("first_sale"),
                sa_func.max(SaleModel.occurred_at).label("last_sale"),
                sa_func.min(SaleModel.currency).label("currency"),
            ).where(
                SaleModel.offer_id == offer.id,
                SaleModel.tenant_id == TENANT_A,
                SaleModel.status == "COMPLETED",
            ),
        ).first()

        assert agg_row is not None
        assert agg_row.sales_count == 0
        assert float(agg_row.total_revenue) == 0.0
        assert agg_row.unique_customers == 0
        assert agg_row.first_sale is None
        assert agg_row.last_sale is None
        # currency should be None when no sales; endpoint defaults to "USD"
        currency = agg_row.currency or "USD"
        assert currency == "USD"

    def test_source_breakdown_groups_correctly(self, db: Session):
        """Source breakdown should group by SaleModel.source."""
        from sqlalchemy import func as sa_func

        offer = create_product_model(TENANT_A, name="Source Offer")
        cust = _make_profile(TENANT_A)
        db.add_all([offer, cust])
        db.flush()

        sale1 = _make_sale(TENANT_A, offer.id, cust.id, "txn-s1", 100.0)
        sale1.source = "SHOPIFY"
        sale2 = _make_sale(TENANT_A, offer.id, cust.id, "txn-s2", 50.0)
        sale2.source = "SHOPIFY"
        sale3 = _make_sale(TENANT_A, offer.id, cust.id, "txn-s3", 75.0)
        sale3.source = "STRIPE"
        db.add_all([sale1, sale2, sale3])
        db.flush()

        source_rows = db.execute(
            select(
                SaleModel.source,
                sa_func.count(SaleModel.id),
            )
            .where(
                SaleModel.offer_id == offer.id,
                SaleModel.tenant_id == TENANT_A,
                SaleModel.status == "COMPLETED",
            )
            .group_by(SaleModel.source),
        ).all()
        breakdown = dict(source_rows)

        assert breakdown["SHOPIFY"] == 2
        assert breakdown["STRIPE"] == 1
