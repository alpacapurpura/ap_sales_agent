"""Brand Personality Engine API endpoints.

10 REST endpoints for personality profile management.
All endpoints filter by X-Tenant-ID via get_current_user dependency.
All endpoints declare response_model= (PII compliance via Tessl/Maria rule).
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from luana_core_brand_studio.application.services.personality_service import PersonalityService
from luana_core_brand_studio.domain.personality import PERSONALITY_PRESETS
from luana_core_brand_studio.infrastructure.repositories.personality_repository import PersonalityProfileRepository
from luana_core_iam.api.dependencies import get_current_user
from luana_core_iam.domain.user import User
from luana_core_platform.core.database import get_db
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

logger = structlog.get_logger()

router = APIRouter(prefix="/personality", tags=["Brand - Personality"])


# ---------------------------------------------------------------------------
# DTOs
# ---------------------------------------------------------------------------


class PresetSummaryDTO(BaseModel):
    """Summary of a built-in personality preset for the selection UI."""

    key: str
    name: str
    icon: str
    description: str
    sample_message: str  # First SampleExchange.author_response
    dimensions: dict  # {energy: 0.65, warmth: 0.85, ...}


class PersonalityProfileDTO(BaseModel):
    """Full serialization of a PersonalityProfileModel."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    profile_type: str
    preset_key: str | None
    is_active: bool
    dimensions: dict
    linguistic_patterns: dict
    sample_exchanges: list[dict]
    negative_constraints: list[str]
    system_instruction: str | None
    source_metadata: dict
    anchor_count: int
    created_at: datetime
    updated_at: datetime


class SelectPresetRequest(BaseModel):
    """Request body for POST /personality/select-preset."""

    preset_key: str


class UpdateDimensionsRequest(BaseModel):
    """Request body for PUT /personality/{profile_id}/dimensions."""

    dimensions: dict  # {energy: 0.7, warmth: 0.85, ...}


class SimulationDTO(BaseModel):
    """Response for POST /personality/{profile_id}/simulate."""

    responses: list[dict]  # [{context, prospect_message, agent_response}]


class CloneRequest(BaseModel):
    """Body for POST /personality/clone — either text_input OR file (multipart), not both."""

    model_config = ConfigDict(extra="forbid")

    text_input: str | None = None  # min 10 messages (validated server-side)
    user_name: str | None = None  # label for the resulting profile


class ActivateRequest(BaseModel):
    """Body for POST /personality/{id}/activate — empty body, path param only."""

    model_config = ConfigDict(extra="forbid")


class CloneDryRunResponse(BaseModel):
    """Quick parser-only inspection of the material BEFORE running the LLM pipeline.

    Used by the FE to surface a quality gauge ("47 mensajes detectados, cobertura
    en 4 contextos — clon decente") so the user can decide whether to invest the
    2-4 minute LLM analysis or paste more material first. No LLM calls happen
    here — just the format-detect parser + simple keyword bucketing for contexts.
    """

    model_config = ConfigDict(extra="forbid")

    message_count: int  # parsed messages (post format-detect)
    detected_format: str  # whatsapp | instagram | telegram | plain | unsupported
    contexts_detected: dict[str, int]  # {greeting: 5, price: 2, objection: 0, closing: 3, follow_up: 1}
    quality_tier: str  # insufficient | basic | decent | strong
    quality_score: float  # 0.0..1.0 — composite of count + diversity
    recommendation: str  # localized recommendation for the user


class FromVoiceToneResponse(BaseModel):
    """Response for POST /personality/from-voice-tone.

    On success: the newly created migrated profile plus audit context.
    """

    model_config = ConfigDict(extra="forbid")

    profile: PersonalityProfileDTO
    source_voice_tone: str  # the original text that was migrated, for audit
    matched_preset_key: str | None  # nearest preset matched (may be null)
    match_confidence: float  # 0.0..1.0


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _build_service(db: Session) -> PersonalityService:
    """Build PersonalityService without Qdrant (API layer only)."""
    return PersonalityService(db=db)


def _model_to_dto(model: object) -> PersonalityProfileDTO:
    """Convert PersonalityProfileModel to PersonalityProfileDTO."""
    return PersonalityProfileDTO.model_validate(model)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.get("/presets")
async def list_presets(
    current_user: Annotated[User, Depends(get_current_user)],
) -> list[PresetSummaryDTO]:
    """List all 6 built-in personality presets with name, icon, description, and sample message.

    Does not require DB access — presets are defined in domain constants.
    """
    logger.info("personality.list_presets", tenant_id=str(current_user.tenant_id))

    summaries: list[PresetSummaryDTO] = []
    for preset in PERSONALITY_PRESETS.values():
        first_sample = preset.sample_exchanges[0].author_response if preset.sample_exchanges else ""
        summaries.append(
            PresetSummaryDTO(
                key=preset.key,
                name=preset.name,
                icon=preset.icon,
                description=preset.description,
                sample_message=first_sample,
                dimensions=preset.dimensions.model_dump(),
            )
        )
    return summaries


