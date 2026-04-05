# Plan: Cross-Module Import Violations — Waves 4–7

> **Fecha:** 2026-04-05
> **Rama:** `refactor/eliminate-legacy-allowlists`
> **Estado:** Waves 0–3 completados. 59 violaciones restantes.

## Resumen de progreso

| Wave | Qué hizo | Violaciones eliminadas | Commit |
|------|----------|----------------------|--------|
| 0A | Eliminó shims de sales_agent (channel_model, channel_repository, __init__.py) | -5 | `46f6d2e` |
| 0B | Movió domain events (SaleCompletedEvent, etc.) + CHANNEL_TYPE_TO_CAPTURE_SLUG a shared/domain/events.py | 0 (infra) | `46f6d2e` |
| 1 | Desacopló brand de copilot: BrandExtractionService directo, PromptLoader→shared, style_analyzer→brand | -4 | `eaa0678` |
| 2 | Creó shared/domain/ports.py (ConnectionPort, OfferReadPort, ProductMappingPort). Eliminó ghost entries offer→crm. LandingPageConfig→dict | -7 | `b81791a` |
| 3 | crm/landing→offer: raw SQL para reads cross-module | -2 | `488f38a` |
| **Total** | | **-18** | **77→59** |

## Infraestructura creada (disponible para waves posteriores)

| Archivo | Contenido | Creado en |
|---------|-----------|-----------|
| `shared/domain/ports.py` | ConnectionPort, ConnectionCredentials, OfferReadPort, OfferReadDTO, ProductMappingPort | Wave 2 |
| `shared/domain/events.py` | DomainEvent, EventBus + SaleCompletedEvent, ChurnEvent, LeadCapturedEvent, AppointmentEvent, CHANNEL_TYPE_TO_CAPTURE_SLUG | Wave 0B |
| `shared/infrastructure/prompts/base.py` | PromptLoader + prompt_loader singleton | Wave 1 |
| `brand/application/agents/style_analyzer/` | LangGraph movido de copilot (sin trace_node dependency) | Wave 1 |
| `analytics/domain/ports.py` | Re-exporta desde shared/domain/ports.py | Wave 2 |
| `crm/domain/events.py` | Re-exporta desde shared/domain/events.py | Wave 0B |

## Violaciones diferidas de waves anteriores

Estas 2 violaciones NO se eliminaron en sus waves originales por complejidad:

### `offer -> copilot | offer/api/offer_ai.py` (de Wave 2)

**Import:** `CopilotOfferPsychologyService` — servicio que genera insights psicológicos para ofertas.

**Por qué no se resolvió:** El service depende de `AvatarRepository` (brand). Moverlo a offer crearía `offer → brand`. Crear un port para avatar data añade complejidad sin reducir violaciones netas.

**Estrategia recomendada:** Resolver en Wave 6 junto con sales_agent→brand, creando un `AvatarReadPort` compartido en `shared/domain/ports.py`.

### `offer -> crm | offer/api/product_mappings.py` (de Wave 2)

**Import:** `JourneyEventModel`, `SaleModel` — ORM models para SQL JOINs en endpoints de product mapping.

**Por qué no se resolvió:** Mismos ORM models que analytics usa (16 violaciones). Se resuelve naturalmente en Wave 7 cuando CRM models migran a shared.

---

## Allowlist actual (59 entradas)

