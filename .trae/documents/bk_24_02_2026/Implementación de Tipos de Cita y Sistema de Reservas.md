# Implementación de Tipos de Cita y Página de Reservas

He completado la implementación solicitada replicando la funcionalidad de Calc.com/Google Calendar.

## Backend
1.  **Esquema y Servicio (`EventTypeService`)**:
    *   Creado modelo `EventType` con configuración de límites de programación y reglas de reserva.
    *   Implementado almacenamiento en `Tenant.config_json` con validación de unicidad de slug.
2.  **API Endpoints**:
    *   `GET/POST/PATCH/DELETE /api/v1/event-types`: Gestión CRUD.
    *   `GET /api/v1/public/event-types/{tenant_slug}/{event_slug}`: Resolución pública de eventos.
    *   `GET .../slots`: Cálculo de horarios disponibles respetando reglas (buffer, márgenes, disponibilidad específica).
    *   `POST .../book`: Reserva de citas vinculada al tipo de evento.
3.  **Lógica de Disponibilidad**:
    *   Actualizado `AvailabilityService` para soportar `get_event_type_slots`.
    *   Implementado lógica de buffer, márgenes de anticipación (días/horas) y validación de calendario.

## Frontend
1.  **Dashboard de Ventas (`/sales`)**:
    *   Implementado `EventTypeView` con tarjetas visualmente idénticas a la referencia.
    *   Acciones: Editar, Duplicar, Copiar Link, Abrir, Eliminar, Ocultar/Mostrar.
2.  **Sidebar de Edición (`EventTypeSidebar`)**:
    *   Formulario completo con todos los campos solicitados: Título, Slug, Descripción, Duración, Disponibilidad, Plazos y Configuración de Reserva.
3.  **Página de Reservas (`/book/[tenant]/[slug]`)**:
    *   Nueva página pública dinámica que carga la configuración del evento.
    *   Muestra información del tenant (logo, nombre) y detalles del evento.
    *   Calendario interactivo con slots calculados en tiempo real según las reglas definidas.
    *   Formulario de reserva integrado.

## Archivos Clave
*   `backend/src/core/domain/event_type_schema.py`: Modelos de datos.
*   `backend/src/core/services/availability_service.py`: Lógica de slots.
*   `frontend/src/components/sales/event-type-view.tsx`: UI del Dashboard.
*   `frontend/src/app/book/[tenant_slug]/[event_slug]/page.tsx`: Landing Page de Reservas.