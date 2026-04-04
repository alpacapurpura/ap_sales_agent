import pytest
import uuid
from unittest.mock import MagicMock
from src.modules.brand.domain import (
    BrandSettings, BrandIdentity, BrandVisuals, BrandStory, BrandStrategy,
    BrandContact, BrandTestimonial, BrandAuthorityItem, KeyFigure,
    BrandPositioning, BrandNarrative, CommunicationAssets,
    Avatar,
)
from src.modules.brand.infrastructure.models.avatar_model import AvatarModel

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
    return BrandIdentity(
        brand_name="TestBrand",
        tagline="Test tagline",
        description="A test brand",
        industry="Technology",
        website="https://testbrand.com",
        founding_year="2020",
    )


@pytest.fixture
def sample_visuals():
    return BrandVisuals(
        primary_color="#0f172a",
        secondary_color="#1e293b",
        accent_color="#3b82f6",
        background_color="#ffffff",
        font_heading="Inter",
        font_body="Inter",
    )


@pytest.fixture
def sample_story():
    return BrandStory(
        origin_story="Founded in a garage",
        mission="Make the world better",
        vision="Be the best",
    )


@pytest.fixture
def sample_avatar(tenant_id, user_id):
    return Avatar(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=user_id,
        name="Ideal Customer",
        scope="GLOBAL",
        icp_description="Tech-savvy entrepreneur",
        anti_avatar="People who don't value quality",
        is_default=False,
    )


@pytest.fixture
def sample_settings(sample_identity, sample_visuals, sample_story):
    return BrandSettings(
        identity=sample_identity,
        visuals=sample_visuals,
        story=sample_story,
        team=[],
        testimonials=[],
        authority_vault=[],
    )


@pytest.fixture
def seed_tenant(db, tenant_id):
    """Insert a TenantModel row so BrandRepository can find it."""
    from src.modules.iam.infrastructure.models.tenant_model import TenantModel
    tenant = TenantModel(
        id=tenant_id,
        name="Test Tenant",
        slug="test-tenant",
        config_json={},
    )
    db.add(tenant)
    db.commit()
    return tenant
