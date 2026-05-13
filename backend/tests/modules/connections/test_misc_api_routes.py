"""Tests for miscellaneous connections API routes:
gmail, telegram, status (batch), mailerlite, manychat, webhook.
"""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import HTTPException

from luana_core_connections.api.gmail import (
    disconnect,
    get_auth_url,
    get_status,
    oauth_callback,
)
from luana_core_connections.api.gmail import test_connection as gmail_test_connection
from luana_core_connections.api.mailerlite import (
    connect_mailerlite,
    disconnect_mailerlite,
    get_mailerlite_status,
)
from luana_core_connections.api.mailerlite import test_mailerlite_connection as ml_test_connection
from luana_core_connections.api.manychat import (
    connect_manychat,
    disconnect_manychat,
    get_manychat_status,
)
from luana_core_connections.api.manychat import test_manychat_connection as mc_test_connection
from luana_core_connections.api.status import (
    BatchConnectionStatusResponse,
    _mask_pii,
    get_all_connections_status,
)
from luana_core_connections.api.telegram import (
    connect_telegram,
    disconnect_telegram,
    get_telegram_status,
)
from luana_core_connections.api.telegram import test_telegram_connection as tg_test_connection
from luana_core_connections.api.webhook import get_tenant_by_secret, webhook_chat

TENANT_ID = uuid4()


def _user():
    return SimpleNamespace(tenant_id=TENANT_ID, id=uuid4())


def _repo(**kwargs):
    repo = MagicMock()
    for k, v in kwargs.items():
        setattr(repo, k, v)
    return repo


def _conn(config=None, credentials=None):
    c = MagicMock()
    c.config = {} if config is None else config
    c.credentials = {"api_key": "key123"} if credentials is None else credentials
    return c


# ─────────────────────────────────────────────────────────────────────────────
# Gmail API
# ─────────────────────────────────────────────────────────────────────────────


class TestGmailGetAuthUrl:
    @pytest.mark.asyncio
    async def test_returns_url_and_state(self):
        user = _user()
        with patch(
            "luana_core_connections.api.gmail.GmailAdapter.get_authorization_url",
            return_value=("https://accounts.google.com/auth", "state_123"),
        ):
            result = await get_auth_url(user, redirect_uri=None)
        assert result["url"] == "https://accounts.google.com/auth"
        assert result["state"] == "state_123"


class TestGmailOAuthCallback:
    @pytest.mark.asyncio
    async def test_raises_400_on_exchange_failure(self):
        repo = _repo(upsert=MagicMock())
        user = _user()
        with (
            patch("luana_core_connections.api.gmail.GmailAdapter.exchange_code", side_effect=Exception("bad code")),
            pytest.raises(HTTPException) as exc_info,
        ):
            await oauth_callback("bad_code", user, repo, redirect_uri=None)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_400_when_profile_fails(self):
        repo = _repo(upsert=MagicMock())
        user = _user()
        creds = {"access_token": "at"}
        with (
            patch("luana_core_connections.api.gmail.GmailAdapter.exchange_code", return_value=creds),
            patch("luana_core_connections.api.gmail.GmailAdapter") as MockAdapter,
        ):
            MockAdapter.return_value.get_profile.side_effect = Exception("API error")
            with pytest.raises(HTTPException) as exc_info:
                await oauth_callback("code123", user, repo, redirect_uri=None)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_connects_successfully(self):
        repo = _repo(upsert=MagicMock())
        user = _user()
        creds = {"access_token": "at"}
        with (
            patch("luana_core_connections.api.gmail.GmailAdapter.exchange_code", return_value=creds),
            patch("luana_core_connections.api.gmail.GmailAdapter") as MockAdapter,
        ):
            MockAdapter.return_value.get_profile.return_value = {"emailAddress": "user@gmail.com"}
            result = await oauth_callback("code123", user, repo, redirect_uri=None)
        assert result["status"] == "connected"
        assert result["email"] == "user@gmail.com"
        repo.upsert.assert_called_once()


