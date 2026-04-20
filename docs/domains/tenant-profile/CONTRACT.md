# tenant_profile — CONTRACT

**Status:** authoritative. Single source of truth for the `tenant_profile` bounded
context introduced on 2026-04-20. Both backend and frontend agents consume this
document. Any divergence between this contract and implementation is a defect.

**Rationale:** `business_types` is operational tenant classification, not brand
identity. Migrating it out of `BrandIdentity` into a first-class aggregate
establishes the SSoT, removes a cross-feature FSD violation, unlocks future
tenant-wide classification fields (sector, company_size, stage, goals) and lets
downstream modules read via a typed port instead of a JSONB blob.

---

## 1. Domain model

### 1.1 Aggregate root — `TenantProfile`

```python
# backend/src/modules/tenant_profile/domain/tenant_profile.py

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from uuid import UUID

from src.shared.domain.datetime_utils import utc_now
from src.shared.domain.expert_business_type import ExpertBusinessType


BUSINESS_TYPES_MIN = 1
BUSINESS_TYPES_MAX = 2                 # product-tunable
RATE_LIMIT_WINDOW = timedelta(days=30)  # one change per calendar month


@dataclass
class TenantProfile:
    tenant_id: UUID
    business_types: tuple[ExpertBusinessType, ...]
    declared_at: datetime | None              # None → never completed onboarding
    updated_at: datetime
    last_business_types_change_at: datetime | None

    # ── Invariants ─────────────────────────────────────────────────────
    @property
    def is_complete(self) -> bool:
        return self.declared_at is not None and len(self.business_types) >= BUSINESS_TYPES_MIN

    def can_change_business_types(self, now: datetime | None = None) -> bool:
        """False while inside the 30-day rate-limit window after last change.

        First-time declaration (``declared_at is None``) is never rate-limited.
        """
        if self.declared_at is None:
            return True
        anchor = self.last_business_types_change_at or self.declared_at
        return (now or utc_now()) - anchor >= RATE_LIMIT_WINDOW

    def next_allowed_change_at(self) -> datetime | None:
        """Absolute timestamp after which a new change is allowed, or None
        if unrestricted."""
        anchor = self.last_business_types_change_at or self.declared_at
        return anchor + RATE_LIMIT_WINDOW if anchor else None

    # ── Command ────────────────────────────────────────────────────────
    def update_business_types(
        self,
        new: tuple[ExpertBusinessType, ...],
        *,
        now: datetime | None = None,
    ) -> list["DomainEvent"]:
        if not (BUSINESS_TYPES_MIN <= len(new) <= BUSINESS_TYPES_MAX):
            raise ValueError(
                f"business_types must have between {BUSINESS_TYPES_MIN} "
                f"and {BUSINESS_TYPES_MAX} entries; got {len(new)}"
            )
        if len(set(new)) != len(new):
            raise ValueError("business_types must not contain duplicates")

        now = now or utc_now()

        if self.declared_at is None:
            # First-time declaration — never rate-limited
            self.business_types = new
            self.declared_at = now
            self.updated_at = now
            self.last_business_types_change_at = now
            return [TenantProfileInitialized(tenant_id=self.tenant_id, business_types=new, at=now)]

        if set(self.business_types) == set(new):
            return []  # no-op write, no event

        if not self.can_change_business_types(now):
            raise BusinessTypesChangeRateLimited(
                next_allowed_at=self.next_allowed_change_at(),
            )

        old = self.business_types
        self.business_types = new
        self.updated_at = now
        self.last_business_types_change_at = now
        return [BusinessTypesChanged(tenant_id=self.tenant_id, old=old, new=new, at=now)]
```

### 1.2 Domain events

```python
# backend/src/modules/tenant_profile/domain/events.py

@dataclass(frozen=True)
class TenantProfileInitialized:
    tenant_id: UUID
    business_types: tuple[ExpertBusinessType, ...]
    at: datetime

@dataclass(frozen=True)
class BusinessTypesChanged:
    tenant_id: UUID
    old: tuple[ExpertBusinessType, ...]
    new: tuple[ExpertBusinessType, ...]
    at: datetime
```

### 1.3 Domain exceptions

