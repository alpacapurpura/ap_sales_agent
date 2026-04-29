"""Tests for small modules: shopify_compliance, webhook_security, copilot_provider, webhook adapter."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# ---------------------------------------------------------------------------
# api/shopify_compliance.py
# ---------------------------------------------------------------------------
from src.modules.connections.api.shopify_compliance import (
    customers_data_request,
    customers_redact,
    shop_redact,
)


def _request_with_json(payload: dict):
    req = MagicMock()
    req.json = AsyncMock(return_value=payload)
    return req


def _request_raising():
    req = MagicMock()
    req.json = AsyncMock(side_effect=Exception("parse error"))
    return req


class TestShopifyComplianceRoutes:
    @pytest.mark.asyncio
    async def test_customers_data_request_success(self):
        req = _request_with_json({"shop_domain": "mystore.myshopify.com", "customer": {"id": 1}})
        result = await customers_data_request(req, verified=True)
        assert result["status"] == "received"

    @pytest.mark.asyncio
    async def test_customers_data_request_exception_returns_error(self):
        req = _request_raising()
        result = await customers_data_request(req, verified=True)
        assert result["status"] == "error"
        assert "parse error" in result["message"]

    @pytest.mark.asyncio
    async def test_customers_redact_success(self):
        req = _request_with_json({"shop_domain": "mystore.myshopify.com"})
        result = await customers_redact(req, verified=True)
        assert result["status"] == "received"

    @pytest.mark.asyncio
    async def test_customers_redact_exception_returns_error(self):
        req = _request_raising()
        result = await customers_redact(req, verified=True)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_shop_redact_success(self):
        req = _request_with_json({"shop_domain": "mystore.myshopify.com"})
        result = await shop_redact(req, verified=True)
        assert result["status"] == "received"

    @pytest.mark.asyncio
    async def test_shop_redact_exception_returns_error(self):
        req = _request_raising()
        result = await shop_redact(req, verified=True)
        assert result["status"] == "error"


# ---------------------------------------------------------------------------
# api/dependencies/webhook_security.py
# ---------------------------------------------------------------------------


from src.modules.connections.api.dependencies.webhook_security import (
    verify_meta_signature,
    verify_shopify_signature,
)


def _req_shopify(signature=None, body=b"payload", secret="shopify_secret"):
    req = MagicMock()
    req.headers = {"X-Shopify-Hmac-Sha256": signature} if signature else {}
    req.body = AsyncMock(return_value=body)
    return req


def _req_meta(signature_header=None, body=b"payload"):
    req = MagicMock()
    req.headers = {"X-Hub-Signature-256": signature_header} if signature_header else {}
    req.body = AsyncMock(return_value=body)
    return req


class TestVerifyShopifySignature:
    @pytest.mark.asyncio
    async def test_raises_401_when_no_signature(self):
        from fastapi import HTTPException

        req = _req_shopify(signature=None)
        with pytest.raises(HTTPException) as exc_info:
            await verify_shopify_signature(req)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_500_when_no_secret_configured(self):
        from fastapi import HTTPException

        req = _req_shopify(signature="somesig")

        with patch("src.modules.connections.api.dependencies.webhook_security.settings") as mock_settings:
            mock_settings.SHOPIFY_API_SECRET = None
            with pytest.raises(HTTPException) as exc_info:
                await verify_shopify_signature(req)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_raises_401_when_signature_invalid(self):
        from fastapi import HTTPException

        req = _req_shopify(signature="invalidsig")

        with patch("src.modules.connections.api.dependencies.webhook_security.settings") as mock_settings:
            mock_settings.SHOPIFY_API_SECRET = "mysecret"
            with pytest.raises(HTTPException) as exc_info:
                await verify_shopify_signature(req)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_true_when_signature_valid(self):
        import base64
        import hashlib
        import hmac as hmac_lib

        body = b"mypayload"
        secret = "shopify_test_secret"
        digest = hmac_lib.new(secret.encode(), body, hashlib.sha256).digest()
        sig = base64.b64encode(digest).decode()

        req = _req_shopify(signature=sig, body=body)

        with patch("src.modules.connections.api.dependencies.webhook_security.settings") as mock_settings:
            mock_settings.SHOPIFY_API_SECRET = secret
            result = await verify_shopify_signature(req)
        assert result is True


class TestVerifyMetaSignature:
    @pytest.mark.asyncio
    async def test_raises_401_when_no_signature(self):
        from fastapi import HTTPException

        req = _req_meta(signature_header=None)
        with pytest.raises(HTTPException) as exc_info:
            await verify_meta_signature(req)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_500_when_no_secret_configured(self):
        from fastapi import HTTPException

        req = _req_meta(signature_header="sha256=abc")

        with patch("src.modules.connections.api.dependencies.webhook_security.settings") as mock_settings:
            mock_settings.META_APP_SECRET = None
            with pytest.raises(HTTPException) as exc_info:
                await verify_meta_signature(req)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_raises_401_when_signature_format_invalid(self):
        from fastapi import HTTPException

        req = _req_meta(signature_header="noprefix=abc")

        with patch("src.modules.connections.api.dependencies.webhook_security.settings") as mock_settings:
            mock_settings.META_APP_SECRET = "mysecret"
            with pytest.raises(HTTPException) as exc_info:
                await verify_meta_signature(req)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_raises_401_when_signature_invalid(self):
        from fastapi import HTTPException

        req = _req_meta(signature_header="sha256=badsig")

        with patch("src.modules.connections.api.dependencies.webhook_security.settings") as mock_settings:
            mock_settings.META_APP_SECRET = "mysecret"
            with pytest.raises(HTTPException) as exc_info:
                await verify_meta_signature(req)
        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_returns_true_when_signature_valid(self):
        import hashlib
        import hmac as hmac_lib

        body = b"metapayload"
        secret = "meta_test_secret"
        digest = hmac_lib.new(secret.encode(), body, hashlib.sha256).hexdigest()
        sig_header = f"sha256={digest}"

        req = _req_meta(signature_header=sig_header, body=body)

        with patch("src.modules.connections.api.dependencies.webhook_security.settings") as mock_settings:
            mock_settings.META_APP_SECRET = secret
            result = await verify_meta_signature(req)
        assert result is True


# ---------------------------------------------------------------------------
# copilot_provider/provider.py
# ---------------------------------------------------------------------------


from src.modules.connections.copilot_provider.provider import (
    ConnectionsCopilotProvider,
    _connections_read_fn,
    _connections_repo_factory,
)


class TestConnectionsCopilotProvider:
    def test_module_id(self):
        provider = ConnectionsCopilotProvider()
        assert provider.module_id == "connections"

    def test_label(self):
        provider = ConnectionsCopilotProvider()
        assert provider.label == "Conexiones"

    def test_module_data_returns_module_data(self):
        provider = ConnectionsCopilotProvider()
        data = provider.module_data()
        assert data is not None
        assert data.module_id == "connections"
        assert data.label == "Conexiones"

    def test_repo_factory_returns_repository(self):
        db = MagicMock()
        repo = _connections_repo_factory(db)
        assert repo is not None

    def test_read_fn_calls_get_all_by_tenant(self):
        repo = MagicMock()
        tid = uuid.uuid4()
        _connections_read_fn(repo, tid)
        repo.get_all_by_tenant.assert_called_once_with(tid)


# ---------------------------------------------------------------------------
# infrastructure/channels/webhook.py
# ---------------------------------------------------------------------------


from src.modules.connections.infrastructure.channels.webhook import WebhookAdapter
from src.shared.domain.messages import OutgoingMessage


class TestWebhookAdapter:
    def test_init_creates_empty_responses(self):
        adapter = WebhookAdapter()
        assert adapter.responses == []

    @pytest.mark.asyncio
    async def test_send_message_appends_text(self):
        adapter = WebhookAdapter()
        msg = OutgoingMessage(user_id="u1", text="Hello!", channel_type="webhook")
        await adapter.send_message(msg)
        assert adapter.responses == ["Hello!"]

    @pytest.mark.asyncio
    async def test_set_typing_status_is_noop(self):
        adapter = WebhookAdapter()
        await adapter.set_typing_status("user1")

    def test_normalize_payload_returns_none(self):
        adapter = WebhookAdapter()
        result = adapter.normalize_payload({"any": "payload"})
        assert result is None
