# Testing Patterns

**Analysis Date:** 2026-03-15

## Test Framework

**Backend Runner:**
- pytest (configured in `backend/pyproject.toml`)
- Run inside container: `docker exec -t visionarias_brain_dev pytest`
- No separate `pytest.ini` — using `pyproject.toml` defaults

**Frontend Runner:**
- Vitest with React plugin
- Config: `frontend/vitest.config.mts`
- Environment: `happy-dom`
- Globals enabled (no need to import `describe`, `it`, `expect` in test files)
- Setup file: `frontend/src/test/setup.ts` (imports `@testing-library/jest-dom`)

**Run Commands:**
```bash
# Backend (inside visionarias_brain_dev container)
docker exec -t visionarias_brain_dev pytest                      # All tests
docker exec -t visionarias_brain_dev pytest tests/modules/       # Module tests only
docker exec -t visionarias_brain_dev pytest tests/integration/   # Integration tests only

# Frontend (inside visionarias_client_dev container or local)
npx vitest run          # Run all tests once
npx vitest              # Watch mode
npx vitest --coverage   # Coverage report
```

## Test File Organization

**Backend:**
- Separate `tests/` directory at `backend/tests/`
- Mirrors module structure: `tests/modules/connections/`, `tests/integration/`
- Files named `test_X.py` (e.g., `test_webhooks.py`, `test_channel_security.py`)
- Shared fixtures in `backend/tests/conftest.py`
- Some ad-hoc scripts in `backend/src/modules/brand/tests/repro_issue.py` (not pytest files)

```
backend/
└── tests/
    ├── conftest.py                             # Shared fixtures (DB, session)
    ├── integration/
    │   └── test_brand_connection.py            # FastAPI TestClient integration tests
    └── modules/
        └── connections/
            ├── test_channel_security.py
            ├── test_instagram_channel.py
            ├── test_shopify_exchange.py
            └── test_webhooks.py
```

**Frontend:**
- Co-located tests within feature directories
- Two patterns observed:
  1. `__tests__/` subdirectory: `frontend/src/features/offer-studio/components/editor/sections/program-details/__tests__/`
  2. `tests/` directory at feature level: `frontend/src/features/offer-studio/tests/`
  3. Co-located `.test.ts` file: `frontend/src/features/brand/utils/brand-validation.test.ts`
- Also: `frontend/src/components/ui/label.test.tsx` (co-located with component)
- Files named `X.test.ts` or `X.test.tsx`

```
frontend/src/
├── components/ui/
│   └── label.test.tsx                         # Co-located component test
├── features/
│   ├── brand/utils/
│   │   └── brand-validation.test.ts           # Co-located util test
│   ├── offer-studio/
│   │   ├── tests/                             # Feature-level test dir
│   │   │   ├── fixtures.ts                    # Shared mock data
│   │   │   ├── dashboard-logic.test.tsx
│   │   │   └── offer-card.test.tsx
│   │   └── components/.../
│   │       └── __tests__/                     # Component-level test dir
│   │           ├── program-form.test.tsx
│   │           └── session-schedule-builder.test.tsx
│   └── marketing-studio/components/strategy-canvas/
│       └── __tests__/
│           └── StrategyCanvas.test.tsx
└── test/
    └── setup.ts                               # Global test setup
```

## Test Structure

**Backend Suite Organization:**
```python
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

# Fixtures defined with @pytest.fixture
@pytest.fixture
def mock_settings():
    with patch("src.modules.connections.api.dependencies.webhook_security.settings") as mock:
        mock.SHOPIFY_API_SECRET = "test_shopify_secret"
        yield mock

@pytest.fixture
def mock_db():
    mock_session = MagicMock()
    app.dependency_overrides[get_db] = lambda: mock_session
    yield mock_session
    app.dependency_overrides = {}  # Always clean up overrides

# Test functions (not classes)
def test_shopify_signature_valid(mock_settings, mock_db):
    # Arrange
    payload = {"test": "data"}
    body = json.dumps(payload).encode('utf-8')
    signature = generate_signature(secret, body)
    headers = {"X-Shopify-Hmac-Sha256": signature}

    # Act
    response = client.post("/api/v1/...", content=body, headers=headers)

    # Assert
    assert response.status_code == 200
    assert response.json() == {"status": "received"}
```

