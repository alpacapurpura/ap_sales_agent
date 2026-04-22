"""Tests for POST /api/v1/assets/{id}/promote.

Promotion is the explicit bridge between *temporary chat context* uploads
(ephemeral / context_extract) and *canonical* tenant assets (library /
deliverable). It NEVER happens implicitly — a user action or a confirmed
copilot suggestion triggers the endpoint.

Contract:
* purpose → scope mapping comes from the domain enums; clients cannot
  set a scope that contradicts the purpose.
* deliverable purposes (offer_collateral, legal_doc) require entity_type
  + entity_id — without them the endpoint 422.
* idempotent: promoting the same asset with the same payload a second
  time succeeds and does not create duplicate links.
* cross-tenant: returns 404, never 403, to avoid leaking existence.
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.core.database import get_db
from src.modules.assets.api.router import router
from src.modules.assets.domain.enums import (
    AssetPurpose,
    AssetScope,
)
from src.modules.iam.api.dependencies import get_current_user


def _build_client(tenant_id, user_id=None):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/assets")
    mock_db = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(
        id=user_id or uuid4(),
        tenant_id=tenant_id,
    )
    return TestClient(app), mock_db


def _asset(tenant_id, *, scope=AssetScope.EPHEMERAL.value, purpose=AssetPurpose.CONTEXT_EXTRACT.value):
    return SimpleNamespace(
        id=uuid4(),
        tenant_id=tenant_id,
        scope=scope,
        purpose=purpose,
        filename="brief.pdf",
        mime_type="application/pdf",
        public_url="/uploads/brief.pdf",
        type="DOCUMENT",
        user_description=None,
        ai_description=None,
        ai_metadata={},
        ai_colors=[],
        status="completed",
        error_message=None,
        storage_provider="LOCAL",
        storage_path="/tmp/brief.pdf",
        extracted_text=None,
        extracted_summary=None,
        extracted_at=None,
        extraction_status="extracted",
        extraction_error=None,
        expires_at=None,
        offer_id=None,
        created_at=None,
        updated_at=None,
    )


class TestPromoteEndpoint:
    def test_promote_to_library_brand_asset(self) -> None:
        """brand_asset purpose → scope=library, no entity link required."""
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)
        asset = _asset(tenant_id)

        with (
            patch("src.modules.assets.api.router.AssetRepository") as mock_repo_cls,
            patch("src.modules.assets.api.router.AssetLinkRepository") as mock_link_cls,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = asset
            promoted = _asset(
                tenant_id,
                scope=AssetScope.LIBRARY.value,
                purpose=AssetPurpose.BRAND_ASSET.value,
            )
            mock_repo.update_partial.return_value = promoted
            mock_repo_cls.return_value = mock_repo
            mock_link_cls.return_value = MagicMock()

            resp = client.post(
                f"/api/v1/assets/{asset.id}/promote",
                json={"purpose": "brand_asset"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["scope"] == "library"
        assert data["purpose"] == "brand_asset"
        mock_link_cls.return_value.create.assert_not_called()

    def test_promote_to_deliverable_with_link(self) -> None:
        """offer_collateral purpose requires entity + creates link."""
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)
        asset = _asset(tenant_id)
        offer_id = uuid4()

        with (
            patch("src.modules.assets.api.router.AssetRepository") as mock_repo_cls,
            patch("src.modules.assets.api.router.AssetLinkRepository") as mock_link_cls,
        ):
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = asset
            promoted = _asset(
                tenant_id,
                scope=AssetScope.DELIVERABLE.value,
                purpose=AssetPurpose.OFFER_COLLATERAL.value,
            )
            mock_repo.update_partial.return_value = promoted
            mock_repo_cls.return_value = mock_repo

            mock_link = MagicMock()
            mock_link_cls.return_value = mock_link

            resp = client.post(
                f"/api/v1/assets/{asset.id}/promote",
                json={
                    "purpose": "offer_collateral",
                    "entity_type": "offer",
                    "entity_id": str(offer_id),
                    "role": "primary_flyer",
                },
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["scope"] == "deliverable"
        mock_link.create.assert_called_once()
        kwargs = mock_link.create.call_args.kwargs
        assert kwargs["entity_type"] == "offer"
        assert kwargs["entity_id"] == offer_id
        assert kwargs["role"] == "primary_flyer"

    def test_deliverable_without_entity_returns_422(self) -> None:
        """Purpose requiring a link but without entity_id is rejected at the DTO layer."""
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)
        asset = _asset(tenant_id)

        with patch("src.modules.assets.api.router.AssetRepository"):
            resp = client.post(
                f"/api/v1/assets/{asset.id}/promote",
                json={"purpose": "offer_collateral"},
            )

        assert resp.status_code == 422

    def test_nonexistent_returns_404(self) -> None:
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)

        with patch("src.modules.assets.api.router.AssetRepository") as mock_repo_cls:
            mock_repo = MagicMock()
            mock_repo.get_by_id.return_value = None
            mock_repo_cls.return_value = mock_repo

            resp = client.post(
                f"/api/v1/assets/{uuid4()}/promote",
                json={"purpose": "brand_asset"},
            )

        assert resp.status_code == 404

    def test_unknown_purpose_rejected(self) -> None:
        tenant_id = uuid4()
        client, _ = _build_client(tenant_id)
        asset = _asset(tenant_id)

        resp = client.post(
            f"/api/v1/assets/{asset.id}/promote",
            json={"purpose": "definitely_not_a_purpose"},
        )

        assert resp.status_code == 422
