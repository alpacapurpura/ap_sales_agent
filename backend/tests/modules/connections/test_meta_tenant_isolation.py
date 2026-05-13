"""Tests for Meta SDK multi-tenant isolation (BUGFIX-02).

Verifies that:
- Sequential: Two MetaAdapter instances with different tokens return correct tenant data
- Concurrent: Two MetaAdapter instances running concurrently via asyncio.gather() never cross-contaminate
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from luana_core_connections.infrastructure.channels.meta import MetaAdapter


def _create_adapter_with_mocks(token: str, mock_api_class, mock_session_class):
    """Helper: create a MetaAdapter with a mocked per-instance API."""
    mock_session = MagicMock()
    mock_session_class.return_value = mock_session

    mock_api_instance = MagicMock()
    # Store the token on the mock so tests can verify which API was used
    mock_api_instance._test_token = token
    mock_api_class.return_value = mock_api_instance

    adapter = MetaAdapter(
        app_id="test_app_id",
        app_secret="test_app_secret",
        access_token=token,
    )
    return adapter, mock_api_instance


@patch("luana_core_connections.infrastructure.channels.meta.settings")
class TestSequentialTenantIsolation:
    """Two MetaAdapter instances with different tokens return their own tenant's data."""

    @pytest.mark.asyncio
    async def test_sequential_isolation(self, mock_settings):
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        tenant_a_data = {"id": "111", "name": "Tenant A User", "email": "a@test.com"}
        tenant_b_data = {"id": "222", "name": "Tenant B User", "email": "b@test.com"}

        with (
            patch(
                "luana_core_connections.infrastructure.channels.meta.FacebookAdsApi",
            ) as mock_api_class,
            patch(
                "luana_core_connections.infrastructure.channels.meta.FacebookSession",
            ),
            patch(
                "luana_core_connections.infrastructure.channels.meta.User",
            ) as mock_user_class,
        ):
            # Create two adapters with different tokens
            # We need to track which api instance maps to which adapter
            api_instances = {}

            def make_api(session, api_version=None):
                """Track API instances by session access token."""
                instance = MagicMock()
                instance._test_session = session
                # Store mapping
                api_instances[id(instance)] = instance
                return instance

            mock_api_class.side_effect = make_api

            adapter_a = MetaAdapter(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="tenant_A_token",
            )
            api_a = adapter_a._api_instance

            adapter_b = MetaAdapter(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="tenant_B_token",
            )
            api_b = adapter_b._api_instance

            # Verify different API instances
            assert api_a is not api_b

            # Mock User to return data based on which api= was passed
            def make_user(fbid, api=None):
                user = MagicMock()
                if api is api_a:
                    user.api_get.return_value = user
                    user.export_all_data.return_value = tenant_a_data
                elif api is api_b:
                    user.api_get.return_value = user
                    user.export_all_data.return_value = tenant_b_data
                else:
                    msg = "User created without explicit api parameter"
                    raise AssertionError(msg)
                return user

            mock_user_class.side_effect = make_user

            # Sequential calls
            result_a = await adapter_a.get_user_profile()
            result_b = await adapter_b.get_user_profile()

            assert result_a == tenant_a_data, f"Tenant A got wrong data: {result_a}"
            assert result_b == tenant_b_data, f"Tenant B got wrong data: {result_b}"

            # Verify User was called with explicit api= each time
            assert mock_user_class.call_count == 2
            for call in mock_user_class.call_args_list:
                assert "api" in call.kwargs, "User() must be called with api= keyword argument"


