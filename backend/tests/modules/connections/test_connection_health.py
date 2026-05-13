"""Tests for evaluate_connection_health() — pure function unit tests.

TDD: Written BEFORE implementation. These must fail until health.py exists.
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock

import pytest


class TestEvaluateConnectionHealth:
    """Unit tests for the pure function that evaluates token health."""

    def test_not_connected_when_none(self) -> None:
        """Returns status 'not_connected' when credentials is None."""
        from luana_core_connections.api.health import evaluate_connection_health

        result = evaluate_connection_health(credentials=None, channel_slug="meta")

        assert result.status == "not_connected"
        assert result.channel_slug == "meta"
        assert result.expires_at is None

    def test_healthy_when_no_expires_at(self) -> None:
        """Returns 'healthy' when credentials exist but no expires_at field."""
        from luana_core_connections.api.health import evaluate_connection_health

        creds = {"access_token": "some-token"}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "healthy"
        assert result.channel_slug == "meta"
        assert result.expires_at is None

    def test_healthy_when_far_from_expiry(self) -> None:
        """Returns 'healthy' when expires_at is more than 7 days away."""
        from luana_core_connections.api.health import evaluate_connection_health

        future = datetime.now(timezone.utc) + timedelta(days=30)
        creds = {"access_token": "tok", "expires_at": future.isoformat()}
        result = evaluate_connection_health(
            credentials=creds,
            channel_slug="google-analytics",
        )

        assert result.status == "healthy"
        assert result.channel_slug == "google-analytics"
        assert result.expires_at is not None

    def test_expiring_soon_within_7_days(self) -> None:
        """Returns 'expiring_soon' when expires_at is within 7 days."""
        from luana_core_connections.api.health import evaluate_connection_health

        soon = datetime.now(timezone.utc) + timedelta(days=3)
        creds = {"access_token": "tok", "expires_at": soon.isoformat()}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "expiring_soon"
        assert result.channel_slug == "meta"

    def test_expired_when_past(self) -> None:
        """Returns 'expired' when expires_at is in the past."""
        from luana_core_connections.api.health import evaluate_connection_health

        past = datetime.now(timezone.utc) - timedelta(days=5)
        creds = {"access_token": "tok", "expires_at": past.isoformat()}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "expired"
        assert result.channel_slug == "meta"

    def test_healthy_when_invalid_format(self) -> None:
        """Returns 'healthy' when expires_at can't be parsed (graceful fallback)."""
        from luana_core_connections.api.health import evaluate_connection_health

        creds = {"access_token": "tok", "expires_at": "not-a-date"}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "healthy"
        assert result.channel_slug == "meta"

    def test_messages_in_spanish(self) -> None:
        """All messages returned must be in Spanish with correct accents."""
        from luana_core_connections.api.health import evaluate_connection_health

        # not_connected
        r1 = evaluate_connection_health(credentials=None, channel_slug="meta")
        assert "conexi" in r1.message.lower() or "conectad" in r1.message.lower()

        # healthy
        r2 = evaluate_connection_health(
            credentials={"access_token": "t"},
            channel_slug="meta",
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
        from luana_core_connections.api.health import evaluate_connection_health

        boundary = datetime.now(timezone.utc) + timedelta(days=7)
        creds = {"access_token": "tok", "expires_at": boundary.isoformat()}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "expiring_soon"

    def test_expired_unix_timestamp(self) -> None:
        """Handles expires_at as a unix timestamp (int/float stored as string)."""
        from luana_core_connections.api.health import evaluate_connection_health

        past_ts = (datetime.now(timezone.utc) - timedelta(days=1)).timestamp()
        creds = {"access_token": "tok", "expires_at": str(int(past_ts))}
        result = evaluate_connection_health(credentials=creds, channel_slug="meta")

        assert result.status == "expired"


class TestConnectionHealthResponse:
    """Validates the Pydantic response model shape."""

    def test_response_model_fields(self) -> None:
        from luana_core_connections.api.health import ConnectionHealthResponse

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
        from luana_core_connections.api.health import ConnectionHealthResponse

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


class TestParseExpiresAtNaiveDatetime:
    def test_naive_iso_datetime_gets_utc_tzinfo(self):
        from luana_core_connections.api.health import _parse_expires_at

        result = _parse_expires_at("2025-06-01T12:00:00")
        assert result is not None
        assert result.tzinfo is not None


class TestGetConnectionHealthRoute:
    def _user(self):
        u = MagicMock()
        u.tenant_id = uuid.uuid4()
        return u

    def _make_db(self, connection=None):
        db = MagicMock()
        repo = MagicMock()
        repo.get_by_tenant_and_type.return_value = connection
        return db, repo

    async def _call(self, slug, user, db, repo):
        from unittest.mock import patch

        from luana_core_connections.api.health import get_connection_health
        from luana_core_connections.infrastructure.repositories import ChannelConnectionRepository

        with (
            patch.object(ChannelConnectionRepository, "__init__", return_value=None),
            patch.object(
                ChannelConnectionRepository,
                "get_by_tenant_and_type",
                return_value=repo.get_by_tenant_and_type.return_value,
            ),
        ):
            return await get_connection_health(slug, user, db)

    @pytest.mark.asyncio
    async def test_raises_404_for_unknown_slug(self):
        from fastapi import HTTPException

        from luana_core_connections.api.health import get_connection_health

        user = self._user()
        db = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await get_connection_health("unknown-channel", user, db)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_not_connected_when_no_connection(self):
        from unittest.mock import patch

        from luana_core_connections.api.health import get_connection_health
        from luana_core_connections.infrastructure.repositories import ChannelConnectionRepository

        user = self._user()
        db = MagicMock()
        with (
            patch.object(ChannelConnectionRepository, "__init__", return_value=None),
            patch.object(ChannelConnectionRepository, "get_by_tenant_and_type", return_value=None),
        ):
            result = await get_connection_health("meta", user, db)
        assert result.status == "not_connected"

    @pytest.mark.asyncio
    async def test_not_connected_when_inactive(self):
        from unittest.mock import patch

        from luana_core_connections.api.health import get_connection_health
        from luana_core_connections.infrastructure.repositories import ChannelConnectionRepository

        user = self._user()
        db = MagicMock()
        conn = MagicMock()
        conn.is_active = False
        with (
            patch.object(ChannelConnectionRepository, "__init__", return_value=None),
            patch.object(ChannelConnectionRepository, "get_by_tenant_and_type", return_value=conn),
        ):
            result = await get_connection_health("meta", user, db)
        assert result.status == "not_connected"

    @pytest.mark.asyncio
    async def test_returns_health_when_active(self):
        from unittest.mock import patch

        from luana_core_connections.api.health import get_connection_health
        from luana_core_connections.infrastructure.repositories import ChannelConnectionRepository

        user = self._user()
        db = MagicMock()
        conn = MagicMock()
        conn.is_active = True
        conn.credentials = {"access_token": "tok"}
        with (
            patch.object(ChannelConnectionRepository, "__init__", return_value=None),
            patch.object(ChannelConnectionRepository, "get_by_tenant_and_type", return_value=conn),
        ):
            result = await get_connection_health("meta", user, db)
        assert result.status == "healthy"
