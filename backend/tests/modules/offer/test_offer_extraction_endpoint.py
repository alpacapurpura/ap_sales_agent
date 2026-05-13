"""Tests for offer extraction API endpoints."""

import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from luana_core_iam.api.dependencies import get_current_user, get_db
from luana_core_offer_studio.api.dto.extraction import (
    ExtractFullOfferResponse,
    OfferExtractionStatusResponse,
)
from luana_core_offer_studio.api.offer_extraction import router

TENANT_ID = uuid.UUID("aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa")
OFFER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _mock_user():
    user = MagicMock()
    user.tenant_id = TENANT_ID
    return user


def _fake_db():
    return MagicMock()


def _build_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/offer/tools")
    app.dependency_overrides[get_current_user] = _mock_user
    app.dependency_overrides[get_db] = _fake_db
    app.state.arq_pool = AsyncMock()
    app.state.arq_pool.enqueue_job = AsyncMock()
    return app


class TestExtractFullOfferEndpoint:
    """POST /api/v1/offer/tools/extract-full-offer"""

    @patch("luana_core_offer_studio.api.offer_extraction.redis_client")
    def test_returns_202_with_job_id(self, mock_redis):
        app = _build_app()
        mock_redis.setex = MagicMock()

        client = TestClient(app)
        response = client.post(
            "/api/v1/offer/tools/extract-full-offer",
            data={
                "offer_id": str(OFFER_ID),
                "url": "https://example.com/product",
                "mode": "initial",
            },
        )

        assert response.status_code == 202
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "queued"
        ExtractFullOfferResponse(**data)

    @patch("luana_core_offer_studio.api.offer_extraction.redis_client")
    def test_requires_offer_id(self, mock_redis):
        app = _build_app()
        client = TestClient(app)
        response = client.post(
            "/api/v1/offer/tools/extract-full-offer",
            data={"url": "https://example.com"},
        )
        assert response.status_code == 422  # Missing required field

    @patch("luana_core_offer_studio.api.offer_extraction.redis_client")
    def test_requires_at_least_one_source(self, mock_redis):
        app = _build_app()
        client = TestClient(app)
        response = client.post(
            "/api/v1/offer/tools/extract-full-offer",
            data={"offer_id": str(OFFER_ID), "mode": "initial"},
        )
        assert response.status_code == 400


class TestOfferExtractionStatusEndpoint:
    """GET /api/v1/offer/tools/extract-full-offer/status/{job_id}"""

    @patch("luana_core_offer_studio.api.offer_extraction.redis_client")
    def test_returns_status_from_redis(self, mock_redis):
        app = _build_app()
        job_id = str(uuid.uuid4())

        redis_data = json.dumps(
            {
                "status": "processing",
                "progress": 50,
                "stage": "Analizando promesa...",
                "started_at": "2026-04-06T10:00:00",
            },
        )

        mock_redis.get.return_value = redis_data
        client = TestClient(app)
        response = client.get(f"/api/v1/offer/tools/extract-full-offer/status/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "processing"
        assert data["progress"] == 50
        OfferExtractionStatusResponse(**data)

    @patch("luana_core_offer_studio.api.offer_extraction.redis_client")
    def test_returns_404_for_unknown_job(self, mock_redis):
        app = _build_app()
        job_id = str(uuid.uuid4())

        mock_redis.get.return_value = None
        client = TestClient(app)
        response = client.get(f"/api/v1/offer/tools/extract-full-offer/status/{job_id}")
        assert response.status_code == 404

    @patch("luana_core_offer_studio.api.offer_extraction.redis_client")
    def test_rejects_invalid_job_id(self, mock_redis):
        app = _build_app()
        client = TestClient(app)
        response = client.get(
            "/api/v1/offer/tools/extract-full-offer/status/not-a-uuid",
        )
        assert response.status_code == 400
