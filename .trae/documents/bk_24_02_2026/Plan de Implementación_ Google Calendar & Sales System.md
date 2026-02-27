# Implementación de Integración Google Calendar y Sistema de Citas

Este plan detalla la arquitectura para integrar Google Workspace (Calendar) y crear un sistema de gestión de disponibilidad ("Calendly Clone") y visualización de ventas.

## 1. Backend: Integración Google Workspace y Servicios
### Dependencias
- Agregar `google-auth-oauthlib` y `google-api-python-client` a `backend/requirements.txt`.

### Arquitectura (Agentic Standard)
- **Adapter**: `backend/src/channels/google_calendar.py`
  - Implementación de `GoogleCalendarAdapter` para manejar la autenticación OAuth2 (Offline Access).
  - Métodos para generar URL de autorización e intercambiar `code` por tokens.
  - Wrapper sobre `googleapis` para `freebusy` y `events.insert` (con soporte Google Meet).
- **Service**: `backend/src/core/services/availability_service.py`
  - `get_available_slots`: Lógica de negocio para calcular huecos libres interseccionando horario laboral (configuración) con `freebusy` de Google.
  - `create_meeting`: Orquestación para crear evento, generar link de Meet y guardar metadatos (Lead ID).
- **API Router**: `backend/src/api/routers/calendar.py`
  - Endpoints OAuth: `/auth-url`, `/callback`.
  - Endpoints Funcionales: `/slots` (GET), `/book` (POST), `/appointments` (GET para vista de ventas).

### Persistencia
- Reutilizar modelo `ChannelConnection` (Postgres) con `channel_type='google_calendar'`.
- Almacenar tokens (access + refresh) de forma segura en la columna `credentials` (JSONB).

## 2. Frontend: Dashboard y Gestión
### Módulo Conexiones
- **Vista**: `frontend/src/components/connections/google-calendar-view.tsx`
  - Botón "Conectar Google Calendar" (OAuth flow).
  - Estado de conexión y botón "Desconectar".
  - Configuración básica (Horario laboral, duración de citas).
- **Integración**: Actualizar `frontend/src/app/(dashboard)/connections/page.tsx` para incluir el tab "Calendario".

### Módulo Ventas (Nuevo)
- **Página**: `frontend/src/app/(dashboard)/sales/page.tsx`
  - **Weekly Calendar View**: Componente personalizado (usando `date-fns` y CSS Grid) para visualizar citas de la semana.
  - **Lead Sidebar**: Reutilización de componentes existentes para mostrar detalle del Lead al hacer click en una cita.
  - Visualización de datos clave: Link de Meet, correo, fecha/hora.

### Módulo Availability (Configuración)
- Interfaz para definir "Tipos de Evento" (duración, nombre) y obtener el link único de reserva (Skeleton/Mock por ahora, funcional en backend).

## 3. Consideraciones Técnicas
- **Tipado**: Interfaces TypeScript estrictas para todos los DTOs (`Slot`, `Meeting`, `CalendarConfig`).
- **Manejo de Errores**: Retries automáticos para refresh tokens expirados.
- **UX**: Feedback visual durante la conexión y reserva.
