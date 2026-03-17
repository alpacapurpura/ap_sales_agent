"""
Test that validates the entire Telegram message processing flow,
step by step, against the real database. This catches enum mismatches,
type errors, and constraint violations BEFORE manual testing.

Run: docker exec visionarias_brain_dev pytest src/tests/test_telegram_flow.py -v
"""
import pytest
import uuid
from uuid import UUID
from sqlalchemy import text

from src.core.database import SessionLocal
from src.modules.crm.infrastructure.repositories.customer_repository import CustomerRepository
from src.modules.crm.infrastructure.repositories.lead_metrics_repository import LeadRepository
from src.modules.crm.application.services.identity_service import IdentityService
from src.modules.crm.domain.enums import IdentityType, LifecycleStage
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel, CustomerIdentityModel
from src.modules.sales_agent.infrastructure.memory.audit_repository import AuditRepository
from src.core.context import set_tenant_id
# Import all related models so SQLAlchemy can resolve relationships
from src.modules.iam.infrastructure.models.tenant_model import TenantModel  # noqa: F401
from src.modules.scheduling.infrastructure.models.appointment_model import AppointmentModel  # noqa: F401
from src.modules.sales_agent.infrastructure.models.message_model import MessageModel  # noqa: F401


TENANT_ID = UUID("6347e21e-8112-4aa1-80d3-6adaa73bf6f9")


@pytest.fixture
def db():
    session = SessionLocal()
    yield session
    session.rollback()
    session.close()


@pytest.fixture
def cleanup_test_data(db):
    """Clean up test data after each test."""
    test_user_id = f"test_{uuid.uuid4().hex[:8]}"
    yield test_user_id
    # Cleanup: remove test data created during the test
    db.execute(text(
        "DELETE FROM messages WHERE user_id IN "
        "(SELECT id FROM leads WHERE telegram_id = :tid)"
    ), {"tid": test_user_id})
    db.execute(text("DELETE FROM leads WHERE telegram_id = :tid"), {"tid": test_user_id})
    db.execute(text(
        "DELETE FROM customer_identities WHERE value = :tid"
    ), {"tid": test_user_id})
    db.execute(text(
        "DELETE FROM customer_profiles WHERE id IN "
        "(SELECT profile_id FROM customer_identities WHERE value = :tid)"
    ), {"tid": test_user_id})
    db.commit()


class TestStep1_IdentityResolution:
    """Step 1: IdentityType mapping from channel_type string."""

    def test_telegram_maps_to_identity_type(self):
        """channel_type 'telegram' should map to IdentityType.TELEGRAM."""
        channel_type = "telegram"
        identity_type = IdentityType(channel_type)
        assert identity_type == IdentityType.TELEGRAM
        assert identity_type.name == "TELEGRAM"
        assert identity_type.value == "telegram"

    def test_whatsapp_maps_to_identity_type(self):
        channel_type = "whatsapp"
        identity_type = IdentityType(channel_type)
        assert identity_type == IdentityType.WHATSAPP

    def test_unknown_channel_falls_back(self):
        """Unknown channels should fall back to EXTERNAL_ID."""
        try:
            IdentityType("unknown_channel")
            assert False, "Should have raised ValueError"
        except ValueError:
            identity_type = IdentityType.EXTERNAL_ID
            assert identity_type == IdentityType.EXTERNAL_ID