```python
class BusinessTypesChangeRateLimited(DomainError):
    def __init__(self, next_allowed_at: datetime):
        self.next_allowed_at = next_allowed_at
        super().__init__(f"business_types change rate-limited until {next_allowed_at.isoformat()}")
```

### 1.4 Repository interface

```python
# backend/src/modules/tenant_profile/domain/repository.py

class TenantProfileRepository(ABC):
    @abstractmethod
    async def get_or_none(self, tenant_id: UUID) -> TenantProfile | None: ...

    @abstractmethod
    async def get_or_init(self, tenant_id: UUID) -> TenantProfile:
        """Returns existing profile or a fresh one with no business_types."""

    @abstractmethod
    async def save(self, profile: TenantProfile) -> None: ...
```

---

## 2. Persistence

### 2.1 Table schema (migration 052)

```sql
CREATE TABLE IF NOT EXISTS tenant_profiles (
    tenant_id UUID PRIMARY KEY REFERENCES tenants(id) ON DELETE CASCADE,
    business_types TEXT[] NOT NULL DEFAULT '{}',
    declared_at TIMESTAMPTZ,
    last_business_types_change_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_tenant_profiles_business_types
    ON tenant_profiles USING GIN (business_types);

CREATE INDEX IF NOT EXISTS idx_tenant_profiles_declared_at
    ON tenant_profiles (declared_at);
```

**CHECK constraint via domain validation only** — Python-side invariants cover
length 1..N and uniqueness; DB stays simple for forward-compat with N changes.

### 2.2 Backfill (migration 052 downgrade-safe step)

```sql
-- Idempotent raw SQL inside upgrade() of 052
INSERT INTO tenant_profiles (tenant_id, business_types, declared_at, last_business_types_change_at, updated_at)
SELECT
    t.id,
    COALESCE(
        (t.config_json #> '{brand_settings,identity,business_types}')::jsonb -- jsonb array
             |> ARRAY(SELECT jsonb_array_elements_text(...)),
        '{}'::text[]
    ),
    NOW(),         -- declared_at — prior tenants treated as declared now
    NOW(),
    NOW()
FROM tenants t
WHERE NOT EXISTS (SELECT 1 FROM tenant_profiles tp WHERE tp.tenant_id = t.id);
```

> **Implementation note:** use a `DO $$ ... $$` block to translate JSONB array to
> `TEXT[]` safely and skip tenants whose `business_types` is malformed, logging
> via `RAISE NOTICE`. Backend agent writes the definitive SQL.

### 2.3 Migration 053 — strip from BrandIdentity blob

```sql
UPDATE tenants
SET config_json = jsonb_set(
    config_json,
    '{brand_settings,identity}',
    (config_json #> '{brand_settings,identity}')::jsonb - 'business_types'
)
WHERE config_json #> '{brand_settings,identity,business_types}' IS NOT NULL;
```

---

## 3. API

### 3.1 Endpoints

| Method | Path | Purpose | Response |
|---|---|---|---|
| `GET`   | `/api/v1/tenant/profile` | Current tenant profile | `TenantProfileResponse` |
| `PATCH` | `/api/v1/tenant/profile` | Update business_types | `TenantProfileResponse` |
| `GET`   | `/api/v1/catalogs/business-types` | Enum catalog (metadata) | `BusinessTypesCatalogResponse` |

All tenant-scoped endpoints require `X-Tenant-ID`. The catalogs endpoint is
tenant-agnostic but still requires auth (any authenticated user).

### 3.2 DTOs

```python
# backend/src/modules/tenant_profile/api/dtos.py

class TenantProfileResponse(BaseModel):
    tenant_id: UUID
    business_types: list[ExpertBusinessTypeSlug]
    declared_at: datetime | None
    updated_at: datetime
    is_complete: bool
    can_change_now: bool
    next_allowed_change_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


class UpdateTenantProfileRequest(BaseModel):
    business_types: list[ExpertBusinessTypeSlug] = Field(
        min_length=BUSINESS_TYPES_MIN,
        max_length=BUSINESS_TYPES_MAX,
    )


class BusinessTypeMetadataDTO(BaseModel):
    slug: ExpertBusinessTypeSlug
    label_es: str
    description_es: str
    icon_name: str
    examples_es: list[str]


class BusinessTypesCatalogResponse(BaseModel):
    version: str                # _CATALOG_VERSION bumper
    business_types: list[BusinessTypeMetadataDTO]
```

