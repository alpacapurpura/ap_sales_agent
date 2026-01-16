# Modelo de Datos - Visionarias Sales Agent

Este documento describe la estructura de datos implementada en PostgreSQL para soportar la lógica de ventas High Ticket y trazabilidad cognitiva.

## 1. Productos (`products`)

Define el catálogo de ofertas disponibles, categorizados por nivel de compromiso (Tier).

| Campo | Tipo | Descripción | Objetivo de Negocio |
|-------|------|-------------|---------------------|
| `id` | UUID | Identificador único | Referencia global del producto. |
| `name` | String | Nombre comercial | Identificación en logs y reportes. |
| `tier` | String | Nivel (`lead_magnet`, `high_ticket`) | **Clave**: Define si es un producto de entrada (gratis) o de monetización (pago). |
| `type` | String | Formato (`program`, `webinar`) | Define la modalidad de entrega. |
| `status` | String | `active` / `archived` | Controla qué productos están disponibles para venta. |
| `dates` | JSONB | `{start, offer_deadline}` | Controla la **Ventana de Lanzamiento** y urgencia (Scarcity). |
| `pricing` | JSONB | `{regular, offer, currency}` | Manejo de precios dinámicos y ofertas. |

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
| `metadata_log` | JSONB | **Cognitive Trace** | Guarda `{ intent: "educate", thought: "User is skeptical", state: "S3_Gap" }`. Permite auditar la lógica del agente. |
| `product_context_id` | UUID | Contexto | Sobre qué producto se estaba hablando en ese mensaje. |

## 4. Inscripciones (`enrollments`)

Representa la relación "viva" entre un usuario y un producto (su viaje por el funnel).

| Campo | Tipo | Descripción | Objetivo de Negocio |
|-------|------|-------------|---------------------|
| `status` | String | Estado del funnel | `awareness`, `qualified`, `disqualified`, `enrolled`. |
| `stage` | String | Etapa de venta | `S1_Rapport` ... `S6_Closing`. Granularidad fina. |
| `lead_score` | Int | Puntaje (0-100) | Priorización de leads calientes. |
| `objections` | JSONB | Lista de objeciones | Registro de barreras detectadas (precio, tiempo). |

## Relaciones Principales

*   **User** 1:N **Enrollments** (Un usuario puede estar en varios funnels: webinar + programa).
*   **User** 1:N **OfferLogs** (Historial de intentos de venta).
*   **Product** 1:N **Enrollments** (Todos los leads de un producto).
