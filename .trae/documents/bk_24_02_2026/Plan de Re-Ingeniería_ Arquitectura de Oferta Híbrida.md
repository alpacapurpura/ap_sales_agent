# Implementación de Arquitectura de Oferta "Lifelong Nurturing"

Este plan transformará la entidad básica `Product` en un modelo `Offer` robusto, capaz de manejar Value Ladders, Pricing complejo y lógica de ventas híbrida.

## 1. Definición de Enums de Negocio
**Archivo:** `backend/src/core/domain/lead_enums.py`
Agregaremos los vocabularios controlados para estandarizar la lógica de ventas:
- `OfferType` (DIGITAL_PRODUCT, COHORT_PROGRAM, etc.)
- `DeliveryModel` (DIY, DWY, DFY)
- `GuaranteeType` (UNCONDITIONAL, ACTION_BASED, etc.)
- `OfferStatus` (ALWAYS_ON, WAITLIST, CLOSED)

## 2. Refactorización del Modelo de Base de Datos
**Archivo:** `backend/src/services/db/models/business.py`
Transformaremos la clase `Product` en `Offer`.
*Nota: Mantendremos el nombre de la tabla `products` para preservar la integridad de los datos existentes y las relaciones de claves foráneas, pero la lógica de la aplicación usará `Offer`.*

### Nuevos Campos:
- **Identidad:** `internal_sku`, `public_name` (migrado de `name`), `offer_type`, `delivery_model`.
- **Promesa:** `headline_promise`, `target_avatars` (JSON), `primary_outcome`, `time_to_value`.
- **Gatekeeping:** `requires_application`, `min_financial_capacity`, `prerequisites` (JSON).
- **Financiero:** `pricing_options` (JSONB - Estructura compleja), `currency`.
- **Garantía:** `guarantee_type`, `guarantee_terms`.
- **Relaciones de Escalera:** `downsell_offer_id` (FK), `upsell_offer_id` (FK), `includes_offers` (JSONB - IDs para Value Stacking).
- **Activos:** `vsl_link`, `checkout_page_url`, `calendar_link`.

## 3. Actualización de Esquemas Pydantic (Domain Layer)
**Archivo:** `backend/src/core/domain/offer/schema.py`
Actualizaremos `HighTicketOffer` para reflejar la nueva riqueza de datos, permitiendo que el Agente razone sobre precios y garantías.
- Creación de sub-modelos: `PricingStructure`, `DeliverableItem`.
- Validación estricta de Enums.

## 4. Actualización de Repositorios y Lógica
**Archivo:** `backend/src/services/db/repositories/business.py`
- Actualizar referencias de `Product` a `Offer`.
- Renombrar métodos para consistencia (ej. `get_current_launch_product` -> `get_current_launch_offer`).

## 5. Limpieza de Referencias "Enrollment"
**Archivo:** `backend/src/core/agents/orchestrator/nodes.py`
- Verificar y limpiar cualquier comentario o referencia residual al antiguo nombre "Enrollment" para evitar confusión técnica.

## Verificación
- Ejecutaremos una validación de importaciones para asegurar que el cambio de nombre de clase `Product` -> `Offer` no rompa el inicio de la aplicación.
