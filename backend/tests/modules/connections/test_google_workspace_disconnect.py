"""
Tests for Google Workspace disconnect behavior.

Regression: Previously, disconnect only set is_active=False but kept OAuth
credentials in DB, causing get_status to return is_connected=True after
the user unlinked their Google account.

Fix: repo.revoke() clears credentials + sets is_active=False, so the
has_credentials check in get_status correctly returns is_connected=False.
"""

import uuid

import pytest

from src.modules.connections.domain.enums import ChannelType
from src.modules.connections.infrastructure.repositories.channel_connection_repository import (
    ChannelConnectionRepository,
)

GOOGLE_SERVICE_TYPES = [
    ChannelType.GMAIL,
    ChannelType.GOOGLE_CALENDAR,
    ChannelType.GOOGLE_ANALYTICS,
    ChannelType.YOUTUBE,
    ChannelType.YOUTUBE_ANALYTICS,
]

FAKE_CREDS = {
    "access_token": "ya29.xyz",
    "refresh_token": "1//abc",
    "token_uri": "https://oauth2.googleapis.com/token",
}


@pytest.fixture
def repo(db):
    return ChannelConnectionRepository(db)


@pytest.fixture
def connected_google_tenant(repo):
    """Tenant with all 5 Google services connected and active."""
    tenant_id = uuid.uuid4()
    for channel_type in GOOGLE_SERVICE_TYPES:
        repo.upsert(tenant_id, channel_type, FAKE_CREDS, {"email": "user@gmail.com"})
    return tenant_id


class TestGoogleWorkspaceDisconnect:
    def test_revoke_clears_credentials(self, repo, connected_google_tenant):
        """repo.revoke() must clear OAuth credentials (set to empty dict)."""
        tenant_id = connected_google_tenant
        conn = repo.get_by_tenant_and_type(tenant_id, ChannelType.GMAIL)

        repo.revoke(conn)

        repo.db.refresh(conn)
        assert conn.credentials == {}

    def test_revoke_sets_inactive(self, repo, connected_google_tenant):
        """repo.revoke() must set is_active=False."""
        tenant_id = connected_google_tenant
        conn = repo.get_by_tenant_and_type(tenant_id, ChannelType.GMAIL)

        repo.revoke(conn)

        repo.db.refresh(conn)
        assert conn.is_active is False

    def test_status_is_not_connected_after_revoke_all_services(
        self, repo, connected_google_tenant
    ):
        """After revoking all Google services, get_status logic must return is_connected=False."""
        tenant_id = connected_google_tenant

        for channel_type in GOOGLE_SERVICE_TYPES:
            conn = repo.get_by_tenant_and_type(tenant_id, channel_type)
            if conn:
                repo.revoke(conn)

        # Replicate the exact logic from get_status endpoint
        any_connected = False
        for channel_type in GOOGLE_SERVICE_TYPES:
            conn = repo.get_by_tenant_and_type(tenant_id, channel_type)
            has_credentials = bool(conn and conn.credentials)
            if has_credentials:
                any_connected = True

        assert not any_connected, (
            "is_connected must be False after full disconnect — "
            "credentials must be cleared so get_status reports disconnected"
        )

    def test_reconnect_after_revoke_restores_active_state(
        self, repo, connected_google_tenant
    ):
        """After revoke, upsert with new OAuth credentials must re-activate the connection."""
        tenant_id = connected_google_tenant
        conn = repo.get_by_tenant_and_type(tenant_id, ChannelType.GMAIL)
        repo.revoke(conn)

        new_creds = {"access_token": "ya29.new", "refresh_token": "1//new"}
        repo.upsert(
            tenant_id, ChannelType.GMAIL, new_creds, {"email": "user@gmail.com"}
        )

        conn = repo.get_by_tenant_and_type(tenant_id, ChannelType.GMAIL)
        assert conn.is_active is True
        assert conn.credentials == new_creds
