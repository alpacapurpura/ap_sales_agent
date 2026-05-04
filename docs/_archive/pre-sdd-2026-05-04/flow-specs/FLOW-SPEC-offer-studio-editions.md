# Flow Spec — Offer Studio: Editions, Landing Per-Edition, Enrollment & Copilot Rework

> **Scope:** End-to-end refactor of the `offer` module (backend DDD) plus integrations with `sales_agent`, `copilot`, `landing`, `analytics`, and the frontend `offer-studio` feature slice.
>
> **Status:** Proposed. Pending implementation.
>
> **Date:** 2026-04-16
>
> **Author:** ux-flow-architect (skill-generated from interactive design session).
>
> **Related rules:** `.claude/rules/backend-ddd.md`, `.claude/rules/frontend-fsd.md`, `.claude/rules/backend-migrations.md`, `.claude/rules/tenant-isolation.md`, `.claude/rules/tdd-mandatory.md`, `.claude/rules/copilot-resilience.md`.

---

## 1. Context & Problem Statement

### 1.1 Current pain points (validated)

| # | Problem | Severity |
|---|---------|----------|
| 1 | Creating the first edition crashes with `TypeError: Cannot read properties of undefined (reading 'map')` at `EditionPricingOverride.tsx:55`. Root cause: broken prop contract (`offerPricing` declared non-nullable, passed `undefined` when offer has no `pricing_options`). | 🔴 Critical |
| 2 | Each edition must have its own landing page; current schema has `landing_pages.offer_id` only — no `edition_id`. A single landing is shared across all editions. | 🔴 Critical |
| 3 | Each edition must have its own assets (flyers, videos); `offer_assets.offer_id` FK points to `products.id`, not to an edition. Assets cannot be edition-scoped. | 🔴 Critical |
| 4 | No way to clone edition N landing/assets into edition N+1 while evolving content. `duplicate_edition` only copies dates/pricing. | 🟡 High |
| 5 | Sales Agent cannot enroll a lead in a specific edition. The `sales_agent` module has zero references to editions. | 🔴 Critical |
| 6 | No `enrollments` table; no lead-to-edition linkage; no waitlist mechanism for future editions without a set date. | 🔴 Critical |
| 7 | Copilot `offer_config.py` interview creates the offer but never asks about the first edition — user lands on empty Editions tab and must manually create one. | 🟡 High |
| 8 | Copilot focus mode uses generic `entity_write` tool without domain validation for editions. A rewrite with edition-specific tools is required. | 🟡 High |
| 9 | Archetype capabilities (who supports editions, what fields are required) are scattered across 4 files: `offer.py` validator, `enums.py` default delivery map, `editions-copy.ts` frontend copy, `EditionsOptIn.tsx` render conditional. No single source of truth. | 🟡 High |
| 10 | `LaunchEdition.start_date` is `nullable=False` in SQL. Impossible to create a placeholder edition without a date. | 🟡 High |
| 11 | `pricing_override` is a `list[PricingStructure]` with no temporal validity. Cannot model early bird → regular → last call with date windows. | 🟢 Medium |
| 12 | No per-edition analytics. Cannot compare conversion/CAC/revenue across editions #1 → #N. | 🟢 Medium |

### 1.2 Design principles (derived from user input)

1. **Any archetype may support editions in the future.** Start with EXPERIENCIA, PROGRAMA, SERVICIO; keep architecture open for PRODUCTO/MEMBRESIA to opt-in later.
2. **Editions are first-class citizens.** They own landings, assets, pricing tiers, enrollments, analytics.
3. **Placeholder-first creation.** Every offer with `supports_editions=true` is born with a DRAFT edition #1 automatically — the user never faces an empty Editions tab.
4. **Clone-with-evolution.** When creating edition N+1, inherit from edition N and evolve via conversational diff in copilot. Decoupled after clone.
5. **Sales agent only offers public, non-draft editions.** DRAFT/PAUSED editions are invisible to leads.
6. **Waitlist as a first-class state.** Enrollment without `edition_id` is valid when no public edition exists.
7. **Copilot is the primary entry point.** Every flow must work end-to-end via interview mode (creation) and focus mode (update/clone).

---

## 2. Archetype Catalog (new single source of truth)

### 2.1 Problem

Scattered archetype knowledge:
- `src/modules/offer/domain/offer.py:170-182` — validator forces `has_editions=False` for PRODUCTO/MEMBRESIA.
- `src/modules/offer/domain/enums.py:284-290` — `ARCHETYPE_DEFAULT_DELIVERY` map.
- `frontend/src/features/offer-studio/utils/editions-copy.ts` — Spanish copy per archetype.
- `frontend/src/features/offer-studio/components/editor/sections/common/EditionsOptIn.tsx` — render conditional.

### 2.2 Proposed artifact

**New file:** `backend/src/modules/offer/domain/archetype_catalog.py`

