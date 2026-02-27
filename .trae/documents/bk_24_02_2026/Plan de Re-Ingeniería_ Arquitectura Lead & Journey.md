Voy a ejecutar el "Plan de Re-Ingeniería: Arquitectura Lead & Journey" incorporando tu solicitud explícita de renombrar `Enrollment` a `JourneyProgress`.

### Plan de Ejecución Detallado

**1. Definición de Inteligencia (Nuevo Archivo)**
Crearé `backend/src/core/domain/lead_enums.py` con tus taxonomías expertas:
- `FinancialCapacity` (BROKE_STUDENT...)
- `SophisticationLevel` (UNAWARE...)
- `AuthorityLevel` (SOLO...)
- `LeadTemperature` (COLD, WARM, HOT, RADIOACTIVE)
- `AvatarPersona` (NEWBIE, SKEPTIC, VIP)
- `PipelineStage` (NEW_LEAD...)

**2. Evolución de la Clase Maestra (Lead)**
En `backend/src/services/db/models/lead.py`, agregaré columnas explícitas para permitir queries de alto rendimiento:
- `fit_score`, `intent_score` (Integer)
- `temperature` (Enum/String)
- `timezone`, `social_handle_main`
- `is_blacklisted`, `next_scheduled_action`
- `conversation_summary`, `key_objections_history`

**3. Refactorización Mayor: Enrollment -> JourneyProgress**
En `backend/src/services/db/models/business.py`, transformaré la clase `Enrollment`:
- **Renombrar Clase:** `class Enrollment` $\rightarrow$ `class JourneyProgress`
- **Renombrar Tabla:** `__tablename__ = "enrollments"` $\rightarrow$ `"journey_progress"`
- **Nuevos Atributos:**
    - `funnel_entry_point` (String)
    - `deal_value_potential` (Float)
    - `objection_status` (String)
    - `product_line` (Derivado de Product o explícito si se requiere snapshot)

**4. Actualización de Referencias (Refactoring)**
Buscaré y reemplazaré todas las referencias para evitar código roto ("Find & Replace" inteligente):
- **Archivos Afectados:**
    - `backend/src/services/db/models/lead.py` (Relación `enrollments` $\rightarrow$ `journeys`)
    - `backend/src/services/db/models/business.py` (Relación en `Product`)
    - `backend/src/services/db/repositories/business.py`
    - `backend/src/services/db/repositories/audit.py`
    - `backend/src/core/agents/orchestrator/nodes.py`
    - `backend/src/services/db/models/__init__.py`
- **Tarea:** Asegurar que `lead.enrollments` pase a ser `lead.journeys` y que las importaciones apunten a `JourneyProgress`.

**5. Actualización de Esquemas Pydantic**
Actualizaré `backend/src/core/domain/schema.py` para reflejar estos cambios en la API y validaciones.

Este plan cumple con tu visión de "Lifelong Nurturing" y la separación estricta de Identidad vs. Viaje, renombrando explícitamente la entidad como solicitaste.