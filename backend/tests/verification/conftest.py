"""Shared fixtures for Layer 2 verification tests.

These tests require a real PostgreSQL database with official_metrics data.
They connect to the visionarias_postgres container via DATABASE_URL.

Run: cd backend && .venv/bin/pytest tests/verification/ -m verify -x -q
"""

import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/visionarias_logs",
)
TENANT_ID = os.environ.get("VERIFY_TENANT_ID") or os.environ.get("E2E_TENANT_ID")
BACKEND_URL = os.environ.get("VERIFY_BACKEND_URL", "http://localhost:8000")


@pytest.fixture(scope="session")
def db_engine():
    engine = create_engine(DATABASE_URL)
    try:
        with engine.connect():
            pass
    except Exception as exc:  # noqa: BLE001 — surface any DB connectivity failure as skip
        engine.dispose()
        pytest.skip(
            f"DATABASE_URL not reachable for verify suite ({exc.__class__.__name__}); "
            "set DATABASE_URL env var to a tenant DB to run Layer 2 verification.",
            allow_module_level=False,
        )
    yield engine
    engine.dispose()


@pytest.fixture()
def db_session(db_engine):
    with Session(db_engine) as session:
        yield session


@pytest.fixture(scope="session")
def tenant_id():
    if not TENANT_ID:
        pytest.skip("VERIFY_TENANT_ID or E2E_TENANT_ID env var not set")
    return TENANT_ID


@pytest.fixture(scope="session")
def backend_url():
    return BACKEND_URL
