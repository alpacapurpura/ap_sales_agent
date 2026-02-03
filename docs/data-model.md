# Modelo de Datos - Visionarias Sales Agent

Este documento describe la estructura de datos implementada en PostgreSQL para soportar la lógica de ventas High Ticket y trazabilidad cognitiva.

## 1. Ofertas (`products`)

Define el catálogo de ofertas disponibles (Cursos, Mentorías, Servicios), categorizados por nivel de compromiso y lógica de entrega.

| Campo | Tipo | Descripción | Objetivo de Negocio |
|-------|------|-------------|---------------------|
| `id` | UUID | Identificador único | Referencia global del producto. |
| `internal_sku` | String | SKU Interno | Identificación logística (ej: "MASTERMIND_Q1_2026"). |
| `name` | String | Nombre Público | Nombre comercial visible al cliente. |
| `type` | String | Tipo de Oferta | `HYBRID_MENTORSHIP`, `DIGITAL_PRODUCT`, etc. (Ver `OfferType`). |
| `delivery_model` | String | Modelo de Entrega | `DIY`, `DWY`, `DFY`. Define el precio y nivel de soporte. |
| `status` | String | Estado | `ALWAYS_ON`, `WAITLIST_ONLY`. Controla disponibilidad. |
| `headline_promise` | String | Promesa Principal | El "Gancho" o transformación que vende el agente. |
| `target_avatar_match` | JSONB | Lista de Avatares | A qué perfiles (`THE_NEWBIE`, `THE_VIP`) se dirige esta oferta. |
| `pricing` | JSONB | Estructura de Precios | Lista de opciones (Contado, Financiado) con detalles de ahorro. |
| `dates` | JSONB | `{start, offer_deadline}` | Controla la **Ventana de Lanzamiento**. |
| `metadata_info` | JSONB | Assets | Links (VSL, Checkout), IDs de Calendly. |
| `downsell_product_id` | UUID | Estrategia Downsell | Producto alternativo si se rechaza por precio. |
| `upsell_product_id` | UUID | Estrategia Upsell | Siguiente paso lógico en la escalera de valor. |

## 2. Ofrecimientos (`offer_logs`)

**Nueva Tabla**. Registro inmutable de cada vez que el agente realiza una invitación o pitch formal.

| Campo | Tipo | Descripción | Objetivo de Negocio |
|-------|------|-------------|---------------------|
| `id` | UUID | ID del evento | Trazabilidad única. |
| `user_id` | UUID | Cliente | Quién recibió la oferta. |
| `product_id` | UUID | Producto | Qué se ofreció. |
| `offered_at` | DateTime | Timestamp | **Cuándo** se ofreció (crucial para no repetir ofertas). |
| `pitch_type` | String | Tipo de Pitch | Ej: `soft_pitch` (mención), `hard_close` (cierre directo). |
| `response` | String | Estado | `pending`, `accepted`, `rejected`. |

## 3. Mensajes Enriquecidos (`messages`)

Historial de conversación que ahora incluye la "mente" del agente.

| Campo | Tipo | Descripción | Objetivo de Negocio |
|-------|------|-------------|---------------------|
| `role` | String | `user` / `assistant` | Quién habla. |
| `content` | Text | Texto del mensaje | El contenido visible. |
| `metadata_log` | JSONB | **Cognitive Trace** | Guarda `{ intent: "educate", thought: "User is skeptical", state: "S3_Gap" }`. |
| `product_context_id` | UUID | Contexto | Sobre qué producto se estaba hablando en ese mensaje. |

## 4. Progreso del Viaje (`journey_progress`)

*Anteriormente `enrollments`*. Representa la relación "viva" entre un usuario y un producto (su viaje por el funnel).

| Campo | Tipo | Descripción | Objetivo de Negocio |
|-------|------|-------------|---------------------|
| `status` | String | Estado del Lead | `awareness`, `qualified`, `disqualified`, `enrolled`. |
| `stage` | String | Etapa de Venta | `S1_Rapport` ... `S6_Closing`. Granularidad fina. |
| `product_line` | String | Línea de Producto | `Low`, `Mid`, `High`. Contexto macro. |
| `funnel_entry_point` | String | Origen | `Ad`, `Webinar`, `Email`. Atribución. |
| `deal_value_potential` | Float | Valor Potencial | Estimación de venta para forecast. |
| `lead_score` | Int | Puntaje (0-100) | Priorización de leads calientes. |
| `objection_status` | String | Bloqueo Actual | La objeción activa que impide la venta. |
| `objections` | JSONB | Historial | Registro histórico de barreras detectadas. |

## Relaciones Principales

*   **Lead** 1:N **JourneyProgress** (Un usuario puede estar en varios funnels simultáneamente).
*   **Lead** 1:N **OfferLogs** (Historial de intentos de venta).
*   **Offer (Product)** 1:N **JourneyProgress** (Todos los leads activos en una oferta).
