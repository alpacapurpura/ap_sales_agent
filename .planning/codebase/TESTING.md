# Testing Patterns

**Analysis Date:** 2026-03-20

> This document cross-references actual test patterns with the desired standards defined in
> `.trae/skills/backend-expert/references/testing.md`.
> Deviations are marked with ⚠️.

---

## Backend Testing

### Test Framework

**Runner:**
- `pytest` with `pytest-asyncio`
- Config: `backend/pyproject.toml`
  ```toml
  [tool.pytest.ini_options]
  pythonpath = ["."]
  testpaths = ["tests", "src/tests"]
  ```

**Run Commands (inside Docker container):**
```bash
docker exec -t visionarias_brain_dev pytest                                    # All tests
docker exec -t visionarias_brain_dev pytest tests/modules/analytics            # Module tests
docker exec -t visionarias_brain_dev pytest tests/modules/brand/test_extraction_router.py -s  # Single file with output
```

### Test File Organization

**Actual structure (hybrid — desired is module-level tests inside src):**

```
backend/
├── tests/                              # Primary test root
│   ├── conftest.py                     # Global: SQLite in-memory DB, MockJSONB, MockUUID
│   ├── integration/
│   │   ├── test_brand_connection.py    # Live integration test
│   │   └── test_ga4_live.py           # Live API test
│   ├── modules/
│   │   ├── analytics/
│   │   │   ├── conftest.py            # Module-level fixtures (test_tenant_id, sample_offer_id)
│   │   │   ├── test_cac_calculation.py
│   │   │   ├── test_sales_endpoint.py
│   │   │   ├── test_meta_provider.py
│   │   │   └── ... (11 test files)
│   │   ├── brand/
│   │   │   └── test_extraction_router.py
│   │   ├── connections/
│   │   │   ├── test_channel_security.py
│   │   │   ├── test_meta_tenant_isolation.py
│   │   │   └── ... (6 test files)
│   │   ├── scheduling/
│   │   │   └── test_appointment_events.py
│   │   └── crm/
│   │       └── conftest.py
│   └── shared/
│       ├── test_ai_action_service.py
│       └── test_event_bus.py
└── src/tests/
    └── test_telegram_flow.py           # Module-embedded test (single file)
```

⚠️ **Deviation:** The desired pattern places unit tests inside `src/modules/{module}/tests/`.
In practice, only `backend/src/tests/test_telegram_flow.py` and `backend/src/modules/brand/tests/repro_issue.py`
(a debug script, not a proper test) exist inside `src/`. All other tests live in the top-level `tests/` directory.

### Global Test Configuration (`backend/tests/conftest.py`)

The global conftest sets up an in-memory SQLite DB for integration tests:

```python
# SQLite compatibility shims for PostgreSQL types
class MockJSONB(TypeDecorator):      # Maps JSONB -> Text with JSON encode/decode
class MockUUID(TypeDecorator):       # Maps UUID -> CHAR(36)

# Applied at module level:
postgresql.JSONB = MockJSONB
postgresql.UUID = MockUUID

@pytest.fixture(scope="session")
def db_engine():
    """SQLite in-memory engine, session-scoped. Creates all tables once."""
    engine = create_engine("sqlite:///:memory:", ...)
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db(db_engine):
    """Transactional rollback after each test — leaves DB clean."""
    connection = db_engine.connect()
    transaction = connection.begin()
    session = sessionmaker(..., bind=connection)()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
```

**Key design decision:** Uses SQLite instead of a real PostgreSQL test DB. This avoids Docker-in-Docker
complexity but means PostgreSQL-specific features (JSONB operators, UUID functions) are shimmed.

### Module Fixtures (`backend/tests/modules/analytics/conftest.py`)