### 3.3 Error responses

| HTTP | Code | When |
|---|---|---|
| 400 | `invalid_business_types` | length / duplicate violations |
| 409 | `rate_limited` | rate-limit inside 30-day window. Body: `{ "next_allowed_change_at": "..." }` |
| 403 | `forbidden` | tenant mismatch |

### 3.4 Deprecated (removed in Migration 053)

- `GET /api/v1/brand/expert-business-types/catalog` → 301 to `/api/v1/catalogs/business-types` for two weeks, then deleted.
- `PATCH /api/v1/brand/settings` with `identity.business_types` → **400 from day one**. Payload rejected with hint pointing to new endpoint.
- `GET /api/v1/brand/settings` stops returning `identity.business_types` (field removed from `BrandIdentity`).

---

## 4. Cross-module port

```python
# backend/src/shared/links/ports/tenant_profile.py

async def get_tenant_business_types(
    db: AsyncSession,
    tenant_id: UUID,
) -> tuple[ExpertBusinessType, ...]:
    """Read-only access for other bounded contexts.

    Returns an empty tuple when the tenant has no declared profile yet.
    Used by: sales_agent (grounding), landing (template fallback),
    analytics (segmentation, future).
    """
    from src.modules.tenant_profile.infrastructure.repositories.tenant_profile_repository import (
        TenantProfileRepository,
    )
    profile = await TenantProfileRepository(db).get_or_none(tenant_id)
    return profile.business_types if profile else ()


async def is_tenant_profile_complete(
    db: AsyncSession,
    tenant_id: UUID,
) -> bool:
    from src.modules.tenant_profile.infrastructure.repositories.tenant_profile_repository import (
        TenantProfileRepository,
    )
    profile = await TenantProfileRepository(db).get_or_none(tenant_id)
    return profile.is_complete if profile else False
```

Do not expose the aggregate or repository type to other modules. Ports only.

---

## 5. Event dispatch

The service layer (`tenant_profile/application/services/tenant_profile_service.py`)
publishes events to the existing in-process bus in `shared/events/`. For
`BusinessTypesChanged` we MUST publish a WebSocket broadcast to the tenant's
connected clients so active UI invalidates React Query caches for:

- `['offer-type-presets', business_types]`
- `['offer-formats', business_types, archetype]`
- `['tenant-profile']`

Server-side subscribers to evaluate (future — not required in this sprint):

- Landing page cache invalidation
- Sales-agent knowledge rebuild

---

## 6. Frontend contract

### 6.1 Feature slice

```
frontend/src/features/tenant-profile/
├── api/
│   └── tenant-profile-api.ts        # fetchClient wrappers
├── hooks/
│   ├── use-tenant-profile.ts        # GET
│   ├── use-update-tenant-profile.ts # PATCH (with cache invalidation)
│   └── use-business-types-catalog.ts
├── components/
│   ├── BusinessTypesSelector.tsx    # Primitive (moved from brand-studio)
│   ├── BusinessTypesChipBar.tsx     # Display chip (moved to shared later)
│   ├── BusinessTypeCard.tsx         # Single card primitive
│   └── ChangeBusinessTypesConfirmDialog.tsx  # Impact warning
├── types/
│   └── tenant-profile.ts
└── utils/
    └── rate-limit.ts                # formatNextAllowed helpers
```

### 6.2 Global shell integration

- `components/shared/app-header/TenantContextBar.tsx` renders `BusinessTypesChipBar`
  (imported from `features/tenant-profile`). Shown on every authenticated page.
  Clicking the chip routes to `/settings/perfil-negocio`.

### 6.3 Routes

```
app/(main)/[tenantId]/
├── onboarding/
│   └── perfil-negocio/
│       └── page.tsx                 # Full-screen gate
└── (dashboard)/
    └── settings/
        └── perfil-negocio/
            └── page.tsx             # Settings sub-section
```

### 6.4 Gating middleware

`app/(main)/[tenantId]/(dashboard)/layout.tsx` server-component logic:

