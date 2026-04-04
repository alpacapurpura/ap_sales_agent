import pytest
import uuid
from tests.factories import TenantFactory

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")


@pytest.fixture
def tenant_id():
    return TENANT_A


@pytest.fixture
def other_tenant_id():
    return TENANT_B


@pytest.fixture
def seed_tenant(db, tenant_id):
    """Insert a TenantModel row so landing FK constraints are satisfied."""
    tenant = TenantFactory.build(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def seed_other_tenant(db, other_tenant_id):
    """Insert a second TenantModel for tenant isolation tests."""
    tenant = TenantFactory.build(
        id=other_tenant_id,
        name="Other Tenant",
        slug="other-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant


@pytest.fixture
def sample_squeeze_config_dict():
    """Minimal valid LandingPageConfig dict for THE_SQUEEZE archetype."""
    return {
        "archetype": "THE_SQUEEZE",
        "slug": "my-squeeze-page",
        "content": {
            "headline": "Grab This Free Guide",
            "subheadline": "No more struggling with X",
            "bullets": ["Benefit 1", "Benefit 2", "Benefit 3"],
            "cta_text": "Send it now",
            "privacy_text": "Your data is safe.",
        },
    }


@pytest.fixture
def sample_transformer_config_dict():
    """Minimal valid LandingPageConfig dict for THE_TRANSFORMER archetype."""
    return {
        "archetype": "THE_TRANSFORMER",
        "slug": "my-transformer-page",
        "content": {
            "headline": "Become a 6-Figure Coach in 90 Days",
            "subheadline": "Even if you're starting from zero",
            "problem_text": "You're tired of trading time for money",
            "agitation_text": "Every month without a system costs you thousands",
            "solution_text": "The Accelerator Method gets you there fast",
            "method_name": "The Accelerator Method",
            "method_description": "A 3-phase system proven to work",
            "authority_name": "Jane Doe",
            "authority_bio": "Helped 500+ coaches scale to 6-figures",
            "modules": [
                {"title": "Module 1: Foundations", "description": "Build your base"},
            ],
            "price_anchor": "$2,997",
            "price_offer": "$997",
            "scarcity_text": "Only 10 spots left",
            "cta_text": "Join now",
        },
    }
