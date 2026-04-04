import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import sys
from unittest.mock import MagicMock
import uuid

# --- Mock missing optional dependencies for test environment ---
# passlib is only used at runtime for password hashing in IAM; not needed for tests.
for mod_name in ("passlib", "passlib.context", "passlib.hash"):
    if mod_name not in sys.modules:
        sys.modules[mod_name] = MagicMock()

from src.shared.domain.base_entity import Base

# --- Monkeypatch PostgreSQL Types for SQLite ---
from sqlalchemy.dialects import postgresql
from sqlalchemy.types import TypeDecorator, CHAR, Text

class MockJSONB(TypeDecorator):
    """SQLite doesn't support JSONB, so we map it to standard JSON or String"""
    impl = Text
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.JSONB())
        else:
            return dialect.type_descriptor(Text())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        import json
        return json.dumps(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        import json
        try:
            return json.loads(value)
        except:
            return {}

class MockUUID(TypeDecorator):
    """SQLite doesn't support UUID native type, map to CHAR(36)"""
    impl = CHAR(36)
    cache_ok = True

    def __init__(self, as_uuid=True):
        self.as_uuid = as_uuid
        super().__init__()

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(postgresql.UUID(as_uuid=self.as_uuid))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if self.as_uuid:
            return uuid.UUID(value)
        return value

# Apply patches
postgresql.JSONB = MockJSONB
postgresql.UUID = MockUUID

# --- Fixtures ---

@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    
    # Import all models to ensure they are registered and relationships can be resolved
    try:
        from src.modules.iam.infrastructure.models.tenant_model import TenantModel
        from src.modules.crm.infrastructure.models.lead_model import LeadModel
        from src.modules.crm.infrastructure.models.lifecycle_transition_model import LifecycleTransitionModel
        from src.modules.sales_agent.infrastructure.models.channel_model import ChannelConnectionModel
        from src.modules.sales_agent.infrastructure.models.message_model import MessageModel
        from src.modules.scheduling.infrastructure.models.appointment_model import AppointmentModel
        from src.modules.crm.infrastructure.models.sale_model import SaleModel
        from src.modules.offer.infrastructure.models.product_model import ProductModel
        from src.modules.sales_agent.infrastructure.models.agent_state_checkpoint_model import AgentStateCheckpointModel
        from src.modules.brand.infrastructure.models.avatar_model import AvatarModel
        from src.modules.brand.infrastructure.models.extraction_trace_model import BrandExtractionTrace
        from src.modules.tenant_domains.infrastructure.models.tenant_domain_model import TenantDomainModel  # noqa: F401
        from src.modules.landing.infrastructure.models.landing_model import LandingPageModel  # noqa: F401
    except ImportError as e:
        print(f"Warning: Could not import some models: {e}")
    
    # Create tables
    Base.metadata.create_all(bind=engine)
    
    yield engine
    
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()

    yield session

    session.close()
    transaction.rollback()
    connection.close()
