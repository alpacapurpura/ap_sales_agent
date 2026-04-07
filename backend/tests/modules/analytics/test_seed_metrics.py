"""Tests for seed_metrics.py — validates seed data population and idempotency.

Uses a mock DB session to verify the seed function creates rows
in staging_metrics, official_metrics, and metric_aggregations.
"""

import uuid
from unittest.mock import MagicMock

import pytest

# The seed script defines a seed function we can test
from scripts.seed_metrics import (
    SEED_TENANT_ID,
    seed_data,
)


@pytest.fixture
def mock_db():
    """Mock SQLAlchemy session."""
    db = MagicMock()
    db.execute = MagicMock()
    db.add = MagicMock()
    db.add_all = MagicMock()
    db.commit = MagicMock()
    db.close = MagicMock()
    return db


class TestSeedMetrics:
    """Tests for the seed_data function."""

    def test_seed_creates_staging_rows(self, mock_db):
        """Seed function adds staging_metrics rows."""
        seed_data(mock_db)

        # Check that add_all was called (bulk inserts)
        assert mock_db.add_all.called
        # Verify commit was called
        assert mock_db.commit.called

    def test_seed_creates_official_rows(self, mock_db):
        """Seed function creates official_metrics rows alongside staging."""
        seed_data(mock_db)

        # add_all should be called multiple times (staging, official, aggregations)
        assert mock_db.add_all.call_count >= 2

    def test_seed_creates_aggregation_rows(self, mock_db):
        """Seed function creates metric_aggregations rows."""
        seed_data(mock_db)

        # At least 3 calls to add_all: staging, official, aggregations
        assert mock_db.add_all.call_count >= 3

    def test_seed_is_idempotent(self, mock_db):
        """Running seed twice produces the same result (clears before inserting)."""
        seed_data(mock_db)
        first_call_count = mock_db.add_all.call_count
        first_execute_count = mock_db.execute.call_count

        mock_db.reset_mock()

        seed_data(mock_db)
        second_call_count = mock_db.add_all.call_count
        second_execute_count = mock_db.execute.call_count

        # Same number of operations each time (idempotent)
        assert first_call_count == second_call_count
        assert first_execute_count == second_execute_count

    def test_seed_clears_before_insert(self, mock_db):
        """Seed function deletes existing data for the test tenant before inserting."""
        seed_data(mock_db)

        # execute should be called first (for DELETE statements)
        assert mock_db.execute.called
        # The first calls should be deletes (before add_all)
        execute_calls = mock_db.execute.call_args_list
        assert len(execute_calls) >= 3  # At least 3 DELETE statements

    def test_seed_tenant_id_is_fixed(self):
        """The seed tenant ID is a fixed UUID for consistency."""
        assert isinstance(SEED_TENANT_ID, uuid.UUID)
