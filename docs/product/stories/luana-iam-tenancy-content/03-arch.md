---
story_id: luana-iam-tenancy-content
arch_version: 1
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 01-spec.md + outcome §7.3 lift mode + §7.4 halt + Story 2 03-arch.md pattern reference
deviations_from_spec:
  - "modules/commercial_calendar/copilot_provider/ + modules/social_proof/copilot_provider/ DEFERRED to Story 6 (copilot lift). They import src.modules.copilot.domain.ports which doesn't exist in luana-platform yet. Same deferred-files pattern as Story 2 §3.3 (workers/copilot_quality_eval.py)."
  - "tenant_domains/workers/tasks.py lifts together with module (small ARQ worker file, no module-coupling — verified)."
  - "8 Python packages NOT 6: iam, tenant_profile, tenant_domains, commercial_calendar, social_proof, assets = 6 lifted in this story. Spec said '8-12 tickets' — confirms granularity. No deviation in package count."
---

# Story 3 — Luana IAM + Tenancy + Content lift — Architecture (03-arch.md)

## §1. Topology — Dependency Graph (resolved)

### §1.1 Audit method

Ran cross-module import grep for each Story 3 module per `.claude/rules/anti-duplication.md`:

```bash
cd /home/chris/AISALESHT/backend/src/modules
for m in iam tenant_profile tenant_domains commercial_calendar social_proof assets; do
    grep -rEh "^from src\.(modules|shared|core)\." $m/ --include="*.py" | sort -u
done
```

Cross-tabulated each module's external dependencies. Resolved 0 cycles. Found 1
deviation: `commercial_calendar/copilot_provider/` + `social_proof/copilot_provider/`
import `src.modules.copilot.domain.ports` (Story 6 territory) — DEFERRED.

### §1.2 Python package dependency DAG (6 packages)

```
                    luana-core-platform (Story 2 — foundation: shared.domain + src.core + shared.infrastructure)
                          ↑
        ┌─────────────────┼─────────────────┬─────────────────────┐
        │                 │                 │                     │
  luana-core-iam   luana-core-tenant-profile  (platform-only deps, no inter-Story-3 deps among foundation)
        ↑                 │
        │                 │
        └──────┬──────────┴──────┬──────────┬──────────┐
               ↓                 ↓          ↓          ↓
       luana-core-tenant-domains   luana-core-commercial-calendar   luana-core-social-proof   luana-core-assets
       (needs iam.User for         (needs iam.User; copilot_provider/  (needs iam.User; copilot_provider/  (needs iam.User)
        get_current_user;           DEFERRED Story 6)                   DEFERRED Story 6)
        DomainLookupPort via
        platform.links.ports)
```

**Resolution summary (cross-package edges, all DAG-clean):**

| Source package | Depends on | Symbol used |
|---|---|---|
| `luana-core-iam` | `luana-core-platform` | `shared.domain.{base_entity, currency, locale}` + `shared.infrastructure.external.clerk::ClerkService` + `core.{config, context, database}` |
| `luana-core-tenant-profile` | `luana-core-platform` | `shared.domain.{base_entity, datetime_utils, expert_business_type}` + `core.database` |
| `luana-core-tenant-domains` | `luana-core-platform` | `shared.domain.base_entity` + `shared.links.ports.domain_lookup::DomainLookupPort` + `core.{config, database}` |
| `luana-core-tenant-domains` | `luana-core-iam` | `iam.api.dependencies::get_current_user` + `iam.domain.user::User` |
| `luana-core-commercial-calendar` | `luana-core-platform` | `shared.domain.{base_entity, datetime_utils}` + `core.database` |
| `luana-core-commercial-calendar` | `luana-core-iam` | `iam.api.dependencies::get_current_user` + `iam.domain.user::User` |
| `luana-core-social-proof` | `luana-core-platform` | `shared.domain.{base_entity, datetime_utils, events}` + `core.database` |
| `luana-core-social-proof` | `luana-core-iam` | `iam.api.dependencies::get_current_user` + `iam.domain.user::User` |
| `luana-core-assets` | `luana-core-platform` | `shared.domain.{base_entity, datetime_utils}` + `shared.infrastructure.files.file_parsing_service::FileParsingService` + `core.{config, database}` |
| `luana-core-assets` | `luana-core-iam` | `iam.api.dependencies::{get_current_user, get_current_tenant_id}` + `iam.domain.user::User` |

