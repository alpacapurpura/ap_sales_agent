"""Unit tests for social_proof domain entities (Pydantic)."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from luana_core_social_proof.domain.authority_item import AuthorityItem
from luana_core_social_proof.domain.enums import (
    AuthorityType,
    SourceTable,
    SurfaceType,
    TestimonialMediaType,
)
from luana_core_social_proof.domain.placement import Placement
from luana_core_social_proof.domain.team_member import TeamMember
from luana_core_social_proof.domain.testimonial import Testimonial


@pytest.fixture
def tenant_id() -> uuid.UUID:
    return uuid.uuid4()


@pytest.fixture
def user_id() -> uuid.UUID:
    return uuid.uuid4()


class TestTestimonialEntity:
    def test_minimal_valid_testimonial(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        testimonial = Testimonial(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            author_name="Juana Pérez",
        )
        assert testimonial.media_type is TestimonialMediaType.TEXT
        assert testimonial.language == "es"
        assert testimonial.tags == []
        assert testimonial.is_active is True
        assert testimonial.deleted_at is None

    def test_rating_out_of_range_rejected(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        with pytest.raises(ValidationError):
            Testimonial(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                author_name="Juana Pérez",
                rating=7,
            )

    def test_rating_below_one_rejected(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        with pytest.raises(ValidationError):
            Testimonial(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                author_name="Juana Pérez",
                rating=0,
            )

    def test_author_name_required(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        with pytest.raises(ValidationError):
            Testimonial(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
            )  # type: ignore[call-arg]

    def test_media_type_enum_coercion_from_string(
        self,
        tenant_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> None:
        testimonial = Testimonial(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            author_name="Juana Pérez",
            media_type="video",
        )
        assert testimonial.media_type is TestimonialMediaType.VIDEO


class TestAuthorityItemEntity:
    def test_minimal_valid_authority(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        item = AuthorityItem(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            entity_name="Universidad Nacional",
            authority_type=AuthorityType.CERTIFICATION,
        )
        assert item.authority_type is AuthorityType.CERTIFICATION
        assert item.is_active is True
        assert item.deleted_at is None

    def test_authority_type_required(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        with pytest.raises(ValidationError):
            AuthorityItem(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                user_id=user_id,
                entity_name="Harvard",
            )  # type: ignore[call-arg]


class TestTeamMemberEntity:
    def test_minimal_valid_team_member(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        member = TeamMember(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            name="Chris Alpaca",
        )
        assert member.is_primary_voice is False
        assert member.gallery == []
        assert member.sort_order == 0
        assert member.deleted_at is None

    def test_gallery_accepts_url_list(self, tenant_id: uuid.UUID, user_id: uuid.UUID) -> None:
        member = TeamMember(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            user_id=user_id,
            name="Chris Alpaca",
            gallery=["https://cdn.example/1.png", "https://cdn.example/2.png"],
        )
        assert len(member.gallery) == 2


class TestPlacementEntity:
    def test_brand_homepage_allows_null_ref_id(self, tenant_id: uuid.UUID) -> None:
        placement = Placement(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            source_table=SourceTable.TESTIMONIAL,
            source_id=uuid.uuid4(),
            surface_type=SurfaceType.BRAND_HOMEPAGE,
            surface_ref_id=None,
        )
        assert placement.surface_ref_id is None
        assert placement.is_visible is True
        assert placement.sort_order == 0

    def test_offer_surface_requires_ref_id(self, tenant_id: uuid.UUID) -> None:
        with pytest.raises(ValidationError):
            Placement(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                source_table=SourceTable.TESTIMONIAL,
                source_id=uuid.uuid4(),
                surface_type=SurfaceType.OFFER,
                surface_ref_id=None,
            )

    def test_landing_surface_requires_ref_id(self, tenant_id: uuid.UUID) -> None:
        with pytest.raises(ValidationError):
            Placement(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                source_table=SourceTable.AUTHORITY_ITEM,
                source_id=uuid.uuid4(),
                surface_type=SurfaceType.LANDING_PAGE,
                surface_ref_id=None,
            )

    def test_brand_homepage_with_ref_id_rejected(self, tenant_id: uuid.UUID) -> None:
        """brand_homepage is tenant-wide — a ref_id is nonsensical and must be None."""
        with pytest.raises(ValidationError):
            Placement(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                source_table=SourceTable.TESTIMONIAL,
                source_id=uuid.uuid4(),
                surface_type=SurfaceType.BRAND_HOMEPAGE,
                surface_ref_id=uuid.uuid4(),
            )

    def test_soft_deleted_placement(self, tenant_id: uuid.UUID) -> None:
        placement = Placement(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            source_table=SourceTable.TEAM_MEMBER,
            source_id=uuid.uuid4(),
            surface_type=SurfaceType.OFFER,
            surface_ref_id=uuid.uuid4(),
            deleted_at=datetime.now(UTC),
        )
        assert placement.deleted_at is not None
