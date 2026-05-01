# CONTRACT — PR-10-crm-contacts-api-forward-compat

> Owner: `nicolify-architect` (escrito por main session PM Opus 4.7 — agente paused mid-investigation; PM completó). SSoT pre-implementación. Builder: `nicolify-backend` (Sonnet). Auditor: `nicolify-backend-auditor` (Opus).

## § 0 Context Summary

| Campo | Valor |
|---|---|
| Architect run on | 2026-04-30 |
| Surface scope | business (BE-only) — `modules/crm/` |
| Builder owner | `nicolify-backend` (Sonnet) |
| Auditor owner | `nicolify-backend-auditor` (Opus) |
| CONTEXT-BRIEF source | PM main session (pre-flight Haiku paused — PM ejecutó greps inline) |
| Skills consulted | backend-expert (FastAPI + SQLA 2.0 patterns + Pydantic v2 strict) |
| Migrations expected | 0 |
| Tests expected | integration (sin mocks, política PR-4) + 1 arch test forward-compat |

### Surface ownership mapping

| Path | Builder | Auditor |
|---|---|---|
| `backend/src/modules/crm/api/contacts.py` (NEW) | `nicolify-backend` | `nicolify-backend-auditor` |
| `backend/src/modules/crm/api/dto/contacts.py` (NEW) | mismo | mismo |
| `backend/src/modules/crm/api/dto/contact_filters.py` (NEW) | mismo | mismo |
| `backend/src/modules/crm/application/services/contact_query_service.py` (NEW) | mismo | mismo |
| `backend/src/shared/links/ports/campaigns.py` (EXTEND si necesario) | mismo | mismo |
| `backend/src/main.py` (mount router NEW endpoint) | mismo | mismo |
| `backend/tests/modules/crm/test_contacts_api.py` (NEW) | mismo | mismo |
| `backend/tests/architecture/test_contacts_filter_params_forward_compat.py` (NEW) | mismo | mismo |

## § 1 Existing systems audit (NO NEW LAYER rule)

### Audit cross-module ejecutado (PM main session, 2026-04-30)

```bash
grep -rn "@router.get\|GET /contacts\|list_contacts\|get_contacts" backend/src/modules/crm/api/
grep -rn "PaginatedResponse\|PaginationParams" backend/src/modules/
grep -rn "from src.shared.links.ports.campaigns\|CampaignTaskLookup\|CampaignsLookupPort" backend/src/
find backend/src/modules/crm -name "*.py"
grep -n "class \|^[a-z_]* = Column" backend/src/shared/infrastructure/models/crm.py
grep -n "class LifecycleStage" backend/src/shared/domain/enums.py
```

### Sistemas existentes encontrados

| Sistema | Path | Estado | Decisión |
|---|---|---|---|
| `crm_leads_router` (legacy básico) | `modules/crm/api/leads.py` con `/search` (POST) + `/{lead_id}` (GET) | active | **EXTEND OFF — keep intact** (legacy consumers; scope distinto: search rápida vs unified contact view) |
| `crm_cdp_router` (resolución identidad) | `modules/crm/api/cdp.py` con `identify_customer` (POST) | active | **OFF-SCOPE** (escribe identidad, no lista contactos) |
| `crm_pipeline_router` (kanban view) | `modules/crm/api/pipeline.py` | active | **OFF-SCOPE** (kanban por stage, no listado paginado con filters) |
| `crm_copilot_provider` | `modules/crm/copilot_provider/{data_access,provider}.py` | active | READ-ONLY reference (PI-3 wrappea `/contacts` desde tools — no toca PR-10) |
| `PaginatedResponse[T]` (campaigns S1 PR-3) | `modules/campaigns/application/dtos/pagination.py` | active | **REUSE direct** — generic Pydantic wrapper con `items, total_count, limit, offset, has_more`. Importable cross-module (DTO neutro) |
| `CampaignsLookupPort` + `find_recent_campaign_tasks_for_leads` (batch) | `shared/links/ports/campaigns.py` (PR-8) | active | **REUSE direct** — batch lookup ya existe (`dict[UUID, CampaignTaskLookupResult]`); perfect para `has_campaign_engagement` filter sin N+1 |
| `LeadModel` + `CustomerProfileModel` + `CustomerIdentityModel` | `shared/infrastructure/models/crm.py` (cross-module shared) | active | **READ direct** — schemas estables, no `deleted_at` (no soft delete) |
| `LifecycleStage` enum | `shared/domain/enums.py` (8 valores: SUBSCRIBER/LEAD/MQL/SQL/OPPORTUNITY/CUSTOMER/EVANGELIST/CHURNED) | active | **REUSE direct** — Pydantic schema importa enum del shared |

