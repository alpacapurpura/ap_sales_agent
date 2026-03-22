"""Tests for referral service: code generation, tenant isolation, Shopify extraction."""
import pytest


class TestReferralService:
    """Referral code generation and management."""

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_generate_code_produces_ref_prefix(self):
        """Generated code starts with REF- prefix."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_generate_code_unique_per_customer(self):
        """Each customer gets a unique code."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_get_codes_by_tenant_filters_correctly(self):
        """Only returns codes for the specified tenant_id."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_deactivate_code_sets_is_active_false(self):
        """Deactivated codes have is_active=False."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_extract_shopify_codes_sets_source_shopify(self):
        """Codes from Shopify have source='shopify'."""
        pass
