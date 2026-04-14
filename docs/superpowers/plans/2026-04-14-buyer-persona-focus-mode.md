# Buyer Persona Focus Mode — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Migrate from legacy Avatar (3 fields) to rich BuyerPersona (12+ JSONB fields) with full Focus Mode, Interview Engine integration, manual editing, and a globally full-width layout.

**Architecture:** Backend REST API for BuyerPersona CRUD + BuyerPersonaPersister for the Interview Engine. Frontend: API client + React Query hook, migrated `AvatarsSection` with mode selection + Focus chip, and a new full-width detail page for manual editing. Dashboard layout removes `max-w-7xl` constraint globally.

**Tech Stack:** FastAPI, SQLAlchemy 2.0, Pydantic v2, pytest (backend) | Next.js 15 App Router, React Query, Zustand, Vitest, Shadcn UI (frontend)

**Spec:** `docs/superpowers/specs/2026-04-14-buyer-persona-focus-mode.md`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Modify | `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx` | Remove `FULL_WIDTH_PATTERNS`, always render `p-6 md:p-8 h-full` |
| Create | `backend/src/modules/brand/api/buyer_personas.py` | REST endpoints: list, create, get, patch, delete |
| Create | `backend/src/modules/brand/api/dto/buyer_personas.py` | Pydantic DTOs: Create, SectionUpdate, Response |
| Modify | `backend/src/main.py` | Mount buyer_personas router |
| Create | `backend/tests/modules/brand/test_buyer_persona_api.py` | API integration tests |
| Create | `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py` | Interview Engine persister |
| Modify | `backend/src/modules/copilot/infrastructure/persisters/persister_registry.py` | Register buyer_persona persister |
| Create | `backend/tests/modules/copilot/test_buyer_persona_persister.py` | Persister unit tests |
| Create | `frontend/src/lib/api/buyer-persona.ts` | API client functions |
| Create | `frontend/src/features/brand/hooks/useBuyerPersonas.ts` | React Query hook |
| Create | `frontend/src/features/brand/hooks/__tests__/useBuyerPersonas.test.ts` | Hook tests |
| Modify | `frontend/src/features/brand/sections/avatars/avatars-preview.tsx` | Migrate Avatar→BuyerPersona, mode selection, Focus chip |
| Create | `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/publico/persona/[personaId]/page.tsx` | Manual edit detail page |
| Modify | `backend/src/modules/copilot/application/services/interview_service.py` | Per-domain initial messages |

---

## Task 0: Full-Width Layout

**Files:**
- Modify: `frontend/src/app/(main)/[tenantId]/(dashboard)/layout.tsx`

- [ ] **Step 1: Edit layout — remove FULL_WIDTH_PATTERNS and simplify wrapper**

Remove the `FULL_WIDTH_PATTERNS` constant, the `matchesFullWidth` function, the `isFullWidth` state, and the `useEffect`. Replace `MemoizedChildren` to always use the padding-only wrapper:

```tsx
const MemoizedChildren = memo(function MemoizedChildren({
  children,
}: {
  children: React.ReactNode;
}) {
  return <div className="p-6 md:p-8 h-full">{children}</div>;
});
```

In `DashboardContent`, remove the `isFullWidth` state and `useEffect`, and update the JSX:

```tsx
// Remove these lines:
// const [isFullWidth, setIsFullWidth] = useState(false);
// useEffect(() => { setIsFullWidth(matchesFullWidth(pathname)); }, [pathname]);

// Update MemoizedChildren call — remove isFullWidth prop:
<MemoizedChildren>{children}</MemoizedChildren>
```

Also remove the `useState` import if no longer needed (keep `memo`), and remove the unused `usePathname` import and `pathname` variable if nothing else uses them.

- [ ] **Step 2: Verify frontend types compile**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No errors related to layout.tsx

- [ ] **Step 3: Verify frontend lint passes**

Run: `cd frontend && npx eslint src/app/\(main\)/\[tenantId\]/\(dashboard\)/layout.tsx`
Expected: No errors

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/layout.tsx
git commit -m "refactor(layout): remove max-w-7xl constraint — full-width globally

Remove FULL_WIDTH_PATTERNS workaround. All pages now use p-6 md:p-8 h-full.
Individual sections manage their own max-w internally."
```

---

## Task 1: Backend — BuyerPersona DTOs

**Files:**
- Create: `backend/src/modules/brand/api/dto/buyer_personas.py`

- [ ] **Step 1: Create DTO file**

```python
"""BuyerPersona API DTOs."""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BuyerPersonaCreateDTO(BaseModel):
    """Create a new buyer persona (shell — just a name)."""

    name: str
    tagline: str | None = None
    scope: str = "GLOBAL"
    offer_id: UUID | None = None


class BuyerPersonaSectionUpdateDTO(BaseModel):
    """PATCH parcial — only sent fields are updated."""

    name: str | None = None
    tagline: str | None = None
    demographics: dict[str, Any] | None = None
    psychographics: dict[str, Any] | None = None
    pain_points: list[dict[str, Any]] | None = None
    desires: list[dict[str, Any]] | None = None
    objections: list[dict[str, Any]] | None = None
    preferred_channels: list[dict[str, Any]] | None = None
    buyer_journey: dict[str, Any] | None = None
    purchase_triggers: list[str] | None = None
    anti_patterns: list[str] | None = None


class BuyerPersonaResponseDTO(BaseModel):
    """Full buyer persona response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    tagline: str | None
    scope: str
    is_primary: bool
    demographics: dict[str, Any]
    psychographics: dict[str, Any]
    pain_points: list[dict[str, Any]]
    desires: list[dict[str, Any]]
    objections: list[dict[str, Any]]
    preferred_channels: list[dict[str, Any]]
    buyer_journey: dict[str, Any]
    purchase_triggers: list[str]
    anti_patterns: list[str]
    completeness_score: float
    interview_session_id: UUID | None
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 2: Verify lint**

Run: `cd backend && .venv/bin/ruff check src/modules/brand/api/dto/buyer_personas.py --no-cache`
Expected: All checks passed!

- [ ] **Step 3: Commit**

```bash
git add backend/src/modules/brand/api/dto/buyer_personas.py
git commit -m "feat(brand): add BuyerPersona DTOs — create, section-update, response"
```

---

## Task 2: Backend — BuyerPersona API Endpoints

**Files:**
- Create: `backend/src/modules/brand/api/buyer_personas.py`
- Modify: `backend/src/main.py`
- Create: `backend/tests/modules/brand/test_buyer_persona_api.py`

- [ ] **Step 1: Write API test file**

```python
"""Tests for BuyerPersona REST API — CRUD + tenant isolation."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.modules.brand.api.buyer_personas import router
from src.modules.brand.infrastructure.repositories.buyer_persona_repository import (
    BuyerPersonaRepository,
)
from src.modules.iam.api.dependencies import get_current_user, get_db
from src.modules.iam.domain.user import User
from tests.modules.conftest import TENANT_A, TENANT_B, USER_A

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _build_client(db: Session, tenant_id: uuid.UUID) -> TestClient:
    """Build a TestClient with overridden dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/brand/buyer-personas")

    fake_user = User(
        id=USER_A,
        email="test@example.com",
        full_name="Test User",
        tenant_id=tenant_id,
        is_active=True,
    )
    app.dependency_overrides[get_db] = lambda: db
    app.dependency_overrides[get_current_user] = lambda: fake_user
    return TestClient(app)


class TestBuyerPersonaAPI:
    """CRUD tests for buyer persona endpoints."""

    def test_create_persona(self, db: Session) -> None:
        """POST creates a persona and returns it with an id."""
        client = _build_client(db, TENANT_A)
        resp = client.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Mamá Rural"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "Mamá Rural"
        assert data["scope"] == "GLOBAL"
        assert data["completeness_score"] == 0.0
        assert "id" in data

    def test_list_personas(self, db: Session) -> None:
        """GET list returns personas for the tenant."""
        client = _build_client(db, TENANT_A)
        client.post("/api/v1/brand/buyer-personas/", json={"name": "P1"})
        client.post("/api/v1/brand/buyer-personas/", json={"name": "P2"})

        resp = client.get("/api/v1/brand/buyer-personas/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2

    def test_get_persona(self, db: Session) -> None:
        """GET by id returns the persona."""
        client = _build_client(db, TENANT_A)
        created = client.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Test"},
        ).json()

        resp = client.get(f"/api/v1/brand/buyer-personas/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["name"] == "Test"

    def test_patch_persona_section(self, db: Session) -> None:
        """PATCH updates specific fields and recalculates completeness."""
        client = _build_client(db, TENANT_A)
        created = client.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Test"},
        ).json()

        resp = client.patch(
            f"/api/v1/brand/buyer-personas/{created['id']}",
            json={
                "demographics": {"age_range": "25-35", "location": "LATAM"},
                "pain_points": [{"description": "No time", "intensity": "high"}],
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["demographics"]["age_range"] == "25-35"
        assert len(data["pain_points"]) == 1
        assert data["completeness_score"] > 0.0

    def test_delete_persona(self, db: Session) -> None:
        """DELETE soft-deletes (persona no longer in list)."""
        client = _build_client(db, TENANT_A)
        created = client.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Doomed"},
        ).json()

        resp = client.delete(f"/api/v1/brand/buyer-personas/{created['id']}")
        assert resp.status_code == 204

        resp = client.get("/api/v1/brand/buyer-personas/")
        assert len(resp.json()) == 0

    def test_get_persona_wrong_tenant_returns_404(self, db: Session) -> None:
        """Persona created by TENANT_A is invisible to TENANT_B."""
        client_a = _build_client(db, TENANT_A)
        created = client_a.post(
            "/api/v1/brand/buyer-personas/",
            json={"name": "Secret"},
        ).json()

        client_b = _build_client(db, TENANT_B)
        resp = client_b.get(f"/api/v1/brand/buyer-personas/{created['id']}")
        assert resp.status_code == 404

    def test_patch_nonexistent_returns_404(self, db: Session) -> None:
        """PATCH on a nonexistent persona returns 404."""
        client = _build_client(db, TENANT_A)
        fake_id = str(uuid.uuid4())
        resp = client.patch(
            f"/api/v1/brand/buyer-personas/{fake_id}",
            json={"name": "Ghost"},
        )
        assert resp.status_code == 404
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/brand/test_buyer_persona_api.py -x -q --tb=short`
Expected: FAIL — `ModuleNotFoundError` or `ImportError` (buyer_personas module doesn't exist yet)

- [ ] **Step 3: Write API endpoint file**

Create `backend/src/modules/brand/api/buyer_personas.py`:

```python
"""BuyerPersona REST API endpoints."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from src.core.database import get_db
from src.modules.brand.api.dto.buyer_personas import (
    BuyerPersonaCreateDTO,
    BuyerPersonaResponseDTO,
    BuyerPersonaSectionUpdateDTO,
)
from src.modules.brand.domain.buyer_persona import BuyerPersona
from src.modules.brand.infrastructure.repositories.buyer_persona_repository import (
    BuyerPersonaRepository,
)
from src.modules.iam.api.dependencies import get_current_user
from src.modules.iam.domain.user import User

