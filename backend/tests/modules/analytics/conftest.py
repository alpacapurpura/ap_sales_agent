import uuid
import pytest
from uuid import UUID


@pytest.fixture
def test_tenant_id() -> UUID:
    """Fixed tenant UUID for test determinism."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def mock_credentials() -> dict:
    """Simulated OAuth credentials dict."""
    return {
        "access_token": "test-access-token-abc123",
        "refresh_token": "test-refresh-token-xyz789",
    }


@pytest.fixture
def mock_connection_credentials():
    """ConnectionCredentials instance for testing."""
    from src.modules.analytics.domain.ports import ConnectionCredentials

    return ConnectionCredentials(
        channel_type="meta",
        credentials={"access_token": "test-token"},
        config={"page_id": "123456"},
    )
