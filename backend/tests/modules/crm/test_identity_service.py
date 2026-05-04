"""
Tests for IdentityService get_or_create_customer.

CRM-04: Identity resolution — returns existing or creates new with lead_source.
"""

import uuid
from unittest.mock import MagicMock, patch

import pytest

from src.modules.crm.application.services.identity_service import IdentityService
from src.modules.crm.domain.enums import IdentityType

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
OTHER_TENANT_ID = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_repo():
    """Return a MagicMock standing in for CustomerRepository."""
    return MagicMock()


def _make_mock_customer(tenant_id: uuid.UUID, email: str = "test@test.com"):
    """Return a domain CustomerProfile mock."""
    customer = MagicMock()
    customer.id = uuid.uuid4()
    customer.tenant_id = tenant_id
    customer.primary_email = email
    return customer


# ---------------------------------------------------------------------------
# get_or_create_customer — returns existing
# ---------------------------------------------------------------------------


class TestGetOrCreateExisting:
    """When find_by_identity returns a customer, it is returned unchanged."""

    def test_returns_existing_customer(self):
        """find_by_identity hit → (customer, False)."""
        repo = _make_mock_repo()
        existing = _make_mock_customer(SAMPLE_TENANT_ID)
        repo.find_by_identity.return_value = existing

        svc = IdentityService(repo)
        result, was_created = svc.get_or_create_customer(
            tenant_id=SAMPLE_TENANT_ID,
            identity_type=IdentityType.EMAIL,
            identity_value="test@test.com",
            profile_data={"first_name": "Test"},
        )

        assert result is existing
        assert was_created is False
        repo.find_by_identity.assert_called_once_with(
            identity_value="test@test.com",
            identity_type=IdentityType.EMAIL,
            tenant_id=SAMPLE_TENANT_ID,
        )
        repo.create_with_identity.assert_not_called()

    def test_returns_existing_with_lead_source(self):
        """lead_source/lead_source_detail are passed but not used when existing."""
        repo = _make_mock_repo()
        existing = _make_mock_customer(SAMPLE_TENANT_ID)
        repo.find_by_identity.return_value = existing

        svc = IdentityService(repo)
        result, was_created = svc.get_or_create_customer(
            tenant_id=SAMPLE_TENANT_ID,
            identity_type=IdentityType.WHATSAPP,
            identity_value="5491112345678",
            profile_data={},
            lead_source="instagram_ad",
            lead_source_detail="spring_campaign",
        )

        assert result is existing
        assert was_created is False
        repo.create_with_identity.assert_not_called()


# ---------------------------------------------------------------------------
# get_or_create_customer — creates new
# ---------------------------------------------------------------------------


class TestGetOrCreateNew:
    """When find_by_identity returns None, a new customer is created."""

    def test_creates_new_customer(self):
        """find_by_identity miss → create_with_identity called → (new, True)."""
        repo = _make_mock_repo()
        repo.find_by_identity.return_value = None
        new_customer = _make_mock_customer(SAMPLE_TENANT_ID, "new@test.com")
        repo.create_with_identity.return_value = new_customer

        svc = IdentityService(repo)
        profile_data = {"first_name": "New", "last_name": "User"}
        result, was_created = svc.get_or_create_customer(
            tenant_id=SAMPLE_TENANT_ID,
            identity_type=IdentityType.EMAIL,
            identity_value="new@test.com",
            profile_data=profile_data,
        )

        assert result is new_customer
        assert was_created is True
        repo.create_with_identity.assert_called_once_with(
            tenant_id=SAMPLE_TENANT_ID,
            identity_type=IdentityType.EMAIL,
            identity_value="new@test.com",
            profile_data=profile_data,
            lead_source=None,
            lead_source_detail=None,
        )

    def test_creates_with_lead_source(self):
        """lead_source and lead_source_detail forwarded to create_with_identity."""
        repo = _make_mock_repo()
        repo.find_by_identity.return_value = None
        new_customer = _make_mock_customer(SAMPLE_TENANT_ID)
        repo.create_with_identity.return_value = new_customer

        svc = IdentityService(repo)
        result, was_created = svc.get_or_create_customer(
            tenant_id=SAMPLE_TENANT_ID,
            identity_type=IdentityType.TELEGRAM,
            identity_value="tg_user_123",
            profile_data={"first_name": "TG"},
            lead_source="referral",
            lead_source_detail="partner_xyz",
        )

        assert was_created is True
        call_kwargs = repo.create_with_identity.call_args.kwargs
        assert call_kwargs["lead_source"] == "referral"
        assert call_kwargs["lead_source_detail"] == "partner_xyz"


# ---------------------------------------------------------------------------
# Tenant isolation
# ---------------------------------------------------------------------------


class TestTenantIsolation:
    """Identity lookups are scoped to tenant_id."""

    def test_searches_only_within_tenant(self):
        """A customer from another tenant is not found → new one created."""
        repo = _make_mock_repo()
        # Simulate: no customer found for SAMPLE_TENANT_ID
        repo.find_by_identity.return_value = None
        new_customer = _make_mock_customer(SAMPLE_TENANT_ID)
        repo.create_with_identity.return_value = new_customer

        svc = IdentityService(repo)
        svc.get_or_create_customer(
            tenant_id=SAMPLE_TENANT_ID,
            identity_type=IdentityType.EMAIL,
            identity_value="shared@test.com",
            profile_data={},
        )

        # The find call used SAMPLE_TENANT_ID, not OTHER_TENANT_ID
        repo.find_by_identity.assert_called_once()
        call_kwargs = repo.find_by_identity.call_args.kwargs
        assert call_kwargs["tenant_id"] == SAMPLE_TENANT_ID

    def test_different_tenants_create_separate_customers(self):
        """Two tenants with same identity_value get separate customers."""
        repo = _make_mock_repo()
        repo.find_by_identity.return_value = None
        customer_a = _make_mock_customer(SAMPLE_TENANT_ID)
        customer_b = _make_mock_customer(OTHER_TENANT_ID)
        repo.create_with_identity.side_effect = [customer_a, customer_b]

        svc = IdentityService(repo)

        result_a, _ = svc.get_or_create_customer(
            tenant_id=SAMPLE_TENANT_ID,
            identity_type=IdentityType.EMAIL,
            identity_value="shared@test.com",
            profile_data={},
        )
        result_b, _ = svc.get_or_create_customer(
            tenant_id=OTHER_TENANT_ID,
            identity_type=IdentityType.EMAIL,
            identity_value="shared@test.com",
            profile_data={},
        )

        assert result_a is customer_a
        assert result_b is customer_b
        assert repo.create_with_identity.call_count == 2