class TestGmailGetStatus:
    @pytest.mark.asyncio
    async def test_not_connected_when_no_connection(self):
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))
        result = await get_status(user, repo)
        assert result.is_connected is False

    @pytest.mark.asyncio
    async def test_connected_returns_email(self):
        user = _user()
        conn = _conn(config={"email": "me@gmail.com"})
        repo = _repo(get_active=MagicMock(return_value=conn))
        result = await get_status(user, repo)
        assert result.is_connected is True
        assert result.email == "me@gmail.com"


class TestGmailDisconnect:
    @pytest.mark.asyncio
    async def test_disconnects_when_connected(self):
        user = _user()
        conn = _conn()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn), deactivate=MagicMock())
        result = await disconnect(user, repo)
        repo.deactivate.assert_called_once_with(conn)
        assert result["status"] == "disconnected"

    @pytest.mark.asyncio
    async def test_returns_disconnected_when_no_connection(self):
        user = _user()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        result = await disconnect(user, repo)
        assert result["status"] == "disconnected"


class TestGmailTestConnection:
    @pytest.mark.asyncio
    async def test_raises_400_when_no_connection(self):
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await gmail_test_connection(user, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_ok_on_success(self):
        user = _user()
        conn = _conn(credentials={"access_token": "tok"})
        repo = _repo(get_active=MagicMock(return_value=conn))
        with patch("luana_core_connections.api.gmail.GmailAdapter") as MockAdapter:
            MockAdapter.return_value.get_profile.return_value = {"emailAddress": "user@gmail.com"}
            result = await gmail_test_connection(user, repo)
        assert result["status"] == "ok"

    @pytest.mark.asyncio
    async def test_returns_error_on_exception(self):
        user = _user()
        conn = _conn(credentials={"access_token": "tok"})
        repo = _repo(get_active=MagicMock(return_value=conn))
        with patch("luana_core_connections.api.gmail.GmailAdapter") as MockAdapter:
            MockAdapter.return_value.get_profile.side_effect = Exception("API error")
            result = await gmail_test_connection(user, repo)
        assert result["status"] == "error"


# ─────────────────────────────────────────────────────────────────────────────
# Telegram API
# ─────────────────────────────────────────────────────────────────────────────


class TestTelegramGetStatus:
    @pytest.mark.asyncio
    async def test_not_connected_when_no_connection(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.get_status.return_value = {"is_connected": False}
            result = await get_telegram_status(db, user)
        assert result.is_connected is False

    @pytest.mark.asyncio
    async def test_connected_returns_status(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.get_status.return_value = {
                "is_connected": True,
                "bot_name": "TestBot",
                "username": "testbot",
            }
            result = await get_telegram_status(db, user)
        assert result.is_connected is True


class TestTelegramConnect:
    @pytest.mark.asyncio
    async def test_raises_400_on_value_error(self):
        user = _user()
        db = MagicMock()
        payload = MagicMock()
        payload.token = "bad_token"
        background_tasks = MagicMock()

        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.connect = AsyncMock(side_effect=ValueError("invalido"))
            with pytest.raises(HTTPException) as exc_info:
                await connect_telegram(payload, background_tasks, db, user)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_raises_503_on_runtime_error(self):
        user = _user()
        db = MagicMock()
        payload = MagicMock()
        payload.token = "tok"
        background_tasks = MagicMock()

        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.connect = AsyncMock(side_effect=RuntimeError("Error conectando"))
            with pytest.raises(HTTPException) as exc_info:
                await connect_telegram(payload, background_tasks, db, user)
        assert exc_info.value.status_code == 503

    @pytest.mark.asyncio
    async def test_raises_500_on_generic_exception(self):
        user = _user()
        db = MagicMock()
        payload = MagicMock()
        payload.token = "tok"
        background_tasks = MagicMock()

        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.connect = AsyncMock(side_effect=Exception("unexpected"))
            with pytest.raises(HTTPException) as exc_info:
                await connect_telegram(payload, background_tasks, db, user)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_returns_result_on_success(self):
        user = _user()
        db = MagicMock()
        payload = MagicMock()
        payload.token = "valid_token"
        background_tasks = MagicMock()

        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.connect = AsyncMock(return_value={"status": "connected", "bot": {}})
            result = await connect_telegram(payload, background_tasks, db, user)
        assert result["status"] == "connected"


class TestTelegramTestConnection:
    @pytest.mark.asyncio
    async def test_raises_404_on_value_error(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.test_connection = AsyncMock(side_effect=ValueError("No hay conexion"))
            with pytest.raises(HTTPException) as exc_info:
                await tg_test_connection(db, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_500_on_runtime_error(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.test_connection = AsyncMock(side_effect=RuntimeError("corruptas"))
            with pytest.raises(HTTPException) as exc_info:
                await tg_test_connection(db, user)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_returns_error_on_generic_exception(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.test_connection = AsyncMock(side_effect=Exception("unknown"))
            result = await tg_test_connection(db, user)
        assert result["status"] == "error"

    @pytest.mark.asyncio
    async def test_returns_ok_on_success(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.test_connection = AsyncMock(return_value={"status": "ok"})
            result = await tg_test_connection(db, user)
        assert result["status"] == "ok"


class TestTelegramDisconnect:
    @pytest.mark.asyncio
    async def test_raises_404_on_value_error(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.disconnect = AsyncMock(side_effect=ValueError("No hay conexion"))
            with pytest.raises(HTTPException) as exc_info:
                await disconnect_telegram(db, user)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_500_on_generic_exception(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.disconnect = AsyncMock(side_effect=Exception("unexpected"))
            with pytest.raises(HTTPException) as exc_info:
                await disconnect_telegram(db, user)
        assert exc_info.value.status_code == 500

    @pytest.mark.asyncio
    async def test_disconnects_successfully(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.telegram.TelegramService") as MockSvc:
            MockSvc.return_value.disconnect = AsyncMock(return_value={"status": "disconnected"})
            result = await disconnect_telegram(db, user)
        assert result["status"] == "disconnected"


# ─────────────────────────────────────────────────────────────────────────────
# Batch Status API
# ─────────────────────────────────────────────────────────────────────────────


class TestMaskPii:
    def test_masks_gmail_email(self):
        result = _mask_pii("user@gmail.com", "gmail")
        assert result == "u***@gmail.com"

    def test_masks_google_calendar_email(self):
        result = _mask_pii("contact@example.com", "google_calendar")
        assert result == "c***@example.com"

    def test_masks_whatsapp_phone(self):
        result = _mask_pii("5199999999", "whatsapp")
        assert "***" in result
        assert result.startswith("51")
        assert result.endswith("99")

    def test_masks_short_whatsapp_phone(self):
        result = _mask_pii("12", "whatsapp")
        assert result == "***"

    def test_returns_value_unchanged_for_other_types(self):
        result = _mask_pii("MyShop", "shopify")
        assert result == "MyShop"


class TestGetAllConnectionsStatus:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_connections(self):
        user = _user()
        db = MagicMock()
        with patch("luana_core_connections.api.status.ChannelConnectionRepository") as MockRepo:
            MockRepo.return_value.get_all_by_tenant.return_value = []
            result = await get_all_connections_status(user, db)
        assert result.connections == []

    @pytest.mark.asyncio
    async def test_returns_connections_with_display_names(self):
        user = _user()
        db = MagicMock()

        conn1 = MagicMock()
        conn1.channel_type = "gmail"
        conn1.is_active = True
        conn1.config = {"email": "user@gmail.com", "last_sync": "2024-01-01"}

        conn2 = MagicMock()
        conn2.channel_type = "shopify"
        conn2.is_active = False
        conn2.config = {"shop_url": "myshop.myshopify.com"}

        with patch("luana_core_connections.api.status.ChannelConnectionRepository") as MockRepo:
            MockRepo.return_value.get_all_by_tenant.return_value = [conn1, conn2]
            result = await get_all_connections_status(user, db)

        assert len(result.connections) == 2
        gmail_conn = next(c for c in result.connections if c.channel_type == "gmail")
        assert gmail_conn.is_connected is True
        assert "***" in gmail_conn.display_name  # PII masked

    @pytest.mark.asyncio
    async def test_handles_unknown_channel_type(self):
        user = _user()
        db = MagicMock()

        conn = MagicMock()
        conn.channel_type = "custom_channel"
        conn.is_active = True
        conn.config = {}

        with patch("luana_core_connections.api.status.ChannelConnectionRepository") as MockRepo:
            MockRepo.return_value.get_all_by_tenant.return_value = [conn]
            result = await get_all_connections_status(user, db)

        assert len(result.connections) == 1
        assert result.connections[0].display_name is None

    @pytest.mark.asyncio
    async def test_includes_last_sync(self):
        user = _user()
        db = MagicMock()

        conn = MagicMock()
        conn.channel_type = "shopify"
        conn.is_active = True
        conn.config = {"shop_url": "myshop", "last_extraction_at": "2024-01-01T00:00:00Z"}

        with patch("luana_core_connections.api.status.ChannelConnectionRepository") as MockRepo:
            MockRepo.return_value.get_all_by_tenant.return_value = [conn]
            result = await get_all_connections_status(user, db)

        assert result.connections[0].last_sync is not None


# ─────────────────────────────────────────────────────────────────────────────
# MailerLite API
# ─────────────────────────────────────────────────────────────────────────────


class TestMailerliteGetStatus:
    @pytest.mark.asyncio
    async def test_not_connected_when_no_connection(self):
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))
        result = await get_mailerlite_status(user, repo)
        assert result.is_connected is False

    @pytest.mark.asyncio
    async def test_connected_returns_account_info(self):
        user = _user()
        conn = _conn(config={"account_info": {"name": "My Account"}})
        repo = _repo(get_active=MagicMock(return_value=conn))
        result = await get_mailerlite_status(user, repo)
        assert result.is_connected is True
        assert result.account_info == {"name": "My Account"}


class TestMailerliteConnect:
    @pytest.mark.asyncio
    async def test_raises_400_on_invalid_api_key(self):
        user = _user()
        repo = _repo()
        request = MagicMock()
        request.api_key = "bad_key"
        with (
            patch(
                "luana_core_connections.api.mailerlite.MailerliteConnector.verify_connection",
                new_callable=AsyncMock,
                return_value=(False, {"error": "Unauthorized"}),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await connect_mailerlite(request, user, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_connects_successfully(self):
        user = _user()
        repo = _repo(upsert=MagicMock())
        request = MagicMock()
        request.api_key = "valid_key"
        with patch(
            "luana_core_connections.api.mailerlite.MailerliteConnector.verify_connection",
            new_callable=AsyncMock,
            return_value=(True, {"account_name": "MyAcc"}),
        ):
            result = await connect_mailerlite(request, user, repo)
        assert result.status == "connected"
        repo.upsert.assert_called_once()


class TestMailerliteDisconnect:
    @pytest.mark.asyncio
    async def test_raises_404_when_no_connection(self):
        user = _user()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await disconnect_mailerlite(user, repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_disconnects_successfully(self):
        user = _user()
        conn = _conn()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn), deactivate=MagicMock())
        result = await disconnect_mailerlite(user, repo)
        repo.deactivate.assert_called_once_with(conn)
        assert result.status == "disconnected"


class TestMailerliteTestConnection:
    @pytest.mark.asyncio
    async def test_raises_404_when_no_connection(self):
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await ml_test_connection(user, repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_400_when_no_api_key(self):
        user = _user()
        conn = _conn(credentials={})
        repo = _repo(get_active=MagicMock(return_value=conn))
        with pytest.raises(HTTPException) as exc_info:
            await ml_test_connection(user, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_active_when_valid(self):
        user = _user()
        conn = _conn(credentials={"api_key": "key"})
        repo = _repo(get_active=MagicMock(return_value=conn), update_config=MagicMock())
        with patch(
            "luana_core_connections.api.mailerlite.MailerliteConnector.verify_connection",
            new_callable=AsyncMock,
            return_value=(True, {"account_name": "Acc"}),
        ):
            result = await ml_test_connection(user, repo)
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_returns_error_when_invalid(self):
        user = _user()
        conn = _conn(credentials={"api_key": "bad"})
        repo = _repo(get_active=MagicMock(return_value=conn))
        with patch(
            "luana_core_connections.api.mailerlite.MailerliteConnector.verify_connection",
            new_callable=AsyncMock,
            return_value=(False, {"error": "Unauthorized"}),
        ):
            result = await ml_test_connection(user, repo)
        assert result.status == "error"


# ─────────────────────────────────────────────────────────────────────────────
# ManyChat API
# ─────────────────────────────────────────────────────────────────────────────


class TestManychatGetStatus:
    @pytest.mark.asyncio
    async def test_not_connected_when_no_connection(self):
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))
        result = await get_manychat_status(user, repo)
        assert result.is_connected is False

    @pytest.mark.asyncio
    async def test_connected_returns_account_info(self):
        user = _user()
        conn = _conn(config={"account_info": {"page": "MyPage"}})
        repo = _repo(get_active=MagicMock(return_value=conn))
        result = await get_manychat_status(user, repo)
        assert result.is_connected is True


class TestManychatConnect:
    @pytest.mark.asyncio
    async def test_raises_400_on_invalid_api_key(self):
        user = _user()
        repo = _repo()
        request = MagicMock()
        request.api_key = "bad_key"
        with (
            patch(
                "luana_core_connections.api.manychat.ManyChatConnector.verify_connection",
                new_callable=AsyncMock,
                return_value=(False, {"error": "Unauthorized"}),
            ),
            pytest.raises(HTTPException) as exc_info,
        ):
            await connect_manychat(request, user, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_connects_successfully(self):
        user = _user()
        repo = _repo(upsert=MagicMock())
        request = MagicMock()
        request.api_key = "valid_key"
        with patch(
            "luana_core_connections.api.manychat.ManyChatConnector.verify_connection",
            new_callable=AsyncMock,
            return_value=(True, {"page": "MyPage"}),
        ):
            result = await connect_manychat(request, user, repo)
        assert result.status == "connected"
        repo.upsert.assert_called_once()


class TestManychatDisconnect:
    @pytest.mark.asyncio
    async def test_raises_404_when_no_connection(self):
        user = _user()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await disconnect_manychat(user, repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_disconnects_successfully(self):
        user = _user()
        conn = _conn()
        repo = _repo(get_by_tenant_and_type=MagicMock(return_value=conn), deactivate=MagicMock())
        result = await disconnect_manychat(user, repo)
        repo.deactivate.assert_called_once_with(conn)
        assert result.status == "disconnected"


class TestManychatTestConnection:
    @pytest.mark.asyncio
    async def test_raises_404_when_no_connection(self):
        user = _user()
        repo = _repo(get_active=MagicMock(return_value=None))
        with pytest.raises(HTTPException) as exc_info:
            await mc_test_connection(user, repo)
        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    async def test_raises_400_when_no_api_key(self):
        user = _user()
        conn = _conn(credentials={})
        repo = _repo(get_active=MagicMock(return_value=conn))
        with pytest.raises(HTTPException) as exc_info:
            await mc_test_connection(user, repo)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_returns_active_when_valid(self):
        user = _user()
        conn = _conn(credentials={"api_key": "key"})
        repo = _repo(get_active=MagicMock(return_value=conn), update_config=MagicMock())
        with patch(
            "luana_core_connections.api.manychat.ManyChatConnector.verify_connection",
            new_callable=AsyncMock,
            return_value=(True, {"page": "P1"}),
        ):
            result = await mc_test_connection(user, repo)
        assert result.status == "active"

    @pytest.mark.asyncio
    async def test_returns_error_when_invalid(self):
        user = _user()
        conn = _conn(credentials={"api_key": "bad"})
        repo = _repo(get_active=MagicMock(return_value=conn))
        with patch(
            "luana_core_connections.api.manychat.ManyChatConnector.verify_connection",
            new_callable=AsyncMock,
            return_value=(False, {"error": "Unauthorized"}),
        ):
            result = await mc_test_connection(user, repo)
        assert result.status == "error"


# ─────────────────────────────────────────────────────────────────────────────
# Webhook API
# ─────────────────────────────────────────────────────────────────────────────


class TestGetTenantBySecret:
    def _patch_webhook(self, db, tenant_result):
        # Mock both select and Tenant to bypass SQLAlchemy column validation
        db.execute.return_value.scalars.return_value.first.return_value = tenant_result
        import contextlib
        from unittest.mock import patch as _patch

        @contextlib.contextmanager
        def _ctx():
            with (
                _patch("luana_core_connections.api.webhook.select", return_value=MagicMock()),
                _patch("luana_core_connections.api.webhook.Tenant", MagicMock()),
            ):
                yield

        return _ctx()

    def test_raises_401_when_no_tenant(self):
        db = MagicMock()
        with self._patch_webhook(db, None), pytest.raises(HTTPException) as exc_info:
            get_tenant_by_secret("bad_secret", db)
        assert exc_info.value.status_code == 401

    def test_raises_403_when_tenant_inactive(self):
        db = MagicMock()
        tenant = MagicMock()
        tenant.is_active = False
        tenant.id = uuid4()
        with self._patch_webhook(db, tenant), pytest.raises(HTTPException) as exc_info:
            get_tenant_by_secret("secret", db)
        assert exc_info.value.status_code == 403

    def test_returns_tenant_when_valid(self):
        db = MagicMock()
        tenant = MagicMock()
        tenant.is_active = True
        tenant.id = uuid4()
        with (
            self._patch_webhook(db, tenant),
            patch("luana_core_connections.api.webhook.set_tenant_id"),
            patch("structlog.contextvars.bind_contextvars"),
        ):
            result = get_tenant_by_secret("valid_secret", db)
        assert result is tenant


class TestWebhookChat:
    @pytest.mark.asyncio
    async def test_raises_400_when_missing_fields(self):
        tenant = MagicMock()
        handler = MagicMock()
        with pytest.raises(HTTPException) as exc_info:
            await webhook_chat({}, tenant, handler)
        assert exc_info.value.status_code == 400

    @pytest.mark.asyncio
    async def test_processes_chat_and_returns_response(self):
        tenant = MagicMock()
        tenant.id = uuid4()
        handler = MagicMock()
        handler.process_chat_flow = AsyncMock()

        with patch("luana_core_connections.api.webhook.WebhookAdapter") as MockAdapter:
            mock_adapter = MagicMock()
            mock_adapter.responses = ["Hello, how can I help?"]
            MockAdapter.return_value = mock_adapter
            result = await webhook_chat({"user_id": "u1", "message": "Hi"}, tenant, handler)

        assert "response" in result
        assert result["response"] == "Hello, how can I help?"

    @pytest.mark.asyncio
    async def test_raises_500_on_handler_exception(self):
        tenant = MagicMock()
        tenant.id = uuid4()
        handler = MagicMock()
        handler.process_chat_flow = AsyncMock(side_effect=Exception("agent error"))

        with patch("luana_core_connections.api.webhook.WebhookAdapter"), pytest.raises(HTTPException) as exc_info:
            await webhook_chat({"user_id": "u1", "message": "Hi"}, tenant, handler)
        assert exc_info.value.status_code == 500
