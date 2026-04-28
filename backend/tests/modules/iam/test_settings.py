"""Tests for IAM settings endpoints."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.api.settings import router
from src.modules.iam.domain.user import User


def _make_user(tenant_id: uuid.UUID) -> User:
    return User(
        id=uuid.uuid4(),
        full_name="Alice Test",
        email="alice@example.com",
        clerk_id="clerk_test",
        role="admin",
        is_active=True,
        tenant_id=tenant_id,
    )


@pytest.fixture
def app(db, tenant_id):
    user = _make_user(tenant_id)
    _app = FastAPI()
    _app.include_router(router, prefix="/settings")
    _app.dependency_overrides[get_db] = lambda: db
    _app.dependency_overrides[get_current_user] = lambda: user
    return _app


@pytest.fixture
def client(app):
    return TestClient(app)


# ---------------------------------------------------------------------------
# General Settings
# ---------------------------------------------------------------------------


class TestGeneralSettings:
    def test_get_general_returns_200(self, client, seed_tenant):
        resp = client.get("/settings/general")
        assert resp.status_code == 200
        body = resp.json()
        assert "default_currency" in body
        assert "timezone" in body

    def test_get_general_tenant_not_found_returns_404(self, db):
        user = _make_user(uuid.uuid4())  # random tenant not in db
        app = FastAPI()
        app.include_router(router, prefix="/settings")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        resp = TestClient(app).get("/settings/general")
        assert resp.status_code == 404

    def test_patch_general_updates_currency(self, client, seed_tenant):
        resp = client.patch("/settings/general", json={"default_currency": "PEN"})
        assert resp.status_code == 200
        assert resp.json()["default_currency"] == "PEN"

    def test_patch_general_updates_timezone(self, client, seed_tenant):
        resp = client.patch("/settings/general", json={"timezone": "America/Lima"})
        assert resp.status_code == 200
        assert resp.json()["timezone"] == "America/Lima"

    def test_patch_general_partial_update_preserves_other_fields(self, client, seed_tenant):
        client.patch("/settings/general", json={"default_currency": "MXN"})
        resp = client.patch("/settings/general", json={"timezone": "America/Mexico_City"})
        assert resp.status_code == 200
        assert resp.json()["default_currency"] == "MXN"

    def test_get_general_no_tenant_id_returns_400(self, db):
        user = User(
            id=uuid.uuid4(),
            full_name="No Tenant",
            email="notenant@x.com",
            clerk_id="c1",
            role="user",
            is_active=True,
        )
        app = FastAPI()
        app.include_router(router, prefix="/settings")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        resp = TestClient(app).get("/settings/general")
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# AI Settings
# ---------------------------------------------------------------------------


class TestAISettings:
    def test_get_ai_returns_200(self, client, seed_tenant):
        resp = client.get("/settings/ai")
        assert resp.status_code == 200
        assert "can_use_platform_keys" in resp.json()

    def test_patch_ai_updates_key(self, client, seed_tenant):
        resp = client.patch("/settings/ai", json={"openai_api_key": "sk-test-123"})
        assert resp.status_code == 200
        assert resp.json()["openai_api_key"] == "sk-test-123"

    def test_patch_ai_multiple_keys(self, client, seed_tenant):
        resp = client.patch(
            "/settings/ai",
            json={"deepseek_api_key": "ds-key", "kimi_api_key": "kimi-key"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["deepseek_api_key"] == "ds-key"
        assert body["kimi_api_key"] == "kimi-key"

    def test_get_ai_tenant_not_found_returns_404(self, db):
        user = _make_user(uuid.uuid4())
        app = FastAPI()
        app.include_router(router, prefix="/settings")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        resp = TestClient(app).get("/settings/ai")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------


class TestProfileSettings:
    def test_get_profile_returns_200(self, client, seed_tenant):
        resp = client.get("/settings/profile")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "alice@example.com"
        assert "tenant" in body

    def test_get_profile_no_tenant_returns_user_without_tenant(self, db):
        user = User(
            id=uuid.uuid4(),
            full_name="No Tenant",
            email="notenant@x.com",
            clerk_id="c1",
            role="user",
            is_active=True,
        )
        app = FastAPI()
        app.include_router(router, prefix="/settings")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        resp = TestClient(app).get("/settings/profile")
        assert resp.status_code == 200
        assert resp.json()["tenant"] is None


# ---------------------------------------------------------------------------
# Webhook Settings
# ---------------------------------------------------------------------------


class TestWebhookSettings:
    def test_get_webhook_returns_200(self, client, seed_tenant):
        with patch("src.modules.iam.api.settings.app_settings") as mock_cfg:
            mock_cfg.API_DOMAIN = "localhost:8000"
            resp = client.get("/settings/webhook")
        assert resp.status_code == 200
        assert "webhook_url" in resp.json()

    def test_get_webhook_missing_api_domain_returns_500(self, client, seed_tenant):
        with patch("src.modules.iam.api.settings.app_settings") as mock_cfg:
            mock_cfg.API_DOMAIN = None
            resp = client.get("/settings/webhook")
        assert resp.status_code == 500

    def test_regenerate_webhook_secret_returns_new_secret(self, client, seed_tenant):
        with patch("src.modules.iam.api.settings.app_settings") as mock_cfg:
            mock_cfg.API_DOMAIN = "api.example.com"
            resp = client.post("/settings/webhook/regenerate")
        assert resp.status_code == 200
        body = resp.json()
        assert body["webhook_secret"] is not None
        assert body["webhook_secret"].startswith("sk_live_")

    def test_regenerate_generates_new_secret_each_call(self, client, seed_tenant):
        with patch("src.modules.iam.api.settings.app_settings") as mock_cfg:
            mock_cfg.API_DOMAIN = "api.example.com"
            first = client.post("/settings/webhook/regenerate").json()["webhook_secret"]
            second = client.post("/settings/webhook/regenerate").json()["webhook_secret"]
        assert first != second


# ---------------------------------------------------------------------------
# Team Members
# ---------------------------------------------------------------------------


class TestTeamSettings:
    def test_get_team_returns_200(self, client, seed_user_tenant_link):
        resp = client.get("/settings/team")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_get_team_member_has_required_fields(self, client, seed_user_tenant_link):
        resp = client.get("/settings/team")
        member = resp.json()[0]
        for field in ("id", "full_name", "email", "role", "is_active"):
            assert field in member

    def test_create_team_member_email_exists_returns_400(self, client, seed_user_tenant_link):
        """Email already in system → 400."""
        resp = client.post(
            "/settings/team",
            json={
                "email": "alice@example.com",
                "full_name": "Alice Dupe",
                "password": "Test1234!",
            },
        )
        assert resp.status_code == 400

    def test_create_team_member_limit_exceeded_returns_403(self, client, db, seed_user_tenant_link, tenant_id):
        """Already 1 member, add 2 more to hit limit of 3, then fail."""
        from src.modules.iam.infrastructure.models.user_model import UserModel
        from src.modules.iam.infrastructure.models.user_tenant_model import UserTenantModel

        for i in range(2):
            u = UserModel(
                id=uuid.uuid4(),
                full_name=f"Extra {i}",
                email=f"extra{i}@x.com",
                clerk_id=f"clerk_extra_{i}",
                role="member",
                is_active=True,
            )
            db.add(u)
            db.flush()
            db.add(UserTenantModel(user_id=u.id, tenant_id=tenant_id, role="member"))
        db.commit()

        with patch("src.modules.iam.api.settings.ClerkService") as mock_clerk_cls:
            mock_clerk_cls.return_value.create_user.return_value = {"id": "new_clerk_id"}
            mock_clerk_cls.return_value.update_user_metadata.return_value = None
            resp = client.post(
                "/settings/team",
                json={"email": "new@x.com", "full_name": "New", "password": "Test1234!"},
            )
        assert resp.status_code == 403

    def test_get_team_no_tenant_id_returns_400(self, db):
        user = User(
            id=uuid.uuid4(),
            full_name="No Tenant",
            email="notenant@x.com",
            clerk_id="c1",
            role="user",
            is_active=True,
        )
        app = FastAPI()
        app.include_router(router, prefix="/settings")
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user
        resp = TestClient(app).get("/settings/team")
        assert resp.status_code == 400
