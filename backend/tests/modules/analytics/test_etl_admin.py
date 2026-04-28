"""Tests for ETL admin API endpoints."""

import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

TENANT_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))
RUN_ID = str(uuid.UUID("22222222-2222-2222-2222-222222222222"))


def _make_run(**kwargs):
    run = MagicMock()
    run.id = uuid.UUID(RUN_ID)
    run.tenant_id = uuid.UUID(TENANT_ID)
    run.provider = "meta"
    run.status = "success"
    run.error = None
    run.completed_at = datetime(2026, 3, 1, tzinfo=UTC)
    run.created_at = datetime(2026, 3, 1, tzinfo=UTC)
    run.metrics_count = 50
    run.sub_extractor_failures = []
    for k, v in kwargs.items():
        setattr(run, k, v)
    return run


def _make_app(db_mock):
    from src.core.database import get_db
    from src.modules.analytics.api.etl_admin import health_router, tenant_router

    app = FastAPI()
    app.include_router(health_router)
    app.include_router(tenant_router)
    app.dependency_overrides[get_db] = lambda: db_mock
    return app


# ─── GET /health/etl ─────────────────────────────────────────────────────────


class TestGetEtlHealth:
    def _db(self, last_success=None, pending_count=0, failed_runs=None):
        db = MagicMock()
        # scalar_one_or_none for last_success
        db.execute.return_value.scalar_one_or_none.return_value = last_success
        # scalar_one for pending count
        db.execute.return_value.scalar_one.return_value = pending_count
        # scalars().all() for failed runs
        db.execute.return_value.scalars.return_value.all.return_value = failed_runs or []
        return db

    def test_returns_200_empty(self):
        db = self._db()
        # Need sequential returns for different execute calls
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(scalar_one=MagicMock(return_value=0)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]
        call_count = [0]

        def side_effect(*args, **kwargs):
            r = results[min(call_count[0], len(results) - 1)]
            call_count[0] += 1
            return r

        db.execute.side_effect = side_effect

        app = _make_app(db)
        client = TestClient(app)
        resp = client.get("/health/etl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pending_tenants"] == 0
        assert data["active_failures"] == []
        assert "timestamp" in data

    def test_returns_last_success_and_failures(self):
        run = _make_run(status="failed", error="Token expired", provider="shopify")
        ts = datetime(2026, 3, 15, tzinfo=UTC)
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=ts)),
            MagicMock(scalar_one=MagicMock(return_value=2)),
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[run])))),
        ]
        call_count = [0]

        def side_effect(*args, **kwargs):
            r = results[min(call_count[0], len(results) - 1)]
            call_count[0] += 1
            return r

        db = MagicMock()
        db.execute.side_effect = side_effect

        app = _make_app(db)
        client = TestClient(app)
        resp = client.get("/health/etl")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pending_tenants"] == 2
        assert len(data["active_failures"]) == 1
        assert data["active_failures"][0]["provider"] == "shopify"
        assert data["active_failures"][0]["error"] == "Token expired"

    def test_pending_count_none_becomes_zero(self):
        results = [
            MagicMock(scalar_one_or_none=MagicMock(return_value=None)),
            MagicMock(scalar_one=MagicMock(return_value=None)),  # DB returns None
            MagicMock(scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))),
        ]
        call_count = [0]

        def side_effect(*args, **kwargs):
            r = results[min(call_count[0], len(results) - 1)]
            call_count[0] += 1
            return r

        db = MagicMock()
        db.execute.side_effect = side_effect

        app = _make_app(db)
        client = TestClient(app)
        resp = client.get("/health/etl")
        assert resp.status_code == 200
        assert resp.json()["pending_tenants"] == 0


# ─── GET /etl/status ─────────────────────────────────────────────────────────


