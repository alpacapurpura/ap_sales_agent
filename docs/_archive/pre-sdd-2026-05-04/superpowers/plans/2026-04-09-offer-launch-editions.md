# Offer Launch Editions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `LaunchEdition` child entity to Offer so programs, events, and services can have multiple launches with their own dates and optional pricing overrides.

**Architecture:** New `LaunchEdition` entity within the `offer` bounded context (same DDD module). One-to-many relationship with `Offer`. Pricing override is nullable — null means inherit from parent offer. Frontend gets a new "Ediciones" section in the offer editor NavRail, visible only for applicable archetypes.

**Tech Stack:** FastAPI, SQLAlchemy 2.0 (sync Session), Pydantic v2, Alembic (idempotent raw SQL), React 18, TypeScript, Tanstack React Query, Shadcn UI, Zod.

**Spec:** `docs/superpowers/specs/2026-04-09-offer-launch-editions-design.md`

---

## File Map

### Backend — New Files
| File | Purpose |
|------|---------|
| `backend/src/modules/offer/domain/launch_edition.py` | Domain entity + enum + DTOs |
| `backend/src/modules/offer/infrastructure/models/launch_edition_model.py` | SQLAlchemy model |
| `backend/src/modules/offer/infrastructure/repositories/launch_edition_repository.py` | CRUD repo |
| `backend/src/modules/offer/application/launch_edition_service.py` | Business logic |
| `backend/src/modules/offer/api/launch_editions.py` | FastAPI router |
| `backend/tests/modules/offer/test_launch_edition_domain.py` | Domain entity tests |
| `backend/tests/modules/offer/test_launch_edition_repository.py` | Repository tests |
| `backend/tests/modules/offer/test_launch_edition_service.py` | Service tests |
| `backend/tests/modules/offer/test_launch_edition_api.py` | API endpoint tests |

### Backend — Modified Files
| File | Change |
|------|--------|
| `backend/src/main.py` | Register launch_editions router |

### Frontend — New Files
| File | Purpose |
|------|---------|
| `frontend/src/features/offer-studio/api/editions-api.ts` | API client for editions CRUD |
| `frontend/src/features/offer-studio/hooks/use-editions.ts` | React Query hook |
| `frontend/src/features/offer-studio/components/editions/EditionsSection.tsx` | Main section (list + header) |
| `frontend/src/features/offer-studio/components/editions/EditionCard.tsx` | Single edition card |
| `frontend/src/features/offer-studio/components/editions/EditionFormDialog.tsx` | Create/edit dialog |
| `frontend/src/features/offer-studio/components/editions/EditionPricingOverride.tsx` | Pricing toggle + form |
| `frontend/src/features/offer-studio/components/editions/EditionStatusBadge.tsx` | Status pill component |

### Frontend — Modified Files
| File | Change |
|------|--------|
| `frontend/src/features/offer-studio/types/index.ts` | Add `EditionStatus` enum + `LaunchEdition` type |
| `frontend/src/features/offer-studio/config/offer-builder-config.ts` | Add `editions` to `SECTION_REGISTRY` + `ARCHETYPE_BUILDER_CONFIG` |

### Migration
| File | Purpose |
|------|---------|
| Alembic migration (auto-generated path) | `CREATE TABLE IF NOT EXISTS launch_editions` |

---

## Task 1: Domain Entity + Enum

**Files:**
- Create: `backend/src/modules/offer/domain/launch_edition.py`
- Test: `backend/tests/modules/offer/test_launch_edition_domain.py`

- [ ] **Step 1: Write failing tests for LaunchEdition domain**

Create `backend/tests/modules/offer/test_launch_edition_domain.py`:

```python
"""Tests for LaunchEdition domain entity."""

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from src.modules.offer.domain.launch_edition import (
    EditionStatus,
    LaunchEdition,
    LaunchEditionCreate,
    LaunchEditionUpdate,
)
from src.modules.offer.domain.offer import PricingStructure


class TestEditionStatus:
    def test_all_values_exist(self):
        assert EditionStatus.DRAFT == "draft"
        assert EditionStatus.UPCOMING == "upcoming"
        assert EditionStatus.ACTIVE == "active"
        assert EditionStatus.COMPLETED == "completed"
        assert EditionStatus.CANCELLED == "cancelled"


class TestLaunchEdition:
    def test_create_minimal(self):
        edition = LaunchEdition(
            offer_id=uuid4(),
            tenant_id=uuid4(),
            edition_name="Cohorte #1",
            edition_number=1,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.status == EditionStatus.DRAFT
        assert edition.pricing_override is None
        assert edition.capacity is None
        assert edition.enrollment_count == 0

    def test_create_with_pricing_override(self):
        pricing = [
            PricingStructure(label="Early Bird", total_amount=397.0),
        ]
        edition = LaunchEdition(
            offer_id=uuid4(),
            tenant_id=uuid4(),
            edition_name="Cohorte #2",
            edition_number=2,
            start_date=datetime(2026, 10, 7, tzinfo=timezone.utc),
            end_date=datetime(2026, 11, 18, tzinfo=timezone.utc),
            pricing_override=pricing,
            capacity=30,
        )
        assert edition.pricing_override is not None
        assert len(edition.pricing_override) == 1
        assert edition.pricing_override[0].total_amount == 397.0
        assert edition.capacity == 30

    def test_end_date_before_start_raises(self):
        with pytest.raises(ValueError, match="end_date.*before.*start_date"):
            LaunchEdition(
                offer_id=uuid4(),
                tenant_id=uuid4(),
                edition_name="Bad",
                edition_number=1,
                start_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
                end_date=datetime(2026, 9, 1, tzinfo=timezone.utc),
            )

    def test_registration_end_before_start_raises(self):
        with pytest.raises(ValueError, match="registration_end.*before.*registration_start"):
            LaunchEdition(
                offer_id=uuid4(),
                tenant_id=uuid4(),
                edition_name="Bad",
                edition_number=1,
                start_date=datetime(2026, 10, 1, tzinfo=timezone.utc),
                registration_start=datetime(2026, 9, 15, tzinfo=timezone.utc),
                registration_end=datetime(2026, 9, 1, tzinfo=timezone.utc),
            )


class TestLaunchEditionCreate:
    def test_minimal(self):
        dto = LaunchEditionCreate(
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert dto.edition_name is None
        assert dto.pricing_override is None

    def test_with_all_fields(self):
        dto = LaunchEditionCreate(
            edition_name="Cohorte Especial",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            end_date=datetime(2026, 8, 26, tzinfo=timezone.utc),
            registration_start=datetime(2026, 6, 1, tzinfo=timezone.utc),
            registration_end=datetime(2026, 7, 1, tzinfo=timezone.utc),
            timezone="America/Lima",
            capacity=30,
            notes="Early bird pricing",
        )
        assert dto.edition_name == "Cohorte Especial"
        assert dto.timezone == "America/Lima"


class TestLaunchEditionUpdate:
    def test_all_optional(self):
        dto = LaunchEditionUpdate()
        assert dto.edition_name is None
        assert dto.status is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/test_launch_edition_domain.py -x -q --tb=short
```

Expected: FAIL — `ModuleNotFoundError: No module named 'src.modules.offer.domain.launch_edition'`

- [ ] **Step 3: Implement domain entity**

Create `backend/src/modules/offer/domain/launch_edition.py`:

