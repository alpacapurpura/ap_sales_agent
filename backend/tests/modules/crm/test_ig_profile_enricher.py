"""
Tests for InstagramProfileEnricher service.

CRM-06: Instagram User Profile API enrichment — fetches name, username,
profile_pic, follower_count, follows_business and updates CustomerProfile traits.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import LifecycleStage
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_profile(
    db: Session,
    tenant_id: uuid.UUID,
    **kwargs,
) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=kwargs.get("profile_id", uuid.uuid4()),
        tenant_id=tenant_id,
        primary_email=kwargs.get("email", f"{uuid.uuid4().hex[:8]}@test.com"),
        full_name=kwargs.get("full_name"),
        lifecycle_stage=kwargs.get("stage", LifecycleStage.SUBSCRIBER),
        lead_score=kwargs.get("lead_score", 0.0),
        is_inactive=False,
        traits=kwargs.get("traits", {}),
        computed_traits={},
    )
    db.add(profile)
    db.flush()
    return profile


def _make_ig_response(
    name: str = "Test User",
    username: str = "testuser",
    profile_pic: str = "https://example.com/pic.jpg",
    follower_count: int = 1500,
    is_user_follow_business: bool = True,
) -> dict:
    return {
        "name": name,
        "username": username,
        "profile_pic": profile_pic,
        "follower_count": follower_count,
        "is_user_follow_business": is_user_follow_business,
    }


# ---------------------------------------------------------------------------
# enrich — successful enrichment
# ---------------------------------------------------------------------------


class TestIgProfileEnricherSuccess:
    """InstagramProfileEnricher.enrich updates profile traits on successful API call."""

    async def test_enrich_updates_all_traits(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id, full_name=None)
        igsid = "12345678"
        access_token = "tok_abc"
        ig_data = _make_ig_response()

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ig_data

            with patch(
                "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait",
                return_value=None,
            ):
                result = await enricher.enrich(tenant_id, igsid, profile.id, access_token)

                assert result == "testuser"
                db.refresh(profile)

                traits = profile.traits
                assert traits["instagram_username"] == "testuser"
                assert traits["profile_pic_url"] == "https://example.com/pic.jpg"
                assert traits["follower_count"] == 1500
                assert traits["follows_business"] is True

    async def test_enrich_sets_full_name_when_empty(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id, full_name=None)
        ig_data = _make_ig_response(name="Maria Garcia")

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ig_data

            with patch(
                "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait",
                return_value=None,
            ):
                await enricher.enrich(tenant_id, "99999", profile.id, "tok")

                db.refresh(profile)
                assert profile.full_name == "Maria Garcia"

    async def test_enrich_does_not_overwrite_existing_full_name(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id, full_name="Existing Name")
        ig_data = _make_ig_response(name="New Name From IG")

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ig_data

            with patch(
                "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait",
                return_value=None,
            ):
                await enricher.enrich(tenant_id, "88888", profile.id, "tok")

                db.refresh(profile)
                assert profile.full_name == "Existing Name"

    async def test_enrich_returns_username(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id)
        ig_data = _make_ig_response(username="cool_dealer")

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ig_data

            with patch(
                "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait",
                return_value=None,
            ):
                result = await enricher.enrich(tenant_id, "77777", profile.id, "tok")

                assert result == "cool_dealer"

    async def test_enrich_partial_data_only_updates_present_fields(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id, full_name=None)
        ig_data = {"username": "partial_user"}

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ig_data

            with patch(
                "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait",
                return_value=None,
            ):
                await enricher.enrich(tenant_id, "66666", profile.id, "tok")

                db.refresh(profile)
                assert profile.traits["instagram_username"] == "partial_user"
                assert "profile_pic_url" not in profile.traits
                assert "follower_count" not in profile.traits


# ---------------------------------------------------------------------------
# enrich — API failure cases
# ---------------------------------------------------------------------------


class TestIgProfileEnricherApiFailure:
    """InstagramProfileEnricher handles API failures gracefully."""

    async def test_returns_none_when_api_returns_404(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id)

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            result = await enricher.enrich(tenant_id, "55555", profile.id, "tok")

            assert result is None

    async def test_returns_none_on_network_error(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id)

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            result = await enricher.enrich(tenant_id, "44444", profile.id, "tok")

            assert result is None

    async def test_returns_none_on_timeout(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id)

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = None

            result = await enricher.enrich(tenant_id, "33333", profile.id, "tok")

            assert result is None


# ---------------------------------------------------------------------------
# enrich — profile not found
# ---------------------------------------------------------------------------


class TestIgProfileEnricherProfileNotFound:
    """InstagramProfileEnricher handles missing customer profile."""

    async def test_returns_username_when_profile_not_found(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        nonexistent_id = uuid.uuid4()
        ig_data = _make_ig_response(username="ghost_user")

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = ig_data

            result = await enricher.enrich(tenant_id, "22222", nonexistent_id, "tok")

            assert result == "ghost_user"


# ---------------------------------------------------------------------------
# _fetch_ig_profile — HTTP call
# ---------------------------------------------------------------------------


class TestFetchIgProfile:
    """InstagramProfileEnricher._fetch_ig_profile calls Instagram User Profile API."""

    async def test_successful_api_call(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        enricher = InstagramProfileEnricher(db)
        igsid = "11111"
        access_token = "tok_success"
        ig_data = _make_ig_response()

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = ig_data

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await enricher._fetch_ig_profile(igsid, access_token)

            assert result == ig_data
            mock_client.get.assert_called_once()
            call_args = mock_client.get.call_args
            assert "11111" in call_args[0][0]

    async def test_returns_none_on_non_200_status(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        enricher = InstagramProfileEnricher(db)

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Invalid token"

        mock_client = AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await enricher._fetch_ig_profile("99999", "bad_token")

            assert result is None

    async def test_returns_none_on_connection_error(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        enricher = InstagramProfileEnricher(db)

        mock_client = AsyncMock()
        mock_client.get.side_effect = Exception("Connection refused")
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)

        with patch("httpx.AsyncClient", return_value=mock_client):
            result = await enricher._fetch_ig_profile("88888", "tok")

            assert result is None


# ---------------------------------------------------------------------------
# _merge_manychat_duplicate
# ---------------------------------------------------------------------------


class TestMergeManychatDuplicate:
    """InstagramProfileEnricher._merge_manychat_duplicate merges profiles with same IG username."""

    async def test_merges_when_duplicate_found(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        target = _make_profile(db, tenant_id)
        manychat_profile = _make_profile(
            db,
            tenant_id,
            profile_id=uuid.uuid4(),
            traits={"instagram_username": "shared_user"},
        )

        enricher = InstagramProfileEnricher(db)

        with patch.object(
            enricher,
            "_fetch_ig_profile",
            new_callable=AsyncMock,
        ) as mock_fetch:
            mock_fetch.return_value = {"username": "shared_user"}

            with patch(
                "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait"
            ) as mock_find:
                mock_find.return_value = MagicMock(
                    id=manychat_profile.id,
                )

                with patch(
                    "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.merge_profiles"
                ) as mock_merge:
                    await enricher.enrich(tenant_id, "12345", target.id, "tok")

                    mock_merge.assert_called_once()

    async def test_no_merge_when_same_profile(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id)

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"username": "unique_user"}

            with patch(
                "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait"
            ) as mock_find:
                mock_find.return_value = MagicMock(id=profile.id)

                with patch(
                    "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.merge_profiles"
                ) as mock_merge:
                    await enricher.enrich(tenant_id, "54321", profile.id, "tok")

                    mock_merge.assert_not_called()

    async def test_no_merge_when_no_duplicate(self, db: Session, tenant_id: uuid.UUID):
        from src.modules.crm.application.services.ig_profile_enricher import (
            InstagramProfileEnricher,
        )

        profile = _make_profile(db, tenant_id)

        enricher = InstagramProfileEnricher(db)

        with patch.object(enricher, "_fetch_ig_profile", new_callable=AsyncMock) as mock_fetch:
            mock_fetch.return_value = {"username": "only_one"}

            with patch(
                "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.find_by_trait"
            ) as mock_find:
                mock_find.return_value = None

                with patch(
                    "src.modules.crm.infrastructure.repositories.customer_repository.CustomerRepository.merge_profiles"
                ) as mock_merge:
                    await enricher.enrich(tenant_id, "11111", profile.id, "tok")

                    mock_merge.assert_not_called()
