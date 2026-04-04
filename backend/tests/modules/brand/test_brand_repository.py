"""Tests for BrandRepository -- JSONB persistence in Tenant.config_json."""
import pytest
import uuid
from src.modules.brand.infrastructure.repositories.brand_repository import BrandRepository
from src.modules.brand.domain import BrandSettings, BrandIdentity


class TestBrandRepository:
    def test_get_settings_empty_tenant(self, db, seed_tenant, tenant_id):
        repo = BrandRepository(db)
        settings = repo.get_settings(tenant_id)
        assert isinstance(settings, BrandSettings)
        assert settings.identity is None

    def test_get_settings_nonexistent_tenant(self, db):
        repo = BrandRepository(db)
        settings = repo.get_settings(uuid.uuid4())
        assert isinstance(settings, BrandSettings)

    def test_save_and_retrieve(self, db, seed_tenant, tenant_id, sample_settings):
        repo = BrandRepository(db)
        repo.save_settings(tenant_id, sample_settings)

        retrieved = repo.get_settings(tenant_id)
        assert retrieved.identity is not None
        assert retrieved.identity.brand_name == "TestBrand"
        assert retrieved.visuals.primary_color == "#0f172a"

    def test_save_overwrites(self, db, seed_tenant, tenant_id):
        repo = BrandRepository(db)

        # First save
        s1 = BrandSettings(identity=BrandIdentity(brand_name="First"))
        repo.save_settings(tenant_id, s1)

        # Second save
        s2 = BrandSettings(identity=BrandIdentity(brand_name="Second"))
        repo.save_settings(tenant_id, s2)

        retrieved = repo.get_settings(tenant_id)
        assert retrieved.identity.brand_name == "Second"

    def test_tenant_isolation(self, db, seed_tenant, tenant_id):
        """Settings saved for tenant A are not visible to tenant B."""
        repo = BrandRepository(db)
        repo.save_settings(tenant_id, BrandSettings(identity=BrandIdentity(brand_name="A")))

        other = repo.get_settings(uuid.uuid4())
        assert other.identity is None

    def test_save_nonexistent_tenant_raises(self, db):
        repo = BrandRepository(db)
        with pytest.raises(ValueError, match="Tenant not found"):
            repo.save_settings(uuid.uuid4(), BrandSettings())
