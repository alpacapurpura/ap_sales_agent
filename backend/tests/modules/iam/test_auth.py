"""Tests for verify_token_payload — valid JWT, expired, missing claims, misconfig."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import HTTPException


class TestVerifyTokenPayload:
    """Unit tests for auth.verify_token_payload using mocked JWKS client."""

    def _make_payload(self, **overrides) -> dict:
        base = {
            "sub": "user_clerk_abc123",
            "email": "test@example.com",
            "name": "Test User",
            "iat": 1700000000,
            "exp": 9999999999,
        }
        base.update(overrides)
        return base

    def test_valid_token_returns_payload(self):
        """A well-formed, valid JWT returns its decoded payload."""
        expected_payload = self._make_payload()

        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")

        with (
            patch("luana_core_iam.application.auth.jwks_client", mock_jwks),
            patch(
                "luana_core_iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
            patch("jwt.decode", return_value=expected_payload),
        ):
            from luana_core_iam.application.auth import verify_token_payload

            result = verify_token_payload("fake.jwt.token")

        assert result["email"] == "test@example.com"
        assert result["sub"] == "user_clerk_abc123"

    def test_expired_token_raises_401(self):
        """An expired JWT must raise HTTPException with status 401."""
        import jwt as pyjwt

        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")

        with (
            patch("luana_core_iam.application.auth.jwks_client", mock_jwks),
            patch(
                "luana_core_iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
            patch(
                "jwt.decode",
                side_effect=pyjwt.exceptions.ExpiredSignatureError("Token expired"),
            ),
        ):
            from luana_core_iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("expired.jwt.token")

        assert exc_info.value.status_code == 401
        assert "Invalid Token" in exc_info.value.detail or "expired" in exc_info.value.detail.lower()

    def test_invalid_signature_raises_401(self):
        """A token with a bad signature must raise HTTPException 401."""
        import jwt as pyjwt

        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")

        with (
            patch("luana_core_iam.application.auth.jwks_client", mock_jwks),
            patch(
                "luana_core_iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
            patch(
                "jwt.decode",
                side_effect=pyjwt.exceptions.InvalidSignatureError(
                    "Signature mismatch",
                ),
            ),
        ):
            from luana_core_iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("tampered.jwt.token")

        assert exc_info.value.status_code == 401

    def test_missing_clerk_issuer_raises_500(self):
        """If CLERK_ISSUER env is not set, the server should return 500."""
        with patch("luana_core_iam.application.auth.CLERK_ISSUER", None):
            from luana_core_iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("any.jwt.token")

        assert exc_info.value.status_code == 500
        assert "misconfiguration" in exc_info.value.detail.lower() or "CLERK_ISSUER" in exc_info.value.detail

    def test_jwks_client_error_raises_401(self):
        """If JWKS key lookup fails (network/format error), return 401."""
        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt.side_effect = Exception("JWKS unreachable")

        with (
            patch("luana_core_iam.application.auth.jwks_client", mock_jwks),
            patch(
                "luana_core_iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
        ):
            from luana_core_iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("any.jwt.token")

        assert exc_info.value.status_code == 401

    def test_decode_error_raises_401(self):
        """Any PyJWTError during decode results in 401."""
        import jwt as pyjwt

        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")

        with (
            patch("luana_core_iam.application.auth.jwks_client", mock_jwks),
            patch(
                "luana_core_iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
            patch(
                "jwt.decode",
                side_effect=pyjwt.exceptions.DecodeError("Cannot decode"),
            ),
        ):
            from luana_core_iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("garbage.token")

        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# HTTP-level tests for auth_router (/users/me and /users/me/tenants)
# ---------------------------------------------------------------------------


class TestAuthRouterEndpoints:
    def _make_app(self, db_session, token_payload: dict):
        from fastapi import FastAPI
        from fastapi.testclient import TestClient

        from luana_core_platform.core.database import get_db
        from luana_core_iam.api.routers.auth_router import router
        from luana_core_iam.application.auth import verify_clerk_token

        app = FastAPI()
        app.include_router(router, prefix="/users")
        app.dependency_overrides[verify_clerk_token] = lambda: token_payload
        app.dependency_overrides[get_db] = lambda: db_session
        return TestClient(app)

    def test_get_me_returns_user(self, db, seed_user):
        payload = {"sub": "clerk_alice_001", "email": "alice@example.com"}
        client = self._make_app(db, payload)
        resp = client.get("/users/me")
        assert resp.status_code == 200
        assert resp.json()["email"] == "alice@example.com"

    def test_get_me_unknown_email_returns_403(self, db):
        payload = {"sub": "clerk_xyz", "email": "nobody@x.com"}
        client = self._make_app(db, payload)
        resp = client.get("/users/me")
        assert resp.status_code == 403

    def test_get_me_tenants_returns_list(self, db, seed_user_tenant_link):
        payload = {"sub": "clerk_alice_001", "email": "alice@example.com"}
        client = self._make_app(db, payload)
        resp = client.get("/users/me/tenants")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)
        assert len(resp.json()) >= 1

    def test_get_me_tenants_has_required_fields(self, db, seed_user_tenant_link):
        payload = {"sub": "clerk_alice_001", "email": "alice@example.com"}
        client = self._make_app(db, payload)
        resp = client.get("/users/me/tenants")
        item = resp.json()[0]
        for field in ("id", "name", "slug", "role"):
            assert field in item
