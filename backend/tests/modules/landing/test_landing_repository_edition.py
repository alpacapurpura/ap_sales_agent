"""Tests for edition-aware lookups on ``LandingRepository`` (Phase 3).

After Phase 3, landings may be either offer-level (``edition_id IS NULL``
— legacy/fallback template) or edition-scoped (``edition_id`` set). The
repository exposes ``get_by_offer_and_edition`` so callers can pick the
right row without leaking the ``edition_id IS NULL`` sentinel semantics
into service code.
"""

from __future__ import annotations

import uuid

from luana_core_landing.domain.content import LandingPageConfig, SqueezeContent
from luana_core_landing.domain.enums import LandingPageArchetype
from luana_core_landing.domain.landing_page import LandingPage
from luana_core_landing.infrastructure.repositories.landing_repository import (
    LandingRepository,
)


def _make_landing(
    tenant_id: uuid.UUID,
    offer_id: uuid.UUID,
    *,
    slug: str,
    edition_id: uuid.UUID | None = None,
) -> LandingPage:
    return LandingPage(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        offer_id=offer_id,
        edition_id=edition_id,
        slug=slug,
        config=LandingPageConfig(
            archetype=LandingPageArchetype.THE_SQUEEZE,
            slug=slug,
            content=SqueezeContent(
                headline="H",
                subheadline="S",
                bullets=["a", "b", "c"],
            ),
        ),
    )


class TestGetByOfferAndEdition:
    def test_offer_level_lookup_matches_only_null_edition(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        repo = LandingRepository(db)
        offer_id = uuid.uuid4()

        offer_level = repo.create(
            _make_landing(tenant_id, offer_id, slug="template"),
        )
        edition_scoped = repo.create(
            _make_landing(
                tenant_id,
                offer_id,
                slug="edition-one",
                edition_id=uuid.uuid4(),
            ),
        )

        result = repo.get_by_offer_and_edition(tenant_id, offer_id, None)
        assert result is not None
        assert result.id == offer_level.id
        # The edition-scoped row MUST NOT bleed into the offer-level lookup.
        assert result.id != edition_scoped.id

    def test_edition_scoped_lookup_returns_exact_match(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        repo = LandingRepository(db)
        offer_id = uuid.uuid4()
        edition_a = uuid.uuid4()
        edition_b = uuid.uuid4()

        landing_a = repo.create(
            _make_landing(tenant_id, offer_id, slug="a", edition_id=edition_a),
        )
        repo.create(
            _make_landing(tenant_id, offer_id, slug="b", edition_id=edition_b),
        )

        result = repo.get_by_offer_and_edition(tenant_id, offer_id, edition_a)
        assert result is not None
        assert result.id == landing_a.id

    def test_missing_edition_returns_none(self, db, seed_tenant, tenant_id):
        repo = LandingRepository(db)
        offer_id = uuid.uuid4()

        result = repo.get_by_offer_and_edition(tenant_id, offer_id, uuid.uuid4())
        assert result is None

    def test_tenant_isolation(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        repo = LandingRepository(db)
        offer_id = uuid.uuid4()
        edition_id = uuid.uuid4()

        repo.create(
            _make_landing(
                other_tenant_id,
                offer_id,
                slug="other-tenant",
                edition_id=edition_id,
            ),
        )

        # Same offer+edition, wrong tenant → must not leak.
        assert repo.get_by_offer_and_edition(tenant_id, offer_id, edition_id) is None
