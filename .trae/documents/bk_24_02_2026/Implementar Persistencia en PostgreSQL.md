# Plan Refinado: CRM High-Ticket & Ecosistema de Productos

Este plan incorpora la lógica de negocio específica de "Visionarias" (Avatar Valeria, Lanzamientos, Downsell) directamente en la estructura de datos.

## 1. Modelo de Datos Estratégico (`src/services/models.py`)

Diseñaremos el esquema para capturar no solo datos, sino **contexto de venta**.

### A. Gestión de Identidad (`users`)
*   **Datos Clave:** `id`, `full_name`, `phone`, `email`.
*   **`avatar_profile` (JSONB):** Mapeo directo contra el perfil "Valeria".
    *   *Ejemplo:* `{"pain_points": ["saturación_mental", "falta_foco"], "desires": ["tribu", "libertad_financiera"], "business_stage": "transition_corporate"}`.
*   **`lead_score` (Integer):** Puntuación dinámica (0-100) basada en la coincidencia con el avatar y la intención de compra.

### B. Catálogo de Productos y Lanzamientos (`products`)
*   Soporta la lógica de **precios y fechas** del documento.
*   Campos:
    *   `type`: `program` (High Ticket), `webinar` (Lead Magnet/Downsell), `community` (Skool).
    *   `pricing`: `{"regular": 5925, "offer": 4444, "currency": "PEN"}`.
    *   `dates`: `{"start": "2026-02-10", "offer_deadline": "2026-08-12"}`.
    *   **`downsell_product_id` (FK):** Referencia al producto alternativo (ej: si rechaza el High Ticket, el sistema sabe qué ofrecer).

### C. El Viaje del Cliente (`enrollments`)
*   Tabla pivote que rastrea la relación Usuario-Producto.
*   **`status`:** `awareness` -> `qualified` -> `objection_handling` -> `call_booked` -> `enrolled` -> `downsell_accepted`.
*   **`objections` (JSONB):** Registro de frenos detectados (ej: `["price", "time", "spousal_approval"]`) para análisis posterior.

### D. Conversión (`appointments`)
*   Registro de las "Sesiones de Claridad" o "Cierre".
*   Estado: `scheduled`, `completed`, `no_show`.

## 2. Lógica de Negocio (`src/services/repository.py`)

*   **`initialize_catalog()`:** Script que insertará automáticamente el producto "De Propósito a Prosperidad" con sus precios y fechas al iniciar.
*   **`update_lead_scoring(user_id)`:** Sube el puntaje si el usuario menciona palabras clave ("estoy lista", "necesito orden").
*   **`get_next_offer(user_id)`:** Lógica para decidir: ¿Le ofrezco el programa? ¿Ya lo rechazó? -> Ofrezco el Webinar.

## 3. Integración en el Chat (`src/core/nodes.py`)

*   **Detección de Avatar:** El LLM analizará cada mensaje buscando "síntomas Valeria" y actualizará el perfil en segundo plano.
*   **Manejo de Fechas:** El bot consultará la DB para saber si la oferta de S/. 4,444 sigue vigente antes de mencionarla.
*   **Cierre:** Al agendar, se guarda la cita y se marca al usuario como `call_booked` para detener el seguimiento de venta agresiva.

## 4. Inicialización
*   Se creará la estructura de base de datos.
*   Se "sembrará" (seed) el producto principal con la data de tus documentos para que el bot tenga "consciencia" de lo que vende desde el primer momento.