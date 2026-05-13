"""Tests for the LiteLLM pricing sync worker.

Mocks ``httpx`` so we never hit the network in unit tests. Verifies the
diff: insert new snapshots, close changed ones, leave equivalent ones
untouched. Uses an in-memory SQLite session via the global ``db_engine``
fixture.
"""

from __future__ import annotations

import datetime as dt
from decimal import Decimal
from unittest.mock import MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.orm import sessionmaker


@pytest.fixture
def db(db_engine):
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


SAMPLE_LITELLM_JSON = {
    "sample_spec": {"litellm_provider": "openai"},  # template — must be skipped
    "gpt-4o": {
        "input_cost_per_token": 0.0000025,
        "output_cost_per_token": 0.000010,
        "cache_read_input_token_cost": 0.00000125,
        "cache_creation_input_token_cost": 0,
        "litellm_provider": "openai",
        "mode": "chat",
    },
    "claude-3-5-sonnet-20241022": {
        "input_cost_per_token": 0.000003,
        "output_cost_per_token": 0.000015,
        "cache_read_input_token_cost": 0.0000003,
        "cache_creation_input_token_cost": 0.00000375,
        "litellm_provider": "anthropic",
        "mode": "chat",
    },
    "dall-e-3": {  # image — must be skipped (mode != chat)
        "output_cost_per_image": 0.04,
        "litellm_provider": "openai",
        "mode": "image_generation",
    },
}


def _http_response(payload, etag="etag-001"):
    """Build a minimal httpx-like response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload
    response.headers = {"ETag": etag}
    response.raise_for_status = MagicMock()
    return response


class TestLitellmSync:
    def test_initial_run_inserts_chat_models_only(self, db) -> None:
        from luana_core_observability.persistence.models.pricing_snapshot_model import (
            ModelPricingSnapshotModel,
        )
        from luana_core_observability.pricing.litellm_sync import sync_pricing

        client = MagicMock()
        client.get.return_value = _http_response(SAMPLE_LITELLM_JSON)

        result = sync_pricing(db, http_client=client)
        db.flush()

        rows = db.query(ModelPricingSnapshotModel).all()
        # gpt-4o + claude-3-5-sonnet (image and sample_spec skipped).
        assert len(rows) == 2
        assert {(r.provider, r.model) for r in rows} == {
            ("openai", "gpt-4o"),
            ("anthropic", "claude-3-5-sonnet-20241022"),
        }
        assert all(r.valid_to is None for r in rows)
        assert result.rows_added == 2
        assert result.rows_updated == 0

    def test_second_run_with_unchanged_payload_is_noop(self, db) -> None:
        from luana_core_observability.persistence.models.pricing_snapshot_model import (
            ModelPricingSnapshotModel,
        )
        from luana_core_observability.pricing.litellm_sync import sync_pricing

        client = MagicMock()
        client.get.return_value = _http_response(SAMPLE_LITELLM_JSON, etag="etag-001")

        sync_pricing(db, http_client=client)
        db.flush()
        first_count = db.query(ModelPricingSnapshotModel).count()

        # Same etag → ETag short-circuit OR same content → diff nothing.
        result = sync_pricing(db, http_client=client)
        db.flush()
        second_count = db.query(ModelPricingSnapshotModel).count()
        assert second_count == first_count
        assert result.rows_added == 0
        assert result.rows_updated == 0

    def test_price_change_closes_old_inserts_new(self, db) -> None:
        from luana_core_observability.persistence.models.pricing_snapshot_model import (
            ModelPricingSnapshotModel,
        )
        from luana_core_observability.pricing.litellm_sync import sync_pricing

        # Seed with one active snapshot for gpt-4o at older price.
        seeded = ModelPricingSnapshotModel(
            id=uuid4(),
            provider="openai",
            model="gpt-4o",
            input_cost_per_token=Decimal("0.000005"),  # was 5e-6, now 2.5e-6
            output_cost_per_token=Decimal("0.000020"),
            source="litellm",
            valid_from=dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.UTC),
            valid_to=None,
            raw_payload={},
        )
        db.add(seeded)
        db.flush()

        # New payload — only gpt-4o, with the lower published price.
        new_payload = {
            "gpt-4o": {
                "input_cost_per_token": 0.0000025,
                "output_cost_per_token": 0.000010,
                "litellm_provider": "openai",
                "mode": "chat",
            },
        }
        client = MagicMock()
        client.get.return_value = _http_response(new_payload, etag="etag-002")

        result = sync_pricing(db, http_client=client)
        db.flush()

        # Old row should now be closed; new row should be active.
        rows = (
            db.query(ModelPricingSnapshotModel)
            .filter_by(provider="openai", model="gpt-4o")
            .order_by(ModelPricingSnapshotModel.valid_from.asc())
            .all()
        )
        assert len(rows) == 2
        assert rows[0].valid_to is not None  # closed
        assert rows[1].valid_to is None  # active
        assert rows[1].input_cost_per_token == Decimal("0.0000025")
        assert result.rows_added == 1
        assert result.rows_updated == 1
