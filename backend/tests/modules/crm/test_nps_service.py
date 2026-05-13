"""
Tests for NpsService: survey lifecycle, response handling, scoring, evangelist detection.

CRM-06: NPS survey creation, response validation, standard NPS calculation, evangelist candidates.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.orm import Session

from luana_core_crm.domain.enums import LifecycleStage
from luana_core_crm.infrastructure.models.customer_model import CustomerProfileModel
from luana_core_crm.infrastructure.models.nps_models import (
    NpsResponseModel,
    NpsSurveyModel,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAMPLE_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _make_survey(
    db: Session,
    tenant_id: uuid.UUID = SAMPLE_TENANT_ID,
    customer_id: uuid.UUID | None = None,
    token: str | None = None,
    status: str = "pending",
    delivery_channel: str = "universal_link",
    expires_at: datetime | None = None,
) -> NpsSurveyModel:
    import secrets

    survey = NpsSurveyModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        token=token or secrets.token_urlsafe(32),
        customer_id=customer_id,
        delivery_channel=delivery_channel,
        status=status,
        expires_at=expires_at or (datetime.now(timezone.utc) + timedelta(days=30)),
    )
    db.add(survey)
    db.flush()
    return survey


def _make_response(
    db: Session,
    tenant_id: uuid.UUID = SAMPLE_TENANT_ID,
    survey_id: uuid.UUID | None = None,
    customer_id: uuid.UUID | None = None,
    score: int = 5,
) -> NpsResponseModel:
    response = NpsResponseModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        survey_id=survey_id or uuid.uuid4(),
        customer_id=customer_id or uuid.uuid4(),
        score=score,
    )
    db.add(response)
    db.flush()
    return response


def _make_profile(
    db: Session,
    tenant_id: uuid.UUID = SAMPLE_TENANT_ID,
    stage: LifecycleStage = LifecycleStage.SUBSCRIBER,
    full_name: str = "Test User",
    computed_traits: dict | None = None,
) -> CustomerProfileModel:
    profile = CustomerProfileModel(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        primary_email=f"{uuid.uuid4().hex[:8]}@test.com",
        full_name=full_name,
        lifecycle_stage=stage,
        lead_score=0.0,
        lifetime_value=0.0,
        is_inactive=False,
        traits={},
        computed_traits=computed_traits or {},
    )
    db.add(profile)
    db.flush()
    return profile


# ---------------------------------------------------------------------------
# Tests: Create Survey
# ---------------------------------------------------------------------------


class TestCreateSurvey:
    """create_survey generates token, sets expiry, status, and optional fields."""

    def test_create_survey_generates_long_token(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)

        assert len(survey.token) >= 32

    def test_create_survey_expires_in_30_days(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)

        now = datetime.now(timezone.utc)
        assert survey.expires_at is not None
        assert survey.expires_at > now + timedelta(days=29)
        assert survey.expires_at < now + timedelta(days=31)

    def test_create_survey_status_pending(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)

        assert survey.status == "pending"

    def test_create_survey_optional_fields(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)

        assert survey.customer_id is None
        assert survey.offer_id is None
        assert survey.delivery_channel == "universal_link"


# ---------------------------------------------------------------------------
# Tests: Get Survey By Token
# ---------------------------------------------------------------------------


class TestGetSurveyByToken:
    """get_survey_by_token retrieves or returns None."""

    def test_get_survey_by_existing_token(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)

        result = svc.get_survey_by_token(survey.token)

        assert result is not None
        assert result.id == survey.id
        assert result.token == survey.token

    def test_get_survey_by_nonexistent_token(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        result = svc.get_survey_by_token("nonexistent-token-xyz")

        assert result is None


# ---------------------------------------------------------------------------
# Tests: Submit Response
# ---------------------------------------------------------------------------


class TestSubmitResponse:
    """submit_response validates score, creates response, updates survey and profile."""

    def test_submit_response_valid_score(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)
        profile = _make_profile(db, tenant_id=tenant_id)

        response = svc.submit_response(
            survey_id=survey.id,
            tenant_id=tenant_id,
            customer_id=profile.id,
            score=5,
        )

        assert response.score == 5
        assert response.tenant_id == tenant_id
        assert response.customer_id == profile.id

        db.refresh(survey)
        assert survey.status == "responded"

    def test_submit_response_updates_profile_nps_score(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)
        profile = _make_profile(db, tenant_id=tenant_id)

        svc.submit_response(
            survey_id=survey.id,
            tenant_id=tenant_id,
            customer_id=profile.id,
            score=8,
        )

        db.refresh(profile)
        assert profile.computed_traits["nps_score"] == 8

    def test_submit_response_invalid_score_negative(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)
        profile = _make_profile(db, tenant_id=tenant_id)

        with pytest.raises(ValueError, match="must be 0-10"):
            svc.submit_response(
                survey_id=survey.id,
                tenant_id=tenant_id,
                customer_id=profile.id,
                score=-1,
            )

    def test_submit_response_invalid_score_over_10(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)
        profile = _make_profile(db, tenant_id=tenant_id)

        with pytest.raises(ValueError, match="must be 0-10"):
            svc.submit_response(
                survey_id=survey.id,
                tenant_id=tenant_id,
                customer_id=profile.id,
                score=11,
            )

    def test_submit_response_tenant_isolation(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        other = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)
        profile = _make_profile(db, tenant_id=tenant_id)

        response = svc.submit_response(
            survey_id=survey.id,
            tenant_id=tenant_id,
            customer_id=profile.id,
            score=9,
        )

        assert response.tenant_id == tenant_id

        count = (
            db.execute(
                select(NpsResponseModel).where(NpsResponseModel.tenant_id == other),
            )
            .scalars()
            .all()
        )
        assert len(count) == 0


# ---------------------------------------------------------------------------
# Tests: Get NPS Summary
# ---------------------------------------------------------------------------


class TestGetNpsSummary:
    """get_nps_summary aggregates scores, calculates standard NPS and response rate."""

    def test_nps_summary_empty_tenant(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        summary = svc.get_nps_summary(tenant_id)

        assert summary["nps_score"] is None
        assert summary["standard_nps"] is None
        assert summary["promoter_count"] == 0
        assert summary["passive_count"] == 0
        assert summary["detractor_count"] == 0
        assert summary["total_responses"] == 0
        assert summary["surveys_sent"] == 0
        assert summary["response_rate_pct"] == 0.0

    def test_nps_summary_with_mixed_scores(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey1 = svc.create_survey(tenant_id=tenant_id)
        survey2 = svc.create_survey(tenant_id=tenant_id)
        survey3 = svc.create_survey(tenant_id=tenant_id)

        profile1 = _make_profile(db, tenant_id=tenant_id, full_name="Promoter")
        profile2 = _make_profile(db, tenant_id=tenant_id, full_name="Passive")
        profile3 = _make_profile(db, tenant_id=tenant_id, full_name="Detractor")

        svc.submit_response(survey_id=survey1.id, tenant_id=tenant_id, customer_id=profile1.id, score=9)
        svc.submit_response(survey_id=survey2.id, tenant_id=tenant_id, customer_id=profile2.id, score=7)
        svc.submit_response(survey_id=survey3.id, tenant_id=tenant_id, customer_id=profile3.id, score=3)

        summary = svc.get_nps_summary(tenant_id)

        assert summary["promoter_count"] == 1
        assert summary["passive_count"] == 1
        assert summary["detractor_count"] == 1
        assert summary["total_responses"] == 3
        assert summary["surveys_sent"] == 3
        assert summary["response_rate_pct"] == 100.0
        assert summary["standard_nps"] == 0.0
        assert summary["nps_score"] == 6.3


# ---------------------------------------------------------------------------
# Tests: Get Evangelist Candidates
# ---------------------------------------------------------------------------


class TestGetEvangelistCandidates:
    """get_evangelist_candidates finds high-NPS customers not yet promoted."""

    def test_evangelist_candidates_returns_high_scores(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)
        profile = _make_profile(db, tenant_id=tenant_id, stage=LifecycleStage.CUSTOMER, full_name="Happy Customer")

        svc.submit_response(survey_id=survey.id, tenant_id=tenant_id, customer_id=profile.id, score=10)

        candidates = svc.get_evangelist_candidates(tenant_id)

        assert len(candidates) == 1
        assert candidates[0]["full_name"] == "Happy Customer"
        assert candidates[0]["nps_score"] == 10

    def test_evangelist_candidates_filters_by_tenant(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        other = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
        svc = NpsService(db)

        survey_a = svc.create_survey(tenant_id=tenant_id)
        profile_a = _make_profile(db, tenant_id=tenant_id, full_name="Tenant A")
        svc.submit_response(survey_id=survey_a.id, tenant_id=tenant_id, customer_id=profile_a.id, score=10)

        survey_b = svc.create_survey(tenant_id=other)
        profile_b = _make_profile(db, tenant_id=other, full_name="Tenant B")
        svc.submit_response(survey_id=survey_b.id, tenant_id=other, customer_id=profile_b.id, score=10)

        candidates = svc.get_evangelist_candidates(tenant_id)

        assert len(candidates) == 1
        assert candidates[0]["full_name"] == "Tenant A"

    def test_evangelist_candidates_empty_when_all_evangelist(self, db: Session, tenant_id):
        from luana_core_crm.application.services.nps_service import NpsService

        svc = NpsService(db)
        survey = svc.create_survey(tenant_id=tenant_id)
        profile = _make_profile(
            db, tenant_id=tenant_id, stage=LifecycleStage.EVANGELIST, full_name="Already Evangelist"
        )

        svc.submit_response(survey_id=survey.id, tenant_id=tenant_id, customer_id=profile.id, score=10)

        candidates = svc.get_evangelist_candidates(tenant_id)

        assert len(candidates) == 0


# ---------------------------------------------------------------------------
# Tests: Calculate NPS Score (static)
# ---------------------------------------------------------------------------


class TestCalculateNpsScore:
    """calculate_nps_score returns average rounded to 1 decimal."""

    def test_empty_returns_none(self):
        from luana_core_crm.application.services.nps_service import NpsService

        assert NpsService.calculate_nps_score([]) is None

    def test_average_rounded(self):
        from luana_core_crm.application.services.nps_service import NpsService

        result = NpsService.calculate_nps_score([9, 8, 3])

        assert result == 6.7

    def test_single_score(self):
        from luana_core_crm.application.services.nps_service import NpsService

        result = NpsService.calculate_nps_score([10])

        assert result == 10.0


# ---------------------------------------------------------------------------
# Tests: Calculate Standard NPS (static)
# ---------------------------------------------------------------------------


class TestCalculateStandardNps:
    """calculate_standard_nps returns ((promoters - detractors) / total) * 100."""

    def test_empty_returns_none(self):
        from luana_core_crm.application.services.nps_service import NpsService

        assert NpsService.calculate_standard_nps([]) is None

    def test_all_promoters(self):
        from luana_core_crm.application.services.nps_service import NpsService

        result = NpsService.calculate_standard_nps([9, 9, 9])

        assert result == 100.0

    def test_all_detractors(self):
        from luana_core_crm.application.services.nps_service import NpsService

        result = NpsService.calculate_standard_nps([0, 0, 0])

        assert result == -100.0

    def test_mixed_balanced(self):
        from luana_core_crm.application.services.nps_service import NpsService

        # promoter=9, passive=7, detractor=0 → (1-1)/3*100 = 0.0
        result = NpsService.calculate_standard_nps([9, 7, 0])

        assert result == 0.0
