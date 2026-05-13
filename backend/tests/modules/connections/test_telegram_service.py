"""Tests for TelegramService channel adapter."""

from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from luana_core_connections.infrastructure.channels.telegram_service import TelegramService

TENANT_ID = uuid4()


def _service(conn=None, active=True):
    db = MagicMock()
    svc = TelegramService(db)
    svc.repo = MagicMock()
    svc.repo.get_active.return_value = conn
    return svc


def _conn(token="bot_token_123", config=None):
    c = MagicMock()
    c.credentials = {"token": token}
    c.config = {"metadata": {"first_name": "MyBot", "username": "my_bot"}} if config is None else config
    return c


# ---------------------------------------------------------------------------
# get_status
# ---------------------------------------------------------------------------


class TestTelegramGetStatus:
    def test_not_connected_when_no_connection(self):
        svc = _service(conn=None)
        result = svc.get_status(TENANT_ID)
        assert result["is_connected"] is False

    def test_connected_returns_bot_info(self):
        conn = _conn(config={"metadata": {"first_name": "TestBot", "username": "testbot"}})
        svc = _service(conn=conn)
        result = svc.get_status(TENANT_ID)
        assert result["is_connected"] is True
        assert result["bot_name"] == "TestBot"
        assert result["username"] == "testbot"

    def test_connected_missing_metadata_returns_none_fields(self):
        conn = _conn(config={})
        svc = _service(conn=conn)
        result = svc.get_status(TENANT_ID)
        assert result["is_connected"] is True
        assert result["bot_name"] is None


# ---------------------------------------------------------------------------
# connect
# ---------------------------------------------------------------------------


class TestTelegramConnect:
    @pytest.mark.asyncio
    async def test_raises_on_invalid_token(self):
        svc = _service()
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.text = "Unauthorized"
        mock_resp.json.return_value = {}

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=mock_resp)
            with pytest.raises(ValueError, match="invalido"):
                await svc.connect(TENANT_ID, "bad_token")

    @pytest.mark.asyncio
    async def test_raises_on_network_error(self):
        import httpx

        svc = _service()

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.RequestError("connection refused"))
            with pytest.raises(RuntimeError, match="Error conectando"):
                await svc.connect(TENANT_ID, "any_token")

    @pytest.mark.asyncio
    async def test_successful_connect_saves_to_db(self):
        svc = _service()
        svc.repo.upsert = MagicMock()

        bot_info = {"id": 123, "first_name": "MyBot", "username": "mybot"}
        validate_resp = MagicMock()
        validate_resp.status_code = 200
        validate_resp.json.return_value = {"result": bot_info}

        delete_resp = MagicMock()
        delete_resp.status_code = 200
        delete_resp.json.return_value = {"ok": True}

        set_webhook_resp = MagicMock()
        set_webhook_resp.status_code = 200
        set_webhook_resp.json.return_value = {"ok": True}

        call_count = [0]

        async def fake_get(url, **kwargs):
            call_count[0] += 1
            if "getMe" in url:
                return validate_resp
            if "deleteWebhook" in url:
                return delete_resp
            return MagicMock(status_code=200)

        async def fake_post(url, **kwargs):
            return set_webhook_resp

        with (
            patch("luana_core_connections.infrastructure.channels.telegram_service.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.API_DOMAIN = "api.example.com"
            mock_settings.DOMAIN_NAME = "example.com"
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=fake_get)
            MockClient.return_value.post = AsyncMock(side_effect=fake_post)
            result = await svc.connect(TENANT_ID, "valid_token")

        assert result["status"] == "connected"
        assert result["bot"]["first_name"] == "MyBot"
        svc.repo.upsert.assert_called_once()

    @pytest.mark.asyncio
    async def test_raises_when_webhook_setup_fails(self):
        svc = _service()

        bot_info = {"id": 123, "first_name": "MyBot", "username": "mybot"}
        validate_resp = MagicMock()
        validate_resp.status_code = 200
        validate_resp.json.return_value = {"result": bot_info}

        delete_resp = MagicMock()
        delete_resp.status_code = 200

        webhook_fail_resp = MagicMock()
        webhook_fail_resp.status_code = 400
        webhook_fail_resp.text = "bad request"
        webhook_fail_resp.json.return_value = {"description": "Bad Request: url is not allowed"}

        async def fake_get(url, **kwargs):
            if "getMe" in url:
                return validate_resp
            return delete_resp

        async def fake_post(url, **kwargs):
            return webhook_fail_resp

        with (
            patch("luana_core_connections.infrastructure.channels.telegram_service.settings") as mock_settings,
            patch("httpx.AsyncClient") as MockClient,
        ):
            mock_settings.API_DOMAIN = "api.example.com"
            mock_settings.DOMAIN_NAME = "example.com"
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=fake_get)
            MockClient.return_value.post = AsyncMock(side_effect=fake_post)
            with pytest.raises(RuntimeError):
                await svc.connect(TENANT_ID, "valid_token")