```python
KNOWN_CROSS_MODULE_IMPORTS: set[str] = {
    # --- analytics (28) ---
    "analytics -> connections | analytics/api/metrics.py",
    "analytics -> connections | analytics/application/services/etl_service.py",
    "analytics -> connections | analytics/application/services/metrics_service.py",
    "analytics -> connections | analytics/infrastructure/providers/google_ads_provider.py",
    "analytics -> connections | analytics/infrastructure/providers/google_analytics_provider.py",
    "analytics -> connections | analytics/infrastructure/providers/search_console_provider.py",
    "analytics -> connections | analytics/infrastructure/providers/tiktok_provider.py",
    "analytics -> connections | analytics/infrastructure/providers/youtube_provider.py",
    "analytics -> connections | analytics/workers/manychat_sync.py",
    "analytics -> connections | analytics/workers/tasks.py",
    "analytics -> crm | analytics/application/services/etl_service.py",
    "analytics -> crm | analytics/application/services/ig_dm_sync_service.py",
    "analytics -> crm | analytics/application/services/metrics_service.py",
    "analytics -> crm | analytics/application/services/stage_services/summary_stage.py",
    "analytics -> crm | analytics/infrastructure/engines/rfm.py",
    "analytics -> crm | analytics/infrastructure/engines/scoring.py",
    "analytics -> crm | analytics/infrastructure/providers/crm_internal_provider.py",
    "analytics -> crm | analytics/infrastructure/repositories/adoption_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/capture_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/evangelization_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/expansion_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/nurture_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/opportunity_repository.py",
    "analytics -> crm | analytics/infrastructure/repositories/sales_metrics_repository.py",
    "analytics -> crm | analytics/workers/manychat_sync.py",
    "analytics -> crm | analytics/workers/tasks.py",
    "analytics -> offer | analytics/api/metrics.py",
    "analytics -> offer | analytics/application/services/etl_service.py",
    # --- connections (11) ---
    "connections -> analytics | connections/api/channel_info.py",
    "connections -> analytics | connections/api/marketing_webhooks.py",
    "connections -> analytics | connections/application/services/connection_port_impl.py",
    "connections -> crm | connections/api/calendar.py",
    "connections -> crm | connections/api/marketing_webhooks.py",
    "connections -> offer | connections/api/marketing_webhooks.py",
    "connections -> sales_agent | connections/api/meta.py",
    "connections -> sales_agent | connections/api/telegram.py",
    "connections -> sales_agent | connections/api/webhook.py",
    "connections -> sales_agent | connections/api/whatsapp.py",
    "connections -> scheduling | connections/api/calendar.py",
    # --- offer (2, deferred) ---
    "offer -> copilot | offer/api/offer_ai.py",
    "offer -> crm | offer/api/product_mappings.py",
    # --- sales_agent (14) ---
    "sales_agent -> brand | sales_agent/application/services/knowledge_builder.py",
    "sales_agent -> connections | sales_agent/application/orchestrator/chat.py",
    "sales_agent -> connections | sales_agent/application/services/channel_resolver.py",
    "sales_agent -> connections | sales_agent/application/services/channel_service.py",
    "sales_agent -> crm | sales_agent/api/audit.py",
    "sales_agent -> crm | sales_agent/api/closer_studio.py",
    "sales_agent -> crm | sales_agent/application/orchestrator/chat.py",
    "sales_agent -> crm | sales_agent/application/services/channel_resolver.py",
    "sales_agent -> crm | sales_agent/application/services/closer_studio_service.py",
    "sales_agent -> crm | sales_agent/infrastructure/memory/audit_repository.py",
    "sales_agent -> offer | sales_agent/application/services/knowledge_builder.py",
    "sales_agent -> offer | sales_agent/infrastructure/db/repositories/business_repository.py",
    "sales_agent -> scheduling | sales_agent/api/dto/public_links.py",
    "sales_agent -> scheduling | sales_agent/application/agents/sales/tools.py",
    # --- scheduling (4) ---
    "scheduling -> connections | scheduling/application/services/availability_service.py",
    "scheduling -> crm | scheduling/api/agenda.py",
    "scheduling -> crm | scheduling/application/services/availability_service.py",
    "scheduling -> tenant_domains | scheduling/application/booking_url.py",
}
```

---

## Wave 4: connections (11 violaciones) — DIFÍCIL

### 4A: connections → sales_agent (4 violaciones) — CRÍTICO

**Archivos:**
- `connections/api/meta.py`
- `connections/api/telegram.py`
- `connections/api/webhook.py`
- `connections/api/whatsapp.py`

**Import:** Todos importan `ChatOrchestrator` de `sales_agent.application.orchestrator.chat` para rutear mensajes entrantes al agente de ventas.

**Estrategia: InboundMessageHandlerPort**

1. Agregar a `shared/domain/ports.py`:
```python
class InboundMessageHandlerPort(ABC):
    @abstractmethod
    async def handle_inbound_message(
        self, tenant_id: UUID, channel_type: str,
        sender_id: str, message_text: str,
        metadata: dict
    ) -> str | None:
        """Process inbound message. Returns optional response text."""
```

