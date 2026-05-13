"""Tests for DomainService._extract_root_domain static method — pure function, no DB."""

from luana_core_tenant_domains.application.domain_service import DomainService


class TestExtractRootDomain:
    def test_subdomain_returns_root(self):
        assert DomainService._extract_root_domain("www.example.com") == "example.com"

    def test_deep_subdomain_returns_two_parts(self):
        assert DomainService._extract_root_domain("go.visionarias.lat") == "visionarias.lat"

    def test_apex_domain_unchanged(self):
        """A bare second-level domain has no subdomain — method returns it as-is."""
        assert DomainService._extract_root_domain("example.com") == "example.com"

    def test_multi_level_subdomain_returns_root(self):
        assert DomainService._extract_root_domain("a.b.c.example.com") == "example.com"

    def test_single_label_returned_as_is(self):
        """Edge case: single-word hostname (e.g., localhost) has no dot — returned as-is."""
        assert DomainService._extract_root_domain("localhost") == "localhost"

    def test_nicolify_subdomain(self):
        assert DomainService._extract_root_domain("myshop.nicolify.com") == "nicolify.com"
