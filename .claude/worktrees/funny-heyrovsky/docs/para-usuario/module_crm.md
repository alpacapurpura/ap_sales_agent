---
module: CRM
status: active
core_files:
  - backend/src/modules/crm/domain/customer.py
  - backend/src/modules/crm/domain/lead.py
  - backend/src/modules/crm/domain/sale.py
  - backend/src/modules/crm/domain/enums.py
  - backend/src/modules/crm/infrastructure/models/customer_model.py
  - backend/src/modules/crm/infrastructure/models/lead_model.py
  - backend/src/modules/crm/infrastructure/models/sale_model.py
---

## 1. Propósito del Negocio (El "Por Qué")
Convertir interacciones temporales en relaciones duraderas. Gestiona la identidad unificada de cada persona que interactúa con el negocio, su ciclo de vida completo (desde visitante anónimo hasta evangelista), y el historial de ventas (LTV, Upselling, Cross-selling).

## 2. Arquitectura de Datos: Las 3 Tablas Clave

El módulo CRM sigue un patrón **CDP (Customer Data Platform)** con separación clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────┐
│                   customer_profiles                      │
│  (WHO) La persona unificada — "Golden Record"            │
│  - id, tenant_id, full_name, primary_email               │
│  - lifecycle_stage, lead_score, rfm_segment               │
│  - traits (JSONB), computed_traits (JSONB)                │
├─────────────────────────────────────────────────────────┤
│        ▲ 1:N                        ▲ 1:N               │
│        │                             │                    │
│  customer_identities              leads                   │
│  (HOW we find them)         (SALES context)               │
│  - type: email/phone/       - profile_data (JSONB)        │
│    telegram/whatsapp/       - fit_score, intent_score     │
│    instagram/tiktok         - temperature, funnel_stage   │
│  - value: el dato real      - conversation_summary        │
│  - is_primary               - key_objections_history      │
│                              - customer_id → profile FK   │
└─────────────────────────────────────────────────────────┘
```

### ¿Por qué 3 tablas y no 1?

| Tabla | Responsabilidad | Ciclo de Vida |
|-------|----------------|---------------|
| **customer_profiles** | Identidad unificada ("Golden Record"). Una persona = un perfil, sin importar cuántos canales use. | Permanente — el perfil sobrevive a múltiples interacciones de venta |
| **customer_identities** | Resolución de identidad multi-canal. Permite encontrar al mismo perfil por email, teléfono, Telegram ID, etc. | Crece con cada canal nuevo que el contacto usa |
| **leads** | Contexto de venta activo. Scores, temperatura, historial de objeciones, estado del funnel. | Por oportunidad — un cliente puede tener múltiples leads si vuelve a comprar |

**Beneficios de esta separación:**
- **Identity Resolution**: Si un contacto llega por Telegram y luego da su email, ambas identities apuntan al mismo profile
- **Reutilización**: `customer_profiles` se usa también en el módulo de Sales (ventas), Analytics (métricas), y Growth (retención)
- **Escalabilidad**: Los datos de conversación pesados (JSONB en leads) no contaminan la tabla ligera de profiles
- **Multi-canal nativo**: Agregar un nuevo canal (ej: TikTok DMs) es solo un nuevo `IdentityType`, no un schema change

### Tablas de soporte

| Tabla | Propósito |
|-------|-----------|
| **journey_events** | CDP event tracking (page_view, email_opened, checkout_completed) — vinculado a customer_profiles |
| **sales** | Registro transaccional de ventas, con auto-stage (CONVERSION vs EXPANSION) |

## 3. Reglas de Negocio Estrictas

- **Resolución de Identidad**: Un usuario entra al CRM cuando el sales_agent lo identifica por canal. `IdentityService.get_or_create_customer()` busca por identidad existente antes de crear perfil nuevo.
- **Lifecycle automático**: `SaleService` auto-determina CONVERSION (primera venta) vs EXPANSION (venta recurrente) basándose en el conteo de ventas previas del customer.
- **Consistencia de eventos**: Actualizaciones reactivas — escucha eventos del sales_agent y pasarelas de pago.
- **Aislamiento multitenant**: `tenant_id` (UUID) en todas las tablas, todas las queries filtran por tenant.
- **Soft deletes**: `is_blacklisted` en leads, `lifecycle_stage = CHURNED` en profiles.

## 4. Flujo de Datos

```
1. Lead entra por Telegram/WhatsApp/Instagram
   → IdentityService.get_or_create_customer() resuelve identidad
   → CustomerProfile creado/encontrado
   → Lead creado con customer_id vinculado

2. Conversación con el Sales Agent
   → Lead.profile_data actualizado (scores, temperatura, objeciones)
   → Messages registrados en sales_agent.messages

3. Venta completada
   → Sale creada vía SaleService.create_sale()
   → Stage auto: CONVERSION (primera) o EXPANSION (recurrente)
   → CustomerProfile.lifecycle_stage actualizado
```

## 5. Mapa de Código

```
backend/src/modules/crm/
├── domain/
│   ├── enums.py              # 15+ enums (IdentityType, LifecycleStage, FunnelStage, etc.)
│   ├── customer.py           # CustomerProfile, CustomerIdentity (domain entities)
│   ├── lead.py               # Lead, UserProfile "Valeria" (domain entities)
│   └── sale.py               # Sale (domain entity)
├── infrastructure/
│   ├── models/
│   │   ├── customer_model.py # CustomerProfileModel, CustomerIdentityModel, JourneyEventModel
│   │   ├── lead_model.py     # LeadModel
│   │   └── sale_model.py     # SaleModel
│   ├── repositories/
│   │   ├── customer_repository.py      # CRUD + identity resolution
│   │   ├── lead_repository.py          # CRUD by channel
│   │   ├── lead_metrics_repository.py  # Metrics + active lead management
│   │   └── sale_repository.py          # CRUD + date range queries
│   └── engines/
│       └── identity.py       # IdentityResolutionEngine
├── application/services/
│   ├── customer_service.py   # CustomerService (identify)
│   ├── identity_service.py   # IdentityService (get_or_create_customer)
│   ├── lead_service.py       # LeadService, PipelineService
│   └── sale_service.py       # SaleService (auto CONVERSION/EXPANSION)
└── api/
    ├── leads.py              # GET /search, GET /{lead_id}
    ├── pipeline.py           # GET /pipeline
    ├── sales.py              # POST /sales, GET /sales/ticker
    └── cdp.py                # POST /identify
```

## 6. Convenciones Técnicas

- `tenant_id` es `UUID` en todas las tablas (alineado con el resto del sistema)
- `IdentityType` enum tiene valores en UPPERCASE en PostgreSQL (TELEGRAM, WHATSAPP, etc.) para compatibilidad con SQLAlchemy
- `Lead.profile_data` se almacena como JSONB y se deserializa al domain entity `UserProfile`
- `Lead.customer_id` usa FK a `customer_profiles` para vincular lead con perfil unificado

## 7. Casos Borde Conocidos

- **Falsos positivos de identidad**: Dos personas compartiendo email/teléfono podrían unificarse incorrectamente
- **Escalabilidad de histórico**: Queries N+1 al renderizar historial extenso de un cliente
- **Duplicación de leads**: Si un contacto llega por Telegram y luego por WhatsApp sin haber dado datos cruzados, puede generar 2 customer_profiles separados hasta que se resuelva manualmente