class TestStep2_CustomerProfileCreation:
    """Step 2: get_or_create_customer — creates CustomerProfile + CustomerIdentity."""

    def test_create_new_customer_via_identity_service(self, db, cleanup_test_data):
        """First contact: should create both profile and identity."""
        test_user_id = cleanup_test_data
        set_tenant_id(TENANT_ID)

        customer_repo = CustomerRepository(db)
        identity_service = IdentityService(customer_repo)

        customer, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=IdentityType.TELEGRAM,
            identity_value=test_user_id,
            profile_data={
                "first_name": "Test",
                "last_name": "User",
                "traits": {"source": "telegram"}
            }
        )

        assert customer is not None
        assert customer.full_name == "Test User"
        assert customer.tenant_id == TENANT_ID

        # Verify identity was created
        identity = db.query(CustomerIdentityModel).filter(
            CustomerIdentityModel.value == test_user_id,
            CustomerIdentityModel.tenant_id == TENANT_ID
        ).first()
        assert identity is not None
        assert identity.profile_id == customer.id

    def test_find_existing_customer(self, db, cleanup_test_data):
        """Second contact: should find existing profile, not create duplicate."""
        test_user_id = cleanup_test_data
        set_tenant_id(TENANT_ID)

        customer_repo = CustomerRepository(db)
        identity_service = IdentityService(customer_repo)

        # First call creates
        customer1, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=IdentityType.TELEGRAM,
            identity_value=test_user_id,
            profile_data={"first_name": "Test", "last_name": "User", "traits": {}}
        )

        # Second call should find existing
        customer2, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=IdentityType.TELEGRAM,
            identity_value=test_user_id,
            profile_data={"first_name": "Test", "last_name": "User", "traits": {}}
        )

        assert customer1.id == customer2.id, "Should return same customer, not create duplicate"

    def test_lifecycle_stage_default(self, db, cleanup_test_data):
        """New customer should get SUBSCRIBER lifecycle stage (tests enum compatibility)."""
        test_user_id = cleanup_test_data
        set_tenant_id(TENANT_ID)

        customer_repo = CustomerRepository(db)
        identity_service = IdentityService(customer_repo)

        customer, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=IdentityType.TELEGRAM,
            identity_value=test_user_id,
            profile_data={"first_name": "Test", "last_name": "Enum", "traits": {}}
        )

        # Verify the DB accepted the lifecycle_stage enum value
        profile = db.query(CustomerProfileModel).filter(
            CustomerProfileModel.id == customer.id
        ).first()
        assert profile is not None
        assert profile.lifecycle_stage == LifecycleStage.SUBSCRIBER


class TestStep3_LeadCreation:
    """Step 3: get_active_lead / create_lead — Lead linked to Customer."""

    def test_create_lead_for_new_customer(self, db, cleanup_test_data):
        """Should create lead linked to customer with telegram_id set."""
        test_user_id = cleanup_test_data
        set_tenant_id(TENANT_ID)

        customer_repo = CustomerRepository(db)
        identity_service = IdentityService(customer_repo)
        lead_repo = LeadRepository(db)

        customer, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=IdentityType.TELEGRAM,
            identity_value=test_user_id,
            profile_data={"first_name": "Test", "last_name": "Lead", "traits": {}}
        )

        # Simulate orchestrator flow: get_active_lead -> create_lead
        user = lead_repo.get_active_lead(customer.id)
        assert user is None, "No lead should exist yet"

        user = lead_repo.create_lead(
            customer_id=customer.id,
            channel="telegram",
            channel_user_id=test_user_id
        )

        assert user is not None
        assert user.customer_id == customer.id
        assert user.telegram_id == test_user_id

    def test_duplicate_lead_returns_existing(self, db, cleanup_test_data):
        """Creating lead with same telegram_id should return existing, not crash."""
        test_user_id = cleanup_test_data
        set_tenant_id(TENANT_ID)

        customer_repo = CustomerRepository(db)
        identity_service = IdentityService(customer_repo)
        lead_repo = LeadRepository(db)

        customer, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=IdentityType.TELEGRAM,
            identity_value=test_user_id,
            profile_data={"first_name": "Test", "last_name": "Dup", "traits": {}}
        )

        # Create first lead
        lead1 = lead_repo.create_lead(
            customer_id=customer.id,
            channel="telegram",
            channel_user_id=test_user_id
        )

        # Create second lead with same telegram_id — should return existing
        lead2 = lead_repo.create_lead(
            customer_id=customer.id,
            channel="telegram",
            channel_user_id=test_user_id
        )

        assert lead1.id == lead2.id, "Should return same lead, not create duplicate"


