"""
Tests for booking_url helper.

get_booking_base_url returns:
- A custom domain URL when the tenant has an active primary domain.
- settings.DASHBOARD_DOMAIN as fallback when no custom domain exists.
"""

import uuid
from unittest.mock import MagicMock, patch

TENANT_ID = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


def _make_domain_lookup(hostname: str | None = None) -> MagicMock:
    """Create a mock DomainLookupPort that returns the given hostname."""
    port = MagicMock()
    port.get_verified_domain.return_value = hostname
    return port


def test_returns_custom_domain_when_active_primary_exists():
    """Returns https://<hostname> for a primary active domain."""
    from src.modules.scheduling.application.booking_url import get_booking_base_url

    lookup = _make_domain_lookup("booking.mystore.com")
    result = get_booking_base_url(TENANT_ID, lookup)

    assert result == "https://booking.mystore.com"


def test_falls_back_to_dashboard_domain_when_no_custom_domain():
    """Returns DASHBOARD_DOMAIN when the tenant has no domains."""
    from src.modules.scheduling.application.booking_url import get_booking_base_url

    lookup = _make_domain_lookup(None)

    with patch("src.modules.scheduling.application.booking_url.settings") as mock_settings:
        mock_settings.DASHBOARD_DOMAIN = "https://app.nicolify.com"
        result = get_booking_base_url(TENANT_ID, lookup)

    assert result == "https://app.nicolify.com"


def test_accepts_string_tenant_id():
    """Accepts a string tenant_id and converts it to UUID internally."""
    from src.modules.scheduling.application.booking_url import get_booking_base_url

    lookup = _make_domain_lookup(None)

    with patch("src.modules.scheduling.application.booking_url.settings") as mock_settings:
        mock_settings.DASHBOARD_DOMAIN = "https://app.nicolify.com"
        result = get_booking_base_url(str(TENANT_ID), lookup)

    assert result == "https://app.nicolify.com"