### Decisión NEW endpoint group `/api/v1/contacts/`

**NEW** (no EXTEND legacy `/leads`). Razones:

1. **Scope semántico distinto**: `/leads/search` es POST search-by-criteria limited; `/contacts` es GET listado paginado con TODOS PI-3 filters declarados.
2. **Source de truth**: `/contacts` retorna unified `CustomerProfileModel + Lead` (LEFT JOIN) — la UX session FLOW-SPEC § 5.1 "Personas" describe exactamente esto. `/leads/{id}` retorna solo Lead row.
3. **Forward-compat**: PI-3 expande filters + agrega `/journey` + `/campaigns` sub-resources sobre `/contacts/{id}`. Si EXTEND `/leads`, PI-3 forzaría rename de URL.
4. **Cero breaking changes**: legacy consumers de `/leads` siguen funcionando. PR-10 puramente additivo.
5. **Criterio Chris 1000 clientes**: contract canonical desde día 1 = cero refactor PI-3.

**No-deuda gate**: ningún factory/registry/provider duplicado. Solo router + DTO + service nuevos siguiendo DDD strict.

## § 2 Domain entities (no nuevas)

PR-10 NO introduce nuevas entidades dominio. Reusa:
- `CustomerProfileModel` (shared/infrastructure/models/crm.py) — source of truth contact identity
- `LeadModel` (mismo file) — channel-specific data optional
- `CustomerIdentityModel` (mismo file) — multi-channel identifiers
- `LifecycleStage` enum (shared/domain/enums.py)

## § 3 API endpoints

### 3.1 GET /api/v1/contacts (live)

| Field | Detail |
|---|---|
| Path | `GET /api/v1/contacts` |
| Query params | `ContactFilterParams` (Pydantic schema con TODOS PI-3 filters declarados) + `limit: int (1..100, default 50)` + `offset: int (≥0, default 0)` |
| Auth | Clerk JWT + `X-Tenant-ID` (middleware existente) |
| response_model | `PaginatedResponse[ContactListItem]` |
| Status codes | 200, 400 (filter validation), 401 (auth), 403 (tenant mismatch) |
| Cache headers | `Cache-Control: private, max-age=30` (UI freshness > caching agresivo) |

### 3.2 GET /api/v1/contacts/{contact_id} (live)

| Field | Detail |
|---|---|
| Path | `GET /api/v1/contacts/{contact_id}` |
| Path param | `contact_id: UUID` (= `CustomerProfileModel.id`) |
| response_model | `ContactDetail` |
| Status codes | 200, 401, 404 (not found OR tenant mismatch — same response, no leak) |

### 3.3 GET /api/v1/contacts/{contact_id}/journey (501 deferred PI-3)

| Field | Detail |
|---|---|
| Path | `GET /api/v1/contacts/{contact_id}/journey` |
| response_model | `DeferredEndpointResponse` (NEW — explicit canonical schema for 501 stubs) |
| Status code | 501 |
| Headers | `Retry-After: PI-3` |
| OpenAPI description | "Timeline de eventos del contact (page views, opens, clicks, conversions). Endpoint canonical declarado para PR-10 forward-compat. Implementación deferred PI-3 — consumir cuando endpoint retorne 200." |

### 3.4 GET /api/v1/contacts/{contact_id}/campaigns (501 deferred PI-3)