class TestGetEtlStatus:
    def test_returns_empty_when_no_runs(self):
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = []
        app = _make_app(db)
        client = TestClient(app)
        resp = client.get("/etl/status", headers={"X-Tenant-ID": TENANT_ID})
        assert resp.status_code == 200
        data = resp.json()
        assert data["tenant_id"] == TENANT_ID
        assert data["extractions"] == []

    def test_returns_extraction_items_per_provider(self):
        run = _make_run(status="success", provider="meta", metrics_count=100, sub_extractor_failures=[])
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [run]
        app = _make_app(db)
        client = TestClient(app)
        resp = client.get("/etl/status", headers={"X-Tenant-ID": TENANT_ID})
        assert resp.status_code == 200
        exts = resp.json()["extractions"]
        assert len(exts) == 1
        assert exts[0]["provider"] == "meta"
        assert exts[0]["metrics_count"] == 100
        assert exts[0]["error"] is None  # success → no error

    def test_failed_run_includes_error(self):
        run = _make_run(status="failed", error="Auth failed", provider="google_analytics")
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [run]
        app = _make_app(db)
        client = TestClient(app)
        resp = client.get("/etl/status", headers={"X-Tenant-ID": TENANT_ID})
        assert resp.status_code == 200
        exts = resp.json()["extractions"]
        assert exts[0]["error"] == "Auth failed"

    def test_sub_extractor_failures_included(self):
        sub_failures = [
            {"extractor_name": "campaigns", "error": "timeout", "error_type": "TimeoutError"},
        ]
        run = _make_run(status="partial", sub_extractor_failures=sub_failures)
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [run]
        app = _make_app(db)
        client = TestClient(app)
        resp = client.get("/etl/status", headers={"X-Tenant-ID": TENANT_ID})
        assert resp.status_code == 200
        exts = resp.json()["extractions"]
        assert len(exts[0]["sub_extractor_failures"]) == 1
        assert exts[0]["sub_extractor_failures"][0]["extractor_name"] == "campaigns"

    def test_completed_at_none_falls_back_to_created_at(self):
        run = _make_run(status="running")
        run.completed_at = None
        run.created_at = datetime(2026, 3, 20, tzinfo=UTC)
        db = MagicMock()
        db.execute.return_value.scalars.return_value.all.return_value = [run]
        app = _make_app(db)
        client = TestClient(app)
        resp = client.get("/etl/status", headers={"X-Tenant-ID": TENANT_ID})
        assert resp.status_code == 200
        assert resp.json()["extractions"][0]["last_updated"] is not None

    def test_missing_tenant_id_header_returns_422(self):
        db = MagicMock()
        app = _make_app(db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/etl/status")
        assert resp.status_code == 422


# ─── POST /etl/retry/{run_id} ─────────────────────────────────────────────────


class TestRetryExtraction:
    def _db_with_run(self, run=None, recent=None):
        db = MagicMock()
        call_count = [0]
        results = [
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=run)))),
            MagicMock(scalars=MagicMock(return_value=MagicMock(first=MagicMock(return_value=recent)))),
        ]

        def side_effect(*args, **kwargs):
            r = results[min(call_count[0], len(results) - 1)]
            call_count[0] += 1
            return r

        db.execute.side_effect = side_effect
        return db

    def test_run_not_found_returns_404(self):
        db = self._db_with_run(run=None)
        app = _make_app(db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/etl/retry/{RUN_ID}",
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 404

    def test_cooldown_active_returns_429(self):
        run = _make_run()
        recent = _make_run()  # recent = another run within cooldown
        db = self._db_with_run(run=run, recent=recent)
        app = _make_app(db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(
            f"/etl/retry/{RUN_ID}",
            headers={"X-Tenant-ID": TENANT_ID},
        )
        assert resp.status_code == 429

    def test_successful_retry_enqueues_job(self):
        run = _make_run()
        db = self._db_with_run(run=run, recent=None)
        app = _make_app(db)
        client = TestClient(app, raise_server_exceptions=False)

        pool_mock = AsyncMock()
        pool_mock.enqueue_job = AsyncMock()
        pool_mock.close = AsyncMock()

        with patch("arq.connections.create_pool", AsyncMock(return_value=pool_mock)):
            resp = client.post(
                f"/etl/retry/{RUN_ID}",
                headers={"X-Tenant-ID": TENANT_ID},
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "queued"
        assert data["run_id"] == RUN_ID

    def test_arq_failure_returns_500(self):
        run = _make_run()
        db = self._db_with_run(run=run, recent=None)
        app = _make_app(db)
        client = TestClient(app, raise_server_exceptions=False)

        with patch("arq.connections.create_pool", AsyncMock(side_effect=RuntimeError("redis down"))):
            resp = client.post(
                f"/etl/retry/{RUN_ID}",
                headers={"X-Tenant-ID": TENANT_ID},
            )

        assert resp.status_code == 500

    def test_missing_tenant_header_returns_422(self):
        db = MagicMock()
        app = _make_app(db)
        client = TestClient(app, raise_server_exceptions=False)
        resp = client.post(f"/etl/retry/{RUN_ID}")
        assert resp.status_code == 422