2. Crear `sales_agent/application/services/inbound_handler.py` que implementa el port wrapeando `ChatOrchestrator`.

3. Crear `shared/application/service_locator.py`:
```python
class ServiceLocator:
    _registry: dict[str, Any] = {}

    @classmethod
    def register(cls, name: str, instance: Any) -> None:
        cls._registry[name] = instance

    @classmethod
    def get(cls, name: str) -> Any:
        return cls._registry[name]
```

4. En `main.py` (app startup), registrar:
```python
from sales_agent.application.services.inbound_handler import SalesAgentInboundHandler
ServiceLocator.register("inbound_handler", SalesAgentInboundHandler())
```

5. En cada webhook file: `handler = ServiceLocator.get("inbound_handler")`.

**Nota:** `ChatOrchestrator` es singleton module-level. El ServiceLocator replica este patrón.

**Riesgo:** Los webhooks pasan datos específicos del canal (page_id, ig_id, etc.) además del mensaje. Verificar que el port abstrae suficiente contexto.

### 4B: connections → analytics (3 violaciones)

**Archivos e imports:**
- `channel_info.py`: `ExtractionRunRepository`, `OfficialMetricModel` — muestra info del último ETL y conteo de métricas
- `marketing_webhooks.py`: `ManyChatMetricsPromoter` — promueve métricas de ManyChat
- `connection_port_impl.py`: `ConnectionPort` ABC de analytics → **YA RESUELTO** si se actualiza a importar de `shared/domain/ports.py` en vez de `analytics/domain/ports.py`

**Estrategia:**

1. **connection_port_impl.py** (1 violación): Cambiar import de `analytics.domain.ports.ConnectionPort` → `shared.domain.ports.ConnectionPort`. Win fácil.

2. **channel_info.py** (1 violación): Crear `AnalyticsReadPort` en `shared/domain/ports.py`:
```python
class AnalyticsReadPort(ABC):
    @abstractmethod
    async def get_last_extraction_status(self, tenant_id: UUID, channel_type: str) -> dict | None: ...
    @abstractmethod
    async def get_metrics_count(self, tenant_id: UUID, channel_type: str) -> int: ...
```
Analytics implementa. O usar raw SQL (más simple, como Wave 3).

3. **marketing_webhooks.py → ManyChatMetricsPromoter** (1 violación): EventBus — webhook emite `ManyChatSyncEvent`, analytics handler lo procesa. O mover ManyChatMetricsPromoter a shared.

### 4C: connections → crm (2 violaciones)

**Archivos:**
- `calendar.py`: importa `Lead` domain model para booking links personalizados
- `marketing_webhooks.py`: importa ~15 cosas de crm (CustomerService, LifecycleService, JourneyEventModel, etc.)

**Estrategia calendar.py:** Recibir `lead_name: str` como parámetro o usar raw SQL para el nombre del lead.

**Estrategia marketing_webhooks.py:** REFACTORING MAYOR.
- Los webhook handlers (Shopify, Mailerlite, ManyChat) tienen ~600 líneas de lógica CRM embebida
- **Event-driven:** Webhook parsea payload → emite domain events (ShopifyOrderEvent, MailerliteSubscriberEvent) → CRM event handlers procesan
- Esta es la pieza más compleja de todo el plan
- **Sugerencia:** Hacer este refactoring como un sub-wave dedicado con su propio PR

### 4D: connections → offer + scheduling (2 violaciones)

- `marketing_webhooks.py → offer`: `ExternalProductMappingRepository` — resolver product_id → offer_id. Incluir offer_id resuelto en el event payload.
- `calendar.py → scheduling`: DTOs de scheduling + `AvailabilityService` + `BookingLink` model. **Mover** `calendar.py` a `scheduling/api/external_calendar.py` — la lógica es 100% de scheduling.

### Orden recomendado dentro de Wave 4:
1. `connection_port_impl.py` → shared import (1 min)
2. `calendar.py` → mover a scheduling o raw SQL (30 min)
3. Los 4 webhook files → InboundMessageHandlerPort (2h)
4. `channel_info.py` → AnalyticsReadPort o raw SQL (30 min)
5. `marketing_webhooks.py` → event-driven refactoring (4-6h, puede ser wave separado)