| Field | Detail |
|---|---|
| Path | `GET /api/v1/contacts/{contact_id}/campaigns` |
| response_model | `DeferredEndpointResponse` |
| Status code | 501 |
| Headers | `Retry-After: PI-3` |
| OpenAPI description | "Historial de campañas en las que el contact participó. Endpoint canonical declarado para PR-10 forward-compat. Implementación deferred PI-3." |

### 3.5 GET /api/v1/contacts/_filter-schema (live)

| Field | Detail |
|---|---|
| Path | `GET /api/v1/contacts/_filter-schema` |
| response_model | `FilterSchemaResponse` (lista campos disponibles + tipo + valid values para enums) |
| Use case | FE consume metadata para construir filter UI dinámico (PI-3); también self-documenting |

## § 4 DTOs (Pydantic v2)

> Todos los DTOs `model_config = ConfigDict(extra="forbid")` (strict).

### 4.1 `ContactFilterParams` — flat schema con TODOS PI-3 filters

```python
# backend/src/modules/crm/api/dto/contact_filters.py
from datetime import datetime
from typing import Annotated
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from src.shared.domain.enums import LifecycleStage


class ContactFilterParams(BaseModel):
    """Forward-compat filter schema. UI lite consume subset; PI-3 expand UI sin tocar BE.

    INVARIANTE arch-test (forward_compat): este schema MUST contener TODOS los
    filtros listados en CANONICAL_FILTER_FIELDS abajo. Ratchet shrink-only —
    futuro adds OK; remove FAIL test.
    """

    model_config = ConfigDict(extra="forbid")

    # ── Lifecycle / scoring ───────────────────────────────────────────────────
    lifecycle_stage_in: list[LifecycleStage] | None = Field(
        default=None, description="Filtra por uno o más lifecycle stages."
    )
    score_min: int | None = Field(default=None, ge=0, le=100, description="lead_score mínimo (CustomerProfile)")
    score_max: int | None = Field(default=None, ge=0, le=100)

    # ── Source / acquisition ──────────────────────────────────────────────────
    source_in: list[str] | None = Field(default=None, description="Filtra por lead_source string")

    # ── Identity presence ─────────────────────────────────────────────────────
    has_email: bool | None = Field(default=None)
    has_phone: bool | None = Field(default=None)
    has_telegram_id: bool | None = Field(default=None)
    has_whatsapp_id: bool | None = Field(default=None)
    has_instagram_id: bool | None = Field(default=None)
    has_tiktok_id: bool | None = Field(default=None)

    # ── Activity / temporal ───────────────────────────────────────────────────
    created_after: datetime | None = Field(default=None)
    created_before: datetime | None = Field(default=None)
    last_activity_after: datetime | None = Field(default=None)
    last_activity_before: datetime | None = Field(default=None)
    is_inactive: bool | None = Field(default=None, description="CustomerProfile.is_inactive flag")

    # ── Engagement (cross-module via CampaignsLookupPort) ─────────────────────
    has_campaign_engagement: bool | None = Field(
        default=None,
        description="True si lead recibió >=1 CampaignTask SENT en últimos 90d.",
    )

    # ── Geographic ────────────────────────────────────────────────────────────
    country_in: list[str] | None = Field(default=None, description="ISO 3166-1 alpha-2 lowercase")

    # ── Search ────────────────────────────────────────────────────────────────
    q: str | None = Field(default=None, max_length=120, description="Full-text on full_name + primary_email + primary_phone")
```

**CANONICAL_FILTER_FIELDS** (listado canónico para arch test forward-compat):

```python
# backend/tests/architecture/test_contacts_filter_params_forward_compat.py
CANONICAL_FILTER_FIELDS: frozenset[str] = frozenset({
    "lifecycle_stage_in", "score_min", "score_max",
    "source_in",
    "has_email", "has_phone", "has_telegram_id", "has_whatsapp_id",
    "has_instagram_id", "has_tiktok_id",
    "created_after", "created_before", "last_activity_after", "last_activity_before",
    "is_inactive",
    "has_campaign_engagement",
    "country_in",
    "q",
})
```

