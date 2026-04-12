"""Tests for Interview API endpoints."""

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.copilot.api.interview import router
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context


def _build_client(tenant_id):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/interview")
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id
    )
    return TestClient(app), mock_db


class TestStartInterview:
    def test_start_creates_session(self):
        tenant_id = uuid4()
        client, _mock_db = _build_client(tenant_id)
        session_id = uuid4()
        conv_id = uuid4()

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.start_interview.return_value = {
                "session_id": session_id,
                "conversation_id": conv_id,
                "config": {"domain": "brand", "bloques": []},
                "initial_message": "¡Hola! Vamos a construir tu Brand Studio juntos.",
            }
            svc_cls.return_value = svc
            response = client.post(
                "/api/v1/copilot/interview/start", json={"domain": "brand"}
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == str(session_id)
        assert data["initial_message"] != ""

    def test_start_returns_409_if_active_exists(self):
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.start_interview.side_effect = ValueError("Active session exists")
            svc_cls.return_value = svc
            response = client.post(
                "/api/v1/copilot/interview/start", json={"domain": "brand"}
            )

        assert response.status_code == 409

    def test_start_with_resume_session_id(self):
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)
        session_id = uuid4()
        conv_id = uuid4()

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.start_interview.return_value = {
                "session_id": session_id,
                "conversation_id": conv_id,
                "config": {"domain": "brand", "bloques": []},
                "initial_message": "¡Bienvenido de vuelta!",
            }
            svc_cls.return_value = svc
            response = client.post(
                "/api/v1/copilot/interview/start",
                json={"domain": "brand", "resume_session_id": str(session_id)},
            )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data


class TestGetActive:
    def test_returns_active_session(self):
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.get_active.return_value = {
                "session_id": uuid4(),
                "domain": "brand",
                "domain_label": "Brand Studio",
                "bloque_actual": "identidad",
                "bloques_completados": [],
                "total_bloques": 5,
            }
            svc_cls.return_value = svc
            response = client.get("/api/v1/copilot/interview/active")

        assert response.status_code == 200
        assert response.json()["domain"] == "brand"

    def test_returns_204_when_no_active(self):
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.get_active.return_value = None
            svc_cls.return_value = svc
            response = client.get("/api/v1/copilot/interview/active")

        assert response.status_code == 204


class TestGetState:
    def test_returns_full_state(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.get_state.return_value = {
                "session_id": session_id,
                "mapa_global": {"story.origin_story": "Test"},
                "bloque_actual": "identidad",
                "bloques_completados": [],
                "config": {"bloques": []},
                "messages_count": 5,
            }
            svc_cls.return_value = svc
            response = client.get(f"/api/v1/copilot/interview/{session_id}/state")

        assert response.status_code == 200
        assert response.json()["mapa_global"]["story.origin_story"] == "Test"

    def test_returns_404_when_not_found(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.get_state.return_value = None
            svc_cls.return_value = svc
            response = client.get(f"/api/v1/copilot/interview/{session_id}/state")

        assert response.status_code == 404


class TestPause:
    def test_pause_session(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.pause.return_value = True
            svc_cls.return_value = svc
            response = client.post(f"/api/v1/copilot/interview/{session_id}/pause")

        assert response.status_code == 200

    def test_pause_returns_400_if_not_active(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.pause.return_value = False
            svc_cls.return_value = svc
            response = client.post(f"/api/v1/copilot/interview/{session_id}/pause")

        assert response.status_code == 400


class TestAbandon:
    def test_abandon_session(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.abandon.return_value = True
            svc_cls.return_value = svc
            response = client.post(f"/api/v1/copilot/interview/{session_id}/abandon")

        assert response.status_code == 200

    def test_abandon_returns_400_if_not_paused_or_active(self):
        tenant_id = uuid4()
        session_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.copilot.api.interview.InterviewService") as svc_cls:
            svc = MagicMock()
            svc.abandon.return_value = False
            svc_cls.return_value = svc
            response = client.post(f"/api/v1/copilot/interview/{session_id}/abandon")

        assert response.status_code == 400