**Eliminará:** 11 entradas connections → *.

---

## Wave 5: scheduling (4 violaciones) — MEDIO

### 5A: scheduling → connections (1 violación)

**Archivo:** `availability_service.py`
**Imports:** `GmailAdapter`, `GoogleCalendarAdapter`, `ChannelConnectionModel`

**Estrategia:** Crear ports en `scheduling/domain/ports.py`:
```python
class CalendarPort(ABC):
    async def get_available_slots(self, credentials: dict, date_range: tuple) -> list[dict]: ...
    async def create_event(self, credentials: dict, event_data: dict) -> dict: ...

class EmailPort(ABC):
    async def send_confirmation(self, credentials: dict, to: str, subject: str, body: str): ...

class ChannelCredentialsPort(ABC):
    async def get_credentials(self, tenant_id: UUID, channel_type: str) -> dict | None: ...
```

`connections` implementa. `availability_service.py` recibe ports via constructor.

**Alternativa simple:** `ChannelCredentialsPort` ya existe como `ConnectionPort` en `shared/domain/ports.py`. Si `availability_service.py` solo necesita credenciales, usar `ConnectionPort` directamente. Para los adapters (GmailAdapter, GoogleCalendarAdapter), crear wrappers que usen credenciales sin importar de connections.

### 5B: scheduling → crm (2 violaciones)

**Archivos:**
- `agenda.py`: importa `LeadModel` para enriquecer appointments con nombre del lead
- `availability_service.py`: importa `Lead` domain model

**Estrategia:** Raw SQL para obtener el nombre del lead (mismo patrón que Wave 3):
```python
row = db.execute(sa_text("SELECT name FROM leads WHERE id = :id AND tenant_id = :tid"), {...}).mappings().first()
```

O denormalizar `lead_name` en `AppointmentModel` (copiar al crear el appointment).

### 5C: scheduling → tenant_domains (1 violación)

**Archivo:** `booking_url.py`
**Import:** `DomainStatus`, `DomainRepositoryImpl` para construir la URL de booking con custom domain.

**Estrategia:** Port `TenantUrlPort` en `shared/domain/ports.py`:
```python
class TenantUrlPort(ABC):
    @abstractmethod
    async def get_primary_url(self, tenant_id: UUID) -> str: ...
```
`tenant_domains` implementa. Retorna custom domain o default.

**Alternativa simple:** Raw SQL:
```python
row = db.execute(sa_text("SELECT domain FROM tenant_domains WHERE tenant_id = :tid AND status = 'active'"), {...})
```

**Eliminará:** 4 entradas scheduling → *.

---

## Wave 6: sales_agent (14 violaciones) — DIFÍCIL

### 6A: sales_agent → brand + offer (3 violaciones)

**Archivos:**
- `knowledge_builder.py` → brand: `AvatarRepository`, `BrandRepository`
- `knowledge_builder.py` → offer: `OfferRepository` (o ProductModel)
- `business_repository.py` → offer: `ProductModel`

**Estrategia: TenantKnowledgePort**

Crear `sales_agent/domain/ports.py`:
```python
class TenantKnowledgePort(ABC):
    @abstractmethod
    async def get_brand_context(self, tenant_id: UUID) -> dict: ...
    @abstractmethod
    async def get_offer_catalog(self, tenant_id: UUID) -> list[dict]: ...
    @abstractmethod
    async def get_avatar_context(self, tenant_id: UUID) -> dict | None: ...
```

Implementar en `brand/application/services/` y `offer/application/services/`. O un adapter unificado en `shared/application/`.

`knowledge_builder.py` recibe el port via constructor. El wiring se concentra en un archivo de startup.

Para `business_repository.py` → offer: raw SQL o port.

### 6B: sales_agent → connections (3 violaciones)

**Archivos:**
- `chat.py`: `TelegramChannel`, `ChannelConnectionModel`
- `channel_resolver.py`: `ChannelConnectionModel`, lazy imports de `TelegramChannel`, `WhatsAppChannel`, etc.
- `channel_service.py`: `ChannelConnection` domain model