```python
@pytest.fixture
def test_tenant_id() -> UUID:
    """Fixed tenant UUID for test determinism."""
    return uuid.UUID("11111111-1111-1111-1111-111111111111")

@pytest.fixture
def mock_credentials() -> dict:
    return {"access_token": "test-access-token-abc123", "refresh_token": "test-refresh-token-xyz789"}

@pytest.fixture
def mock_connection_credentials():
    return ConnectionCredentials(channel_type="meta", credentials={"access_token": "test-token"}, ...)
```

### Test Naming Convention

**Desired:** `test_[function]_[condition]_[expected_result]`
**Actual observed patterns (mixed):**

```python
# Structured (correct):
def test_create_offer_with_invalid_data_raises_error(): ...

# Descriptive class-grouped (most common):
class TestStageCostServiceExtension:
    def test_method_exists(self): ...
    def test_method_signature_returns_tuple(self): ...

class TestSalesMetricsRepository:
    def test_repository_uses_select_syntax(self): ...  # source inspection test

# Standalone (also used):
def test_brand_extract_endpoint_delegates_to_copilot_service(): ...
def test_channel_credentials_encryption(db): ...
```

Most tests are grouped in classes by the system-under-test. Standalone functions are used for
router/endpoint integration tests.

### Mocking Patterns

**Framework:** `unittest.mock` (stdlib) — `MagicMock`, `AsyncMock`, `patch`.

**Router / API Integration pattern (most common for API layer tests):**
```python
# backend/tests/modules/brand/test_extraction_router.py
from fastapi import FastAPI
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch

def _build_client(tenant_id):
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/brand/tools")
    app.dependency_overrides[get_db] = lambda: MagicMock()
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=uuid4(), tenant_id=tenant_id)
    return TestClient(app)

def test_brand_extract_endpoint_delegates_to_copilot_service():
    client = _build_client(uuid4())
    with patch("src.modules.brand.api.extraction.CopilotBrandAIActionsService") as service_cls:
        service_instance = MagicMock()
        service_instance.extract_brand_identity = AsyncMock(return_value={...})
        service_cls.return_value = service_instance
        response = client.post("/api/v1/brand/tools/extract", json={...})
    assert response.status_code == 200
    service_instance.extract_brand_identity.assert_awaited_once_with(...)
```

**Structural / "Contract" tests (prevalent in analytics tests):**
```python
# Tests verify class/method existence and source code properties — not behavior
class TestSalesMetricsRepository:
    def test_repository_uses_select_syntax(self):
        import inspect
        from src.modules.analytics.infrastructure.repositories import sales_metrics_repository
        source = inspect.getsource(sales_metrics_repository)
        assert "db.query" not in source, "Must use SQLAlchemy 2.0 select() syntax"
        assert "select(" in source
```

⚠️ **Concern:** Structural tests using `inspect.getsource()` are fragile — they test implementation
details rather than behavior. Widespread in `tests/modules/analytics/`. Useful as scaffolding but
should be replaced with behavior tests as features mature.

**DB integration pattern:**
```python
# backend/tests/modules/connections/test_channel_security.py
def test_channel_credentials_encryption(db):  # receives session fixture from conftest
    channel = ChannelConnectionModel(tenant_id=uuid4(), channel_type="whatsapp", credentials={...})
    db.add(channel)
    db.commit()
    db.refresh(channel)
    assert channel.credentials == credentials
```

### Async Tests

- `@pytest.mark.asyncio` is used in 65 test functions.
- Async tests use `AsyncMock` for coroutine mocking.
- `pytest-asyncio` is the runner for async tests.

```python
@pytest.mark.asyncio
async def test_save_user(db_session):
    repo = UserRepository(db_session)
    await repo.save(User(email="real@db.com"))
    saved = await repo.get_by_email("real@db.com")
    assert saved is not None
```

### Coverage

**Requirements:** No enforced coverage gate configured in `pyproject.toml`.
No `--cov` flag in default pytest config.

**Areas with good coverage:**
- `analytics` module — 11 test files covering DTOs, repositories, providers, endpoints.
- `connections` module — 6 test files covering webhooks, security, channel isolation.
- `brand` module — router-level integration tests.