### 4.2 `ContactListItem` (subset para tabla lite)

```python
# backend/src/modules/crm/api/dto/contacts.py

class ContactListItem(BaseModel):
    """Subset campos para tabla principal lite. PI-3 expande agregando ContactDetailColumns."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    full_name: str | None
    primary_email: str | None
    primary_phone: str | None
    lifecycle_stage: LifecycleStage
    lead_score: float
    is_inactive: bool
    last_activity_at: datetime | None
    lead_source: str | None
    country: str | None
    # Channel identifiers (boolean presence; valor real solo en Detail)
    has_telegram_id: bool
    has_whatsapp_id: bool
    has_instagram_id: bool
    has_tiktok_id: bool
    has_email: bool
    has_phone: bool
    # Campaign engagement summary (None = no batch lookup; bool = computed if filter applied)
    has_recent_campaign_engagement: bool | None
    created_at: datetime
```

### 4.3 `ContactDetail` (todo lo que UI lite drawer + página completa PI-3 reusan)

```python
class ContactIdentity(BaseModel):
    """Multi-channel identifier subset."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    type: str  # IdentityType.value
    value: str
    is_primary: bool
    verification_status: str
    last_seen_at: datetime


class ContactDetail(BaseModel):
    """Detail rico — drawer hoy + página completa PI-3 USAN MISMO SCHEMA."""

    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    full_name: str | None
    primary_email: str | None
    primary_phone: str | None
    lifecycle_stage: LifecycleStage
    lead_score: float
    rfm_segment: str | None
    lifetime_value: float
    is_inactive: bool
    first_conversion_at: datetime | None
    first_seen_at: datetime | None
    last_activity_at: datetime | None
    lead_source: str | None
    lead_source_detail: str | None
    traits: dict[str, object]
    computed_traits: dict[str, object]
    created_at: datetime
    updated_at: datetime | None

    # Lead-level data (None si no hay Lead row asociado)
    lead_id: UUID | None
    telegram_id: str | None
    whatsapp_id: str | None
    instagram_id: str | None
    tiktok_id: str | None
    api_id: str | None
    fit_score: int | None
    intent_score: int | None
    temperature: str | None
    is_blacklisted: bool | None
    last_interaction_date: datetime | None
    country: str | None
    conversation_summary: str | None

    # Multi-channel identities (CustomerIdentityModel)
    identities: list[ContactIdentity]
```

### 4.4 `DeferredEndpointResponse` (canonical for 501 stubs)

```python
class DeferredEndpointResponse(BaseModel):
    """Schema canonical para endpoints declarados pero deferred PI-3."""

    model_config = ConfigDict(extra="forbid")

    detail: str
    deferred_until: str  # "PI-3"
    canonical_path: str
    expected_response_model: str  # nombre de la clase Pydantic que retornará 200 (info doc)
```

### 4.5 `FilterSchemaResponse` (metadata para FE)

```python
class FilterFieldMeta(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    type: str  # "enum_list" | "int_range" | "bool" | "datetime" | "string"
    enum_values: list[str] | None
    description: str | None


class FilterSchemaResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: str  # "1.0" — bump cuando shape cambia
    fields: list[FilterFieldMeta]
```

## § 5 Service layer

### 5.1 `ContactQueryService` — application/services/contact_query_service.py

```python
class ContactQueryService:
    """Read-only query service. SQLA 2.0 async + tenant isolation cada query."""

    def __init__(
        self,
        session: AsyncSession,
        campaigns_lookup: CampaignsLookupPort,
        *,
        campaign_engagement_window_days: int = 90,
    ) -> None: ...

    async def list_contacts(
        self,
        *,
        tenant_id: UUID,
        filters: ContactFilterParams,
        limit: int,
        offset: int,
    ) -> PaginatedResponse[ContactListItem]: ...

    async def get_contact_detail(
        self,
        *,
        tenant_id: UUID,
        contact_id: UUID,
    ) -> ContactDetail | None: ...
```

### 5.2 Query strategy

