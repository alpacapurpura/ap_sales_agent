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
    find_nearest_preset,
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

# Module-level import of personality_app so tests can patch it at this path:
# src.modules.brand.application.services.personality_service.personality_app
# The import is deferred via a try/except to allow unit tests without LangGraph.
try:
    from src.modules.brand.application.agents.style_analyzer.graph import (
        personality_app,
    )
except Exception:  # noqa: BLE001
    personality_app = None  # type: ignore[assignment]

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

    def activate(
        self,
        *,
        profile_id: UUID,
        tenant_id: UUID,
    ) -> PersonalityProfileModel | None:
        """Activate a pre-existing profile. Idempotent: if already active, returns unchanged.

        Deactivates any currently active global profile for the tenant in the same
        transaction. Returns None if profile not found or belongs to a different tenant.

        Parameters
        ----------
        profile_id:
            ID of the profile to activate.
        tenant_id:
            Owning tenant — used for isolation.
        """
        profile = self.repo.get_by_id(profile_id, tenant_id=tenant_id)
        if profile is None:
            return None

        if profile.is_active:
            # Already active — idempotent, return as-is
            logger.info(
                "personality_service.activate_idempotent",
                tenant_id=str(tenant_id),
                profile_id=str(profile_id),
            )
            return profile

        self.repo.activate(profile_id, tenant_id=tenant_id)
        logger.info(
            "personality_service.activated",
            tenant_id=str(tenant_id),
            profile_id=str(profile_id),
        )
        refreshed = self.repo.get_by_id(profile_id, tenant_id=tenant_id)
        return refreshed or profile

    async def clone_from_material(
        self,
        *,
        tenant_id: UUID,
        text_input: str | None,
        file_bytes: bytes | None,
        file_name: str | None,
        user_name: str | None,
    ) -> PersonalityProfileModel:
        """Run the personality_app LangGraph pipeline, persist the resulting profile.

        The profile is created with ``is_active=False``. The caller invokes
        ``activate()`` once the user approves the preview.

        Parameters
        ----------
        tenant_id:
            The owning tenant.
        text_input:
            Raw chat text (mutually exclusive with file_bytes).
        file_bytes:
            Raw bytes of an uploaded file (mutually exclusive with text_input).
        file_name:
            Original file name (used for validation).
        user_name:
            Label for the resulting profile (optional).

        Raises:
        ------
        ValueError
            If both inputs are None, both are provided, or fewer than 10 messages found.
        RuntimeError
            If the LangGraph pipeline fails irrecoverably.
        """
        # --- Input validation ---
        if text_input is not None and file_bytes is not None:
            msg = "Envía texto O archivo, no ambos."
            raise ValueError(msg)

        if text_input is None and file_bytes is None:
            msg = "Debes proporcionar text_input o file_bytes para clonar tu estilo."
            raise ValueError(msg)

        # Resolve raw text (from input or file). file_bytes is non-None here
        # because the guard above raises when both are None.
        raw_text = (
            text_input if text_input is not None else file_bytes.decode("utf-8", errors="replace")  # type: ignore[union-attr]
        )

        # Validate minimum message count (non-empty lines)
        lines = [ln for ln in raw_text.splitlines() if ln.strip()]
        if len(lines) < 10:
            msg = "Necesitas pegar al menos 10 mensajes para clonar tu estilo."
            raise ValueError(msg)

        # --- Run pipeline ---
        # Uses the module-level personality_app (patchable in tests).
        # At this point personality_app is guaranteed to be imported or test-patched.
        state = {
            "user_id": str(tenant_id),
            "raw_input": raw_text,
            "target_url": None,
            "cleaned_input": None,
            "style_profile": None,
            "research_summary": None,
            "offer_context": None,
            "system_instruction": None,
            "simulation_examples": [],
            "error": None,
            "parsed_messages": [],
            "personality_dimensions": {},
            "personality_linguistic_patterns": {},
            "personality_sample_exchanges": [],
            "personality_confidence": 0.0,
            "personality_profile_id": "",
            "anchor_count": 0,
        }

        logger.info("personality_service.clone_start", tenant_id=str(tenant_id))
        result_state = await personality_app.ainvoke(state)

        if result_state.get("error") or not result_state.get("personality_dimensions"):
            error_detail = result_state.get("error", "Pipeline returned no results")
            logger.error(
                "personality_service.clone_pipeline_failed",
                tenant_id=str(tenant_id),
                error=error_detail,
            )
            msg = "No pudimos analizar tu material. Intenta nuevamente en unos minutos."
            raise RuntimeError(msg)

        # --- Build domain objects ---
        dims_data = result_state["personality_dimensions"]
        patterns_data = result_state.get("personality_linguistic_patterns", {})
        exchanges_data = result_state.get("personality_sample_exchanges", [])
        confidence = float(result_state.get("personality_confidence", 0.0))

        dims = PersonalityDimensions(
            energy=float(dims_data.get("energy", 0.5)),
            warmth=float(dims_data.get("warmth", 0.5)),
            humor=float(dims_data.get("humor", 0.5)),
            expressiveness=float(dims_data.get("expressiveness", 0.5)),
            narrative=float(dims_data.get("narrative", 0.5)),
            verbosity=float(dims_data.get("verbosity", 0.5)),
        )
        patterns = LinguisticPatterns(
            emoji_style=patterns_data.get("emoji_style", "moderate"),
            favorite_emojis=patterns_data.get("favorite_emojis", []),
            greeting=patterns_data.get("greeting", "Hola"),
            farewell=patterns_data.get("farewell", "Hasta pronto"),
            filler_phrases=patterns_data.get("filler_phrases", []),
            avg_message_length=patterns_data.get("avg_message_length", "medium"),
            punctuation_style=patterns_data.get("punctuation_style", "standard"),
            humor_type=patterns_data.get("humor_type", "none"),
            unique_vocabulary=patterns_data.get("unique_vocabulary", []),
        )
        exchanges = [SampleExchange(**e) for e in exchanges_data if isinstance(e, dict)]
        negative_constraints = _collect_negative_constraints(dims)
        system_instruction = result_state.get("system_instruction") or PersonalityCompiler.compile(
            dims, patterns, exchanges
        )

        profile_name = user_name or "Estilo Clonado"
        source_metadata: dict = {"confidence": confidence}
        if file_name:
            source_metadata["file_name"] = file_name

        profile = self.repo.create(
            tenant_id=tenant_id,
            name=profile_name,
            profile_type="cloned",
            dimensions=dims_data,
            linguistic_patterns=patterns_data,
            sample_exchanges=exchanges_data,
            negative_constraints=negative_constraints,
            system_instruction=system_instruction,
            source_metadata=source_metadata,
        )

        # Upsert Qdrant anchors (best-effort — failure must not break the endpoint)
        if self._style_store is not None:
            try:
                anchor_count = await self._style_store.upsert_exchanges(
                    tenant_id=tenant_id,
                    profile_id=profile.id,
                    exchanges=exchanges_data,
                )
                profile.anchor_count = anchor_count
                self.db.commit()
            except Exception:
                logger.exception(
                    "personality_service.clone_qdrant_failed",
                    tenant_id=str(tenant_id),
                    profile_id=str(profile.id),
                )

        logger.info(
            "personality_service.clone_complete",
            tenant_id=str(tenant_id),
            profile_id=str(profile.id),
            profile_type="cloned",
        )
        return profile

    async def migrate_from_voice_tone(
        self,
        *,
        tenant_id: UUID,
        voice_tone_text: str,
    ) -> tuple[PersonalityProfileModel, str | None, float]:
        """Map a legacy BrandIdentity.voice_tone text to a PersonalityProfile.

        Selects the nearest preset via LLM similarity, creates a profile with
        ``profile_type="migrated_from_voice_tone"``, and auto-activates it.
        Returns (profile, matched_preset_key, confidence).

        Parameters
        ----------
        tenant_id:
            The owning tenant.
        voice_tone_text:
            The raw legacy voice_tone string from BrandIdentity.

        Raises:
        ------
        ValueError
            If voice_tone_text is empty.
        """
        if not voice_tone_text or not voice_tone_text.strip():
            msg = "El texto de voice_tone está vacío. No hay nada que migrar."
            raise ValueError(msg)

        # Build LLM caller using LLMFactory (best-effort, may return None on failure)
        llm_caller = None
        try:
            from src.core.enums import ModelRole
            from src.shared.infrastructure.llm.factory import LLMFactory

            llm_service = LLMFactory.get_service()

            def _call_llm(prompt: str) -> str:
                return llm_service.generate_response(
                    messages=[{"role": "user", "content": prompt}],
                    model_type=ModelRole.FAST,
                    temperature=0.1,
                )

            llm_caller = _call_llm
        except Exception:
            logger.exception("personality_service.migrate_llm_init_failed", tenant_id=str(tenant_id))

        matched_key, confidence = find_nearest_preset(voice_tone_text, llm_caller=llm_caller)

        # Build profile using the matched preset if available; otherwise use defaults
        if matched_key and matched_key in PERSONALITY_PRESETS:
            preset = PERSONALITY_PRESETS[matched_key]
            dims_data = preset.dimensions.model_dump()
            patterns_data = preset.linguistic_patterns.model_dump()
            exchanges_data = [e.model_dump() for e in preset.sample_exchanges]
            dims = preset.dimensions
            patterns = preset.linguistic_patterns
            exchanges = list(preset.sample_exchanges)
        else:
            # Fallback: generic mid-range dimensions
            dims = PersonalityDimensions(
                energy=0.5,
                warmth=0.5,
                humor=0.5,
                expressiveness=0.5,
                narrative=0.5,
                verbosity=0.5,
            )
            patterns = LinguisticPatterns(
                emoji_style="moderate",
                favorite_emojis=[],
                greeting="Hola",
                farewell="Hasta pronto",
                filler_phrases=[],
                avg_message_length="medium",
                punctuation_style="standard",
                humor_type="none",
                unique_vocabulary=[],
            )
            exchanges = []
            dims_data = dims.model_dump()
            patterns_data = patterns.model_dump()
            exchanges_data = []

        negative_constraints = _collect_negative_constraints(dims)
        system_instruction = PersonalityCompiler.compile(dims, patterns, exchanges)

        profile = self.repo.create(
            tenant_id=tenant_id,
            name="Estilo Migrado",
            profile_type="migrated_from_voice_tone",
            preset_key=matched_key,
            dimensions=dims_data,
            linguistic_patterns=patterns_data,
            sample_exchanges=exchanges_data,
            negative_constraints=negative_constraints,
            system_instruction=system_instruction,
            source_metadata={"legacy_text": voice_tone_text},
        )

        # Auto-activate
        self.repo.activate(profile.id, tenant_id=tenant_id)
        refreshed = self.repo.get_by_id(profile.id, tenant_id=tenant_id)

        logger.info(
            "personality_service.migrate_complete",
            tenant_id=str(tenant_id),
            profile_id=str(profile.id),
            matched_key=matched_key,
            confidence=confidence,
        )
        return refreshed or profile, matched_key, confidence
