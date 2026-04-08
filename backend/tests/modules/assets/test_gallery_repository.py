"""Tests for GalleryRepository -- CRUD + tenant isolation."""

import uuid

from src.modules.assets.domain.entity import GalleryImage
from src.modules.assets.infrastructure.repositories.gallery_repository import (
    GalleryRepository,
)


def _make_gallery_image(
    tenant_id: uuid.UUID, offer_id: uuid.UUID = None
) -> GalleryImage:
    return GalleryImage(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        offer_id=offer_id or uuid.uuid4(),
        filename="test.png",
        storage_path="/tmp/test.png",  # noqa: S108
        public_url="https://example.com/test.png",
        user_description="Test image",
        ai_description="A test image",
        ai_colors=["#ffffff"],
        status="COMPLETED",
        error_message=None,
    )


class TestGalleryRepository:
    def test_get_by_id_filters_by_tenant(
        self, db, seed_tenant, tenant_id, seed_other_tenant, other_tenant_id
    ):
        repo = GalleryRepository(db)
        image = _make_gallery_image(tenant_id)
        created = repo.create(image)

        # Should find it with correct tenant
        retrieved = repo.get_by_id(created.id, tenant_id=tenant_id)
        assert retrieved is not None
        assert retrieved.id == created.id

        # Should NOT find it with wrong tenant
        retrieved_wrong = repo.get_by_id(created.id, tenant_id=other_tenant_id)
        assert retrieved_wrong is None
