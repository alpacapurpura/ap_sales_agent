"""Supplemental tests for StagingMetricsRepository — covering uncovered branches."""

import uuid
from datetime import UTC, date, datetime, timedelta
from unittest.mock import MagicMock

TENANT_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
RUN_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


def _make_repo():
    from src.modules.analytics.infrastructure.repositories.staging_repository import (
        StagingMetricsRepository,
    )

    db = MagicMock()
    return StagingMetricsRepository(db), db


def _make_model(**kwargs):
    from src.modules.analytics.infrastructure.models.staging_metrics_model import (
        StagingMetricModel,
    )

    m = MagicMock(spec=StagingMetricModel)
    m.tenant_id = kwargs.get("tenant_id", TENANT_ID)
    m.provider = kwargs.get("provider", "meta")
    m.channel_slug = kwargs.get("channel_slug", "ig-organic")
    m.metric_name = kwargs.get("metric_name", "reach")
    m.metric_date = kwargs.get("metric_date", date(2026, 3, 1))
    m.campaign_id = kwargs.get("campaign_id")
    m.ad_set_id = kwargs.get("ad_set_id")
    m.ad_id = kwargs.get("ad_id")
    m.value = kwargs.get("value", 100.0)
    m.extraction_run_id = kwargs.get("extraction_run_id", RUN_ID)
    return m


# ─── bulk_insert ───────────────────────────────────────────────────────────────


class TestBulkInsert:
    def test_empty_list_returns_zero(self):
        repo, db = _make_repo()
        result = repo.bulk_insert([])
        assert result == 0
        db.add_all.assert_not_called()

    def test_single_metric_inserted(self):
        repo, db = _make_repo()
        m = _make_model()
        result = repo.bulk_insert([m])
        assert result == 1
        db.add_all.assert_called_once()
        db.flush.assert_called_once()

    def test_duplicate_natural_key_last_wins(self):
        repo, db = _make_repo()
        m1 = _make_model(value=100.0)
        m2 = _make_model(value=200.0)  # same key as m1
        result = repo.bulk_insert([m1, m2])
        assert result == 1  # deduped to 1
        args = db.add_all.call_args[0][0]
        assert args[0].value == 200.0

    def test_different_metrics_not_deduped(self):
        repo, _ = _make_repo()
        m1 = _make_model(metric_name="reach")
        m2 = _make_model(metric_name="impressions")
        result = repo.bulk_insert([m1, m2])
        assert result == 2


# ─── get_by_run ───────────────────────────────────────────────────────────────


class TestGetByRun:
    def test_returns_empty_when_no_rows(self):
        repo, db = _make_repo()
        db.execute.return_value.scalars.return_value.all.return_value = []
        result = repo.get_by_run(RUN_ID)
        assert result == []

    def test_returns_rows_as_list(self):
        repo, db = _make_repo()
        m = _make_model()
        db.execute.return_value.scalars.return_value.all.return_value = [m]
        result = repo.get_by_run(RUN_ID)
        assert len(result) == 1


# ─── get_by_tenant_provider_date ─────────────────────────────────────────────


class TestGetByTenantProviderDate:
    def test_returns_filtered_rows(self):
        repo, db = _make_repo()
        m = _make_model()
        db.execute.return_value.scalars.return_value.all.return_value = [m]
        result = repo.get_by_tenant_provider_date(TENANT_ID, "meta", date(2026, 3, 1), date(2026, 3, 31))
        assert len(result) == 1

    def test_returns_empty_when_no_match(self):
        repo, db = _make_repo()
        db.execute.return_value.scalars.return_value.all.return_value = []
        result = repo.get_by_tenant_provider_date(TENANT_ID, "shopify", date(2026, 3, 1), date(2026, 3, 31))
        assert result == []


# ─── delete_by_tenant_provider ────────────────────────────────────────────────


class TestDeleteByTenantProvider:
    def test_returns_rowcount(self):
        repo, db = _make_repo()
        db.execute.return_value.rowcount = 5
        result = repo.delete_by_tenant_provider(TENANT_ID, "meta")
        assert result == 5
        db.flush.assert_called_once()

    def test_zero_rows_deleted(self):
        repo, db = _make_repo()
        db.execute.return_value.rowcount = 0
        result = repo.delete_by_tenant_provider(TENANT_ID, "nonexistent")
        assert result == 0


# ─── delete_older_than ────────────────────────────────────────────────────────


class TestDeleteOlderThan:
    def test_deletes_and_returns_count(self):
        repo, db = _make_repo()
        db.execute.return_value.rowcount = 10
        result = repo.delete_older_than(days=30)
        assert result == 10
        db.flush.assert_called_once()

    def test_custom_days(self):
        repo, db = _make_repo()
        db.execute.return_value.rowcount = 3
        result = repo.delete_older_than(days=7)
        assert result == 3
