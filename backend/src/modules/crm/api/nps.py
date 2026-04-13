"""CRM NPS API: survey creation, public response, and evangelist candidate listing."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(prefix="/nps", tags=["CRM - NPS"])


# --- Request / Response Models ---


class CreateSurveyRequest(BaseModel):
    """Request schema for create survey."""

    customer_id: str | None = None  # null = per-offer batch
    offer_id: str | None = None
    delivery_channel: str = "universal_link"


class SurveyResponse(BaseModel):
    """Response schema for survey."""

    id: str
    token: str
    status: str
    delivery_channel: str
    survey_url: str  # constructed from token


class SubmitNpsRequest(BaseModel):
    """Request schema for submit nps."""

    score: int  # 0-10
    feedback_text: str | None = None
    testimonial_text: str | None = None
    testimonial_audio_url: str | None = None
    consent_public_use: bool = False


class NpsSummaryResponse(BaseModel):
    """Response schema for nps summary."""

    nps_score: float | None
    standard_nps: float | None
    promoter_count: int
    passive_count: int
    detractor_count: int
    total_responses: int
    surveys_sent: int
    response_rate_pct: float


class EvangelistCandidateResponse(BaseModel):
    """Response schema for evangelist candidate."""

    customer_id: str
    full_name: str | None
    nps_score: int
    responded_at: str | None


class SurveyPublicResponse(BaseModel):
    """Public survey details returned to the respondent."""

    id: str
    token: str
    status: str
    delivery_channel: str
    offer_id: str | None


class NpsSubmitResponse(BaseModel):
    """Confirmation returned after a successful NPS submission."""

    id: str
    score: int
    status: str
    message: str


# --- Endpoints ---


@router.post("/surveys")
async def create_survey(
    body: CreateSurveyRequest,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> SurveyResponse:
    """Create NPS survey. Returns survey with unique token URL."""
    from uuid import UUID

    from src.modules.crm.application.services.nps_service import NpsService

    customer_id = UUID(body.customer_id) if body.customer_id else None
    offer_id = UUID(body.offer_id) if body.offer_id else None

    svc = NpsService(db)
    survey = svc.create_survey(
        tenant_id=user.tenant_id,
        customer_id=customer_id,
        offer_id=offer_id,
        delivery_channel=body.delivery_channel,
    )
    db.commit()

    return SurveyResponse(
        id=str(survey.id),
        token=survey.token,
        status=survey.status,
        delivery_channel=survey.delivery_channel,
        survey_url=f"/nps/survey/{survey.token}",
    )


@router.get("/survey/{token}")
async def get_survey(
    token: str,
    db: Annotated[Session, Depends(get_db)],
) -> SurveyPublicResponse:
    """Public endpoint (no auth) -- retrieve survey by token for respondent.

    Returns survey details. No tenant auth needed.
    """
    from src.modules.crm.application.services.nps_service import NpsService

    svc = NpsService(db)
    survey = svc.get_survey_by_token(token)

    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if survey.status == "expired":
        raise HTTPException(status_code=410, detail="Survey has expired")

    if survey.status == "responded":
        raise HTTPException(status_code=409, detail="Survey already responded")

    return SurveyPublicResponse(
        id=str(survey.id),
        token=survey.token,
        status=survey.status,
        delivery_channel=survey.delivery_channel,
        offer_id=str(survey.offer_id) if survey.offer_id else None,
    )


@router.post("/survey/{token}/respond")
async def submit_nps_response(
    token: str,
    body: SubmitNpsRequest,
    db: Annotated[Session, Depends(get_db)],
) -> NpsSubmitResponse:
    """Public endpoint (no auth) -- submit NPS response.

    Validates score 0-10. Updates survey status. Stores response.
    """
    from src.modules.crm.application.services.nps_service import NpsService

    svc = NpsService(db)
    survey = svc.get_survey_by_token(token)

    if not survey:
        raise HTTPException(status_code=404, detail="Survey not found")

    if survey.status == "responded":
        raise HTTPException(status_code=409, detail="Survey already responded")

    if survey.status == "expired":
        raise HTTPException(status_code=410, detail="Survey has expired")

    if not (0 <= body.score <= 10):
        raise HTTPException(status_code=400, detail="Score must be between 0 and 10")

    if not survey.customer_id:
        raise HTTPException(
            status_code=400,
            detail="Survey has no associated customer",
        )

    try:
        response = svc.submit_response(
            survey_id=survey.id,
            tenant_id=survey.tenant_id,
            customer_id=survey.customer_id,
            score=body.score,
            feedback_text=body.feedback_text,
            testimonial_text=body.testimonial_text,
            testimonial_audio_url=body.testimonial_audio_url,
            consent_public_use=body.consent_public_use,
        )
        db.commit()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    return NpsSubmitResponse(
        id=str(response.id),
        score=response.score,
        status="responded",
        message="Thank you for your feedback!",
    )


@router.get("/summary")
async def get_nps_summary(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> NpsSummaryResponse:
    """Get NPS summary metrics for tenant."""
    from src.modules.crm.application.services.nps_service import NpsService

    svc = NpsService(db)
    summary = svc.get_nps_summary(user.tenant_id)

    return NpsSummaryResponse(**summary)


@router.get("/candidates")
async def get_evangelist_candidates(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> list[EvangelistCandidateResponse]:
    """Get customers with NPS >= 9 not yet promoted to EVANGELIST."""
    from src.modules.crm.application.services.nps_service import NpsService

    svc = NpsService(db)
    candidates = svc.get_evangelist_candidates(user.tenant_id)

    return [EvangelistCandidateResponse(**c) for c in candidates]