```typescript
const profile = await fetchTenantProfileServer();
if (!profile.is_complete && !pathname.startsWith("/onboarding/")) {
  redirect(`/${tenantId}/onboarding/perfil-negocio?returnTo=${pathname}`);
}
```

### 6.5 PATCH UX

- Button disabled with tooltip `"Próxima edición disponible: {date}"` when
  `can_change_now === false`.
- On submit when changing post-declaration: open
  `ChangeBusinessTypesConfirmDialog` explaining impact (presets, landing, agent).
- On 409 from backend (race): show toast with `next_allowed_change_at`.
- On success: invalidate the three React Query keys listed in §5.

### 6.6 Wizard + offer-studio consumers

- `CreateOfferWizard.tsx`: replace `settings.identity.business_types` with
  `useTenantProfile().business_types`.
- `OfferStudioView.tsx`: remove `BusinessTypeOnboardingDialog` entirely — gating
  middleware guarantees the tenant arrives with a complete profile.
- `PresetBadge.tsx`: no change (does not read business_types directly).

### 6.7 Brand Studio cleanup

- Remove sidebar entry for "Tipo de negocio".
- Delete `features/brand-studio/components/business-types/` entire directory.
- `section-pages.tsx`: remove import and read-only render.
- Remove `business_types` from `BrandIdentitySchema` (Zod) and `settings.identity`.

---

## 7. Testing

### 7.1 Backend tests

- `tests/modules/tenant_profile/test_tenant_profile_aggregate.py` — invariants
  (min/max, duplicates, rate-limit window, event emission).
- `tests/modules/tenant_profile/test_tenant_profile_service.py` — orchestration.
- `tests/modules/tenant_profile/test_tenant_profile_repository.py` — SQLAlchemy
  round-trip + tenant isolation.
- `tests/modules/tenant_profile/test_tenant_profile_api.py` — endpoints, 400/409/403.
- `tests/architecture/test_business_types_ssot.py` — NEW: no `business_types`
  field declared outside `tenant_profile/domain/`.
- `tests/architecture/test_brand_identity_has_no_business_types.py` — NEW:
  `BrandIdentity.model_fields` MUST NOT include `business_types`.

### 7.2 Frontend tests

- `features/tenant-profile/__tests__/*.test.tsx` — hooks, rate-limit helpers,
  selector, chip bar.
- `features/tenant-profile/api/__tests__/tenant-profile-api.test.ts` — fetchClient.
- `e2e/specs/smoke/tenant-profile-gating.smoke.spec.ts` — redirect when incomplete.

### 7.3 Architecture fitness (new rule)

No module outside `tenant_profile/` may:
- declare a field named `business_types` in a domain dataclass or Pydantic model;
- import `OFFER_TYPE_PRESET_CATALOG`-adjacent helpers expecting business_types
  from `BrandIdentity`.

---

## 8. Business rules — single source of truth

| Rule | Value | Enforcement |
|---|---|---|
| Min business_types | 1 | domain + DTO |
| Max business_types | 2 | domain + DTO constant (product-tunable via `BUSINESS_TYPES_MAX`) |
| No duplicates | — | domain |
| Rate limit between changes | 30 days | domain `can_change_business_types` |
| First-time declaration is not rate-limited | — | domain |
| No-op write (same set) does not reset the clock | — | domain |
| Effect on existing offers | none (confirmed by product) | product behaviour, no code |

---

## 9. Out of scope (for this sprint)

- Splitting `BrandSettings` into a proper `brand_settings` table (stays JSONB).
- Adding sector / company_size / stage / goals fields to `TenantProfile` (DTO
  and aggregate are designed to admit them without schema migration beyond
  column adds).
- Server-side cache invalidation for Landing page previews.
- Analytics event forwarding for `BusinessTypesChanged`.

---

## 10. Glossary

- **`business_types`** — tuple of `ExpertBusinessType` slugs declared by the
  tenant. Drives preset filtering, format suitability, ladder hints, landing
  template defaults, and sales-agent grounding.
- **`ExpertBusinessType`** — enum in `shared/domain/expert_business_type.py`.
  Remains the catalog SSoT; this refactor does not touch it.
- **Gating** — server-side redirect that prevents unauthenticated-for-this-flow
  access to dashboard routes until the profile is complete.
