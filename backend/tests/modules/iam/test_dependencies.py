"""Tests for IAM dependency functions."""

import uuid
from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.iam.api.dependencies import (
    _resolve_email_from_clerk_api,
    _resolve_name,
    _sync_clerk_fields,
    get_current_tenant_id,
    get_current_user,
    get_optional_current_user,
    get_user_from_token,
)
from src.modules.iam.application.auth import verify_clerk_token
from src.modules.iam.domain.user import User
from src.modules.iam.infrastructure.models.user_model import UserModel

# ---------------------------------------------------------------------------
# Helper: minimal FastAPI app for HTTP-level tests
# ---------------------------------------------------------------------------


def _make_app(db_session, token_payload: dict):
    """Build a test app with `get_current_user` dep exercised end-to-end."""
    from fastapi import APIRouter

    from src.modules.iam.api.routers.auth_router import router as auth_router

    app = FastAPI()

    # Override JWT verification so tests don't need a real Clerk JWKS
    app.dependency_overrides[verify_clerk_token] = lambda: token_payload
    app.dependency_overrides[get_db] = lambda: db_session
    app.include_router(auth_router, prefix="/users")
    return TestClient(app)


# ---------------------------------------------------------------------------
# Unit tests: _resolve_name
# ---------------------------------------------------------------------------


class TestResolveName:
    def test_uses_name_claim_first(self):
        payload = {"name": "Alice Test", "given_name": "X", "family_name": "Y"}
        assert _resolve_name(payload, None) == "Alice Test"

    def test_falls_back_to_given_family(self):
        payload = {"given_name": "Bob", "family_name": "Smith"}
        assert _resolve_name(payload, None) == "Bob Smith"

    def test_strips_whitespace_when_only_given(self):
        payload = {"given_name": "Alice", "family_name": ""}
        assert _resolve_name(payload, None) == "Alice"

    def test_uses_clerk_data_as_last_fallback(self):
        clerk_data = {"first_name": "Carol", "last_name": "Jones"}
        assert _resolve_name({}, clerk_data) == "Carol Jones"

    def test_returns_none_when_nothing(self):
        assert _resolve_name({}, None) is None

    def test_returns_none_when_clerk_data_also_empty(self):
        assert _resolve_name({}, {"first_name": "", "last_name": ""}) is None


# ---------------------------------------------------------------------------
# Unit tests: _sync_clerk_fields
# ---------------------------------------------------------------------------