```python
"""LaunchEdition domain entity — represents one launch of an offer."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import model_validator

from src.modules.offer.domain.offer import PricingStructure
from src.shared.domain.base_entity import BaseEntity


class EditionStatus(str, Enum):
    DRAFT = "draft"
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class LaunchEdition(BaseEntity):
    """One launch/edition of an offer (cohort, event date, workshop run)."""

    id: UUID | None = None
    offer_id: UUID
    tenant_id: UUID

    edition_name: str
    edition_number: int

    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"

    pricing_override: list[PricingStructure] | None = None

    capacity: int | None = None
    enrollment_count: int = 0

    status: EditionStatus = EditionStatus.DRAFT

    location_override: dict[str, Any] | None = None
    notes: str | None = None

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_dates(self):
        if self.end_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if (
            self.registration_start
            and self.registration_end
            and self.registration_end < self.registration_start
        ):
            raise ValueError(
                "registration_end cannot be before registration_start"
            )
        return self


class LaunchEditionCreate(BaseEntity):
    """DTO for creating a new edition."""

    edition_name: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"
    pricing_override: list[PricingStructure] | None = None
    capacity: int | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None


class LaunchEditionUpdate(BaseEntity):
    """DTO for patching an edition (all fields optional)."""

    edition_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str | None = None
    pricing_override: list[PricingStructure] | None = None
    capacity: int | None = None
    enrollment_count: int | None = None
    status: EditionStatus | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/test_launch_edition_domain.py -x -q --tb=short
```

Expected: all 8 tests PASS.

- [ ] **Step 5: Lint**

```bash
cd backend && .venv/bin/ruff check src/modules/offer/domain/launch_edition.py tests/modules/offer/test_launch_edition_domain.py --no-cache
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/offer/domain/launch_edition.py backend/tests/modules/offer/test_launch_edition_domain.py
git commit -m "feat(offer): add LaunchEdition domain entity with EditionStatus enum"
```

---

## Task 2: SQLAlchemy Model + Alembic Migration

**Files:**
- Create: `backend/src/modules/offer/infrastructure/models/launch_edition_model.py`
- Migration: auto-generated Alembic file

- [ ] **Step 1: Create SQLAlchemy model**

Create `backend/src/modules/offer/infrastructure/models/launch_edition_model.py`:

```python
"""SQLAlchemy model for launch_editions table."""

import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from src.shared.domain.base_entity import Base


class LaunchEditionModel(Base):
    __tablename__ = "launch_editions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(
        UUID(as_uuid=True), ForeignKey("products.id"), nullable=False
    )
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    edition_name = Column(String, nullable=False)
    edition_number = Column(Integer, nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    registration_start = Column(DateTime(timezone=True), nullable=True)
    registration_end = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String, default="UTC")

    pricing_override = Column(JSONB, nullable=True)
    capacity = Column(Integer, nullable=True)
    enrollment_count = Column(Integer, default=0)

    status = Column(String, default="draft")
    location_override = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

- [ ] **Step 2: Run existing tests to verify no breakage**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/ -x -q --tb=short
```

Expected: all existing offer tests PASS (the new model registers with Base.metadata but doesn't break anything).

- [ ] **Step 3: Create idempotent Alembic migration**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic revision --autogenerate -m 'add launch_editions table'"
```

Then **replace** the generated `upgrade()` and `downgrade()` functions with raw SQL:

```python
def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS launch_editions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            offer_id UUID NOT NULL REFERENCES products(id),
            tenant_id UUID NOT NULL,
            edition_name VARCHAR NOT NULL,
            edition_number INTEGER NOT NULL,
            start_date TIMESTAMPTZ NOT NULL,
            end_date TIMESTAMPTZ,
            registration_start TIMESTAMPTZ,
            registration_end TIMESTAMPTZ,
            timezone VARCHAR DEFAULT 'UTC',
            pricing_override JSONB,
            capacity INTEGER,
            enrollment_count INTEGER DEFAULT 0,
            status VARCHAR DEFAULT 'draft',
            location_override JSONB,
            notes TEXT,
            created_at TIMESTAMPTZ DEFAULT NOW(),
            updated_at TIMESTAMPTZ DEFAULT NOW(),
            CONSTRAINT uq_launch_editions_offer_number UNIQUE (offer_id, edition_number)
        )
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_launch_editions_tenant_offer_status
        ON launch_editions (tenant_id, offer_id, status)
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_launch_editions_tenant_offer_status")
    op.execute("DROP TABLE IF EXISTS launch_editions")
```

- [ ] **Step 4: Apply migration**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && alembic upgrade head"
```

- [ ] **Step 5: Lint**

```bash
cd backend && .venv/bin/ruff check src/modules/offer/infrastructure/models/launch_edition_model.py --no-cache
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/offer/infrastructure/models/launch_edition_model.py backend/alembic/versions/*.py
git commit -m "feat(offer): add launch_editions table with idempotent migration"
```

---

## Task 3: Repository

**Files:**
- Create: `backend/src/modules/offer/infrastructure/repositories/launch_edition_repository.py`
- Test: `backend/tests/modules/offer/test_launch_edition_repository.py`

- [ ] **Step 1: Write failing repository tests**

Create `backend/tests/modules/offer/test_launch_edition_repository.py`:

