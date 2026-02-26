# Documentación Funcional: Estructura de Ofertas

## 1. Visión General de Arquitectura
El sistema utiliza una **Arquitectura Polimórfica** tanto en Backend como en Frontend.
- **Backend**: La entidad `Offer` tiene un campo `type` (Enum) y un campo `specific_details` (JSONB). La estructura de `specific_details` es forzada por modelos Pydantic mapeados al `OfferType`.
- **Frontend**: Un patrón "Builder" donde el `OfferType` determina una lista de `Secciones`. Cada `Sección` corresponde a un Componente de Formulario específico.

## 2. Guía del Desarrollador: Cómo Crear un Nuevo OfferType

Para añadir un nuevo OfferType (ej. `HYBRID_MASTERMIND`), sigue estos pasos:

### Backend
1.  **Enum**: Añade `HYBRID_MASTERMIND` a `OfferType` en `backend/src/core/domain/offer_enums.py`.
2.  **Schema**:
    *   Si los modelos de detalles existentes (`ProgramDetails`, `ServiceDetails`, etc.) encajan, usa uno existente.
    *   Si no, define `HybridMastermindDetails(BaseModel)` en `backend/src/core/domain/offer/schema.py`.
3.  **Mapping**: Actualiza `OFFER_TYPE_TO_DETAILS_MAPPING` en `schema.py` para vincular `HYBRID_MASTERMIND` -> `HybridMastermindDetails`.

### Frontend
1.  **Enum**: Añade el tipo a `OfferType` en los tipos de TypeScript.
2.  **Config**: Actualiza `OFFER_BUILDER_CONFIG` en `frontend/src/features/offer-studio/config/offer-builder-config.ts`.
    ```typescript
    [OfferType.HYBRID_MASTERMIND]: ['identity', 'strategy', 'program_details', 'pricing', 'closing']
    ```
3.  **Formularios**: Si se necesita una nueva sección, crea el componente de formulario y regístralo en `SECTION_REGISTRY`.

---

## 3. Catálogo Detallado de Formularios

### A. Formularios Comunes (Todas las Ofertas)

#### 1. Formulario de Identidad (`identity`)
*   **Lógica**: Siempre es el primer paso. Define el "Alma" de la oferta.
*   **Campos**:
    | Campo | Etiqueta UI | Tipo | Obligatorio | Descripción |
    | :--- | :--- | :--- | :--- | :--- |
    | `public_name` | Nombre Público | Texto | Sí | Nombre mostrado a los clientes. |
    | `type` | Tipo de Oferta | Badge | - | Muestra el OfferType actual (solo lectura). |
    | `delivery_model` | Modelo de Entrega | Badge | - | Muestra el Modelo de Entrega (DIY/DWY/DFY). |

#### 2. Formulario de Precios (`pricing`)
*   **Lógica**: Maneja los modelos financieros.
*   **Campos**:
    | Campo | Etiqueta UI | Tipo | Obligatorio | Descripción |
    | :--- | :--- | :--- | :--- | :--- |
    | `pricing_options` | Opciones de Precio | Lista | Sí | Lista de planes de pago. |
    | `total_amount` | Precio Total | Número | Sí | Valor monetario. |
    | `currency` | Moneda | Select | Sí | USD, EUR, MXN, etc. |
    | `plan_type` | Tipo de Plan | Select | No | Pago Único vs Suscripción. |
    | `number_of_installments` | Cuotas | Número | No | Para pagos divididos. |

### B. Formularios de Detalles Específicos (Polimórficos)

#### 3. Detalles del Programa (`program_details`)
*   **Usado Por**: `COHORT_BASED_COURSE`, `HYBRID_MENTORSHIP`, `GROUP_COACHING`, `CHALLENGE`.
*   **Lógica**:
    *   Si `structure_type` es `FIXED_DATE_COHORT`, `start_date` es obligatorio.
    *   Las recomendaciones para `interaction_type` aparecen basadas en `structure_type`.
*   **Campos**:
    | Campo | Etiqueta UI | Tipo | Obligatorio | Descripción |
    | :--- | :--- | :--- | :--- | :--- |
    | `structure_type` | Tipo de Estructura | Select | Sí | Cohorte, Evergreen, o Reto. |
    | `is_application_required` | Requiere Aplicación | Switch | No | Activa filtro "High Ticket". |
    | `duration_weeks` | Duración (Semanas) | Número | No | Duración del compromiso. |
    | `interaction_type` | Dinámica de Interacción | Select | No | En vivo, Híbrido, Asíncrono. |
    | `community_platform` | Plataforma de Comunidad | Select | No | Circle, Slack, Discord, etc. |
    | `start_date` | Fecha de Inicio | Date+Time | Condicional | Obligatorio para Cohortes. |
    | `registration_end_date` | Cierre de Inscripciones | Date+Time | No | Fecha límite de venta. |
    | `end_date` | Fecha de Fin | Date | No | Fecha de graduación. |

