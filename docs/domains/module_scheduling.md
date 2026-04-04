---
module: Scheduling
status: active
---

# Scheduling

Gestiona disponibilidad, citas y reservas. Es la autoridad final sobre el tiempo: otros modulos (Sales Agent, Landing) consultan aqui, nunca calculan disponibilidad por su cuenta.

## Domain Concepts

- **EventType**: Configuracion de un tipo de reunion (duracion, horario). Se almacena en `Tenant.config_json`, no en tabla propia, para iterar sin migraciones.
- **AvailabilitySchedule**: Horario laboral semanal con timezone. Tambien vive en `config_json`.
- **Appointment**: Cita confirmada en Postgres (integridad referencial con Leads).

## Architecture Decisions

- **Google Calendar = fuente de verdad para "ocupado"**. Nuestra DB es fuente de verdad para metadata de negocio (lead, notas, contexto del deal).
- **Almacenamiento hibrido**: Citas en SQL (queries por rango de fechas), configuracion en JSONB (iteracion rapida sin migraciones).
- **Agnosticismo de dominio**: El modulo no sabe de "ventas" ni "soporte". Solo entiende bloques de tiempo y participantes.

## Business Rules

- Todas las comparaciones de slots se hacen en UTC; el schedule define timezone local que se convierte internamente.
- El frontend/agente DEBE enviar fechas en ISO 8601 con offset o UTC explicito.
- La API devuelve slots en UTC; el frontend formatea a la zona horaria del navegador.
- `book_meeting` verifica atomicamente que el slot siga libre contra Google Calendar. Si Google rechaza, falla gracefully.
- Los `BookingLink` pueden tener TTL; siempre verificar validez antes de renderizar.

## Edge Cases

- **Double booking**: Ventana de milisegundos entre ver slot y reservar. La unica defensa es la verificacion contra Google Calendar al momento de crear el evento.
- **Legacy schedule migration**: Existe `_migrate_schedule_structure` que convierte formatos antiguos (`weekly_hours` -> `schedule`, `is_active` -> `active`, `slots` -> `ranges`). Si falla, se omite silenciosamente el schedule corrupto.
- **Calendar no conectado**: Si no hay Google Calendar activo, `get_available_slots` retorna todos los slots del horario sin restar busy periods.

## CRITICAL -- Do Not Violate

- Nunca calcular disponibilidad fuera de `AvailabilityService`. Otros modulos DEBEN consumir este servicio.
- Toda cita en DB debe tener `tenant_id`. Sin excepcion.
- El `google_event_id` vincula la cita local con Google Calendar; perderlo rompe la sincronizacion.
