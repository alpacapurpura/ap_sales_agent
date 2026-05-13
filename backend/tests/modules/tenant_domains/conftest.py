"""Fixtures for tenant_domains module tests."""

import uuid

import pytest

from luana_core_tenant_domains.infrastructure.models.tenant_domain_model import (
    TenantDomainModel,
)


@pytest.fixture
def sample_domain_model(db, tenant_id):
    """Insert a TenantDomainModel row directly (bypasses service)."""
    model = TenantDomainModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        hostname="shop.example.com",
        domain_type="custom",
        status="pending_verification",
        is_primary=False,
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model
