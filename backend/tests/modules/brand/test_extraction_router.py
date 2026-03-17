from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.brand.api.extraction import router
from src.modules.iam.api.dependencies import get_current_user, get_db


def _build_client(tenant_id):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/brand/tools")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), tenant_id=tenant_id)
    return TestClient(app)


def test_brand_extract_endpoint_delegates_to_copilot_service():
    tenant_id = uuid4()
    client = _build_client(tenant_id)

    with patch("src.modules.brand.api.extraction.CopilotBrandAIActionsService") as service_cls:
        service_instance = MagicMock()
        service_instance.extract_brand_identity = AsyncMock(
            return_value={"brand_name": "Visionarias", "industry": "Marketing"}
        )
        service_cls.return_value = service_instance

        response = client.post(
            "/api/v1/brand/tools/extract",
            json={"url": "https://visionarias.ai", "type": "brand_identity"},
        )

    assert response.status_code == 200
    assert response.json()["brand_name"] == "Visionarias"
    service_instance.extract_brand_identity.assert_awaited_once_with(
        "https://visionarias.ai",
        "brand_identity",
    )


def test_brand_extract_full_endpoint_delegates_to_copilot_service():
    tenant_id = uuid4()
    client = _build_client(tenant_id)

    with patch("src.modules.brand.api.extraction.CopilotBrandAIActionsService") as service_cls:
        service_instance = MagicMock()
        service_instance.extract_full_brand = AsyncMock(
            return_value={
                "identity": {"brand_name": "Visionarias"},
                "story": {},
                "strategy": {},
                "visuals": {},
                "key_messages": [],
                "team": [],
            }
        )
        service_cls.return_value = service_instance

        response = client.post(
            "/api/v1/brand/tools/extract-full-brand",
            files={"url": (None, "https://visionarias.ai")},
        )

    assert response.status_code == 200
    service_instance.extract_full_brand.assert_awaited_once()
