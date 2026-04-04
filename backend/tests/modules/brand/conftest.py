import pytest
import uuid

from tests.factories import (
    TenantFactory,
    BrandIdentityFactory,
    BrandVisualsFactory,
    BrandStoryFactory,
    BrandSettingsFactory,
    AvatarFactory,
)

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
USER_A = uuid.UUID("cccc0000-0000-0000-0000-000000000001")


@pytest.fixture
def tenant_id():
    return TENANT_A


@pytest.fixture
def other_tenant_id():
    return TENANT_B


@pytest.fixture
def user_id():
    return USER_A


@pytest.fixture
def sample_identity():
    return BrandIdentityFactory(
        brand_name="TestBrand",
        tagline="Test tagline",
        description="A test brand",
        industry="Technology",
        website="https://testbrand.com",
        founding_year="2020",
    )


@pytest.fixture
def sample_visuals():
    return BrandVisualsFactory(
        primary_color="#0f172a",
        secondary_color="#1e293b",
        accent_color="#3b82f6",
        background_color="#ffffff",
        font_heading="Inter",
        font_body="Inter",
    )


@pytest.fixture
def sample_story():
    return BrandStoryFactory(
        origin_story="Founded in a garage",
        mission="Make the world better",
        vision="Be the best",
    )


@pytest.fixture
def sample_avatar(tenant_id, user_id):
    return AvatarFactory(
        tenant_id=tenant_id,
        user_id=user_id,
        name="Ideal Customer",
        icp_description="Tech-savvy entrepreneur",
        anti_avatar="People who don't value quality",
    )


@pytest.fixture
def sample_settings(sample_identity, sample_visuals, sample_story):
    return BrandSettingsFactory(
        identity=sample_identity,
        visuals=sample_visuals,
        story=sample_story,
    )


@pytest.fixture
def seed_tenant(db, tenant_id):
    """Insert a TenantModel row so BrandRepository can find it."""
    tenant = TenantFactory.build(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant
