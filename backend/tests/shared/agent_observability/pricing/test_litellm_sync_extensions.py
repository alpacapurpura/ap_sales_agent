"""T-2 — extensions to litellm_sync.py: yaml cross-check + upstream drift detection.

Per `04-tickets.yaml` T-2 acceptance criteria A1-A4:
  A1: ``make sync-pricing`` exit 0 on happy path (smoke).
  A2: ``make sync-pricing`` exit 1 when upstream URL unreachable (httpx ConnectError).
  A3: yaml lists model not in ``litellm.model_cost`` registry → structlog warn
      ``pricing_sync.config_yaml_model_unknown_to_litellm``.
  A4: snapshot row diverges from upstream JSON entry by > 0.0001 USD → structlog
      warn ``pricing_sync.upstream_drift_detected`` with ``delta_usd`` field.

The Makefile target ``sync-pricing`` invokes ``sync_litellm_pricing`` (ARQ task) as a
synchronous one-shot for CI / local debug. Exit codes:
  - 0 = success (rows added/updated logged)
  - 1 = upstream connection failure / parse error / SQL exception
  - 2 = reserved (currently unused, kept for future "drift hard-fail" mode)

The TTL ETag short-circuit (304 Not Modified) is preserved (already covered by
``test_litellm_sync.py::test_second_run_with_unchanged_payload_is_noop``); this file
focuses on the 4 NEW behaviours T-2 introduces.
"""

from __future__ import annotations

import asyncio
from decimal import Decimal
from pathlib import Path
from unittest.mock import MagicMock, patch
from uuid import uuid4

import httpx
import pytest
from sqlalchemy.orm import sessionmaker
from structlog.testing import capture_logs


@pytest.fixture
def db(db_engine):
    """Per-test transactional session — rolled back at teardown."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(autocommit=False, autoflush=False, bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()


def _http_response(payload: dict, etag: str = "etag-001"):
    """Build a minimal httpx-like response."""
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = payload
    response.headers = {"ETag": etag}
    response.raise_for_status = MagicMock()
    return response


_UPSTREAM_PAYLOAD = {
    "sample_spec": {"litellm_provider": "openai"},  # template — must be skipped
    "gpt-4o-mini": {
        "input_cost_per_token": 0.000000150,
        "output_cost_per_token": 0.000000600,
        "litellm_provider": "openai",
        "mode": "chat",
    },
    "deepseek/deepseek-v4-flash": {
        "input_cost_per_token": 0.0000001,
        "output_cost_per_token": 0.0000003,
        "litellm_provider": "deepseek",
        "mode": "chat",
    },
}


# ──────────────────────────────────────────────────────────────────────────────
# A3 — config yaml cross-check warns on unknown-to-litellm model
# ──────────────────────────────────────────────────────────────────────────────


class TestConfigYamlCrossCheck:
    def test_yaml_model_unknown_to_litellm_emits_warning(self, db, tmp_path: Path) -> None:
        """A3 — yaml lists a model that is NOT in ``litellm.model_cost`` → warn."""
        from src.shared.agent_observability.pricing.litellm_sync import sync_pricing

        # Fixture yaml with one known model + one bogus model (NOT in litellm registry).
        yaml_path = tmp_path / "litellm_config.yaml"
        yaml_path.write_text(
            """
model_list:
  - model_name: openai/gpt-4o-mini
    litellm_params:
      model: openai/gpt-4o-mini
  - model_name: bogus/nonexistent-model-xyz
    litellm_params:
      model: bogus/nonexistent-model-xyz
