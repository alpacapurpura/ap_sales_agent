# Plan de Re-Ingeniería: Arquitectura "Lifelong Nurturing" & "Hybrid Offer Ecosystem"

Este plan consolida la visión de separar la Identidad (Lead) de la Aventura (Journey) y transforma la oferta en una entidad inteligente capaz de negociar.

## 1. Fundamentos Técnicos

* **Hibridación Relacional-Documental**: Usaremos PostgreSQL con columnas `JSONB` para manejar la complejidad variable de las ofertas (Pricing Structures, Deliverables) manteniendo la integridad relacional para el núcleo (SKU, IDs).

* **Separación de Responsabilidades**:

  * `Lead`: Datos estáticos y profundos de la persona.

  * `JourneyProgress`: Estado dinámico del cliente *por producto*.

  * `Product (Offer)`: Reglas de negocio, promesas y arquitectura financiera.

* **Tipado Estricto (Enums)**: Centralización de reglas de negocio en Enums para evitar "magic strings" y permitir que el LLM razone con categorías cerradas.

## 2. Implementación Paso a Paso

### FASE 1: Taxonomía y Reglas de Negocio (Enums)

Crearemos el vocabulario controlado que el agente utilizará para razonar.

* **Archivo**: `backend/src/core/domain/offer_enums.py`

* **Definiciones**: `OfferType`, `DeliveryModel`, `GuaranteeType`, `OfferStatus`.

### FASE 2: Evolución del Modelo de Datos (DB)

Transformaremos la tabla `products` para soportar la estructura "Offer" completa.

* **Archivo**: `backend/src/services/db/models/business.py`

* **Cambios en** **`Product`**:

  * Agregar: `internal_sku`, `delivery_model`, `headline_promise`, `target_avatar_match` (JSONB), `requires_application`, `min_financial_capacity`, `guarantee_type`, `downsell_product_id`, `upsell_product_id`.

  * Estructurar `pricing` (JSONB) para soportar listas de opciones.

  * Estructurar `metadata_info` (JSONB) para incluir `vsl_link`, `checkout_url`.

* **Verificación** **`JourneyProgress`**:

  * Asegurar que la tabla `journey_progress` (antes Enrollment) tenga las relaciones correctas y columnas `funnel_entry_point`, `deal_value_potential`.

### FASE 3: Lógica de Dominio (Schemas Pydantic)

Actualizaremos los esquemas que el Agente utiliza para validar y estructurar la información en tiempo de ejecución.

* **Archivo**: `backend/src/core/domain/offer/schema.py`

* **Nuevos Modelos**:

  * `PricingStructure`: Manejo de pagos únicos vs financiados.

  * `DeliverableItem`: Stack de valor.

  * `Offer`: La representación completa para el agente.

### FASE 4: Inteligencia del Agente (Orchestrator)

Implementar las reglas de decisión en el cerebro del agente.

* **Archivo**: `backend/src/core/agents/orchestrator/nodes.py`

* **Limpieza**: Renombrar cualquier comentario o string residual de "Enrollment" a "Journey".

* **Lógica de Downsell**: Preparar el nodo para leer `downsell_product_id` si el usuario rechaza por precio.

* **Matriz de Compatibilidad**: Implementar la regla `Offer.min_financial_capacity <= Lead.financial_tier`.

### FASE 5: Actualización de Referencias Rotas

* Buscar y reemplazar referencias a `Enrollment` en todo el codebase (Tests, APIs, Utils) para apuntar a `JourneyProgress`.

## 3. Resultado Esperado

El sistema podrá:

1. Identificar si un Lead es apto para High Ticket o debe ir a Low Ticket (Matriz de Compatibilidad).
2. Ofrecer planes de pago estructurados dinámicamente.
3. Hacer "Downsell" automático a un producto menor si se rechaza la oferta principal.
4. Mantener un historial limpio de múltiples intentos de compra por usuario (`JourneyProgress`).

