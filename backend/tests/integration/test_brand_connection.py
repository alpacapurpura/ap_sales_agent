import sys
import os
import uuid
import json
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine, Column, String, Boolean
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import JSONB, UUID
from fastapi.testclient import TestClient

# --- MOCK SETUP ---
# Mock dependencies to avoid importing the whole backend stack
mock_deps = MagicMock()
sys.modules["src.modules.iam.api.dependencies"] = mock_deps
sys.modules["src.shared.infrastructure.db.database"] = mock_deps
sys.modules["src.config"] = MagicMock()
sys.modules["src.config"].settings = MagicMock()

# --- DB SETUP ---
Base = declarative_base()

class MockTenantModel(Base):
    __tablename__ = "tenants"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, default="Test Tenant")
    slug = Column(String, default="test-tenant")
    config_json = Column(String, default="{}") # SQLite doesn't support JSONB natively easily in this context without extensions
    openai_api_key = Column(String, nullable=True)
    gemini_api_key = Column(String, nullable=True)
    can_use_platform_keys = Column(Boolean, default=False)
    webhook_secret = Column(String, nullable=True)

# Patch the real models
with patch("src.modules.iam.infrastructure.models.TenantModel", MockTenantModel):
    from src.modules.landing.brand.api.router import router
    from src.modules.landing.brand.domain.models import BrandSettings

# --- APP SETUP ---
from fastapi import FastAPI
app = FastAPI()
app.include_router(router, prefix="/api/v1/settings")

client = TestClient(app)

# --- TEST ---
def test_brand_connection():
    # Setup DB
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    
    # Create Tenant
    tenant_id = str(uuid.uuid4())
    tenant = MockTenantModel(id=tenant_id, config_json=json.dumps({}))
    db.add(tenant)
    db.commit()

    # Mock Dependency Overrides
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
            
    def override_get_current_user():
        user = MagicMock()
        user.tenant_id = tenant_id
        return user

    app.dependency_overrides[mock_deps.get_db] = override_get_db
    app.dependency_overrides[mock_deps.get_current_user] = override_get_current_user # Note: In real code it's get_current_user

    # 1. TEST GET (Initial)
    response = client.get("/api/v1/settings/brand")
    assert response.status_code == 200
    data = response.json()
    assert data == {} # Should be empty initially

    # 2. TEST PATCH (Update)
    payload = {
        "identity": {
            "primary_color": "#FF0000",
            "accent_color": "#00FF00",
            "design_style": "Modern"
        },
        "contact": {
            "email": "test@brand.com"
        }
    }
    response = client.patch("/api/v1/settings/brand", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["identity"]["primary_color"] == "#FF0000"
    assert data["contact"]["email"] == "test@brand.com"

    # 3. TEST PERSISTENCE (Get again)
    response = client.get("/api/v1/settings/brand")
    assert response.status_code == 200
    data = response.json()
    assert data["identity"]["primary_color"] == "#FF0000"

    print("✅ Brand Studio Connection Tests Passed!")

if __name__ == "__main__":
    test_brand_connection()