```python
"""Tests for LaunchEditionRepository CRUD operations."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.modules.offer.domain.launch_edition import EditionStatus, LaunchEdition
from src.modules.offer.infrastructure.models.launch_edition_model import (
    LaunchEditionModel,
)
from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from tests.modules.offer.conftest import TENANT_A, TENANT_B, create_product_model


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    """Helper: create a product and return its id."""
    model = create_product_model(tenant_id, archetype="programa")
    db.add(model)
    db.flush()
    return model.id


class TestCreate:
    def test_create_and_auto_number(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)

        edition = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Cohorte #1",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.id is not None
        assert edition.edition_number == 1
        assert edition.edition_name == "Cohorte #1"
        assert edition.status == EditionStatus.DRAFT

    def test_auto_increment_number(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)

        e1 = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        e2 = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 10, 7, tzinfo=timezone.utc),
        )
        assert e1.edition_number == 1
        assert e2.edition_number == 2

    def test_auto_name_when_none(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)

        edition = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.edition_name == "Edición #1"


class TestGetById:
    def test_found(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        created = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Test",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        found = repo.get_by_id(created.id, tenant_a)
        assert found is not None
        assert found.edition_name == "Test"

    def test_wrong_tenant_returns_none(self, db: Session, tenant_a, tenant_b):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        created = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Test",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert repo.get_by_id(created.id, tenant_b) is None


class TestListByOffer:
    def test_ordered_by_start_date_desc(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Jan",
            start_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Jul",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        editions = repo.list_by_offer(offer_id, tenant_a)
        assert len(editions) == 2
        assert editions[0].edition_name == "Jul"  # newest first

    def test_excludes_cancelled(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        e1 = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 1, 15, tzinfo=timezone.utc),
        )
        repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        # Cancel first one
        repo.update(e1.id, tenant_a, {"status": "cancelled"})
        editions = repo.list_by_offer(offer_id, tenant_a)
        assert len(editions) == 1


class TestUpdate:
    def test_patch_fields(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        created = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Old Name",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        updated = repo.update(created.id, tenant_a, {
            "edition_name": "New Name",
            "capacity": 50,
            "status": "upcoming",
        })
        assert updated.edition_name == "New Name"
        assert updated.capacity == 50
        assert updated.status == EditionStatus.UPCOMING


class TestSoftDelete:
    def test_delete_sets_cancelled(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        created = repo.create(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        repo.soft_delete(created.id, tenant_a)
        edition = repo.get_by_id(created.id, tenant_a)
        assert edition is not None
        assert edition.status == EditionStatus.CANCELLED


class TestGetNextEditionNumber:
    def test_first_edition(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        assert repo.get_next_edition_number(offer_id) == 1

    def test_after_three_editions(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        repo = LaunchEditionRepository(db)
        for _ in range(3):
            repo.create(
                offer_id=offer_id,
                tenant_id=tenant_a,
                start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            )
        assert repo.get_next_edition_number(offer_id) == 4
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/test_launch_edition_repository.py -x -q --tb=short
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement repository**

Create `backend/src/modules/offer/infrastructure/repositories/launch_edition_repository.py`:

```python
"""Repository for LaunchEdition CRUD operations."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from src.modules.offer.domain.launch_edition import (
    EditionStatus,
    LaunchEdition,
)
from src.modules.offer.domain.offer import PricingStructure
from src.modules.offer.infrastructure.models.launch_edition_model import (
    LaunchEditionModel,
)


class LaunchEditionRepository:
    def __init__(self, db: Session):
        self.db = db

    def _to_domain(self, model: LaunchEditionModel) -> LaunchEdition:
        pricing = None
        if model.pricing_override is not None:
            pricing = [
                PricingStructure(**p) for p in model.pricing_override
            ]

        return LaunchEdition(
            id=model.id,
            offer_id=model.offer_id,
            tenant_id=model.tenant_id,
            edition_name=model.edition_name,
            edition_number=model.edition_number,
            start_date=model.start_date,
            end_date=model.end_date,
            registration_start=model.registration_start,
            registration_end=model.registration_end,
            timezone=model.timezone or "UTC",
            pricing_override=pricing,
            capacity=model.capacity,
            enrollment_count=model.enrollment_count or 0,
            status=EditionStatus(model.status) if model.status else EditionStatus.DRAFT,
            location_override=model.location_override,
            notes=model.notes,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )

    def get_next_edition_number(self, offer_id: UUID) -> int:
        stmt = select(func.coalesce(func.max(LaunchEditionModel.edition_number), 0)).where(
            LaunchEditionModel.offer_id == offer_id,
        )
        result = self.db.execute(stmt).scalar()
        return (result or 0) + 1

    def create(
        self,
        offer_id: UUID,
        tenant_id: UUID,
        start_date,
        edition_name: str | None = None,
        end_date=None,
        registration_start=None,
        registration_end=None,
        timezone: str = "UTC",
        pricing_override: list[PricingStructure] | None = None,
        capacity: int | None = None,
        location_override: dict | None = None,
        notes: str | None = None,
    ) -> LaunchEdition:
        edition_number = self.get_next_edition_number(offer_id)
        if not edition_name:
            edition_name = f"Edición #{edition_number}"

        pricing_json = None
        if pricing_override is not None:
            pricing_json = [p.model_dump(mode="json") for p in pricing_override]

        model = LaunchEditionModel(
            offer_id=offer_id,
            tenant_id=tenant_id,
            edition_name=edition_name,
            edition_number=edition_number,
            start_date=start_date,
            end_date=end_date,
            registration_start=registration_start,
            registration_end=registration_end,
            timezone=timezone,
            pricing_override=pricing_json,
            capacity=capacity,
            enrollment_count=0,
            status=EditionStatus.DRAFT.value,
            location_override=location_override,
            notes=notes,
        )
        self.db.add(model)
        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def get_by_id(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition | None:
        stmt = select(LaunchEditionModel).where(
            LaunchEditionModel.id == edition_id,
            LaunchEditionModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        return self._to_domain(model) if model else None

    def list_by_offer(
        self, offer_id: UUID, tenant_id: UUID
    ) -> list[LaunchEdition]:
        stmt = (
            select(LaunchEditionModel)
            .where(
                LaunchEditionModel.offer_id == offer_id,
                LaunchEditionModel.tenant_id == tenant_id,
                LaunchEditionModel.status != EditionStatus.CANCELLED.value,
            )
            .order_by(LaunchEditionModel.start_date.desc())
        )
        models = self.db.execute(stmt).scalars().all()
        return [self._to_domain(m) for m in models]

    def update(
        self, edition_id: UUID, tenant_id: UUID, data: dict
    ) -> LaunchEdition:
        stmt = select(LaunchEditionModel).where(
            LaunchEditionModel.id == edition_id,
            LaunchEditionModel.tenant_id == tenant_id,
        )
        model = self.db.execute(stmt).scalar_one_or_none()
        if not model:
            raise ValueError(f"Edition {edition_id} not found")

        for key, value in data.items():
            if key == "pricing_override" and value is not None:
                if isinstance(value, list) and value and hasattr(value[0], "model_dump"):
                    value = [p.model_dump(mode="json") for p in value]
            if hasattr(model, key):
                setattr(model, key, value)

        self.db.flush()
        self.db.refresh(model)
        return self._to_domain(model)

    def soft_delete(self, edition_id: UUID, tenant_id: UUID) -> None:
        self.update(edition_id, tenant_id, {"status": EditionStatus.CANCELLED.value})
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/test_launch_edition_repository.py -x -q --tb=short
```

Expected: all 9 tests PASS.

- [ ] **Step 5: Lint**

```bash
cd backend && .venv/bin/ruff check src/modules/offer/infrastructure/repositories/launch_edition_repository.py tests/modules/offer/test_launch_edition_repository.py --no-cache
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/offer/infrastructure/repositories/launch_edition_repository.py backend/tests/modules/offer/test_launch_edition_repository.py
git commit -m "feat(offer): add LaunchEditionRepository with CRUD and auto-numbering"
```

---

## Task 4: Application Service

**Files:**
- Create: `backend/src/modules/offer/application/launch_edition_service.py`
- Test: `backend/tests/modules/offer/test_launch_edition_service.py`

- [ ] **Step 1: Write failing service tests**

Create `backend/tests/modules/offer/test_launch_edition_service.py`:

```python
"""Tests for LaunchEditionService business logic."""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from src.modules.offer.application.launch_edition_service import (
    LaunchEditionService,
)
from src.modules.offer.domain.launch_edition import EditionStatus
from src.modules.offer.domain.offer import PricingStructure
from tests.modules.offer.conftest import TENANT_A, create_product_model


def _make_offer(db: Session, tenant_id: uuid.UUID, **kwargs) -> uuid.UUID:
    model = create_product_model(
        tenant_id,
        archetype="programa",
        pricing=[{"label": "Base", "total_amount": 497, "plan_type": "one_time"}],
        currency="USD",
        **kwargs,
    )
    db.add(model)
    db.flush()
    return model.id


class TestCreateEdition:
    def test_create_with_defaults(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.edition_number == 1
        assert edition.edition_name == "Edición #1"
        assert edition.status == EditionStatus.DRAFT

    def test_create_with_custom_name(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Cohorte Especial",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert edition.edition_name == "Cohorte Especial"

    def test_create_for_nonexistent_offer_raises(self, db: Session, tenant_a):
        svc = LaunchEditionService(db)
        with pytest.raises(ValueError, match="not found"):
            svc.create_edition(
                offer_id=uuid.uuid4(),
                tenant_id=tenant_a,
                start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            )


class TestResolveEffectivePricing:
    def test_no_override_returns_offer_pricing(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        pricing, currency = svc.resolve_effective_pricing(edition, tenant_a)
        assert len(pricing) == 1
        assert pricing[0]["total_amount"] == 497
        assert currency == "USD"

    def test_override_returns_edition_pricing(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            pricing_override=[
                PricingStructure(label="Early Bird", total_amount=397),
            ],
        )
        pricing, currency = svc.resolve_effective_pricing(edition, tenant_a)
        assert len(pricing) == 1
        assert pricing[0]["total_amount"] == 397
        assert currency == "USD"


class TestDuplicateEdition:
    def test_duplicate_increments_number(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        original = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            edition_name="Original",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            capacity=30,
        )
        dup = svc.duplicate_edition(original.id, tenant_a)
        assert dup.edition_number == 2
        assert dup.capacity == 30
        assert dup.status == EditionStatus.DRAFT
        assert dup.enrollment_count == 0


class TestListEditions:
    def test_list_returns_non_cancelled(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 1, 1, tzinfo=timezone.utc),
        )
        e2 = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 1, tzinfo=timezone.utc),
        )
        svc.delete_edition(e2.id, tenant_a)
        editions = svc.list_editions(offer_id, tenant_a)
        assert len(editions) == 1
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/test_launch_edition_service.py -x -q --tb=short
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Implement service**

Create `backend/src/modules/offer/application/launch_edition_service.py`:

```python
"""Business logic for managing launch editions."""

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy.orm import Session

from src.modules.offer.domain.launch_edition import LaunchEdition
from src.modules.offer.domain.offer import PricingStructure
from src.modules.offer.infrastructure.repositories.launch_edition_repository import (
    LaunchEditionRepository,
)
from src.modules.offer.infrastructure.repositories.offer_repository import (
    OfferRepository,
)


class LaunchEditionService:
    def __init__(self, db: Session):
        self.db = db
        self.repo = LaunchEditionRepository(db)
        self.offer_repo = OfferRepository(db)

    def create_edition(
        self,
        offer_id: UUID,
        tenant_id: UUID,
        start_date: datetime,
        edition_name: str | None = None,
        end_date: datetime | None = None,
        registration_start: datetime | None = None,
        registration_end: datetime | None = None,
        timezone: str = "UTC",
        pricing_override: list[PricingStructure] | None = None,
        capacity: int | None = None,
        location_override: dict[str, Any] | None = None,
        notes: str | None = None,
    ) -> LaunchEdition:
        offer = self.offer_repo.get_by_id(offer_id, tenant_id)
        if not offer:
            raise ValueError(f"Offer {offer_id} not found")

        return self.repo.create(
            offer_id=offer_id,
            tenant_id=tenant_id,
            edition_name=edition_name,
            start_date=start_date,
            end_date=end_date,
            registration_start=registration_start,
            registration_end=registration_end,
            timezone=timezone,
            pricing_override=pricing_override,
            capacity=capacity,
            location_override=location_override,
            notes=notes,
        )

    def get_edition(self, edition_id: UUID, tenant_id: UUID) -> LaunchEdition | None:
        return self.repo.get_by_id(edition_id, tenant_id)

    def list_editions(self, offer_id: UUID, tenant_id: UUID) -> list[LaunchEdition]:
        return self.repo.list_by_offer(offer_id, tenant_id)

    def update_edition(
        self, edition_id: UUID, tenant_id: UUID, data: dict
    ) -> LaunchEdition:
        return self.repo.update(edition_id, tenant_id, data)

    def delete_edition(self, edition_id: UUID, tenant_id: UUID) -> None:
        self.repo.soft_delete(edition_id, tenant_id)

    def duplicate_edition(
        self, edition_id: UUID, tenant_id: UUID
    ) -> LaunchEdition:
        original = self.repo.get_by_id(edition_id, tenant_id)
        if not original:
            raise ValueError(f"Edition {edition_id} not found")

        return self.repo.create(
            offer_id=original.offer_id,
            tenant_id=tenant_id,
            edition_name=None,  # Auto-generate name
            start_date=original.start_date,
            end_date=original.end_date,
            registration_start=original.registration_start,
            registration_end=original.registration_end,
            timezone=original.timezone,
            pricing_override=original.pricing_override,
            capacity=original.capacity,
            location_override=original.location_override,
            notes=original.notes,
        )

    def resolve_effective_pricing(
        self, edition: LaunchEdition, tenant_id: UUID
    ) -> tuple[list[dict[str, Any]], str]:
        """Return (pricing_list, currency). Uses override if set, else offer's pricing."""
        offer = self.offer_repo.get_by_id(edition.offer_id, tenant_id)
        if not offer:
            raise ValueError(f"Offer {edition.offer_id} not found")

        currency = offer.currency

        if edition.pricing_override is not None:
            return (
                [p.model_dump(mode="json") for p in edition.pricing_override],
                currency,
            )

        return (
            [p.model_dump(mode="json") for p in offer.pricing_options],
            currency,
        )
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/test_launch_edition_service.py -x -q --tb=short
```

Expected: all 7 tests PASS.

- [ ] **Step 5: Lint**

```bash
cd backend && .venv/bin/ruff check src/modules/offer/application/launch_edition_service.py tests/modules/offer/test_launch_edition_service.py --no-cache
```

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/offer/application/launch_edition_service.py backend/tests/modules/offer/test_launch_edition_service.py
git commit -m "feat(offer): add LaunchEditionService with create, duplicate, effective pricing"
```

