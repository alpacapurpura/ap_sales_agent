# Modelo de Datos - Visionarias Sales Agent

Este documento describe la estructura de datos implementada en PostgreSQL (via SQLAlchemy) para soportar la lógica de ventas High Ticket, multi-tenancy y trazabilidad cognitiva.

## 1. Núcleo de Negocio (Business Core)

Define *qué* se vende, *a quién* y *cómo*.

### 1.1. Ofertas (`products`)
El catálogo de productos, mentorías y servicios. Es la entidad central de la estrategia de ventas.

| Campo | Tipo | Descripción | Objetivo de Negocio |
|-------|------|-------------|---------------------|
| `id` | UUID | PK | Identificador único global. |
| `tenant_id` | String | FK | Tenant al que pertenece. |
| `internal_sku` | String | Código | Identificación logística (ej: "MASTERMIND_Q1_2026"). |
| `name` | String | Nombre Público | Nombre comercial visible al cliente. |
| `type` | Enum | `OfferType` | Taxonomía: `TRIPWIRE_OFFER`, `HIGH_TICKET_MENTORING`, etc. |
| `offer_value_level` | Enum | `OfferValueLevel` | Nivel en la escalera de valor (`N1_LOW_TICKET` a `N6_CORPORATE`). |
| `delivery_model` | Enum | `OfferDeliveryModel` | `DIY` (Do It Yourself), `DWY` (Done With You), `DFY` (Done For You). |
| `status` | Enum | `OfferStatus` | `ALWAYS_ON`, `WAITLIST_ONLY`, `SOLD_OUT`. |
| `headline_promise` | String | Promesa | El "Gancho" o transformación principal. |
| `target_avatar_match` | JSONB | Avatares | Lista de IDs de avatares compatibles. |
| `pricing` | JSONB | Precios | Estructura compleja de precios (contado, plazos, ahorro). |
| `prerequisites` | JSONB | Requisitos | Filtros de cualificación (ingresos, experiencia, etc.). |
| `guarantee_type` | Enum | `GuaranteeType` | Tipo de garantía (`UNCONDITIONAL`, `ACTION_BASED`). |
| `guarantee_terms` | Text | Términos | Texto legal/explicativo de la garantía. |
| `metadata_info` | JSONB | Assets | Links (Checkout, VSL), IDs externos. |
| `downsell_product_id` | UUID | FK | Producto alternativo de menor valor. |
| `upsell_product_id` | UUID | FK | Siguiente paso en la escalera de valor. |

### 1.2. Avatares (`avatar_definitions`)
Define los perfiles de cliente ideal (ICP) y sus anti-perfiles.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `name` | String | Nombre interno (ej: "Emprendedor Novato"). |
| `icp_description` | Text | Descripción detallada del cliente ideal. |
| `anti_avatar` | Text | Descripción de a quién NO vender. |
| `voice_tone_config` | JSONB | Configuración de tono de voz específico para este avatar. |

### 1.3. Assets de Marketing (`marketing_assets`)
Recursos educativos o de venta (Webinars, PDFs, VSLs).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `product_id` | UUID | Producto asociado. |
| `type` | String | `webinar`, `vsl`, `pdf`, `audio`. |
| `url` | String | Enlace al recurso. |
| `transcript_summary` | Text | Resumen para RAG del contenido. |
| `hook_points` | JSONB | Puntos clave para usar en argumentos de venta. |

---

## 2. Gestión de Leads y Ventas (CRM)

Gestiona las personas y su viaje a través del embudo.

### 2.1. Leads (`leads`)
La persona potencial cliente. Centraliza identidad y perfilado.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `full_name` | String | Nombre completo. |
| `email` | String | Email principal. |
| `phone` | String | Teléfono (WhatsApp). |
| `telegram_id` | String | ID de Telegram. |
| `whatsapp_id` | String | ID de WhatsApp. |
| `fit_score` | Int | 0-100. Qué tan bien encaja con el ICP. |
| `intent_score` | Int | 0-100. Qué tantas ganas tiene de comprar. |
| `temperature` | Enum | `LeadTemperature` (`COLD`, `WARM`, `HOT`). |
| `profile_data` | JSONB | Datos extraídos (profesión, ingresos, dolores). |
| `conversation_summary` | Text | Resumen acumulativo de charlas previas. |

