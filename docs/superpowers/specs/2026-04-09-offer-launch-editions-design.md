# Offer Studio — Launch Editions

## Problem

Offers with recurring nature (cohorts, events, webinars, workshops) need multiple launches over time. Currently the model supports only ONE set of dates (in `ProgramDetails.start_date`/`EventDetails.start_date`) and ONE pricing config per offer. To launch a new cohort, users must duplicate the entire offer — losing history, breaking Sales Agent context, and creating maintenance burden.

## Solution

Add a `LaunchEdition` child entity to `Offer`. The offer remains the "template" (identity, promise, psychology, value stack, base pricing). Each edition represents one launch with its own dates, optional pricing override, capacity, and status.

## Scope

**Applies to archetypes:** Programa, Experiencia, Servicio (when `frequency_type = one_off`).
**Does NOT apply to:** Producto, Membresía (evergreen — no editions section shown).

## Data Model

### New enum: `EditionStatus`

```python
class EditionStatus(str, Enum):
    DRAFT = "draft"           # Tentative dates, not public
    UPCOMING = "upcoming"     # Published, registration open
    ACTIVE = "active"         # In progress
    COMPLETED = "completed"   # Finished
    CANCELLED = "cancelled"   # Cancelled
```

### New domain entity: `LaunchEdition`

```python
class LaunchEdition(BaseEntity):
    id: UUID | None = None
    offer_id: UUID
    tenant_id: UUID

    # Identity
    edition_name: str                    # "Cohorte #4 — Octubre 2026"
    edition_number: int                  # Auto-incremented per offer

    # Dates
    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"

    # Pricing
    pricing_override: list[PricingStructure] | None = None  # null = inherit from offer

    # Capacity
    capacity: int | None = None          # null = unlimited
    enrollment_count: int = 0

    # Status
    status: EditionStatus = EditionStatus.DRAFT

    # Overrides (null = inherit from offer)
    location_override: dict[str, Any] | None = None  # For events: venue changes

    # Internal
    notes: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
```

### New SQLAlchemy model: `LaunchEditionModel`

Table name: `launch_editions`

```python
class LaunchEditionModel(Base):
    __tablename__ = "launch_editions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    offer_id = Column(UUID(as_uuid=True), ForeignKey("products.id"), nullable=False)
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    edition_name = Column(String, nullable=False)
    edition_number = Column(Integer, nullable=False)

    start_date = Column(DateTime(timezone=True), nullable=False)
    end_date = Column(DateTime(timezone=True), nullable=True)
    registration_start = Column(DateTime(timezone=True), nullable=True)
    registration_end = Column(DateTime(timezone=True), nullable=True)
    timezone = Column(String, default="UTC")

    pricing_override = Column(JSONB, nullable=True)  # null = inherit
    capacity = Column(Integer, nullable=True)
    enrollment_count = Column(Integer, default=0)

    status = Column(String, default="draft")
    location_override = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

Unique constraint: `(offer_id, edition_number)`.
Index: `(tenant_id, offer_id, status)` for common queries.

### Pricing rule

- `pricing_override IS NULL` → edition uses offer's `pricing_options`
- `pricing_override IS NOT NULL` → edition uses its own pricing (early bird, special price, etc.)
- The `currency` is always inherited from the offer (no per-edition currency).

## API Endpoints

All under `/api/v1/offer/products/{offer_id}/editions/`:

| Method | Path | Response | Description |
|--------|------|----------|-------------|
| GET | `/` | `list[LaunchEditionResponse]` | List editions for offer (ordered by start_date desc) |
| POST | `/` | `LaunchEditionResponse` | Create new edition |
| GET | `/{edition_id}` | `LaunchEditionResponse` | Get single edition |
| PATCH | `/{edition_id}` | `LaunchEditionResponse` | Update edition |
| DELETE | `/{edition_id}` | 204 | Soft-delete (set status=cancelled) |
| POST | `/{edition_id}/duplicate` | `LaunchEditionResponse` | Clone edition with incremented number |

### DTOs

```python
class LaunchEditionCreate(BaseModel):
    edition_name: str | None = None       # Auto-generated if omitted
    start_date: datetime
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"
    pricing_override: list[PricingStructure] | None = None
    capacity: int | None = None
    location_override: dict[str, Any] | None = None
    notes: str | None = None

