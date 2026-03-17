# 12 — CRM Integration

## Vision General

El Sales Agent se integra con el CRM via el patron **CDP (Customer Data Platform)**. Cuando un usuario escribe por primera vez, el sistema crea un perfil unificado en el CDP y emite eventos de dominio para que otros modulos reaccionen (analytics, pipeline, etc.).

```
         Telegram msg (user_id="123456")
                │
                ▼
     IdentityService.get_or_create_customer()
                │
                ├─── Busca: customer_identities
                │      WHERE identity_type='telegram'
                │      AND identity_value='123456'
                │      AND tenant_id=<UUID>
                │
                ├─── FOUND → return (profile, False)
                │
                └─── NOT FOUND → CREATE:
                       ├── customer_profiles (full_name, traits)
                       ├── customer_identities (type, value)
                       └── emit LeadCapturedEvent
                              │
                              ▼
                         EventBus._dispatch()
                              │
                              ├── analytics handler (increment capture metric)
                              └── pipeline handler (create pipeline entry)
```

---

## 1. IdentityService

**Archivo:** `backend/src/modules/crm/application/services/identity_service.py` (L7-45)

```python
class IdentityService:
    def __init__(self, customer_repository: CustomerRepository):
        self.customer_repository = customer_repository

    def get_or_create_customer(
        self,
        tenant_id: UUID,
        identity_type: IdentityType,
        identity_value: str,
        profile_data: Dict[str, Any],
        lead_source: Optional[str] = None,
        lead_source_detail: Optional[str] = None,
    ) -> tuple[CustomerProfile, bool]:
        """Returns (profile, was_created)."""

        existing = self.customer_repository.find_by_identity(
            identity_value=identity_value,
            identity_type=identity_type,
            tenant_id=tenant_id
        )

        if existing:
            return existing, False

        new_customer = self.customer_repository.create_with_identity(
            tenant_id=tenant_id,
            identity_type=identity_type,
            identity_value=identity_value,
            profile_data=profile_data,
            lead_source=lead_source,
            lead_source_detail=lead_source_detail,
        )
        return new_customer, True
```

### IdentityType Enum
```python
class IdentityType(str, Enum):
    TELEGRAM = "telegram"
    WHATSAPP = "whatsapp"
    INSTAGRAM = "instagram"
    TIKTOK = "tiktok"
    EMAIL = "email"
    PHONE = "phone"
    EXTERNAL_ID = "external_id"
```

### Flujo de Resolucion de Identidad

```
Channel Type → IdentityType mapping (chat.py:244-248):
  "telegram"  → IdentityType.TELEGRAM
  "whatsapp"  → IdentityType.WHATSAPP
  "instagram" → IdentityType.INSTAGRAM
  "api"       → IdentityType.EXTERNAL_ID  (fallback)

Identity resolution query:
  SELECT cp.* FROM customer_profiles cp
  JOIN customer_identities ci ON ci.profile_id = cp.id
  WHERE ci.identity_type = 'telegram'
    AND ci.identity_value = '123456789'
    AND ci.tenant_id = '<UUID>'
```

**Multicanal unificado:** Un mismo cliente que escribe por Telegram y luego por WhatsApp se puede unificar si comparte alguna identidad (email, telefono). El CDP soporta multiples identidades por perfil.

---

## 2. CustomerRepository

**Archivo:** `backend/src/modules/crm/infrastructure/repositories/customer_repository.py`

### find_by_identity
```python
def find_by_identity(self, identity_value: str, identity_type: IdentityType, tenant_id: UUID):
    """Find customer profile by identity (with tenant isolation)."""
    return self.db.query(CustomerProfileModel).join(
        CustomerIdentityModel
    ).filter(
        CustomerIdentityModel.identity_type == identity_type.value,
        CustomerIdentityModel.identity_value == identity_value,
        CustomerIdentityModel.tenant_id == tenant_id,
    ).first()
```