---

## Task 5: API Endpoints

**Files:**
- Create: `backend/src/modules/offer/api/launch_editions.py`
- Modify: `backend/src/main.py`
- Test: `backend/tests/modules/offer/test_launch_edition_api.py`

- [ ] **Step 1: Write failing API tests**

Create `backend/tests/modules/offer/test_launch_edition_api.py`:

```python
"""Tests for launch_editions API endpoints via direct router calls."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from src.modules.offer.api.launch_editions import (
    LaunchEditionCreateDTO,
    LaunchEditionResponse,
    LaunchEditionUpdateDTO,
)
from src.modules.offer.application.launch_edition_service import (
    LaunchEditionService,
)
from tests.modules.offer.conftest import TENANT_A, create_product_model


def _make_offer(db: Session, tenant_id: uuid.UUID) -> uuid.UUID:
    model = create_product_model(
        tenant_id,
        archetype="programa",
        pricing=[{"label": "Base", "total_amount": 497, "plan_type": "one_time"}],
        currency="USD",
    )
    db.add(model)
    db.flush()
    return model.id


class TestLaunchEditionCreateDTO:
    def test_minimal(self):
        dto = LaunchEditionCreateDTO(
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        assert dto.edition_name is None

    def test_full(self):
        dto = LaunchEditionCreateDTO(
            edition_name="Cohorte #1",
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
            end_date=datetime(2026, 8, 26, tzinfo=timezone.utc),
            timezone="America/Lima",
            capacity=30,
        )
        assert dto.capacity == 30


class TestLaunchEditionResponse:
    def test_from_domain(self, db: Session, tenant_a):
        offer_id = _make_offer(db, tenant_a)
        svc = LaunchEditionService(db)
        edition = svc.create_edition(
            offer_id=offer_id,
            tenant_id=tenant_a,
            start_date=datetime(2026, 7, 15, tzinfo=timezone.utc),
        )
        effective_pricing, currency = svc.resolve_effective_pricing(edition, tenant_a)
        response = LaunchEditionResponse.from_domain(edition, effective_pricing, currency)
        assert response.edition_name == "Edición #1"
        assert response.effective_pricing[0]["total_amount"] == 497
        assert response.currency == "USD"
        assert response.pricing_override is None
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/test_launch_edition_api.py -x -q --tb=short
```

Expected: FAIL — `ModuleNotFoundError`

- [ ] **Step 3: Create API router**

Create `backend/src/modules/offer/api/launch_editions.py`:

