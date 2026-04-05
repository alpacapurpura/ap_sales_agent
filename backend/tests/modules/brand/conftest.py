"""Fixtures for brand module tests."""

import pytest

from tests.factories import (
    AvatarFactory,
    BrandIdentityFactory,
    BrandSettingsFactory,
    BrandStoryFactory,
    BrandVisualsFactory,
)


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
