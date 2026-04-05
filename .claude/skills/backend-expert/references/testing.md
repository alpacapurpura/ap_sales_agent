# Testing Backend

## TDD Protocol by DDD Layer

Write tests BEFORE implementation, following this order:

1. **Domain** (Pydantic models, enums, value objects) → Pure unit tests, no fixtures needed
2. **Infrastructure** (repositories) → Use `db` fixture (SQLite in-memory), `seed_tenant`
3. **Application** (services) → Integration tests with real repos via `db` fixture
4. **API** (routes) → TestClient with dependency overrides (optional, low priority)

## Test Location & Structure

```
backend/tests/modules/{module}/
  __init__.py
  conftest.py              # Module fixtures
  test_domain_models.py    # Pydantic validation, enums
  test_{name}_repository.py # CRUD, tenant isolation, soft delete
  test_{name}_service.py   # Service orchestration
```

## Factories

Use `factory-boy` factories from `tests/factories/`:

```python
from tests.factories import TenantFactory, BrandSettingsFactory

# ORM model (add to db session):
tenant = TenantFactory.build(id=tenant_id, name="Test Tenant", slug="test-tenant", config_json={})
db.add(tenant)
db.commit()

# Domain model (Pydantic, use directly):
settings = BrandSettingsFactory()
```

## Conftest Pattern (FOLLOW THIS)

```python
import pytest
import uuid
from tests.factories import TenantFactory

TENANT_A = uuid.UUID("aaaa0000-0000-0000-0000-000000000001")
TENANT_B = uuid.UUID("bbbb0000-0000-0000-0000-000000000002")
USER_A = uuid.UUID("cccc0000-0000-0000-0000-000000000001")

@pytest.fixture
def tenant_id():
    return TENANT_A

@pytest.fixture
def other_tenant_id():
    return TENANT_B

@pytest.fixture
def user_id():
    return USER_A

@pytest.fixture
def seed_tenant(db, tenant_id):
    tenant = TenantFactory.build(id=tenant_id, name="Test Tenant", slug="test-tenant", config_json={})
    db.add(tenant)
    db.commit()
    return tenant

@pytest.fixture
def seed_other_tenant(db, other_tenant_id):
    tenant = TenantFactory.build(id=other_tenant_id, name="Other Tenant", slug="other-tenant", config_json={})
    db.add(tenant)
    db.commit()
    return tenant
```

## Root conftest (`backend/tests/conftest.py`)

Provides:
- `db_engine` (session-scoped): SQLite in-memory with MockJSONB/MockUUID patches
- `db` (function-scoped): Session with transaction rollback per test

If your module's model isn't registered there, add it to the `db_engine` fixture imports.

## Test Naming Convention

```
test_[function]_[condition]_[expected_result]
```

Examples:
- `test_create_tenant_with_duplicate_slug_raises_error`
- `test_get_by_id_with_wrong_tenant_returns_none`
- `test_list_events_filters_by_category`

## Tenant Isolation Tests (MANDATORY)

Every repository MUST have isolation tests:

```python
class TestTenantIsolation:
    def test_tenant_b_cannot_list_tenant_a_data(self, db, seed_tenant, seed_other_tenant):
        repo = SomeRepository(db)
        repo.create(tenant_id=TENANT_A, ...)
        results = repo.list_by_tenant(tenant_id=TENANT_B)
        assert len(results) == 0

    def test_get_by_id_with_wrong_tenant_returns_none(self, db, seed_tenant, seed_other_tenant):
        repo = SomeRepository(db)
        item = repo.create(tenant_id=TENANT_A, ...)
        result = repo.get_by_id(id=item.id, tenant_id=TENANT_B)
        assert result is None
```

## Coverage

- Run: `cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q`
- Threshold: **60%** (CI will fail below this)
- The skill `/test-backend` already includes coverage automatically
- **Mandatory coverage:** application + domain layers must be tested
- **Recommended coverage:** infrastructure layer (repositories, clients)
- **Low priority:** api layer (thin — covered by integration/E2E tests)

## Execution (Native — NEVER use docker exec)

```bash
# All tests
cd backend && .venv/bin/pytest -x -q --tb=short

# Single module
cd backend && .venv/bin/pytest tests/modules/{module}/ -v

# With coverage
cd backend && .venv/bin/pytest --cov=src/modules --cov=src/shared --cov-report=term-missing -q

# Architecture fitness tests
cd backend && .venv/bin/pytest tests/architecture/ -v
```

## Rules

1. SQLAlchemy 2.0 syntax only: `select(Model).where(...)`, not `session.query(Model)`
2. Soft deletes: verify `deleted_at` filtering works (deleted rows shouldn't appear)
3. Pure functions → unit tests without DB. Services → integration with `db` fixture.
4. No `any` types in test code
5. Run `ruff check` on test files before committing

## Architectural Fitness Tests

Located at `backend/tests/architecture/`. These run as part of the regular pytest suite.

### What they enforce
| Test | Rule | Ratchet |
|---|---|---|
| `test_no_new_cross_module_imports` | Module A cannot import from Module B (except copilot, shared, core) | Allowlist in test file |
| `test_domain_layer_has_no_framework_imports` | domain/ must be pure Python (no SQLAlchemy, FastAPI) | No allowlist — zero tolerance |
| `test_all_endpoints_have_response_model` | Every @router endpoint needs response_model= | Allowlist in test file |
| `test_no_hard_deletes` | No session.delete() — use soft delete | Allowlist in test file |
| `test_no_sqlalchemy_1x_query_syntax` | No session.query() — use select().where() | Allowlist in test file |

### Ratchet pattern
Tests with allowlists have a `KNOWN_*` set listing legacy violations. The test passes if
all violations are in the allowlist. **New violations fail the build.** To fix a violation:
1. Refactor the code
2. Remove the entry from the allowlist
3. The allowlist can only shrink — never add new entries without code review justification

### When to run
- `make arch-test` — standalone
- `make pytest` — included automatically (they're in `tests/architecture/`)
- `/test-backend` — runs as step 3
- `/test-all` — runs as step 2
