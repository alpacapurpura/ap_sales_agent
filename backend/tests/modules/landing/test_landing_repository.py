"""Tests for LandingRepository — CRUD, slug uniqueness, soft delete, tenant isolation."""

import uuid

import pytest

from luana_core_landing.domain.content import LandingPageConfig, SqueezeContent
from luana_core_landing.domain.enums import LandingPageArchetype
from luana_core_landing.domain.landing_page import LandingPage
from luana_core_landing.infrastructure.repositories.landing_repository import (
    LandingRepository,
)


def _make_landing(
    tenant_id: uuid.UUID,
    slug: str = "test-page",
    offer_id: uuid.UUID | None = None,
    is_published: bool = False,
) -> LandingPage:
    config = LandingPageConfig(
        archetype=LandingPageArchetype.THE_SQUEEZE,
        slug=slug,
        content=SqueezeContent(
            headline="Free Guide",
            subheadline="No more struggle",
            bullets=["B1", "B2", "B3"],
        ),
    )
    return LandingPage(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        offer_id=offer_id,
        slug=slug,
        config=config,
        is_published=is_published,
    )


class TestLandingRepositoryCRUD:
    def test_create_and_get_by_id(self, db, seed_tenant, tenant_id):
        repo = LandingRepository(db)
        landing = _make_landing(tenant_id, slug="create-test")

        created = repo.create(landing)
        retrieved = repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.slug == "create-test"
        assert retrieved.tenant_id == tenant_id

    def test_get_by_id_nonexistent_returns_none(self, db, seed_tenant):
        repo = LandingRepository(db)
        result = repo.get_by_id(uuid.uuid4())
        assert result is None

    def test_list_by_tenant_returns_only_own_pages(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        repo = LandingRepository(db)
        repo.create(_make_landing(tenant_id, slug="page-a1"))
        repo.create(_make_landing(tenant_id, slug="page-a2"))
        repo.create(_make_landing(other_tenant_id, slug="page-b1"))

        pages = repo.list_by_tenant(tenant_id)
        assert len(pages) == 2
        assert all(p.tenant_id == tenant_id for p in pages)

    def test_list_by_tenant_empty_returns_empty_list(self, db, seed_tenant, tenant_id):
        repo = LandingRepository(db)
        result = repo.list_by_tenant(tenant_id)
        assert result == []

    def test_update_slug_and_publish(self, db, seed_tenant, tenant_id):
        repo = LandingRepository(db)
        landing = _make_landing(tenant_id, slug="old-slug")
        created = repo.create(landing)

        created.slug = "new-slug"
        created.is_published = True
        # Config slug must also match for consistency
        created.config.slug = "new-slug"

        updated = repo.update(created)
        assert updated.slug == "new-slug"
        assert updated.is_published is True

    def test_update_nonexistent_raises(self, db, seed_tenant, tenant_id):
        repo = LandingRepository(db)
        phantom = _make_landing(tenant_id)
        with pytest.raises(ValueError, match="Landing Page not found"):
            repo.update(phantom)


class TestSlugUniquenessPerTenant:
    def test_same_slug_different_tenants_is_allowed(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        """Slug uniqueness is scoped per tenant — same slug for two tenants must not conflict."""
        repo = LandingRepository(db)
        repo.create(_make_landing(tenant_id, slug="shared-slug"))
        # This should NOT raise
        result = repo.create(_make_landing(other_tenant_id, slug="shared-slug"))
        assert result.slug == "shared-slug"
        assert result.tenant_id == other_tenant_id

    def test_get_by_slug_and_tenant_returns_correct_page(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        repo = LandingRepository(db)
        repo.create(_make_landing(tenant_id, slug="shared-slug"))
        repo.create(_make_landing(other_tenant_id, slug="shared-slug"))

        page_a = repo.get_by_slug_and_tenant("shared-slug", tenant_id)
        page_b = repo.get_by_slug_and_tenant("shared-slug", other_tenant_id)

        assert page_a.tenant_id == tenant_id
        assert page_b.tenant_id == other_tenant_id

    def test_get_by_slug_and_tenant_nonexistent_returns_none(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        repo = LandingRepository(db)
        result = repo.get_by_slug_and_tenant("ghost-slug", tenant_id)
        assert result is None


class TestSoftDelete:
    def test_soft_deleted_page_not_in_list(self, db, seed_tenant, tenant_id):
        """After setting deleted_at, the page should not appear in list_by_tenant."""
        from datetime import datetime, timezone

        from sqlalchemy import select

        from luana_core_landing.infrastructure.models.landing_model import (
            LandingPageModel,
        )

        repo = LandingRepository(db)
        landing = _make_landing(tenant_id, slug="to-delete")
        created = repo.create(landing)

        # Simulate soft delete directly on the ORM model
        stmt = select(LandingPageModel).where(LandingPageModel.id == created.id)
        model = db.execute(stmt).scalars().first()
        model.deleted_at = datetime.now(timezone.utc)
        db.commit()

        pages = repo.list_by_tenant(tenant_id)
        assert all(p.id != created.id for p in pages)

    def test_soft_deleted_page_not_found_by_id(self, db, seed_tenant, tenant_id):
        from datetime import datetime, timezone

        from sqlalchemy import select

        from luana_core_landing.infrastructure.models.landing_model import (
            LandingPageModel,
        )

        repo = LandingRepository(db)
        landing = _make_landing(tenant_id, slug="to-delete-by-id")
        created = repo.create(landing)

        stmt = select(LandingPageModel).where(LandingPageModel.id == created.id)
        model = db.execute(stmt).scalars().first()
        model.deleted_at = datetime.now(timezone.utc)
        db.commit()

        assert repo.get_by_id(created.id) is None

    def test_soft_deleted_page_not_found_by_slug(self, db, seed_tenant, tenant_id):
        from datetime import datetime, timezone

        from sqlalchemy import select

        from luana_core_landing.infrastructure.models.landing_model import (
            LandingPageModel,
        )

        repo = LandingRepository(db)
        landing = _make_landing(tenant_id, slug="deleted-slug")
        created = repo.create(landing)

        stmt = select(LandingPageModel).where(LandingPageModel.id == created.id)
        model = db.execute(stmt).scalars().first()
        model.deleted_at = datetime.now(timezone.utc)
        db.commit()

        assert repo.get_by_slug_and_tenant("deleted-slug", tenant_id) is None


class TestTenantIsolation:
    def test_get_by_id_returns_page_regardless_of_tenant(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        """get_by_id has no tenant filter — tests that data exists but is opaque without slug+tenant."""
        repo = LandingRepository(db)
        page_b = repo.create(_make_landing(other_tenant_id, slug="tenant-b-page"))

        # get_by_id has no tenant scope — this is intentional for admin use
        result = repo.get_by_id(page_b.id)
        assert result is not None
        assert result.tenant_id == other_tenant_id

    def test_list_by_tenant_a_does_not_include_tenant_b_pages(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        repo = LandingRepository(db)
        repo.create(_make_landing(other_tenant_id, slug="only-b-page"))

        pages_a = repo.list_by_tenant(tenant_id)
        assert len(pages_a) == 0

    def test_get_by_slug_and_tenant_does_not_cross_tenants(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        """Tenant A cannot fetch tenant B's page using tenant B's slug with tenant A's ID."""
        repo = LandingRepository(db)
        repo.create(_make_landing(other_tenant_id, slug="secret-page"))

        result = repo.get_by_slug_and_tenant("secret-page", tenant_id)
        assert result is None