class TestStep4_AuditLogging:
    """Step 4: Message logging in audit repository."""

    def test_log_and_retrieve_message(self, db, cleanup_test_data):
        """Should log user message and retrieve it."""
        test_user_id = cleanup_test_data
        set_tenant_id(TENANT_ID)

        customer_repo = CustomerRepository(db)
        identity_service = IdentityService(customer_repo)
        lead_repo = LeadRepository(db)
        audit_repo = AuditRepository(db)

        customer, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=IdentityType.TELEGRAM,
            identity_value=test_user_id,
            profile_data={"first_name": "Test", "last_name": "Audit", "traits": {}}
        )

        user = lead_repo.create_lead(
            customer_id=customer.id,
            channel="telegram",
            channel_user_id=test_user_id
        )

        # Log message
        audit_repo.log_message(
            user_id=user.id,
            role="user",
            content="Hola, quiero información",
            channel="telegram"
        )

        # Retrieve
        last_msg = audit_repo.get_last_message(user.id)
        assert last_msg is not None
        assert last_msg.content == "Hola, quiero información"

        history = audit_repo.get_chat_history(user.id, limit=10)
        assert len(history) >= 1


class TestStep5_FullFlowIntegration:
    """Step 5: Full flow simulation (everything before agent invocation)."""

    def test_complete_pre_agent_flow(self, db, cleanup_test_data):
        """
        Simulates the full process_chat_flow up to agent invocation:
        1. Map channel to IdentityType
        2. get_or_create_customer
        3. get_active_lead / create_lead
        4. Log message
        5. Get chat history
        All without hitting the LLM.
        """
        test_user_id = cleanup_test_data
        set_tenant_id(TENANT_ID)

        # Simulate incoming message metadata
        channel_type = "telegram"
        metadata = {
            "first_name": "Integration",
            "last_name": "Test",
            "username": "testbot",
            "language_code": "es",
            "source": "telegram",
        }

        # Step 1: Map channel to IdentityType
        identity_type = IdentityType(channel_type)
        assert identity_type == IdentityType.TELEGRAM

        # Step 2: Get or Create Customer
        customer_repo = CustomerRepository(db)
        identity_service = IdentityService(customer_repo)

        customer, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=identity_type,
            identity_value=test_user_id,
            profile_data={
                "first_name": metadata.get("first_name"),
                "last_name": metadata.get("last_name"),
                "traits": metadata
            }
        )
        assert customer is not None
        assert customer.full_name == "Integration Test"

        # Step 3: Get or Create Lead
        lead_repo = LeadRepository(db)
        user = lead_repo.get_active_lead(customer.id)
        if not user:
            user = lead_repo.create_lead(
                customer_id=customer.id,
                channel=channel_type,
                channel_user_id=test_user_id
            )
        assert user is not None
        assert user.telegram_id == test_user_id

        # Step 4: Log message
        audit_repo = AuditRepository(db)
        audit_repo.log_message(
            user_id=user.id,
            role="user",
            content="hola amiga",
            channel=channel_type
        )

        # Step 5: Session state
        last_msg = audit_repo.get_last_message(user.id)
        assert last_msg is not None

        history = audit_repo.get_chat_history(user.id, limit=10)
        assert len(history) >= 1

        # Step 6: Simulate second message (idempotency)
        customer2, _ = identity_service.get_or_create_customer(
            tenant_id=TENANT_ID,
            identity_type=identity_type,
            identity_value=test_user_id,
            profile_data={
                "first_name": metadata.get("first_name"),
                "last_name": metadata.get("last_name"),
                "traits": metadata
            }
        )
        assert customer2.id == customer.id, "Second message should find same customer"

        user2 = lead_repo.get_active_lead(customer2.id)
        assert user2 is not None
        assert user2.id == user.id, "Second message should find same lead"