class LaunchEditionUpdate(BaseModel):
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

class LaunchEditionResponse(BaseModel):
    id: UUID
    offer_id: UUID
    edition_name: str
    edition_number: int
    start_date: datetime
    end_date: datetime | None
    registration_start: datetime | None
    registration_end: datetime | None
    timezone: str
    pricing_override: list[dict[str, Any]] | None
    effective_pricing: list[dict[str, Any]]  # Resolved: override or offer's pricing
    currency: str                             # From parent offer
    capacity: int | None
    enrollment_count: int
    status: str
    location_override: dict[str, Any] | None
    notes: str | None
    created_at: datetime | None
    updated_at: datetime | None
```

Key: `effective_pricing` is computed server-side — if `pricing_override` is null, it returns the offer's `pricing_options`. This simplifies frontend logic.

## Backend Architecture (DDD layers)

### Domain (`offer/domain/`)
- `launch_edition.py` — `LaunchEdition` entity, `EditionStatus` enum
- `LaunchEditionCreate`, `LaunchEditionUpdate` value objects

### Infrastructure (`offer/infrastructure/`)
- `models/launch_edition_model.py` — SQLAlchemy model
- `repositories/launch_edition_repository.py` — CRUD, `get_next_edition_number()`, `get_active_or_upcoming()`

### Application (`offer/application/`)
- `launch_edition_service.py` — Business logic: create (auto-number, auto-name), update, duplicate, resolve effective pricing

### API (`offer/api/`)
- `launch_editions.py` — FastAPI router mounted as sub-router of products

## Frontend Architecture

### Types (`features/offer-studio/types/`)
- Add `LaunchEdition`, `LaunchEditionCreate`, `LaunchEditionUpdate`, `EditionStatus` to types
- Add Zod schema `LaunchEditionSchema`

### API (`features/offer-studio/api/`)
- `editions-api.ts` — CRUD operations for editions

### Hooks (`features/offer-studio/hooks/`)
- `use-editions.ts` — React Query hook: list, create, update, delete, duplicate

### Components (`features/offer-studio/components/editions/`)
- `EditionsSection.tsx` — Main section (list of edition cards + "Nueva Edición" button)
- `EditionCard.tsx` — Single edition summary card with status badge, dates, pricing, actions
- `EditionFormDialog.tsx` — Dialog/sheet for creating or editing an edition
- `EditionPricingOverride.tsx` — Toggle + pricing form for price override
- `EditionStatusBadge.tsx` — Color-coded status pill

### Navigation integration
- Add "Ediciones" nav item in `OfferNavRail` — only visible when archetype is Programa, Experiencia, or Servicio
- New section in `SECTION_REGISTRY` config

## AI Extraction Impact

The existing `offer_extract_details` prompt template extracts `start_date`, `end_date` etc. into `specific_details`. This continues to work as-is for the offer template.

New behavior: after the main extraction completes, if dates are found in `specific_details` AND the archetype supports editions, auto-create a `LaunchEdition` from those dates. This is a post-extraction hook in `OfferExtractionService.extract_all()`, not a new extractor.

## Sales Agent Integration (future, not this PR)

`TenantKnowledgeBuilder` already reads offers. After this feature ships, a follow-up will:
- Query active/upcoming editions alongside offers
- Inject "next launch" context into agent_identity prompt
- Enable the agent to answer "when's the next cohort?" with real data

## Migration

Idempotent Alembic migration using raw SQL:

```sql
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
);
CREATE INDEX IF NOT EXISTS ix_launch_editions_tenant_offer_status
    ON launch_editions (tenant_id, offer_id, status);
```

## Edition Lifecycle

```
Draft → Upcoming → Active → Completed
                ↘ Cancelled
```

Transitions can be manual (user changes status) or automatic (background job checks dates). For MVP: manual only. Auto-transitions are a follow-up.

## What is NOT in scope

- Analytics per edition (future)
- Sales Agent edition-aware context injection (future, separate PR)
- Landing page edition-aware countdown (future)
- Auto-status transitions via background job (future)
- Migrating existing `ProgramDetails.start_date`/`EventDetails.start_date` to editions (existing data stays as-is, editions are additive)
