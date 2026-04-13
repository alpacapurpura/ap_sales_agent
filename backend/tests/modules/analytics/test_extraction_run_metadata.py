"""Tests for ExtractionRunRepository period metadata.

Every extraction run MUST record ``period_start``, ``period_end`` and
``extraction_type`` so operators can audit what date range each run
actually covered. Previously these columns existed on the model but
were never populated on create, making audits impossible.
"""

from datetime import date
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from src.modules.analytics.infrastructure.repositories.extraction_run_repository import (
    ExtractionRunRepository,
)


class TestExtractionRunMetadata:
    def test_create_records_period_start_and_period_end(self, db: Session):
        tenant_id = uuid4()
        repo = ExtractionRunRepository(db)

        run = repo.create(
            tenant_id=tenant_id,
            provider="meta",
            period_start=date(2026, 4, 1),
            period_end=date(2026, 4, 8),
            extraction_type="scheduled",
        )

        assert run.period_start == date(2026, 4, 1)
        assert run.period_end == date(2026, 4, 8)
        assert run.extraction_type == "scheduled"
        assert run.tenant_id == tenant_id
        assert run.provider == "meta"

    def test_create_without_period_metadata_is_backwards_compatible(self, db: Session):
        """Callers that don't pass period metadata still succeed (legacy paths)."""
        tenant_id = uuid4()
        repo = ExtractionRunRepository(db)

        run = repo.create(tenant_id=tenant_id, provider="meta")

        assert run.period_start is None
        assert run.period_end is None
        # DB server_default kicks in — value may be None on the in-memory
        # instance until flush. Don't assert extraction_type here.

    def test_create_records_initial_load_type(self, db: Session):
        tenant_id = uuid4()
        repo = ExtractionRunRepository(db)

        run = repo.create(
            tenant_id=tenant_id,
            provider="shopify",
            period_start=date(2026, 3, 1),
            period_end=date(2026, 3, 31),
            extraction_type="initial_load",
        )

        assert run.extraction_type == "initial_load"


@pytest.fixture
def db():
    """In-memory SQLite session scoped to the analytics models."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    from src.modules.analytics.infrastructure.models.extraction_run_model import (
        ExtractionRunModel,
    )
    from src.shared.domain.base_entity import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