- **Source table**: `customer_profiles` (CDP source of truth). `LEFT JOIN leads ON leads.customer_id = customer_profiles.id` para channel-specific data + scoring fields LeadModel. Aggregate Lead row preferring most-recent if multiple (rare per Chris CDP design).
- **Filtering**:
  - `lifecycle_stage_in` → `customer_profiles.lifecycle_stage IN (...)`
  - `score_min/max` → `customer_profiles.lead_score BETWEEN`
  - `source_in` → `customer_profiles.lead_source IN (...)`
  - `has_email` → `customer_profiles.primary_email IS NOT NULL` (rápido) OR `EXISTS(SELECT 1 FROM customer_identities WHERE profile_id = customer_profiles.id AND type = 'EMAIL')` (más completo). **Decisión: primary_email IS NOT NULL** (índice existente, rápido). PI-3 puede expandir si telemetría dice.
  - `has_phone` → `customer_profiles.primary_phone IS NOT NULL`
  - `has_telegram_id` → `EXISTS(SELECT 1 FROM leads WHERE customer_id = customer_profiles.id AND telegram_id IS NOT NULL)` (correlated EXISTS — Postgres optimiza)
  - `has_whatsapp_id`, `has_instagram_id`, `has_tiktok_id` mismo pattern
  - `created_after/before` → `customer_profiles.created_at`
  - `last_activity_after/before` → `customer_profiles.last_activity_at` (índice existente)
  - `is_inactive` → `customer_profiles.is_inactive`
  - `country_in` → `EXISTS(SELECT 1 FROM leads WHERE customer_id = customer_profiles.id AND country IN (...))` — leads.country tiene index
  - `has_campaign_engagement` → **2-step**: (a) primer query de profiles con todos los OTROS filters (sin engagement); (b) batch lookup vía `CampaignsLookupPort.find_recent_campaign_tasks_for_leads(tenant_id, lead_ids=[...], window_hours=2160)` (2160 = 90 días); (c) filter in-memory profiles cuyos leads tuvieron hit. **NO hace JOIN cross-module** (DDD boundary).
  - `q` (search) → `ILIKE '%{q}%'` sobre `full_name || primary_email || primary_phone` con `OR`. PI-3 puede migrar a `pg_trgm` si performance.
- **Ordering**: `ORDER BY last_activity_at DESC NULLS LAST, created_at DESC` (default — última actividad primero).
- **Tenant isolation**: cada query `WHERE customer_profiles.tenant_id = :tenant_id` PRIMER predicate. `leads.tenant_id = :tenant_id` también si JOIN.
- **Total count**: `SELECT COUNT(*) FROM ... WHERE ...` separado del SELECT principal (mismo WHERE, sin LIMIT/OFFSET). Performance hit aceptable para offset MVP — cursor pagination follow-up post-S4.

### 5.3 `has_campaign_engagement` — pseudocódigo

