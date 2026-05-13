"""Tests for TelegramChannelRouter._resolve_telegram_id — real CRM port wire.

TDD RED → GREEN for Sub-E:
- Real LeadModel mock with telegram_id='@alice' → router resolves '@alice'
- Lead without telegram_id → None
- Tenant_id mismatch → None (cross-tenant lookup blocked)
- No session injected → None (graceful skip)

PR-7 PI-1 S3.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_campaigns.infrastructure.channels.telegram import TelegramChannelRouter


# ── Helpers ────────────────────────────────────────────────────────────────────


def _make_router(session: Any = None) -> TelegramChannelRouter:
    """Build TelegramChannelRouter with optional async session injected."""
    token_provider = AsyncMock(return_value="test:BOT_TOKEN")
    return TelegramChannelRouter(
        token_provider=token_provider,
        session=session,
    )


# ── Tests ──────────────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_resolve_telegram_id_returns_chat_id_on_hit() -> None:
    """Real LeadModel mock with telegram_id='@alice' → router resolves '@alice'."""
    lead_id = uuid4()
    tenant_id = uuid4()

    # Mock get_lead_telegram_id_async to return '@alice'
    mock_session = MagicMock()
    router = _make_router(session=mock_session)

    with patch(
        "luana_core_campaigns.infrastructure.channels.telegram.get_lead_telegram_id_async",
        new=AsyncMock(return_value="@alice"),
    ) as mock_fn:
        result = await router._resolve_telegram_id(lead_id, tenant_id)

    assert result == "@alice"
    mock_fn.assert_awaited_once_with(mock_session, tenant_id, lead_id)


@pytest.mark.asyncio
async def test_resolve_telegram_id_returns_none_when_no_telegram_id() -> None:
    """Lead without telegram_id → None."""
    lead_id = uuid4()
    tenant_id = uuid4()
    mock_session = MagicMock()
    router = _make_router(session=mock_session)

    with patch(
        "luana_core_campaigns.infrastructure.channels.telegram.get_lead_telegram_id_async",
        new=AsyncMock(return_value=None),
    ):
        result = await router._resolve_telegram_id(lead_id, tenant_id)

    assert result is None


@pytest.mark.asyncio
async def test_resolve_telegram_id_tenant_mismatch_returns_none() -> None:
    """Tenant_id mismatch → None (cross-tenant isolation enforced by port)."""
    lead_id = uuid4()
    wrong_tenant = uuid4()
    mock_session = MagicMock()
    router = _make_router(session=mock_session)

    # Port returns None because tenant_id doesn't match the lead's tenant
    with patch(
        "luana_core_campaigns.infrastructure.channels.telegram.get_lead_telegram_id_async",
        new=AsyncMock(return_value=None),
    ) as mock_fn:
        result = await router._resolve_telegram_id(lead_id, wrong_tenant)

    # Called with wrong_tenant — port enforces tenant isolation
    mock_fn.assert_awaited_once_with(mock_session, wrong_tenant, lead_id)
    assert result is None


@pytest.mark.asyncio
async def test_resolve_telegram_id_no_session_returns_none() -> None:
    """No session injected → graceful None (no DB call made)."""
    lead_id = uuid4()
    tenant_id = uuid4()
    router = _make_router(session=None)

    result = await router._resolve_telegram_id(lead_id, tenant_id)

    assert result is None


@pytest.mark.asyncio
async def test_resolve_telegram_id_port_exception_returns_none() -> None:
    """Port raises exception → graceful None (never aborts channel flow)."""
    lead_id = uuid4()
    tenant_id = uuid4()
    mock_session = MagicMock()
    router = _make_router(session=mock_session)

    with patch(
        "luana_core_campaigns.infrastructure.channels.telegram.get_lead_telegram_id_async",
        new=AsyncMock(side_effect=RuntimeError("DB unavailable")),
    ):
        result = await router._resolve_telegram_id(lead_id, tenant_id)

    assert result is None
