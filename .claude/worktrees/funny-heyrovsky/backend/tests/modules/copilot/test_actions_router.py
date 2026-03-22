from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.copilot.api.actions import router
from src.modules.iam.api.dependencies import get_current_user, get_tenant_context
from src.modules.offer.domain.offer_ai_schemas import PsychologyGenerationResponse


def _build_client(tenant_id):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/copilot/actions")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_tenant_context] = lambda: tenant_id
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), tenant_id=tenant_id)
    return TestClient(app)


def test_copilot_offer_psychology_endpoint_keeps_contract():
    tenant_id = uuid4()
    client = _build_client(tenant_id)

    with patch("src.modules.copilot.api.actions.CopilotOfferPsychologyService") as service_cls:
        service_instance = MagicMock()
        service_instance.generate_psychology = AsyncMock(
            return_value=PsychologyGenerationResponse(
                pains=["p1", "p2", "p3", "p4", "p5"],
                desires=["d1", "d2", "d3", "d4", "d5"],
            )
        )
        service_cls.return_value = service_instance

        response = client.post(
            "/api/v1/copilot/actions/offer/psychology",
            json={
                "avatar_id": str(uuid4()),
                "offer_name": "Mentoría Premium",
                "offer_description": "Escalar ventas",
                "current_pains": ["p0"],
                "current_desires": ["d0"],
            },
        )

    assert response.status_code == 200
    assert set(response.json().keys()) == {"pains", "desires"}
    service_instance.generate_psychology.assert_awaited_once()
    assert service_instance.generate_psychology.await_args.args[1] == tenant_id


def test_copilot_brand_extract_delegates_to_service():
    tenant_id = uuid4()
    client = _build_client(tenant_id)

    with patch("src.modules.copilot.api.actions.CopilotBrandAIActionsService") as service_cls:
        service_instance = MagicMock()
        service_instance.extract_brand_identity = AsyncMock(
            return_value={"brand_name": "Visionarias", "industry": "Marketing"}
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
    assert response.json()["brand_name"] == "Visionarias"
    service_instance.extract_brand_identity.assert_awaited_once_with(
        "https://visionarias.ai",
        "brand_identity",
    )