### create_with_identity
```python
def create_with_identity(self, tenant_id, identity_type, identity_value, profile_data, lead_source, lead_source_detail):
    """Create new customer profile + identity record."""
    profile = CustomerProfileModel(
        tenant_id=tenant_id,
        full_name=f"{profile_data.get('first_name', '')} {profile_data.get('last_name', '')}".strip(),
        traits=profile_data.get("traits", {}),
        lead_source=lead_source,
        lead_source_detail=lead_source_detail,
    )
    self.db.add(profile)
    self.db.flush()

    identity = CustomerIdentityModel(
        profile_id=profile.id,
        tenant_id=tenant_id,
        identity_type=identity_type.value,
        identity_value=identity_value,
    )
    self.db.add(identity)
    self.db.commit()
    return profile
```

---

## 3. Domain Events

### EventBus (Shared Infrastructure)

**Archivo:** `backend/src/shared/domain/events.py` (L32-78)

```python
class EventBus:
    _handlers: Dict[str, List[Callable]] = {}  # Class-level, singleton

    @classmethod
    def subscribe(cls, event_name: str, handler: Callable):
        cls._handlers.setdefault(event_name, []).append(handler)

    @classmethod
    def publish(cls, event: DomainEvent, session=None):
        if session is not None:
            # Deferred: dispatch after commit
            @sa_event.listens_for(session, "after_commit", once=True)
            def _on_commit(sess):
                cls._dispatch(event)
        else:
            cls._dispatch(event)

    @classmethod
    def _dispatch(cls, event: DomainEvent):
        for handler in cls._handlers.get(event.event_name, []):
            try:
                handler(event)
            except Exception:
                logger.exception("Event handler failed")
```

**Decisiones de diseno:**
- **In-process:** No usa message broker externo (Kafka, RabbitMQ). Es simple y suficiente para el volumen actual.
- **After-commit:** Los eventos se despachan despues del `session.commit()`. Esto asegura que los datos referenciados existen en la BD cuando los handlers los consulten.
- **Exception isolation:** Si un handler falla, los demas siguen ejecutandose. El error se loguea pero no se propaga al publisher.

### LeadCapturedEvent

**Archivo:** `backend/src/modules/crm/domain/events.py` (L96-125)

```python
@dataclass
class LeadCapturedEvent(DomainEvent):
    """Emitted by Sales Agent when a new customer profile is created."""

    @classmethod
    def create(cls, tenant_id, profile_id, channel_slug, extracted_field, source_channel_type):
        return cls(
            event_name="lead_captured",
            tenant_id=tenant_id,
            payload={
                "profile_id": str(profile_id),
                "channel_slug": channel_slug,           # "ig-dm", "telegram-dm", etc.
                "extracted_field": extracted_field,       # "external_id"
                "source_channel_type": source_channel_type,  # "telegram", "instagram"
            },
        )
```

**Emision en chat.py (L268-279):**
```python
if was_created and tenant_uuid:
    EventBus.publish(
        LeadCapturedEvent.create(
            tenant_id=tenant_uuid,
            profile_id=customer.id,
            channel_slug=capture_slug,
            extracted_field="external_id",
            source_channel_type=channel_type,
        ),
        session=db,
    )
```

### Channel Slug Mapping (L86-92)

```python
CHANNEL_TYPE_TO_CAPTURE_SLUG = {
    "instagram": "ig-dm",
    "facebook": "fb-messenger",
    "tiktok": "tiktok-dm",
    "whatsapp": "whatsapp-inbound",
    "telegram": "telegram-dm",
}
```

Los slugs se usan en el modulo de Analytics para agregar capturas por canal en el Bowtie Funnel.

### Otros Eventos CRM