```python
from dataclasses import dataclass
from enum import StrEnum

from src.modules.offer.domain.enums import (
    OfferArchetype,
    OfferDeliveryModel,
    FulfillmentType,
)


class EditionStructure(StrEnum):
    NONE = "none"                  # no editions
    SINGLE_DATE = "single_date"    # one date, possibly recurring (EXPERIENCIA)
    COHORT = "cohort"              # start → end window (PROGRAMA)
    RECURRING = "recurring"        # rolling batches (SERVICIO opt-in)


@dataclass(frozen=True)
class ArchetypeCapabilities:
    archetype: OfferArchetype
    supports_editions: bool
    edition_structure: EditionStructure
    edition_noun_es: str          # "fecha", "cohorte", "lote"
    edition_noun_plural_es: str   # "fechas", "cohortes", "lotes"
    requires_start_date: bool     # true when edition transitions to UPCOMING
    requires_end_date: bool
    requires_location: bool
    supports_capacity: bool
    supports_waitlist: bool
    default_delivery: OfferDeliveryModel
    default_fulfillment: FulfillmentType
    label_es: str
    icon_name: str                # lucide-react icon


ARCHETYPE_CATALOG: dict[OfferArchetype, ArchetypeCapabilities] = {
    OfferArchetype.EXPERIENCIA: ArchetypeCapabilities(
        archetype=OfferArchetype.EXPERIENCIA,
        supports_editions=True,
        edition_structure=EditionStructure.SINGLE_DATE,
        edition_noun_es="fecha",
        edition_noun_plural_es="fechas",
        requires_start_date=True,
        requires_end_date=False,
        requires_location=True,
        supports_capacity=True,
        supports_waitlist=True,
        default_delivery=OfferDeliveryModel.DWY,
        default_fulfillment=FulfillmentType.MANUAL_PROVISIONING,
        label_es="Experiencia / Evento",
        icon_name="Calendar",
    ),
    OfferArchetype.PROGRAMA: ArchetypeCapabilities(
        archetype=OfferArchetype.PROGRAMA,
        supports_editions=True,
        edition_structure=EditionStructure.COHORT,
        edition_noun_es="cohorte",
        edition_noun_plural_es="cohortes",
        requires_start_date=True,
        requires_end_date=True,
        requires_location=False,
        supports_capacity=True,
        supports_waitlist=True,
        default_delivery=OfferDeliveryModel.DWY,
        default_fulfillment=FulfillmentType.LMS_ACCESS,
        label_es="Programa / Cohorte",
        icon_name="GraduationCap",
    ),
    OfferArchetype.SERVICIO: ArchetypeCapabilities(
        archetype=OfferArchetype.SERVICIO,
        supports_editions=True,  # opt-in, default true
        edition_structure=EditionStructure.RECURRING,
        edition_noun_es="lote",
        edition_noun_plural_es="lotes",
        requires_start_date=False,
        requires_end_date=False,
        requires_location=False,
        supports_capacity=True,
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DFY,
        default_fulfillment=FulfillmentType.MANUAL_PROVISIONING,
        label_es="Servicio",
        icon_name="Briefcase",
    ),
    OfferArchetype.PRODUCTO: ArchetypeCapabilities(
        archetype=OfferArchetype.PRODUCTO,
        supports_editions=False,
        edition_structure=EditionStructure.NONE,
        edition_noun_es="",
        edition_noun_plural_es="",
        requires_start_date=False,
        requires_end_date=False,
        requires_location=False,
        supports_capacity=False,
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DIY,
        default_fulfillment=FulfillmentType.DIGITAL_DOWNLOAD,
        label_es="Producto Digital",
        icon_name="Package",
    ),
    OfferArchetype.MEMBRESIA: ArchetypeCapabilities(
        archetype=OfferArchetype.MEMBRESIA,
        supports_editions=False,
        edition_structure=EditionStructure.NONE,
        edition_noun_es="",
        edition_noun_plural_es="",
        requires_start_date=False,
        requires_end_date=False,
        requires_location=False,
        supports_capacity=False,
        supports_waitlist=False,
        default_delivery=OfferDeliveryModel.DIY,
        default_fulfillment=FulfillmentType.LMS_ACCESS,
        label_es="Membresía / Suscripción",
        icon_name="Repeat",
    ),
}


def get_capabilities(archetype: OfferArchetype) -> ArchetypeCapabilities:
    return ARCHETYPE_CATALOG[archetype]
```

### 2.3 Consumption points (refactor targets)

- **Backend**
  - `offer.py` validator → delegate to `get_capabilities(archetype).supports_editions` instead of hardcoded list.
  - `launch_edition_service.create_edition` → use `supports_editions` + `requires_start_date` + `requires_location` for validation.
  - `offer_service.create` → when `supports_editions=true`, emit `OfferCreated` domain event that triggers placeholder edition creation.
- **API endpoint (new)**
  - `GET /api/v1/offer/archetypes/catalog` → returns list[ArchetypeCapabilitiesDTO] for frontend consumption (no secrets, cacheable).
- **Frontend**
  - Delete `utils/editions-copy.ts` entirely.
  - Rewrite `EditionsOptIn.tsx` to consume catalog via `useArchetypeCatalog()` hook.
  - Wizard `CreateOfferWizard.tsx` uses catalog to render archetype picker cards.
- **Architecture test (new)**
  - `tests/architecture/test_archetype_catalog.py` — fails if `OfferArchetype` enum value is added without a corresponding `ARCHETYPE_CATALOG` entry.

---

## 3. Domain Model Changes

### 3.1 `LaunchEdition` — rediseño

**File:** `backend/src/modules/offer/domain/launch_edition.py`

Changes:

```diff
class EditionStatus(StrEnum):
    DRAFT = "draft"
    UPCOMING = "upcoming"
    ACTIVE = "active"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


+class EditionVisibility(StrEnum):
+    PRIVATE = "private"   # not visible to sales agent / public URLs
+    PUBLIC = "public"     # available for enrollment


class LaunchEdition(BaseEntity):
    id: UUID | None = None
    offer_id: UUID
    tenant_id: UUID

    edition_name: str
    edition_number: int

-   start_date: datetime
+   start_date: datetime | None = None      # NOW NULLABLE (placeholder state)
    end_date: datetime | None = None
    registration_start: datetime | None = None
    registration_end: datetime | None = None
    timezone: str = "UTC"

-   pricing_override: list[PricingStructure] | None = None
+   pricing_tiers: list[PricingTier] = []    # replaces pricing_override

    capacity: int | None = None
    enrollment_count: int = 0

    status: EditionStatus = EditionStatus.DRAFT
+   visibility: EditionVisibility = EditionVisibility.PRIVATE

    location_override: dict[str, Any] | None = None
    notes: str | None = None

+   cloned_from_edition_id: UUID | None = None   # provenance

    created_at: datetime | None = None
    updated_at: datetime | None = None

    @model_validator(mode="after")
    def validate_dates(self) -> LaunchEdition:
        if self.end_date and self.start_date and self.end_date < self.start_date:
            raise ValueError("end_date cannot be before start_date")
        if self.registration_start and self.registration_end and self.registration_end < self.registration_start:
            raise ValueError("registration_end cannot be before registration_start")

+       # Public editions MUST have a start_date.
+       if self.visibility == EditionVisibility.PUBLIC and self.start_date is None:
+           raise ValueError("PUBLIC edition requires start_date")
+
+       # UPCOMING/ACTIVE editions MUST have a start_date.
+       if self.status in (EditionStatus.UPCOMING, EditionStatus.ACTIVE) and self.start_date is None:
+           raise ValueError(f"{self.status.value} edition requires start_date")
        return self
```

### 3.2 New VO — `PricingTier`

**File:** `backend/src/modules/offer/domain/launch_edition.py` (same file)

```python
class PricingTier(BaseEntity):
    label: str                             # "early_bird" | "regular" | "last_call" | custom
    pricing: PricingStructure              # reuses existing structure
    valid_from: datetime | None = None     # None = open-ended start
    valid_until: datetime | None = None    # None = open-ended end
    sort_order: int = 0                    # display order in UI


def resolve_active_tier(tiers: list[PricingTier], now: datetime) -> PricingTier | None:
    """Returns the first tier whose window contains `now`, ordered by sort_order.
    Returns None if no tier is active (edition may be pre-sales or closed).
    """
    applicable = [
        t for t in sorted(tiers, key=lambda x: x.sort_order)
        if (t.valid_from is None or t.valid_from <= now)
        and (t.valid_until is None or now < t.valid_until)
    ]
    return applicable[0] if applicable else None
```

**Invariant:** within a single edition, tier windows MUST NOT overlap (validator at edition level).

### 3.3 New entity — `Enrollment`

**New module subtree:** `backend/src/modules/sales_agent/domain/enrollment.py`

> **Rationale:** enrollment is a sales-domain concept (lead → customer). It belongs with sales_agent, not with offer catalog. This respects DDD module boundaries.