```python
async def list_contacts(self, *, tenant_id, filters, limit, offset):
    # Step 1: SELECT profiles con todos filters EXCEPTO has_campaign_engagement
    base_query = select(CustomerProfileModel).where(
        CustomerProfileModel.tenant_id == tenant_id,
        # ... todos los predicates excepto has_campaign_engagement
    )

    if filters.has_campaign_engagement is not None:
        # Sub-step: para los profiles candidate, batch lookup leads → campaign engagement
        # Para no perder count exacto cuando hay > limit candidates, primero corremos batch lookup
        # ANTES de aplicar limit/offset.
        candidate_profile_ids = (await session.execute(
            base_query.options(load_only(CustomerProfileModel.id))
        )).scalars().all()

        # Get all lead_ids for candidate profiles
        leads_by_profile = await session.execute(
            select(LeadModel.id, LeadModel.customer_id)
            .where(
                LeadModel.tenant_id == tenant_id,
                LeadModel.customer_id.in_(candidate_profile_ids),
            )
        )
        all_lead_ids = [row.id for row in leads_by_profile]

        # Batch lookup engagement (CampaignsLookupPort)
        engagement_map = await self._campaigns_lookup.find_recent_campaign_tasks_for_leads(
            tenant_id=tenant_id,
            lead_ids=all_lead_ids,
            window_hours=self._engagement_window_days * 24,
            session=session,
        )

        # profile_id → has_engagement
        engaged_profile_ids = {
            row.customer_id for row in leads_by_profile
            if row.id in engagement_map
        }

        # Filter base_query
        if filters.has_campaign_engagement is True:
            base_query = base_query.where(CustomerProfileModel.id.in_(engaged_profile_ids))
        else:  # False
            base_query = base_query.where(CustomerProfileModel.id.not_in(engaged_profile_ids))

    # Step 2: count total
    count_query = select(func.count()).select_from(base_query.subquery())
    total = (await session.execute(count_query)).scalar_one()

    # Step 3: page
    page_rows = (await session.execute(
        base_query.order_by(...).limit(limit).offset(offset)
    )).scalars().all()

    # Step 4: enrich page with channel presence + engagement bool (already computed)
    items = [self._to_list_item(p, engagement_map=engagement_map if filters.has_campaign_engagement is not None else None) for p in page_rows]

    return PaginatedResponse(items=items, total_count=total, limit=limit, offset=offset, has_more=...)
```

**Performance note 1000 clientes**: si tenant tiene >5k profiles, el batch lookup engagement cuesta 1 query subselect plus 1 `find_recent_campaign_tasks_for_leads` que ya está optimizado batch (PR-8). Acceptable MVP; cursor pagination + materialized view follow-up si telemetría >100ms p95.

## § 6 Cross-module port — `CampaignsLookupPort` ¿EXTEND?

**Decisión: NO EXTEND.** El método `find_recent_campaign_tasks_for_leads(tenant_id, lead_ids, window_hours, session)` ya existe (PR-8) y es exactamente lo que necesitamos. Window 90 días = `window_hours=2160`. Reuse direct.

## § 7 Mounting router en main.py

```python
# backend/src/main.py — agregar UNA línea import + UN bloque include_router
from src.modules.crm.api import contacts as crm_contacts
# ...
app.include_router(
    crm_contacts.router,
    prefix="/api/v1/contacts",
    tags=["crm:contacts"],
)
```

**NO modificar** routers existentes (`leads`, `cdp`, `pipeline`, `nps`, `sales`, `referral`).

## § 8 Tenant isolation invariants

1. `ContactQueryService.__init__(session)` — caller pasa AsyncSession Clerk-scoped.
2. **Cada query** del service: `WHERE customer_profiles.tenant_id = :tenant_id` (incluso `get_contact_detail` por id).
3. Endpoint dependency: `tenant_id: UUID = Depends(get_tenant_id_from_header)` (middleware existing).
4. Service NO acepta `tenant_id=None`. Nunca.
5. 404 vs 403: si profile_id existe pero tenant no match → return 404 (no leak existence). **Nota**: documentado.

## § 9 Observability

- structlog log per endpoint:
  - `contact_query_listed` con `{tenant_id, filter_count, result_count, latency_ms}` (NO incluir profile_ids — PII)
  - `contact_detail_fetched` con `{tenant_id, contact_id, found: bool}` (UUID OK; no email/phone)
- NO trace events (PR-10 read-only; sin emisión domain events).

## § 10 PII sanitization

- response_model strict (`extra="forbid"`) en cada endpoint.
- `ContactListItem`/`ContactDetail` exponen email/phone porque user-facing visualization es el use case (UI tabla muestra email — ya está en `current-state/crm.md`).
- Logs estructurados NO incluyen email/phone/telegram_id (UUID-only).
- Comentario en cada DTO con PII: justify exposure.

## § 11 Tests requeridos (TDD strict — RED → GREEN)

### 11.1 Integration `tests/modules/crm/test_contacts_api.py`

Política PR-4: **sin mocks**. Real DB fixture (`db_session_async`), tenant fixture, leads/profiles seed.

Casos (cada caso = test func separado):