| Event | Emitido Por | Proposito |
|-------|-------------|-----------|
| `LeadCapturedEvent` | ChatOrchestrator | Nuevo perfil creado via canal |
| `SaleCompletedEvent` | SaleService | Venta completada (CONVERSION/EXPANSION) |
| `ChurnEvent` | Shopify/Stripe webhooks | Cancelacion de suscripcion |
| `AppointmentEvent` | Scheduling module | Cita agendada/completada/no-show |

---

## 4. Lead & LeadMetrics Repository

**Archivo:** `backend/src/modules/crm/infrastructure/repositories/lead_metrics_repository.py`

### Metodos usados por el Chat Flow

```python
class LeadRepository:
    def get_active_lead(self, customer_id: UUID) -> Optional[LeadModel]:
        """Get the most recent active lead for a customer."""
        return self.db.query(LeadModel).filter(
            LeadModel.customer_id == customer_id,
            LeadModel.is_blacklisted == False,
        ).order_by(LeadModel.created_at.desc()).first()

    def create_lead(self, customer_id, channel, channel_user_id) -> LeadModel:
        """Create a new lead linked to a customer profile."""
        lead = LeadModel(
            customer_id=customer_id,
            **{f"{channel}_id": channel_user_id},  # Dynamic field assignment
        )
        self.db.add(lead)
        self.db.commit()
        return lead
```

**Dynamic field assignment:** `{f"{channel}_id": channel_user_id}` — si `channel="telegram"`, crea `telegram_id=channel_user_id`. Esto es un legacy pattern; el CDP pattern actual usa `customer_identities`.

---

## 5. Flujo Completo de Integracion

```
Mensaje de Telegram (user_id="123456", name="María")
    │
    ▼
ChatOrchestrator.process_chat_flow()
    │
    ├── [1] IdentityType("telegram")
    │
    ├── [2] IdentityService.get_or_create_customer(
    │         tenant_id=UUID("abc"),
    │         identity_type=TELEGRAM,
    │         identity_value="123456",
    │         profile_data={"first_name": "María", "traits": {...}},
    │         lead_source="telegram-dm"
    │       )
    │       │
    │       ├── find_by_identity("123456", TELEGRAM, tenant=abc)
    │       │   → NULL (first time)
    │       │
    │       └── create_with_identity(...)
    │           → INSERT customer_profiles (full_name="María")
    │           → INSERT customer_identities (type=telegram, value=123456)
    │           → return (profile, True)
    │
    ├── [3] was_created=True → EventBus.publish(LeadCapturedEvent)
    │       → After commit: dispatch to analytics handler
    │         → Increment capture metric for "telegram-dm" channel
    │
    ├── [4] Update traits (merge metadata into profile)
    │
    ├── [5] get_active_lead(customer.id)
    │       → NULL (no lead yet)
    │       → create_lead(customer_id, channel="telegram", user_id="123456")
    │
    ├── [6] audit_repo.log_message(user_id=lead.id, role="user", ...)
    │
    ├── [7-9] Agent processing...
    │
    └── [10] audit_repo.log_message(user_id=lead.id, role="assistant", ...)
```

---

## Casuisticas

### Que pasa si el mismo usuario escribe por Telegram y luego por Instagram?
Se crean **dos perfiles separados** porque las identities son diferentes (telegram:123456 vs instagram:789). La unificacion se haria via email/phone si el agente logra capturar esa informacion durante la conversacion.

### Que pasa si un handler de evento falla?
El error se loguea pero los demas handlers siguen ejecutandose. El flujo principal (chat processing) no se ve afectado.

### Tenant isolation en el CRM?
Todas las queries incluyen `tenant_id` en el WHERE. `find_by_identity()` filtra por `CustomerIdentityModel.tenant_id == tenant_id`. Un usuario de Telegram con el mismo ID en dos tenants diferentes genera dos perfiles completamente separados.

### Los eventos se pierden si el servidor se reinicia durante el dispatch?
Si. Es un EventBus in-process, no persistente. Para el volumen actual esto es aceptable. Si se necesita garantia de entrega, se migraria a un message broker (Redis Streams, SQS, etc.).