```python
class EnrollmentStatus(StrEnum):
    INTENT = "intent"                   # lead expressed interest, no commitment
    WAITLIST = "waitlist"               # lead waiting for a public edition
    PAYMENT_PENDING = "payment_pending" # payment link sent
    PAID = "paid"                       # payment confirmed
    ATTENDED = "attended"               # lead attended (close-by-meeting flow)
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentProvider(StrEnum):
    STRIPE = "stripe"
    MERCADOPAGO = "mercadopago"
    MANUAL = "manual"                   # marked paid by user, offline


class Enrollment(BaseEntity):
    id: UUID | None = None
    tenant_id: UUID
    offer_id: UUID
    edition_id: UUID | None = None      # None = waitlist

    contact_id: UUID                    # FK to crm.contacts
    conversation_id: UUID | None = None # FK to sales_agent.conversations (origin)

    status: EnrollmentStatus = EnrollmentStatus.INTENT

    pricing_tier_label: str | None = None
    pricing_amount: float | None = None
    currency: str | None = None

    payment_provider: PaymentProvider | None = None
    payment_transaction_id: str | None = None
    payment_link_url: str | None = None

    created_at: datetime | None = None
    paid_at: datetime | None = None
    attended_at: datetime | None = None
    cancelled_at: datetime | None = None
```

**Key invariants:**
- `edition_id IS NULL` ↔ `status = WAITLIST`.
- `status = PAID` ↔ `paid_at IS NOT NULL` AND `payment_transaction_id IS NOT NULL` (manual provider allowed).
- `status = ATTENDED` requires `paid_at IS NOT NULL` (cannot attend without paying).
- All queries MUST filter by `tenant_id`.

### 3.4 Domain events (new)

**File:** `backend/src/modules/offer/domain/events.py` (extend)

```python
class OfferCreated(DomainEvent):
    offer_id: UUID
    archetype: OfferArchetype
    supports_editions: bool

class EditionCreated(DomainEvent):
    edition_id: UUID
    offer_id: UUID
    edition_number: int
    is_placeholder: bool
    cloned_from_edition_id: UUID | None

class EditionPublished(DomainEvent):
    """Fires when visibility transitions to PUBLIC. Triggers waitlist notification."""
    edition_id: UUID
    offer_id: UUID
    start_date: datetime

class EditionClonedWithLanding(DomainEvent):
    new_edition_id: UUID
    source_edition_id: UUID
    new_landing_id: UUID | None
```

**File:** `backend/src/modules/sales_agent/domain/events.py` (new or extend)

```python
class EnrollmentCreated(DomainEvent):
    enrollment_id: UUID
    offer_id: UUID
    edition_id: UUID | None
    contact_id: UUID
    status: EnrollmentStatus

class EnrollmentPaid(DomainEvent):
    enrollment_id: UUID
    edition_id: UUID | None
    paid_at: datetime
    amount: float
    currency: str
```

### 3.5 Event handlers

| Event | Handler | Effect |
|-------|---------|--------|
| `OfferCreated` (supports_editions=true) | `CreateDraftEditionOnOfferCreated` | Creates placeholder `LaunchEdition(status=DRAFT, visibility=PRIVATE, start_date=null, edition_number=1)` |
| `EditionPublished` | `NotifyWaitlistOnEditionPublished` | Lists `Enrollment(status=WAITLIST, offer_id=X)`, marks as eligible, emits notifications |
| `EnrollmentPaid` | `IncrementEditionEnrollmentCount` | `edition.enrollment_count += 1` if `edition_id` set |

---

## 4. Schema Migrations

All migrations MUST be idempotent (see `.claude/rules/backend-migrations.md`).

### 4.1 Migration: `add_edition_id_to_landing_and_assets`

```python
"""add edition_id to landing_pages and offer_assets

Revision ID: XXXXXX
Revises: (prev)
"""


def upgrade() -> None:
    op.execute("""
        ALTER TABLE landing_pages
        ADD COLUMN IF NOT EXISTS edition_id UUID NULL;
    """)
    op.execute("""
        ALTER TABLE landing_pages
        ADD CONSTRAINT fk_landing_edition
        FOREIGN KEY (edition_id) REFERENCES launch_editions(id) ON DELETE CASCADE
        NOT VALID;
    """)
    # Partial index: enforces 1 landing per (offer, edition) when edition is set
    op.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS uq_landing_per_offer_edition
        ON landing_pages (tenant_id, offer_id, edition_id)
        WHERE deleted_at IS NULL AND edition_id IS NOT NULL;
    """)

    op.execute("""
        ALTER TABLE offer_assets
        ADD COLUMN IF NOT EXISTS edition_id UUID NULL;
    """)
    op.execute("""
        ALTER TABLE offer_assets
        ADD COLUMN IF NOT EXISTS shared_across_editions BOOLEAN NOT NULL DEFAULT FALSE;
    """)
    op.execute("""
        ALTER TABLE offer_assets
        ADD CONSTRAINT fk_asset_edition
        FOREIGN KEY (edition_id) REFERENCES launch_editions(id) ON DELETE SET NULL
        NOT VALID;
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_offer_assets_edition
        ON offer_assets (tenant_id, offer_id, edition_id)
        WHERE deleted_at IS NULL;
    """)
```

### 4.2 Migration: `relax_edition_start_date_and_add_visibility_provenance`

```python
def upgrade() -> None:
    op.execute("""
        ALTER TABLE launch_editions
        ALTER COLUMN start_date DROP NOT NULL;
    """)
    op.execute("""
        ALTER TABLE launch_editions
        ADD COLUMN IF NOT EXISTS visibility VARCHAR(20) NOT NULL DEFAULT 'private';
    """)
    op.execute("""
        ALTER TABLE launch_editions
        ADD COLUMN IF NOT EXISTS cloned_from_edition_id UUID NULL;
    """)
    op.execute("""
        ALTER TABLE launch_editions
        ADD CONSTRAINT fk_edition_cloned_from
        FOREIGN KEY (cloned_from_edition_id) REFERENCES launch_editions(id) ON DELETE SET NULL
        NOT VALID;
    """)
```

### 4.3 Migration: `migrate_pricing_override_to_pricing_tiers`

```python
def upgrade() -> None:
    op.execute("""
        ALTER TABLE launch_editions
        ADD COLUMN IF NOT EXISTS pricing_tiers JSONB NULL;
    """)
    # One-shot data migration: existing pricing_override becomes a single "regular" tier
    op.execute("""
        UPDATE launch_editions
        SET pricing_tiers = jsonb_build_array(
            jsonb_build_object(
                'label', 'regular',
                'pricing', pricing_override_item,
                'valid_from', NULL,
                'valid_until', NULL,
                'sort_order', 0
            )
        )
        FROM (
            SELECT id, jsonb_array_elements(pricing_override) AS pricing_override_item
            FROM launch_editions
            WHERE pricing_override IS NOT NULL
        ) sub
        WHERE launch_editions.id = sub.id
          AND launch_editions.pricing_tiers IS NULL;
    """)
    # pricing_override column kept for 1 release, then dropped in follow-up migration
```

