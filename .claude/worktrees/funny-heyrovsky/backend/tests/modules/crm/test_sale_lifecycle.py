"""
Tests for sale-triggered lifecycle transitions via EventBus.

CRM-02/CRM-03: SaleService emits SaleCompletedEvent, handler transitions
profile to CUSTOMER (CONVERSION), increments lifetime_value (EXPANSION),
and reactivates CHURNED profiles.
"""
import uuid
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import LifecycleStage, SaleStage
from src.modules.crm.infrastructure.models.customer_model import (
    CustomerProfileModel,
)
from src.modules.crm.infrastructure.models.lifecycle_transition_model import (
    LifecycleTransitionModel,
)
from src.shared.domain.events import EventBus

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_profile(
    db: Session,
    tenant_id: uuid.UUID,
    stage: LifecycleStage = LifecycleStage.SQL,
    score: float = 75.0,
    lifetime_value: float = 0.0,
    first_conversion_at: datetime | None = None,
) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email=f"{uuid.uuid4().hex[:8]}@test.com",
        full_name="Sale Test User",
        lifecycle_stage=stage,
        lead_score=score,
        lifetime_value=lifetime_value,
        is_inactive=False,
        first_conversion_at=first_conversion_at,
        traits={},
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


# ---------------------------------------------------------------------------
# Sale -> Lifecycle Transitions (via LifecycleService.handle_sale_completed)
# ---------------------------------------------------------------------------

class TestConversionSale:
    """CONVERSION sale transitions profile to CUSTOMER."""

    def test_conversion_sale_triggers_customer_stage(self, db: Session, tenant_id):
        from src.modules.crm.application.services.lifecycle_service import LifecycleService
        from src.modules.crm.domain.events import SaleCompletedEvent

        profile = _make_profile(db, tenant_id, stage=LifecycleStage.SQL)

        event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=uuid.uuid4(),
            customer_id=profile.id,
            stage="CONVERSION",
            amount=99.0,
            offer_id=uuid.uuid4(),
        )

        svc = LifecycleService(db)
        svc.handle_sale_completed(event)

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.CUSTOMER

    def test_conversion_sets_first_conversion_at(self, db: Session, tenant_id):
        from src.modules.crm.application.services.lifecycle_service import LifecycleService
        from src.modules.crm.domain.events import SaleCompletedEvent

        profile = _make_profile(db, tenant_id, stage=LifecycleStage.SQL)
        assert profile.first_conversion_at is None

        event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=uuid.uuid4(),
            customer_id=profile.id,
            stage="CONVERSION",
            amount=50.0,
            offer_id=uuid.uuid4(),
        )

        svc = LifecycleService(db)
        svc.handle_sale_completed(event)

        db.refresh(profile)
        assert profile.first_conversion_at is not None

    def test_conversion_increments_lifetime_value(self, db: Session, tenant_id):
        from src.modules.crm.application.services.lifecycle_service import LifecycleService
        from src.modules.crm.domain.events import SaleCompletedEvent

        profile = _make_profile(db, tenant_id, stage=LifecycleStage.SQL, lifetime_value=0.0)

        event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=uuid.uuid4(),
            customer_id=profile.id,
            stage="CONVERSION",
            amount=150.0,
            offer_id=uuid.uuid4(),
        )

        svc = LifecycleService(db)
        svc.handle_sale_completed(event)

        db.refresh(profile)
        assert profile.lifetime_value == 150.0