@router.get("/active")
async def get_active_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PersonalityProfileDTO | None:
    """Return the currently active global personality profile for the tenant, or null."""
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    service = _build_service(db)
    model = service.get_active(current_user.tenant_id)

    if model is None:
        return None

    return _model_to_dto(model)


@router.post("/select-preset")
async def select_preset(
    request: SelectPresetRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PersonalityProfileDTO:
    """Select a built-in preset → create + activate a PersonalityProfile for the tenant.

    Deactivates any previously active global profile.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    logger.info(
        "personality.select_preset",
        tenant_id=str(current_user.tenant_id),
        preset_key=request.preset_key,
    )

    try:
        service = _build_service(db)
        model = service.select_preset(
            tenant_id=current_user.tenant_id,
            preset_key=request.preset_key,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return _model_to_dto(model)


@router.post("/clone")
async def clone_from_chat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    text_input: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
    user_name: Annotated[str | None, Form()] = None,
) -> PersonalityProfileDTO:
    """Upload a chat file or paste text → run the Personality Engine pipeline → create a cloned profile.

    Accepts ``text_input`` (Form field) OR ``file`` (UploadFile), not both.
    The resulting profile is created with ``is_active=False``. The user must
    explicitly call ``POST /{profile_id}/activate`` to activate it.

    Validations:
    - At least one of text_input or file must be provided.
    - text_input and file are mutually exclusive.
    - text_input (or file content) must contain at least 10 non-empty messages.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    logger.info(
        "personality.clone_from_chat",
        tenant_id=str(current_user.tenant_id),
        user_name=user_name,
        has_file=file is not None,
        has_text=text_input is not None,
    )

    file_bytes: bytes | None = None
    file_name: str | None = None

    if file is not None:
        # B1: BE accepts the same formats the parser supports —
        # WhatsApp .txt, Instagram DM .json, Telegram .json, plus .csv.
        # The auto-detect parser (infrastructure/parsers/base.py::detect_and_parse)
        # routes by content shape, so we accept text/plain, text/csv,
        # and application/json content-types here.
        allowed_types = {"text/plain", "text/csv", "application/json"}
        allowed_extensions = (".txt", ".csv", ".json")
        content_type = file.content_type or ""
        original_name = file.filename or ""
        if content_type not in allowed_types and not any(
            original_name.lower().endswith(ext) for ext in allowed_extensions
        ):
            raise HTTPException(
                status_code=400,
                detail=("Formato no válido. Acepta WhatsApp .txt, Instagram DM .json, Telegram .json o .csv."),
            )
        file_bytes = await file.read()
        file_name = original_name

    service = _build_service(db)
    try:
        model = await service.clone_from_material(
            tenant_id=current_user.tenant_id,
            text_input=text_input,
            file_bytes=file_bytes,
            file_name=file_name,
            user_name=user_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return _model_to_dto(model)


@router.post("/clone/dry-run")
async def clone_dry_run(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    text_input: Annotated[str | None, Form()] = None,
    file: Annotated[UploadFile | None, File()] = None,
) -> CloneDryRunResponse:
    """Parse-only inspection of the material — no LLM, fast (<1s).

    Returns the parsed message count, detected format, context coverage
    (greeting / price / objection / closing / follow_up) and a quality tier
    so the FE can warn the user BEFORE running the 2-4 minute LLM pipeline:

    - ``insufficient`` (<10 messages): block clone.
    - ``basic`` (10-29 messages): clone is permitted but warns about weak fidelity.
    - ``decent`` (30-99 messages): standard quality.
    - ``strong`` (100+ messages with diverse contexts): high fidelity.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    if text_input is not None and file is not None:
        raise HTTPException(status_code=400, detail="Envía texto O archivo, no ambos.")
    if text_input is None and file is None:
        raise HTTPException(status_code=400, detail="Proporciona text_input o file.")

    file_bytes: bytes | None = None
    if file is not None:
        file_bytes = await file.read()

    service = _build_service(db)
    try:
        result = service.dry_run_clone(text_input=text_input, file_bytes=file_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return CloneDryRunResponse(**result)


@router.post("/{profile_id}/activate")
async def activate_profile(
    profile_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PersonalityProfileDTO:
    """Activate an existing personality profile for the tenant.

    Idempotent: if the profile is already active, returns it unchanged.
    Deactivates any other currently active global profile for the tenant.

    Returns 404 if the profile does not exist or belongs to a different tenant.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    logger.info(
        "personality.activate",
        tenant_id=str(current_user.tenant_id),
        profile_id=str(profile_id),
    )

    service = _build_service(db)
    model = service.activate(profile_id=profile_id, tenant_id=current_user.tenant_id)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail="Perfil no encontrado o no pertenece a este tenant.",
        )

    return _model_to_dto(model)


@router.post("/from-voice-tone")
async def migrate_from_voice_tone(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> FromVoiceToneResponse:
    """Migrate legacy BrandIdentity.voice_tone to a full PersonalityProfile.

    Reads the tenant's ``BrandIdentity.voice_tone`` text, maps it to the
    nearest personality preset via LLM similarity, creates a profile with
    ``profile_type="migrated_from_voice_tone"``, and auto-activates it.

    Returns:
    - 404 if no legacy voice_tone text is found.
    - 409 if a migrated profile already exists and is active for this tenant.
    - 200 with FromVoiceToneResponse on success.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    logger.info("personality.from_voice_tone", tenant_id=str(current_user.tenant_id))

    # Read brand identity to get voice_tone
    from luana_core_brand_studio.infrastructure.repositories.brand_repository import BrandRepository

    brand_repo = BrandRepository(db)
    brand_settings = brand_repo.get_settings(current_user.tenant_id)

    if not brand_settings or not brand_settings.identity or not brand_settings.identity.voice_tone:
        raise HTTPException(
            status_code=404,
            detail="No hay tono de voz legado que migrar.",
        )

    voice_tone_text = brand_settings.identity.voice_tone

    # Check if migration already done (any active profile of type migrated_from_voice_tone)
    repo = PersonalityProfileRepository(db)
    active_profile = repo.get_active(tenant_id=current_user.tenant_id)
    if active_profile is not None and active_profile.profile_type == "migrated_from_voice_tone":
        raise HTTPException(
            status_code=409,
            detail="Este tenant ya tiene un perfil migrado activo.",
        )

    service = _build_service(db)
    try:
        profile_model, matched_preset_key, confidence = await service.migrate_from_voice_tone(
            tenant_id=current_user.tenant_id,
            voice_tone_text=voice_tone_text,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return FromVoiceToneResponse(
        profile=_model_to_dto(profile_model),
        source_voice_tone=voice_tone_text,
        matched_preset_key=matched_preset_key,
        match_confidence=confidence,
    )


@router.put("/{profile_id}/dimensions")
async def update_dimensions(
    profile_id: UUID,
    request: UpdateDimensionsRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> PersonalityProfileDTO:
    """Update the numeric dimension sliders and recompile system_instruction.

    All 6 dimension keys (energy, warmth, humor, expressiveness, narrative, verbosity)
    must be present in the request body as floats in [0.0, 1.0].
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    logger.info(
        "personality.update_dimensions",
        tenant_id=str(current_user.tenant_id),
        profile_id=str(profile_id),
    )

    try:
        service = _build_service(db)
        model = service.update_dimensions(
            profile_id=profile_id,
            tenant_id=current_user.tenant_id,
            new_dimensions=request.dimensions,
        )
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"PersonalityProfile {profile_id} not found or does not belong to this tenant.",
        )

    return _model_to_dto(model)


@router.post("/{profile_id}/simulate")
async def simulate_responses(
    profile_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> SimulationDTO:
    """Generate a personality simulation preview using the profile's system_instruction.

    Returns 3 canned example exchanges drawn from the stored sample_exchanges.
    Full LLM-driven simulation can be wired here later.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    logger.info(
        "personality.simulate",
        tenant_id=str(current_user.tenant_id),
        profile_id=str(profile_id),
    )

    repo = PersonalityProfileRepository(db)
    model = repo.get_by_id(profile_id, tenant_id=current_user.tenant_id)

    if model is None:
        raise HTTPException(
            status_code=404,
            detail=f"PersonalityProfile {profile_id} not found or does not belong to this tenant.",
        )

    # Build mock simulation from stored sample_exchanges
    sample_exchanges = model.sample_exchanges or []
    responses = [
        {
            "context": ex.get("context", ""),
            "prospect_message": ex.get("other_message", ""),
            "agent_response": ex.get("author_response", ""),
        }
        for ex in sample_exchanges[:3]
    ]

    # Pad to 3 entries if fewer exchanges are stored
    while len(responses) < 3:
        responses.append(
            {
                "context": "generic",
                "prospect_message": "Hola, ¿me puedes contar más?",
                "agent_response": model.system_instruction[:200] if model.system_instruction else "",
            }
        )

    return SimulationDTO(responses=responses)


@router.delete("/{profile_id}", status_code=204)
async def delete_profile(
    profile_id: UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> Response:
    """Soft-delete a personality profile and clean up Qdrant style anchors.

    Returns 204 No Content on success, 404 if profile not found.
    """
    if not current_user.tenant_id:
        raise HTTPException(status_code=400, detail="User has no tenant")

    logger.info(
        "personality.delete",
        tenant_id=str(current_user.tenant_id),
        profile_id=str(profile_id),
    )

    service = _build_service(db)
    deleted = await service.delete_with_anchors(
        profile_id=profile_id,
        tenant_id=current_user.tenant_id,
    )

    if not deleted:
        raise HTTPException(
            status_code=404,
            detail=f"PersonalityProfile {profile_id} not found or does not belong to this tenant.",
        )

    return Response(status_code=204)
