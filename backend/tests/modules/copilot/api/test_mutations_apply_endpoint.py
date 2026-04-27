"""Tests for POST /api/v1/copilot/conversations/{id}/mutations/apply (B22-FP1)."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.copilot.api.conversations import router
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id):
    """Wire FastAPI test client with mocked auth/db deps."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot")
    user_id = uuid4()
    mock_db = MagicMock()

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=user_id,
        tenant_id=tenant_id,
    )
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id

    return TestClient(app), user_id, mock_db


def _conv_stub(conv_id, tenant_id):
    """Return a dummy conversation row that the repo lookup will yield."""
    return SimpleNamespace(
        id=conv_id,
        tenant_id=tenant_id,
        title=None,
    )


class TestApplyMutationsContract:
    """Endpoint exists, returns ApplyMutationsResponse, requires auth."""

    def test_returns_404_when_conversation_missing(self) -> None:
        tenant_id = uuid4()
        conv_id = uuid4()
        client, _uid, _db = _build_client(tenant_id)

        with patch(
            "src.modules.copilot.api.conversations.ConversationRepository",
        ) as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_cls.return_value = mock_repo

            resp = client.post(
                f"/api/v1/copilot/conversations/{conv_id}/mutations/apply",
                json={"message_id": str(uuid4()), "updates": []},
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 404

    def test_returns_401_without_tenant(self) -> None:
        """Endpoint requires X-Tenant-ID context."""
        conv_id = uuid4()
        app = FastAPI()
        app.include_router(router, prefix="/api/v1/copilot")
        mock_db = MagicMock()
        mock_user = SimpleNamespace(id=uuid4(), tenant_id=None)

        def _db_override() -> MagicMock:
            return mock_db

        def _user_override() -> SimpleNamespace:
            return mock_user

        def _tenant_override() -> None:
            return None

        app.dependency_overrides[get_db] = _db_override
        app.dependency_overrides[get_current_user] = _user_override
        app.dependency_overrides[get_tenant_context] = _tenant_override
        client = TestClient(app)

        resp = client.post(
            f"/api/v1/copilot/conversations/{conv_id}/mutations/apply",
            json={"message_id": str(uuid4()), "updates": []},
        )
        assert resp.status_code == 401


class TestApplyMutationsHappyPath:
    """Valid updates persist via the apply service and respond with applied rows."""

    def test_returns_applied_mutation_ids(self) -> None:
        tenant_id = uuid4()
        conv_id = uuid4()
        msg_id = uuid4()
        client, _uid, _db = _build_client(tenant_id)

        applied_id = uuid4()

        with (
            patch(
                "src.modules.copilot.api.conversations.ConversationRepository",
            ) as mock_repo_cls,
            patch(
                "src.modules.copilot.api.conversations.MutationApplyService",
            ) as mock_svc_cls,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = _conv_stub(conv_id, tenant_id)
            mock_repo_cls.return_value = mock_repo

            mock_svc = MagicMock()
            mock_svc.apply.return_value = SimpleNamespace(
                applied=[
                    SimpleNamespace(
                        id=applied_id,
                        field_path="identity.brand_name",
                        domain="brand",
                        status="applied",
                    ),
                ],
                rejected=[],
            )
            mock_svc_cls.return_value = mock_svc

            resp = client.post(
                f"/api/v1/copilot/conversations/{conv_id}/mutations/apply",
                json={
                    "message_id": str(msg_id),
                    "updates": [
                        {
                            "field_id": "identity.brand_name",
                            "new_value": "Visionarias",
                        },
                    ],
                },
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["applied"]) == 1
        assert body["applied"][0]["id"] == str(applied_id)
        assert body["applied"][0]["field_path"] == "identity.brand_name"
        assert body["applied"][0]["domain"] == "brand"
        assert body["applied"][0]["status"] == "applied"
        assert body["rejected"] == []

    def test_rejects_unknown_field_id(self) -> None:
        tenant_id = uuid4()
        conv_id = uuid4()
        msg_id = uuid4()
        client, _uid, _db = _build_client(tenant_id)

        with (
            patch(
                "src.modules.copilot.api.conversations.ConversationRepository",
            ) as mock_repo_cls,
            patch(
                "src.modules.copilot.api.conversations.MutationApplyService",
            ) as mock_svc_cls,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = _conv_stub(conv_id, tenant_id)
            mock_repo_cls.return_value = mock_repo

            mock_svc = MagicMock()
            mock_svc.apply.return_value = SimpleNamespace(
                applied=[],
                rejected=[
                    SimpleNamespace(
                        field_id="bogus.path",
                        reason="No está en el catálogo editable.",
                    ),
                ],
            )
            mock_svc_cls.return_value = mock_svc

            resp = client.post(
                f"/api/v1/copilot/conversations/{conv_id}/mutations/apply",
                json={
                    "message_id": str(msg_id),
                    "updates": [
                        {"field_id": "bogus.path", "new_value": "x"},
                    ],
                },
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["applied"] == []
        assert len(body["rejected"]) == 1
        assert body["rejected"][0]["field_id"] == "bogus.path"


class TestApplyMutationsIdempotency:
    """Same (conv, message, field_path) repeated → service returns existing row."""

    def test_idempotent_repeated_call_returns_existing(self) -> None:
        """The endpoint forwards the call to the service; the service marks
        the row as ``status="existing"`` when an active row already exists.
        Endpoint must propagate that intact (no second insert)."""
        tenant_id = uuid4()
        conv_id = uuid4()
        msg_id = uuid4()
        client, _uid, _db = _build_client(tenant_id)

        existing_id = uuid4()

        with (
            patch(
                "src.modules.copilot.api.conversations.ConversationRepository",
            ) as mock_repo_cls,
            patch(
                "src.modules.copilot.api.conversations.MutationApplyService",
            ) as mock_svc_cls,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = _conv_stub(conv_id, tenant_id)
            mock_repo_cls.return_value = mock_repo

            mock_svc = MagicMock()
            mock_svc.apply.return_value = SimpleNamespace(
                applied=[
                    SimpleNamespace(
                        id=existing_id,
                        field_path="identity.brand_name",
                        domain="brand",
                        status="existing",
                    ),
                ],
                rejected=[],
            )
            mock_svc_cls.return_value = mock_svc

            resp = client.post(
                f"/api/v1/copilot/conversations/{conv_id}/mutations/apply",
                json={
                    "message_id": str(msg_id),
                    "updates": [
                        {
                            "field_id": "identity.brand_name",
                            "new_value": "Visionarias",
                        },
                    ],
                },
                headers={"X-Tenant-ID": str(tenant_id)},
            )

        assert resp.status_code == 200
        body = resp.json()
        assert body["applied"][0]["status"] == "existing"
        assert body["applied"][0]["id"] == str(existing_id)