""",
            encoding="utf-8",
        )

        client = MagicMock()
        client.get.return_value = _http_response(_UPSTREAM_PAYLOAD)

        with capture_logs() as logs:
            result = sync_pricing(db, http_client=client, config_yaml_path=yaml_path)
            db.flush()

        # Result surfaces config_yaml_warnings count.
        assert result.config_yaml_warnings == 1, "Expected 1 unknown-to-litellm warning for bogus/nonexistent-model-xyz"
        assert "bogus/nonexistent-model-xyz" in result.unknown_yaml_models
        # And structlog emitted the canonical event name.
        warns = [log for log in logs if log.get("event") == "pricing_sync.config_yaml_model_unknown_to_litellm"]
        assert len(warns) == 1, (
            f"Expected 1 'pricing_sync.config_yaml_model_unknown_to_litellm'; got {len(warns)}: {logs}"
        )
        assert warns[0].get("model") == "bogus/nonexistent-model-xyz"
        assert warns[0].get("log_level") == "warning"

    def test_yaml_missing_path_skipped_silently(self, db, tmp_path: Path) -> None:
        """When ``config_yaml_path`` does not exist, sync still succeeds (best-effort).

        Graceful degradation: the cross-check is opt-in. Missing yaml emits a single
        info log and the sync proceeds normally without warnings.
        """
        from src.shared.agent_observability.pricing.litellm_sync import sync_pricing

        client = MagicMock()
        client.get.return_value = _http_response(_UPSTREAM_PAYLOAD)
        nonexistent = tmp_path / "does_not_exist.yaml"

        result = sync_pricing(db, http_client=client, config_yaml_path=nonexistent)
        db.flush()

        # 0 warnings (yaml not read).
        assert result.config_yaml_warnings == 0
        # Sync still ran.
        assert result.rows_added == 2  # gpt-4o-mini + deepseek/deepseek-v4-flash


# ──────────────────────────────────────────────────────────────────────────────
# A4 — upstream drift detection (snapshot vs upstream divergence)
# ──────────────────────────────────────────────────────────────────────────────


class TestUpstreamDriftDetection:
    def test_snapshot_diverges_from_upstream_warns(self, db) -> None:
        """A4 — pre-existing snapshot row whose price differs from upstream by
        more than the drift threshold → structlog warn + result.drift_warnings += 1.
        """
        import datetime as dt

        from src.shared.agent_observability.persistence.models.pricing_snapshot_model import (
            ModelPricingSnapshotModel,
        )
        from src.shared.agent_observability.pricing.litellm_sync import sync_pricing

        # Seed: snapshot row for a model whose seeded price differs from upstream
        # by MORE than UPSTREAM_DRIFT_THRESHOLD_USD (0.0001 USD/token).
        # Use input_cost=0.001 vs upstream 0.000000150 → delta ~0.001 (>>0.0001).
        seeded = ModelPricingSnapshotModel(
            id=uuid4(),
            provider="openai",
            model="gpt-4o-mini",
            input_cost_per_token=Decimal("0.001000000"),
            output_cost_per_token=Decimal("0.004000000"),
            source="litellm",
            valid_from=dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.UTC),
            valid_to=None,
            raw_payload={},
        )
        db.add(seeded)
        db.flush()

        client = MagicMock()
        client.get.return_value = _http_response(_UPSTREAM_PAYLOAD)

        with capture_logs() as logs:
            result = sync_pricing(db, http_client=client)
            db.flush()

        # Drift detected ≥ 1 (input_cost diverged for gpt-4o-mini).
        assert result.drift_warnings >= 1, f"Expected drift_warnings >= 1; got {result.drift_warnings}"
        warns = [log for log in logs if log.get("event") == "pricing_sync.upstream_drift_detected"]
        assert len(warns) >= 1, f"Expected ≥1 drift warn; got {logs}"
        # Drift event surfaces the diverged model + delta + threshold.
        assert any(w.get("model") == "gpt-4o-mini" for w in warns)
        assert all(w.get("threshold_usd") for w in warns)
        assert all("delta_input_usd" in w for w in warns)
        # And the close-and-replace path still ran (rows_added=2 + rows_updated=1).
        assert result.rows_updated == 1

    def test_snapshot_within_threshold_no_drift_warn(self, db) -> None:
        """When snapshot matches upstream within threshold, no drift warn fires.

        Tiny delta below UPSTREAM_DRIFT_THRESHOLD_USD (0.0001) on a single token.
        Upstream input_cost = 0.000000150; seed at 0.000000200 → delta 5e-8 < 1e-4.
        """
        import datetime as dt

        from src.shared.agent_observability.persistence.models.pricing_snapshot_model import (
            ModelPricingSnapshotModel,
        )
        from src.shared.agent_observability.pricing.litellm_sync import sync_pricing

        seeded = ModelPricingSnapshotModel(
            id=uuid4(),
            provider="openai",
            model="gpt-4o-mini",
            input_cost_per_token=Decimal("0.000000200"),  # delta 5e-8 vs upstream 1.5e-7
            output_cost_per_token=Decimal("0.000000700"),  # delta 1e-7 vs upstream 6e-7
            source="litellm",
            valid_from=dt.datetime(2026, 1, 1, 0, 0, tzinfo=dt.UTC),
            valid_to=None,
            raw_payload={},
        )
        db.add(seeded)
        db.flush()

        client = MagicMock()
        client.get.return_value = _http_response(_UPSTREAM_PAYLOAD)

        with capture_logs() as logs:
            result = sync_pricing(db, http_client=client)
            db.flush()

        assert result.drift_warnings == 0, (
            f"Expected drift_warnings=0 when delta < threshold; got {result.drift_warnings}"
        )
        assert not any(log.get("event") == "pricing_sync.upstream_drift_detected" for log in logs)


# ──────────────────────────────────────────────────────────────────────────────
# A2 — make sync-pricing exit 1 on httpx ConnectError
# ──────────────────────────────────────────────────────────────────────────────


class TestMakeSyncPricingExitCodes:
    def test_make_sync_pricing_exit_1_on_connect_error(self) -> None:
        """A2 — httpx.ConnectError during upstream fetch → ARQ task returns
        ``ok=False`` → Makefile target script exits 1.
        """
        from src.shared.agent_observability.workers.pricing_sync_task import (
            sync_litellm_pricing,
        )

        # Patch SessionLocal to a no-op (we don't reach DB before HTTP fails).
        # Patch httpx.Client to raise ConnectError on .get().
        class _BoomClient:
            def __init__(self, *args, **kwargs):
                pass

            def __enter__(self):
                return self

            def __exit__(self, *exc):
                return False

            def get(self, *args, **kwargs):
                err = "upstream unreachable"
                raise httpx.ConnectError(err)

        with (
            patch(
                "src.shared.agent_observability.workers.pricing_sync_task.httpx.Client",
                _BoomClient,
            ),
            patch("src.shared.agent_observability.workers.pricing_sync_task.SessionLocal") as mock_session_local,
        ):
            mock_session = MagicMock()
            mock_session_local.return_value = mock_session
            result = asyncio.run(sync_litellm_pricing({}))

        assert result["ok"] is False, f"Expected ok=False; got {result}"
        assert "error" in result
        # Session should have been rolled back + closed.
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()


# ──────────────────────────────────────────────────────────────────────────────
# Worker task propagates new SyncResult fields to log output
# ──────────────────────────────────────────────────────────────────────────────


class TestWorkerTaskFieldPropagation:
    def test_worker_task_returns_yaml_and_drift_counts(self, db_engine) -> None:
        """SyncResult.config_yaml_warnings + drift_warnings flow to ARQ return dict."""
        from src.shared.agent_observability.pricing.litellm_sync import SyncResult
        from src.shared.agent_observability.workers import pricing_sync_task

        # Patch SessionLocal to return a real session bound to in-memory engine.
        Session = sessionmaker(bind=db_engine)
        session = Session()

        fake_result = SyncResult(
            rows_added=3,
            rows_updated=1,
            rows_skipped=2,
            etag="etag-test",
            config_yaml_warnings=1,
            drift_warnings=2,
        )

        with (
            patch.object(pricing_sync_task, "SessionLocal", return_value=session),
            patch.object(pricing_sync_task, "sync_pricing", return_value=fake_result),
            patch.object(pricing_sync_task, "httpx") as mock_httpx,
        ):
            mock_httpx.Client.return_value.__enter__.return_value = MagicMock()
            mock_httpx.Client.return_value.__exit__.return_value = False

            result = asyncio.run(pricing_sync_task.sync_litellm_pricing({}))

        assert result["ok"] is True
        assert result["rows_added"] == 3
        assert result["rows_updated"] == 1
        assert result["rows_skipped"] == 2
        assert result["config_yaml_warnings"] == 1
        assert result["drift_warnings"] == 2
        session.close()
