"""Tests for WhatsApp API route functions."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from src.modules.connections.api.whatsapp import (
    create_whatsapp_session,
    delete_whatsapp_session,
    get_whatsapp_qr,
    get_whatsapp_status,
    handle_whatsapp_webhook,
    verify_whatsapp_webhook,
    whatsapp_webhook,
)

TENANT_ID = str(uuid4())


def _repo(**kwargs):
    repo = MagicMock()
    for k, v in kwargs.items():
        setattr(repo, k, v)
    return repo


def _conn(config=None, is_active=True):
    c = MagicMock()
    c.config = config or {}
    c.is_active = is_active
    return c


# ---------------------------------------------------------------------------
# verify_whatsapp_webhook
# ---------------------------------------------------------------------------


class TestVerifyWhatsAppWebhook:
    @pytest.mark.asyncio
    async def test_returns_challenge_on_valid_token(self):
        with patch("src.modules.connections.api.whatsapp.settings") as mock_settings:
            mock_settings.WHATSAPP_VERIFY_TOKEN = "secret_token"
            result = await verify_whatsapp_webhook(
                mode="subscribe",
                token="secret_token",
                challenge="12345",
            )
        assert result == 12345

    @pytest.mark.asyncio
    async def test_raises_403_on_wrong_token(self):
        with patch("src.modules.connections.api.whatsapp.settings") as mock_settings:
            mock_settings.WHATSAPP_VERIFY_TOKEN = "secret_token"
            with pytest.raises(HTTPException) as exc_info:
                await verify_whatsapp_webhook(
                    mode="subscribe",
                    token="wrong_token",
                    challenge="12345",
                )
        assert exc_info.value.status_code == 403

    @pytest.mark.asyncio
    async def test_raises_403_on_wrong_mode(self):
        with patch("src.modules.connections.api.whatsapp.settings") as mock_settings:
            mock_settings.WHATSAPP_VERIFY_TOKEN = "secret_token"
            with pytest.raises(HTTPException) as exc_info:
                await verify_whatsapp_webhook(
                    mode="unsubscribe",
                    token="secret_token",
                    challenge="12345",
                )
        assert exc_info.value.status_code == 403


# ---------------------------------------------------------------------------
# whatsapp_webhook (global, no tenant)
# ---------------------------------------------------------------------------


class TestWhatsAppWebhookGlobal:
    @pytest.mark.asyncio
    async def test_delegates_to_handler(self):
        req = MagicMock()
        req.json = AsyncMock(return_value={"object": "whatsapp_business_account"})
        bg_tasks = MagicMock()
        handler = MagicMock()
        handler.handle_whatsapp_webhook = AsyncMock()

        result = await whatsapp_webhook(req, bg_tasks, handler)

        handler.handle_whatsapp_webhook.assert_called_once()
        assert result == {"status": "received"}


# ---------------------------------------------------------------------------
# get_whatsapp_status
# ---------------------------------------------------------------------------


class TestGetWhatsAppStatus:
    @pytest.mark.asyncio
    async def test_disconnected_when_no_connections(self):
        repo = _repo(
            get_active=MagicMock(return_value=None),
        )
        result = await get_whatsapp_status(TENANT_ID, repo)
        assert result["evolution"]["status"] == "disconnected"
        assert result["meta"]["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_evolution_connected_when_state_open(self):
        evo_conn = _conn(config={"metadata": {"first_name": "Test User"}})

        def _get_active(tenant_uuid, channel_type):
            from src.modules.connections.domain.enums import ChannelType

            if channel_type == ChannelType.WHATSAPP:
                return evo_conn
            return None

        repo = _repo(get_active=MagicMock(side_effect=_get_active))

        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.check_status = AsyncMock(
                return_value={"exists": True, "state": "open", "data": {"instance": {}}}
            )
            result = await get_whatsapp_status(TENANT_ID, repo)

        assert result["evolution"]["status"] == "connected"

    @pytest.mark.asyncio
    async def test_evolution_connecting_state(self):
        evo_conn = _conn()

        def _get_active(tenant_uuid, channel_type):
            from src.modules.connections.domain.enums import ChannelType

            if channel_type == ChannelType.WHATSAPP:
                return evo_conn
            return None

        repo = _repo(get_active=MagicMock(side_effect=_get_active))

        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.check_status = AsyncMock(return_value={"exists": True, "state": "connecting"})
            result = await get_whatsapp_status(TENANT_ID, repo)

        assert result["evolution"]["status"] == "connecting"

    @pytest.mark.asyncio
    async def test_meta_connected_when_active(self):
        meta_conn = _conn(config={"metadata": {"phone": "+51999"}})

        def _get_active(tenant_uuid, channel_type):
            from src.modules.connections.domain.enums import ChannelType

            if channel_type == ChannelType.WHATSAPP_CLOUD:
                return meta_conn
            return None

        repo = _repo(get_active=MagicMock(side_effect=_get_active))

        result = await get_whatsapp_status(TENANT_ID, repo)
        assert result["meta"]["status"] == "connected"


# ---------------------------------------------------------------------------
# create_whatsapp_session
# ---------------------------------------------------------------------------


class TestCreateWhatsAppSession:
    @pytest.mark.asyncio
    async def test_meta_provider_returns_coming_soon(self):
        repo = _repo()
        result = await create_whatsapp_session(TENANT_ID, repo, provider="meta")
        assert result["status"] == "error"
        assert "coming soon" in result["message"].lower()

    @pytest.mark.asyncio
    async def test_creates_evolution_session(self):
        repo = _repo(upsert=MagicMock())

        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.check_status = AsyncMock(return_value={"exists": False})
            MockChannel.return_value.create_instance = AsyncMock(return_value={"status": 201})
            MockChannel.return_value.configure_webhook = AsyncMock(return_value={"status": 200})
            with (
                patch("src.modules.connections.api.whatsapp.asyncio.sleep", new_callable=AsyncMock),
                patch("src.modules.connections.api.whatsapp.settings") as mock_settings,
            ):
                mock_settings.API_URL = "https://api.example.com"
                result = await create_whatsapp_session(TENANT_ID, repo, provider="evolution")

        assert result["status"] == "created"
        repo.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_resets_existing_instance_before_creating(self):
        repo = _repo(upsert=MagicMock())

        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.check_status = AsyncMock(return_value={"exists": True})
            MockChannel.return_value.delete_instance = AsyncMock()
            MockChannel.return_value.create_instance = AsyncMock(return_value={"status": 201})
            MockChannel.return_value.configure_webhook = AsyncMock(return_value={"status": 200})
            with (
                patch("src.modules.connections.api.whatsapp.asyncio.sleep", new_callable=AsyncMock),
                patch("src.modules.connections.api.whatsapp.settings") as mock_settings,
            ):
                mock_settings.API_URL = "https://api.example.com"
                await create_whatsapp_session(TENANT_ID, repo, provider="evolution")

        MockChannel.return_value.delete_instance.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_500_when_create_fails(self):
        repo = _repo()

        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.check_status = AsyncMock(return_value={"exists": False})
            MockChannel.return_value.create_instance = AsyncMock(return_value={"status": 500, "text": "server error"})
            with (
                patch("src.modules.connections.api.whatsapp.asyncio.sleep", new_callable=AsyncMock),
                pytest.raises(HTTPException) as exc_info,
            ):
                await create_whatsapp_session(TENANT_ID, repo, provider="evolution")
        assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# get_whatsapp_qr
# ---------------------------------------------------------------------------


class TestGetWhatsAppQR:
    @pytest.mark.asyncio
    async def test_returns_qr_code_from_base64(self):
        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.get_qr = AsyncMock(
                return_value={"status": 200, "data": {"base64": "qr_base64_data"}}
            )
            result = await get_whatsapp_qr(TENANT_ID)
        assert result["code"] == "qr_base64_data"

    @pytest.mark.asyncio
    async def test_raises_404_when_instance_not_found(self):
        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.get_qr = AsyncMock(return_value={"status": 404})
            with pytest.raises(HTTPException) as exc_info:
                await get_whatsapp_qr(TENANT_ID)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_500_on_evolution_error(self):
        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.get_qr = AsyncMock(return_value={"status": 500, "text": "error"})
            with pytest.raises(HTTPException) as exc_info:
                await get_whatsapp_qr(TENANT_ID)
        assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# delete_whatsapp_session
# ---------------------------------------------------------------------------


class TestDeleteWhatsAppSession:
    @pytest.mark.asyncio
    async def test_deletes_meta_connection(self):
        conn = _conn()
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=conn),
            deactivate=MagicMock(),
        )
        result = await delete_whatsapp_session(TENANT_ID, repo, provider="meta")
        repo.deactivate.assert_called_once_with(conn)
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_deletes_meta_returns_deleted_when_no_connection(self):
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await delete_whatsapp_session(TENANT_ID, repo, provider="meta")
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_deletes_evolution_session(self):
        conn = _conn()
        repo = _repo(
            get_by_tenant_and_type=MagicMock(return_value=conn),
            deactivate=MagicMock(),
        )

        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.logout = AsyncMock()
            MockChannel.return_value.delete_instance = AsyncMock()
            result = await delete_whatsapp_session(TENANT_ID, repo, provider="evolution")

        repo.deactivate.assert_called_once_with(conn)
        assert result["status"] == "deleted"

    @pytest.mark.asyncio
    async def test_evolution_raises_500_on_error(self):
        repo = _repo()

        with patch("src.modules.connections.api.whatsapp.WhatsAppChannel") as MockChannel:
            MockChannel.return_value.logout = AsyncMock(side_effect=Exception("network error"))
            with pytest.raises(HTTPException) as exc_info:
                await delete_whatsapp_session(TENANT_ID, repo, provider="evolution")
        assert exc_info.value.status_code == 500


# ---------------------------------------------------------------------------
# handle_whatsapp_webhook per-tenant
# ---------------------------------------------------------------------------


class TestHandleWhatsAppWebhookPerTenant:
    @pytest.mark.asyncio
    async def test_with_background_tasks_adds_task(self):
        handler = MagicMock()
        handler.handle_incoming_webhook = AsyncMock()
        bg_tasks = MagicMock()

        result = await handle_whatsapp_webhook(
            TENANT_ID,
            {"entry": []},
            handler,
            background_tasks=bg_tasks,
        )

        bg_tasks.add_task.assert_called_once()
        assert result == {"status": "ok"}

    @pytest.mark.asyncio
    async def test_without_background_tasks_awaits_directly(self):
        handler = MagicMock()
        handler.handle_incoming_webhook = AsyncMock()

        result = await handle_whatsapp_webhook(
            TENANT_ID,
            {"entry": []},
            handler,
            background_tasks=None,
        )

        handler.handle_incoming_webhook.assert_called_once()
        assert result == {"status": "ok"}