class TestExpansionSale:
    """EXPANSION sale increments lifetime_value and keeps CUSTOMER stage."""

    def test_expansion_sale_increments_lifetime_value(self, db: Session, tenant_id):
        from src.modules.crm.application.services.lifecycle_service import LifecycleService
        from src.modules.crm.domain.events import SaleCompletedEvent

        profile = _make_profile(
            db, tenant_id,
            stage=LifecycleStage.CUSTOMER,
            lifetime_value=100.0,
            first_conversion_at=datetime.now(timezone.utc) - timedelta(days=30),
        )

        event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=uuid.uuid4(),
            customer_id=profile.id,
            stage="EXPANSION",
            amount=50.0,
            offer_id=uuid.uuid4(),
        )

        svc = LifecycleService(db)
        svc.handle_sale_completed(event)

        db.refresh(profile)
        assert profile.lifetime_value == 150.0

    def test_expansion_keeps_customer_stage(self, db: Session, tenant_id):
        from src.modules.crm.application.services.lifecycle_service import LifecycleService
        from src.modules.crm.domain.events import SaleCompletedEvent

        profile = _make_profile(
            db, tenant_id,
            stage=LifecycleStage.CUSTOMER,
            lifetime_value=100.0,
            first_conversion_at=datetime.now(timezone.utc) - timedelta(days=30),
        )

        event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=uuid.uuid4(),
            customer_id=profile.id,
            stage="EXPANSION",
            amount=75.0,
            offer_id=uuid.uuid4(),
        )

        svc = LifecycleService(db)
        svc.handle_sale_completed(event)

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.CUSTOMER


class TestChurnedReactivation:
    """CHURNED profile reactivated by new sale becomes CUSTOMER."""

    def test_churned_reactivation(self, db: Session, tenant_id):
        from src.modules.crm.application.services.lifecycle_service import LifecycleService
        from src.modules.crm.domain.events import SaleCompletedEvent

        profile = _make_profile(
            db, tenant_id,
            stage=LifecycleStage.CHURNED,
            lifetime_value=200.0,
        )

        event = SaleCompletedEvent.create(
            tenant_id=tenant_id,
            sale_id=uuid.uuid4(),
            customer_id=profile.id,
            stage="CONVERSION",
            amount=80.0,
            offer_id=uuid.uuid4(),
        )

        svc = LifecycleService(db)
        svc.handle_sale_completed(event)

        db.refresh(profile)
        assert profile.lifecycle_stage == LifecycleStage.CUSTOMER
        assert profile.lifetime_value == 280.0

        # Verify audit trail shows reactivation
        transitions = (
            db.query(LifecycleTransitionModel)
            .filter(LifecycleTransitionModel.profile_id == profile.id)
            .all()
        )
        assert len(transitions) == 1
        assert transitions[0].triggered_by == "reactivation"


# ---------------------------------------------------------------------------
# EventBus Integration
# ---------------------------------------------------------------------------

class TestSaleEventEmission:
    """SaleService emits SaleCompletedEvent via EventBus."""

    def test_sale_event_emitted_after_commit(self, db: Session, tenant_id):
        """Verify EventBus.publish called with correct SaleCompletedEvent."""
        from src.modules.crm.application.services.sale_service import SaleService
        from src.modules.crm.domain.enums import PaymentMethod

        # Create a customer profile so the sale can reference it
        profile = _make_profile(db, tenant_id, stage=LifecycleStage.SQL)
        offer_id = uuid.uuid4()

        with patch.object(EventBus, "publish") as mock_publish:
            svc = SaleService(db)
            sale = svc.create_sale(
                tenant_id=tenant_id,
                customer_id=profile.id,
                offer_id=offer_id,
                amount=100.0,
                payment_method=PaymentMethod.STRIPE,
            )

            assert mock_publish.called
            event = mock_publish.call_args[0][0]
            assert event.event_name == "sale_completed"
            assert event.tenant_id == tenant_id
            assert event.payload["customer_id"] == str(profile.id)
            assert event.payload["amount"] == 100.0


class TestEventHandlerRegistration:
    """Event handlers registered at startup."""

    def test_register_event_handlers(self):
        from src.modules.crm.application.event_handlers import register_event_handlers

        EventBus.clear()
        register_event_handlers()

        assert "sale_completed" in EventBus._handlers
        assert len(EventBus._handlers["sale_completed"]) >= 1

        # Cleanup
        EventBus.clear()


# ---------------------------------------------------------------------------
# Module Decoupling
# ---------------------------------------------------------------------------

class TestModuleDecoupling:
    """Sales module does not import CRM services directly."""

    def test_sales_module_does_not_import_crm(self):
        """Static check: sale_service.py has no imports from crm.application.services."""
        import inspect
        import src.modules.crm.application.services.sale_service as sale_mod

        source = inspect.getsource(sale_mod)
        assert "from src.modules.crm.application.services.lifecycle_service" not in source
        assert "from src.modules.crm.application.services.customer_service" not in source
