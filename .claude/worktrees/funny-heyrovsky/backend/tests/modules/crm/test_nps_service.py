"""Tests for NPS service: survey lifecycle, scoring, candidate detection."""
import pytest


class TestNpsService:
    """NPS survey creation, response handling, and scoring."""

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_create_survey_generates_unique_token(self):
        """create_survey produces a unique URL-safe token."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_submit_response_validates_score_range(self):
        """Score must be 0-10 inclusive."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_get_nps_summary_categorizes_scores(self):
        """Promoters 9-10, passives 7-8, detractors 0-6."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_get_evangelist_candidates_filters_nps_gte_9(self):
        """Only customers with NPS >= 9 and not already EVANGELIST."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_calculate_nps_score_empty_returns_none(self):
        """Empty scores list returns None."""
        pass

    @pytest.mark.skip(reason="Wave 0 stub — implement after Plan 10-01 Task 1")
    def test_calculate_standard_nps_range(self):
        """Standard NPS formula returns value between -100 and +100."""
        pass
