"""Tests for CaptureCostService, StageCostService, ManyChatMetricsPromoter."""

import uuid
from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


def _db_with_rows(rows):
    db = MagicMock()
    db.execute.return_value.all.return_value = rows
    db.execute.return_value.scalars.return_value.all.return_value = rows
    db.execute.return_value.scalar.return_value = 0.0
    return db


# ─── CaptureCostService ────────────────────────────────────────────────────────


class TestCaptureCostServiceGetChannelCosts:
    def test_empty_db_returns_empty_dict(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        db = _db_with_rows([])
        svc = CaptureCostService(db=db)
        result = svc.get_channel_costs(TENANT_ID)
        assert result == {}

    def test_rows_returned_as_dict(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        row1 = MagicMock()
        row1.channel_slug = "mailerlite"
        row1.total = 29.0
        row2 = MagicMock()
        row2.channel_slug = "ig-dm"
        row2.total = 15.0

        db = _db_with_rows([row1, row2])
        svc = CaptureCostService(db=db)
        result = svc.get_channel_costs(TENANT_ID)
        assert result == {"mailerlite": 29.0, "ig-dm": 15.0}

    def test_custom_stage_arg_accepted(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        db = _db_with_rows([])
        svc = CaptureCostService(db=db)
        result = svc.get_channel_costs(TENANT_ID, stage="capture")
        assert result == {}


class TestCaptureCostServiceGetTotalStage0Spend:
    def test_zero_spend_returns_zero(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        db = MagicMock()
        db.execute.return_value.scalar.return_value = 0.0
        svc = CaptureCostService(db=db)
        result = svc.get_total_stage0_spend(
            TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC)
        )
        assert result == 0.0

    def test_spend_returned(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        db = MagicMock()
        db.execute.return_value.scalar.return_value = 1500.0
        svc = CaptureCostService(db=db)
        result = svc.get_total_stage0_spend(
            TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC)
        )
        assert result == 1500.0

    def test_none_result_returns_zero(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        db = MagicMock()
        db.execute.return_value.scalar.return_value = None
        svc = CaptureCostService(db=db)
        result = svc.get_total_stage0_spend(
            TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC)
        )
        assert result == 0.0


class TestCaptureCostServiceCalculateCal:
    def test_zero_leads_returns_none(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        svc = CaptureCostService(db=MagicMock())
        assert svc.calculate_cal(100.0, 0) is None

    def test_non_zero_leads_computes(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        svc = CaptureCostService(db=MagicMock())
        result = svc.calculate_cal(300.0, 10)
        assert result == 30.0

    def test_rounding_applied(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        svc = CaptureCostService(db=MagicMock())
        result = svc.calculate_cal(100.0, 3)
        assert result == round(100.0 / 3, 2)


class TestCaptureCostServiceGetProratedAgencyCosts:
    def test_no_rows_returns_empty(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = []
        svc = CaptureCostService(db=db)
        result = svc.get_prorated_agency_costs(TENANT_ID, ["ig-dm"])
        assert result == {}

    def test_no_connected_channels_returns_empty(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        row = MagicMock()
        row.proration_category = "organic_management"
        row.monthly_amount = 100.0
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [row]
        svc = CaptureCostService(db=db)
        result = svc.get_prorated_agency_costs(TENANT_ID, [])
        assert result == {}

    def test_organic_management_splits_across_eligible(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        row = MagicMock()
        row.proration_category = "organic_management"
        row.monthly_amount = 90.0
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [row]
        svc = CaptureCostService(db=db)
        # ig-dm and fb-messenger are both in "organic_management"
        result = svc.get_prorated_agency_costs(TENANT_ID, ["ig-dm", "fb-messenger"])
        assert "ig-dm" in result
        assert "fb-messenger" in result
        assert result["ig-dm"] == pytest.approx(45.0)

    def test_full_service_splits_all_channels(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        row = MagicMock()
        row.proration_category = "full_service"
        row.monthly_amount = 200.0
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [row]
        svc = CaptureCostService(db=db)
        result = svc.get_prorated_agency_costs(TENANT_ID, ["ig-dm", "mailerlite", "email-capture"])
        assert len(result) == 3
        for slug in ["ig-dm", "mailerlite", "email-capture"]:
            assert result[slug] == pytest.approx(200.0 / 3)

    def test_category_with_no_eligible_channels_skipped(self):
        from src.modules.analytics.application.services.capture_cost_service import CaptureCostService

        row = MagicMock()
        row.proration_category = "paid_management"
        row.monthly_amount = 100.0
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [row]
        svc = CaptureCostService(db=db)
        # No paid channels connected
        result = svc.get_prorated_agency_costs(TENANT_ID, ["ig-dm", "mailerlite"])
        assert result == {}


# ─── StageCostService ─────────────────────────────────────────────────────────


class TestStageCostServiceGetChannelCosts:
    def test_empty_returns_empty(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        db = _db_with_rows([])
        svc = StageCostService(db=db)
        result = svc.get_channel_costs(TENANT_ID)
        assert result == {}

    def test_rows_returned(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        row = MagicMock()
        row.channel_slug = "ai-sdr"
        row.total = 50.0
        db = _db_with_rows([row])
        svc = StageCostService(db=db)
        result = svc.get_channel_costs(TENANT_ID)
        assert result == {"ai-sdr": 50.0}


class TestStageCostServiceGetRetargetingSpend:
    def test_empty_returns_empty(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        db = _db_with_rows([])
        svc = StageCostService(db=db)
        result = svc.get_retargeting_spend(
            TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC)
        )
        assert result == {}

    def test_rows_returned(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        row = MagicMock()
        row.channel_slug = "meta-retargeting"
        row.total = 450.0
        db = _db_with_rows([row])
        svc = StageCostService(db=db)
        result = svc.get_retargeting_spend(
            TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC)
        )
        assert result == {"meta-retargeting": 450.0}


class TestStageCostServiceCalculateCostPerMql:
    def test_zero_mqls_returns_none(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        svc = StageCostService(db=MagicMock())
        assert svc.calculate_cost_per_mql(100.0, 0) is None

    def test_non_zero_computes(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        svc = StageCostService(db=MagicMock())
        result = svc.calculate_cost_per_mql(300.0, 10)
        assert result == 30.0


class TestStageCostServiceGetGroupCostPerMql:
    def test_zero_mqls_returns_none(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        svc = StageCostService(db=MagicMock())
        result = svc.get_group_cost_per_mql(
            "retargeting", TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC), 0
        )
        assert result is None

    def test_unknown_group_returns_none(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        svc = StageCostService(db=MagicMock())
        result = svc.get_group_cost_per_mql(
            "unknown_group", TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC), 10
        )
        assert result is None

    def test_retargeting_zero_spend_returns_none(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        db = _db_with_rows([])
        svc = StageCostService(db=db)
        result = svc.get_group_cost_per_mql(
            "retargeting", TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC), 5
        )
        assert result is None

    def test_retargeting_with_spend_computes(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        row = MagicMock()
        row.channel_slug = "meta-retargeting"
        row.total = 500.0
        db = _db_with_rows([row])
        svc = StageCostService(db=db)
        result = svc.get_group_cost_per_mql(
            "retargeting", TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC), 10
        )
        assert result == 50.0

    def test_automation_zero_costs_returns_none(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        db = _db_with_rows([])
        svc = StageCostService(db=db)
        result = svc.get_group_cost_per_mql(
            "automation", TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC), 5
        )
        assert result is None

    def test_automation_with_costs_computes(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        row = MagicMock()
        row.channel_slug = "mailerlite"
        row.total = 100.0
        db = _db_with_rows([row])
        svc = StageCostService(db=db)
        result = svc.get_group_cost_per_mql(
            "automation", TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC), 10
        )
        assert result == 10.0


class TestStageCostServiceGetTotalFunnelInvestment:
    def test_zero_all_returns_zero_incomplete(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        db = MagicMock()
        db.execute.return_value.scalar.return_value = 0.0
        db.execute.return_value.all.return_value = []
        svc = StageCostService(db=db)
        total, is_complete = svc.get_total_funnel_investment(
            TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC)
        )
        assert total == 0.0
        assert is_complete is False

    def test_nonzero_ad_spend_marks_complete(self):
        from src.modules.analytics.application.services.stage_cost_service import StageCostService

        call_count = [0]

        def execute_side_effect(stmt):
            call_count[0] += 1
            result = MagicMock()
            if call_count[0] == 1:
                result.scalar.return_value = 1000.0  # ad spend
            else:
                result.all.return_value = []
            return result

        db = MagicMock()
        db.execute.side_effect = execute_side_effect
        svc = StageCostService(db=db)
        _total, is_complete = svc.get_total_funnel_investment(
            TENANT_ID, datetime(2026, 3, 1, tzinfo=UTC), datetime(2026, 3, 31, tzinfo=UTC)
        )
        assert is_complete is True


# ─── ManyChatMetricsPromoter ──────────────────────────────────────────────────


class TestManyChatMetricsPromoter:
    def _make_promoter(self):
        from src.modules.analytics.application.services.manychat_metrics_promoter import (
            ManyChatMetricsPromoter,
        )

        db = MagicMock()
        return ManyChatMetricsPromoter(db=db)

    def test_promote_event_calls_upsert_increment(self):
        from datetime import date

        promoter = self._make_promoter()
        promoter.official_repo = MagicMock()
        promoter.promote_event(
            tenant_id=TENANT_ID,
            channel_slug="ig-dm",
            metric_name="leads",
            metric_date=date(2026, 3, 15),
            stage_slug="capture",
            value=1.0,
        )
        promoter.official_repo.upsert_increment.assert_called_once()
        call_kwargs = promoter.official_repo.upsert_increment.call_args.kwargs
        assert call_kwargs["tenant_id"] == TENANT_ID
        assert call_kwargs["channel_slug"] == "ig-dm"
        assert call_kwargs["metric_name"] == "leads"
        assert call_kwargs["value"] == 1.0

    def test_promote_event_with_extra(self):
        from datetime import date

        promoter = self._make_promoter()
        promoter.official_repo = MagicMock()
        promoter.promote_event(
            tenant_id=TENANT_ID,
            channel_slug="manychat-ig",
            metric_name="conversations",
            metric_date=date(2026, 3, 15),
            stage_slug="capture",
            extra={"source": "manychat_webhook"},
        )
        call_kwargs = promoter.official_repo.upsert_increment.call_args.kwargs
        assert call_kwargs["extra"] == {"source": "manychat_webhook"}

    def test_promote_event_default_value_is_one(self):
        from datetime import date

        promoter = self._make_promoter()
        promoter.official_repo = MagicMock()
        promoter.promote_event(
            tenant_id=TENANT_ID,
            channel_slug="ig-dm",
            metric_name="leads",
            metric_date=date(2026, 3, 15),
            stage_slug="capture",
        )
        call_kwargs = promoter.official_repo.upsert_increment.call_args.kwargs
        assert call_kwargs["value"] == 1.0

    def test_promote_event_none_extra_becomes_empty_dict(self):
        from datetime import date

        promoter = self._make_promoter()
        promoter.official_repo = MagicMock()
        promoter.promote_event(
            tenant_id=TENANT_ID,
            channel_slug="ig-dm",
            metric_name="leads",
            metric_date=date(2026, 3, 15),
            stage_slug="capture",
            extra=None,
        )
        call_kwargs = promoter.official_repo.upsert_increment.call_args.kwargs
        assert call_kwargs["extra"] == {}