1. `test_list_contacts_tenant_isolation` — tenant A NO ve profiles tenant B (cross-tenant leak gate)
2. `test_filter_lifecycle_stage_in_returns_only_matching` — `lifecycle_stage_in=[MQL,SQL]` → solo MQL+SQL
3. `test_filter_score_range_inclusive` — `score_min=40&score_max=80` → solo dentro rango (boundaries inclusive)
4. `test_filter_has_telegram_id_true` — solo profiles con Lead.telegram_id NOT NULL
5. `test_filter_has_telegram_id_false` — solo profiles SIN Lead o Lead.telegram_id NULL
6. `test_filter_has_email_true` — solo profiles con primary_email
7. `test_filter_has_phone_true` — solo profiles con primary_phone
8. `test_filter_created_after` — date filter inclusive
9. `test_filter_last_activity_before_excludes_recent` — boundary
10. `test_filter_is_inactive_true_returns_only_inactive`
11. `test_filter_source_in_returns_matching` — `source_in=["instagram_dm","landing"]`
12. `test_filter_country_in_returns_matching`
13. `test_filter_has_campaign_engagement_true_returns_engaged` — seed Lead + CampaignTask SENT 30d ago → in engagement window → returns
14. `test_filter_has_campaign_engagement_false_excludes_engaged`
15. `test_filter_has_campaign_engagement_window_boundary` — task 100 days ago (out of 90d window) → returns False
16. `test_search_q_matches_name_email_phone` — `q=juan` matchea profiles name="Juan", email="juan@x", phone="+541199juan"
17. `test_search_q_case_insensitive`
18. `test_pagination_offset_limit_correct_slice`
19. `test_pagination_total_count_consistent`
20. `test_pagination_has_more_flag`
21. `test_pagination_limit_max_100_validates`
22. `test_pagination_limit_zero_rejects` — Pydantic validator
23. `test_get_contact_detail_returns_full_schema` — assert all ContactDetail fields populated
24. `test_get_contact_detail_includes_identities_list` — multi-channel identities serialized
25. `test_get_contact_detail_404_when_other_tenant`
26. `test_get_contact_detail_404_when_nonexistent_uuid`
27. `test_journey_endpoint_returns_501_with_retry_after` — header check
28. `test_campaigns_endpoint_returns_501_with_retry_after`
29. `test_filter_schema_endpoint_returns_canonical_fields_list` — verify version "1.0" + fields list matches CANONICAL_FILTER_FIELDS
30. `test_response_model_extra_forbid_rejects_unknown_field` — Pydantic strict
31. `test_concurrent_filters_combine_correctly` — `lifecycle_stage_in=[MQL]&score_min=50&has_telegram_id=true` AND combination

### 11.2 Arch test `tests/architecture/test_contacts_filter_params_forward_compat.py`

```python
"""Forward-compat invariant: ContactFilterParams MUST contain ALL canonical filters.

Ratchet shrink-only: futuro adds OK; remove FAIL test. Origen: PR-10 PI-1 S4.
Cuando PI-3 agrega filter nuevo → DEBE actualizar CANONICAL_FILTER_FIELDS aquí.
"""
from src.modules.crm.api.dto.contact_filters import ContactFilterParams

CANONICAL_FILTER_FIELDS: frozenset[str] = frozenset({
    "lifecycle_stage_in", "score_min", "score_max",
    "source_in",
    "has_email", "has_phone", "has_telegram_id", "has_whatsapp_id",
    "has_instagram_id", "has_tiktok_id",
    "created_after", "created_before", "last_activity_after", "last_activity_before",
    "is_inactive",
    "has_campaign_engagement",
    "country_in",
    "q",
})


def test_contact_filter_params_includes_all_canonical_fields():
    actual = frozenset(ContactFilterParams.model_fields.keys())
    missing = CANONICAL_FILTER_FIELDS - actual
    assert not missing, (
        f"ContactFilterParams MISSING canonical fields: {missing}. "
        f"Forward-compat invariant violated. PR-10 PI-1 S4."
    )


def test_contact_filter_params_no_extra_undocumented_fields():
    """Si agregás field nuevo → DEBÉS sumarlo a CANONICAL_FILTER_FIELDS aquí."""
    actual = frozenset(ContactFilterParams.model_fields.keys())
    extra = actual - CANONICAL_FILTER_FIELDS
    assert not extra, (
        f"ContactFilterParams has UNDOCUMENTED fields: {extra}. "
        f"Update CANONICAL_FILTER_FIELDS in this test."
    )
```