**Frontend Suite Organization:**
```typescript
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';

describe('ComponentName', () => {
  it('renders X correctly', () => {
    render(<Component prop={value} />);
    expect(screen.getByText("Expected Text")).toBeInTheDocument();
  });

  it('handles edge case Y', () => {
    const result = utilFunction(edgeInput);
    expect(result.status).toBe('expected');
    expect(result.score).toBe(0);
  });
});
```

## Mocking

**Backend Framework:** `unittest.mock` (`MagicMock`, `patch`)

**Backend Patterns:**
```python
# 1. Patch module-level settings
with patch("src.modules.X.api.dependencies.settings") as mock:
    mock.SOME_KEY = "test_value"
    yield mock

# 2. Override FastAPI dependencies for DB
mock_session = MagicMock()
app.dependency_overrides[get_db] = lambda: mock_session
# Always restore after test:
app.dependency_overrides = {}

# 3. Mock entire sys modules to avoid import chain
sys.modules["src.modules.iam.api.dependencies"] = MagicMock()
sys.modules["src.core.database"] = MagicMock()

# 4. Mock DB query chain
mock_db.query.return_value.filter.return_value.all.return_value = []
```

**Frontend Framework:** Vitest `vi.mock()`

**Frontend Patterns:**
```typescript
// 1. Mock Next.js navigation
vi.mock('next/navigation', () => ({
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: 'visionarias' }),
}));

// 2. Mock complex UI components (JSDOM incompatibility)
vi.mock('@/components/ui/smart-datetime-picker', () => ({
  SmartDateTimePicker: () => <div data-testid="smart-datetime-picker">Picker</div>
}));

// 3. Partial mock preserving real implementation
vi.mock('@visx/responsive', async () => {
  const actual = await vi.importActual('@visx/responsive');
  return {
    ...actual,
    ParentSize: ({ children }) => <div>{children({ width: 1200, height: 800 })}</div>,
  };
});
```

**What to Mock:**
- Next.js router (`next/navigation`) — JSDOM has no router
- UI components with canvas/SVG/resize dependencies (e.g., `@visx/responsive`, datetime pickers)
- External API calls (use mock data files, not live fetch)
- FastAPI `get_db` dependency — use SQLite in-memory or `MagicMock`
- App settings (`src.core.config.settings`) — patch with test values

**What NOT to Mock:**
- Domain/entity logic — test it directly
- Utility functions — test the real implementation
- Pydantic validation — test real models

## Fixtures and Factories

**Backend Shared Fixtures (`backend/tests/conftest.py`):**
```python
@pytest.fixture(scope="session")
def db_engine():
    # SQLite in-memory with PostgreSQL type patches (MockJSONB, MockUUID)
    engine = create_engine("sqlite:///:memory:", ...)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    # Each test gets isolated transaction, rolled back after
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(...)(connection)
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

**PostgreSQL Type Patching for SQLite Tests:**
- `MockJSONB` (maps `postgresql.JSONB` → `Text` with JSON serialization) defined in `conftest.py`
- `MockUUID` (maps `postgresql.UUID` → `CHAR(36)`) defined in `conftest.py`
- Applied via: `postgresql.JSONB = MockJSONB` before any model imports

**Frontend Fixtures:**
- Shared mock data in `tests/fixtures.ts` at feature level
- Example: `frontend/src/features/offer-studio/tests/fixtures.ts` exports `MOCK_BACKEND_RESPONSE`, `MOCK_OFFER_NORMALIZED`
- Mock data files in `api/mock-data.ts` per feature for runtime mock mode

**Test Data Pattern:**
```typescript
// frontend/src/features/offer-studio/tests/fixtures.ts
export const MOCK_BACKEND_RESPONSE = {
  public_name: "Guía: Liberar la Mente",
  status: "active",
  type: "FREE_RESOURCE",
  // ...
};