**Areas with minimal or no tests:**
- `sales_agent` — complex orchestrator/graph logic largely untested.
- `offer` — no dedicated test files found beyond brand extraction.
- `crm` — conftest exists but no test files inside `tests/modules/crm/`.
- `scheduling` — 1 test file (`test_appointment_events.py`).
- `landing` — no tests found.
- `iam` — no tests found in `tests/modules/iam/`.

---

## Frontend Testing

### Test Framework

**Runner:**
- Vitest 4.x
- Config: `frontend/vitest.config.mts`

```typescript
export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'happy-dom',    // happy-dom (faster than jsdom, chosen for component tests)
    setupFiles: './src/test/setup.ts',
    globals: true,
    alias: { '@': path.resolve(__dirname, './src') },
  },
})
```

**Assertion Library:**
- Vitest's built-in `expect` + `@testing-library/jest-dom` matchers.
- Setup file: `frontend/src/test/setup.ts` — imports `@testing-library/jest-dom`.

**Component Rendering:**
- `@testing-library/react` — `render`, `screen`, `renderHook`, `waitFor`.

**Run Commands (inside or outside container):**
```bash
npm run test           # vitest run (CI mode)
npm run test:watch     # vitest (watch mode)
npm run test:ui        # vitest --ui (browser UI)
```

### Test File Organization

**Two coexisting patterns (inconsistent):**

**Pattern A — Sibling `__tests__/` directory (new/preferred):**
```
src/features/offer-studio/components/editor/sections/program-details/
├── program-form.tsx
├── session-schedule-builder.tsx
└── __tests__/
    ├── program-form.test.tsx
    └── session-schedule-builder.test.tsx

src/features/marketing-studio/components/metrics-dashboard/
├── StageCard.tsx
└── __tests__/
    └── StageCard.test.tsx
```

**Pattern B — Feature-level `tests/` directory:**
```
src/features/offer-studio/
├── tests/
│   ├── dashboard-logic.test.tsx
│   ├── offer-card.test.tsx
│   └── fixtures.ts
```

**Pattern C — Co-located in same directory:**
```
src/components/ui/
├── label.tsx
└── label.test.tsx

src/features/brand/utils/
├── brand-validation.ts
└── brand-validation.test.ts

src/lib/api/
├── ai-actions.ts
└── ai-actions.test.ts
```

⚠️ **No single convention enforced.** New tests should prefer co-location (`__tests__/`) adjacent to the component.

### Test Structure

**Standard pattern:**
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ComponentName } from '../component-name';

describe('ComponentName', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should do X when Y', () => {
    render(<ComponentName prop="value" />);
    expect(screen.getByText('Expected')).toBeInTheDocument();
  });
});
```

**Hook testing pattern:**
```typescript
import { renderHook, waitFor } from '@testing-library/react';
import { useMyHook } from '../use-my-hook';

// Mock dependencies before import
vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({ getToken: vi.fn(() => Promise.resolve('mock-token')) }),
}));

describe('useMyHook', () => {
  it('should return data', async () => {
    const { result } = renderHook(() => useMyHook());
    await waitFor(() => expect(result.current.data).toBeDefined());
  });
});
```

**API function testing pattern:**
```typescript
// Mock dependencies before import (module hoisting)
const fetchClientMock = vi.fn();
vi.mock("@/lib/http-client", () => ({ fetchClient: (...args: any[]) => fetchClientMock(...args) }));
vi.mock("@/lib/config", () => ({ config: { api: { baseUrl: "http://localhost:8000" } } }));

import { myApi } from "./my-api"; // import AFTER mocks