### 4.4 Migration: `create_enrollments_table`

```python
def upgrade() -> None:
    op.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            tenant_id UUID NOT NULL,
            offer_id UUID NOT NULL,
            edition_id UUID NULL,
            contact_id UUID NOT NULL,
            conversation_id UUID NULL,
            status VARCHAR(30) NOT NULL DEFAULT 'intent',
            pricing_tier_label VARCHAR(50) NULL,
            pricing_amount NUMERIC(12,2) NULL,
            currency VARCHAR(3) NULL,
            payment_provider VARCHAR(20) NULL,
            payment_transaction_id VARCHAR(255) NULL,
            payment_link_url TEXT NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            paid_at TIMESTAMPTZ NULL,
            attended_at TIMESTAMPTZ NULL,
            cancelled_at TIMESTAMPTZ NULL,
            deleted_at TIMESTAMPTZ NULL
        );
    """)
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_tenant ON enrollments(tenant_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_edition ON enrollments(edition_id) WHERE edition_id IS NOT NULL;")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_contact ON enrollments(tenant_id, contact_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_waitlist ON enrollments(tenant_id, offer_id) WHERE status = 'waitlist';")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_status ON enrollments(tenant_id, status);")
```

### 4.5 Migration test

Run against cloned DB (see `.claude/rules/backend-migrations.md` "Test Before Prod" section) before merging.

---

## 5. Journey Maps

### Journey 1 — Create Offer with First Edition (via Copilot Interview)

**Persona:** Creator building a masterclass.
**Trigger:** Opens Copilot, chooses "Crear oferta nueva" in interview mode.
**Frequency:** Once per new offer (5-15 per tenant typical).
**Priority:** Critical.

| Step | User Action | Expected Route | Nav Element | Status (target) |
|------|-------------|----------------|-------------|-----------------|
| 1 | Sidebar "Copilot" or "+" button on Offer Studio | `/copilot/interview?topic=offer` | Sidebar CTA | ✅ OK |
| 2 | Copilot asks archetype → user picks "Masterclass" | (chat) | Chat quick-reply | ✅ OK |
| 3 | Copilot extracts offer data via existing interview tools (voice, docs) | (chat) | Tools: `extract_structured`, `web_research`, `offer_alternatives` | ✅ OK |
| 4 | **NEW BLOCK:** Copilot: "¿Cuándo planeas tu primera fecha?" | (chat) | Conversational + quick-reply "Todavía no sé" | ❌ Missing → add |
| 5a | User skips → placeholder edition DRAFT created | `/offer-studio/{offer_id}` | Auto-redirect on completion | ❌ Missing → add |
| 5b | User provides date → edition UPCOMING created | `/offer-studio/{offer_id}` | Auto-redirect on completion | ❌ Missing → add |
| 6 | Copilot: "¿Genero landing base?" | (chat) | Quick-reply yes/no | ⚠️ Friction → uses existing tool but not tied to edition |
| 7 | User sees offer detail with Editions tab showing edition #1 | `/offer-studio/{offer_id}` (tab=editions) | Tab bar | ⚠️ Friction → tab tucked inside section today |

**Friction Points:**
- Step 7: `EditionsSection` is a card inside the editor today, not a prominent tab. Needs elevation to full tab.
- Step 6: Landing generation today links to `offer_id` only; must target `edition_id` too.