# ---------------------------------------------------------------------------
# test_connection
# ---------------------------------------------------------------------------


class TestTelegramTestConnection:
    @pytest.mark.asyncio
    async def test_raises_when_no_connection(self):
        svc = _service(conn=None)
        with pytest.raises(ValueError, match="No hay conexion"):
            await svc.test_connection(TENANT_ID)

    @pytest.mark.asyncio
    async def test_raises_when_no_token(self):
        conn = MagicMock()
        conn.credentials = {}
        svc = _service(conn=conn)
        with pytest.raises(RuntimeError, match="corruptas"):
            await svc.test_connection(TENANT_ID)

    @pytest.mark.asyncio
    async def test_returns_ok_on_success(self):
        conn = _conn()
        svc = _service(conn=conn)

        ok_resp = MagicMock()
        ok_resp.status_code = 200
        ok_resp.json.return_value = {"ok": True, "result": {"id": 123}}

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=ok_resp)
            result = await svc.test_connection(TENANT_ID)

        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_error_on_non_200(self):
        conn = _conn()
        svc = _service(conn=conn)

        fail_resp = MagicMock()
        fail_resp.status_code = 401

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=fail_resp)
            result = await svc.test_connection(TENANT_ID)

        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_returns_error_on_http_exception(self):
        import httpx

        conn = _conn()
        svc = _service(conn=conn)

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.HTTPError("network error"))
            result = await svc.test_connection(TENANT_ID)

        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# disconnect
# ---------------------------------------------------------------------------


class TestTelegramDisconnect:
    @pytest.mark.asyncio
    async def test_raises_when_no_connection(self):
        svc = _service(conn=None)
        with pytest.raises(ValueError, match="No hay conexion"):
            await svc.disconnect(TENANT_ID)

    @pytest.mark.asyncio
    async def test_disconnects_and_deactivates(self):
        conn = _conn()
        svc = _service(conn=conn)
        svc.repo.deactivate = MagicMock()

        delete_resp = MagicMock()
        delete_resp.status_code = 200

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=delete_resp)
            result = await svc.disconnect(TENANT_ID)

        svc.repo.deactivate.assert_called_once_with(conn)
        assert result["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_still_deactivates_when_webhook_delete_fails(self):
        import httpx

        conn = _conn()
        svc = _service(conn=conn)
        svc.repo.deactivate = MagicMock()

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))
            result = await svc.disconnect(TENANT_ID)

        svc.repo.deactivate.assert_called_once()
        assert result["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_skips_webhook_delete_when_no_token(self):
        conn = MagicMock()
        conn.credentials = {}  # no token
        svc = _service(conn=conn)
        svc.repo.deactivate = MagicMock()

        result = await svc.disconnect(TENANT_ID)

        svc.repo.deactivate.assert_called_once()
        assert result["status"] == "disconnected"