router = APIRouter()

# Fields that count toward completeness (profile-only, not metadata).
_PROFILE_FIELDS = (
    "demographics",
    "psychographics",
    "pain_points",
    "desires",
    "objections",
    "preferred_channels",
    "buyer_journey",
    "purchase_triggers",
    "anti_patterns",
)


def _calc_completeness(persona: BuyerPersona) -> float:
    """Return 0.0–100.0 based on how many profile fields are non-empty."""
    filled = 0
    for field in _PROFILE_FIELDS:
        value = getattr(persona, field, None)
        if isinstance(value, dict) and value:
            filled += 1
        elif isinstance(value, list) and value:
            filled += 1
    return round((filled / len(_PROFILE_FIELDS)) * 100, 1)


@router.get("/", response_model=list[BuyerPersonaResponseDTO])
async def list_buyer_personas(
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
    scope: str | None = None,
) -> list[BuyerPersona]:
    """List buyer personas for the tenant."""
    repo = BuyerPersonaRepository(db)
    return repo.list_by_tenant(user.tenant_id, scope=scope)


@router.post("/", response_model=BuyerPersonaResponseDTO)
async def create_buyer_persona(
    dto: BuyerPersonaCreateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuyerPersona:
    """Create a new buyer persona (shell)."""
    repo = BuyerPersonaRepository(db)
    persona = BuyerPersona(
        id=uuid.uuid4(),
        tenant_id=user.tenant_id,
        user_id=user.id,
        name=dto.name,
        tagline=dto.tagline,
        scope=dto.scope,
        offer_id=dto.offer_id,
    )
    return repo.create(persona)


@router.get("/{persona_id}", response_model=BuyerPersonaResponseDTO)
async def get_buyer_persona(
    persona_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuyerPersona:
    """Get a single buyer persona by id."""
    repo = BuyerPersonaRepository(db)
    persona = repo.get_by_id(user.tenant_id, persona_id)
    if not persona:
        raise HTTPException(status_code=404, detail="Buyer persona not found")
    return persona


@router.patch("/{persona_id}", response_model=BuyerPersonaResponseDTO)
async def update_buyer_persona(
    persona_id: uuid.UUID,
    dto: BuyerPersonaSectionUpdateDTO,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> BuyerPersona:
    """Partial update — only sent fields are written."""
    repo = BuyerPersonaRepository(db)
    updates = dto.model_dump(exclude_unset=True)
    updated = repo.update(user.tenant_id, persona_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail="Buyer persona not found")

    # Recalculate completeness after update
    score = _calc_completeness(updated)
    if score != updated.completeness_score:
        updated = repo.update(
            user.tenant_id,
            persona_id,
            {"completeness_score": score},
        )

    return updated


@router.delete("/{persona_id}", status_code=204)
async def delete_buyer_persona(
    persona_id: uuid.UUID,
    db: Annotated[Session, Depends(get_db)],
    user: Annotated[User, Depends(get_current_user)],
) -> None:
    """Soft-delete a buyer persona."""
    repo = BuyerPersonaRepository(db)
    existing = repo.get_by_id(user.tenant_id, persona_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Buyer persona not found")
    repo.soft_delete(user.tenant_id, persona_id)
```

- [ ] **Step 4: Register router in main.py**

Add import near other brand imports (around line 36–42):
```python
from src.modules.brand.api import buyer_personas as brand_buyer_personas
```

Add router mount after the `brand_avatars` block (around line 393):
```python
app.include_router(
    brand_buyer_personas.router,
    prefix="/api/v1/brand/buyer-personas",
    tags=["Brand - Buyer Personas"],
    dependencies=[Depends(get_tenant_context)],
)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd backend && .venv/bin/pytest tests/modules/brand/test_buyer_persona_api.py -x -q --tb=short`
Expected: 7 passed

- [ ] **Step 6: Verify lint**

Run: `cd backend && .venv/bin/ruff check src/modules/brand/api/buyer_personas.py src/modules/brand/api/dto/buyer_personas.py --no-cache`
Expected: All checks passed!

- [ ] **Step 7: Run architecture tests (response_model check)**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: All passed (all endpoints have `response_model=`)

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/brand/api/buyer_personas.py backend/src/modules/brand/api/dto/buyer_personas.py backend/tests/modules/brand/test_buyer_persona_api.py backend/src/main.py
git commit -m "feat(brand): add BuyerPersona REST API — CRUD + tenant isolation + completeness

Endpoints: GET/POST /buyer-personas/, GET/PATCH/DELETE /buyer-personas/{id}
Completeness recalculated on every PATCH.
7 API tests including cross-tenant isolation."
```

---

## Task 3: Backend — BuyerPersonaPersister + Registry

**Files:**
- Create: `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py`
- Modify: `backend/src/modules/copilot/infrastructure/persisters/persister_registry.py`
- Create: `backend/tests/modules/copilot/test_buyer_persona_persister.py`

- [ ] **Step 1: Write persister test file**

```python
"""Tests for BuyerPersonaPersister — persist, load, registry."""

from __future__ import annotations

from unittest.mock import MagicMock, patch
from uuid import uuid4

from src.modules.brand.domain.buyer_persona import BuyerPersona
from src.modules.copilot.infrastructure.persisters.buyer_persona_persister import (
    BuyerPersonaPersister,
)
from src.modules.copilot.infrastructure.persisters.persister_registry import (
    get_persister,
)


def _make_persona(**overrides: object) -> BuyerPersona:
    """Build a minimal BuyerPersona for testing."""
    defaults: dict = {
        "id": uuid4(),
        "tenant_id": uuid4(),
        "user_id": uuid4(),
        "name": "Test Persona",
    }
    defaults.update(overrides)
    return BuyerPersona(**defaults)


class TestBuyerPersonaPersist:
    """Tests for persist method."""

    def test_persist_creates_new_when_no_entity_id(self) -> None:
        """Without entity_id, persister creates a new persona."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()

        mapa_global = {
            "name": "Mamá Rural",
            "demographics.age_range": "30-45",
            "demographics.location": "Rural LATAM",
            "pain_points": [{"description": "No time", "intensity": "high"}],
        }
        fields = list(mapa_global.keys())

        with patch.object(persister, "repo") as mock_repo:
            created = _make_persona(tenant_id=tenant_id, name="Mamá Rural")
            mock_repo.create.return_value = created

            result_id = persister.persist(tenant_id, mapa_global, fields)

            mock_repo.create.assert_called_once()
            assert result_id == created.id

    def test_persist_updates_existing_entity(self) -> None:
        """With entity_id, persister updates existing persona."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()
        persona = _make_persona(id=entity_id, tenant_id=tenant_id)

        mapa_global = {
            "demographics.age_range": "25-35",
            "demographics.location": "Urban",
        }
        fields = list(mapa_global.keys())

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = persona
            mock_repo.update.return_value = persona

            result_id = persister.persist(
                tenant_id, mapa_global, fields, entity_id=entity_id,
            )

            mock_repo.get_by_id.assert_called_once_with(tenant_id, entity_id)
            mock_repo.update.assert_called_once()
            assert result_id == entity_id

    def test_persist_returns_none_if_entity_not_found(self) -> None:
        """If entity_id is given but not found, return None."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = None
            result = persister.persist(
                tenant_id, {"name": "X"}, ["name"], entity_id=entity_id,
            )
            assert result is None
            mock_repo.update.assert_not_called()

    def test_persist_skips_missing_fields(self) -> None:
        """Fields in fields_to_persist but not in mapa_global are skipped."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()
        persona = _make_persona(id=entity_id, tenant_id=tenant_id)

        mapa_global = {"demographics.age_range": "25-35"}
        fields = ["demographics.age_range", "demographics.location"]

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = persona
            mock_repo.update.return_value = persona

            persister.persist(tenant_id, mapa_global, fields, entity_id=entity_id)

            call_args = mock_repo.update.call_args[1]
            updates = call_args["updates"]
            # Only age_range present (location was missing from mapa_global)
            assert updates["demographics"]["age_range"] == "25-35"


class TestBuyerPersonaLoadExisting:
    """Tests for load_existing method."""

    def test_load_existing_returns_flat_dict(self) -> None:
        """load_existing flattens persona data to dot-notation keys."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()
        persona = _make_persona(
            id=entity_id,
            tenant_id=tenant_id,
            name="Mamá Rural",
            demographics={"age_range": "30-40", "location": "Rural"},
            pain_points=[{"description": "No time"}],
            purchase_triggers=["discount", "urgency"],
        )

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = persona
            result = persister.load_existing(tenant_id, entity_id)

        assert result["name"] == "Mamá Rural"
        assert result["demographics.age_range"] == "30-40"
        assert result["demographics.location"] == "Rural"
        assert result["pain_points"] == [{"description": "No time"}]
        assert result["purchase_triggers"] == ["discount", "urgency"]

    def test_load_existing_returns_empty_if_not_found(self) -> None:
        """If entity_id not found, return empty dict."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = None
            result = persister.load_existing(uuid4(), uuid4())
            assert result == {}

    def test_load_existing_calls_repo_exactly_once(self) -> None:
        """Single query guarantee — no N+1."""
        db = MagicMock()
        persister = BuyerPersonaPersister(db)
        tenant_id = uuid4()
        entity_id = uuid4()
        persona = _make_persona(id=entity_id, tenant_id=tenant_id)

        with patch.object(persister, "repo") as mock_repo:
            mock_repo.get_by_id.return_value = persona
            persister.load_existing(tenant_id, entity_id)

        mock_repo.get_by_id.assert_called_once_with(tenant_id, entity_id)


class TestPersisterRegistryBuyerPersona:
    """Registry recognises buyer_persona."""

    def test_get_buyer_persona_persister(self) -> None:
        """get_persister('buyer_persona') returns BuyerPersonaPersister."""
        db = MagicMock()
        persister = get_persister("buyer_persona", db)
        assert isinstance(persister, BuyerPersonaPersister)

    def test_existing_persisters_still_work(self) -> None:
        """brand and offer persisters unaffected."""
        db = MagicMock()
        from src.modules.copilot.infrastructure.persisters.brand_persister import (
            BrandPersister,
        )
        from src.modules.copilot.infrastructure.persisters.offer_persister import (
            OfferPersister,
        )

        assert isinstance(get_persister("brand", db), BrandPersister)
        assert isinstance(get_persister("offer", db), OfferPersister)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_buyer_persona_persister.py -x -q --tb=short`
Expected: FAIL — `ImportError` (BuyerPersonaPersister doesn't exist yet)

- [ ] **Step 3: Create the persister**

Create `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py`:

```python
"""Persists interview mapa_global data into BuyerPersona entities."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import structlog

from src.modules.brand.domain.buyer_persona import BuyerPersona
from src.modules.brand.infrastructure.repositories.buyer_persona_repository import (
    BuyerPersonaRepository,
)

if TYPE_CHECKING:
    from uuid import UUID

    from sqlalchemy.orm import Session

logger = structlog.get_logger()

# BuyerPersona fields that are dicts (flattened with dot-notation).
_DICT_FIELDS = {"demographics", "psychographics", "buyer_journey"}

# BuyerPersona fields that are lists (stored directly, not flattened).
_LIST_FIELDS = {
    "pain_points",
    "desires",
    "objections",
    "preferred_channels",
    "purchase_triggers",
    "anti_patterns",
}

# Simple scalar fields.
_SCALAR_FIELDS = {"name", "tagline"}


class BuyerPersonaPersister:
    """Writes confirmed interview data to a BuyerPersona entity.

    Field-path conventions match the interview config in buyer_persona_config.py:
    - Dict fields use dot-notation: ``demographics.age_range``
    - List fields use the field name directly: ``pain_points``
    - Scalar fields use the field name directly: ``name``

    Query-count contract (no N+1):
        All BuyerPersona profile fields are JSONB columns — no ORM
        relationships.  ``load_existing`` = 1 SELECT, ``persist`` with
        entity_id = 1 SELECT + 1 UPDATE (2 total), without entity_id
        = 1 INSERT.
    """

    def __init__(self, db: Session) -> None:
        """Initialize with database session."""
        self.db = db
        self.repo = BuyerPersonaRepository(db)

    def persist(
        self,
        tenant_id: UUID,
        mapa_global: dict,
        fields_to_persist: list[str],
        entity_id: UUID | None = None,
    ) -> UUID | None:
        """Persist fields from mapa_global to a BuyerPersona.

        If ``entity_id`` is provided, updates the existing persona.
        If ``entity_id`` is None, creates a new GLOBAL persona.

        Returns:
            The persona UUID, or None if entity_id was given but not found.
        """
        if entity_id is not None:
            return self._update_existing(tenant_id, entity_id, mapa_global, fields_to_persist)
        return self._create_new(tenant_id, mapa_global, fields_to_persist)

    def load_existing(self, tenant_id: UUID, entity_id: UUID) -> dict:
        """Load persona data as a flat dict for pre-filling mapa_global.

        Dict fields (demographics, psychographics, buyer_journey) are
        flattened to dot-notation.  List/scalar fields are stored directly.

        Returns:
            Flat dict or empty dict if not found.
        """
        persona = self.repo.get_by_id(tenant_id, entity_id)
        if not persona:
            return {}

        result: dict = {}

        # Scalar fields
        for field in _SCALAR_FIELDS:
            value = getattr(persona, field, None)
            if value is not None:
                result[field] = value

        # Dict fields → flatten to dot-notation
        for field in _DICT_FIELDS:
            value = getattr(persona, field, None)
            if isinstance(value, dict):
                for k, v in value.items():
                    if v is not None:
                        result[f"{field}.{k}"] = v

        # List fields → store directly
        for field in _LIST_FIELDS:
            value = getattr(persona, field, None)
            if isinstance(value, list) and value:
                result[field] = value

        return result

    def _update_existing(
        self,
        tenant_id: UUID,
        entity_id: UUID,
        mapa_global: dict,
        fields_to_persist: list[str],
    ) -> UUID | None:
        """Update an existing persona with data from mapa_global."""
        persona = self.repo.get_by_id(tenant_id, entity_id)
        if not persona:
            logger.warning(
                "buyer_persona_persister_not_found",
                tenant_id=str(tenant_id),
                entity_id=str(entity_id),
            )
            return None

        updates = self._build_updates(mapa_global, fields_to_persist)
        if updates:
            self.repo.update(
                tenant_id=tenant_id,
                persona_id=entity_id,
                updates=updates,
            )
            logger.info(
                "buyer_persona_persister_updated",
                tenant_id=str(tenant_id),
                entity_id=str(entity_id),
                fields_updated=len(updates),
            )
        return entity_id

    def _create_new(
        self,
        tenant_id: UUID,
        mapa_global: dict,
        fields_to_persist: list[str],
    ) -> UUID:
        """Create a new persona from mapa_global data."""
        updates = self._build_updates(mapa_global, fields_to_persist)
        persona = BuyerPersona(
            id=uuid4(),
            tenant_id=tenant_id,
            user_id=tenant_id,  # best-effort — interview may not have user context
            name=updates.pop("name", "Buyer Persona"),
            **updates,
        )
        created = self.repo.create(persona)
        logger.info(
            "buyer_persona_persister_created",
            tenant_id=str(tenant_id),
            entity_id=str(created.id),
        )
        return created.id

    @staticmethod
    def _build_updates(
        mapa_global: dict,
        fields_to_persist: list[str],
    ) -> dict:
        """Convert flat field paths to a dict suitable for repo.update().

        Dot-notation paths (e.g. ``demographics.age_range``) are merged
        into their parent dict.  Direct fields (e.g. ``pain_points``)
        are passed through.
        """
        updates: dict = {}

        for field_path in fields_to_persist:
            if field_path not in mapa_global:
                continue

            value = mapa_global[field_path]

            if "." in field_path:
                parent, key = field_path.split(".", 1)
                if parent in _DICT_FIELDS:
                    if parent not in updates:
                        updates[parent] = {}
                    updates[parent][key] = value
            else:
                updates[field_path] = value

        return updates
```

- [ ] **Step 4: Update persister registry**

Edit `backend/src/modules/copilot/infrastructure/persisters/persister_registry.py`:

Add import:
```python
from src.modules.copilot.infrastructure.persisters.buyer_persona_persister import (
    BuyerPersonaPersister,
)
```

Update return type and registry dict:
```python
def get_persister(
    domain: str,
    db: Session,
) -> BrandPersister | BuyerPersonaPersister | OfferPersister:
    """Get the appropriate persister for a domain."""
    registry: dict[str, type[BrandPersister | BuyerPersonaPersister | OfferPersister]] = {
        "brand": BrandPersister,
        "buyer_persona": BuyerPersonaPersister,
        "offer": OfferPersister,
    }
```

- [ ] **Step 5: Run tests**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/test_buyer_persona_persister.py -x -q --tb=short`
Expected: 8 passed

- [ ] **Step 6: Verify lint**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py src/modules/copilot/infrastructure/persisters/persister_registry.py --no-cache`
Expected: All checks passed!

- [ ] **Step 7: Verify architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: All passed (copilot is in CROSS_IMPORT_ALLOWED_SOURCES)

- [ ] **Step 8: Commit**

```bash
git add backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py backend/src/modules/copilot/infrastructure/persisters/persister_registry.py backend/tests/modules/copilot/test_buyer_persona_persister.py
git commit -m "feat(copilot): add BuyerPersonaPersister + register in persister_registry

Interview Engine can now persist buyer persona data from mapa_global.
Supports create (no entity_id) and update (with entity_id).
Dot-notation for dict fields, direct for lists. 8 tests."
```

---

## Task 4: Backend — Per-Domain Initial Messages

**Files:**
- Modify: `backend/src/modules/copilot/application/services/interview_service.py`

- [ ] **Step 1: Add INITIAL_MESSAGES dict and update start_interview**

In `interview_service.py`, add the following dict after `DOMAIN_LABELS` (line ~37):

```python
INITIAL_MESSAGES: dict[str, str] = {
    "brand": (
        "¡Hola! Vamos a construir tu marca juntos. "
        "Cuéntame, ¿cómo nació tu negocio?"
    ),
    "buyer_persona": (
        "Un buyer persona es el perfil de tu cliente ideal: quién es, "
        "qué le duele, qué desea. Vamos a construirlo juntos con preguntas "
        "simples.\n\n"
        "Para empezar — ¿cómo quieres llamarle a este segmento de clientes?"
    ),
    "offer": (
        "¡Hola! Vamos a construir tu oferta juntos. "
        "Cuéntame, ¿qué problema resuelve tu producto o servicio?"
    ),
}

_DEFAULT_INITIAL = (
    "¡Hola! Vamos a construir tu {label} juntos. "
    "Cuéntame, ¿cómo nació tu negocio?"
)
```

Then update the two places where `initial_message` is returned in `start_interview`. Replace the hardcoded string at line ~143-146 and line ~154-157 with:

```python
"initial_message": INITIAL_MESSAGES.get(
    domain,
    _DEFAULT_INITIAL.format(label=DOMAIN_LABELS.get(domain, "proyecto")),
),
```

- [ ] **Step 2: Run existing copilot tests**

Run: `cd backend && .venv/bin/pytest tests/modules/copilot/ -x -q --tb=short`
Expected: All passed

- [ ] **Step 3: Verify lint**

Run: `cd backend && .venv/bin/ruff check src/modules/copilot/application/services/interview_service.py --no-cache`
Expected: All checks passed!

- [ ] **Step 4: Commit**

```bash
git add backend/src/modules/copilot/application/services/interview_service.py
git commit -m "feat(copilot): add per-domain initial messages for interview engine

buyer_persona gets KISS explanation + name question.
brand and offer keep their existing greetings.
Fallback for unknown domains."
```

---

## Task 5: Frontend — API Client + Hook

**Files:**
- Create: `frontend/src/lib/api/buyer-persona.ts`
- Create: `frontend/src/features/brand/hooks/useBuyerPersonas.ts`
- Create: `frontend/src/features/brand/hooks/__tests__/useBuyerPersonas.test.ts`

- [ ] **Step 1: Write hook test**

```typescript
import { describe, it, expect, vi, beforeEach } from "vitest";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

// Mock Clerk
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
  }),
}));

// Mock the API module
const mockList = vi.fn();
vi.mock("@/lib/api/buyer-persona", () => ({
  buyerPersonaApi: {
    list: (...args: unknown[]) => mockList(...args),
  },
}));

import { useBuyerPersonas } from "../useBuyerPersonas";

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });
  return function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(
      QueryClientProvider,
      { client: queryClient },
      children,
    );
  };
}

describe("useBuyerPersonas", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("fetches buyer personas and returns data", async () => {
    const personas = [
      { id: "1", name: "Mamá Rural", completeness_score: 45 },
      { id: "2", name: "Joven Pro", completeness_score: 80 },
    ];
    mockList.mockResolvedValue(personas);

    const { result } = renderHook(() => useBuyerPersonas(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));

    expect(result.current.personas).toHaveLength(2);
    expect(result.current.personas[0].name).toBe("Mamá Rural");
    expect(mockList).toHaveBeenCalledWith("test-token");
  });

  it("returns empty array when API returns empty", async () => {
    mockList.mockResolvedValue([]);

    const { result } = renderHook(() => useBuyerPersonas(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.personas).toHaveLength(0);
  });

  it("handles fetch error gracefully", async () => {
    mockList.mockRejectedValue(new Error("Network error"));

    const { result } = renderHook(() => useBuyerPersonas(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => expect(result.current.isLoading).toBe(false));
    expect(result.current.personas).toHaveLength(0);
  });
});
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd frontend && npx vitest run src/features/brand/hooks/__tests__/useBuyerPersonas.test.ts`
Expected: FAIL — module `@/lib/api/buyer-persona` or `../useBuyerPersonas` not found

- [ ] **Step 3: Create API client**

Create `frontend/src/lib/api/buyer-persona.ts`:

```typescript
import { config } from "../config";
import { fetchClient } from "../http-client";

const API_URL = config.api.baseUrl;

export interface BuyerPersona {
  id: string;
  name: string;
  tagline: string | null;
  scope: string;
  is_primary: boolean;
  demographics: Record<string, unknown>;
  psychographics: Record<string, unknown>;
  pain_points: Record<string, unknown>[];
  desires: Record<string, unknown>[];
  objections: Record<string, unknown>[];
  preferred_channels: Record<string, unknown>[];
  buyer_journey: Record<string, unknown>;
  purchase_triggers: string[];
  anti_patterns: string[];
  completeness_score: number;
  interview_session_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface BuyerPersonaCreateDTO {
  name: string;
  tagline?: string;
  scope?: string;
  offer_id?: string;
}

export type BuyerPersonaSectionUpdateDTO = Partial<
  Pick<
    BuyerPersona,
    | "name"
    | "tagline"
    | "demographics"
    | "psychographics"
    | "pain_points"
    | "desires"
    | "objections"
    | "preferred_channels"
    | "buyer_journey"
    | "purchase_triggers"
    | "anti_patterns"
  >
>;

export const buyerPersonaApi = {
  list: async (token: string): Promise<BuyerPersona[]> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to list buyer personas");
    return res.json();
  },

  get: async (token: string, id: string): Promise<BuyerPersona> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/${id}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to get buyer persona");
    return res.json();
  },

  create: async (token: string, data: BuyerPersonaCreateDTO): Promise<BuyerPersona> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to create buyer persona");
    return res.json();
  },

  patch: async (
    token: string,
    id: string,
    data: BuyerPersonaSectionUpdateDTO,
  ): Promise<BuyerPersona> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/${id}`, {
      method: "PATCH",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    });
    if (!res.ok) throw new Error("Failed to update buyer persona");
    return res.json();
  },

  delete: async (token: string, id: string): Promise<void> => {
    const res = await fetchClient(`${API_URL}/api/v1/brand/buyer-personas/${id}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error("Failed to delete buyer persona");
  },
};
```

- [ ] **Step 4: Create hook**

Create `frontend/src/features/brand/hooks/useBuyerPersonas.ts`:

```typescript
"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@clerk/nextjs";
import {
  buyerPersonaApi,
  type BuyerPersona,
  type BuyerPersonaCreateDTO,
  type BuyerPersonaSectionUpdateDTO,
} from "@/lib/api/buyer-persona";

const QUERY_KEY = ["buyer_personas"] as const;

export function useBuyerPersonas() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery<BuyerPersona[]>({
    queryKey: QUERY_KEY,
    queryFn: async () => {
      const token = await getToken();
      if (!token) return [];
      return buyerPersonaApi.list(token);
    },
    retry: (failureCount, err: Error) => {
      if (err.message.includes("401") || err.message.includes("404")) return false;
      return failureCount < 2;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (dto: BuyerPersonaCreateDTO) => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return buyerPersonaApi.create(token, dto);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const patchMutation = useMutation({
    mutationFn: async ({
      id,
      data: patchData,
    }: {
      id: string;
      data: BuyerPersonaSectionUpdateDTO;
    }) => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return buyerPersonaApi.patch(token, id, patchData);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return buyerPersonaApi.delete(token, id);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  return {
    personas: data ?? [],
    isLoading,
    error,
    create: createMutation.mutateAsync,
    patch: patchMutation.mutateAsync,
    remove: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isPatching: patchMutation.isPending,
  };
}
```

- [ ] **Step 5: Run hook test**

Run: `cd frontend && npx vitest run src/features/brand/hooks/__tests__/useBuyerPersonas.test.ts`
Expected: 3 passed

- [ ] **Step 6: Verify types compile**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -20`
Expected: No new errors

- [ ] **Step 7: Commit**

```bash
git add frontend/src/lib/api/buyer-persona.ts frontend/src/features/brand/hooks/useBuyerPersonas.ts frontend/src/features/brand/hooks/__tests__/useBuyerPersonas.test.ts
git commit -m "feat(brand): add buyerPersonaApi client + useBuyerPersonas hook

API client: list, get, create, patch, delete.
Hook: React Query with create/patch/delete mutations.
3 hook tests (happy path, empty, error)."
```

---

## Task 6: Frontend — Migrate AvatarsSection → BuyerPersona Cards + Empty State

**Files:**
- Modify: `frontend/src/features/brand/sections/avatars/avatars-preview.tsx`

This is the largest frontend task. It replaces the Avatar-based grid with:
1. Empty state: two CTAs (Modo Inteligente / Modo Manual)
2. Persona cards: avatar initials + completeness bar + Focus chip

- [ ] **Step 1: Rewrite avatars-preview.tsx**

Replace the entire content of `frontend/src/features/brand/sections/avatars/avatars-preview.tsx`:

```tsx
"use client";

import { Users, Sparkles, PenLine, Plus } from "lucide-react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import { FocusModeButton } from "@/features/copilot/components/focus-mode-button";
import { useCopilotStore } from "@/features/copilot/store/copilot-store";
import { useBuyerPersonas } from "../../hooks/useBuyerPersonas";
import { buyerPersonaApi } from "@/lib/api/buyer-persona";

interface AvatarsSectionProps {
  onStartInterview?: () => void;
}

export function AvatarsSection({ onStartInterview }: AvatarsSectionProps) {
  const { getToken } = useAuth();
  const router = useRouter();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params.tenantId;

  const { personas, isLoading, create } = useBuyerPersonas();

  const setSidebarState = useCopilotStore((s) => s.setSidebarState);
  const setFocusEntity = useCopilotStore((s) => s.setFocusEntity);
  const setFocusSnapshot = useCopilotStore((s) => s.setFocusSnapshot);
  const clearSelectedFields = useCopilotStore((s) => s.clearSelectedFields);

  const handleModoInteligente = async () => {
    try {
      const persona = await create({ name: "Mi buyer persona" });
      const token = await getToken();
      if (!token) return;

      // Start interview via copilot API
      const res = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/v1/copilot/interview/start`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            domain: "buyer_persona",
            entity_id: persona.id,
          }),
        },
      );

      if (!res.ok) {
        // Fallback: just open focus mode without interview
        setFocusEntity({
          domain: "buyer_persona",
          entityId: persona.id,
          label: persona.name,
        });
        setFocusSnapshot(persona as unknown as Record<string, unknown>);
        clearSelectedFields();
        setSidebarState("expanded");
        return;
      }

      const interview = await res.json();

      // Set copilot store state for interview mode
      const store = useCopilotStore.getState();
      store.setFocusEntity({
        domain: "buyer_persona",
        entityId: persona.id,
        label: persona.name,
      });
      store.setFocusSnapshot(persona as unknown as Record<string, unknown>);
      if (interview.session_id) {
        store.setInterviewSession(interview.session_id);
      }
      if (interview.conversation_id) {
        store.setConversationId(interview.conversation_id);
      }
      if (interview.initial_message) {
        store.addMessage({
          role: "assistant",
          content: interview.initial_message,
        });
      }
      store.clearSelectedFields();
      store.setSidebarState("expanded");
    } catch (err) {
      console.error("Failed to start intelligent mode:", err);
    }

    onStartInterview?.();
  };

  const handleModoManual = async () => {
    try {
      const persona = await create({ name: "Mi buyer persona" });
      router.push(`/${tenantId}/brand-studio/publico/persona/${persona.id}`);
    } catch (err) {
      console.error("Failed to create persona:", err);
    }
  };

  const handleCardClick = (personaId: string) => {
    router.push(`/${tenantId}/brand-studio/publico/persona/${personaId}`);
  };

  if (isLoading) {
    return (
      <section className="group relative -mx-4 p-6 rounded-xl">
        <div className="flex items-center gap-3 mb-6 text-muted-foreground">
          <div className="p-2 rounded-md bg-muted">
            <Users className="w-5 h-5" />
          </div>
          <h3 className="text-sm font-semibold uppercase tracking-wider">
            Buyer Personas
          </h3>
        </div>
        <div className="flex gap-4">
          <Skeleton className="h-32 w-40 rounded-xl" />
          <Skeleton className="h-32 w-40 rounded-xl" />
          <Skeleton className="h-32 w-40 rounded-xl" />
        </div>
      </section>
    );
  }

  const hasPersonas = personas.length > 0;

  return (
    <section className="group relative -mx-4 p-6 rounded-xl transition-all duration-300 hover:bg-muted/40">
      {/* Header */}
      <div className="flex items-center gap-3 mb-6 text-muted-foreground group-hover:text-primary transition-colors">
        <div className="p-2 rounded-md bg-muted group-hover:bg-primary/10 transition-colors">
          <Users className="w-5 h-5" />
        </div>
        <h3 className="text-sm font-semibold uppercase tracking-wider">
          Buyer Personas
        </h3>
      </div>

      {!hasPersonas ? (
        /* Empty state — mode selection */
        <div className="flex flex-col items-center justify-center py-10 text-center border-2 border-dashed rounded-xl bg-muted/20 hover:bg-muted/30 transition-colors">
          <div className="w-12 h-12 rounded-full bg-purple-100 text-purple-600 flex items-center justify-center mb-4 shadow-sm">
            <Users className="w-6 h-6" />
          </div>
          <h3 className="text-lg font-semibold mb-2">Sin Buyer Personas</h3>
          <p className="text-sm text-muted-foreground mb-6 max-w-sm leading-relaxed">
            ¿Cómo quieres crear tu primer buyer persona?
          </p>
          <div className="flex gap-4">
            <Button
              onClick={handleModoInteligente}
              className="shadow-lg shadow-purple-500/20 bg-gradient-to-r from-purple-600 to-indigo-600 hover:from-purple-700 hover:to-indigo-700 text-white border-none"
            >
              <Sparkles className="w-4 h-4 mr-2" />
              Modo Inteligente
            </Button>
            <Button
              variant="outline"
              onClick={handleModoManual}
            >
              <PenLine className="w-4 h-4 mr-2" />
              Modo Manual
            </Button>
          </div>
        </div>
      ) : (
        /* Persona cards grid */
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {personas.map((persona) => (
            <div
              key={persona.id}
              className="flex flex-col items-center p-4 rounded-xl border border-border/50 bg-card hover:border-primary/30 hover:bg-muted/40 transition-all cursor-pointer"
              onClick={() => handleCardClick(persona.id)}
            >
              <Avatar className="h-14 w-14 mb-3">
                <AvatarFallback className="text-sm font-bold bg-gradient-to-br from-purple-500 to-indigo-600 text-white">
                  {persona.name.substring(0, 2).toUpperCase()}
                </AvatarFallback>
              </Avatar>
              <h4 className="font-medium text-sm text-center truncate w-full">
                {persona.name}
              </h4>
              <div className="w-full mt-2 mb-3">
                <Progress
                  value={persona.completeness_score}
                  className="h-1.5"
                />
                <span className="text-[10px] text-muted-foreground mt-1 block text-center">
                  {Math.round(persona.completeness_score)}% completo
                </span>
              </div>
              <FocusModeButton
                domain="buyer_persona"
                entityId={persona.id}
                label={persona.name}
                entityData={persona as unknown as Record<string, unknown>}
                className="w-full rounded-full text-xs h-7"
              />
            </div>
          ))}

          {/* Add new persona card */}
          <div
            className="flex flex-col items-center justify-center p-4 rounded-xl border-2 border-dashed border-border/50 hover:border-primary/30 hover:bg-muted/30 transition-all cursor-pointer min-h-[180px]"
            onClick={handleModoManual}
          >
            <Plus className="w-6 h-6 text-muted-foreground mb-2" />
            <span className="text-sm text-muted-foreground">Nueva Persona</span>
          </div>
        </div>
      )}
    </section>
  );
}
```

- [ ] **Step 2: Verify types compile**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No errors in avatars-preview.tsx

- [ ] **Step 3: Verify lint**

Run: `cd frontend && npx eslint src/features/brand/sections/avatars/avatars-preview.tsx`
Expected: No errors (warnings OK)

- [ ] **Step 4: Commit**

```bash
git add frontend/src/features/brand/sections/avatars/avatars-preview.tsx
git commit -m "feat(brand): migrate AvatarsSection to BuyerPersona cards + mode selection

Empty state: Modo Inteligente (interview) + Modo Manual (detail page).
Cards: avatar initials, completeness Progress bar, Focus chip.
Uses useBuyerPersonas hook + buyerPersonaApi."
```

---

## Task 7: Frontend — Persona Detail Page (Modo Manual)

**Files:**
- Create: `frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/publico/persona/[personaId]/page.tsx`

This page follows the same pattern as Offer Studio: full-width, left nav with sections, right form area.

- [ ] **Step 1: Create directory and page file**

First verify parent directories exist:
```bash
ls frontend/src/app/\(main\)/\[tenantId\]/\(dashboard\)/brand-studio/
```

Create the page file:

```tsx
"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import { useAuth } from "@clerk/nextjs";
import { ArrowLeft, Save, Check } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Progress } from "@/components/ui/progress";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { cn } from "@/lib/utils";
import { buyerPersonaApi } from "@/lib/api/buyer-persona";
import type { BuyerPersona, BuyerPersonaSectionUpdateDTO } from "@/lib/api/buyer-persona";
import { WithCopilot } from "@/features/copilot/components/WithCopilot";
import { FocusModeButton } from "@/features/copilot/components/focus-mode-button";

/* ─────────────── Section definitions ─────────────── */

interface SectionDef {
  id: string;
  label: string;
  icon: string;
  description: string;
}

const SECTIONS: SectionDef[] = [
  {
    id: "demographics",
    label: "Demografía",
    icon: "👤",
    description: "¿Quién es esta persona? Edad, ubicación, ocupación.",
  },
  {
    id: "pain_desire",
    label: "Dolores & Deseos",
    icon: "😣",
    description: "¿Qué le frustra y qué aspira conseguir?",
  },
  {
    id: "psychographics",
    label: "Psicografía",
    icon: "🧠",
    description: "Valores, creencias, estilo de vida.",
  },
  {
    id: "objections",
    label: "Objeciones",
    icon: "🚧",
    description: "Barreras de compra y triggers.",
  },
  {
    id: "channels_journey",
    label: "Canales & Journey",
    icon: "🗺️",
    description: "Dónde vive digitalmente y cómo compra.",
  },
];

/* ─────────────── Section status ─────────────── */

type SectionStatus = "empty" | "partial" | "done";

function getSectionStatus(persona: BuyerPersona, sectionId: string): SectionStatus {
  switch (sectionId) {
    case "demographics": {
      const d = persona.demographics;
      if (!d || Object.keys(d).length === 0) return "empty";
      return Object.keys(d).length >= 3 ? "done" : "partial";
    }
    case "pain_desire": {
      const hasPains = persona.pain_points.length > 0;
      const hasDesires = persona.desires.length > 0;
      if (!hasPains && !hasDesires) return "empty";
      return hasPains && hasDesires ? "done" : "partial";
    }
    case "psychographics": {
      const p = persona.psychographics;
      if (!p || Object.keys(p).length === 0) return "empty";
      return Object.keys(p).length >= 3 ? "done" : "partial";
    }
    case "objections": {
      const hasObj = persona.objections.length > 0;
      const hasTrig = persona.purchase_triggers.length > 0;
      if (!hasObj && !hasTrig) return "empty";
      return hasObj && hasTrig ? "done" : "partial";
    }
    case "channels_journey": {
      const hasCh = persona.preferred_channels.length > 0;
      const hasJ = persona.buyer_journey && Object.keys(persona.buyer_journey).length > 0;
      if (!hasCh && !hasJ) return "empty";
      return hasCh && hasJ ? "done" : "partial";
    }
    default:
      return "empty";
  }
}

/* ─────────────── List field component ─────────────── */

function ListField({
  items,
  displayKey,
  placeholder,
  onAdd,
  onRemove,
}: {
  items: Record<string, unknown>[];
  displayKey: string;
  placeholder: string;
  onAdd: (value: string) => void;
  onRemove: (index: number) => void;
}) {
  const [newValue, setNewValue] = useState("");

  const handleAdd = () => {
    if (newValue.trim()) {
      onAdd(newValue.trim());
      setNewValue("");
    }
  };

  return (
    <div className="space-y-2">
      {items.map((item, idx) => (
        <div
          key={idx}
          className="flex items-center gap-2 bg-muted/50 border rounded-md px-3 py-2"
        >
          <span className="text-sm flex-1">
            {String(item[displayKey] ?? item.description ?? item.objection ?? JSON.stringify(item))}
          </span>
          <button
            type="button"
            onClick={() => onRemove(idx)}
            className="text-xs text-muted-foreground hover:text-destructive"
          >
            ✕
          </button>
        </div>
      ))}
      <div className="flex gap-2">
        <Input
          value={newValue}
          onChange={(e) => setNewValue(e.target.value)}
          placeholder={placeholder}
          className="text-sm"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleAdd();
            }
          }}
        />
        <Button type="button" variant="outline" size="sm" onClick={handleAdd}>
          +
        </Button>
      </div>
    </div>
  );
}

/* ─────────────── String list field ─────────────── */

function StringListField({
  items,
  placeholder,
  onAdd,
  onRemove,
}: {
  items: string[];
  placeholder: string;
  onAdd: (value: string) => void;
  onRemove: (index: number) => void;
}) {
  const [newValue, setNewValue] = useState("");

  const handleAdd = () => {
    if (newValue.trim()) {
      onAdd(newValue.trim());
      setNewValue("");
    }
  };

  return (
    <div className="space-y-2">
      {items.map((item, idx) => (
        <div
          key={idx}
          className="flex items-center gap-2 bg-muted/50 border rounded-md px-3 py-2"
        >
          <span className="text-sm flex-1">{item}</span>
          <button
            type="button"
            onClick={() => onRemove(idx)}
            className="text-xs text-muted-foreground hover:text-destructive"
          >
            ✕
          </button>
        </div>
      ))}
      <div className="flex gap-2">
        <Input
          value={newValue}
          onChange={(e) => setNewValue(e.target.value)}
          placeholder={placeholder}
          className="text-sm"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              handleAdd();
            }
          }}
        />
        <Button type="button" variant="outline" size="sm" onClick={handleAdd}>
          +
        </Button>
      </div>
    </div>
  );
}

/* ─────────────── Main page ─────────────── */

export default function PersonaDetailPage() {
  const { personaId, tenantId } = useParams<{
    personaId: string;
    tenantId: string;
  }>();
  const router = useRouter();
  const { getToken } = useAuth();

  const [persona, setPersona] = useState<BuyerPersona | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [activeSection, setActiveSection] = useState("demographics");

  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Fetch persona
  useEffect(() => {
    let cancelled = false;
    (async () => {
      const token = await getToken();
      if (!token || cancelled) return;
      try {
        const data = await buyerPersonaApi.get(token, personaId);
        if (!cancelled) setPersona(data);
      } catch {
        if (!cancelled) router.push(`/${tenantId}/brand-studio`);
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [personaId, tenantId, getToken, router]);

  // Auto-save with debounce
  const autoSave = useCallback(
    (updates: BuyerPersonaSectionUpdateDTO) => {
      if (debounceRef.current) clearTimeout(debounceRef.current);
      debounceRef.current = setTimeout(async () => {
        const token = await getToken();
        if (!token) return;
        setSaving(true);
        try {
          const updated = await buyerPersonaApi.patch(token, personaId, updates);
          setPersona(updated);
          setSaved(true);
          setTimeout(() => setSaved(false), 2500);
        } catch (err) {
          console.error("Auto-save failed:", err);
        } finally {
          setSaving(false);
        }
      }, 1500);
    },
    [getToken, personaId],
  );

  // Field update helpers
  const updateDictField = (
    field: "demographics" | "psychographics" | "buyer_journey",
    key: string,
    value: string,
  ) => {
    if (!persona) return;
    const updated = { ...persona, [field]: { ...persona[field], [key]: value } };
    setPersona(updated);
    autoSave({ [field]: updated[field] });
  };

  const updateListField = (
    field: "pain_points" | "desires" | "objections" | "preferred_channels",
    newList: Record<string, unknown>[],
  ) => {
    if (!persona) return;
    const updated = { ...persona, [field]: newList };
    setPersona(updated);
    autoSave({ [field]: newList });
  };

  const updateStringListField = (
    field: "purchase_triggers" | "anti_patterns",
    newList: string[],
  ) => {
    if (!persona) return;
    const updated = { ...persona, [field]: newList };
    setPersona(updated);
    autoSave({ [field]: newList });
  };

  if (loading || !persona) {
    return (
      <div className="flex items-center justify-center h-[60vh]">
        <div className="animate-pulse text-muted-foreground">Cargando persona...</div>
      </div>
    );
  }

  /* ─────────────── Section renderers ─────────────── */

  const renderDemographics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {["age_range", "location", "occupation", "income_range", "education", "family_status"].map(
        (key) => (
          <WithCopilot
            key={key}
            fieldId={`demographics.${key}`}
            fieldLabel={key.replace(/_/g, " ")}
          >
            <div>
              <label className="text-xs font-medium text-muted-foreground capitalize mb-1 block">
                {key.replace(/_/g, " ")}
              </label>
              <Input
                value={String(persona.demographics[key] ?? "")}
                onChange={(e) => updateDictField("demographics", key, e.target.value)}
                placeholder={`Ej: ${key === "age_range" ? "25-35" : key === "location" ? "LATAM" : "..."}`}
                className="text-sm"
              />
            </div>
          </WithCopilot>
        ),
      )}
    </div>
  );

  const renderPainDesire = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <WithCopilot fieldId="pain_points" fieldLabel="Dolores principales">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-2 block">
            Dolores principales
          </label>
          <ListField
            items={persona.pain_points}
            displayKey="description"
            placeholder="Agregar dolor..."
            onAdd={(v) =>
              updateListField("pain_points", [
                ...persona.pain_points,
                { description: v, intensity: "medium" },
              ])
            }
            onRemove={(i) =>
              updateListField(
                "pain_points",
                persona.pain_points.filter((_, idx) => idx !== i),
              )
            }
          />
        </div>
      </WithCopilot>
      <WithCopilot fieldId="desires" fieldLabel="Deseos principales">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-2 block">
            Deseos principales
          </label>
          <ListField
            items={persona.desires}
            displayKey="description"
            placeholder="Agregar deseo..."
            onAdd={(v) =>
              updateListField("desires", [
                ...persona.desires,
                { description: v, priority: "medium" },
              ])
            }
            onRemove={(i) =>
              updateListField(
                "desires",
                persona.desires.filter((_, idx) => idx !== i),
              )
            }
          />
        </div>
      </WithCopilot>
    </div>
  );

  const renderPsychographics = () => (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {["values", "beliefs", "lifestyle", "personality_traits", "media_consumption"].map((key) => (
        <WithCopilot
          key={key}
          fieldId={`psychographics.${key}`}
          fieldLabel={key.replace(/_/g, " ")}
        >
          <div>
            <label className="text-xs font-medium text-muted-foreground capitalize mb-1 block">
              {key.replace(/_/g, " ")}
            </label>
            <Textarea
              value={
                typeof persona.psychographics[key] === "string"
                  ? (persona.psychographics[key] as string)
                  : Array.isArray(persona.psychographics[key])
                    ? (persona.psychographics[key] as string[]).join(", ")
                    : ""
              }
              onChange={(e) => updateDictField("psychographics", key, e.target.value)}
              placeholder={`Describe ${key.replace(/_/g, " ")}...`}
              rows={2}
              className="text-sm resize-none"
            />
          </div>
        </WithCopilot>
      ))}
    </div>
  );

  const renderObjections = () => (
    <div className="space-y-6">
      <WithCopilot fieldId="objections" fieldLabel="Objeciones">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-2 block">
            Objeciones
          </label>
          <ListField
            items={persona.objections}
            displayKey="objection"
            placeholder="Agregar objeción..."
            onAdd={(v) =>
              updateListField("objections", [
                ...persona.objections,
                { objection: v, root_cause: "" },
              ])
            }
            onRemove={(i) =>
              updateListField(
                "objections",
                persona.objections.filter((_, idx) => idx !== i),
              )
            }
          />
        </div>
      </WithCopilot>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <WithCopilot fieldId="purchase_triggers" fieldLabel="Triggers de compra">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block">
              Triggers de compra
            </label>
            <StringListField
              items={persona.purchase_triggers}
              placeholder="Agregar trigger..."
              onAdd={(v) =>
                updateStringListField("purchase_triggers", [...persona.purchase_triggers, v])
              }
              onRemove={(i) =>
                updateStringListField(
                  "purchase_triggers",
                  persona.purchase_triggers.filter((_, idx) => idx !== i),
                )
              }
            />
          </div>
        </WithCopilot>
        <WithCopilot fieldId="anti_patterns" fieldLabel="Anti-patrones">
          <div>
            <label className="text-xs font-medium text-muted-foreground mb-2 block">
              Anti-patrones
            </label>
            <StringListField
              items={persona.anti_patterns}
              placeholder="Agregar anti-patrón..."
              onAdd={(v) =>
                updateStringListField("anti_patterns", [...persona.anti_patterns, v])
              }
              onRemove={(i) =>
                updateStringListField(
                  "anti_patterns",
                  persona.anti_patterns.filter((_, idx) => idx !== i),
                )
              }
            />
          </div>
        </WithCopilot>
      </div>
    </div>
  );

  const renderChannelsJourney = () => (
    <div className="space-y-6">
      <WithCopilot fieldId="preferred_channels" fieldLabel="Canales preferidos">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-2 block">
            Canales preferidos
          </label>
          <ListField
            items={persona.preferred_channels}
            displayKey="channel"
            placeholder="Agregar canal..."
            onAdd={(v) =>
              updateListField("preferred_channels", [
                ...persona.preferred_channels,
                { channel: v, usage_pattern: "" },
              ])
            }
            onRemove={(i) =>
              updateListField(
                "preferred_channels",
                persona.preferred_channels.filter((_, idx) => idx !== i),
              )
            }
          />
        </div>
      </WithCopilot>
      <WithCopilot fieldId="buyer_journey" fieldLabel="Buyer Journey">
        <div>
          <label className="text-xs font-medium text-muted-foreground mb-2 block">
            Buyer Journey
          </label>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {["awareness", "consideration", "decision"].map((stage) => (
              <div key={stage}>
                <label className="text-[10px] font-medium text-muted-foreground uppercase mb-1 block">
                  {stage}
                </label>
                <Textarea
                  value={String(persona.buyer_journey[stage] ?? "")}
                  onChange={(e) => updateDictField("buyer_journey", stage, e.target.value)}
                  placeholder={`¿Cómo ${stage === "awareness" ? "descubre" : stage === "consideration" ? "evalúa" : "decide"}?`}
                  rows={3}
                  className="text-sm resize-none"
                />
              </div>
            ))}
          </div>
        </div>
      </WithCopilot>
    </div>
  );

  const sectionRenderers: Record<string, () => React.ReactNode> = {
    demographics: renderDemographics,
    pain_desire: renderPainDesire,
    psychographics: renderPsychographics,
    objections: renderObjections,
    channels_journey: renderChannelsJourney,
  };

  const currentSection = SECTIONS.find((s) => s.id === activeSection);

  return (
    <div className="flex flex-col h-[calc(100vh-4rem)] -m-6 md:-m-8">
      {/* Topbar */}
      <div className="flex items-center gap-3 px-5 py-2.5 border-b bg-card/50 shrink-0">
        <Button
          variant="ghost"
          size="sm"
          onClick={() => router.push(`/${tenantId}/brand-studio`)}
          className="text-xs text-muted-foreground"
        >
          <ArrowLeft className="w-3.5 h-3.5 mr-1" />
          Buyer Personas
        </Button>
        <span className="text-muted-foreground/50">/</span>
        <span className="text-sm font-medium">{persona.name}</span>
        <div className="ml-auto flex items-center gap-2 text-xs text-muted-foreground">
          {saving && <span>Guardando...</span>}
          {saved && (
            <span className="flex items-center gap-1 text-emerald-500">
              <Check className="w-3 h-3" /> Guardado
            </span>
          )}
          <FocusModeButton
            domain="buyer_persona"
            entityId={persona.id}
            label={persona.name}
            entityData={persona as unknown as Record<string, unknown>}
            className="text-xs h-7"
          />
        </div>
      </div>

      {/* Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* Left nav */}
        <nav className="w-[220px] shrink-0 border-r bg-card/30 flex flex-col">
          <div className="p-4 border-b flex items-center gap-3">
            <Avatar className="h-10 w-10">
              <AvatarFallback className="text-xs font-bold bg-gradient-to-br from-purple-500 to-indigo-600 text-white">
                {persona.name.substring(0, 2).toUpperCase()}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0">
              <div className="text-sm font-semibold truncate">{persona.name}</div>
              <div className="text-[10px] text-muted-foreground">
                {Math.round(persona.completeness_score)}% completo
              </div>
            </div>
          </div>
          <div className="flex-1 p-2 space-y-0.5">
            {SECTIONS.map((section) => {
              const status = getSectionStatus(persona, section.id);
              return (
                <button
                  key={section.id}
                  onClick={() => setActiveSection(section.id)}
                  className={cn(
                    "flex items-center gap-2 w-full px-3 py-2 rounded-lg text-left text-xs transition-all",
                    activeSection === section.id
                      ? "bg-purple-500/10 border border-purple-500/25 text-purple-300 font-semibold"
                      : "text-muted-foreground hover:bg-muted/50",
                  )}
                >
                  <div
                    className={cn(
                      "w-2 h-2 rounded-full shrink-0",
                      status === "done" && "bg-emerald-500",
                      status === "partial" && "bg-purple-500",
                      status === "empty" && "bg-muted-foreground/20",
                    )}
                  />
                  <span className="flex-1 truncate">{section.label}</span>
                  <span
                    className={cn(
                      "text-[9px] px-1.5 py-0.5 rounded-full",
                      status === "done" && "bg-emerald-500/15 text-emerald-400",
                      status === "partial" && "bg-purple-500/20 text-purple-400",
                      status === "empty" && "bg-muted text-muted-foreground/50",
                    )}
                  >
                    {status === "done" ? "✓" : status === "partial" ? "●" : "vacío"}
                  </span>
                </button>
              );
            })}
          </div>
          <div className="p-3 border-t">
            <div className="flex justify-between text-[9px] text-muted-foreground mb-1">
              <span>Completeness</span>
              <span>{Math.round(persona.completeness_score)}%</span>
            </div>
            <Progress value={persona.completeness_score} className="h-1" />
          </div>
        </nav>

        {/* Main form area */}
        <div className="flex-1 flex flex-col min-w-0">
          {currentSection && (
            <div className="flex items-center gap-3 px-6 py-3 border-b bg-card/20 shrink-0">
              <div className="w-8 h-8 rounded-lg bg-purple-500/15 flex items-center justify-center text-sm">
                {currentSection.icon}
              </div>
              <div>
                <div className="text-sm font-semibold">{currentSection.label}</div>
                <div className="text-[11px] text-muted-foreground">
                  {currentSection.description}
                </div>
              </div>
            </div>
          )}
          <div className="flex-1 overflow-y-auto p-6">
            {sectionRenderers[activeSection]?.()}
          </div>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Verify types compile**

Run: `cd frontend && npx tsc --noEmit 2>&1 | head -30`
Expected: No new errors

- [ ] **Step 3: Verify lint**

Run: `cd frontend && npx eslint "src/app/(main)/[tenantId]/(dashboard)/brand-studio/publico/persona/[personaId]/page.tsx"`
Expected: No errors (warnings are OK for a file this size — may hit max-lines warning which is Phase 1C)

- [ ] **Step 4: Commit**

```bash
git add "frontend/src/app/(main)/[tenantId]/(dashboard)/brand-studio/publico/persona/[personaId]/page.tsx"
git commit -m "feat(brand): add buyer persona detail page — manual edit with sections

Full-width page at /brand-studio/publico/persona/[id].
Left nav: 5 sections with status dots + completeness.
Auto-save with 1.5s debounce on field changes.
WithCopilot on every field for AI assistance.
Focus chip in topbar for switching to interview mode."
```

---

## Task 8: Full Backend + Frontend Test Pass

Final verification that everything works together.

- [ ] **Step 1: Run all backend tests**

Run: `cd backend && .venv/bin/pytest -x -q --tb=short`
Expected: All passed

- [ ] **Step 2: Run backend lint**

Run: `cd backend && .venv/bin/ruff check src/ tests/ --no-cache`
Expected: All checks passed!

- [ ] **Step 3: Run architecture tests**

Run: `cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short`
Expected: All passed

- [ ] **Step 4: Run frontend types**

Run: `cd frontend && npx tsc --noEmit`
Expected: No errors

- [ ] **Step 5: Run frontend lint**

Run: `cd frontend && npx eslint src/`
Expected: No new errors

- [ ] **Step 6: Run frontend tests**

Run: `cd frontend && npx vitest run`
Expected: All passed

- [ ] **Step 7: Verify no uncommitted changes**

Run: `git status --short`
Expected: Clean working tree (all changes committed in previous tasks)

---

## Dependency Graph

```
Task 0 (layout)           ─── independent
Task 1 (DTOs)             ─── independent
Task 2 (API + main.py)    ─── depends on Task 1
Task 3 (persister)        ─── independent (backend only)
Task 4 (initial messages) ─── independent (backend only)
Task 5 (API client+hook)  ─── independent (frontend only)
Task 6 (cards+empty state)─── depends on Task 5
Task 7 (detail page)      ─── depends on Task 5
Task 8 (full test pass)   ─── depends on all
```

**Parallelizable:** Tasks 0, 1, 3, 4, 5 can all run in parallel.
**Sequential:** 1→2 (DTOs first, then API), 5→6, 5→7, all→8.