class TestSyncClerkFields:
    def _make_user_orm(self, db, clerk_id="old_clerk", full_name="Old Name", email="u@x.com"):
        user = UserModel(
            id=uuid.uuid4(),
            full_name=full_name,
            email=email,
            clerk_id=clerk_id,
            role="user",
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    def test_updates_clerk_id_when_changed(self, db):
        user_orm = self._make_user_orm(db, clerk_id="old_id")
        _sync_clerk_fields(db, user_orm, "new_id", None, "u@x.com")
        assert user_orm.clerk_id == "new_id"

    def test_updates_full_name_when_changed(self, db):
        user_orm = self._make_user_orm(db, full_name="Old Name")
        _sync_clerk_fields(db, user_orm, "same_clerk", "New Name", "u@x.com")
        assert user_orm.full_name == "New Name"

    def test_no_commit_when_nothing_changed(self, db):
        user_orm = self._make_user_orm(db, clerk_id="stable", full_name="Stable")
        db_mock = MagicMock(wraps=db)
        _sync_clerk_fields(db_mock, user_orm, "stable", "Stable", "u@x.com")
        db_mock.add.assert_not_called()

    def test_does_not_overwrite_name_with_none(self, db):
        user_orm = self._make_user_orm(db, full_name="Keep Me")
        _sync_clerk_fields(db, user_orm, "same_clerk", None, "u@x.com")
        assert user_orm.full_name == "Keep Me"


# ---------------------------------------------------------------------------
# Unit tests: _resolve_email_from_clerk_api
# ---------------------------------------------------------------------------


class TestResolveEmailFromClerkApi:
    def test_returns_primary_email(self):
        clerk_resp = {
            "primary_email_address_id": "em_1",
            "email_addresses": [
                {"id": "em_1", "email_address": "alice@x.com"},
                {"id": "em_2", "email_address": "other@x.com"},
            ],
        }
        with patch("src.modules.iam.api.dependencies.httpx.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = clerk_resp
            email, data = _resolve_email_from_clerk_api("user_1", "sk_secret")
        assert email == "alice@x.com"
        assert data == clerk_resp

    def test_falls_back_to_first_email_when_primary_missing(self):
        clerk_resp = {
            "primary_email_address_id": "em_999",
            "email_addresses": [{"id": "em_1", "email_address": "first@x.com"}],
        }
        with patch("src.modules.iam.api.dependencies.httpx.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = clerk_resp
            email, _ = _resolve_email_from_clerk_api("user_1", "sk_secret")
        assert email == "first@x.com"

    def test_returns_none_on_non_200(self):
        with patch("src.modules.iam.api.dependencies.httpx.get") as mock_get:
            mock_get.return_value.status_code = 404
            email, data = _resolve_email_from_clerk_api("user_1", "sk_secret")
        assert email is None
        assert data is None

    def test_returns_none_on_exception(self):
        with patch(
            "src.modules.iam.api.dependencies.httpx.get",
            side_effect=ConnectionError("timeout"),
        ):
            email, data = _resolve_email_from_clerk_api("user_1", "sk_secret")
        assert email is None
        assert data is None


# ---------------------------------------------------------------------------
# HTTP tests: get_user_from_token / get_current_user
# ---------------------------------------------------------------------------


class TestGetUserFromToken:
    def test_valid_token_with_email_returns_user(self, db, seed_user, user_id):
        payload = {"sub": "clerk_alice_001", "email": "alice@example.com"}
        client = _make_app(db, payload)
        resp = client.get("/users/me")
        assert resp.status_code == 200
        body = resp.json()
        assert body["email"] == "alice@example.com"

    def test_token_missing_email_resolves_via_clerk_api(self, db, seed_user):
        payload = {"sub": "clerk_alice_001"}  # no email claim
        clerk_resp = {
            "primary_email_address_id": "em_1",
            "email_addresses": [{"id": "em_1", "email_address": "alice@example.com"}],
        }
        with (
            patch("src.modules.iam.api.dependencies.httpx.get") as mock_get,
            patch.dict("os.environ", {"CLERK_SECRET_KEY": "sk_test"}),
        ):
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = clerk_resp
            client = _make_app(db, payload)
            resp = client.get("/users/me")
        assert resp.status_code == 200

    def test_token_no_email_no_fallback_returns_401(self, db, seed_user):
        """No email claim + no CLERK_SECRET_KEY → 401."""
        payload = {"sub": "clerk_alice_001"}
        with patch.dict("os.environ", {}, clear=True):  # ensure no CLERK_SECRET_KEY
            client = _make_app(db, payload)
            resp = client.get("/users/me")
        assert resp.status_code == 401

    def test_user_not_in_db_returns_403(self, db):
        payload = {"sub": "clerk_ghost", "email": "ghost@x.com"}
        client = _make_app(db, payload)
        resp = client.get("/users/me")
        assert resp.status_code == 403


class TestGetCurrentUser:
    def _app_with_user_dep(self, db_session, user: User):
        """App overriding get_user_from_token directly to inject a resolved User."""
        from fastapi import APIRouter

        app = FastAPI()
        app.dependency_overrides[verify_clerk_token] = dict
        app.dependency_overrides[get_db] = lambda: db_session
        app.dependency_overrides[get_user_from_token] = lambda: user

        router = APIRouter()

        @router.get("/test")
        def _endpoint(u: User = __import__("fastapi").Depends(get_current_user)):
            return {"tenant_id": str(u.tenant_id), "role": u.role}

        app.include_router(router)
        return TestClient(app)

    def test_resolves_tenant_from_x_tenant_id_header(self, db, seed_user_tenant_link, user_id, tenant_id):
        from src.modules.iam.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        client = self._app_with_user_dep(db, user)
        resp = client.get("/test", headers={"X-Tenant-ID": str(tenant_id)})
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == str(tenant_id)

    def test_invalid_tenant_id_not_member_returns_403(self, db, seed_user, user_id):
        from src.modules.iam.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        client = self._app_with_user_dep(db, user)
        resp = client.get("/test", headers={"X-Tenant-ID": str(uuid.uuid4())})
        assert resp.status_code == 403

    def test_resolves_tenant_by_slug(self, db, seed_user_tenant_link, seed_tenant, user_id):
        from src.modules.iam.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        client = self._app_with_user_dep(db, user)
        resp = client.get("/test", headers={"X-Tenant-ID": "test-tenant"})
        assert resp.status_code == 200

    def test_invalid_slug_raises_400(self, db, seed_user, user_id):
        from src.modules.iam.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        client = self._app_with_user_dep(db, user)
        resp = client.get("/test", headers={"X-Tenant-ID": "nonexistent-slug"})
        assert resp.status_code == 400

    def test_no_header_uses_default_tenant(self, db, seed_user_tenant_link, user_id, tenant_id):
        from src.modules.iam.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        client = self._app_with_user_dep(db, user)
        resp = client.get("/test")  # no X-Tenant-ID
        assert resp.status_code == 200
        assert resp.json()["tenant_id"] == str(tenant_id)

    def test_no_header_no_tenant_returns_403(self, db, seed_user, user_id):
        """User exists but has no tenant link → 403."""
        from src.modules.iam.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        client = self._app_with_user_dep(db, user)
        resp = client.get("/test")
        assert resp.status_code == 403


class TestGetCurrentTenantId:
    def test_returns_tenant_id_string(self, db, seed_user_tenant_link, user_id, tenant_id):
        from fastapi import APIRouter

        from src.modules.iam.infrastructure.repositories.user_repository import UserRepository

        repo = UserRepository(db)
        user = repo.get_by_id(user_id)
        user.tenant_id = tenant_id

        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db
        app.dependency_overrides[get_current_user] = lambda: user

        rt = APIRouter()

        @rt.get("/tid")
        def _endpoint(tid: str = __import__("fastapi").Depends(get_current_tenant_id)):
            return {"tid": tid}

        app.include_router(rt)
        resp = TestClient(app).get("/tid")
        assert resp.status_code == 200
        assert resp.json()["tid"] == str(tenant_id)


class TestGetOptionalCurrentUser:
    def test_no_credentials_returns_none(self, db):
        app = FastAPI()
        app.dependency_overrides[get_db] = lambda: db

        from fastapi import APIRouter

        rt = APIRouter()

        @rt.get("/opt")
        def _endpoint(u=__import__("fastapi").Depends(get_optional_current_user)):
            return {"user": u}

        app.include_router(rt)
        resp = TestClient(app).get("/opt")
        assert resp.status_code == 200
        assert resp.json()["user"] is None

    def test_invalid_token_returns_none(self, db):
        with patch("src.modules.iam.api.dependencies.verify_token_payload", side_effect=Exception("bad")):
            from fastapi import APIRouter

            app = FastAPI()
            app.dependency_overrides[get_db] = lambda: db

            rt = APIRouter()

            @rt.get("/opt2")
            def _endpoint(u=__import__("fastapi").Depends(get_optional_current_user)):
                return {"user": u}

            app.include_router(rt)
            resp = TestClient(app).get("/opt2", headers={"Authorization": "Bearer fake"})
            assert resp.json()["user"] is None
