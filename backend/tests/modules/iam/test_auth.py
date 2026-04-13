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
            patch("src.modules.iam.application.auth.jwks_client", mock_jwks),
            patch(
                "src.modules.iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
            patch("jwt.decode", return_value=expected_payload),
        ):
            from src.modules.iam.application.auth import verify_token_payload

            result = verify_token_payload("fake.jwt.token")

        assert result["email"] == "test@example.com"
        assert result["sub"] == "user_clerk_abc123"

    def test_expired_token_raises_401(self):
        """An expired JWT must raise HTTPException with status 401."""
        import jwt as pyjwt

        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")

        with (
            patch("src.modules.iam.application.auth.jwks_client", mock_jwks),
            patch(
                "src.modules.iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
            patch(
                "jwt.decode",
                side_effect=pyjwt.exceptions.ExpiredSignatureError("Token expired"),
            ),
        ):
            from src.modules.iam.application.auth import verify_token_payload

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
            patch("src.modules.iam.application.auth.jwks_client", mock_jwks),
            patch(
                "src.modules.iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
            patch(
                "jwt.decode",
                side_effect=pyjwt.exceptions.InvalidSignatureError(
                    "Signature mismatch",
                ),
            ),
        ):
            from src.modules.iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("tampered.jwt.token")

        assert exc_info.value.status_code == 401

    def test_missing_clerk_issuer_raises_500(self):
        """If CLERK_ISSUER env is not set, the server should return 500."""
        with patch("src.modules.iam.application.auth.CLERK_ISSUER", None):
            from src.modules.iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("any.jwt.token")

        assert exc_info.value.status_code == 500
        assert "misconfiguration" in exc_info.value.detail.lower() or "CLERK_ISSUER" in exc_info.value.detail

    def test_jwks_client_error_raises_401(self):
        """If JWKS key lookup fails (network/format error), return 401."""
        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt.side_effect = Exception("JWKS unreachable")

        with (
            patch("src.modules.iam.application.auth.jwks_client", mock_jwks),
            patch(
                "src.modules.iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
        ):
            from src.modules.iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("any.jwt.token")

        assert exc_info.value.status_code == 401

    def test_decode_error_raises_401(self):
        """Any PyJWTError during decode results in 401."""
        import jwt as pyjwt

        mock_jwks = MagicMock()
        mock_jwks.get_signing_key_from_jwt.return_value = MagicMock(key="fake-key")

        with (
            patch("src.modules.iam.application.auth.jwks_client", mock_jwks),
            patch(
                "src.modules.iam.application.auth.CLERK_ISSUER",
                "https://clerk.example.com",
            ),
            patch(
                "jwt.decode",
                side_effect=pyjwt.exceptions.DecodeError("Cannot decode"),
            ),
        ):
            from src.modules.iam.application.auth import verify_token_payload

            with pytest.raises(HTTPException) as exc_info:
                verify_token_payload("garbage.token")

        assert exc_info.value.status_code == 401
