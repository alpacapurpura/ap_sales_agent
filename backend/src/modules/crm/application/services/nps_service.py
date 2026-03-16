"""NPS service: survey lifecycle, response handling, scoring, and candidate detection."""
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select, func as sa_func
from sqlalchemy.orm import Session

from src.modules.crm.domain.enums import LifecycleStage
from src.modules.crm.infrastructure.models.customer_model import CustomerProfileModel
from src.modules.crm.infrastructure.models.nps_models import (
    NpsResponseModel,
    NpsSurveyModel,
)

logger = logging.getLogger(__name__)


class NpsService:
    """Manage NPS surveys, responses, scoring, and evangelist candidate detection."""

    def __init__(self, db: Session):
        self.db = db

    def create_survey(
        self,
        tenant_id: UUID,
        customer_id: Optional[UUID] = None,
        offer_id: Optional[UUID] = None,
        delivery_channel: str = "universal_link",
    ) -> NpsSurveyModel:
        """Create NPS survey with unique token (secrets.token_urlsafe(32)).

        Set expires_at = now + 30 days. Status = 'pending'.
        """
        token = secrets.token_urlsafe(32)
        now = datetime.now(timezone.utc)

        survey = NpsSurveyModel(
            tenant_id=tenant_id,
            token=token,
            customer_id=customer_id,
            offer_id=offer_id,
            delivery_channel=delivery_channel,
            status="pending",
            expires_at=now + timedelta(days=30),
        )
        self.db.add(survey)
        self.db.flush()

        logger.info(
            "NPS survey created: token=%s tenant=%s customer=%s",
            token[:8] + "...", tenant_id, customer_id,
        )
        return survey

    def get_survey_by_token(self, token: str) -> Optional[NpsSurveyModel]:
        """Retrieve survey by public token (no tenant filter -- public URL)."""
        stmt = select(NpsSurveyModel).where(NpsSurveyModel.token == token)
        result = self.db.execute(stmt)
        return result.scalars().first()

    def submit_response(
        self,
        survey_id: UUID,
        tenant_id: UUID,
        customer_id: UUID,
        score: int,
        feedback_text: Optional[str] = None,
        testimonial_text: Optional[str] = None,
        testimonial_audio_url: Optional[str] = None,
        consent_public_use: bool = False,
    ) -> NpsResponseModel:
        """Record NPS response. Validate score 0-10. Update survey status to 'responded'.

        Update customer_profile.computed_traits['nps_score'] = score via JSONB update.
        """
        if not (0 <= score <= 10):
            raise ValueError(f"NPS score must be 0-10, got {score}")

        response = NpsResponseModel(
            tenant_id=tenant_id,
            survey_id=survey_id,
            customer_id=customer_id,
            score=score,
            feedback_text=feedback_text,
            testimonial_text=testimonial_text,
            testimonial_audio_url=testimonial_audio_url,
            consent_public_use=consent_public_use,
        )
        self.db.add(response)

        # Update survey status
        survey = self.db.execute(
            select(NpsSurveyModel).where(NpsSurveyModel.id == survey_id)
        ).scalars().first()
        if survey:
            survey.status = "responded"

        # Update customer computed_traits with nps_score
        profile = self.db.execute(
            select(CustomerProfileModel).where(
                CustomerProfileModel.id == customer_id,
                CustomerProfileModel.tenant_id == tenant_id,
            )
        ).scalars().first()
        if profile:
            computed = dict(profile.computed_traits or {})
            computed["nps_score"] = score
            profile.computed_traits = computed

        self.db.flush()

        logger.info(
            "NPS response recorded: survey=%s customer=%s score=%d",
            survey_id, customer_id, score,
        )
        return response

    def get_nps_summary(self, tenant_id: UUID) -> dict:
        """Aggregate NPS data for a tenant.

        Return {nps_score (0-10 avg), standard_nps (-100 to +100),
        promoter_count, passive_count, detractor_count,
        total_responses, surveys_sent, response_rate_pct}.
        """
        # Count surveys sent
        surveys_sent = self.db.execute(
            select(sa_func.count(NpsSurveyModel.id)).where(
                NpsSurveyModel.tenant_id == tenant_id,
            )
        ).scalar() or 0

        # Get all response scores
        stmt = select(NpsResponseModel.score).where(
            NpsResponseModel.tenant_id == tenant_id,
        )
        result = self.db.execute(stmt)
        scores = [row[0] for row in result]

        total_responses = len(scores)
        promoter_count = sum(1 for s in scores if s >= 9)
        passive_count = sum(1 for s in scores if 7 <= s <= 8)
        detractor_count = sum(1 for s in scores if s <= 6)

        nps_score = self.calculate_nps_score(scores)
        standard_nps = self.calculate_standard_nps(scores)

        response_rate_pct = (
            round((total_responses / surveys_sent) * 100, 1)
            if surveys_sent > 0
            else 0.0
        )

        return {
            "nps_score": nps_score,
            "standard_nps": standard_nps,
            "promoter_count": promoter_count,
            "passive_count": passive_count,
            "detractor_count": detractor_count,
            "total_responses": total_responses,
            "surveys_sent": surveys_sent,
            "response_rate_pct": response_rate_pct,
        }

    def get_evangelist_candidates(self, tenant_id: UUID) -> list[dict]:
        """Find customers with NPS >= 9 whose lifecycle_stage != EVANGELIST.

        Join NpsResponseModel with CustomerProfileModel.
        Return [{customer_id, full_name, nps_score, responded_at}].
        """
        stmt = (
            select(
                NpsResponseModel.customer_id,
                CustomerProfileModel.full_name,
                NpsResponseModel.score,
                NpsResponseModel.responded_at,
            )
            .join(
                CustomerProfileModel,
                CustomerProfileModel.id == NpsResponseModel.customer_id,
            )
            .where(
                NpsResponseModel.tenant_id == tenant_id,
                NpsResponseModel.score >= 9,
                CustomerProfileModel.lifecycle_stage != LifecycleStage.EVANGELIST,
            )
            .order_by(NpsResponseModel.score.desc())
        )
        result = self.db.execute(stmt)
        rows = result.all()

        return [
            {
                "customer_id": str(row.customer_id),
                "full_name": row.full_name,
                "nps_score": row.score,
                "responded_at": row.responded_at.isoformat() if row.responded_at else None,
            }
            for row in rows
        ]

    @staticmethod
    def calculate_nps_score(scores: list[int]) -> Optional[float]:
        """Average score (0-10 scale). Returns None if empty."""
        if not scores:
            return None
        return round(sum(scores) / len(scores), 1)

    @staticmethod
    def calculate_standard_nps(scores: list[int]) -> Optional[float]:
        """Standard NPS: ((promoters - detractors) / total) * 100. Range -100 to +100."""
        if not scores:
            return None
        total = len(scores)
        promoters = sum(1 for s in scores if s >= 9)
        detractors = sum(1 for s in scores if s <= 6)
        return round(((promoters - detractors) / total) * 100, 1)
