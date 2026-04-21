"""Tests for Personality Engine API — 10 endpoints, tenant isolation, response_model shapes."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.brand.api.personality import router
from src.modules.brand.infrastructure.models.personality_model import PersonalityProfileModel
from src.modules.iam.api.dependencies import get_current_user, get_db
from src.modules.iam.domain.user import User
from tests.modules.conftest import TENANT_A, TENANT_B, USER_A

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _build_client(db: Session, tenant_id: uuid.UUID) -> TestClient:
    """Build a TestClient with overridden dependencies."""
    app = FastAPI(redirect_slashes=False)
    # Router already declares ``prefix="/personality"`` — mount under
    # ``/api/v1/brand`` so the full path matches production (``main.py``).
    app.include_router(router, prefix="/api/v1/brand")

    fake_user = User(
        id=USER_A,
        email="test@example.com",
        full_name="Test User",
        tenant_id=tenant_id,
        is_active=True,
    )
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /presets — list all 6 presets
# ---------------------------------------------------------------------------


class TestListPresets:
    def test_returns_6_presets(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        resp = client.get("/api/v1/brand/personality/presets")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 6

    def test_preset_shape(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        resp = client.get("/api/v1/brand/personality/presets")
        first = resp.json()[0]
        assert "key" in first
        assert "name" in first
        assert "icon" in first
        assert "description" in first
        assert "sample_message" in first
        assert "dimensions" in first


# ---------------------------------------------------------------------------
# GET /active — active profile or null
# ---------------------------------------------------------------------------


class TestGetActiveProfile:
    def test_returns_null_when_no_profile(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        resp = client.get("/api/v1/brand/personality/active")
        assert resp.status_code == 200
        assert resp.json() is None

    def test_returns_profile_after_select(self, db: Session) -> None:
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        svc.select_preset(TENANT_A, "warm_close")

        client = _build_client(db, TENANT_A)
        resp = client.get("/api/v1/brand/personality/active")
        assert resp.status_code == 200
        data = resp.json()
        assert data is not None
        assert data["preset_key"] == "warm_close"
        assert data["is_active"] is True

    def test_tenant_isolation_different_tenant_sees_null(self, db: Session) -> None:
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        svc.select_preset(TENANT_A, "electric")

        # TENANT_B should not see TENANT_A's profile
        client = _build_client(db, TENANT_B)
        resp = client.get("/api/v1/brand/personality/active")
        assert resp.status_code == 200
        assert resp.json() is None


# ---------------------------------------------------------------------------
# POST /select-preset
# ---------------------------------------------------------------------------


class TestSelectPreset:
    def test_select_known_preset_returns_profile(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        resp = client.post(
            "/api/v1/brand/personality/select-preset",
            json={"preset_key": "serene"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["preset_key"] == "serene"
        assert data["is_active"] is True

    def test_select_unknown_preset_returns_400(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        resp = client.post(
            "/api/v1/brand/personality/select-preset",
            json={"preset_key": "nonexistent_xyz"},
        )
        assert resp.status_code == 400


# ---------------------------------------------------------------------------
# POST /clone — replaces 501 stub
# ---------------------------------------------------------------------------


class TestCloneEndpoint:
    def test_clone_without_text_or_file_returns_400(self, db: Session) -> None:
        """Sending neither text_input nor file → 400."""
        client = _build_client(db, TENANT_A)
        resp = client.post("/api/v1/brand/personality/clone", data={})
        assert resp.status_code == 400

    def test_clone_with_both_text_and_file_returns_400(self, db: Session) -> None:
        """Sending both text_input and a file → 400."""
        client = _build_client(db, TENANT_A)
        text = "\n".join([f"Mensaje {i}" for i in range(15)])
        resp = client.post(
            "/api/v1/brand/personality/clone",
            data={"text_input": text},
            files={"file": ("chat.txt", b"some content", "text/plain")},
        )
        assert resp.status_code == 400

    def test_clone_insufficient_messages_returns_400(self, db: Session) -> None:
        """Fewer than 10 messages → 400."""
        client = _build_client(db, TENANT_A)
        few = "\n".join([f"Mensaje {i}" for i in range(5)])
        resp = client.post(
            "/api/v1/brand/personality/clone",
            data={"text_input": few},
        )
        assert resp.status_code == 400

    def test_clone_success_returns_profile_dto(self, db: Session) -> None:
        """With valid text and mocked pipeline → 200 with PersonalityProfileDTO."""
        text = "\n".join([f"Mensaje de ejemplo número {i}" for i in range(15)])

        mock_state = {
            "personality_dimensions": {
                "energy": 0.6,
                "warmth": 0.7,
                "humor": 0.5,
                "expressiveness": 0.5,
                "narrative": 0.4,
                "verbosity": 0.5,
            },
            "personality_linguistic_patterns": {
                "emoji_style": "moderate",
                "favorite_emojis": ["😊"],
                "greeting": "¡Hola!",
                "farewell": "¡Hasta pronto!",
                "filler_phrases": ["mira"],
                "avg_message_length": "medium",
                "punctuation_style": "standard",
                "humor_type": "natural",
                "unique_vocabulary": ["genial"],
            },
            "personality_sample_exchanges": [
                {
                    "context": "greeting",
                    "other_message": "Hola",
                    "author_response": "¡Hola! 😊",
                }
            ],
            "personality_confidence": 0.8,
            "system_instruction": "BLOQUE 1 — test",
            "error": None,
        }

        client = _build_client(db, TENANT_A)
        with patch("src.modules.brand.application.services.personality_service.personality_app") as mock_app:
            mock_app.ainvoke = AsyncMock(return_value=mock_state)
            resp = client.post(
                "/api/v1/brand/personality/clone",
                data={"text_input": text, "user_name": "Mi Estilo"},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["profile_type"] == "cloned"
        assert data["is_active"] is False

    def test_clone_pipeline_failure_returns_500(self, db: Session) -> None:
        """Pipeline error → 500 with Spanish message."""
        text = "\n".join([f"Mensaje {i}" for i in range(15)])
        error_state = {"error": "LLM timeout", "personality_dimensions": None}

        client = _build_client(db, TENANT_A)
        with patch("src.modules.brand.application.services.personality_service.personality_app") as mock_app:
            mock_app.ainvoke = AsyncMock(return_value=error_state)
            resp = client.post(
                "/api/v1/brand/personality/clone",
                data={"text_input": text},
            )

        assert resp.status_code == 500
        assert "pudimos" in resp.json()["detail"].lower() or "analizar" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# POST /{profile_id}/activate — NEW endpoint
# ---------------------------------------------------------------------------


class TestActivateEndpoint:
    def test_activate_existing_profile_returns_200(self, db: Session) -> None:
        """Activating an existing profile → 200 with active profile."""
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        profile = svc.select_preset(TENANT_A, "serene")

        client = _build_client(db, TENANT_A)
        resp = client.post(f"/api/v1/brand/personality/{profile.id}/activate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is True
        assert data["id"] == str(profile.id)

    def test_activate_nonexistent_profile_returns_404(self, db: Session) -> None:
        """Activating a non-existent profile → 404."""
        client = _build_client(db, TENANT_A)
        fake_id = uuid.uuid4()
        resp = client.post(f"/api/v1/brand/personality/{fake_id}/activate")
        assert resp.status_code == 404

    def test_activate_wrong_tenant_returns_404(self, db: Session) -> None:
        """Activating a profile from another tenant → 404 (no cross-tenant leak)."""
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        profile = svc.select_preset(TENANT_A, "electric")

        # TENANT_B tries to activate TENANT_A's profile
        client = _build_client(db, TENANT_B)
        resp = client.post(f"/api/v1/brand/personality/{profile.id}/activate")
        assert resp.status_code == 404

    def test_activate_idempotent(self, db: Session) -> None:
        """Calling activate twice on the same profile returns 200 both times."""
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        profile = svc.select_preset(TENANT_A, "minimalist")

        client = _build_client(db, TENANT_A)
        resp1 = client.post(f"/api/v1/brand/personality/{profile.id}/activate")
        resp2 = client.post(f"/api/v1/brand/personality/{profile.id}/activate")
        assert resp1.status_code == 200
        assert resp2.status_code == 200


# ---------------------------------------------------------------------------
# POST /from-voice-tone — NEW endpoint
# ---------------------------------------------------------------------------


class TestFromVoiceToneEndpoint:
    def test_no_voice_tone_returns_404(self, db: Session) -> None:
        """Tenant has no voice_tone → 404."""
        client = _build_client(db, TENANT_A)
        resp = client.post("/api/v1/brand/personality/from-voice-tone")
        assert resp.status_code == 404

    def test_success_returns_from_voice_tone_response(self, db: Session, seed_tenant) -> None:
        """With voice_tone in BrandIdentity → 200 with FromVoiceToneResponse shape."""
        from src.modules.brand.domain import BrandIdentity, BrandSettings
        from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository

        # Seed brand identity with voice_tone (seed_tenant fixture inserts the tenant row)
        brand_repo = BrandRepository(db)
        settings = BrandSettings(
            identity=BrandIdentity(
                brand_name="Test Brand",
                voice_tone="Cálida, cercana, con energía positiva y humor ligero.",
            )
        )
        brand_repo.save_settings(TENANT_A, settings)

        with patch("src.modules.brand.application.services.personality_service.find_nearest_preset") as mock_find:
            mock_find.return_value = ("warm_close", 0.82)

            client = _build_client(db, TENANT_A)
            resp = client.post("/api/v1/brand/personality/from-voice-tone")

        assert resp.status_code == 200
        data = resp.json()
        assert "profile" in data
        assert "source_voice_tone" in data
        assert "matched_preset_key" in data
        assert "match_confidence" in data
        assert data["profile"]["profile_type"] == "migrated_from_voice_tone"
        assert data["profile"]["is_active"] is True

    def test_already_migrated_returns_409(self, db: Session, seed_tenant) -> None:
        """Calling from-voice-tone when migration already done → 409."""
        from src.modules.brand.domain import BrandIdentity, BrandSettings
        from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository

        brand_repo = BrandRepository(db)
        settings = BrandSettings(
            identity=BrandIdentity(
                brand_name="Test Brand",
                voice_tone="Directa y sin rodeos.",
            )
        )
        brand_repo.save_settings(TENANT_A, settings)

        with patch("src.modules.brand.application.services.personality_service.find_nearest_preset") as mock_find:
            mock_find.return_value = ("direct", 0.75)
            client = _build_client(db, TENANT_A)
            # First migration
            resp1 = client.post("/api/v1/brand/personality/from-voice-tone")
            assert resp1.status_code == 200
            # Second migration → 409
            resp2 = client.post("/api/v1/brand/personality/from-voice-tone")
            assert resp2.status_code == 409


# ---------------------------------------------------------------------------
# PUT /{profile_id}/dimensions — existing endpoint, audited here
# ---------------------------------------------------------------------------


class TestUpdateDimensions:
    def test_update_dimensions_success(self, db: Session) -> None:
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        profile = svc.select_preset(TENANT_A, "warm_close")

        client = _build_client(db, TENANT_A)
        resp = client.put(
            f"/api/v1/brand/personality/{profile.id}/dimensions",
            json={
                "dimensions": {
                    "energy": 0.1,
                    "warmth": 0.85,
                    "humor": 0.6,
                    "expressiveness": 0.7,
                    "narrative": 0.5,
                    "verbosity": 0.4,
                }
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["dimensions"]["energy"] == pytest.approx(0.1)

    def test_update_dimensions_wrong_tenant_returns_404(self, db: Session) -> None:
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        profile = svc.select_preset(TENANT_A, "warm_close")

        client = _build_client(db, TENANT_B)
        resp = client.put(
            f"/api/v1/brand/personality/{profile.id}/dimensions",
            json={
                "dimensions": {
                    "energy": 0.5,
                    "warmth": 0.5,
                    "humor": 0.5,
                    "expressiveness": 0.5,
                    "narrative": 0.5,
                    "verbosity": 0.5,
                }
            },
        )
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /{profile_id}/simulate — existing endpoint, audited here
# ---------------------------------------------------------------------------


class TestSimulate:
    def test_simulate_existing_profile_returns_3_responses(self, db: Session) -> None:
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        profile = svc.select_preset(TENANT_A, "narrative")

        client = _build_client(db, TENANT_A)
        resp = client.post(f"/api/v1/brand/personality/{profile.id}/simulate")
        assert resp.status_code == 200
        data = resp.json()
        assert "responses" in data
        assert len(data["responses"]) == 3

    def test_simulate_nonexistent_returns_404(self, db: Session) -> None:
        client = _build_client(db, TENANT_A)
        resp = client.post(f"/api/v1/brand/personality/{uuid.uuid4()}/simulate")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /{profile_id} — existing endpoint, audited here
# ---------------------------------------------------------------------------


class TestDeleteProfile:
    def test_delete_existing_returns_204(self, db: Session) -> None:
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        profile = svc.select_preset(TENANT_A, "minimalist")

        client = _build_client(db, TENANT_A)
        resp = client.delete(f"/api/v1/brand/personality/{profile.id}")
        assert resp.status_code == 204

    def test_delete_wrong_tenant_returns_404(self, db: Session) -> None:
        from src.modules.brand.application.services.personality_service import PersonalityService

        svc = PersonalityService(db=db)
        profile = svc.select_preset(TENANT_A, "direct")

        client = _build_client(db, TENANT_B)
        resp = client.delete(f"/api/v1/brand/personality/{profile.id}")
        assert resp.status_code == 404