### 2.2. Progreso del Viaje (`journey_progress`)
Estado actual de un Lead respecto a un Producto específico.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `lead_id` | UUID | El cliente. |
| `product_id` | UUID | El producto de interés. |
| `status` | String | `qualified`, `disqualified`, `enrolled`. |
| `stage` | Enum | `PipelineStage` (`DISCOVERY`, `OFFER_MADE`, `CLOSING`). |
| `product_line` | String | Contexto macro (`High`, `Low`). |
| `deal_value_potential` | Float | Valor estimado de la venta. |
| `objection_status` | String | Objeción activa actual. |
| `objections` | JSONB | Historial de objeciones tratadas. |

### 2.3. Logs de Ofertas (`offer_logs`)
Registro inmutable de cada "Pitch" realizado.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `user_id` | UUID | Lead al que se ofertó. |
| `product_id` | UUID | Producto ofrecido. |
| `offered_at` | DateTime | Cuándo ocurrió. |
| `pitch_type` | String | `soft_pitch`, `hard_close`. |
| `response` | String | `accepted`, `rejected`, `pending`. |

---

## 3. Infraestructura y Multi-Tenancy

### 3.1. Tenants (`tenants`)
Configuración de cada cliente del SaaS (Agencia/Empresa).

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `slug` | String | Identificador único (ej: `agencia-x`). |
| `config_json` | JSONB | Configuración global (Brand voice, reglas). |
| `api_keys` | String | Keys de OpenAI/Gemini (encriptadas). |

### 3.2. Conexiones (`channel_connections`)
Integraciones con plataformas de mensajería.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `channel_type` | Enum | `TELEGRAM`, `WHATSAPP`, `MANYCHAT`. |
| `credentials` | JSONB | Tokens, API Keys del canal. |
| `config` | JSONB | Webhook secrets, números de teléfono. |

---

## 4. Motor Cognitivo y Observabilidad

### 4.1. Mensajes (`messages`)
Historial de chat enriquecido.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `role` | String | `user`, `assistant`, `system`. |
| `content` | Text | Texto del mensaje. |
| `metadata_log` | JSONB | **Cognitive Trace**: Intent, Thought, State. |
| `channel` | String | Canal de origen (`telegram`, `web`). |

### 4.2. Documentos RAG (`documents`)
Base de conocimiento vectorial.

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `collection_name` | String | Colección en Qdrant. |
| `category` | String | `knowledge_base`, `product_info`. |
| `chunk_count` | Int | Número de fragmentos vectorizados. |
| `status` | String | `indexed`, `pending`, `error`. |

---

## 5. Diccionario de Enums (Referencia)

Valores estandarizados utilizados en los modelos.

### 5.1. OfferType
*   `TRIPWIRE_OFFER`: Producto de entrada bajo costo.
*   `CORE_OFFER`: Producto principal.
*   `HIGH_TICKET_MENTORING`: Mentoría premium.
*   `DONE_FOR_YOU_SERVICE`: Servicios de agencia.
*   `SUBSCRIPTION_ACCESS`: Membresía recurrente.
*   `MASTERMIND_NETWORK`: Acceso a red exclusiva.

### 5.2. OfferValueLevel
*   `N0_FREE_LEAD_MAGNET`
*   `N1_LOW_TICKET_TRIPWIRE`
*   `N2_MID_TICKET_CORE`
*   `N3_HIGH_TICKET_PREMIUM`
*   `N4_ULTRA_HIGH_EXCLUSIVE`
*   `N6_CORPORATE_B2B`

### 5.3. LeadTemperature
*   `COLD`: Desconocido, sin confianza.
*   `WARM`: Interesado, consume contenido.
*   `HOT`: Listo para comprar, tiene urgencia.
*   `RADIOACTIVE`: Fanático o comprador recurrente.

### 5.4. PipelineStage
*   `NEW_LEAD`: Recién entrado.
*   `DISCOVERY`: Cualificación en proceso.
*   `OFFER_MADE`: Pitch realizado.
*   `NEGOTIATION`: Manejo de objeciones.
*   `WON`: Venta cerrada.
*   `LOST`: Descartado/No compró.
*   `NURTURE`: En seguimiento a largo plazo.

### 5.5. SophisticationLevel (Eugene Schwartz)
*   `UNAWARE`: No sabe que tiene un problema.
*   `PROBLEM_AWARE`: Sabe el problema, busca solución.
*   `SOLUTION_AWARE`: Conoce soluciones, compara tipos.
*   `PRODUCT_AWARE`: Conoce TU producto, compara ofertas.
*   `MOST_AWARE`: Solo quiere el "Deal".
