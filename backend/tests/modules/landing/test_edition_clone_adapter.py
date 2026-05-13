"""Integration tests for :class:`LandingEditionCloneAdapter` (Phase 3).

These touch the real ``landing_pages`` table so the SQL paths
(``get_for_edition`` + ``clone_to_edition``) are covered end-to-end.
"""

from __future__ import annotations

import uuid

from sqlalchemy import select

from luana_core_landing.application.edition_clone_adapter import (
    LandingEditionCloneAdapter,
)
from luana_core_landing.infrastructure.models.landing_model import LandingPageModel


def _insert_landing(
    db,
    *,
    tenant_id,
    offer_id,
    edition_id=None,
    slug="master-class",
    config=None,
):
    model = LandingPageModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        offer_id=offer_id,
        edition_id=edition_id,
        slug=slug,
        config=config
        if config is not None
        else {
            "archetype": "THE_EVENT",
            "slug": slug,
            "content": {
                "headline": "Únete el {{start_date}}",
                "subheadline": "En {{location}}",
                "meta": {"date_label": "{{start_date}}", "untouched": 7},
            },
            "is_published": True,
        },
        is_published=True,
    )
    db.add(model)
    db.flush()
    return model


class TestGetForEdition:
    def test_offer_level_lookup_matches_null_edition(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        offer_id = uuid.uuid4()
        _insert_landing(db, tenant_id=tenant_id, offer_id=offer_id, slug="template")

        adapter = LandingEditionCloneAdapter(db)
        result = adapter.get_for_edition(tenant_id, offer_id, None)

        assert result is not None
        assert result.slug == "template"

    def test_edition_scoped_lookup_returns_exact_row(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        offer_id = uuid.uuid4()
        edition_id = uuid.uuid4()
        _insert_landing(
            db,
            tenant_id=tenant_id,
            offer_id=offer_id,
            edition_id=edition_id,
            slug="cohort-one",
        )

        adapter = LandingEditionCloneAdapter(db)
        result = adapter.get_for_edition(tenant_id, offer_id, edition_id)

        assert result is not None
        assert result.slug == "cohort-one"

    def test_tenant_isolation(
        self,
        db,
        seed_tenant,
        seed_other_tenant,
        tenant_id,
        other_tenant_id,
    ):
        offer_id = uuid.uuid4()
        edition_id = uuid.uuid4()
        _insert_landing(
            db,
            tenant_id=other_tenant_id,
            offer_id=offer_id,
            edition_id=edition_id,
            slug="other",
        )

        adapter = LandingEditionCloneAdapter(db)
        assert adapter.get_for_edition(tenant_id, offer_id, edition_id) is None


class TestCloneToEdition:
    def test_literal_deep_copies_config_without_substitution(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        offer_id = uuid.uuid4()
        source = _insert_landing(db, tenant_id=tenant_id, offer_id=offer_id, slug="src")

        adapter = LandingEditionCloneAdapter(db)
        target_edition = uuid.uuid4()
        ref = adapter.clone_to_edition(
            tenant_id=tenant_id,
            offer_id=offer_id,
            source_landing_id=source.id,
            target_edition_id=target_edition,
            target_slug="src-ed2",
            strategy="literal",
        )

        assert ref.slug == "src-ed2"
        assert ref.id != source.id

        # Fetch the new row from the DB and confirm tokens are untouched.
        stmt = select(LandingPageModel).where(LandingPageModel.id == ref.id)
        clone = db.execute(stmt).scalars().first()
        assert clone is not None
        assert clone.edition_id == target_edition
        assert clone.slug == "src-ed2"
        assert clone.is_published is False
        assert clone.config["content"]["headline"] == "Únete el {{start_date}}"
        # Config slug is kept in sync with the model slug.
        assert clone.config["slug"] == "src-ed2"
        # Non-string leaves untouched through the deepcopy.
        assert clone.config["content"]["meta"]["untouched"] == 7

    def test_date_replace_substitutes_all_tokens(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        offer_id = uuid.uuid4()
        source = _insert_landing(db, tenant_id=tenant_id, offer_id=offer_id, slug="src2")

        adapter = LandingEditionCloneAdapter(db)
        ref = adapter.clone_to_edition(
            tenant_id=tenant_id,
            offer_id=offer_id,
            source_landing_id=source.id,
            target_edition_id=uuid.uuid4(),
            target_slug="src2-ed2",
            strategy="date_replace",
            substitutions={"start_date": "15 mayo", "location": "Lima"},
        )

        stmt = select(LandingPageModel).where(LandingPageModel.id == ref.id)
        clone = db.execute(stmt).scalars().first()
        content = clone.config["content"]
        assert content["headline"] == "Únete el 15 mayo"
        assert content["subheadline"] == "En Lima"
        assert content["meta"]["date_label"] == "15 mayo"

    def test_ai_regen_marks_for_async_rewrite(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        offer_id = uuid.uuid4()
        source = _insert_landing(db, tenant_id=tenant_id, offer_id=offer_id, slug="src3")

        adapter = LandingEditionCloneAdapter(db)
        ref = adapter.clone_to_edition(
            tenant_id=tenant_id,
            offer_id=offer_id,
            source_landing_id=source.id,
            target_edition_id=uuid.uuid4(),
            target_slug="src3-ed2",
            strategy="ai_regen",
            regeneration_context={"changes_brief": "focus on b2b"},
        )

        stmt = select(LandingPageModel).where(LandingPageModel.id == ref.id)
        clone = db.execute(stmt).scalars().first()
        assert clone.generation_job_status == "queued_ai_regen"

    def test_missing_source_raises(
        self,
        db,
        seed_tenant,
        tenant_id,
    ):
        import pytest

        adapter = LandingEditionCloneAdapter(db)
        with pytest.raises(ValueError, match="not found"):
            adapter.clone_to_edition(
                tenant_id=tenant_id,
                offer_id=uuid.uuid4(),
                source_landing_id=uuid.uuid4(),
                target_edition_id=uuid.uuid4(),
                target_slug="ghost",
                strategy="literal",
            )