**Cycle check:** None. DAG-clean. iam is a leaf within the Story 3 package set (depends only on Story 2 packages).

**No cross-Story-4/5 coupling found.** None of the 6 modules imports from `modules/{brand,offer,landing,crm,analytics,advertising,social_media,scheduling,connections,copilot,sales_agent}` EXCEPT the 2 `copilot_provider/` sub-folders (deferred per §9).

### §1.3 Coupling notes

- **iam is the natural foundation.** It defines `User` and `Tenant` aggregates and exposes `get_current_user` (FastAPI Depends). All 4 content modules (tenant_domains, commercial_calendar, social_proof, assets) consume `User` via `Depends(get_current_user)` at API layer.
- **tenant_profile is independent.** Does NOT consume iam — it owns `expert_business_types` data per tenant separately (FK to `tenant_id` only, no User reference).
- **`shared.links.ports.domain_lookup::DomainLookupPort`** is consumed by `tenant_domains/application/domain_lookup_adapter.py`. This port lives in `luana-core-platform.links.ports` (Story 2). Cross-package import works.
- **`shared.infrastructure.external.clerk::ClerkService`** lifts in Story 2 (part of `luana-core-platform.infrastructure.external`). iam consumes verbatim — preserves brand-agnostic Clerk-via-env-config pattern (per ADR-001 §2.5).
- **`commercial_calendar/copilot_provider/` + `social_proof/copilot_provider/` DEFERRED to Story 6** — they import `src.modules.copilot.domain.ports::{BaseCopilotProvider, ModuleData}`. Same pattern as Story 2 deferred `shared/workers/copilot_quality_eval.py`. Documented §9. NO scope expansion to lift copilot.domain.ports early (would break Story 6's lift).

### §1.4 No-cycle proof

Walked the DAG manually:
- iam → platform.shared.domain + platform.shared.infrastructure.external + platform.core (Story 2 lifted, downward edges only)
- tenant_profile → platform (downward)
- tenant_domains → platform + iam (downward — iam doesn't import tenant_domains)
- commercial_calendar → platform + iam (downward)
- social_proof → platform + iam (downward)
- assets → platform + iam (downward)

No cyclic edges. Pure DAG.

## §2. Lift Order

Per dependency graph, lift order is **3 batches × parallelizable within batch**:

**Batch 1 (foundation — sequential, no deps within batch):**
1. `luana-core-iam` — depends only on Story 2 packages. Largest of Story 3, 28 files.
2. `luana-core-tenant-profile` — depends only on Story 2 packages. Independent of iam. (Parallel with iam OK; serialized here for clarity.)

**Batch 2 (depends on iam — parallelizable):**
3. `luana-core-tenant-domains` — needs iam.User
4. `luana-core-commercial-calendar` — needs iam.User; copilot_provider DEFERRED
5. `luana-core-social-proof` — needs iam.User; copilot_provider DEFERRED
6. `luana-core-assets` — needs iam.User

**Cross-cutting:**
- Workspace registration (T-1) before any lift.
- Cross-package integration smoke (T-7) post all 6 lifts.
- Brand-agnostic IAM arch fitness (T-8) post iam lift.
- AISALESHT untouched + lint + finalization (T-9..T-11) post smoke.

## §3. Per-Package Structure

### §3.1 Python package layout (mirror Story 2 §3.1)

```
core/luana-core-<name>/
├── pyproject.toml                    # workspace member, version "0.0.1-alpha"
├── README.md                         # stub: 1 paragraph what + lift origin
├── src/
│   └── luana_core_<name>/            # snake_case (PEP 8)
│       ├── __init__.py
│       └── <preserved DDD structure verbatim>
└── tests/
    ├── __init__.py
    ├── conftest.py                   # lift verbatim if present
    └── <preserved test structure>
```

### §3.2 Example — luana-core-iam

```
core/luana-core-iam/
├── pyproject.toml
├── README.md
├── src/luana_core_iam/
│   ├── __init__.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── auth_router.py
│   │   ├── dependencies.py          # ← consumed by all Batch 2 packages
│   │   ├── dto/users.py
│   │   ├── settings.py
│   │   ├── tenant_locale.py
│   │   └── ...
│   ├── application/
│   │   ├── auth.py                  # verify_clerk_token
│   │   ├── services/{tenant_service,user_service}.py
│   │   └── ...
│   ├── domain/
│   │   ├── tenant.py                # ← consumed cross-platform
│   │   ├── user.py                  # ← consumed by Batch 2 packages
│   │   ├── tracking_config.py
│   │   └── ...
│   └── infrastructure/
│       ├── models/{tenant_model,user_model,user_tenant_model}.py
│       └── repositories/{tenant_repository,user_repository,user_tenant_repository}.py
└── tests/
    ├── conftest.py
    ├── test_auth.py
    ├── test_dependencies.py
    ├── test_domain_models.py
    ├── test_settings.py
    ├── test_tenant_locale_dependency.py
    ├── test_t6a_deprecate_tenant_api_keys.py
    └── test_t6c_drop_tenant_api_keys.py
```

### §3.3 Example — luana-core-social-proof (largest with copilot_provider DEFERRED)

```
core/luana-core-social-proof/
├── pyproject.toml
├── README.md
├── src/luana_core_social_proof/
│   ├── __init__.py
│   ├── api/{authority,placements,team_members,testimonials}.py
│   ├── application/
│   │   ├── dto/{authority,placement,team,testimonial}_dto.py
│   │   └── services/{authority,placement,social_proof_resolver,team,testimonial}_service.py
│   ├── domain/
│   │   ├── authority_item.py
│   │   ├── enums.py
│   │   ├── events.py
│   │   ├── placement.py
│   │   ├── team_member.py
│   │   └── testimonial.py
│   └── infrastructure/
│       ├── models/{authority_item,placement,team_member,testimonial}_model.py
│       └── repositories/{authority_item,placement,team_member,testimonial}_repository.py
│   # NOTE: copilot_provider/ NOT lifted — DEFERRED Story 6
└── tests/
    ├── unit/
    ├── integration/
    └── conftest.py
```

## §4. Workspace Registration

### §4.1 Root pyproject.toml (extend Story 2 state)

Story 2 declared 9 packages. Story 3 adds 6 more:

```toml
[tool.uv.workspace]
members = [
    "core",
    # Story 2 packages (already registered)
    "core/luana-core-platform",
    "core/luana-core-llm",
    "core/luana-core-channels",
    "core/luana-core-idempotency",
    "core/luana-core-observability",
    "core/luana-core-events",
    "core/luana-core-extraction",
    "core/luana-core-compliance",
    "core/luana-core-billing",
    # Story 3 packages (NEW)
    "core/luana-core-iam",
    "core/luana-core-tenant-profile",
    "core/luana-core-tenant-domains",
    "core/luana-core-commercial-calendar",
    "core/luana-core-social-proof",
    "core/luana-core-assets",
    # Brand apps
    "nicolify", "vitalia", "comunify", "lupulo",
]

[tool.uv.sources]
# Story 2 (already registered)
luana-core-platform = { workspace = true }
luana-core-llm = { workspace = true }
luana-core-channels = { workspace = true }
luana-core-idempotency = { workspace = true }
luana-core-observability = { workspace = true }
luana-core-events = { workspace = true }
luana-core-extraction = { workspace = true }
luana-core-compliance = { workspace = true }
luana-core-billing = { workspace = true }
# Story 3 (NEW)
luana-core-iam = { workspace = true }
luana-core-tenant-profile = { workspace = true }
luana-core-tenant-domains = { workspace = true }
luana-core-commercial-calendar = { workspace = true }
luana-core-social-proof = { workspace = true }
luana-core-assets = { workspace = true }
```

### §4.2 No TS this story

Story 3 is backend-only. `pnpm-workspace.yaml` unchanged.

## §5. Import Path Mapping

### §5.1 Python mapping (verbatim preservation rule)

| AISALESHT source path | luana-platform internal path |
|---|---|
| `from src.modules.iam.api.dependencies import get_current_user` | `from luana_core_iam.api.dependencies import get_current_user` |
| `from src.modules.iam.domain.user import User` | `from luana_core_iam.domain.user import User` |
| `from src.modules.iam.domain.tenant import Tenant` | `from luana_core_iam.domain.tenant import Tenant` |
| `from src.modules.iam.application.auth import verify_clerk_token` | `from luana_core_iam.application.auth import verify_clerk_token` |
| `from src.modules.iam.infrastructure.models.user_model import UserModel` | `from luana_core_iam.infrastructure.models.user_model import UserModel` |
| `from src.modules.tenant_profile.domain.tenant_profile import TenantProfile` | `from luana_core_tenant_profile.domain.tenant_profile import TenantProfile` |
| `from src.modules.tenant_domains.domain.domain_entity import TenantDomain` | `from luana_core_tenant_domains.domain.domain_entity import TenantDomain` |
| `from src.modules.commercial_calendar.domain.calendar_event import CalendarEvent` | `from luana_core_commercial_calendar.domain.calendar_event import CalendarEvent` |
| `from src.modules.social_proof.domain.testimonial import Testimonial` | `from luana_core_social_proof.domain.testimonial import Testimonial` |
| `from src.modules.assets.domain.entity import Asset` | `from luana_core_assets.domain.entity import Asset` |
| `from src.shared.domain.base_entity import Base` | `from luana_core_platform.domain.base_entity import Base` (Story 2 SSoT) |
| `from src.shared.infrastructure.external.clerk import ClerkService` | `from luana_core_platform.infrastructure.external.clerk import ClerkService` (Story 2 SSoT) |
| `from src.shared.links.ports.domain_lookup import DomainLookupPort` | `from luana_core_platform.links.ports.domain_lookup import DomainLookupPort` (Story 2 SSoT) |
| `from src.core.database import get_db` | `from luana_core_platform.core.database import get_db` (Story 2 SSoT) |

**Important:** AISALESHT imports NOT touched (Story 10 territory).

## §6. Test Lift Strategy

### §6.1 Python tests

Tests lift in **same commit as source** (per `.claude/rules/auditor-downstream-regression.md`):

| AISALESHT source | luana-platform destination |
|---|---|
| `backend/tests/modules/iam/` | `core/luana-core-iam/tests/` (16 files) |
| `backend/tests/modules/tenant_profile/` | `core/luana-core-tenant-profile/tests/` (6 files) |
| `backend/tests/modules/tenant_domains/` | `core/luana-core-tenant-domains/tests/` (7 files) |
| `backend/tests/modules/commercial_calendar/` | `core/luana-core-commercial-calendar/tests/` (6 files) |
| `backend/tests/modules/social_proof/` | `core/luana-core-social-proof/tests/` (6 files: unit/ + integration/) |
| `backend/tests/modules/assets/` | `core/luana-core-assets/tests/` (9 files) |

### §6.2 Mock path migration

Tests may use `monkeypatch.setattr("src.modules.iam.X")` — update to `luana_core_iam.X` verbatim. Same mechanical sed pattern as Story 2 §6.1.

### §6.3 conftest.py preservation

Each module's `tests/conftest.py` lifts verbatim alongside source.

## §7. Architecture Fitness Tests

### §7.1 Brand-agnostic IAM (NEW — Story 3-specific)

Per 01-spec.md §2.5, `luana-core-iam` MUST stay brand-agnostic.

**New arch fitness test:** `core/tests/architecture/test_iam_brand_agnostic.py`

```python
"""Story 3 — Brand-agnostic IAM invariant.

luana-core-iam MUST NOT contain brand-aware control flow.
Clerk config via env / DI (preserves AISALESHT pattern, ADR-001 §2.5).
"""
from pathlib import Path
import re

IAM_SRC = Path(__file__).parent.parent.parent / "luana-core-iam" / "src" / "luana_core_iam"

# Patterns that indicate brand-aware control flow
FORBIDDEN_PATTERNS = [
    r"if\s+brand\s*==",
    r"if\s+tenant\.brand\s*==",
    r"if\s+self\.brand\s*==",
    r'brand\s*==\s*["\']nicolify["\']',
    r'brand\s*==\s*["\']vitalia["\']',
    r'brand\s*==\s*["\']comunify["\']',
    r'brand\s*==\s*["\']lupulo["\']',
    # Hardcoded Clerk app IDs (must be env)
    r'clerk_app_id\s*=\s*["\'](?!os\.).+["\']',
    r'CLERK_PUBLISHABLE_KEY\s*=\s*["\'](?!os\.|settings\.).+["\']',
]


def test_iam_no_brand_aware_control_flow() -> None:
    """No `if brand == "..."` or hardcoded brand keys in iam source."""
    offenders = []
    for py_file in IAM_SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for pattern in FORBIDDEN_PATTERNS:
            matches = re.findall(pattern, text)
            if matches:
                offenders.append((py_file, pattern, matches))
    assert not offenders, f"luana-core-iam contains brand-aware code: {offenders}"


def test_iam_clerk_config_via_settings_or_env() -> None:
    """ClerkService instantiation must read config from settings/env, not hardcoded."""
    offenders = []
    for py_file in IAM_SRC.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        # Find ClerkService() calls — verify they don't pass hardcoded keys
        if "ClerkService(" in text:
            # Allow: ClerkService(),  ClerkService(secret_key=settings.X), ClerkService(secret_key=os.environ[...])
            # Forbid: ClerkService(secret_key="sk_live_XXX") or similar
            for match in re.finditer(r'ClerkService\(([^)]*)\)', text):
                args = match.group(1)
                if args.strip() and '"' in args and 'settings.' not in args and 'os.' not in args and 'env' not in args.lower():
                    offenders.append((py_file, match.group(0)))
    assert not offenders, f"ClerkService instantiated with hardcoded keys: {offenders}"
```

### §7.2 No cross-Story-3-to-Story-4/5 imports

**New arch fitness test:** `core/tests/architecture/test_story3_no_forward_module_imports.py`

```python
"""Story 3 packages MUST NOT import from Story 4/5/6/7 modules.

Forward-coupling would break the migration sequence.
"""
from pathlib import Path
import re

STORY3_PKGS = [
    "luana-core-iam",
    "luana-core-tenant-profile",
    "luana-core-tenant-domains",
    "luana-core-commercial-calendar",
    "luana-core-social-proof",
    "luana-core-assets",
]

FORBIDDEN_IMPORTS = [
    r"from\s+luana_core_(crm|analytics|advertising|social_media|landing|connections)\.",
    r"from\s+luana_core_(brand|offer)\.",
    r"from\s+luana_core_(copilot|sales_agent)\.",
    r"from\s+luana_core_(campaigns|scheduling)\.",
    # Also block accidental AISALESHT imports
    r"from\s+src\.modules\.",
]


def test_no_forward_module_imports() -> None:
    core_dir = Path(__file__).parent.parent.parent
    offenders = []
    for pkg in STORY3_PKGS:
        pkg_src = core_dir / pkg / "src"
        if not pkg_src.exists():
            continue
        for py_file in pkg_src.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            for pattern in FORBIDDEN_IMPORTS:
                matches = re.findall(pattern, text)
                if matches:
                    offenders.append((py_file, pattern, matches))
    assert not offenders, f"Forward module imports found: {offenders}"
```

### §7.3 Existing arch tests stay (no migration)

Story 3 does NOT migrate any AISALESHT arch test. Tests like `test_iam_tenant_id_isolation.py`, `test_tenant_profile_aggregate_invariants.py` (if they exist) stay in AISALESHT until Story 10. They validate AISALESHT module behavior; Story 3 doesn't touch AISALESHT.

## §8. Per-Package pyproject.toml Dependency Declarations

### §8.1 luana-core-iam/pyproject.toml

```toml
[project]
name = "luana-core-iam"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",
    "luana-core-platform",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_iam"]
```

### §8.2 luana-core-tenant-profile/pyproject.toml

```toml
[project]
name = "luana-core-tenant-profile"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "luana-core-platform",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_tenant_profile"]
```

### §8.3 luana-core-tenant-domains/pyproject.toml

```toml
[project]
name = "luana-core-tenant-domains"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",                 # Cloudflare API client
    "arq>=0.26",                   # workers/tasks.py
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_tenant_domains"]
```

### §8.4 luana-core-commercial-calendar/pyproject.toml

```toml
[project]
name = "luana-core-commercial-calendar"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_commercial_calendar"]
```

### §8.5 luana-core-social-proof/pyproject.toml

```toml
[project]
name = "luana-core-social-proof"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "luana-core-platform",
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_social_proof"]
```

### §8.6 luana-core-assets/pyproject.toml

```toml
[project]
name = "luana-core-assets"
version = "0.0.1-alpha"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "sqlalchemy>=2.0",
    "fastapi>=0.115",
    "structlog>=24.0",
    "httpx>=0.27",                 # external storage strategies
    "luana-core-platform",         # FileParsingService lives here (Story 2)
    "luana-core-iam",
]

[tool.uv.sources]
luana-core-platform = { workspace = true }
luana-core-iam = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/luana_core_assets"]
```

## §9. Deferred Files (Story 3 exception list)

These 2 sub-folders are NOT lifted in Story 3 because they import `src.modules.copilot.domain.ports` which doesn't exist in luana-platform yet:

| AISALESHT path | Reason | Will lift in |
|---|---|---|
| `backend/src/modules/commercial_calendar/copilot_provider/` | imports `src.modules.copilot.domain.ports::{BaseCopilotProvider, ModuleData}` | Story 6 (copilot lift) |
| `backend/src/modules/social_proof/copilot_provider/` | imports `src.modules.copilot.domain.ports::{BaseCopilotProvider, ModuleData}` | Story 6 |

**Lift behavior:** when lifting commercial_calendar/social_proof, /dev-team SKIPS the `copilot_provider/` subfolder (do NOT copy it). Story 6 will lift these alongside copilot module.

**Rationale:** identical pattern to Story 2 §9 (deferred `shared/workers/copilot_quality_eval.py`). Avoids creating dangling imports + scope expansion.

**Tests:** no tests under `tests/modules/{commercial_calendar,social_proof}/test_copilot_provider*` were found — verify before lift; if any exist, they defer with the source.

**Audit trail:** append entry to `core/DEFERRED-FILES.md` (created Story 2):

```markdown
## Story 3 deferrals (2026-05-11)

- backend/src/modules/commercial_calendar/copilot_provider/ → Story 6
- backend/src/modules/social_proof/copilot_provider/ → Story 6

Reason: import src.modules.copilot.domain.ports (Story 6 territory).
```

## §10. Research Notes (state-of-the-art as of 2026-05-11)

| Source | Accessed | Key takeaway |
|---|---|---|
| uv workspace docs https://docs.astral.sh/uv/concepts/workspaces/ | 2026-05-11 (via Story 2 §10) | Workspace sources resolve at install time. Story 3 packages declare `luana-core-platform` and `luana-core-iam` as workspace deps — same pattern as Story 2. |
| Hatchling build backend https://hatch.pypa.io/latest/config/build/ | 2026-05-11 (via Story 2) | `[tool.hatch.build.targets.wheel] packages = ["src/<name>"]` is the canonical src-layout. Matches Story 2 + Story 3 convention. |
| ADR-001 Multi-Clerk (internal doc) | 2026-05-11 | luana-core-iam stays brand-agnostic. Each brand wires its Clerk app via env vars / DI. No hardcoded keys. Arch fitness test enforces (§7.1). |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = January 2026. uv workspace + hatchling patterns predate cutoff. ADR-001 is internal Nicolify doc — verified live against `docs/product/outcomes/luana-platform-migration.md` §2.5.

## §11. Cross-Cutting Concerns (per CLAUDE.md)

- **Tenant isolation:** preserved — every entity in lifted modules already carries `tenant_id` filter in queries (verified via grep of `.where(Model.tenant_id == ...)` in repositories). Lift verbatim.
- **Currency handling:** `luana_core_iam` imports `FALLBACK_CURRENCY` from `luana_core_platform.domain.currency`. Lift verbatim preserves contract.
- **Master data:** `TenantLocale` VO consumed by `luana_core_iam.api.tenant_locale`. Same Story 2 SSoT.
- **Spanish neutro LatAm:** no UI strings in these 6 modules (all BE) → N/A.
- **PII sanitization:** routes already use `response_model=` on user/tenant DTOs in AISALESHT. Lift preserves.
- **Native-first dev:** validators use native `uv run pytest` on luana-platform — no Docker.
- **TDD-mandatory:** Story 3 is lift, not new code. Tests lift verbatim alongside source — preserves RED→GREEN guarantee.
- **Brand-agnostic IAM:** new invariant codified in §7.1 arch fitness test.

## §12. Architecture Fitness Gates (test surfaces)

| Gate | Layer | Owner |
|---|---|---|
| `uv sync --all-packages` GREEN | luana-platform root | gate-runner |
| `uv run pytest core/luana-core-<name>/tests/` GREEN per package (6 packages) | per-package | gate-runner |
| `uv run ruff check core/luana-core-{iam,tenant-profile,tenant-domains,commercial-calendar,social-proof,assets}/` GREEN | luana-platform root | gate-runner |
| `uv run pytest core/tests/architecture/test_iam_brand_agnostic.py` GREEN | luana-platform | gate-runner |
| `uv run pytest core/tests/architecture/test_story3_no_forward_module_imports.py` GREEN | luana-platform | gate-runner |
| AISALESHT untouched verifier (per 01-spec.md §3.5) | AISALESHT repo | gate-runner |
| No-publish verifier (per 01-spec.md §3.6) | luana-platform | gate-runner |
| `core/DEFERRED-FILES.md` updated with Story 3 entries | luana-platform | gate-runner |

## §13. Capability YAML + modules/ Updates Required

**None.** Story 3 is mechanical lift. Does not change user-facing capability. No `docs/product/capabilities/{m}/*.yaml` updates. No `docs/product/modules/{m}.md` updates.

Outcome `luana-platform-migration.md` § progress log will be updated by /pm at story close.

## §14. Open Questions for PM (none blocking)

All scope decisions resolved per outcome §7.3 lift mode + this architect document:

- **6 packages, not 8-12 packages:** spec said "8-12 tickets" — confirmed (11 tickets emitted in 06-tickets.yaml). NO escalation.
- **2 copilot_provider/ subfolders deferred:** per §9. Same pattern as Story 2. NO escalation.
- **iam stays brand-agnostic:** verified via grep + codified arch fitness test. NO escalation.
- **No cross-Story-4/5 coupling:** verified via grep cross-module. tenant_profile is independent of iam (true). NO escalation.
- **tenant_domains/workers/tasks.py:** small ARQ worker file, no module coupling — lifts with module. Added `arq` dep to pyproject.

If Chris reads this and wants to lift copilot_provider/ subfolders early (would require stubbing `BaseCopilotProvider` protocol in `luana-core-platform.links.ports`), that's REFACTOR (scope expansion) — escalate.