```python
"""API endpoints for launch editions (sub-resource of offers)."""

from datetime import datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User
from src.modules.offer.application.launch_edition_service import (
    LaunchEditionService,
)
from src.modules.offer.domain.launch_edition import LaunchEdition

router = APIRouter()


class LaunchEditionCreateDTO(BaseModel):
    edition_name: str | None = None
    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"
    pricing_override: list[dict[str, Any]] | None = None
    capacity: int | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None


class LaunchEditionUpdateDTO(BaseModel):
    edition_name: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str | None = None
    pricing_override: list[dict[str, Any]] | None = None
    capacity: int | None = None
    enrollment_count: int | None = None
    status: str | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None


class LaunchEditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    offer_id: UUID
    edition_name: str
    edition_number: int
    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str
    pricing_override: list[dict[str, Any]] | None = None
    effective_pricing: list[dict[str, Any]]
    currency: str
    capacity: int | None = None
    enrollment_count: int
    status: str
    location_override: dict[str, Any] | None = None
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

    @classmethod
    def from_domain(
        cls,
        edition: LaunchEdition,
        effective_pricing: list[dict[str, Any]],
        currency: str,
    ) -> "LaunchEditionResponse":
        pricing_override = None
        if edition.pricing_override is not None:
            pricing_override = [
                p.model_dump(mode="json") for p in edition.pricing_override
            ]
        return cls(
            id=edition.id,
            offer_id=edition.offer_id,
            edition_name=edition.edition_name,
            edition_number=edition.edition_number,
            start_date=edition.start_date,
            end_date=edition.end_date,
            registration_start=edition.registration_start,
            registration_end=edition.registration_end,
            timezone=edition.timezone,
            pricing_override=pricing_override,
            effective_pricing=effective_pricing,
            currency=currency,
            capacity=edition.capacity,
            enrollment_count=edition.enrollment_count,
            status=edition.status.value if hasattr(edition.status, "value") else edition.status,
            location_override=edition.location_override,
            notes=edition.notes,
            created_at=edition.created_at,
            updated_at=edition.updated_at,
        )


def _build_response(
    svc: LaunchEditionService, edition: LaunchEdition, tenant_id: UUID
) -> LaunchEditionResponse:
    effective_pricing, currency = svc.resolve_effective_pricing(edition, tenant_id)
    return LaunchEditionResponse.from_domain(edition, effective_pricing, currency)


@router.get(
    "/{offer_id}/editions",
    response_model=list[LaunchEditionResponse],
)
async def list_editions(
    offer_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    editions = svc.list_editions(UUID(offer_id), user.tenant_id)
    return [_build_response(svc, e, user.tenant_id) for e in editions]


@router.post(
    "/{offer_id}/editions",
    response_model=LaunchEditionResponse,
    status_code=201,
)
async def create_edition(
    offer_id: str,
    body: LaunchEditionCreateDTO,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    from src.modules.offer.domain.offer import PricingStructure

    pricing = None
    if body.pricing_override is not None:
        pricing = [PricingStructure(**p) for p in body.pricing_override]

    try:
        edition = svc.create_edition(
            offer_id=UUID(offer_id),
            tenant_id=user.tenant_id,
            edition_name=body.edition_name,
            start_date=body.start_date,
            end_date=body.end_date,
            registration_start=body.registration_start,
            registration_end=body.registration_end,
            timezone=body.timezone,
            pricing_override=pricing,
            capacity=body.capacity,
            location_override=body.location_override,
            notes=body.notes,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return _build_response(svc, edition, user.tenant_id)


@router.get(
    "/{offer_id}/editions/{edition_id}",
    response_model=LaunchEditionResponse,
)
async def get_edition(
    offer_id: str,
    edition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    edition = svc.get_edition(UUID(edition_id), user.tenant_id)
    if not edition or str(edition.offer_id) != offer_id:
        raise HTTPException(status_code=404, detail="Edition not found")
    return _build_response(svc, edition, user.tenant_id)


@router.patch(
    "/{offer_id}/editions/{edition_id}",
    response_model=LaunchEditionResponse,
)
async def update_edition(
    offer_id: str,
    edition_id: str,
    body: LaunchEditionUpdateDTO,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    try:
        edition = svc.update_edition(
            UUID(edition_id),
            user.tenant_id,
            body.model_dump(exclude_unset=True),
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Edition not found")
    return _build_response(svc, edition, user.tenant_id)


@router.delete(
    "/{offer_id}/editions/{edition_id}",
    status_code=204,
)
async def delete_edition(
    offer_id: str,
    edition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    svc.delete_edition(UUID(edition_id), user.tenant_id)


@router.post(
    "/{offer_id}/editions/{edition_id}/duplicate",
    response_model=LaunchEditionResponse,
    status_code=201,
)
async def duplicate_edition(
    offer_id: str,
    edition_id: str,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    svc = LaunchEditionService(db)
    try:
        edition = svc.duplicate_edition(UUID(edition_id), user.tenant_id)
    except ValueError:
        raise HTTPException(status_code=404, detail="Edition not found")
    return _build_response(svc, edition, user.tenant_id)
```

- [ ] **Step 4: Register router in main.py**

In `backend/src/main.py`, add the import and router registration after the existing offer routes (after line ~411):

Import at top with other offer imports:
```python
from src.modules.offer.api import launch_editions as offer_launch_editions
```

Registration block:
```python
app.include_router(
    offer_launch_editions.router,
    prefix="/api/v1/offer/products",
    tags=["Offer - Launch Editions"],
    dependencies=[Depends(get_tenant_context)],
)
```

- [ ] **Step 5: Run tests to verify they pass**

```bash
cd backend && .venv/bin/pytest tests/modules/offer/test_launch_edition_api.py -x -q --tb=short
```

Expected: all 3 tests PASS.

- [ ] **Step 6: Run full backend test suite**

```bash
cd backend && .venv/bin/ruff check src/modules/offer/ tests/modules/offer/ --no-cache && .venv/bin/pytest tests/modules/offer/ -x -q --tb=short
```

Expected: ALL tests PASS, zero lint errors.

- [ ] **Step 7: Commit**

```bash
git add backend/src/modules/offer/api/launch_editions.py backend/src/main.py backend/tests/modules/offer/test_launch_edition_api.py
git commit -m "feat(offer): add launch editions API endpoints (CRUD + duplicate)"
```

---

## Task 6: Frontend Types + API Client

**Files:**
- Modify: `frontend/src/features/offer-studio/types/index.ts`
- Create: `frontend/src/features/offer-studio/api/editions-api.ts`
- Create: `frontend/src/features/offer-studio/hooks/use-editions.ts`

- [ ] **Step 1: Add EditionStatus enum and LaunchEdition type**

Add to `frontend/src/features/offer-studio/types/index.ts` (at the end of the enums section, before the interfaces):

```typescript
export enum EditionStatus {
  DRAFT = "draft",
  UPCOMING = "upcoming",
  ACTIVE = "active",
  COMPLETED = "completed",
  CANCELLED = "cancelled",
}

export interface LaunchEdition {
  id: string;
  offer_id: string;
  edition_name: string;
  edition_number: number;
  start_date: string;
  end_date: string | null;
  registration_start: string | null;
  registration_end: string | null;
  timezone: string;
  pricing_override: PricingStructure[] | null;
  effective_pricing: PricingStructure[];
  currency: string;
  capacity: number | null;
  enrollment_count: number;
  status: EditionStatus;
  location_override: Record<string, unknown> | null;
  notes: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface LaunchEditionCreate {
  edition_name?: string;
  start_date: string;
  end_date?: string;
  registration_start?: string;
  registration_end?: string;
  timezone?: string;
  pricing_override?: PricingStructure[];
  capacity?: number;
  location_override?: Record<string, unknown>;
  notes?: string;
}

export interface LaunchEditionUpdate {
  edition_name?: string;
  start_date?: string;
  end_date?: string;
  registration_start?: string;
  registration_end?: string;
  timezone?: string;
  pricing_override?: PricingStructure[] | null;
  capacity?: number;
  enrollment_count?: number;
  status?: EditionStatus;
  location_override?: Record<string, unknown>;
  notes?: string;
}
```

- [ ] **Step 2: Create editions API client**

Create `frontend/src/features/offer-studio/api/editions-api.ts`:

```typescript
import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";
import { LaunchEdition, LaunchEditionCreate, LaunchEditionUpdate } from "../types";

const API_URL = config.api.baseUrl;

export const editionsApi = {
  list: async (offerId: string, token: string): Promise<LaunchEdition[]> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions`,
      { headers: { Authorization: `Bearer ${token}` } }
    );
    if (!res.ok) throw new Error("Failed to list editions");
    return res.json();
  },

  create: async (
    offerId: string,
    data: LaunchEditionCreate,
    token: string
  ): Promise<LaunchEdition> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions`,
      {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      }
    );
    if (!res.ok) throw new Error("Failed to create edition");
    return res.json();
  },

  update: async (
    offerId: string,
    editionId: string,
    data: LaunchEditionUpdate,
    token: string
  ): Promise<LaunchEdition> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions/${editionId}`,
      {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
      }
    );
    if (!res.ok) throw new Error("Failed to update edition");
    return res.json();
  },

  delete: async (
    offerId: string,
    editionId: string,
    token: string
  ): Promise<void> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions/${editionId}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    if (!res.ok) throw new Error("Failed to delete edition");
  },

  duplicate: async (
    offerId: string,
    editionId: string,
    token: string
  ): Promise<LaunchEdition> => {
    const res = await fetchClient(
      `${API_URL}/api/v1/offer/products/${offerId}/editions/${editionId}/duplicate`,
      {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      }
    );
    if (!res.ok) throw new Error("Failed to duplicate edition");
    return res.json();
  },
};
```

- [ ] **Step 3: Create React Query hook**

Create `frontend/src/features/offer-studio/hooks/use-editions.ts`:

```typescript
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { editionsApi } from "../api/editions-api";
import { LaunchEditionCreate, LaunchEditionUpdate } from "../types";

export function useEditions(offerId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const queryKey = ["editions", offerId];

  const { data: editions = [], isLoading, error } = useQuery({
    queryKey,
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.list(offerId, token);
    },
    enabled: !!offerId,
    staleTime: 2 * 60 * 1000,
  });

  const createMutation = useMutation({
    mutationFn: async (data: LaunchEditionCreate) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.create(offerId, data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      toast.success("Edición creada");
    },
    onError: () => toast.error("Error al crear edición"),
  });

  const updateMutation = useMutation({
    mutationFn: async ({
      editionId,
      data,
    }: {
      editionId: string;
      data: LaunchEditionUpdate;
    }) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.update(offerId, editionId, data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      toast.success("Edición actualizada");
    },
    onError: () => toast.error("Error al actualizar edición"),
  });

  const deleteMutation = useMutation({
    mutationFn: async (editionId: string) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.delete(offerId, editionId, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      toast.success("Edición eliminada");
    },
    onError: () => toast.error("Error al eliminar edición"),
  });

  const duplicateMutation = useMutation({
    mutationFn: async (editionId: string) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return editionsApi.duplicate(offerId, editionId, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey });
      toast.success("Edición duplicada");
    },
    onError: () => toast.error("Error al duplicar edición"),
  });

  return {
    editions,
    loading: isLoading,
    error: error ? (error as Error).message : null,
    createEdition: createMutation.mutateAsync,
    updateEdition: updateMutation.mutateAsync,
    deleteEdition: deleteMutation.mutateAsync,
    duplicateEdition: duplicateMutation.mutateAsync,
    saving:
      createMutation.isPending ||
      updateMutation.isPending ||
      deleteMutation.isPending ||
      duplicateMutation.isPending,
  };
}
```

- [ ] **Step 4: Type check**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no new errors from the added files.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/features/offer-studio/types/index.ts frontend/src/features/offer-studio/api/editions-api.ts frontend/src/features/offer-studio/hooks/use-editions.ts
git commit -m "feat(offer): add frontend types, API client, and React Query hook for editions"
```

---

## Task 7: Frontend UI Components

**Files:**
- Create: `frontend/src/features/offer-studio/components/editions/EditionStatusBadge.tsx`
- Create: `frontend/src/features/offer-studio/components/editions/EditionCard.tsx`
- Create: `frontend/src/features/offer-studio/components/editions/EditionPricingOverride.tsx`
- Create: `frontend/src/features/offer-studio/components/editions/EditionFormDialog.tsx`
- Create: `frontend/src/features/offer-studio/components/editions/EditionsSection.tsx`

This task creates all 5 UI components. They follow the same patterns as existing offer-studio forms (Shadcn Card, FormField, Badge, Dialog).

- [ ] **Step 1: Create EditionStatusBadge**

Create `frontend/src/features/offer-studio/components/editions/EditionStatusBadge.tsx`:

```tsx
"use client";

import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { EditionStatus } from "../../types";

const STATUS_CONFIG: Record<EditionStatus, { label: string; className: string }> = {
  [EditionStatus.DRAFT]: {
    label: "Borrador",
    className: "bg-amber-500/10 text-amber-500 border-amber-500/20",
  },
  [EditionStatus.UPCOMING]: {
    label: "Próximo",
    className: "bg-blue-500/10 text-blue-500 border-blue-500/20",
  },
  [EditionStatus.ACTIVE]: {
    label: "En Curso",
    className: "bg-green-500/10 text-green-500 border-green-500/20",
  },
  [EditionStatus.COMPLETED]: {
    label: "Completado",
    className: "bg-muted text-muted-foreground border-muted",
  },
  [EditionStatus.CANCELLED]: {
    label: "Cancelado",
    className: "bg-red-500/10 text-red-500 border-red-500/20",
  },
};

export function EditionStatusBadge({ status }: { status: EditionStatus }) {
  const config = STATUS_CONFIG[status] ?? STATUS_CONFIG[EditionStatus.DRAFT];
  return (
    <Badge variant="outline" className={cn("text-[10px] font-semibold uppercase", config.className)}>
      {config.label}
    </Badge>
  );
}
```

- [ ] **Step 2: Create EditionPricingOverride**

Create `frontend/src/features/offer-studio/components/editions/EditionPricingOverride.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { PricingStructure } from "../../types";
import { formatMoney } from "@/lib/format-money";

interface EditionPricingOverrideProps {
  offerPricing: PricingStructure[];
  currency: string;
  value: PricingStructure[] | null;
  onChange: (pricing: PricingStructure[] | null) => void;
}

export function EditionPricingOverride({
  offerPricing,
  currency,
  value,
  onChange,
}: EditionPricingOverrideProps) {
  const isOverride = value !== null;

  const handleToggle = (checked: boolean) => {
    if (checked) {
      onChange(offerPricing.map((p) => ({ ...p })));
    } else {
      onChange(null);
    }
  };

  const handleAmountChange = (index: number, amount: number) => {
    if (!value) return;
    const updated = [...value];
    updated[index] = { ...updated[index], total_amount: amount };
    onChange(updated);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <Label className="text-sm font-medium">Precio especial para esta edición</Label>
        <div className="flex items-center gap-2">
          <span className="text-xs text-muted-foreground">
            {isOverride ? "Override activo" : "Usa precio base"}
          </span>
          <Switch checked={isOverride} onCheckedChange={handleToggle} />
        </div>
      </div>

      {!isOverride && (
        <p className="text-xs text-muted-foreground">
          Precio heredado de la oferta:{" "}
          {offerPricing.map((p) => formatMoney(p.total_amount, currency)).join(" / ")}
        </p>
      )}

      {isOverride && value && (
        <div className="space-y-3 rounded-lg border p-4 bg-amber-500/5 border-amber-500/20">
          <p className="text-xs font-medium text-amber-500">
            Precio especial activado — esta edición usa precios diferentes.
          </p>
          {value.map((plan, idx) => (
            <div key={idx} className="flex items-center gap-3">
              <span className="text-sm text-muted-foreground w-24 truncate">
                {plan.label || `Plan ${idx + 1}`}
              </span>
              <div className="relative flex-1">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-muted-foreground text-xs">
                  {currency}
                </span>
                <Input
                  type="number"
                  value={plan.total_amount}
                  onChange={(e) => handleAmountChange(idx, parseFloat(e.target.value) || 0)}
                  className="pl-12"
                />
              </div>
              {offerPricing[idx] && plan.total_amount < offerPricing[idx].total_amount && (
                <span className="text-xs text-green-500 whitespace-nowrap">
                  -{Math.round(((offerPricing[idx].total_amount - plan.total_amount) / offerPricing[idx].total_amount) * 100)}%
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 3: Create EditionCard**

Create `frontend/src/features/offer-studio/components/editions/EditionCard.tsx`:

```tsx
"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Pencil, Copy, Trash2, CalendarDays, Users, MapPin } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatMoney } from "@/lib/format-money";
import { LaunchEdition, EditionStatus } from "../../types";
import { EditionStatusBadge } from "./EditionStatusBadge";

