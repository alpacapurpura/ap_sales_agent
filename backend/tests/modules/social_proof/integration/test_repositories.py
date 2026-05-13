"""Integration tests for social_proof repositories (SQLite in-memory)."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

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
from luana_core_social_proof.infrastructure.repositories import (
    AuthorityItemRepository,
    PlacementRepository,
    TeamMemberRepository,
    TestimonialRepository,
)
from tests.modules.conftest import TENANT_A, TENANT_B, USER_A

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _testimonial(tenant_id: uuid.UUID) -> Testimonial:
    return Testimonial(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=USER_A,
        author_name="Juana Pérez",
        content="Experiencia increíble",
        rating=5,
    )


def _authority(tenant_id: uuid.UUID) -> AuthorityItem:
    return AuthorityItem(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=USER_A,
        entity_name="Universidad Nacional",
        authority_type=AuthorityType.CERTIFICATION,
    )


def _team(tenant_id: uuid.UUID) -> TeamMember:
    return TeamMember(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        user_id=USER_A,
        name="Chris Alpaca",
    )


class TestTestimonialRepository:
    def test_create_and_get(self, db: Session) -> None:
        repo = TestimonialRepository(db)
        created = repo.create(_testimonial(TENANT_A))
        fetched = repo.get_by_id(TENANT_A, created.id)
        assert fetched is not None
        assert fetched.author_name == "Juana Pérez"
        assert fetched.rating == 5
        assert fetched.media_type is TestimonialMediaType.TEXT

    def test_get_by_id_wrong_tenant_returns_none(self, db: Session) -> None:
        repo = TestimonialRepository(db)
        created = repo.create(_testimonial(TENANT_A))
        assert repo.get_by_id(TENANT_B, created.id) is None

    def test_list_by_tenant_excludes_other_tenants(self, db: Session) -> None:
        repo = TestimonialRepository(db)
        repo.create(_testimonial(TENANT_A))
        repo.create(_testimonial(TENANT_A))
        repo.create(_testimonial(TENANT_B))
        assert len(repo.list_by_tenant(TENANT_A)) == 2
        assert len(repo.list_by_tenant(TENANT_B)) == 1

    def test_list_by_tenant_excludes_soft_deleted(self, db: Session) -> None:
        repo = TestimonialRepository(db)
        t = repo.create(_testimonial(TENANT_A))
        repo.soft_delete(TENANT_A, t.id)
        assert len(repo.list_by_tenant(TENANT_A)) == 0

    def test_soft_delete_wrong_tenant_returns_false(self, db: Session) -> None:
        repo = TestimonialRepository(db)
        t = repo.create(_testimonial(TENANT_A))
        assert repo.soft_delete(TENANT_B, t.id) is False
        assert repo.get_by_id(TENANT_A, t.id) is not None

    def test_update_writes_and_returns_fresh(self, db: Session) -> None:
        repo = TestimonialRepository(db)
        t = repo.create(_testimonial(TENANT_A))
        updated = repo.update(TENANT_A, t.id, {"content": "Cambió el texto"})
        assert updated is not None
        assert updated.content == "Cambió el texto"


class TestAuthorityItemRepository:
    def test_create_roundtrip(self, db: Session) -> None:
        repo = AuthorityItemRepository(db)
        created = repo.create(_authority(TENANT_A))
        fetched = repo.get_by_id(TENANT_A, created.id)
        assert fetched is not None
        assert fetched.authority_type is AuthorityType.CERTIFICATION

    def test_tenant_isolation_on_list(self, db: Session) -> None:
        repo = AuthorityItemRepository(db)
        repo.create(_authority(TENANT_A))
        repo.create(_authority(TENANT_B))
        assert len(repo.list_by_tenant(TENANT_A)) == 1
        assert len(repo.list_by_tenant(TENANT_B)) == 1


class TestTeamMemberRepository:
    def test_create_and_list_ordered(self, db: Session) -> None:
        repo = TeamMemberRepository(db)
        a = repo.create(
            TeamMember(
                id=uuid.uuid4(),
                tenant_id=TENANT_A,
                user_id=USER_A,
                name="Bravo",
                sort_order=2,
            ),
        )
        b = repo.create(
            TeamMember(
                id=uuid.uuid4(),
                tenant_id=TENANT_A,
                user_id=USER_A,
                name="Alpha",
                sort_order=1,
            ),
        )
        listed = repo.list_by_tenant(TENANT_A)
        # Lower sort_order comes first
        assert [m.id for m in listed] == [b.id, a.id]


class TestPlacementRepository:
    def test_cascade_soft_delete_for_source(self, db: Session) -> None:
        trepo = TestimonialRepository(db)
        prepo = PlacementRepository(db)

        testimonial = trepo.create(_testimonial(TENANT_A))

        # Two placements: brand-wide + one offer
        prepo.create(
            Placement(
                id=uuid.uuid4(),
                tenant_id=TENANT_A,
                source_table=SourceTable.TESTIMONIAL,
                source_id=testimonial.id,
                surface_type=SurfaceType.BRAND_HOMEPAGE,
                surface_ref_id=None,
            ),
        )
        offer_ref = uuid.uuid4()
        prepo.create(
            Placement(
                id=uuid.uuid4(),
                tenant_id=TENANT_A,
                source_table=SourceTable.TESTIMONIAL,
                source_id=testimonial.id,
                surface_type=SurfaceType.OFFER,
                surface_ref_id=offer_ref,
            ),
        )

        n = prepo.cascade_soft_delete_for_source(
            TENANT_A,
            SourceTable.TESTIMONIAL,
            testimonial.id,
        )
        assert n == 2
        assert prepo.list_by_source(TENANT_A, SourceTable.TESTIMONIAL, testimonial.id) == []

    def test_list_for_surface_filters_visible_and_alive(self, db: Session) -> None:
        trepo = TestimonialRepository(db)
        prepo = PlacementRepository(db)
        t1 = trepo.create(_testimonial(TENANT_A))
        t2 = trepo.create(_testimonial(TENANT_A))

        p1 = prepo.create(
            Placement(
                id=uuid.uuid4(),
                tenant_id=TENANT_A,
                source_table=SourceTable.TESTIMONIAL,
                source_id=t1.id,
                surface_type=SurfaceType.BRAND_HOMEPAGE,
                surface_ref_id=None,
                is_visible=True,
            ),
        )
        prepo.create(
            Placement(
                id=uuid.uuid4(),
                tenant_id=TENANT_A,
                source_table=SourceTable.TESTIMONIAL,
                source_id=t2.id,
                surface_type=SurfaceType.BRAND_HOMEPAGE,
                surface_ref_id=None,
                is_visible=False,
            ),
        )
        visible = prepo.list_for_surface(
            TENANT_A,
            SurfaceType.BRAND_HOMEPAGE,
            None,
        )
        assert [p.id for p in visible] == [p1.id]
