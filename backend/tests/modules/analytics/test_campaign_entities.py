"""Tests for analytics campaign domain entities (StrEnums)."""

from src.modules.analytics.domain.campaign_entities import (
    BidStrategy,
    CampaignObjective,
    CampaignStatus,
    EffectiveStatus,
    LearningStage,
    RecommendationSource,
)


class TestCampaignObjective:
    def test_odax_values(self) -> None:
        assert CampaignObjective.OUTCOME_AWARENESS == "OUTCOME_AWARENESS"
        assert CampaignObjective.OUTCOME_SALES == "OUTCOME_SALES"
        assert CampaignObjective.OUTCOME_LEADS == "OUTCOME_LEADS"

    def test_legacy_values(self) -> None:
        assert CampaignObjective.CONVERSIONS == "CONVERSIONS"
        assert CampaignObjective.REACH == "REACH"
        assert CampaignObjective.UNKNOWN == "UNKNOWN"

    def test_all_members_are_strings(self) -> None:
        for member in CampaignObjective:
            assert isinstance(member, str)

    def test_roundtrip_from_string(self) -> None:
        assert CampaignObjective("OUTCOME_ENGAGEMENT") is CampaignObjective.OUTCOME_ENGAGEMENT


class TestCampaignStatus:
    def test_active_paused(self) -> None:
        assert CampaignStatus.ACTIVE == "ACTIVE"
        assert CampaignStatus.PAUSED == "PAUSED"

    def test_terminal_states(self) -> None:
        assert CampaignStatus.DELETED == "DELETED"
        assert CampaignStatus.ARCHIVED == "ARCHIVED"

    def test_all_members(self) -> None:
        statuses = {s.value for s in CampaignStatus}
        assert "ACTIVE" in statuses
        assert "WITH_ISSUES" in statuses

    def test_roundtrip(self) -> None:
        assert CampaignStatus("DELETED") is CampaignStatus.DELETED


class TestEffectiveStatus:
    def test_inherited_states(self) -> None:
        assert EffectiveStatus.CAMPAIGN_PAUSED == "CAMPAIGN_PAUSED"
        assert EffectiveStatus.ADSET_PAUSED == "ADSET_PAUSED"

    def test_review_states(self) -> None:
        assert EffectiveStatus.PENDING_REVIEW == "PENDING_REVIEW"
        assert EffectiveStatus.DISAPPROVED == "DISAPPROVED"
        assert EffectiveStatus.PREAPPROVED == "PREAPPROVED"

    def test_roundtrip(self) -> None:
        assert EffectiveStatus("ACTIVE") is EffectiveStatus.ACTIVE


class TestBidStrategy:
    def test_all_values(self) -> None:
        assert BidStrategy.LOWEST_COST_WITHOUT_CAP == "LOWEST_COST_WITHOUT_CAP"
        assert BidStrategy.LOWEST_COST_WITH_BID_CAP == "LOWEST_COST_WITH_BID_CAP"
        assert BidStrategy.COST_CAP == "COST_CAP"
        assert BidStrategy.LOWEST_COST_WITH_MIN_ROAS == "LOWEST_COST_WITH_MIN_ROAS"

    def test_roundtrip(self) -> None:
        assert BidStrategy("COST_CAP") is BidStrategy.COST_CAP


class TestLearningStage:
    def test_all_values(self) -> None:
        assert LearningStage.LEARNING == "LEARNING"
        assert LearningStage.SUCCESS == "SUCCESS"
        assert LearningStage.FAIL == "FAIL"

    def test_roundtrip(self) -> None:
        assert LearningStage("SUCCESS") is LearningStage.SUCCESS


class TestRecommendationSource:
    def test_values(self) -> None:
        assert RecommendationSource.ACCOUNT == "account"
        assert RecommendationSource.CAMPAIGN == "campaign"
        assert RecommendationSource.AD_SET == "ad_set"
        assert RecommendationSource.AD == "ad"

    def test_roundtrip(self) -> None:
        assert RecommendationSource("ad_set") is RecommendationSource.AD_SET
