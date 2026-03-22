"""CRM NPS API: survey creation, public response, and evangelist candidate listing."""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter(prefix="/nps", tags=["CRM - NPS"])


# --- Request / Response Models ---


class CreateSurveyRequest(BaseModel):
    customer_id: Optional[str] = None  # null = per-offer batch
    offer_id: Optional[str] = None
    delivery_channel: str = "universal_link"


class SurveyResponse(BaseModel):
    id: str
    token: str
    status: str
    delivery_channel: str
    survey_url: str  # constructed from token


class SubmitNpsRequest(BaseModel):
    score: int  # 0-10
    feedback_text: Optional[str] = None
    testimonial_text: Optional[str] = None
    testimonial_audio_url: Optional[str] = None
    consent_public_use: bool = False


class NpsSummaryResponse(BaseModel):
    nps_score: Optional[float]
    standard_nps: Optional[float]
    promoter_count: int
    passive_count: int
    detractor_count: int
    total_responses: int
    surveys_sent: int
    response_rate_pct: float


class EvangelistCandidateResponse(BaseModel):
    customer_id: str
    full_name: Optional[str]
    nps_score: int
    responded_at: Optional[str]


# --- Endpoints ---


@router.post("/surveys", response_model=SurveyResponse)
async def create_survey(
    body: CreateSurveyRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
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
    db: Session = Depends(get_db),
):
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

    return {
        "id": str(survey.id),
        "token": survey.token,
        "status": survey.status,
        "delivery_channel": survey.delivery_channel,
        "offer_id": str(survey.offer_id) if survey.offer_id else None,
    }


@router.post("/survey/{token}/respond")
async def submit_nps_response(
    token: str,
    body: SubmitNpsRequest,
    db: Session = Depends(get_db),
):
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
        raise HTTPException(status_code=400, detail=str(e))

    return {
        "id": str(response.id),
        "score": response.score,
        "status": "responded",
        "message": "Thank you for your feedback!",
    }


@router.get("/summary", response_model=NpsSummaryResponse)
async def get_nps_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get NPS summary metrics for tenant."""
    from src.modules.crm.application.services.nps_service import NpsService

    svc = NpsService(db)
    summary = svc.get_nps_summary(user.tenant_id)

    return NpsSummaryResponse(**summary)


@router.get("/candidates", response_model=List[EvangelistCandidateResponse])
async def get_evangelist_candidates(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Get customers with NPS >= 9 not yet promoted to EVANGELIST."""
    from src.modules.crm.application.services.nps_service import NpsService

    svc = NpsService(db)
    candidates = svc.get_evangelist_candidates(user.tenant_id)

    return [EvangelistCandidateResponse(**c) for c in candidates]
