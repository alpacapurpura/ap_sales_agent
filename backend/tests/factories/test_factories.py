"""Smoke tests to verify factories produce valid instances."""

from tests.factories import (
    AvatarFactory,
    BrandIdentityFactory,
    BrandSettingsFactory,
    BrandStoryFactory,
    BrandVisualsFactory,
    TenantFactory,
)


def test_tenant_factory_builds_valid_instance():
    tenant = TenantFactory.build()
    assert tenant.id is not None
    assert tenant.name
    assert tenant.slug
    assert tenant.is_active is True


def test_brand_identity_factory():
    identity = BrandIdentityFactory()
    assert identity.brand_name
    assert identity.industry


def test_brand_visuals_factory():
    visuals = BrandVisualsFactory()
    assert visuals.primary_color
    assert visuals.font_heading


def test_brand_story_factory():
    story = BrandStoryFactory()
    assert story.origin_story
    assert story.mission


def test_brand_settings_factory():
    settings = BrandSettingsFactory()
    assert settings.identity is not None
    assert settings.visuals is not None
    assert settings.story is not None
    assert isinstance(settings.team, list)


def test_avatar_factory():
    avatar = AvatarFactory()
    assert avatar.id is not None
    assert avatar.tenant_id is not None
    assert avatar.name
    assert avatar.scope == "GLOBAL"


def test_factories_produce_unique_data():
    t1 = TenantFactory.build()
    t2 = TenantFactory.build()
    assert t1.id != t2.id
    assert t1.slug != t2.slug


def test_factory_overrides():
    tenant = TenantFactory.build(name="Custom Tenant", is_active=False)
    assert tenant.name == "Custom Tenant"
    assert tenant.is_active is False

    identity = BrandIdentityFactory(brand_name="Override Corp")
    assert identity.brand_name == "Override Corp"
