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


@pytest.fixture
def sample_offer_id() -> UUID:
    """Fixed offer UUID for test determinism."""
    return uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
def sample_customer_id() -> UUID:
    """Fixed customer UUID for test determinism."""
    return uuid.UUID("33333333-3333-3333-3333-333333333333")
