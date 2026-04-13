from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.copilot.api.actions import router
from src.modules.iam.api.dependencies import get_current_user


def _build_client(tenant_id):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/actions")
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
    )
    return TestClient(app)


def test_copilot_brand_extract_delegates_to_service():
    tenant_id = uuid4()
    client = _build_client(tenant_id)

    with patch(
        "src.modules.copilot.api.actions.CopilotBrandAIActionsService",
    ) as service_cls:
        service_instance = MagicMock()
        service_instance.extract_brand_identity = AsyncMock(
            return_value={"primary_color": "#FF5733", "secondary_color": "#333333"},
        )
        service_cls.return_value = service_instance

        response = client.post(
            "/api/v1/copilot/actions/brand/extract",
            json={
                "url": "https://visionarias.ai",
                "type": "brand_identity",
            },
        )

    assert response.status_code == 200
    assert response.json()["primary_color"] == "#FF5733"
    service_instance.extract_brand_identity.assert_awaited_once_with(
        "https://visionarias.ai",
        "brand_identity",
    )
