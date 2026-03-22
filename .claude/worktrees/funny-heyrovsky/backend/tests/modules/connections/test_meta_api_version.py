"""Tests for Meta API version constant and URL constructions (BUGFIX-01).

Verifies that:
- API_VERSION is set to v24.0 (not deprecated v19.0)
- All URL constructions use the API_VERSION constant
- _init_api() uses per-instance FacebookAdsApi, NOT the global singleton
- get_user_profile() passes explicit api= to User()
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.modules.connections.infrastructure.channels.meta import MetaAdapter


class TestApiVersionConstant:
    """BUGFIX-01: API version must be v24.0."""

    def test_api_version_is_v24(self):
        assert MetaAdapter.API_VERSION == "v24.0"

    def test_api_version_not_deprecated(self):
        """Ensure we're not using any deprecated version."""
        deprecated = {"v19.0", "v20.0", "v21.0"}
        assert MetaAdapter.API_VERSION not in deprecated


class TestAuthorizationUrlVersion:
    """get_authorization_url() must use API_VERSION in the OAuth URL."""

    @patch("src.modules.connections.infrastructure.channels.meta.settings")
    def test_authorization_url_contains_v24(self, mock_settings):
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"
        mock_settings.META_CONFIG_ID = None

        adapter = MetaAdapter(app_id="test_app_id", app_secret="test_app_secret")
        url, state = adapter.get_authorization_url("https://example.com/callback")

        assert "/v24.0/" in url
        assert "/v19.0/" not in url


class TestExchangeCodeVersion:
    """exchange_code() must construct URLs with API_VERSION constant."""

    @patch("src.modules.connections.infrastructure.channels.meta.settings")
    @pytest.mark.asyncio
    async def test_exchange_code_uses_v24_in_url(self, mock_settings):
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        adapter = MetaAdapter(app_id="test_app_id", app_secret="test_app_secret")

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "short_lived_token",
            "token_type": "bearer",
        }

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await adapter.exchange_code("test_code", "https://example.com/callback")

            # Check that all calls used v24.0
            for call in mock_client.get.call_args_list:
                url = call[0][0] if call[0] else call[1].get("url", "")
                assert "/v24.0/" in url, f"URL does not contain /v24.0/: {url}"
                assert "/v19.0/" not in url, f"URL still uses deprecated /v19.0/: {url}"


class TestGetBusinessAssetsVersion:
    """get_business_assets() must construct URLs with API_VERSION constant."""

    @patch("src.modules.connections.infrastructure.channels.meta.settings")
    @pytest.mark.asyncio
    async def test_get_business_assets_uses_v24_in_url(self, mock_settings):
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        adapter = MetaAdapter(
            app_id="test_app_id",
            app_secret="test_app_secret",
            access_token="test_token",
        )

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"data": []}

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client

            await adapter.get_business_assets()

            # Check that all calls used v24.0
            for call in mock_client.get.call_args_list:
                url = call[0][0] if call[0] else call[1].get("url", "")
                assert "/v24.0/" in url, f"URL does not contain /v24.0/: {url}"
                assert "/v19.0/" not in url, f"URL still uses deprecated /v19.0/: {url}"


class TestInitApiNotSingleton:
    """_init_api() must NOT call FacebookAdsApi.init() — uses per-instance API."""

    @patch("src.modules.connections.infrastructure.channels.meta.settings")
    def test_init_api_does_not_call_global_init(self, mock_settings):
        """FacebookAdsApi.init() must never be called."""
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        with patch(
            "src.modules.connections.infrastructure.channels.meta.FacebookAdsApi"
        ) as mock_api_class:
            mock_session = MagicMock()
            with patch(
                "src.modules.connections.infrastructure.channels.meta.FacebookSession",
                return_value=mock_session,
            ):
                adapter = MetaAdapter(
                    app_id="test_app_id",
                    app_secret="test_app_secret",
                    access_token="test_token",
                )

                # FacebookAdsApi.init() must NOT have been called
                mock_api_class.init.assert_not_called()

    @patch("src.modules.connections.infrastructure.channels.meta.settings")
    def test_init_api_creates_per_instance_api(self, mock_settings):
        """_init_api() must create FacebookAdsApi via FacebookSession and store as _api_instance."""
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        with patch(
            "src.modules.connections.infrastructure.channels.meta.FacebookAdsApi"
        ) as mock_api_class:
            mock_session = MagicMock()
            mock_api_instance = MagicMock()
            mock_api_class.return_value = mock_api_instance

            with patch(
                "src.modules.connections.infrastructure.channels.meta.FacebookSession",
                return_value=mock_session,
            ):
                adapter = MetaAdapter(
                    app_id="test_app_id",
                    app_secret="test_app_secret",
                    access_token="test_token",
                )

                # FacebookSession should have been created with credentials
                # FacebookAdsApi should have been instantiated (not .init())
                mock_api_class.assert_called_once_with(
                    mock_session, api_version="v24.0"
                )
                assert adapter._api_instance == mock_api_instance

    @patch("src.modules.connections.infrastructure.channels.meta.settings")
    def test_init_api_does_not_set_default_api(self, mock_settings):
        """_init_api() must NOT call FacebookAdsApi.set_default_api()."""
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        with patch(
            "src.modules.connections.infrastructure.channels.meta.FacebookAdsApi"
        ) as mock_api_class:
            mock_session = MagicMock()
            with patch(
                "src.modules.connections.infrastructure.channels.meta.FacebookSession",
                return_value=mock_session,
            ):
                MetaAdapter(
                    app_id="test_app_id",
                    app_secret="test_app_secret",
                    access_token="test_token",
                )

                mock_api_class.set_default_api.assert_not_called()


class TestGetUserProfileExplicitApi:
    """get_user_profile() must pass api=self._api_instance to User()."""

    @patch("src.modules.connections.infrastructure.channels.meta.settings")
    @pytest.mark.asyncio
    async def test_get_user_profile_passes_explicit_api(self, mock_settings):
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        mock_api_instance = MagicMock()
        mock_profile_data = {"id": "123", "name": "Test User", "email": "test@test.com"}

        with patch(
            "src.modules.connections.infrastructure.channels.meta.FacebookAdsApi"
        ) as mock_api_class, patch(
            "src.modules.connections.infrastructure.channels.meta.FacebookSession"
        ), patch(
            "src.modules.connections.infrastructure.channels.meta.User"
        ) as mock_user_class:
            mock_api_class.return_value = mock_api_instance

            mock_user_instance = MagicMock()
            mock_user_instance.api_get.return_value = mock_user_instance
            mock_user_instance.export_all_data.return_value = mock_profile_data
            mock_user_class.return_value = mock_user_instance

            adapter = MetaAdapter(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="test_token",
            )

            result = await adapter.get_user_profile()

            # User must be called with explicit api= parameter
            mock_user_class.assert_called_once_with(
                fbid="me", api=mock_api_instance
            )
            assert result == mock_profile_data
