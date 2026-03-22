"""Tests for ConnectionPort ABC, ConnectionCredentials, and domain exceptions."""

import pytest


class TestConnectionPort:
    def test_cannot_instantiate_abc(self):
        from src.modules.analytics.domain.ports import ConnectionPort

        with pytest.raises(TypeError):
            ConnectionPort()

    def test_has_abstract_get_credentials(self):
        from src.modules.analytics.domain.ports import ConnectionPort
        import inspect

        methods = {
            name
            for name, _ in inspect.getmembers(
                ConnectionPort, predicate=inspect.isfunction
            )
        }
        assert "get_credentials" in methods

    def test_has_abstract_list_active_connections(self):
        from src.modules.analytics.domain.ports import ConnectionPort
        import inspect

        methods = {
            name
            for name, _ in inspect.getmembers(
                ConnectionPort, predicate=inspect.isfunction
            )
        }
        assert "list_active_connections" in methods


class TestConnectionCredentials:
    def test_validates_model(self, mock_connection_credentials):
        assert mock_connection_credentials.channel_type == "meta"
        assert mock_connection_credentials.credentials["access_token"] == "test-token"
        assert mock_connection_credentials.config["page_id"] == "123456"

    def test_fields_required(self):
        from src.modules.analytics.domain.ports import ConnectionCredentials

        creds = ConnectionCredentials(
            channel_type="telegram",
            credentials={"bot_token": "abc"},
            config={},
        )
        assert creds.channel_type == "telegram"


class TestDomainExceptions:
    def test_connection_revoked_is_exception(self):
        from src.modules.analytics.domain.exceptions import ConnectionRevokedException

        exc = ConnectionRevokedException("Token expired")
        assert isinstance(exc, Exception)
        assert str(exc) == "Token expired"

    def test_connection_revoked_with_channel_type(self):
        from src.modules.analytics.domain.exceptions import ConnectionRevokedException

        exc = ConnectionRevokedException("Revoked", channel_type="meta")
        assert exc.channel_type == "meta"

    def test_token_refresh_failed_is_exception(self):
        from src.modules.analytics.domain.exceptions import TokenRefreshFailed

        exc = TokenRefreshFailed("Refresh failed")
        assert isinstance(exc, Exception)
        assert str(exc) == "Refresh failed"

    def test_token_refresh_failed_with_provider(self):
        from src.modules.analytics.domain.exceptions import TokenRefreshFailed

        exc = TokenRefreshFailed("Failed", provider="google")
        assert exc.provider == "google"
