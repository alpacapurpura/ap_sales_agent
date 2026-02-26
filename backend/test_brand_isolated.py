import sys
import uuid
from unittest.mock import MagicMock
from sqlalchemy import Column, String, Boolean, DateTime, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.pool import StaticPool
from sqlalchemy.ext.compiler import compiles

# 1. Define Mock ORM Models
Base = declarative_base()

# Fix JSONB for SQLite
def compile_jsonb(type_, compiler, **kw):
    return compiler.visit_JSON(type_, **kw)
compiles(JSONB, 'sqlite')(compile_jsonb)

class MockTenantModel(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, default="Test Tenant")
    slug = Column(String, default="test-tenant")
    config_json = Column(JSONB, default={})
    openai_api_key = Column(String, nullable=True)
    gemini_api_key = Column(String, nullable=True)
    can_use_platform_keys = Column(Boolean, default=False)
    webhook_secret = Column(String, nullable=True)

class MockUserModel(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String)
    full_name = Column(String)
    # We add tenant_id here to simplify relationship handling in mocks if needed
    # In real code it's M2M but for this specific test usually we mock the user object returned by dependency
    
class MockUserTenantModel(Base):
    __tablename__ = "user_tenants"
    user_id = Column(UUID(as_uuid=True), primary_key=True)
    tenant_id = Column(UUID(as_uuid=True), primary_key=True)
    role = Column(String, default="member")

# 2. Mock Modules BEFORE importing settings
# We need to mock 'src.modules.iam.infrastructure.models' to return our Mock models
mock_infra = MagicMock()
mock_infra.UserModel = MockUserModel
mock_infra.TenantModel = MockTenantModel
mock_infra.UserTenantModel = MockUserTenantModel

sys.modules["src.modules.iam.infrastructure.models"] = mock_infra
sys.modules["src.modules.iam.infrastructure.models.user"] = MagicMock(UserModel=MockUserModel)
sys.modules["src.modules.iam.infrastructure.models.tenant"] = MagicMock(TenantModel=MockTenantModel)
sys.modules["src.modules.iam.infrastructure.models.user_tenant"] = MagicMock(UserTenantModel=MockUserTenantModel)

# Mock Clerk Service
sys.modules["src.shared.infrastructure.external.clerk"] = MagicMock()

# Mock dependencies if they are imported from elsewhere
# settings.py imports:
# from src.modules.iam.api.dependencies import get_current_user
# from src.shared.infrastructure.db.database import get_db
# We can let them be imported if the files exist and don't cause side effects,
# or mock them. `dependencies.py` imports a lot. Better mock it.
mock_deps = MagicMock()
def mock_get_current_user(): pass
def mock_get_db(): pass
mock_deps.get_current_user = mock_get_current_user
mock_deps.get_db = mock_get_db
sys.modules["src.modules.iam.api.dependencies"] = mock_deps
sys.modules["src.shared.infrastructure.db.database"] = mock_deps # Reusing mock for get_db

# We need pydantic models to be real.
# Ensure they are not mocked if we want validation.
# We will import settings.py now.
# Note: settings.py imports Tenant from domain.
# We want to intercept this import if we want to fix the bug in the test environment,
# OR we want to let it fail to prove the bug.
# Let's try to let it fail first. 
# But wait, if we let it import real Tenant (Pydantic), and run db.query(Tenant), it will crash.
# We WANT to fix it in the code, but first verify.
# To verify, we can just run the test and expect failure.
# However, if we want to write a script that runs and fixes, we should probably just fix the code.
# The user asked to "Audit... Create test script... Run it and fix errors."
# So catching the error is part of the process.

# But there is a catch: settings.py imports `src.config`.
sys.modules["src.config"] = MagicMock()
sys.modules["src.config"].settings = MagicMock()

# Now import
try:
    from src.modules.landing.brand.api.router import router
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

from fastapi import FastAPI
from fastapi.testclient import TestClient

# 3. Setup App and Database
app = FastAPI()
app.include_router(router, prefix="/api/v1/settings")

SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

# 4. Overrides
tenant_id = uuid.uuid4()
user_id = uuid.uuid4()

def override_get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()

# We need a User object that behaves like the one in settings.py
# In settings.py: current_user.tenant_id
from pydantic import BaseModel
class MockUser(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str
    tenant_id: uuid.UUID
    role: str

def override_get_current_user():
    return MockUser(
        id=user_id,
        email="test@example.com",
        full_name="Test User",
        tenant_id=tenant_id,
        role="admin"
    )

app.dependency_overrides[mock_deps.get_db] = override_get_db
app.dependency_overrides[mock_deps.get_current_user] = override_get_current_user

client = TestClient(app)

def setup_data():
    db = SessionLocal()
    tenant = MockTenantModel(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={
            "brand_settings": {
                "identity": {
                    "primary_color": "#000000",
                    "accent_color": "#FFFFFF",
                    "design_style": "Minimal",
                    "background_color": "#FFFFFF",
                    "text_primary_color": "#000000",
                    "text_on_primary": "#FFFFFF"
                },
                "strategy": {
                    "value_proposition": "ValProp",
                    "target_audience": "Audience",
                    "differentiation": "Diff",
                    "offerings": ["Offer1"]
                }
            }
        }
    )
    db.add(tenant)
    db.commit()
    db.close()

def run_tests():
    print("--- Starting Isolated Tests ---")
    setup_data()

    # 1. GET /brand
    # This might fail if the code uses db.query(Tenant) where Tenant is Pydantic
    print("\n[TEST] GET /api/v1/settings/brand")
    try:
        response = client.get("/api/v1/settings/brand")
        if response.status_code == 200:
            print("SUCCESS: Retrieved brand settings.")
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

    # 2. PATCH /brand
    print("\n[TEST] PATCH /api/v1/settings/brand")
    payload = {
        "identity": {
            "primary_color": "#FF0000",
            "accent_color": "#00FF00",
            "design_style": "Bold",
            "background_color": "#FFFFFF",
            "text_primary_color": "#000000",
            "text_on_primary": "#FFFFFF"
        }
    }
    try:
        response = client.patch("/api/v1/settings/brand", json=payload)
        if response.status_code == 200:
            print("SUCCESS: Updated brand settings.")
            data = response.json()
            # Check strategy
            if data.get("strategy") is None:
                print("ISSUE: Strategy was wiped out!")
            else:
                print("SUCCESS: Strategy preserved.")
        else:
            print(f"FAILED: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

if __name__ == "__main__":
    run_tests()