#### 4. Detalles del Producto (`product_details`)
*   **Usado Por**: `EBOOK`, `MERCH`, `TRIPWIRE`, `SELF_PACED_COURSE`.
*   **Lógica**:
    *   Si `fulfillment_type` es `PHYSICAL`, muestra campos de envío.
*   **Campos**:
    | Campo | Etiqueta UI | Tipo | Obligatorio | Descripción |
    | :--- | :--- | :--- | :--- | :--- |
    | `fulfillment_type` | Tipo de Entrega | Select | Sí | Digital o Físico. |
    | `format` | Formato Digital | Select | No | PDF, Video, Audio, etc. |
    | `access_url` | URL de Acceso | URL | No | Link de descarga o acceso. |
    | `requires_shipping` | Requiere Envío | Switch | No | Visible solo si es Físico. |
    | `stock_quantity` | Stock | Número | No | Visible solo si es Físico. |
    | `sku_inventory_code` | SKU Interno | Texto | No | Identificador de inventario. |

#### 5. Detalles del Servicio (`service_details`)
*   **Usado Por**: `AGENCY`, `CONSULTING`, `FREELANCE`.
*   **Campos**:
    | Campo | Etiqueta UI | Tipo | Obligatorio | Descripción |
    | :--- | :--- | :--- | :--- | :--- |
    | `category` | Categoría | Select | No | Advisory vs Agency. |
    | `deliverables_list` | Entregables | Lista | No | Lista de items incluidos. |
    | `turnaround_time_days` | Tiempo de Entrega | Número | No | Días hábiles para entrega. |
    | `booking_url` | Link de Agenda | URL | Condicional | Crítico para Advisory. |
    | `revision_rounds` | Rondas de Cambios | Número | No | Límite de revisiones. |

#### 6. Detalles del Evento (`event_details`)
*   **Usado Por**: `RETREAT`, `MASTERMIND`, `WORKSHOP`.
*   **Lógica**:
    *   Valida que `end_date` sea posterior a `start_date`.
*   **Campos**:
    | Campo | Etiqueta UI | Tipo | Obligatorio | Descripción |
    | :--- | :--- | :--- | :--- | :--- |
    | `start_date` | Fecha Inicio | DateTime | No | Inicio del evento. |
    | `end_date` | Fecha Fin | DateTime | No | Fin del evento. |
    | `location_type` | Tipo de Ubicación | Select | No | Virtual o Físico. |
    | `venue_name` | Lugar/Hotel | Texto | Condicional | Obligatorio si es Físico. |
    | `venue_address` | Dirección | Texto | No | Para Google Maps. |
    | `virtual_meeting_url` | Link de Reunión | URL | Condicional | Obligatorio si es Virtual. |

---

## 4. Análisis UX y Propuestas de Optimización

### Redundancias Identificadas
1.  **Selectores de Fecha**: `ProgramDetails` y `EventDetails` implementan lógica de fechas compleja por separado. Podría unificarse en un `ScheduleComponent`.
2.  **Instructores**: Actualmente es un formulario separado (`instructors`), pero mentalmente el usuario suele asociarlo a la `Identidad` de la oferta.

### Evaluación de Complejidad
*   **Alta Complejidad**: `ProgramDetails` es el formulario más pesado debido a la lógica condicional entre `structure_type` -> `interaction_type` -> `dates`.
*   **Riesgo**: La separación de `Precios` (`Pricing`) de los `Detalles` puede causar fricción (ej. definir un precio de "Membresía" sin haber configurado primero los "Detalles de Suscripción").

### Propuestas de Optimización
1.  **Constructor de Horarios Unificado**: Extraer el planificador de sesiones de `ProgramDetails` y hacerlo disponible para `EventDetails` (Los talleres a menudo tienen horarios).
2.  **Defaults Inteligentes**: Pre-llenar `structure_type` basado en el `OfferType` seleccionado durante la creación (ej. el tipo `COHORT` debería tener `FIXED_DATE` por defecto).