## § 12 OpenAPI documentation

- Cada endpoint con `description=` extenso (Spanish neutro)
- 501 stubs con `responses={501: {"model": DeferredEndpointResponse, "headers": {"Retry-After": {"schema": {"type": "string"}, "description": "PI-3"}}}}`
- `tags=["crm:contacts"]` consistente

## § 13 Quality gates expectations

- Ruff: 0 errors. Imports ordered. Line 120 max.
- Mypy strict: type-correct. No `# type: ignore` en código nuevo.
- Coverage: `crm` module ≥ existing baseline. PR-10 nuevo code expected ≥80% (integration tests cubren casi todo).
- Arch tests: forward-compat verde. NO new domain framework imports. NO cross-module imports excepto port.
- Pip-audit: no new vulnerable deps (PR-10 NO agrega deps).
- jscpd: NO duplication >5 líneas vs existing routers.

## § 14 Migrations

**0 migrations.** PR-10 NO altera schema. Solo queries sobre tablas existentes (`customer_profiles`, `leads`, `customer_identities`).

Si telemetría post-merge muestra slow query >100ms p95 sobre `customer_profiles.last_activity_at` con scan: PR follow-up agrega índice compuesto idempotente. NO en PR-10.

## § 15 Research notes

- FastAPI canonical: https://fastapi.tiangolo.com/ (accessed 2026-04-30) — `Query()` Pydantic, `responses=` para multi-status docs, `Depends(get_tenant_id_from_header)` middleware existing.
- Pydantic v2 canonical: https://docs.pydantic.dev/latest/ (accessed 2026-04-30) — `ConfigDict(extra="forbid")` strict mode.
- SQLA 2.0 async: `select(...).where(...).order_by(...).limit().offset()` modern syntax (existing codebase pattern).
- Decisión EXTEND vs NEW: criterio PR-3 PI-2 audit failure (no parallel layers); aplicado aquí = NEW endpoint group justificado por scope semántico distinto + zero breaking changes.

## § 16 Open questions for PM

**Ninguna.** Todas las decisiones cerradas en este CONTRACT:

| Decisión | Resuelta | Resolución |
|---|---|---|
| EXTEND `/leads` vs NEW `/contacts` | ✅ | NEW (scope semántico distinto + cero breaking changes) |
| Source table CustomerProfile vs Lead | ✅ | CustomerProfileModel SOT + LEFT JOIN Lead opcional |
| Cursor vs offset pagination | ✅ | Offset MVP. Cursor follow-up si telemetría >100ms p95 |
| `has_campaign_engagement` query strategy | ✅ | 2-step: SELECT profiles con otros filters → batch lookup CampaignsLookupPort → filter in-memory |
| 501 stubs canonical schema | ✅ | `DeferredEndpointResponse` + `Retry-After: PI-3` |
| Soft delete `deleted_at` | ✅ | NO existe en customer_profiles/leads — N/A. PI futuro si se agrega tabla con soft delete |
| FilterParams strict scope | ✅ | 18 fields canonical (CANONICAL_FILTER_FIELDS) — ratchet shrink-only |
| `has_email` strategy (primary_email vs identity table) | ✅ | `primary_email IS NOT NULL` (rápido, índice). PI-3 puede expandir si telemetría dice |

---

<!-- @pm: CONTRACT.md ready. Surface mapping: business (BE-only) → nicolify-backend (Sonnet) + nicolify-backend-auditor (Opus). EXTEND-vs-NEW decision: NEW /contacts endpoint group (justificado scope semántico + zero breaking). Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-10 architect done" para review. -->
