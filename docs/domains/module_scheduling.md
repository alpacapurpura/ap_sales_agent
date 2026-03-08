# Módulo de Scheduling (Agendamiento) - Documentación para Agentes

> **CONTEXTO DEL AGENTE**: Este documento es la **FUENTE DE VERDAD** para cualquier tarea relacionada con la gestión de citas, calendarios, disponibilidad y reservas. Si necesitas saber cómo el sistema decide "cuándo" puede ocurrir una reunión o cómo se crea un link para un cliente, este es el lugar.
> **Advertencia**: Este módulo es la autoridad final sobre el tiempo. Otros módulos (Sales Agent, Landing Page) DEBEN consultar a este módulo, NUNCA intentar calcular disponibilidad por su cuenta.

## 1. Mapa de Código (The "Where")

> ⚠️ **Explorar el código directamente** — no confíes en inventarios de archivos que pueden estar desactualizados.

- **Backend**: `backend/src/modules/scheduling/`
  - Dominio (`EventType`, schemas de disponibilidad): `domain/`
  - Modelos SQL (`appointments`, `booking_links`): `infrastructure/models/`
  - Servicio de cálculo de slots disponibles: `application/services/`
  - Endpoints internos (CRUD citas), públicos (reserva anónima por token), configuración (event types): `api/`
  - Adaptador de Google Calendar: `backend/src/modules/connections/infrastructure/channels/` (buscar `google_calendar`)
- **Frontend**:
  - Componentes de UI del dashboard: `frontend/src/features/sales/`
  - Clientes API (slots, booking links): `frontend/src/lib/api/`
  - Página pública de reserva (vista del lead): `frontend/src/app/(main)/book/`

## 2. Lógica de Negocio (The "Why" & "How")

### Estrategia de Almacenamiento Híbrido
- **Citas (SQL)**: Las citas confirmadas necesitan integridad referencial con `Leads` y búsquedas rápidas por rango de fechas, por eso viven en Postgres (`appointments`).
- **Configuración (JSONB)**: Los `EventTypes` (ej. "Demo 30min", "Onboarding") cambian frecuentemente y varían por tenant. Guardarlos en `Tenant.config_json` permite iterar la estructura sin migraciones de DB.

### Flujo de Reserva (Booking Flow)
1.  **Solicitud de Disponibilidad**: El cliente (Front o Agente) pide slots para un `event_type_id` y un rango de fechas.
2.  **Cálculo (AvailabilityService)**:
    - Recupera reglas del `EventType` (duración, horario laboral).
    - Consulta `GoogleCalendar` para obtener "busy slots".
    - Resta "busy slots" del horario laboral -> Retorna `AvailableSlots`.
3.  **Intento de Reserva**:
    - Se valida el token (`public_token` o auth de usuario).
    - Se verifica *atómicamente* que el slot siga libre.
4.  **Confirmación**:
    - Crea evento en Google Calendar (obtiene link de Meet).
    - Guarda `Appointment` en DB local con el `google_event_id`.
    - Dispara notificaciones (Email/WhatsApp).

### Reglas Críticas
- **Agnosticismo**: El módulo de scheduling NO sabe de "Ventas" o "Soporte". Solo entiende de "Bloques de Tiempo" y "Participantes".
- **Verdad Externa**: Google Calendar es la fuente de verdad final para la disponibilidad "ocupada". Nuestra DB es la fuente de verdad para la metadata del negocio (quién es el lead, notas, etc.).

---

## 3. Integraciones y Contratos
-  Tenemos endpoints en `api/v1/scheduling/public/...`.
-  Requiere un `token` válido que represente el contexto (usualmente el `slug` del tenant y del evento).
-  No puede acceder a datos privados del tenant, solo a slots disponibles anonimizados.
- **Consultar**: El nodo usa `AvailabilityService.get_slots(start_date, end_date)` para obtener opciones textuales.
- Para revisar, fecha y hora exacta a reservar `AvailabilityService.book_meeting(...)`.
---

## 4. Casos Borde y Gotchas (Edge Cases)

- **Timezones (La Pesadilla Eterna)**:
  - **Entrada**: El frontend/agente siempre debe enviar fechas en ISO 8601 con offset o UTC explícito.
  - **Procesamiento**: `AvailabilityService` convierte todo a UTC para comparaciones.
  - **Salida**: La API devuelve slots en UTC. El frontend es responsable de formatearlo a la zona horaria del navegador del usuario.
- **Double Booking (Colisión)**:
  - Existe una ventana de milisegundos entre "ver el slot" y "reservar".
  - **Solución**: El método `book_meeting` debe manejar excepciones de Google Calendar o usar bloqueos optimistas. Si Google rechaza, fallamos gracefully: "Lo siento, ese horario acaba de ser tomado".
- **Tokens Expirados**:
  - Los `BookingLinks` pueden tener TTL (Time To Live). Si un agente genera un link hace 24 horas, puede ya no ser válido. Siempre verificar validez antes de renderizar la UI.

---

## 5. Snippets para Agentes (Common Tasks)

### Backend: Verificar disponibilidad manualmente
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
from src.modules.scheduling.application.services.availability_service import AvailabilityService
from datetime import datetime, timedelta

# Inyectar dependencias (asumiendo contexto de DI)
service = AvailabilityService(calendar_adapter=..., repository=...)

# Buscar slots para los próximos 7 días
start_date = datetime.utcnow()
end_date = start_date + timedelta(days=7)

slots = await service.get_available_slots(
    tenant_id="tenant_123",
    event_type_slug="demo-call",
    start_date=start_date,
    end_date=end_date
)
# slots es una lista de objetos datetime en UTC
```

### Backend: Generar un Link de Reserva Único
```python
# ⚠️ Verificar nombres exactos de clases/métodos en el código real antes de usar
from src.modules.scheduling.infrastructure.models.booking_link import BookingLink

# Crear link para un lead específico
link = BookingLink(
    tenant_id="tenant_123",
    lead_id="lead_456",
    event_type_id="evt_789",
    expires_at=datetime.utcnow() + timedelta(hours=24)
)
# Guardar en DB y generar URL
url = f"https://app.visionarias.ai/book/{link.token}"
```

### Frontend: Hook para obtener Event Types
```typescript
// ⚠️ Verificar nombres exactos de componentes/hooks en el código real antes de usar
import { useEventTypes } from '@/lib/api/event-types';

export function BookingSelector() {
  const { data: eventTypes, isLoading } = useEventTypes();

  if (isLoading) return <Spinner />;

  return (
    <ul>
      {eventTypes.map(evt => (
        <li key={evt.id}>
          <button onClick={() => selectEvent(evt.slug)}>
            {evt.title} ({evt.duration} min)
          </button>
        </li>
      ))}
    </ul>
  );
}
```