describe("myApi", () => {
  beforeEach(() => { fetchClientMock.mockReset(); });

  it("calls correct endpoint", async () => {
    fetchClientMock.mockResolvedValueOnce(new Response(JSON.stringify({...}), { status: 200 }));
    const result = await myApi.getData("token-123");
    expect(fetchClientMock).toHaveBeenCalledWith(
      "http://localhost:8000/api/v1/resource",
      expect.objectContaining({ method: "POST" })
    );
  });
});
```

### Mocking

**Framework:** Vitest's `vi` object — `vi.mock()`, `vi.fn()`, `vi.mocked()`.

**What to mock:**
- `@clerk/nextjs` (`useAuth`, `getToken`) — always mocked in component/hook tests.
- `@/lib/http-client` (`fetchClient`) — mocked in API function tests.
- `@/lib/config` — mocked with static test values.
- Complex UI components that cause JSDOM issues (e.g., `SmartDateTimePicker`, `TimezoneSelect`).

**Pattern for complex component mocks:**
```typescript
vi.mock('@/components/ui/smart-datetime-picker', () => ({
  SmartDateTimePicker: () => <div data-testid="smart-datetime-picker">Picker</div>
}));
```

**What NOT to mock:**
- `cn()` utility — use real implementation.
- Business logic/pure functions — test directly without mocking.
- Zod schemas — test against real schema.

### Fixtures

**Location:** `src/features/offer-studio/tests/fixtures.ts` (one known fixture file).

```typescript
export const MOCK_BACKEND_RESPONSE = { ... };  // Static test data objects
```

No centralized fixture factory pattern — each test file defines its own mock data inline.

### Coverage

**Requirements:** No enforced coverage threshold configured.

**What is tested:**
- Business logic / adapter functions (`backendToFrontend` adapter — adapter tests in `dashboard-logic.test.tsx`).
- Pure utility functions (`brand-validation.ts` — full validation logic covered).
- API functions (`ai-actions.ts` — 3 test cases covering endpoint routing and method types).
- Component rendering smoke tests (render + key text assertions).
- Hook state shapes (scaffold tests — see note below).

⚠️ **Concern:** Several hook tests in `useAttractionDetail.test.ts` and `StageCard.test.tsx` are
scaffold/placeholder tests — they contain `TODO (Plan 11-01)` comments and assert on local mock data
instead of the actual hook behavior. These tests pass but provide no real coverage guarantee.

**View Coverage:**
```bash
npx vitest run --coverage   # Not configured by default; add @vitest/coverage-v8 to enable
```

### Test Types

**Unit Tests:**
- Pure function tests: `brand-validation.test.ts`, `dashboard-logic.test.tsx`.
- API client tests: `ai-actions.test.ts`.

**Component Tests (render + assertion):**
- `StageCard.test.tsx`, `program-form.test.tsx`, `session-schedule-builder.test.tsx`.
- Uses wrapper components to provide form context (`react-hook-form`) when needed.

**Hook Tests:**
- `useAttractionDetail.test.ts` — currently scaffold-only (see above).

**E2E Tests:**
- Not present. No Playwright or Cypress configuration found.

**Storybook:**
- Stories exist in `frontend/src/stories/` for UI component documentation (Dialog, Sheet, Calendar, etc.).
- Storybook configured with `@storybook/nextjs-vite`.
- Not integrated as automated tests — visual review only.

---

## Common Anti-Patterns to Avoid

**Backend:**
- Do NOT use `db.query()` — use SQLAlchemy 2.0 `select()` syntax.
- Do NOT write structural `inspect.getsource()` tests as the only coverage for a feature.
- Do NOT use `@pytest.mark.asyncio` without `pytest-asyncio` configured in `pyproject.toml`.

**Frontend:**
- Do NOT import component under test BEFORE `vi.mock()` declarations — Vitest hoists mocks.
- Do NOT render hooks that use `useQuery` without wrapping in `QueryClientProvider` — provide a wrapper.
- Do NOT leave scaffold/TODO tests as-is; they create false confidence in coverage.
- Do NOT assert on mock data within the test itself (e.g., `expect(mockData.value).toBe(x)`) —
  this tests the test fixture, not the component.

---

*Testing analysis: 2026-03-20*
