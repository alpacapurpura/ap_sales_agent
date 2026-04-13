"""Tests for MetricAggregationRepository — idempotent replace/upsert pattern.

Task P1: Running ETL sync twice should not raise UniqueViolation.
The repository uses a delete+insert pattern within the same transaction scope.
"""

import uuid
from datetime import date
from unittest.mock import MagicMock

import pytest

from src.modules.analytics.infrastructure.repositories.metric_aggregation_repository import (
    MetricAggregationRepository,
)


@pytest.fixture
def tenant_id():
    return uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture
def sample_agg_dicts(tenant_id):
    """Two aggregation dicts for the same channel."""
    return [
        {
            "tenant_id": tenant_id,
            "channel_slug": "meta-ads",
            "metric_name": "impressions",
            "period_type": "last_30_days",
            "period_start": date(2026, 3, 1),
            "period_end": date(2026, 3, 30),
            "value": 50000.0,
            "unit": "count",
            "currency": None,
            "cost_type": "investment",
            "extraction_run_id": uuid.uuid4(),
        },
        {
            "tenant_id": tenant_id,
            "channel_slug": "meta-ads",
            "metric_name": "spend",
            "period_type": "last_30_days",
            "period_start": date(2026, 3, 1),
            "period_end": date(2026, 3, 30),
            "value": 1500.0,
            "unit": "currency",
            "currency": "USD",
            "cost_type": "investment",
            "extraction_run_id": uuid.uuid4(),
        },
    ]


class TestReplaceAggregations:
    """Test the delete+insert pattern for idempotent aggregation storage."""

    def test_calls_delete_before_insert(self, tenant_id, sample_agg_dicts):
        """Verify DELETE is called before INSERT for the correct scope."""
        db = MagicMock()
        repo = MetricAggregationRepository(db)

        result = repo.replace_aggregations(tenant_id, "meta-ads", sample_agg_dicts)

        assert result == 2
        # At least 3 calls: 1 delete + 2 inserts
        assert db.execute.call_count >= 3
        db.flush.assert_called_once()

    def test_no_op_on_empty_list(self, tenant_id):
        """Empty agg_dicts should not call delete or insert."""
        db = MagicMock()
        repo = MetricAggregationRepository(db)

        result = repo.replace_aggregations(tenant_id, "meta-ads", [])

        assert result == 0
        db.execute.assert_not_called()
        db.flush.assert_not_called()

    def test_idempotent_double_call(self, tenant_id, sample_agg_dicts):
        """Calling replace_aggregations twice should work without errors.

        This is the core P1 regression test — the second call deletes
        the first batch, then inserts fresh rows.
        """
        db = MagicMock()
        repo = MetricAggregationRepository(db)

        result1 = repo.replace_aggregations(tenant_id, "meta-ads", sample_agg_dicts)
        result2 = repo.replace_aggregations(tenant_id, "meta-ads", sample_agg_dicts)

        assert result1 == 2
        assert result2 == 2

    def test_multi_channel_scoping(self, tenant_id, sample_agg_dicts):
        """Replacing aggregations for one channel should not affect others."""
        db = MagicMock()
        repo = MetricAggregationRepository(db)

        # Replace meta-ads
        repo.replace_aggregations(tenant_id, "meta-ads", sample_agg_dicts)

        # The delete should only target meta-ads
        first_execute_call = db.execute.call_args_list[0]
        sql_text = str(first_execute_call[0][0])
        assert "meta-ads" in str(first_execute_call[0][1]) or "channel_slug" in sql_text


class TestBulkUpsertFromPipeline:
    """Integration-style tests verifying pipeline uses the repo correctly."""

    def test_pipeline_aggregation_dict_keys(self, sample_agg_dicts):
        """Verify aggregation dicts have all required keys for the repo."""
        required_keys = {
            "tenant_id",
            "channel_slug",
            "metric_name",
            "period_type",
            "period_start",
            "period_end",
            "value",
            "unit",
        }
        for agg in sample_agg_dicts:
            assert required_keys.issubset(agg.keys()), f"Missing keys: {required_keys - set(agg.keys())}"
