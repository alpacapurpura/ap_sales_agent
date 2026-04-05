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
    app.dependency_overrides[get_db] = lambda: MagicMock()  # noqa: PLW0108 — lambda required: MagicMock class breaks FastAPI dep injection
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=uuid4(), tenant_id=tenant_id
    )
    # Provide a mock ARQ pool so the endpoint can enqueue jobs without a real Redis connection
    mock_pool = MagicMock()
    mock_pool.enqueue_job = AsyncMock(return_value=None)
    app.state.arq_pool = mock_pool
    return TestClient(app)


def test_brand_extract_endpoint_delegates_to_extraction_service():
    tenant_id = uuid4()
    client = _build_client(tenant_id)

    with patch(
        "src.modules.brand.api.extraction.BrandExtractionService"
    ) as service_cls:
        service_instance = MagicMock()
        service_instance.extract_visuals_only = AsyncMock(
            return_value={"brand_name": "Visionarias", "industry": "Marketing"}
        )
        service_cls.return_value = service_instance

        response = client.post(
            "/api/v1/brand/tools/extract",
            json={"url": "https://visionarias.ai", "type": "brand_identity"},
        )

    assert response.status_code == 200
    assert response.json()["brand_name"] == "Visionarias"
    service_instance.extract_visuals_only.assert_awaited_once_with(
        "https://visionarias.ai",
    )


def test_brand_extract_full_endpoint_dispatches_arq_job():
    tenant_id = uuid4()
    client = _build_client(tenant_id)

    with patch("src.modules.brand.api.extraction.redis_client") as mock_redis:
        mock_redis.setex = MagicMock(return_value=True)

        response = client.post(
            "/api/v1/brand/tools/extract-full-brand",
            files={"url": (None, "https://visionarias.ai")},
        )

    # The endpoint dispatches an async ARQ job and returns 202 Accepted
    assert response.status_code == 202
    body = response.json()
    assert "job_id" in body
    assert body["status"] == "queued"
