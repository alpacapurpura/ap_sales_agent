"""Tests for WhatsApp channel adapters: BaseEvolutionApi, EvolutionApiV2, v1."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from luana_core_connections.infrastructure.channels.whatsapp.base import BaseEvolutionApi
from luana_core_connections.infrastructure.channels.whatsapp.v1 import EvolutionApiV1
from luana_core_connections.infrastructure.channels.whatsapp.v2 import EvolutionApiV2
from luana_core_platform.domain.messages import OutgoingMessage

TENANT_ID = "tenant_abc"
BASE_URL = "https://evolution.example.com"
API_KEY = "test_api_key"


def _v2() -> EvolutionApiV2:
    return EvolutionApiV2(tenant_id=TENANT_ID, base_url=BASE_URL, api_key=API_KEY)


# ---------------------------------------------------------------------------
# BaseEvolutionApi._normalize_jid
# ---------------------------------------------------------------------------


class TestNormalizeJid:
    def test_adds_suffix_when_no_at(self):
        adapter = _v2()
        assert adapter._normalize_jid("5199999999") == "5199999999@s.whatsapp.net"

    def test_keeps_jid_when_already_has_at(self):
        adapter = _v2()
        assert adapter._normalize_jid("5199999999@s.whatsapp.net") == "5199999999@s.whatsapp.net"


# ---------------------------------------------------------------------------
# BaseEvolutionApi.normalize_payload
# ---------------------------------------------------------------------------


class TestNormalizePayload:
    def test_returns_none_when_no_text(self):
        adapter = _v2()
        result = adapter.normalize_payload({"data": {"key": {}, "message": {}}})
        assert result is None

    def test_returns_none_when_from_me(self):
        adapter = _v2()
        payload = {
            "data": {
                "key": {"fromMe": True, "remoteJid": "5199@s.whatsapp.net"},
                "message": {"conversation": "hello"},
                "pushName": "Me",
            }
        }
        assert adapter.normalize_payload(payload) is None

    def test_returns_none_when_no_remote_jid(self):
        adapter = _v2()
        payload = {
            "data": {
                "key": {"fromMe": False},
                "message": {"conversation": "hello"},
                "pushName": "User",
            }
        }
        assert adapter.normalize_payload(payload) is None

    def test_returns_incoming_message_for_valid_payload(self):
        adapter = _v2()
        payload = {
            "data": {
                "key": {"fromMe": False, "remoteJid": "5199999999@s.whatsapp.net"},
                "message": {"conversation": "Hola!"},
                "pushName": "Alice",
            }
        }
        msg = adapter.normalize_payload(payload)
        assert msg is not None
        assert msg.text == "Hola!"
        assert msg.user_id == "5199999999"
        assert msg.channel_type == "whatsapp"

    def test_extracts_extended_text(self):
        adapter = _v2()
        payload = {
            "data": {
                "key": {"fromMe": False, "remoteJid": "5199@s.whatsapp.net"},
                "message": {"extendedTextMessage": {"text": "Link text"}},
                "pushName": "Bob",
            }
        }
        msg = adapter.normalize_payload(payload)
        assert msg is not None
        assert msg.text == "Link text"


# ---------------------------------------------------------------------------
# EvolutionApiV2.normalize_payload adds version metadata
# ---------------------------------------------------------------------------


class TestV2NormalizePayload:
    def test_adds_v2_version_metadata(self):
        adapter = _v2()
        payload = {
            "data": {
                "key": {"fromMe": False, "remoteJid": "5199@s.whatsapp.net"},
                "message": {"conversation": "Hi"},
                "pushName": "Carol",
            }
        }
        msg = adapter.normalize_payload(payload)
        assert msg is not None
        assert msg.metadata["version"] == "v2"

    def test_returns_none_when_base_returns_none(self):
        adapter = _v2()
        result = adapter.normalize_payload({"data": {}})
        assert result is None


# ---------------------------------------------------------------------------
# BaseEvolutionApi.send_message
# ---------------------------------------------------------------------------


class TestSendMessage:
    @pytest.mark.asyncio
    async def test_sends_text_message(self):
        adapter = _v2()
        ok_resp = MagicMock()
        ok_resp.status_code = 201
        ok_resp.json.return_value = {"key": {"id": "msg_123"}}

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=ok_resp)
            msg = OutgoingMessage(user_id="5199999999", text="Hello!", channel_type="whatsapp")
            result = await adapter.send_message(msg)

        assert result == {"key": {"id": "msg_123"}}

    @pytest.mark.asyncio
    async def test_returns_error_on_non_200(self):
        adapter = _v2()
        fail_resp = MagicMock()
        fail_resp.status_code = 500
        fail_resp.text = "Server Error"

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=fail_resp)
            msg = OutgoingMessage(user_id="5199999999", text="Hello!", channel_type="whatsapp")
            result = await adapter.send_message(msg)

        assert "error" in result

    @pytest.mark.asyncio
    async def test_raises_on_network_exception(self):
        import httpx

        adapter = _v2()

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(side_effect=httpx.ConnectError("timeout"))
            msg = OutgoingMessage(user_id="5199", text="Hi", channel_type="whatsapp")
            with pytest.raises(Exception):  # noqa: B017
                await adapter.send_message(msg)


# ---------------------------------------------------------------------------
# BaseEvolutionApi.set_typing_status (fire and forget — no raise)
# ---------------------------------------------------------------------------


class TestSetTypingStatus:
    @pytest.mark.asyncio
    async def test_suppresses_exception(self):
        adapter = _v2()

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(side_effect=Exception("timeout"))
            # Should NOT raise
            await adapter.set_typing_status("5199999999")


# ---------------------------------------------------------------------------
# BaseEvolutionApi management methods
# ---------------------------------------------------------------------------


class TestManagementMethods:
    @pytest.mark.asyncio
    async def test_delete_instance_returns_status(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 200

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.delete = AsyncMock(return_value=resp)
            result = await adapter.delete_instance()

        assert result["status"] == 200

    @pytest.mark.asyncio
    async def test_logout_returns_status(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 200

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.delete = AsyncMock(return_value=resp)
            result = await adapter.logout()

        assert result["status"] == 200

    @pytest.mark.asyncio
    async def test_check_status_connected(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"instance": {"state": "open"}}

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=resp)
            result = await adapter.check_status()

        assert result["exists"] is True
        assert result["state"] == "open"

    @pytest.mark.asyncio
    async def test_check_status_not_found(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 404

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=resp)
            result = await adapter.check_status()

        assert result["exists"] is False

    @pytest.mark.asyncio
    async def test_check_status_error(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 500
        resp.text = "Internal Error"

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=resp)
            result = await adapter.check_status()

        assert result["state"] == "error"

    @pytest.mark.asyncio
    async def test_get_qr_returns_data(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 200
        resp.json.return_value = {"base64": "data:image/png;base64,abc"}

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=resp)
            result = await adapter.get_qr()

        assert result["status"] == 200

    @pytest.mark.asyncio
    async def test_get_qr_returns_error_on_non_200(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 404
        resp.text = "not found"

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.get = AsyncMock(return_value=resp)
            result = await adapter.get_qr()

        assert result["status"] == 404


# ---------------------------------------------------------------------------
# EvolutionApiV2 specific methods
# ---------------------------------------------------------------------------


class TestV2Specific:
    @pytest.mark.asyncio
    async def test_create_instance_returns_status(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 201
        resp.text = '{"instance": {"instanceName": "tenant_abc"}}'
        resp.json.return_value = {"instance": {"instanceName": "tenant_abc"}}

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=resp)
            result = await adapter.create_instance("token_123")

        assert result["status"] == 201

    @pytest.mark.asyncio
    async def test_configure_webhook_returns_status(self):
        adapter = _v2()
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "ok"

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=resp)
            result = await adapter.configure_webhook("https://webhook.example.com/wh")

        assert result["status"] == 200


# ---------------------------------------------------------------------------
# EvolutionApiV1 specific methods
# ---------------------------------------------------------------------------


class TestV1Specific:
    def _v1(self) -> EvolutionApiV1:
        return EvolutionApiV1(tenant_id=TENANT_ID, base_url=BASE_URL, api_key=API_KEY)

    @pytest.mark.asyncio
    async def test_create_instance_returns_status(self):
        adapter = self._v1()
        resp = MagicMock()
        resp.status_code = 201
        resp.text = '{"instance": {"instanceName": "tenant_abc"}}'
        resp.json.return_value = {"instance": {"instanceName": "tenant_abc"}}

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=resp)
            result = await adapter.create_instance("token_v1")

        assert result["status"] == 201

    @pytest.mark.asyncio
    async def test_configure_webhook_returns_status(self):
        adapter = self._v1()
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "ok"

        with patch("httpx.AsyncClient") as MockClient:
            MockClient.return_value.__aenter__ = AsyncMock(return_value=MockClient.return_value)
            MockClient.return_value.__aexit__ = AsyncMock(return_value=False)
            MockClient.return_value.post = AsyncMock(return_value=resp)
            result = await adapter.configure_webhook("https://webhook.example.com/v1")

        assert result["status"] == 200