const STATUS_BORDER: Record<EditionStatus, string> = {
  [EditionStatus.DRAFT]: "border-l-amber-500 border-dashed",
  [EditionStatus.UPCOMING]: "border-l-blue-500",
  [EditionStatus.ACTIVE]: "border-l-green-500",
  [EditionStatus.COMPLETED]: "opacity-60",
  [EditionStatus.CANCELLED]: "opacity-40",
};

function formatDateRange(start: string, end: string | null): string {
  const s = new Date(start);
  const opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "short", year: "numeric" };
  if (!end) return s.toLocaleDateString("es", opts);
  const e = new Date(end);
  return `${s.toLocaleDateString("es", opts)} — ${e.toLocaleDateString("es", opts)}`;
}

interface EditionCardProps {
  edition: LaunchEdition;
  onEdit: () => void;
  onDuplicate: () => void;
  onDelete: () => void;
}

export function EditionCard({ edition, onEdit, onDuplicate, onDelete }: EditionCardProps) {
  const isCompleted = edition.status === EditionStatus.COMPLETED;
  const hasOverride = edition.pricing_override !== null;
  const mainPrice = edition.effective_pricing[0];

  return (
    <Card className={cn("border-l-4 transition-all hover:bg-muted/30", STATUS_BORDER[edition.status])}>
      <CardContent className="p-4 space-y-3">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <span className="font-semibold text-sm">{edition.edition_name}</span>
            <EditionStatusBadge status={edition.status} />
          </div>
          <div className="flex gap-1">
            {!isCompleted && (
              <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onEdit}>
                <Pencil className="h-3.5 w-3.5" />
              </Button>
            )}
            <Button variant="ghost" size="icon" className="h-7 w-7" onClick={onDuplicate}>
              <Copy className="h-3.5 w-3.5" />
            </Button>
            {!isCompleted && (
              <Button variant="ghost" size="icon" className="h-7 w-7 text-destructive" onClick={onDelete}>
                <Trash2 className="h-3.5 w-3.5" />
              </Button>
            )}
          </div>
        </div>

        {/* Meta */}
        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
          <span className="flex items-center gap-1">
            <CalendarDays className="h-3 w-3" />
            {formatDateRange(edition.start_date, edition.end_date)}
          </span>
          {edition.capacity && (
            <span className="flex items-center gap-1">
              <Users className="h-3 w-3" />
              {edition.enrollment_count} / {edition.capacity} inscritos
            </span>
          )}
        </div>

        {/* Pricing */}
        {mainPrice && (
          <div className="flex items-center gap-3 pt-1 border-t text-sm">
            <span className="font-bold">
              {formatMoney(mainPrice.total_amount, edition.currency)}
            </span>
            <span className="text-xs text-muted-foreground">
              {mainPrice.label}
            </span>
            {hasOverride ? (
              <span className="text-xs text-amber-500 font-medium">Precio especial</span>
            ) : (
              <span className="text-xs text-muted-foreground">= precio base</span>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 4: Create EditionFormDialog**

Create `frontend/src/features/offer-studio/components/editions/EditionFormDialog.tsx`:

```tsx
"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Loader2 } from "lucide-react";
import {
  LaunchEdition,
  LaunchEditionCreate,
  LaunchEditionUpdate,
  EditionStatus,
  PricingStructure,
} from "../../types";
import { EditionPricingOverride } from "./EditionPricingOverride";

interface EditionFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  edition?: LaunchEdition;
  offerPricing: PricingStructure[];
  currency: string;
  onSave: (data: LaunchEditionCreate | LaunchEditionUpdate) => Promise<unknown>;
}

function toLocalInputValue(isoString: string | null | undefined): string {
  if (!isoString) return "";
  const d = new Date(isoString);
  const offset = d.getTimezoneOffset();
  const local = new Date(d.getTime() - offset * 60000);
  return local.toISOString().slice(0, 16);
}

function fromLocalInputValue(value: string): string | undefined {
  if (!value) return undefined;
  return new Date(value).toISOString();
}

export function EditionFormDialog({
  open,
  onOpenChange,
  edition,
  offerPricing,
  currency,
  onSave,
}: EditionFormDialogProps) {
  const isEdit = !!edition;

  const [name, setName] = useState(edition?.edition_name ?? "");
  const [startDate, setStartDate] = useState(toLocalInputValue(edition?.start_date));
  const [endDate, setEndDate] = useState(toLocalInputValue(edition?.end_date));
  const [regStart, setRegStart] = useState(toLocalInputValue(edition?.registration_start));
  const [regEnd, setRegEnd] = useState(toLocalInputValue(edition?.registration_end));
  const [tz, setTz] = useState(edition?.timezone ?? "America/Lima");
  const [capacity, setCapacity] = useState<string>(edition?.capacity?.toString() ?? "");
  const [status, setStatus] = useState<EditionStatus>(edition?.status ?? EditionStatus.DRAFT);
  const [pricingOverride, setPricingOverride] = useState<PricingStructure[] | null>(
    edition?.pricing_override ?? null
  );
  const [notes, setNotes] = useState(edition?.notes ?? "");
  const [saving, setSaving] = useState(false);

  const handleSubmit = async () => {
    if (!startDate) return;
    setSaving(true);
    try {
      const data: LaunchEditionCreate & LaunchEditionUpdate = {
        edition_name: name || undefined,
        start_date: fromLocalInputValue(startDate)!,
        end_date: fromLocalInputValue(endDate),
        registration_start: fromLocalInputValue(regStart),
        registration_end: fromLocalInputValue(regEnd),
        timezone: tz,
        capacity: capacity ? parseInt(capacity, 10) : undefined,
        pricing_override: pricingOverride ?? undefined,
        notes: notes || undefined,
      };
      if (isEdit) {
        (data as LaunchEditionUpdate).status = status;
      }
      await onSave(data);
      onOpenChange(false);
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>{isEdit ? "Editar Edición" : "Nueva Edición"}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4 py-2">
          {/* Name */}
          <div className="space-y-1">
            <Label className="text-xs">Nombre de la Edición</Label>
            <Input
              placeholder="Se auto-genera si lo dejas vacío"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {/* Dates */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Fecha de Inicio *</Label>
              <Input
                type="datetime-local"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Fecha de Fin</Label>
              <Input
                type="datetime-local"
                value={endDate}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Inscripciones Desde</Label>
              <Input
                type="datetime-local"
                value={regStart}
                onChange={(e) => setRegStart(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Inscripciones Hasta</Label>
              <Input
                type="datetime-local"
                value={regEnd}
                onChange={(e) => setRegEnd(e.target.value)}
              />
            </div>
          </div>

          {/* Capacity + Status */}
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <Label className="text-xs">Capacidad Máxima</Label>
              <Input
                type="number"
                placeholder="Sin límite"
                value={capacity}
                onChange={(e) => setCapacity(e.target.value)}
              />
            </div>
            {isEdit && (
              <div className="space-y-1">
                <Label className="text-xs">Estado</Label>
                <Select value={status} onValueChange={(v) => setStatus(v as EditionStatus)}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={EditionStatus.DRAFT}>Borrador</SelectItem>
                    <SelectItem value={EditionStatus.UPCOMING}>Próximo</SelectItem>
                    <SelectItem value={EditionStatus.ACTIVE}>En Curso</SelectItem>
                    <SelectItem value={EditionStatus.COMPLETED}>Completado</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            )}
          </div>

          {/* Pricing Override */}
          <EditionPricingOverride
            offerPricing={offerPricing}
            currency={currency}
            value={pricingOverride}
            onChange={setPricingOverride}
          />

          {/* Notes */}
          <div className="space-y-1">
            <Label className="text-xs">Notas Internas</Label>
            <Textarea
              placeholder="Notas visibles solo para ti..."
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              rows={2}
            />
          </div>
        </div>

        <DialogFooter>
          <Button variant="ghost" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button onClick={handleSubmit} disabled={saving || !startDate}>
            {saving && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {isEdit ? "Guardar Cambios" : "Crear Edición"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

- [ ] **Step 5: Create EditionsSection (main section)**

Create `frontend/src/features/offer-studio/components/editions/EditionsSection.tsx`:

```tsx
"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Rocket, Plus, CalendarPlus } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";
import { useEditions } from "../../hooks/use-editions";
import { LaunchEdition, LaunchEditionCreate, LaunchEditionUpdate, PricingStructure } from "../../types";
import { EditionCard } from "./EditionCard";
import { EditionFormDialog } from "./EditionFormDialog";

interface EditionsSectionProps {
  offerId: string;
  offerPricing: PricingStructure[];
  currency: string;
}

export function EditionsSection({ offerId, offerPricing, currency }: EditionsSectionProps) {
  const {
    editions,
    loading,
    createEdition,
    updateEdition,
    deleteEdition,
    duplicateEdition,
  } = useEditions(offerId);

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingEdition, setEditingEdition] = useState<LaunchEdition | undefined>();

  const handleCreate = () => {
    setEditingEdition(undefined);
    setDialogOpen(true);
  };

  const handleEdit = (edition: LaunchEdition) => {
    setEditingEdition(edition);
    setDialogOpen(true);
  };

  const handleSave = async (data: LaunchEditionCreate | LaunchEditionUpdate) => {
    if (editingEdition) {
      await updateEdition({ editionId: editingEdition.id, data: data as LaunchEditionUpdate });
    } else {
      await createEdition(data as LaunchEditionCreate);
    }
  };

  return (
    <Card>
      <CardHeader className="pb-4 border-b bg-purple-50/50 dark:bg-purple-950/20">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-md bg-purple-100 dark:bg-purple-900/30">
              <Rocket className="h-5 w-5 text-purple-600 dark:text-purple-400" />
            </div>
            <div>
              <CardTitle className="text-base">Ediciones de Lanzamiento</CardTitle>
              <CardDescription>
                Cada edición tiene sus propias fechas y opcionalmente precios distintos
              </CardDescription>
            </div>
          </div>
          <Button onClick={handleCreate} size="sm">
            <Plus className="h-4 w-4 mr-1" />
            Nueva Edición
          </Button>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        {loading ? (
          <div className="space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-24 w-full" />
          </div>
        ) : editions.length === 0 ? (
          <div className="text-center py-12">
            <CalendarPlus className="h-10 w-10 mx-auto text-muted-foreground/30 mb-3" />
            <h3 className="font-semibold text-sm mb-1">Sin ediciones todavía</h3>
            <p className="text-xs text-muted-foreground max-w-xs mx-auto mb-4">
              Crea tu primera edición para definir fechas de lanzamiento y precios específicos.
            </p>
            <Button variant="outline" size="sm" onClick={handleCreate}>
              <Plus className="h-4 w-4 mr-1" />
              Crear Primera Edición
            </Button>
          </div>
        ) : (
          <div className="space-y-3">
            {editions.map((edition) => (
              <EditionCard
                key={edition.id}
                edition={edition}
                onEdit={() => handleEdit(edition)}
                onDuplicate={() => duplicateEdition(edition.id)}
                onDelete={() => deleteEdition(edition.id)}
              />
            ))}
          </div>
        )}

        <EditionFormDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          edition={editingEdition}
          offerPricing={offerPricing}
          currency={currency}
          onSave={handleSave}
        />
      </CardContent>
    </Card>
  );
}
```

- [ ] **Step 6: Type check**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
```

Expected: no new errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/features/offer-studio/components/editions/
git commit -m "feat(offer): add EditionsSection UI components (cards, form dialog, pricing override)"
```

---

## Task 8: Wire Editions into Offer Editor

**Files:**
- Modify: `frontend/src/features/offer-studio/config/offer-builder-config.ts`

- [ ] **Step 1: Register editions section in SECTION_REGISTRY and ARCHETYPE_BUILDER_CONFIG**

In `frontend/src/features/offer-studio/config/offer-builder-config.ts`:

Add import at top:
```typescript
import { Rocket } from 'lucide-react';
import { EditionsSection } from '../components/editions/EditionsSection';
```

Add to `SECTION_REGISTRY` (after `closing`):
```typescript
  editions: {
    id: 'editions',
    title: 'Ediciones',
    component: EditionsSection,
    icon: Rocket,
    previewComponent: PlaceholderPreview,
    formComponent: EditionsSection,
  },
```

Update `ARCHETYPE_BUILDER_CONFIG` — add `'editions'` before `'closing'` for applicable archetypes:
```typescript
  [OfferArchetype.PROGRAMA]: ['identity', 'strategy', 'psychology', 'promise', 'program_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'editions', 'closing'],
  [OfferArchetype.SERVICIO]: ['identity', 'strategy', 'psychology', 'promise', 'service_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'editions', 'closing'],
  [OfferArchetype.EXPERIENCIA]: ['identity', 'strategy', 'psychology', 'promise', 'event_details', 'instructors', 'value_stack', 'resources', 'gallery', 'pricing', 'editions', 'closing'],
```

Keep `PRODUCTO` and `MEMBRESIA` **without** editions (they're evergreen).

- [ ] **Step 2: Type check and lint**

```bash
cd frontend && npx tsc --noEmit 2>&1 | head -30
cd frontend && npx eslint src/features/offer-studio/config/offer-builder-config.ts 2>&1 | head -20
```

Expected: no errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/features/offer-studio/config/offer-builder-config.ts
git commit -m "feat(offer): wire EditionsSection into offer editor for programa/servicio/experiencia"
```

---

## Task 9: Full Verification

- [ ] **Step 1: Run full backend tests**

```bash
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd backend && .venv/bin/pytest -x -q --tb=short
```

Expected: ALL pass, zero lint errors.

- [ ] **Step 2: Run full frontend checks**

```bash
cd frontend && npx tsc --noEmit
cd frontend && npx eslint src/
cd frontend && npx vitest run
```

Expected: ALL pass.

- [ ] **Step 3: Run architecture fitness tests**

```bash
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
```

Expected: ALL pass — LaunchEdition is within the `offer` bounded context, no cross-module imports.

- [ ] **Step 4: Final commit if any fixes were needed**

```bash
git status
# If clean: done. If fixes needed: commit them.
```