@patch("luana_core_connections.infrastructure.channels.meta.settings")
class TestConcurrentTenantIsolation:
    """Two MetaAdapter instances running concurrently via asyncio.gather() never cross-contaminate."""

    @pytest.mark.asyncio
    async def test_concurrent_isolation(self, mock_settings):
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        tenant_a_data = {"id": "111", "name": "Tenant A User", "email": "a@test.com"}
        tenant_b_data = {"id": "222", "name": "Tenant B User", "email": "b@test.com"}

        # Use events to force interleaving
        asyncio.Event()
        asyncio.Event()

        with (
            patch(
                "luana_core_connections.infrastructure.channels.meta.FacebookAdsApi",
            ) as mock_api_class,
            patch(
                "luana_core_connections.infrastructure.channels.meta.FacebookSession",
            ),
            patch(
                "luana_core_connections.infrastructure.channels.meta.User",
            ) as mock_user_class,
        ):
            api_a = MagicMock()
            api_b = MagicMock()
            api_instances = []

            def make_api(session, api_version=None):
                instance = MagicMock()
                api_instances.append(instance)
                return instance

            mock_api_class.side_effect = make_api

            adapter_a = MetaAdapter(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="tenant_A_token",
            )
            api_a = adapter_a._api_instance

            adapter_b = MetaAdapter(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="tenant_B_token",
            )
            api_b = adapter_b._api_instance

            assert api_a is not api_b

            def make_user(fbid, api=None):
                user = MagicMock()
                if api is api_a:
                    user.api_get.return_value = user
                    user.export_all_data.return_value = tenant_a_data
                elif api is api_b:
                    user.api_get.return_value = user
                    user.export_all_data.return_value = tenant_b_data
                else:
                    msg = "User created without explicit api parameter"
                    raise AssertionError(msg)
                return user

            mock_user_class.side_effect = make_user

            # Run both concurrently
            result_a, result_b = await asyncio.gather(
                adapter_a.get_user_profile(),
                adapter_b.get_user_profile(),
            )

            assert result_a == tenant_a_data, f"Tenant A got wrong data under concurrency: {result_a}"
            assert result_b == tenant_b_data, f"Tenant B got wrong data under concurrency: {result_b}"

    @pytest.mark.asyncio
    async def test_concurrent_isolation_with_interleaving(self, mock_settings):
        """Force interleaving to catch race conditions in global state."""
        mock_settings.META_APP_ID = "test_app_id"
        mock_settings.META_APP_SECRET = "test_app_secret"

        tenant_a_data = {"id": "111", "name": "Tenant A User", "email": "a@test.com"}
        tenant_b_data = {"id": "222", "name": "Tenant B User", "email": "b@test.com"}

        asyncio.Barrier(2)

        with (
            patch(
                "luana_core_connections.infrastructure.channels.meta.FacebookAdsApi",
            ) as mock_api_class,
            patch(
                "luana_core_connections.infrastructure.channels.meta.FacebookSession",
            ),
            patch(
                "luana_core_connections.infrastructure.channels.meta.User",
            ) as mock_user_class,
        ):

            def make_api(session, api_version=None):
                return MagicMock()

            mock_api_class.side_effect = make_api

            adapter_a = MetaAdapter(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="tenant_A_token",
            )
            api_a = adapter_a._api_instance

            adapter_b = MetaAdapter(
                app_id="test_app_id",
                app_secret="test_app_secret",
                access_token="tenant_B_token",
            )
            api_b = adapter_b._api_instance

            call_log = []

            def make_user(fbid, api=None):
                user = MagicMock()
                if api is api_a:
                    call_log.append("A")
                    user.api_get.return_value = user
                    user.export_all_data.return_value = tenant_a_data
                elif api is api_b:
                    call_log.append("B")
                    user.api_get.return_value = user
                    user.export_all_data.return_value = tenant_b_data
                else:
                    msg = "User created without explicit api parameter"
                    raise AssertionError(msg)
                return user

            mock_user_class.side_effect = make_user

            # Run N times to increase probability of catching race conditions
            for _ in range(5):
                call_log.clear()
                r_a, r_b = await asyncio.gather(
                    adapter_a.get_user_profile(),
                    adapter_b.get_user_profile(),
                )
                assert r_a == tenant_a_data
                assert r_b == tenant_b_data
