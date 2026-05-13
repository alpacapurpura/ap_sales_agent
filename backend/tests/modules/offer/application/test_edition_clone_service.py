"""Tests for :class:`EditionCloneService` (Phase 3).

Covers the three clone strategies + the cross-aggregate fan-out
(edition → landing → assets). The landing collaborator is a fake
adapter so these tests stay inside the offer module boundary and
exercise the orchestration logic without touching the landing DB.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import pytest

from luana_core_offer_studio.application.edition_clone_service import (
    CloneStrategy,
    EditionCloneService,
)
from luana_core_offer_studio.application.launch_edition_service import LaunchEditionService
from luana_core_offer_studio.application.ports import IEditionLandingClonePort, LandingRef
from luana_core_offer_studio.domain.assets import OfferAsset
from luana_core_offer_studio.domain.enums import AssetSource, AssetStatus, AssetType
from luana_core_offer_studio.domain.launch_edition import LaunchEditionCreate
from luana_core_offer_studio.domain.offer import PricingStructure
from luana_core_offer_studio.infrastructure.models.launch_edition_model import (
    LaunchEditionModel,
)
from luana_core_offer_studio.infrastructure.repositories.offer_asset_repository import (
    OfferAssetRepository,
)
from tests.modules.offer.conftest import create_product_model

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


# -------------------------------------------------------------- helpers & fakes


@dataclass
class _CloneCall:
    source_landing_id: uuid.UUID
    target_edition_id: uuid.UUID
    target_slug: str
    strategy: str
    substitutions: dict[str, str] | None
    regeneration_context: dict[str, Any] | None


@dataclass
class FakeLandingClonePort(IEditionLandingClonePort):
    """In-memory port double that records every call.

    Maps ``(tenant, offer, edition)`` → :class:`LandingRef` seeds so the
    clone service thinks a landing exists; clones allocate a new ref and
    push a :class:`_CloneCall` onto :attr:`calls` for assertions.
    """

    seed: dict[tuple[uuid.UUID, uuid.UUID, uuid.UUID | None], LandingRef] = field(
        default_factory=dict,
    )
    calls: list[_CloneCall] = field(default_factory=list)

    def get_for_edition(
        self,
        tenant_id: uuid.UUID,
        offer_id: uuid.UUID,
        edition_id: uuid.UUID | None,
    ) -> LandingRef | None:
        return self.seed.get((tenant_id, offer_id, edition_id))

    def clone_to_edition(
        self,
        *,
        tenant_id: uuid.UUID,
        offer_id: uuid.UUID,
        source_landing_id: uuid.UUID,
        target_edition_id: uuid.UUID,
        target_slug: str,
        strategy: str,
        substitutions: dict[str, str] | None = None,
        regeneration_context: dict[str, Any] | None = None,
    ) -> LandingRef:
        self.calls.append(
            _CloneCall(
                source_landing_id=source_landing_id,
                target_edition_id=target_edition_id,
                target_slug=target_slug,
                strategy=strategy,
                substitutions=substitutions,
                regeneration_context=regeneration_context,
            ),
        )
        new_ref = LandingRef(id=uuid.uuid4(), slug=target_slug)
        self.seed[(tenant_id, offer_id, target_edition_id)] = new_ref
        return new_ref


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    model = create_product_model(tenant_id, archetype="EXPERIENCIA")
    db.add(model)
    db.flush()
    return model.id


def _seed_source_edition(db: Session, tenant_id: uuid.UUID, offer_id: uuid.UUID):
    svc = LaunchEditionService(db)
    return svc.create_edition(
        offer_id=offer_id,
        tenant_id=tenant_id,
        start_date=datetime(2026, 5, 15, 18, 0, tzinfo=timezone.utc),
        edition_name="Edición Mayo",
        pricing_override=[PricingStructure(label="Early Bird", total_amount=300.0)],
        capacity=50,
        location_override={"city": "Lima"},
        notes="nota original",
    )


def _make_asset(
    tenant_id: uuid.UUID,
    offer_id: uuid.UUID,
    *,
    name: str,
    edition_id: uuid.UUID | None = None,
    shared: bool = False,
) -> OfferAsset:
    return OfferAsset(
        tenant_id=tenant_id,
        offer_id=offer_id,
        edition_id=edition_id,
        shared_across_editions=shared,
        name=name,
        type=AssetType.FLYER,
        source=AssetSource.EXTERNAL,
        status=AssetStatus.READY,
        file_url=f"https://cdn/{name}.png",
    )


# ------------------------------------------------------------------------ tests


class TestCloneEditionLiteral:
    def test_creates_draft_private_clone_with_provenance(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        source = _seed_source_edition(db, tenant_a, offer_id)

        svc = EditionCloneService(db, landing_clone=FakeLandingClonePort())
        result = svc.clone_edition(
            source_edition_id=source.id,
            tenant_id=tenant_a,
            strategy=CloneStrategy.LITERAL,
            new_edition_input=LaunchEditionCreate(
                start_date=datetime(2026, 9, 10, 18, 0, tzinfo=timezone.utc),
                edition_name="Edición Setiembre",
            ),
        )

        assert result.edition.cloned_from_edition_id == source.id
        assert result.edition.status.value == "draft"
        assert result.edition.visibility.value == "private"
        assert result.edition.edition_number == source.edition_number + 1
        assert result.edition.start_date.month == 9
        # Defaults survive — pricing/capacity/location carry over.
        assert result.edition.capacity == 50
        assert result.edition.location_override == {"city": "Lima"}
        assert result.edition.pricing_override is not None

    def test_no_landing_no_landing_call(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        """When source edition has no landing, clone succeeds without invoking the port."""
        offer_id = _make_offer(db, tenant_a)
        source = _seed_source_edition(db, tenant_a, offer_id)
        fake_port = FakeLandingClonePort()  # no seeds — source has no landing

        svc = EditionCloneService(db, landing_clone=fake_port)
        result = svc.clone_edition(
            source_edition_id=source.id,
            tenant_id=tenant_a,
            strategy=CloneStrategy.LITERAL,
            new_edition_input=LaunchEditionCreate(
                start_date=datetime(2026, 10, 1, 18, 0, tzinfo=timezone.utc),
            ),
        )

        assert result.landing is None
        assert fake_port.calls == []


class TestCloneEditionLandingStrategies:
    def test_date_replace_passes_substitutions_to_port(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        source = _seed_source_edition(db, tenant_a, offer_id)

        fake_port = FakeLandingClonePort(
            seed={
                (tenant_a, offer_id, source.id): LandingRef(
                    id=uuid.uuid4(),
                    slug="masterclass",
                ),
            },
        )
        svc = EditionCloneService(db, landing_clone=fake_port)

        target_start = datetime(2026, 11, 20, 10, 0, tzinfo=timezone.utc)
        result = svc.clone_edition(
            source_edition_id=source.id,
            tenant_id=tenant_a,
            strategy=CloneStrategy.DATE_REPLACE,
            new_edition_input=LaunchEditionCreate(
                start_date=target_start,
                location_override={"city": "Arequipa", "venue": "Cerro Colorado"},
            ),
        )

        assert len(fake_port.calls) == 1
        call = fake_port.calls[0]
        assert call.strategy == "date_replace"
        assert call.substitutions == {
            "start_date": "2026-11-20",
            "location": "Cerro Colorado",
        }
        # Landing ref is echoed in the result.
        assert result.landing is not None
        assert result.landing.slug == "masterclass-ed2"

    def test_literal_strategy_sends_no_substitutions(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        source = _seed_source_edition(db, tenant_a, offer_id)

        fake_port = FakeLandingClonePort(
            seed={
                (tenant_a, offer_id, source.id): LandingRef(
                    id=uuid.uuid4(),
                    slug="evento-lima",
                ),
            },
        )
        svc = EditionCloneService(db, landing_clone=fake_port)

        svc.clone_edition(
            source_edition_id=source.id,
            tenant_id=tenant_a,
            strategy=CloneStrategy.LITERAL,
            new_edition_input=LaunchEditionCreate(
                start_date=datetime(2027, 1, 5, 9, 0, tzinfo=timezone.utc),
            ),
        )

        assert fake_port.calls[0].strategy == "literal"
        assert fake_port.calls[0].substitutions is None

    def test_ai_regen_forwards_changes_brief(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        source = _seed_source_edition(db, tenant_a, offer_id)

        fake_port = FakeLandingClonePort(
            seed={
                (tenant_a, offer_id, source.id): LandingRef(
                    id=uuid.uuid4(),
                    slug="my-page",
                ),
            },
        )
        svc = EditionCloneService(db, landing_clone=fake_port)

        attachment = uuid.uuid4()
        svc.clone_edition(
            source_edition_id=source.id,
            tenant_id=tenant_a,
            strategy=CloneStrategy.AI_REGEN,
            new_edition_input=LaunchEditionCreate(
                start_date=datetime(2027, 2, 1, 9, 0, tzinfo=timezone.utc),
            ),
            changes_brief="Virar narrativa a público corporativo",
            attachment_ids=[attachment],
        )

        call = fake_port.calls[0]
        assert call.strategy == "ai_regen"
        assert call.regeneration_context == {
            "changes_brief": "Virar narrativa a público corporativo",
            "attachment_ids": [str(attachment)],
        }


class TestCloneEditionAssets:
    def test_edition_scoped_assets_are_duplicated(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        source = _seed_source_edition(db, tenant_a, offer_id)

        asset_repo = OfferAssetRepository(db)
        asset_repo.create(
            _make_asset(tenant_a, offer_id, name="scoped_a", edition_id=source.id),
        )
        asset_repo.create(
            _make_asset(tenant_a, offer_id, name="scoped_b", edition_id=source.id),
        )

        svc = EditionCloneService(db, landing_clone=FakeLandingClonePort())
        result = svc.clone_edition(
            source_edition_id=source.id,
            tenant_id=tenant_a,
            strategy=CloneStrategy.LITERAL,
            new_edition_input=LaunchEditionCreate(
                start_date=datetime(2026, 12, 1, 9, 0, tzinfo=timezone.utc),
            ),
        )

        assert len(result.asset_ids) == 2
        new_assets, _ = asset_repo.list(
            tenant_a,
            offer_id,
            edition_id=result.edition.id,
        )
        assert {a.name for a in new_assets} == {"scoped_a", "scoped_b"}
        # Clones must be distinct rows.
        source_ids = {a.id for a in asset_repo.list(tenant_a, offer_id, edition_id=source.id)[0]}
        assert source_ids.isdisjoint({a.id for a in new_assets})

    def test_shared_assets_not_duplicated(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        """Shared-across-editions assets are already visible in every edition —
        duplicating them would create divergent copies of the same template."""
        offer_id = _make_offer(db, tenant_a)
        source = _seed_source_edition(db, tenant_a, offer_id)

        asset_repo = OfferAssetRepository(db)
        asset_repo.create(
            _make_asset(
                tenant_a,
                offer_id,
                name="shared_template",
                edition_id=source.id,
                shared=True,
            ),
        )

        svc = EditionCloneService(db, landing_clone=FakeLandingClonePort())
        result = svc.clone_edition(
            source_edition_id=source.id,
            tenant_id=tenant_a,
            strategy=CloneStrategy.LITERAL,
            new_edition_input=LaunchEditionCreate(
                start_date=datetime(2027, 3, 1, 9, 0, tzinfo=timezone.utc),
            ),
        )

        assert result.asset_ids == ()


class TestCloneEditionErrors:
    def test_unknown_source_raises_value_error(
        self,
        db: Session,
        tenant_a: uuid.UUID,
    ):
        svc = EditionCloneService(db, landing_clone=FakeLandingClonePort())
        with pytest.raises(ValueError, match="not found"):
            svc.clone_edition(
                source_edition_id=uuid.uuid4(),
                tenant_id=tenant_a,
                strategy=CloneStrategy.LITERAL,
                new_edition_input=LaunchEditionCreate(
                    start_date=datetime(2027, 1, 1, 9, 0, tzinfo=timezone.utc),
                ),
            )

    def test_cross_tenant_source_is_invisible(
        self,
        db: Session,
        tenant_a: uuid.UUID,
        tenant_b: uuid.UUID,
    ):
        offer_id = _make_offer(db, tenant_a)
        source = _seed_source_edition(db, tenant_a, offer_id)

        svc = EditionCloneService(db, landing_clone=FakeLandingClonePort())
        with pytest.raises(ValueError, match="not found"):
            svc.clone_edition(
                source_edition_id=source.id,
                tenant_id=tenant_b,
                strategy=CloneStrategy.LITERAL,
                new_edition_input=LaunchEditionCreate(
                    start_date=datetime(2027, 1, 1, 9, 0, tzinfo=timezone.utc),
                ),
            )


class TestSlugDerivation:
    def test_strips_previous_edition_marker(self) -> None:
        assert EditionCloneService._new_slug("masterclass-ed3", 4) == "masterclass-ed4"

    def test_appends_marker_when_missing(self) -> None:
        assert EditionCloneService._new_slug("masterclass", 2) == "masterclass-ed2"

    def test_preserves_trailing_word_when_not_numeric_suffix(self) -> None:
        assert EditionCloneService._new_slug("masterclass-edicion", 2) == "masterclass-edicion-ed2"
