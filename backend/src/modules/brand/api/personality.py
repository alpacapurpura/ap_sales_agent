"""Brand Personality Engine API endpoints.

7 REST endpoints for personality profile management.
All endpoints filter by X-Tenant-ID via get_current_user dependency.
All endpoints use return type annotations as response models (PII compliance).
"""

from datetime import datetime
from typing import Annotated
from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.brand.application.services.personality_service import PersonalityService
from src.modules.brand.domain.personality import PERSONALITY_PRESETS
from src.modules.brand.infrastructure.repositories.personality_repository import PersonalityProfileRepository
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

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


@router.post("/clone", status_code=501)
async def clone_from_chat(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
    file: Annotated[UploadFile | None, File()] = None,
    user_name: Annotated[str | None, Form()] = None,
) -> PersonalityProfileDTO:
    """Upload a chat file → run the personality pipeline → create a cloned profile.

    This endpoint requires LLM pipeline integration (Janitor → Psychologist →
    Architect → Compiler). Full implementation is pending.
    """
    logger.info(
        "personality.clone_from_chat.not_implemented",
        tenant_id=str(current_user.tenant_id) if current_user.tenant_id else None,
        user_name=user_name,
        has_file=file is not None,
    )
    raise HTTPException(
        status_code=501,
        detail="Clone-from-chat requires LLM pipeline integration — not yet implemented.",
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