**Estrategia: OutboundChannelPort**

```python
class OutboundChannelPort(ABC):
    @abstractmethod
    async def send_message(self, tenant_id: UUID, channel_type: str, recipient_id: str, message: str) -> bool: ...
    @abstractmethod
    async def get_active_connection(self, tenant_id: UUID, channel_type: str) -> dict | None: ...
```

`connections` implementa. Sales agent usa port sin conocer adapters concretos.

Para `ChannelConnectionModel` queries: usar `ConnectionPort.get_credentials()` de `shared/domain/ports.py`.

### 6C: sales_agent → crm (6 violaciones)

**Archivos e imports:**
- `audit.py`: `LeadModel` → raw SQL
- `closer_studio.py`: `LeadModel` → raw SQL
- `chat.py`: `IdentityService`, `CustomerRepository`, `LeadRepository` → CrmLookupPort
- `channel_resolver.py`: `LeadModel` → raw SQL o TYPE_CHECKING
- `closer_studio_service.py`: `CustomerProfileModel`, `LeadModel` → CrmLookupPort
- `audit_repository.py`: `LeadModel` → raw SQL JOINs

**Estrategia:** Combinar CrmLookupPort + raw SQL:

```python
class CrmLookupPort(ABC):
    @abstractmethod
    async def resolve_or_create_customer(self, tenant_id: UUID, identity_type: str, identity_value: str) -> UUID: ...
    @abstractmethod
    async def get_lead_by_channel(self, tenant_id: UUID, channel_type: str, channel_id: str) -> dict | None: ...
```

Para reads simples (nombre del lead, lista de leads): raw SQL como Wave 3.

### 6D: sales_agent → scheduling (2 violaciones)

- `public_links.py`: importa `EventType` schema → mover a `shared/domain/schemas.py`
- `tools.py`: importa `AvailabilityService` → crear `SchedulingPort`:
```python
class SchedulingPort(ABC):
    @abstractmethod
    async def get_available_slots(self, tenant_id: UUID, event_type_id: str) -> list[dict]: ...
    @abstractmethod
    async def book_appointment(self, tenant_id: UUID, slot: dict, lead_data: dict) -> dict: ...
```

**Eliminará:** 14 entradas sales_agent → *.

### Nota sobre offer → copilot (diferido de Wave 2)

Si se crea `AvatarReadPort` en Wave 6A, se puede resolver `offer/api/offer_ai.py` moviendo `CopilotOfferPsychologyService` a offer con el port.

---

## Wave 7: analytics (28 violaciones) — MÁS DIFÍCIL

### 7A: analytics → offer (2 violaciones)

**Archivos:** `metrics.py`, `etl_service.py`
**Import:** `OfferReadPortImpl`, `ExternalProductMappingRepository`

**Estrategia:** Ya resuelto conceptualmente — los port ABCs están en shared. Falta actualizar el wiring. Crear `analytics/api/wiring.py` que centraliza imports de port impls:

```python
# analytics/api/wiring.py
def get_offer_port(db) -> OfferReadPort:
    from src.modules.offer.application.services.offer_read_port_impl import OfferReadPortImpl
    return OfferReadPortImpl(db)
```

La violación se concentra en UN solo archivo de wiring. O usar ServiceLocator de Wave 4.

### 7B: analytics → connections (10 violaciones)

**Categoría 1: Channel adapters (5 violaciones)**
Providers ETL importan adapters concretos: `GoogleAdsAdapter`, `GoogleAnalyticsAdapter`, `SearchConsoleAdapter`, `TikTokAdapter`, `YouTubeAnalyticsAdapter`.

**Estrategia:** Mover channel adapters a `shared/infrastructure/channels/`:
- `connections/infrastructure/channels/google_ads.py` → `shared/infrastructure/channels/google_ads.py`
- Idem para google_analytics, search_console, tiktok, youtube_analytics
- `connections` re-importa desde shared

**Nota:** `shared/infrastructure/channels/base.py` ya existe con la clase base `ChannelAdapter`.

