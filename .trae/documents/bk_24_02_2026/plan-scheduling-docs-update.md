# Plan de Actualización de Documentación: Scheduling Module

Este plan detalla los pasos para actualizar `docs/domains/module_scheduling.md` con información técnica precisa y orientada a agentes, basándose en la implementación actual del código.

## Objetivo
Transformar `docs/domains/module_scheduling.md` en la "Fuente de Verdad" para cualquier agente (AI o humano) que necesite interactuar con el sistema de agendamiento, siguiendo el estándar de calidad de `module_brand.md`.

## Estructura Propuesta

### 1. Contexto del Agente
- Definición clara del alcance: Gestión de disponibilidad, reservas y sincronización de calendarios.
- Advertencia: Este módulo es la autoridad final sobre "cuándo" pueden ocurrir las interacciones.

### 2. Mapa de Código (The "Where")
Detalle exhaustivo de la ubicación de los componentes clave.

#### Backend (Python/FastAPI)
- **Modelos de Dominio**:
  - `AppointmentModel`: Persistencia de citas (`backend/src/modules/scheduling/infrastructure/models/appointment_model.py`).
  - `BookingLink`: Gestión de enlaces públicos (`backend/src/modules/scheduling/infrastructure/models/booking_link.py`).
  - `EventType`: Configuración dinámica en `Tenant.config_json` (Schema: `backend/src/modules/scheduling/domain/event_type_schema.py`).
- **Servicios Principales**:
  - `AvailabilityService`: Lógica de cálculo de slots y orquestación de reservas.
  - `GoogleCalendarAdapter`: Integración con Google Calendar.
- **API Routers**:
  - `connections/api/calendar.py`: Gestión de citas.
  - `scheduling/api/event_types.py`: Configuración de tipos de eventos.
  - `scheduling/api/public_links.py`: Endpoints públicos para leads.

#### Frontend (React/Next.js)
- **Componentes Clave**:
  - `CalendarWidget`: Widget de dashboard.
  - `AvailabilityView`: Configuración de disponibilidad.
  - `EventTypeForm`: ABM de tipos de eventos.
  - `Public Booking Page`: Ruta dinámica para clientes finales (`app/(main)/book/[tenant_slug]/[event_slug]`).
- **Hooks y Clientes**:
  - `lib/api/availability.ts`: Consumo de disponibilidad.
  - `lib/api/booking-links.ts`: Generación de links.

### 3. Lógica de Negocio (The "Why" & "How")
- **Almacenamiento Híbrido**:
  - Citas (`appointments`) en tabla SQL relacional para consultas rápidas y reportes.
  - Configuración (`event_types`) en JSONB del Tenant para flexibilidad sin migraciones.
- **Flujo de Reserva**:
  1. Generación de Link (Público o Único).
  2. Selección de Slot (Validación contra `AvailabilityService` + Google Calendar).
  3. Confirmación (Creación de `Appointment`, Evento en GCal, Notificación).
- **Integración con Sales Agent**:
  - El Agente de Ventas NO agenda directamente; delega al `Scheduler` (nodo conceptual) o genera un `BookingLink` para que el usuario finalice.
  - Uso de `AvailabilityService.get_slots()` para informar opciones en chat.

### 4. Integraciones y Contratos
- **Sales Agent -> Scheduling**:
  - Protocolo: Solicitar slots disponibles -> Presentar opciones -> Generar link de cierre.
- **Landing Page -> Scheduling**:
  - Uso de `public_token` para acceso limitado a la API de disponibilidad.

### 5. Casos Borde y Gotchas (Edge Cases)
- **Timezones**: Conversión estricta a UTC en backend, visualización local en frontend.
- **Double Booking**: Manejo de concurrencia optimista o bloqueo de slots.
- **Token Expiration**: Validez de los enlaces generados dinámicamente.

### 6. Snippets para Agentes (Common Tasks)
- **Backend**: Código Python para consultar disponibilidad y crear un link de reserva.
- **Frontend**: Ejemplo de uso del hook de disponibilidad.

## Pasos de Ejecución
1.  Leer el contenido actual de `docs/domains/module_scheduling.md` (ya realizado).
2.  Reescribir el archivo completo con la nueva estructura y contenido detallado.
3.  Verificar que los enlaces a archivos (Code References) sean correctos y funcionales.
