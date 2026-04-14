"""PersonalityService — orchestrates preset selection, dimension updates, and anchor cleanup."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID  # noqa: TC003 — UUID used in runtime signatures, not type-checking only

import structlog

from src.modules.brand.domain.personality import (
    _NEGATIVE_THRESHOLD,
    PERSONALITY_PRESETS,
    DimensionContract,
    LinguisticPatterns,
    PersonalityCompiler,
    PersonalityDimensions,
    SampleExchange,
)
from src.modules.brand.infrastructure.repositories.personality_repository import (
    PersonalityProfileRepository,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

    from src.modules.brand.infrastructure.models.personality_model import (
        PersonalityProfileModel,
    )
    from src.modules.brand.infrastructure.qdrant.style_anchor_store import StyleAnchorStore

logger = structlog.get_logger()


def _collect_negative_constraints(dimensions: PersonalityDimensions) -> list[str]:
    """Collect all negative constraint strings for dimensions below the negative threshold.

    Helper that iterates all 6 dimensions and collects the ``negative_constraints``
    from any level whose numeric value falls below ``_NEGATIVE_THRESHOLD``.
    """
    dim_items = [
        ("energy", dimensions.energy),
        ("warmth", dimensions.warmth),
        ("humor", dimensions.humor),
        ("expressiveness", dimensions.expressiveness),
        ("narrative", dimensions.narrative),
        ("verbosity", dimensions.verbosity),
    ]
    all_negatives: list[str] = []
    for dim_name, value in dim_items:
        if value < _NEGATIVE_THRESHOLD:
            level = DimensionContract.resolve(dim_name, value)
            all_negatives.extend(level.negative_constraints)
    return all_negatives


class PersonalityService:
    """Orchestrates the two main PersonalityProfile flows.

    1. **Preset selection** — select one of the 6 built-in presets, compile its
       ``system_instruction``, persist it, and activate it for the tenant.
    2. **Dimension update** — patch the numeric sliders and recompile the instruction.
    3. **Delete with anchors** — soft-delete the profile and clean up Qdrant vectors.

    Qdrant integration is optional: pass ``qdrant_client`` and ``embedding_fn`` to
    enable anchor management.  If omitted, the service operates without Qdrant.
    """

    def __init__(
        self,
        db: Session,
        qdrant_client: object | None = None,
        embedding_fn: object | None = None,
    ) -> None:
        """Initialise with a SQLAlchemy session and optional Qdrant wiring."""
        self.db = db
        self.repo = PersonalityProfileRepository(db)
        self._style_store: StyleAnchorStore | None = None

        if qdrant_client is not None:
            from src.modules.brand.infrastructure.qdrant.style_anchor_store import (
                StyleAnchorStore,
            )

            self._style_store = StyleAnchorStore(qdrant_client, embedding_fn)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def select_preset(
        self,
        tenant_id: UUID,
        preset_key: str,
    ) -> PersonalityProfileModel:
        """Select a preset and create an active PersonalityProfile for the tenant.

        Parameters
        ----------
        tenant_id:
            The tenant to create the profile for.
        preset_key:
            One of the keys in ``PERSONALITY_PRESETS`` (e.g. ``"warm_close"``).

        Returns:
        -------
        PersonalityProfileModel
            The newly created and activated profile.

        Raises:
        ------
        ValueError
            If ``preset_key`` is not a recognised preset.
        """
        preset = PERSONALITY_PRESETS.get(preset_key)
        if preset is None:
            msg = f"Unknown preset: '{preset_key}'. Available: {list(PERSONALITY_PRESETS)}"
            raise ValueError(msg)

        # Compile system_instruction from the preset's 3 pillars
        negative_constraints = _collect_negative_constraints(preset.dimensions)
        system_instruction = PersonalityCompiler.compile(
            preset.dimensions,
            preset.linguistic_patterns,
            preset.sample_exchanges,
        )

        # Persist
        profile = self.repo.create(
            tenant_id=tenant_id,
            name=preset.name,
            profile_type="preset",
            preset_key=preset_key,
            dimensions=preset.dimensions.model_dump(),
            linguistic_patterns=preset.linguistic_patterns.model_dump(),
            sample_exchanges=[e.model_dump() for e in preset.sample_exchanges],
            negative_constraints=negative_constraints,
            system_instruction=system_instruction,
        )

        # Activate (deactivates all other global profiles for this tenant)
        self.repo.activate(profile.id, tenant_id=tenant_id)

        logger.info(
            "personality_service.preset_selected",
            tenant_id=str(tenant_id),
            preset_key=preset_key,
            profile_id=str(profile.id),
        )

        # Reload to reflect is_active=True set by activate()
        refreshed = self.repo.get_by_id(profile.id, tenant_id=tenant_id)
        return refreshed or profile

    def get_active(self, tenant_id: UUID) -> PersonalityProfileModel | None:
        """Return the currently active global profile for the tenant, or None.

        Parameters
        ----------
        tenant_id:
            The tenant to query.
        """
        return self.repo.get_active(tenant_id=tenant_id)

    def update_dimensions(
        self,
        profile_id: UUID,
        tenant_id: UUID,
        new_dimensions: dict,
    ) -> PersonalityProfileModel | None:
        """Update the numeric dimension sliders and recompile ``system_instruction``.

        Reads the existing ``linguistic_patterns`` and ``sample_exchanges`` from
        the DB profile so Block 2 and Block 4 stay consistent with the stored data.

        Parameters
        ----------
        profile_id:
            ID of the profile to update.
        tenant_id:
            Owning tenant — used for isolation.
        new_dimensions:
            Dict with all 6 dimension keys (energy, warmth, humor, expressiveness,
            narrative, verbosity), each as a float in [0.0, 1.0].

        Returns:
        -------
        PersonalityProfileModel | None
            Updated model, or ``None`` if not found / wrong tenant.
        """
        profile = self.repo.get_by_id(profile_id, tenant_id=tenant_id)
        if profile is None:
            return None

        dims = PersonalityDimensions(**new_dimensions)
        patterns = LinguisticPatterns(**profile.linguistic_patterns)
        exchanges = [SampleExchange(**e) for e in (profile.sample_exchanges or [])]

        negative_constraints = _collect_negative_constraints(dims)
        system_instruction = PersonalityCompiler.compile(dims, patterns, exchanges)

        updated = self.repo.update_dimensions(
            profile_id,
            tenant_id=tenant_id,
            dimensions=new_dimensions,
            negative_constraints=negative_constraints,
            system_instruction=system_instruction,
        )

        logger.info(
            "personality_service.dimensions_updated",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
        )
        return updated

    async def delete_with_anchors(
        self,
        profile_id: UUID,
        tenant_id: UUID,
    ) -> bool:
        """Soft-delete profile and clean up Qdrant style anchors.

        Qdrant cleanup is best-effort: failures are logged but do not propagate
        so the DB record is always soft-deleted regardless of vector store state.

        Parameters
        ----------
        profile_id:
            ID of the profile to delete.
        tenant_id:
            Owning tenant — used for isolation.

        Returns:
        -------
        bool
            ``True`` if the profile was found and soft-deleted, ``False`` otherwise.
        """
        if self._style_store is not None:
            try:
                await self._style_store.delete_by_profile(tenant_id, profile_id)
            except Exception:
                logger.exception(
                    "personality_service.anchor_cleanup_failed",
                    tenant_id=str(tenant_id),
                    profile_id=str(profile_id),
                )

        result = self.repo.soft_delete(profile_id, tenant_id=tenant_id)
        logger.info(
            "personality_service.deleted_with_anchors",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
            deleted=result,
        )
        return result