**Categoría 2: ConnectionPortImpl (3 violaciones)**
`metrics.py`, `etl_service.py`, `tasks.py` importan `ConnectionPortImpl`.

**Estrategia:** Mismo que 7A — concentrar en wiring file o ServiceLocator.

**Categoría 3: ManyChat/Mailerlite connectors (2 violaciones)**
`manychat_sync.py`, `tasks.py` importan `ManyChatConnector`, `MailerliteConnector`, `ChannelConnectionModel`.

**Estrategia:** Mover marketing connectors a `shared/infrastructure/channels/` junto con los otros adapters.

### 7C: analytics → crm (16 violaciones) — EL MÁS DIFÍCIL

**ORM Models importados:** CustomerProfileModel (12+), JourneyEventModel (5+), SaleModel (4+), LifecycleTransitionModel (4+), NpsScoreModel, ReferralCodeModel, LeadModel.

**Services importados:** CustomerService, LifecycleService, InactivityService, IdentityService, IgProfileEnricher, CustomerRepository, LeadRepository.

**Estrategia: Shared CRM Models**

1. Mover ORM models "publicados" a `shared/infrastructure/models/crm_models.py`:
```python
# Los modelos se mueven a shared. CRM re-exporta para backward compat.
# shared/infrastructure/models/crm_models.py
class CustomerProfileModel(Base): ...
class JourneyEventModel(Base): ...
class SaleModel(Base): ...
class LifecycleTransitionModel(Base): ...
```

2. CRM re-exporta:
```python
# crm/infrastructure/models/customer_model.py
from src.shared.infrastructure.models.crm_models import CustomerProfileModel  # noqa: F401
```

**CUIDADO con SQLAlchemy:** No se pueden tener 2 clases mapeando la misma tabla (`extend_existing` es frágil). Los modelos deben vivir en UN solo lugar y re-exportarse.

3. Para services (CustomerService, etc.), crear ports en `shared/domain/ports.py`:
```python
class CrmCustomerPort(ABC):
    async def resolve_or_create(self, tenant_id, identity_type, value, display_name) -> UUID: ...
    async def update_lifecycle(self, profile_id, new_stage) -> None: ...

class CrmLeadPort(ABC):
    async def get_lead(self, tenant_id, lead_id) -> dict | None: ...
    async def get_active_leads(self, tenant_id) -> list[dict]: ...
```

4. CRM implementa los ports. Analytics + sales_agent + offer los consumen.

**Esto resuelve también:**
- `offer -> crm | offer/api/product_mappings.py` (diferido de Wave 2)
- Varias violaciones de sales_agent → crm (Wave 6C)

**Eliminará:** 28 entradas analytics → * + las 2 diferidas de offer.

---

## Orden de ejecución recomendado

```
Wave 5 (scheduling, 4 viol.)     ← más fácil, independiente
  ↓
Wave 4A-4B (connections parcial) ← eliminar los wins fáciles primero
  ↓
Wave 6 (sales_agent, 14 viol.)   ← depende parcialmente de Wave 7C
  ↓
Wave 7C (analytics→crm, 16)      ← shared CRM models, desbloquea todo
  ↓
Wave 7B (analytics→connections)   ← mover adapters a shared
  ↓
Wave 7A (analytics→offer)        ← wiring
  ↓
Wave 4C-4D (connections→crm)     ← marketing_webhooks event-driven (lo más difícil)
```

**Razón del reorden:** Wave 7C (shared CRM models) desbloquea violaciones en sales_agent, offer, y el propio analytics. Hacerlo antes de terminar Wave 4C (marketing_webhooks) permite que ese mega-refactoring use los shared models directamente.

## Verificación por wave

```bash
# Lint
cd backend && .venv/bin/ruff check src/ --no-cache

# Arch tests
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short

# Module tests (ajustar al módulo)
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/{module}/ -x -q --tb=short"

# Full suite (al final de cada wave)
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest -x -q --tb=short"
```

## Objetivo final

```python
KNOWN_CROSS_MODULE_IMPORTS: set[str] = set()  # vacío
```

Verificar:
```bash
grep -A2 "KNOWN_CROSS_MODULE_IMPORTS" backend/tests/architecture/test_ddd_boundaries.py
```
