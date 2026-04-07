"""
Tests for booking_url helper.

get_booking_base_url returns:
- A custom domain URL when the tenant has an active primary domain.
- settings.DASHBOARD_DOMAIN as fallback when no custom domain exists.
- settings.DASHBOARD_DOMAIN when an exception is raised internally.
"""

import uuid
from unittest.mock import MagicMock, patch

TENANT_ID = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")


def test_returns_custom_domain_when_active_primary_exists():
    """Returns https://<hostname> for a primary active domain."""
    from src.modules.scheduling.application.booking_url import get_booking_base_url
    from src.modules.tenant_domains.domain.domain_entity import DomainStatus

    mock_db = MagicMock()
    domain = MagicMock()
    domain.hostname = "booking.mystore.com"
    domain.is_primary = True
    domain.status = DomainStatus.ACTIVE

    with patch(
        "src.modules.tenant_domains.infrastructure.domain_repository_impl.DomainRepositoryImpl.list_by_tenant",
        return_value=[domain],
    ):
        result = get_booking_base_url(TENANT_ID, mock_db)

    assert result == "https://booking.mystore.com"


def test_falls_back_to_dashboard_domain_when_no_custom_domain():
    """Returns DASHBOARD_DOMAIN when the tenant has no domains."""
    from src.modules.scheduling.application.booking_url import get_booking_base_url

    mock_db = MagicMock()

    with (
        patch(
            "src.modules.tenant_domains.infrastructure.domain_repository_impl.DomainRepositoryImpl.list_by_tenant",
            return_value=[],
        ),
        patch(
            "src.modules.scheduling.application.booking_url.settings"
        ) as mock_settings,
    ):
        mock_settings.DASHBOARD_DOMAIN = "https://app.nicolify.com"
        result = get_booking_base_url(TENANT_ID, mock_db)

    assert result == "https://app.nicolify.com"


def test_falls_back_when_no_primary_active_domain():
    """Returns DASHBOARD_DOMAIN when domains exist but none is primary+active."""
    from src.modules.scheduling.application.booking_url import get_booking_base_url
    from src.modules.tenant_domains.domain.domain_entity import DomainStatus

    mock_db = MagicMock()
    non_primary = MagicMock()
    non_primary.hostname = "old.mystore.com"
    non_primary.is_primary = False
    non_primary.status = DomainStatus.ACTIVE

    with (
        patch(
            "src.modules.tenant_domains.infrastructure.domain_repository_impl.DomainRepositoryImpl.list_by_tenant",
            return_value=[non_primary],
        ),
        patch(
            "src.modules.scheduling.application.booking_url.settings"
        ) as mock_settings,
    ):
        mock_settings.DASHBOARD_DOMAIN = "https://app.nicolify.com"
        result = get_booking_base_url(TENANT_ID, mock_db)

    assert result == "https://app.nicolify.com"


def test_falls_back_on_exception():
    """Returns DASHBOARD_DOMAIN when the domain lookup raises an exception."""
    from src.modules.scheduling.application.booking_url import get_booking_base_url

    mock_db = MagicMock()

    with (
        patch(
            "src.modules.tenant_domains.infrastructure.domain_repository_impl.DomainRepositoryImpl.list_by_tenant",
            side_effect=RuntimeError("DB unreachable"),
        ),
        patch(
            "src.modules.scheduling.application.booking_url.settings"
        ) as mock_settings,
    ):
        mock_settings.DASHBOARD_DOMAIN = "https://app.nicolify.com"
        result = get_booking_base_url(TENANT_ID, mock_db)

    assert result == "https://app.nicolify.com"


def test_accepts_string_tenant_id():
    """Accepts a string tenant_id and converts it to UUID internally."""
    from src.modules.scheduling.application.booking_url import get_booking_base_url

    mock_db = MagicMock()

    with (
        patch(
            "src.modules.tenant_domains.infrastructure.domain_repository_impl.DomainRepositoryImpl.list_by_tenant",
            return_value=[],
        ),
        patch(
            "src.modules.scheduling.application.booking_url.settings"
        ) as mock_settings,
    ):
        mock_settings.DASHBOARD_DOMAIN = "https://app.nicolify.com"
        result = get_booking_base_url(str(TENANT_ID), mock_db)

    assert result == "https://app.nicolify.com"
