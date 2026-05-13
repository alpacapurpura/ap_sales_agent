"""Fixtures for tenant_profile module tests."""

from __future__ import annotations

import uuid
from datetime import timedelta
from unittest.mock import MagicMock

import pytest

from luana_core_tenant_profile.domain.tenant_profile import (
    RATE_LIMIT_WINDOW,
    TenantProfile,
)
from luana_core_tenant_profile.infrastructure.repositories.tenant_profile_repository import (
    SqlTenantProfileRepository,
)
from luana_core_platform.domain.datetime_utils import utc_now
from luana_core_platform.domain.expert_business_type import ExpertBusinessType

# Canonical tenant IDs for these tests (complementary to modules/conftest.py).
TENANT_ID = uuid.UUID("a1a10000-0000-0000-0000-000000000001")
OTHER_TENANT_ID = uuid.UUID("b2b20000-0000-0000-0000-000000000002")

# Convenient enum values
TYPE_A = ExpertBusinessType.ACADEMIA_INFOPRODUCTOR
TYPE_B = ExpertBusinessType.AGENCIA_FREELANCE
TYPE_C = ExpertBusinessType.CONSULTOR_PROFESIONAL


@pytest.fixture
def tenant_id() -> uuid.UUID:
    """Primary tenant for test isolation."""
    return TENANT_ID


@pytest.fixture
def other_tenant_id() -> uuid.UUID:
    """Secondary tenant to verify isolation."""
    return OTHER_TENANT_ID


@pytest.fixture
def new_profile(tenant_id: uuid.UUID) -> TenantProfile:
    """An in-memory profile that has never completed onboarding."""
    return TenantProfile(
        tenant_id=tenant_id,
        business_types=(),
        declared_at=None,
        updated_at=utc_now(),
        last_business_types_change_at=None,
    )


@pytest.fixture
def declared_profile(tenant_id: uuid.UUID) -> TenantProfile:
    """A profile that has completed onboarding 31 days ago (outside rate-limit)."""
    anchor = utc_now() - RATE_LIMIT_WINDOW - timedelta(days=1)
    return TenantProfile(
        tenant_id=tenant_id,
        business_types=(TYPE_A,),
        declared_at=anchor,
        updated_at=anchor,
        last_business_types_change_at=anchor,
    )


@pytest.fixture
def rate_limited_profile(tenant_id: uuid.UUID) -> TenantProfile:
    """A profile that changed its types 5 days ago (inside rate-limit window)."""
    anchor = utc_now() - timedelta(days=5)
    return TenantProfile(
        tenant_id=tenant_id,
        business_types=(TYPE_A,),
        declared_at=anchor,
        updated_at=anchor,
        last_business_types_change_at=anchor,
    )


@pytest.fixture
def repo(db: object) -> SqlTenantProfileRepository:
    """Real repository backed by the in-memory SQLite session."""
    return SqlTenantProfileRepository(db)


@pytest.fixture
def mock_repo() -> MagicMock:
    """Mock repository for service-layer tests (no DB required)."""
    return MagicMock(spec=SqlTenantProfileRepository)
