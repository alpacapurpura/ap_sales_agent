"""Edition clone service — creates edition N+1 from edition N (Phase 3).

The clone is a single transactional operation that fans out across three
aggregates:

1. ``LaunchEdition`` — a new DRAFT + PRIVATE row, stamped with
   ``cloned_from_edition_id`` so the UI can show provenance and the user
   can diff against the source.
2. ``LandingPage`` — via :class:`IEditionLandingClonePort` (the landing
   module owns the aggregate; we reach it through the port).
3. ``OfferAsset`` — every asset bound to the source edition is duplicated
   and re-bound to the new edition. Assets flagged
   ``shared_across_editions=True`` are NOT duplicated; the single row
   continues to be visible from every edition listing.

The orchestrating service owns the transaction boundary: it calls
``db.commit()`` once, after all sub-steps succeed. Individual collaborators
(asset repo, landing adapter, edition repo) use ``db.flush()`` only so a
failure anywhere rolls the whole clone back.

Strategy semantics are documented on :class:`CloneStrategy`.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from src.modules.offer.application.ports import IEditionLandingClonePort, LandingRef
from src.modules.offer.domain.launch_edition import (
    EditionStatus,
    EditionVisibility,
    LaunchEdition,
)
from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from src.modules.offer.infrastructure.repositories.offer_asset_repository import (
    OfferAssetRepository,
)
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

    from src.modules.offer.domain.assets import OfferAsset
    from src.modules.offer.domain.launch_edition import LaunchEditionCreate


class CloneStrategy(StrEnum):
    """How an edition's landing content should be derived from its source.

    ``LITERAL``
        Deep copy, no content changes. Use when the new edition re-runs
        the old one verbatim (e.g. reprise of a sold-out cohort).
    ``DATE_REPLACE``
        Deep copy + allowlisted token substitution (``{{start_date}}``,
        ``{{end_date}}``, ``{{location}}``). The standard case when only
        dates/location change between editions.
    ``AI_REGEN``
        Deep copy, stamped for async regeneration. The clone completes
        synchronously with the source content; the landing module's
        regeneration worker rewrites blocks based on
        ``regeneration_context``. Keeps the clone transaction short and
        the IA call off the request path.
    """

    LITERAL = "literal"
    DATE_REPLACE = "date_replace"
    AI_REGEN = "ai_regen"


@dataclass(frozen=True, slots=True)
class EditionCloneResult:
    """Return value of :meth:`EditionCloneService.clone_edition`."""

    edition: LaunchEdition
    landing: LandingRef | None
    asset_ids: tuple["UUID", ...]


class EditionCloneService:
    """Orchestrates cloning an edition + its landing + its assets."""

    def __init__(
        self,
        db: Session,
        *,
        landing_clone: IEditionLandingClonePort,
    ) -> None:
        """Bind collaborators to the active SA session.

        Repositories and the landing-clone adapter share the same
        session so the entire clone is one transaction.
        """
        self.db = db
        self.edition_repo = LaunchEditionRepository(db)
        self.offer_repo = OfferRepository(db)
        self.asset_repo = OfferAssetRepository(db)
        self.landing_clone = landing_clone

    def clone_edition(
        self,
        source_edition_id: UUID,
        tenant_id: UUID,
        *,
        strategy: CloneStrategy,
        new_edition_input: LaunchEditionCreate,
        changes_brief: str | None = None,
        attachment_ids: list[UUID] | None = None,
    ) -> EditionCloneResult:
        """Clone ``source_edition_id`` into a new DRAFT edition.

        On any failure the transaction rolls back; callers see a fresh
        exception and no partial state. Returns a result bundle with the
        new edition, the new landing (if any), and the ids of newly
        created edition-scoped assets.
        """
        source = self._require_source(source_edition_id, tenant_id)

        try:
            new_edition = self._clone_edition_row(source, tenant_id, new_edition_input)
            new_landing = self._maybe_clone_landing(
                source_edition=source,
                new_edition=new_edition,
                tenant_id=tenant_id,
                strategy=strategy,
                changes_brief=changes_brief,
                attachment_ids=attachment_ids,
            )
            cloned_asset_ids = self._clone_assets(
                source_edition_id=source.id,
                new_edition_id=new_edition.id,
                tenant_id=tenant_id,
                offer_id=source.offer_id,
            )
        except Exception:
            self.db.rollback()
            raise

        self.db.commit()
        return EditionCloneResult(
            edition=new_edition,
            landing=new_landing,
            asset_ids=tuple(cloned_asset_ids),
        )

    # -------------------------------------------------------------- internals

    def _require_source(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition:
        source = self.edition_repo.get_by_id(edition_id, tenant_id)
        if source is None:
            msg = f"Edition {edition_id} not found"
            raise ValueError(msg)
        return source

    def _clone_edition_row(
        self,
        source: LaunchEdition,
        tenant_id: UUID,
        new_input: LaunchEditionCreate,
    ) -> LaunchEdition:
        """Create the new edition with new dates/location, status DRAFT+PRIVATE.

        Pricing, capacity, and notes default to the source's values when
        the caller didn't override them. Clones are never born public.
        """
        pricing = new_input.pricing_override if new_input.pricing_override is not None else source.pricing_override
        capacity = new_input.capacity if new_input.capacity is not None else source.capacity
        location = new_input.location_override if new_input.location_override is not None else source.location_override
        notes = new_input.notes if new_input.notes is not None else source.notes

        return self.edition_repo.create(
            offer_id=source.offer_id,
            tenant_id=tenant_id,
            variant_structure=source.variant_structure,
            structure_data=dict(source.structure_data),
            sort_rank=source.sort_rank,
            edition_name=new_input.edition_name,
            start_date=new_input.start_date,
            end_date=new_input.end_date,
            registration_start=new_input.registration_start,
            registration_end=new_input.registration_end,
            timezone=new_input.timezone or source.timezone,
            pricing_override=pricing,
            capacity=capacity,
            location_override=location,
            notes=notes,
            status=EditionStatus.DRAFT,
            visibility=EditionVisibility.PRIVATE,
            cloned_from_edition_id=source.id,
        )

    def _maybe_clone_landing(
        self,
        *,
        source_edition: LaunchEdition,
        new_edition: LaunchEdition,
        tenant_id: UUID,
        strategy: CloneStrategy,
        changes_brief: str | None,
        attachment_ids: list[UUID] | None,
    ) -> LandingRef | None:
        """Clone the source edition's landing, if any. No-op otherwise."""
        source_landing = self.landing_clone.get_for_edition(
            tenant_id=tenant_id,
            offer_id=source_edition.offer_id,
            edition_id=source_edition.id,
        )
        if source_landing is None:
            return None

        substitutions = self._build_substitutions(new_edition) if strategy == CloneStrategy.DATE_REPLACE else None
        regeneration_context = self._build_regen_context(changes_brief, attachment_ids)

        return self.landing_clone.clone_to_edition(
            tenant_id=tenant_id,
            offer_id=new_edition.offer_id,
            source_landing_id=source_landing.id,
            target_edition_id=new_edition.id,
            target_slug=self._new_slug(source_landing.slug, new_edition.edition_number),
            strategy=strategy.value,
            substitutions=substitutions,
            regeneration_context=regeneration_context,
        )

    def _clone_assets(
        self,
        *,
        source_edition_id: UUID,
        new_edition_id: UUID,
        tenant_id: UUID,
        offer_id: UUID,
    ) -> list[UUID]:
        """Duplicate every edition-scoped asset; rebind clones to new edition.

        Shared-across-editions assets are already visible in the new
        edition's listing (they match the ``shared=True`` filter), so we
        intentionally do NOT duplicate them — duplication would create
        two rows that can diverge silently.
        """
        # Listing with a sentinel UUID we'll never match is the cheapest
        # way to reuse the repo. We filter manually below to keep the
        # repo contract untouched.
        source_assets, _ = self.asset_repo.list(
            tenant_id=tenant_id,
            offer_id=offer_id,
            edition_id=source_edition_id,
            limit=1000,
        )
        cloned_ids: list[UUID] = []
        for source_asset in source_assets:
            if not source_asset.is_edition_scoped:
                # Shared assets belong to every edition already.
                continue
            clone = self._clone_asset(source_asset, new_edition_id=new_edition_id)
            cloned = self.asset_repo.create(clone)
            cloned_ids.append(cloned.id)
        return cloned_ids

    @staticmethod
    def _clone_asset(source: OfferAsset, *, new_edition_id: UUID) -> OfferAsset:
        from uuid import uuid4

        from src.modules.offer.domain.assets import OfferAsset

        return OfferAsset(
            id=uuid4(),
            tenant_id=source.tenant_id,
            offer_id=source.offer_id,
            edition_id=new_edition_id,
            shared_across_editions=False,
            name=source.name,
            type=source.type,
            source=source.source,
            status=source.status,
            file_url=source.file_url,
            thumbnail_url=source.thumbnail_url,
            mime_type=source.mime_type,
            size_bytes=source.size_bytes,
            metadata=dict(source.metadata),
            prompt_params=dict(source.prompt_params) if source.prompt_params else None,
            editable_in_puck=source.editable_in_puck,
        )

    @staticmethod
    def _build_substitutions(edition: LaunchEdition) -> dict[str, str]:
        """Render the three allowlisted tokens from edition fields.

        Missing values fall back to an empty string so partial editions
        still produce a useful diff rather than exploding; copilot /
        wizard validation blocks publishing of tokenless editions.
        """
        subs: dict[str, str] = {}
        if edition.start_date is not None:
            subs["start_date"] = edition.start_date.date().isoformat()
        if edition.end_date is not None:
            subs["end_date"] = edition.end_date.date().isoformat()
        if edition.location_override:
            # Location comes in as a dict ({city, country, venue, ...}).
            # Prefer a concrete "name" or "venue" field, falling back to
            # a compact JSON dump so the user sees *something* while the
            # template is being hand-polished.
            subs["location"] = _format_location(edition.location_override)
        return subs

    @staticmethod
    def _build_regen_context(
        changes_brief: str | None,
        attachment_ids: list[UUID] | None,
    ) -> dict[str, Any] | None:
        if not changes_brief and not attachment_ids:
            return None
        context: dict[str, Any] = {}
        if changes_brief:
            context["changes_brief"] = changes_brief
        if attachment_ids:
            context["attachment_ids"] = [str(a) for a in attachment_ids]
        return context

    @staticmethod
    def _new_slug(source_slug: str, edition_number: int) -> str:
        """Derive a unique slug for the cloned landing.

        Appends ``-edN`` while avoiding double suffixes when cloning a
        clone. Slugs are unique per tenant (DB partial unique index), so
        this is the last line of defence before an integrity error.
        """
        marker = f"-ed{edition_number}"
        base = source_slug
        # Strip a prior ``-edK`` suffix so "masterclass-ed3" → "masterclass-ed4"
        # instead of "masterclass-ed3-ed4".
        if "-ed" in base:
            head, sep, tail = base.rpartition("-ed")
            if sep and tail.isdigit():
                base = head
        return f"{base}{marker}"


def _format_location(location: dict[str, Any]) -> str:
    """Render a location dict as a short human-readable string.

    Prefers the most specific user-set label; falls back to joining all
    set values so we never emit an empty token.
    """
    for key in ("name", "venue", "address", "city"):
        value = location.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    parts = [str(v).strip() for v in location.values() if isinstance(v, str) and str(v).strip()]
    return ", ".join(parts)


__all__ = ["CloneStrategy", "EditionCloneResult", "EditionCloneService"]