**Dead Ends:**
- Without step 4-5, user completes interview and lands on offer with empty Editions card — must manually open dialog (which currently crashes per problem #1).

**Missing Connections:**
- Steps 4 → 5 → 6: need to wire `first_edition` into `OfferCreate` extraction schema + atomic service creation.

---

### Journey 2 — Create Next Edition (Clone Evolutionary, via Copilot)

**Persona:** Creator running their 3rd masterclass.
**Trigger:** Edition #2 is COMPLETED; user clicks "Nueva edición" or says "abrir próxima fecha" in copilot.
**Frequency:** Once per edition cycle (weekly to yearly).
**Priority:** Critical.

| Step | User Action | Expected Route | Nav Element | Status (target) |
|------|-------------|----------------|-------------|-----------------|
| 1 | "Nueva edición" button on edition list OR copilot chat command | `/offer-studio/{offer_id}/editions` | Button / chat tool | ❌ Missing (button exists but routes to broken dialog) |
| 2 | Copilot opens sub-thread: "Basada en Edición #2. ¿Qué cambia?" | (chat split view) | Quick-reply: [Solo fechas] [Precio + fechas] [Cambios mayores] [Desde cero] | ❌ Missing → new tool `clone_edition` |
| 3a | "Solo fechas" → copilot asks new date, clones landing + assets, find-replace date placeholders | (chat + progress) | Tool execution | ❌ Missing |
| 3b | "Cambios mayores" → copilot asks: "¿Qué cambia? Puedes adjuntar archivos." | (chat + upload) | Tool `clone_edition(strategy=MAJOR_CHANGES)` + `ingest_attachments` | ❌ Missing |
| 3c | "Desde cero" → edition shell, no clone | (chat) | Tool `create_edition` without clone | ⚠️ Partial (exists without strategy) |
| 4 | Copilot: "Listo. ¿Generar landing ahora?" | (chat) | Tool `generate_landing(edition_id=new)` | ⚠️ Friction → exists but needs edition scope |
| 5 | User lands on new edition detail page, DRAFT + PRIVATE | `/offer-studio/{offer_id}/editions/{new_id}` | Auto-redirect | ❌ Missing (no detail page today) |
| 6 | User reviews, publishes → status=UPCOMING + visibility=PUBLIC | (detail page) | "Publicar edición" button | ❌ Missing |

**Friction Points:**
- Step 4-5: today landing tool doesn't know about editions.

**Dead Ends:**
- Step 1: "Nueva edición" button opens the crashing dialog (problem #1).

**Missing Connections:**
- Need `clone_edition` tool + `update_edition` tool + edition detail page with publish action.

---

### Journey 3 — Sales Agent Enrolls Lead in Active Edition

**Persona:** Lead chatting with sales agent, interested in the masterclass.
**Trigger:** Lead says "quiero inscribirme" or equivalent intent.
**Frequency:** Highest (every qualified lead).
**Priority:** Critical.

| Step | User Action | Expected Route | Nav Element | Status (target) |
|------|-------------|----------------|-------------|-----------------|
| 1 | Lead expresses purchase intent in chat | Sales agent chat | Intent detection | ⚠️ Friction (exists, generic) |
| 2 | Agent calls `list_public_editions(offer_id)` → filters by UPCOMING/ACTIVE + PUBLIC | Tool call | Tool | ❌ Missing → new tool |
| 3 | Agent presents active/next edition: "Tenemos lanzamiento el 15-may" | Chat | Response | ❌ Missing (prompt update) |
| 4 | Lead confirms | Chat | Intent confirmation | ✅ OK |
| 5 | Agent calls `create_enrollment(contact, offer, edition=active_id)` → status=INTENT | Tool call | Tool | ❌ Missing → new tool |
| 6 | Agent calls `generate_payment_link(enrollment_id)` via connections provider | Tool call | Tool | ❌ Missing → new tool |
| 7 | Agent sends payment link to lead, status=PAYMENT_PENDING | Chat | Response | ❌ Missing |
| 8 | Lead pays; Stripe/MercadoPago webhook → `EnrollmentPaid` event → status=PAID | Webhook | Connection | ⚠️ Partial (webhooks exist for some providers) |
| 9 | Agent sends confirmation + next steps | Chat | Response | ❌ Missing (prompt update) |

**Alternative close-by-meeting flow:**
- Step 7 branches: if archetype's onboarding is `BOOK_KICKOFF_CALL`, agent schedules via `scheduling` module.
- Step 8 becomes: user marks enrollment as `ATTENDED` + `PAID` manually after the meeting (via sales studio UI).

**Friction Points:**
- Prompt-level: agent doesn't know about editions today. Needs prompt extension + tool registration.

**Dead Ends:**
- Without `Enrollment` entity, no way to track lead-to-edition link.

**Missing Connections:**
- Edition-aware tools (list, create, payment), edition-aware prompt templates.

---

### Journey 4 — Waitlist Conversion When New Edition Publishes

**Persona:** Lead asked about the masterclass in the past; no public edition was available at the time.
**Trigger:** User publishes a new edition (status=UPCOMING + visibility=PUBLIC).
**Frequency:** Per edition launch.
**Priority:** Important.

| Step | User Action | Expected Route | Nav Element | Status (target) |
|------|-------------|----------------|-------------|-----------------|
| 1 | Past lead chat: "¿Y en agosto?" → no public edition | Agent chat | — | ❌ Missing (agent doesn't offer waitlist) |
| 2 | Agent: "Aún no anunciamos próxima fecha, ¿te aviso cuando publique?" | Chat | — | ❌ Missing → prompt update |
| 3 | Lead confirms → `create_enrollment(contact, offer, edition=null, status=WAITLIST)` | Tool call | Tool `create_enrollment_waitlist` | ❌ Missing |
| 4 | **Later:** User creates edition #4, publishes → `EditionPublished` event | Domain event | — | ❌ Missing |
| 5 | `NotifyWaitlistOnEditionPublished` handler queries `waitlist` for offer | Handler | — | ❌ Missing |
| 6 | User sees notification in Offer Studio: "12 leads en waitlist — ¿notificar?" | `/offer-studio/{offer_id}/editions/{new_id}` | Inline banner | ❌ Missing |
| 7 | User clicks "Notificar a todos" → agent sends message to each waitlisted contact | Bulk action | — | ❌ Missing |
| 8 | Lead receives: "Ya lanzamos agosto. ¿Te apunto?" → converts to regular enrollment flow | Chat | — | ❌ Missing |

**Friction Points:**
- Entire journey is missing. Needs domain model + handler + UI widget + agent bulk-message capability.

**Dead Ends:**
- No waitlist = no recovery of cold leads.

**Missing Connections:**
- Domain event → handler → notification → bulk-enroll flow.

---

## 6. Gap Analysis

### 6.1 Priority Matrix

| # | Finding | Category | Impact | Effort | Priority |
|---|---------|----------|--------|--------|----------|
| 1 | `EditionPricingOverride` undefined crash | Broken journey | High | Low | P1 |
| 2 | Archetype capabilities scattered (no SSOT) | Architecture | Medium | Medium | P1 |
| 3 | Edition `start_date` non-nullable blocks placeholder | Architecture | High | Low | P1 |
| 4 | No `edition_id` on landings/assets | Missing connection | Critical | High | P1 |
| 5 | No `Enrollment` entity | Missing | Critical | High | P1 |
| 6 | Sales agent has no edition awareness | Missing | Critical | High | P1 |
| 7 | Copilot doesn't ask about first edition | Dead-end | High | Medium | P1 |
| 8 | No clone-with-evolution tool | Missing | High | High | P2 |
| 9 | No temporal pricing tiers | Architecture | Medium | Medium | P2 |
| 10 | No public URL routing per edition | Missing | Medium | Medium | P2 |
| 11 | `entity_write` generic tool lacks edition domain validation | Architecture | Medium | Medium | P2 |
| 12 | No edition detail page in frontend | Missing | High | High | P2 |
| 13 | No asset clone modal ("jalar de otra edición") | Missing | Medium | Medium | P2 |
| 14 | No waitlist flow end-to-end | Missing | Medium | High | P2 |
| 15 | No per-edition analytics / compare dashboard | Missing | Medium | Medium | P3 |

---

## 7. Refactor Plan (11 Phases)

Each phase is independently shippable. Each MUST include: unit tests (TDD), architecture test where applicable, idempotent migration where applicable, and a verification run.

### Phase 0 — Hotfix `EditionPricingOverride` crash

**Goal:** Unblock the user immediately.

**TDD test (first, RED):**
- `frontend/src/features/offer-studio/components/editions/__tests__/EditionPricingOverride.test.tsx`
  - `renders without crash when offerPricing is undefined`
  - `renders "sin precio base" copy when offerPricing is empty`

**Fix:**
1. `EditionPricingOverride.tsx` — change prop type to `PricingStructure[] | undefined`, guard with `const pricing = offerPricing ?? [];` before any `.map`. Add empty-state copy.
2. `EditionsSection.tsx` — pass `offerPricing: offer?.pricing_options ?? []` (instead of assuming defined).
3. `EditionFormDialog.tsx` — fallback display for empty tier list.

**Acceptance:** opening the "Nueva Edición" dialog on any offer (even one with no pricing yet) must not crash.

**Files changed:** 3. Commits: 1. Effort: Low.

---

### Phase 1 — Archetype Catalog SSOT

**Goal:** Eliminate duplicated archetype knowledge.

**Backend:**
- Create `backend/src/modules/offer/domain/archetype_catalog.py` (section 2.2).
- Refactor `offer.py` validator to use `get_capabilities(archetype).supports_editions`.
- New endpoint `GET /api/v1/offer/archetypes/catalog` returning DTO list.
- Test: `tests/architecture/test_archetype_catalog.py` — every `OfferArchetype` enum value has a `ARCHETYPE_CATALOG` entry.

**Frontend:**
- Delete `utils/editions-copy.ts`.
- New hook `features/offer-studio/hooks/use-archetype-catalog.ts` (React Query, 1h staleTime).
- Rewrite `EditionsOptIn.tsx`, `CreateOfferWizard.tsx` to use catalog.

**Acceptance:** grep `has_editions` in backend and frontend returns only the catalog file and the Offer domain entity. No scattered logic.

**Files changed:** ~12. Commits: 2. Effort: Medium.

---

### Phase 2 — Edition Placeholder Lifecycle

**Goal:** Offer creation auto-spawns a DRAFT edition when archetype supports editions.

**Backend:**
- Migration 4.2 (nullable start_date + visibility + cloned_from).
- Extend `LaunchEdition` domain (section 3.1).
- `OfferCreated` event (section 3.4).
- `CreateDraftEditionOnOfferCreated` handler wired to `shared/event_bus`.
- Update `OfferService.create()` to emit event.

**Tests (TDD):**
- Domain: `test_edition_draft_allows_null_start_date`.
- Service: `test_offer_create_for_experiencia_emits_placeholder_edition`.
- Transition: `test_edition_to_upcoming_requires_start_date`.

**Acceptance:** after creating an EXPERIENCIA offer via API or copilot, `GET /offer/{id}/editions` returns exactly one edition, status=DRAFT, start_date=null.

**Files changed:** ~8. Commits: 2. Effort: Medium.

---

### Phase 3 — Per-Edition Landing & Assets

**Goal:** Each edition owns its landing and assets; edition-agnostic fallback remains.

**Backend:**
- Migration 4.1 (add `edition_id` to `landing_pages` and `offer_assets`, add `shared_across_editions`).
- Update `LandingRepository` + `OfferAssetRepository` to accept `edition_id` filter.
- Update `GET /offer/{offer_id}/assets` → support `?edition_id=X` query param.
- Update `GET /landing/{id}` resolver: if `edition_id` set → return edition-scoped; else offer-template.
- New service `EditionCloneService`:
  - `clone_landing(source_edition_id, target_edition_id, strategy: LITERAL|DATE_REPLACE|AI_REGEN, changes_brief?: str)`.
  - `clone_assets(source_edition_id, target_edition_id, asset_ids?: list[UUID])`.
  - Strategy `DATE_REPLACE`: uses Puck block traversal + token-replace for `{{start_date}}`, `{{end_date}}`, `{{location}}` tokens (implemented via a new `LandingTokenizer`).
  - Strategy `AI_REGEN`: delegates to existing `landing_generation_service` with prompt context `{prior_landing_blocks, changes_brief, attachments}`.

**Tests (TDD):**
- `test_clone_landing_literal_strategy_deep_copies_blocks`.
- `test_clone_landing_date_replace_substitutes_tokens`.
- `test_clone_landing_ai_regen_calls_generation_service_with_context`.
- `test_asset_list_respects_edition_filter`.

**Acceptance:** cloning edition #2 into #3 with strategy=DATE_REPLACE yields a new landing with updated dates, same structure. Editing #3 after clone does NOT affect #2.

**Files changed:** ~15. Commits: 3-4. Effort: High.

---

### Phase 4 — Temporal Pricing Tiers

**Goal:** Replace `pricing_override: list[PricingStructure]` with `pricing_tiers: list[PricingTier]` with temporal validity.

**Backend:**
- Migration 4.3 (add `pricing_tiers JSONB`, data-migrate existing `pricing_override` → single "regular" tier).
- Domain: `PricingTier` VO + `resolve_active_tier` fn (section 3.2).
- Edition validator: tier windows non-overlapping.
- Service: `LaunchEditionService.resolve_effective_pricing` returns active tier for a given datetime.
- API: `LaunchEditionResponse.active_tier: PricingTierDTO | None` for current moment.

**Tests (TDD):**
- `test_pricing_tier_windows_cannot_overlap`.
- `test_resolve_active_tier_returns_first_applicable_by_sort_order`.
- `test_pricing_tier_with_null_bounds_is_open_ended`.

**Acceptance:** an edition with [early_bird until 2026-05-01, regular 2026-05-01 to 2026-05-14, last_call 2026-05-14 to 2026-05-15] returns the correct tier for any `now()`.

**Files changed:** ~10. Commits: 2. Effort: Medium.

---

### Phase 5 — Enrollment Entity

**Goal:** Track lead-to-edition linkage with payment status.

**Backend:**
- Migration 4.4 (create `enrollments` table).
- New subtree `backend/src/modules/sales_agent/domain/enrollment.py` + repository + service.
- Domain events (section 3.4).
- API: `POST /api/v1/sales-agent/enrollments`, `GET /api/v1/sales-agent/enrollments?offer_id=X&edition_id=Y&status=Z`, `PATCH .../{id}/status`.
- Waitlist handlers (section 3.5).

**Tests (TDD):**
- Invariants (tenant isolation, status/paid_at coherence).
- `test_enrollment_without_edition_must_be_waitlist`.
- `test_edition_published_event_notifies_waitlist`.

**Acceptance:** creating an enrollment, transitioning through statuses, and querying waitlist per offer all work with tenant isolation verified.

**Files changed:** ~12. Commits: 3. Effort: High.

---

### Phase 6 — Sales Agent Edition Awareness

**Goal:** Sales agent can enroll leads in specific editions and handle waitlist.

**Backend tools (new):**
- `list_public_editions(offer_id) → list[EditionPublic]` (filters by UPCOMING/ACTIVE + PUBLIC).
- `create_enrollment(contact_id, offer_id, edition_id | null) → Enrollment`.
- `generate_payment_link(enrollment_id) → str` (delegates to connections provider — Stripe/MercadoPago).
- `check_payment_status(enrollment_id) → EnrollmentStatus`.
- `mark_enrollment_paid_manual(enrollment_id) → Enrollment`.
- `list_waitlist(offer_id) → list[Enrollment]`.
- `promote_waitlist_to_edition(enrollment_ids[], edition_id) → list[Enrollment]`.

**Prompt updates:**
- `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` — add edition awareness block:
  - "When a lead expresses purchase intent, always call `list_public_editions` first."
  - "Never propose a DRAFT or PAUSED edition."
  - "If no public edition exists, offer waitlist."

**Webhook integration:**
- Extend `connections` module to expose `/webhooks/stripe`, `/webhooks/mercadopago` that emit `EnrollmentPaid` events.
- Handler updates `enrollment.status` + `edition.enrollment_count`.

**Tests (TDD):**
- Tool unit tests with mock connections.
- `test_list_public_editions_excludes_draft_and_paused`.
- `test_generate_payment_link_uses_active_tier`.
- Integration: end-to-end flow with Stripe test webhook.

**Acceptance:** via chat playground, a lead can complete enrollment + payment + status transition to PAID automatically.

**Files changed:** ~18. Commits: 4-5. Effort: High.

---

### Phase 7 — Copilot Rework (Interview + Focus)

**Goal:** Copilot creates edition at offer birth; focus mode has edition-domain tools.

**Interview mode:**
- Extend `backend/src/modules/copilot/domain/interview_configs/offer_config.py`:
  - After archetype extraction, if `supports_editions`, append block asking for first edition.
  - Extend schema `OfferCreateInput` with `first_edition: FirstEditionInput | None`.
- Update `OfferCreationProcedure` (`copilot/application/procedures/offer_creation.py`) to:
  1. Create offer → auto-placeholder edition #1.
  2. If `first_edition` input present → update edition with `start_date`, `location`, tiers.
  3. If not → leave as DRAFT placeholder.

**Focus mode (replace generic `entity_write` for editions):**
- New tool `update_edition(edition_id, patch: EditionUpdatePatch)`:
  - Uses domain validator; returns human-readable diff for conversational confirmation.
- New tool `clone_edition(base_edition_id, strategy: LITERAL|DATE_REPLACE|MAJOR_CHANGES, changes_brief?, attachments?)`:
  - Invokes `EditionCloneService`.
  - If strategy=MAJOR_CHANGES → opens sub-thread asking for changes one-by-one.
- New tool `publish_edition(edition_id)`:
  - Transitions to UPCOMING + PUBLIC.
  - Emits `EditionPublished` event.
- Deprecate `entity_write` for `launch_editions` (still works for simple entities without invariants).

**Registry updates:**
- `copilot/application/tools/registry.py` → map offer-studio routes to include new tools.
- `copilot/domain/module_registry.py` → add `LaunchEdition` to `MODULE_REGISTRY["offer"]`.

**Tests (TDD):**
- `test_interview_offer_with_editions_captures_first_edition`.
- `test_update_edition_tool_rejects_invalid_transition`.
- `test_clone_edition_literal_creates_new_draft`.

**Acceptance:** creating an offer via copilot with "mi masterclass del 15 de mayo" yields offer + edition #1 UPCOMING in a single procedure run.

**Files changed:** ~15. Commits: 3. Effort: Medium-High.

---

### Phase 8 — Public URL Routing Per Edition

**Goal:** `/{tenant-slug}/{offer-slug}` redirects to active edition; `/{tenant-slug}/{offer-slug}/edicion/{N}` serves specific.

**Backend:**
- Public landing resolver:
  - `GET /public/{tenant_slug}/{offer_slug}` → look up active edition (status=ACTIVE; fallback UPCOMING nearest); 302 to `/public/{tenant_slug}/{offer_slug}/edicion/{number}`.
  - `GET /public/{tenant_slug}/{offer_slug}/edicion/{number}` → serve edition-scoped landing.
  - Fallback: if edition has no landing, serve offer-level template landing.
- Ensure public endpoints are tenant-safe (slug-based; no leakage).

**Frontend:**
- Route `app/_public/[tenantSlug]/[offerSlug]/page.tsx` — server redirect.
- Route `app/_public/[tenantSlug]/[offerSlug]/edicion/[number]/page.tsx` — renders landing.

**Tests:**
- Smoke E2E: public URL variants all load correctly.

**Acceptance:** `https://app.example.com/{tenant}/masterclass-copywriting` redirects to `/edicion/3` when edition 3 is ACTIVE.

**Files changed:** ~8. Commits: 2. Effort: Medium.

---

### Phase 9 — Frontend Offer Studio UI Revamp

**Goal:** Full edition lifecycle UI.

**New pages / routes:**
- `app/(main)/[tenantId]/offer-studio/[offerId]/editions/page.tsx` — edition list (cards grid).
- `app/(main)/[tenantId]/offer-studio/[offerId]/editions/[editionId]/page.tsx` — edition detail with sub-tabs.

**Sub-tabs per edition detail:**
- Info (dates, location, pricing tiers, capacity, status, publish CTA)
- Landing (Puck editor scoped to edition_id)
- Assets (gallery scoped to edition; "Jalar de otra edición" modal)
- Enrollments (table: contact, status, paid_at, tier)
- Analytics (vs prior editions compare)

**New components:**
- `features/offer-studio/components/editions/EditionListCard.tsx`
- `features/offer-studio/components/editions/EditionDetailShell.tsx`
- `features/offer-studio/components/editions/AssetCloneModal.tsx`
  - Grid of assets from OTHER editions (filterable by edition).
  - Multi-select → "Clonar a esta edición".
  - Confirmation: "¿Actualizar fechas a {new_date}?" → if yes, token-replace on metadata.
- `features/offer-studio/components/editions/PricingTiersEditor.tsx`
  - Timeline view of tier windows.
  - Drag-resize or date inputs.
  - Live validation (non-overlap).
- `features/offer-studio/components/editions/PublishEditionDialog.tsx` — confirms publish action.
- `features/offer-studio/components/editions/WaitlistBanner.tsx` — shown on newly published edition when waitlist > 0.

**Shared:**
- Navigation breadcrumb: `Offer Studio > {Offer} > Ediciones > Edición #{N}`.

**Sales studio:**
- `features/sales-studio/components/inbox/EnrollmentWidget.tsx` — inline chip in conversation showing active enrollment (status, edition, tier) with manual mark-paid / mark-attended actions.
- New page `app/(main)/[tenantId]/sales/enrollments/page.tsx` — enrollments table.

**Sidebar (no restructure, just 1 added entry):**
```
Sales Studio
├── Inbox
├── Pipeline
├── Enrollments  (NEW)
└── Scheduling
```

**Tests:**
- Component tests (TDD) for each new component.
- Visual smoke E2E.

**Acceptance:** user can navigate Offer Studio → Edition #N → edit landing → publish → enrollments populate as leads convert → analytics shows KPIs.

**Files changed:** ~35-40. Commits: 6-8. Effort: High.

---

### Phase 10 — Per-Edition Analytics

**Goal:** Compare conversion across editions.

**Backend:**
- Extend `metrics_service` + relevant stage services (capture, nurture, sales) to accept `edition_id` dimension.
- New endpoint `GET /api/v1/analytics/editions/compare?offer_id=X` returning array of per-edition KPIs.
- ETL updates: ensure metric rows carry `edition_id` when resolvable (landing page view → edition via URL; enrollment → edition from FK).

**Frontend:**
- New route `app/(main)/[tenantId]/growth-studio/offers/[offerId]/editions-compare/page.tsx`.
- Bar chart per KPI × edition.
- Timeseries overlay comparison.

**Acceptance:** visible diff in conversion rate between edition #1 and #2.

**Files changed:** ~12. Commits: 3. Effort: Medium.

---

## 8. Copilot Integration Summary

| Mode | Change | Phase |
|------|--------|-------|
| Interview (offer creation) | Ask for first edition if archetype supports it | 7 |
| Focus (offer detail page) | Expose `update_edition`, `clone_edition`, `publish_edition` tools | 7 |
| Focus (edition detail page) | Default toolset includes edition tools; route-based selection in `tools/registry.py` | 7 |
| Focus (sales inbox with lead) | Expose enrollment tools so user can instruct copilot to enroll a lead manually | 6, 7 |
| Schema introspection | `MODULE_REGISTRY["offer"]` gains `LaunchEdition` + `PricingTier` entries | 7 |

---

## 9. Sidebar & Navigation Changes

**Minimal sidebar change (single entry added):**

```diff
Sales Studio
├── Inbox
├── Pipeline
+├── Enrollments
└── Scheduling
```

**No other sidebar modifications.** All edition navigation is studio-internal (tabs + breadcrumb).

---

## 10. Acceptance Criteria (Global)

The refactor is complete when **all** of the following hold:

1. Creating any offer of archetype EXPERIENCIA/PROGRAMA/SERVICIO via copilot auto-creates a DRAFT placeholder edition.
2. Creating a new edition N+1 via copilot with `strategy=DATE_REPLACE` clones landing + assets from N and substitutes date tokens, without affecting N.
3. Sales agent, given a lead with purchase intent, lists only public non-draft editions, creates an enrollment, generates a payment link via the connected payment provider, and marks the enrollment PAID upon webhook confirmation.
4. A lead with no public edition available can be placed on waitlist; publishing a future edition surfaces a banner offering to notify waitlisted leads; clicking "Notify" triggers per-contact messages.
5. Public URL `/{tenant}/{offer}` redirects to the active edition's landing; `/{tenant}/{offer}/edicion/{N}` serves edition-scoped content.
6. Edition detail page exposes Info, Landing, Assets, Enrollments, Analytics tabs. Asset clone modal allows pulling from other editions with optional date token update.
7. Copilot `update_edition` tool rejects invalid domain transitions with human-readable error; `clone_edition` tool supports LITERAL / DATE_REPLACE / MAJOR_CHANGES strategies.
8. Architecture tests: `test_archetype_catalog` + existing `test_ddd_boundaries` + `test_api_contracts` all green. No new cross-module imports.
9. Migrations tested against cloned production DB; all idempotent.
10. 0 frontend ESLint errors; 0 TypeScript errors; all new components covered by Vitest + smoke E2E.
11. Per-edition analytics compare dashboard shows differential KPIs for ≥2 editions.

---

## 11. Prototype Reference

- **Preview URL:** `http://localhost:8888`
- **Preview directory:** `/tmp/nicolify-flow-preview/`
- **Pages (6 screens + sidebar context):**

| File | Represents | Primary Journey |
|------|-----------|-----------------|
| `index.html` | Offer Studio — offer detail with Editions tab prominent | 1 (create-first) entry point |
| `edition-list.html` | Editions grid for an offer (status badges, cards) | 1 and 2 |
| `new-edition-copilot.html` | Copilot split view creating edition N+1 with clone strategy picker | 2 |
| `edition-detail.html` | Edition detail page with sub-tabs (Info/Landing/Assets/Enrollments/Analytics) | 2, 3, 4 |
| `asset-clone-modal.html` | Modal: pick assets from other editions, with date-update toggle | 2 |
| `sales-inbox.html` | Sales agent chat with enrollment widget in side panel | 3, 4 |
| `enrollments.html` | Enrollments list view with filters (edition × status × tier) | 3, 4 |

---

## 12. Delta UI-SPECs (Downstream Implementation Briefs)

For each phase that touches frontend, a delta UI-SPEC lives in `docs/ui-specs/`:

| File | Scope | Status | Consumed by |
|------|-------|--------|-------------|
| `UI-SPEC-edition-list.md` | Edition list view with cards + status badges | To write after prototype validation | `nicolify-ux-designer` then `nicolify-frontend` |
| `UI-SPEC-edition-detail-shell.md` | Edition detail with 5 sub-tabs | Requires `ux-disruptivo` | `ux-disruptivo` |
| `UI-SPEC-asset-clone-modal.md` | Pull assets from other editions | Ready | `nicolify-frontend` |
| `UI-SPEC-pricing-tiers-editor.md` | Timeline + tier form | Requires `ux-disruptivo` | `ux-disruptivo` |
| `UI-SPEC-enrollment-widget.md` | Sales inbox enrollment chip | Ready | `nicolify-frontend` |
| `UI-SPEC-enrollments-page.md` | Enrollments table | Ready | `nicolify-frontend` |
| `UI-SPEC-editions-compare-dashboard.md` | Analytics compare | Requires `ux-disruptivo` | `ux-disruptivo` |

---

## 13. Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| Clone-with-evolution IA regen produces off-brand copy | Use existing Brand Studio voice/narrative context + prior landing as anchor; always show diff + require user confirmation before commit |
| Per-edition data balloons landing_pages table | Partial index + JSONB compression; measure at 1k editions |
| Webhook provider downtime breaks payment confirmation | Fallback: `check_payment_status` polling job + manual mark-paid action always available |
| Migration 4.1 adds FK with NOT VALID; must be validated later | Follow-up migration `VALIDATE CONSTRAINT fk_landing_edition` after data stabilizes |
| Scattered `has_editions` usages missed during refactor | Architecture test must grep for direct usages outside the catalog file and fail the build |
| Copilot interview gets longer (more blocks) | Offer creation is once-per-offer; acceptable tradeoff. Allow "skip" on every new block |

---

## 14. Open Questions (to resolve during implementation)

1. **Payment provider selection logic** — how does the agent know which provider to use per tenant? Probably: `TenantSettings.preferred_payment_provider`. Needs confirmation.
2. **Scheduling integration for close-by-meeting** — does the agent auto-book via `scheduling` module, or surface a link for the lead to self-book? User-defined per offer?
3. **Multi-language landings per edition** — out of scope for v1 but keep `landing_pages.locale` nullable so future work doesn't block.
4. **Recurring editions (weekly yoga classes)** — deferred. Current model supports one-off cohorts and single dates well; recurring templates are a Phase 11+ topic.
5. **Notification channel for waitlist** — email first (transactional), later ManyChat/Telegram per contact preference.

---

## 15. Implementation Order Summary

```
Phase 0 (hotfix)                → 1 commit, ~1h
    ↓
Phase 1 (archetype catalog)     → 2 commits, ~4h
    ↓
Phase 2 (edition placeholder)   → 2 commits, ~4h
    ↓
Phase 3 (per-edition landing)   → 3-4 commits, ~12h
    ↓
Phase 4 (pricing tiers)         → 2 commits, ~5h
    ↓
Phase 5 (enrollment entity)     → 3 commits, ~10h
    ↓
Phase 6 (sales agent tools)     → 4-5 commits, ~15h
    ↓
Phase 7 (copilot rework)        → 3 commits, ~10h
    ↓
Phase 8 (URL routing)           → 2 commits, ~4h
    ↓
Phase 9 (frontend revamp)       → 6-8 commits, ~25h
    ↓
Phase 10 (analytics)            → 3 commits, ~8h
```

**Total estimate:** ~30-35 commits, ~100 engineering hours for a single developer.