export const MOCK_OFFER_NORMALIZED = {
  name: "Guía: Liberar la Mente",
  status: OfferStatus.ACTIVE,
  type: OfferType.FREE_RESOURCE,
  // ...
};
```

## Coverage

**Requirements:** None enforced (no coverage thresholds configured)

**View Coverage (Frontend):**
```bash
npx vitest --coverage
```

**View Coverage (Backend):**
```bash
docker exec -t visionarias_brain_dev pytest --cov=src --cov-report=html
```

## Test Types

**Backend Unit Tests:**
- Not prominently used — most backend tests are integration tests
- `backend/src/modules/brand/tests/repro_issue.py` is a reproduction script, not a pytest suite

**Backend Integration Tests:**
- Location: `backend/tests/`
- Use `FastAPI.TestClient` for HTTP-level testing
- Test full request/response cycle including middleware, auth, and DB
- Example: `tests/modules/connections/test_webhooks.py` — tests HMAC signature validation end-to-end

**Frontend Unit Tests:**
- Utility functions: `brand-validation.test.ts` — pure function tests with `describe/it/expect`
- Adapter logic: `dashboard-logic.test.tsx` — data transformation unit tests

**Frontend Component Tests:**
- Use `@testing-library/react` `render` + `screen` queries
- Assert on rendered text and DOM presence
- Mock external dependencies (router, complex UI components)
- Example: `offer-card.test.tsx`, `program-form.test.tsx`, `StrategyCanvas.test.tsx`

**E2E Tests:**
- Not detected in codebase

## Common Patterns

**Async Testing (Frontend):**
```typescript
import { waitFor } from '@testing-library/react';

it('renders after async load', async () => {
  render(<StrategyCanvas config={MOCK_CONFIG} />);
  await waitFor(() => {
    expect(screen.queryByText(/Error:/i)).not.toBeInTheDocument();
    expect(screen.getByText('Universo')).toBeInTheDocument();
  });
});

// Or with findBy (implicit waitFor):
expect(await screen.findByText('Universo')).toBeInTheDocument();
```

**Error/Edge Case Testing (Frontend):**
```typescript
it('handles unknown Enums gracefully', () => {
  const weirdData = { ...MOCK_BACKEND_RESPONSE, type: "UNKNOWN_TYPE_XYZ" };
  const result = backendToFrontend(weirdData as any);
  expect(result.type).toBe(OfferType.FREE_RESOURCE); // Fallback, not crash
});
```

**Wrapper Pattern for Form Tests:**
```typescript
// When component requires form context, wrap in a helper component
function Wrapper() {
  const form = useForm<OfferFormValues>({ defaultValues: { ... } });
  return (
    <Form {...form}>
      <ComponentUnderTest form={form} onSave={async () => {}} />
    </Form>
  );
}

it('renders without crashing', () => {
  render(<Wrapper />);
  expect(screen.getByText('Expected Label')).toBeDefined();
});
```

**Tenant Context in Backend Tests:**
```python
# Always set tenant_id on test data
tenant_id = str(uuid.uuid4())
tenant = MockTenantModel(id=tenant_id, ...)
db.add(tenant)
db.commit()

# Override user dependency to return tenant-scoped user
def override_get_current_user():
    user = MagicMock()
    user.tenant_id = tenant_id
    return user

app.dependency_overrides[mock_deps.get_current_user] = override_get_current_user
```

## Known Testing Gaps

- No E2E test suite (Playwright or Cypress)
- Backend unit tests for domain/application logic are largely absent
- Frontend hooks (e.g., `useBrandSettings`) are not tested directly
- No coverage enforcement — coverage may drift silently
- Some test files use `standalone` patterns without shared fixtures (e.g., `test_brand_connection.py` re-creates its own DB setup)

---

*Testing analysis: 2026-03-15*
