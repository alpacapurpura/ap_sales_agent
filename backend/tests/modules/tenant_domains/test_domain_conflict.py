"""Tests for DomainService.detect_domain_conflict — mocks socket.gethostbyname."""

import socket
from unittest.mock import patch

import pytest

from luana_core_tenant_domains.application.domain_service import DomainService


@pytest.fixture
def service(db):
    """Service instance — DB needed to satisfy constructor, but not used in conflict tests."""
    return DomainService(db)


class TestDetectDomainConflict:
    def test_shopify_ip_returns_conflict(self, service):
        """A Shopify-owned IP triggers a conflict with a suggestion."""
        with patch("socket.gethostbyname", return_value="23.227.38.32"):
            result = service.detect_domain_conflict("shop.example.com")

        assert result is not None
        assert result["provider"] == "Shopify"
        assert result["detected_ip"] == "23.227.38.32"
        assert "go.example.com" in result["suggestion"]

    def test_all_shopify_ips_trigger_conflict(self, service):
        """All three Shopify IPs are in _KNOWN_PROVIDERS."""
        shopify_ips = ["23.227.38.32", "23.227.38.33", "23.227.38.34"]
        for ip in shopify_ips:
            with patch("socket.gethostbyname", return_value=ip):
                result = service.detect_domain_conflict("shop.example.com")
            assert result is not None
            assert result["provider"] == "Shopify"

    def test_unknown_ip_returns_none(self, service):
        """An unknown IP is not a conflict."""
        with patch("socket.gethostbyname", return_value="1.2.3.4"):
            result = service.detect_domain_conflict("shop.example.com")

        assert result is None

    def test_dns_failure_returns_none(self, service):
        """If DNS resolution fails, no conflict — domain simply unresolvable."""
        with patch(
            "socket.gethostbyname",
            side_effect=socket.gaierror("Name not found"),
        ):
            result = service.detect_domain_conflict("nonexistent.example.com")

        assert result is None

    def test_suggestion_uses_provider_prefix(self, service):
        """The suggestion subdomain uses the provider's suggestion_prefix."""
        with patch("socket.gethostbyname", return_value="23.227.38.32"):
            result = service.detect_domain_conflict("www.visionarias.lat")

        assert result["suggestion"] == "go.visionarias.lat"

    def test_conflict_message_contains_root_domain(self, service):
        """The conflict message references the root domain and provider."""
        with patch("socket.gethostbyname", return_value="23.227.38.33"):
            result = service.detect_domain_conflict("store.mysite.com")

        assert "mysite.com" in result["message"]
        assert "Shopify" in result["message"]
