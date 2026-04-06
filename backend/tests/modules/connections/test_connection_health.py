"""Tests for evaluate_connection_health() — pure function unit tests.

TDD: Written BEFORE implementation. These must fail until health.py exists.
"""

from datetime import datetime, timedelta, timezone

import pytest


class TestEvaluateConnectionHealth:
    """Unit tests for the pure function that evaluates token health."""

    def test_not_connected_when_none(self) -> None:
        """Returns status 'not_connected' when credentials is None."""
        from src.modules.connections.api.health import evaluate_connection_health

        result = evaluate_connection_health(credentials=None, channel_slug="meta")

        assert result.status == "not_connected"
        assert result.channel_slug == "meta"
        assert result.expires_at is None

    def test_healthy_when_no_expires_at(self) -> None:
        """Returns 'healthy' when credentials exist but no expires_at field."""
        from src.modules.connections.api.health import evaluate_connection_health

        creds = {"access_token": "some-token"}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "healthy"
        assert result.channel_slug == "meta"
        assert result.expires_at is None

    def test_healthy_when_far_from_expiry(self) -> None:
        """Returns 'healthy' when expires_at is more than 7 days away."""
        from src.modules.connections.api.health import evaluate_connection_health

        future = datetime.now(timezone.utc) + timedelta(days=30)
        creds = {"access_token": "tok", "expires_at": future.isoformat()}
        result = evaluate_connection_health(credentials=creds, channel_slug="google-analytics")

        assert result.status == "healthy"
        assert result.channel_slug == "google-analytics"
        assert result.expires_at is not None

    def test_expiring_soon_within_7_days(self) -> None:
        """Returns 'expiring_soon' when expires_at is within 7 days."""
        from src.modules.connections.api.health import evaluate_connection_health

        soon = datetime.now(timezone.utc) + timedelta(days=3)
        creds = {"access_token": "tok", "expires_at": soon.isoformat()}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "expiring_soon"
        assert result.channel_slug == "meta"

    def test_expired_when_past(self) -> None:
        """Returns 'expired' when expires_at is in the past."""
        from src.modules.connections.api.health import evaluate_connection_health

        past = datetime.now(timezone.utc) - timedelta(days=5)
        creds = {"access_token": "tok", "expires_at": past.isoformat()}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "expired"
        assert result.channel_slug == "meta"

    def test_healthy_when_invalid_format(self) -> None:
        """Returns 'healthy' when expires_at can't be parsed (graceful fallback)."""
        from src.modules.connections.api.health import evaluate_connection_health

        creds = {"access_token": "tok", "expires_at": "not-a-date"}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "healthy"
        assert result.channel_slug == "meta"

    def test_messages_in_spanish(self) -> None:
        """All messages returned must be in Spanish with correct accents."""
        from src.modules.connections.api.health import evaluate_connection_health

        # not_connected
        r1 = evaluate_connection_health(credentials=None, channel_slug="meta")
        assert "conexi" in r1.message.lower() or "conectad" in r1.message.lower()

        # healthy
        r2 = evaluate_connection_health(
            credentials={"access_token": "t"}, channel_slug="meta"
        )
        assert r2.message  # non-empty Spanish message

        # expiring_soon
        soon = datetime.now(timezone.utc) + timedelta(days=2)
        r3 = evaluate_connection_health(
            credentials={"access_token": "t", "expires_at": soon.isoformat()},
            channel_slug="meta",
        )
        assert "expir" in r3.message.lower() or "venc" in r3.message.lower()

        # expired
        past = datetime.now(timezone.utc) - timedelta(days=1)
        r4 = evaluate_connection_health(
            credentials={"access_token": "t", "expires_at": past.isoformat()},
            channel_slug="meta",
        )
        assert "expir" in r4.message.lower() or "venc" in r4.message.lower()

    def test_expiring_soon_boundary_exactly_7_days(self) -> None:
        """At exactly 7 days, should be 'expiring_soon' (<=7 days)."""
        from src.modules.connections.api.health import evaluate_connection_health

        boundary = datetime.now(timezone.utc) + timedelta(days=7)
        creds = {"access_token": "tok", "expires_at": boundary.isoformat()}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "expiring_soon"

    def test_expired_unix_timestamp(self) -> None:
        """Handles expires_at as a unix timestamp (int/float stored as string)."""
        from src.modules.connections.api.health import evaluate_connection_health

        past_ts = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
        creds = {"access_token": "tok", "expires_at": str(int(past_ts))}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "expired"


class TestConnectionHealthResponse:
    """Validates the Pydantic response model shape."""

    def test_response_model_fields(self) -> None:
        from src.modules.connections.api.health import ConnectionHealthResponse

        r = ConnectionHealthResponse(
            status="healthy",
            channel_slug="meta",
            expires_at=None,
            message="Todo bien",
        )
        assert r.status == "healthy"
        assert r.channel_slug == "meta"
        assert r.expires_at is None
        assert r.message == "Todo bien"

    def test_response_model_serialization(self) -> None:
        from src.modules.connections.api.health import ConnectionHealthResponse

        r = ConnectionHealthResponse(
            status="expired",
            channel_slug="google-analytics",
            expires_at="2026-01-01T00:00:00Z",
            message="Token expirado",
        )
        data = r.model_dump()
        assert "status" in data
        assert "channel_slug" in data
        assert "expires_at" in data
        assert "message" in data
