"""Cross-module adapter: clones landings for the offer clone service.

Implements ``IEditionLandingClonePort`` (declared in
``src.modules.offer.application.ports``) so that the offer module's
``EditionCloneService`` never reaches into landing internals directly.

Design choices:

- The adapter operates on the raw ``LandingPageModel`` row because the
  ``LandingPage`` domain entity insists on a strictly-typed
  ``LandingPageConfig`` (including slug consistency), whereas cloning
  needs to copy arbitrary Puck JSON untouched.
- Writes use ``db.flush()`` — never ``db.commit()`` — so the caller owns
  the transaction boundary. A full clone (new edition + landing +
  assets) must succeed or roll back as one.
- ``ai_regen`` currently behaves the same as ``literal`` at the DB level
  but stamps ``generation_job_status='queued_ai_regen'`` so a landing
  worker can pick it up out of band. The copy itself isn't rewritten
  synchronously — Phase 7 wires the copilot-driven regen tool.
"""

from __future__ import annotations

import copy
import uuid
from typing import TYPE_CHECKING, Any

from luana_core_landing.application.tokenizer import substitute_tokens
from luana_core_landing.infrastructure.models.landing_model import LandingPageModel
from luana_core_platform.links.ports.edition_landing_clone import (
    IEditionLandingClonePort,
    LandingRef,
)
from sqlalchemy import select

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session


class LandingEditionCloneAdapter(IEditionLandingClonePort):
    """SQLAlchemy-backed implementation of :class:`IEditionLandingClonePort`."""

    STRATEGY_LITERAL = "literal"
    STRATEGY_DATE_REPLACE = "date_replace"
    STRATEGY_AI_REGEN = "ai_regen"

    def __init__(self, db: Session) -> None:
        """Bind to the active SQLAlchemy session for flush-only writes."""
        self.db = db

    def get_for_edition(
        self,
        tenant_id: UUID,
        offer_id: UUID,
        edition_id: UUID | None,
    ) -> LandingRef | None:
        """Return the landing bound to ``(offer, edition)`` or ``None``."""
        stmt = select(LandingPageModel).where(
            LandingPageModel.tenant_id == tenant_id,
            LandingPageModel.offer_id == offer_id,
            LandingPageModel.deleted_at.is_(None),
        )
        if edition_id is None:
            stmt = stmt.where(LandingPageModel.edition_id.is_(None))
        else:
            stmt = stmt.where(LandingPageModel.edition_id == edition_id)
        model = self.db.execute(stmt).scalars().first()
        if model is None:
            return None
        return LandingRef(id=model.id, slug=model.slug, is_published=bool(model.is_published))

    def clone_to_edition(
        self,
        *,
        tenant_id: UUID,
        offer_id: UUID,
        source_landing_id: UUID,
        target_edition_id: UUID,
        target_slug: str,
        strategy: str,
        substitutions: dict[str, str] | None = None,
        regeneration_context: dict[str, Any] | None = None,
    ) -> LandingRef:
        """See port docstring."""
        source = self._require_source(source_landing_id, tenant_id)
        new_config = self._build_cloned_config(
            source_config=source.config or {},
            target_slug=target_slug,
            strategy=strategy,
            substitutions=substitutions,
        )

        new_model = LandingPageModel(
            id=uuid.uuid4(),
            tenant_id=tenant_id,
            offer_id=offer_id,
            edition_id=target_edition_id,
            slug=target_slug,
            config=new_config,
            is_published=False,
        )
        if strategy == self.STRATEGY_AI_REGEN:
            # Leave a breadcrumb for the landing-generation worker.
            # Actual content rewrites happen asynchronously.
            new_model.generation_job_status = "queued_ai_regen"
            if regeneration_context:
                new_model.generation_error = None  # reset prior error if any

        self.db.add(new_model)
        self.db.flush()
        return LandingRef(id=new_model.id, slug=new_model.slug, is_published=False)

    # -------------------------------------------------------------- internals

    def _require_source(self, source_landing_id: UUID, tenant_id: UUID) -> LandingPageModel:
        stmt = select(LandingPageModel).where(
            LandingPageModel.id == source_landing_id,
            LandingPageModel.tenant_id == tenant_id,
            LandingPageModel.deleted_at.is_(None),
        )
        source = self.db.execute(stmt).scalars().first()
        if source is None:
            msg = f"Source landing {source_landing_id} not found for tenant {tenant_id}"
            raise ValueError(msg)
        return source

    def _build_cloned_config(
        self,
        *,
        source_config: dict[str, Any],
        target_slug: str,
        strategy: str,
        substitutions: dict[str, str] | None,
    ) -> dict[str, Any]:
        new_config = copy.deepcopy(source_config)
        if strategy == self.STRATEGY_DATE_REPLACE and substitutions:
            new_config = substitute_tokens(new_config, substitutions)
        # LandingPageConfig carries its own slug inside the JSONB blob; keep
        # it in sync with the model-level slug so consumers don't see two
        # names for the same page.
        if isinstance(new_config, dict):
            new_config["slug"] = target_slug
            # Freshly cloned landings never start "published".
            new_config["is_published"] = False
        return new_config


__all__ = ["LandingEditionCloneAdapter"]
