"""Tests for Clerk webhook handler."""

from unittest.mock import MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_platform.core.database import get_db
from luana_core_iam.api.webhooks import router

_VALID_HEADERS = {
    "svix-id": "msg_123",
    "svix-timestamp": "1234567890",
    "svix-signature": "v1,abc123",
}

_USER_CREATED_PAYLOAD = {
    "type": "user.created",
    "data": {
        "id": "clerk_abc",
        "first_name": "Alice",
        "last_name": "Test",
        "primary_email_address_id": "em_1",
        "email_addresses": [{"id": "em_1", "email_address": "alice@example.com"}],
    },
}

_USER_DELETED_PAYLOAD = {
    "type": "user.deleted",
    "data": {"id": "clerk_abc"},
}


@pytest.fixture
def client(db):
    app = FastAPI()
    app.include_router(router, prefix="/webhooks")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def _patch_webhook(payload):
    """Return context manager that makes Webhook.verify return payload."""
    wh_instance = MagicMock()
    wh_instance.verify.return_value = payload
    return patch("luana_core_iam.api.webhooks.Webhook", return_value=wh_instance)


class TestWebhookMissingHeaders:
    def test_missing_all_svix_headers_returns_400(self, client):
        resp = client.post("/webhooks/clerk", content=b"{}")
        assert resp.status_code == 400
        assert "svix" in resp.json()["detail"].lower()

    def test_missing_one_svix_header_returns_400(self, client):
        headers = {"svix-id": "msg_1", "svix-timestamp": "123"}  # missing signature
        resp = client.post("/webhooks/clerk", content=b"{}", headers=headers)
        assert resp.status_code == 400


class TestWebhookSecretMissing:
    def test_no_webhook_secret_returns_500(self, client):
        with patch("luana_core_iam.api.webhooks.settings") as mock_settings:
            mock_settings.CLERK_WEBHOOK_SECRET = None
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 500


class TestWebhookInvalidSignature:
    def test_bad_signature_returns_400(self, client):
        from svix.webhooks import WebhookVerificationError

        wh_instance = MagicMock()
        wh_instance.verify.side_effect = WebhookVerificationError("bad sig")

        with (
            patch("luana_core_iam.api.webhooks.settings") as mock_settings,
            patch(
                "luana_core_iam.api.webhooks.Webhook",
                return_value=wh_instance,
            ),
        ):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 400
        assert "signature" in resp.json()["detail"].lower()


class TestWebhookUserCreated:
    def test_new_user_created_returns_200(self, client):
        with patch("luana_core_iam.api.webhooks.settings") as mock_settings, _patch_webhook(_USER_CREATED_PAYLOAD):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 200
        assert resp.json() == {"status": "success"}

    def test_user_created_existing_by_email_links(self, client, db, seed_user):
        """user.created for existing email → update (link by email)."""
        payload = {
            "type": "user.created",
            "data": {
                "id": "clerk_new_id",
                "first_name": "Alice",
                "last_name": "Test",
                "primary_email_address_id": "em_1",
                "email_addresses": [{"id": "em_1", "email_address": "alice@example.com"}],
            },
        }
        with patch("luana_core_iam.api.webhooks.settings") as mock_settings, _patch_webhook(payload):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 200

    def test_user_created_primary_email_fallback(self, client):
        """Falls back to first email when primary_email_address_id not matched."""
        payload = {
            "type": "user.created",
            "data": {
                "id": "clerk_xyz",
                "first_name": "Bob",
                "last_name": "Smith",
                "primary_email_address_id": "em_999",  # no match
                "email_addresses": [{"id": "em_1", "email_address": "bob@example.com"}],
            },
        }
        with patch("luana_core_iam.api.webhooks.settings") as mock_settings, _patch_webhook(payload):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 200


class TestWebhookUserUpdated:
    def test_user_updated_existing_user(self, client, seed_user):
        payload = {
            "type": "user.updated",
            "data": {
                "id": "clerk_alice_001",
                "first_name": "Alice",
                "last_name": "Updated",
                "primary_email_address_id": "em_1",
                "email_addresses": [{"id": "em_1", "email_address": "alice@example.com"}],
            },
        }
        with patch("luana_core_iam.api.webhooks.settings") as mock_settings, _patch_webhook(payload):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 200


class TestWebhookUserDeleted:
    def test_user_deleted_deactivates(self, client, seed_user):
        with patch("luana_core_iam.api.webhooks.settings") as mock_settings, _patch_webhook(_USER_DELETED_PAYLOAD):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 200

    def test_user_deleted_not_found_still_200(self, client):
        payload = {"type": "user.deleted", "data": {"id": "clerk_nonexistent"}}
        with patch("luana_core_iam.api.webhooks.settings") as mock_settings, _patch_webhook(payload):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 200


class TestWebhookUnknownType:
    def test_unknown_event_type_ignored(self, client):
        payload = {"type": "session.created", "data": {"id": "sess_1"}}
        with patch("luana_core_iam.api.webhooks.settings") as mock_settings, _patch_webhook(payload):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 200


class TestWebhookInternalError:
    def test_processing_exception_returns_500(self, client):
        payload = {
            "type": "user.created",
            "data": {
                "id": "clerk_err",
                "first_name": "Err",
                "last_name": "User",
                "primary_email_address_id": "em_1",
                "email_addresses": [{"id": "em_1", "email_address": "err@example.com"}],
            },
        }
        with (
            patch("luana_core_iam.api.webhooks.settings") as mock_settings,
            _patch_webhook(payload),
            patch(
                "luana_core_iam.api.webhooks._handle_user_sync",
                side_effect=RuntimeError("boom"),
            ),
        ):
            mock_settings.CLERK_WEBHOOK_SECRET = "test_secret"
            resp = client.post(
                "/webhooks/clerk",
                content=b"{}",
                headers=_VALID_HEADERS,
            )
        assert resp.status_code == 500
