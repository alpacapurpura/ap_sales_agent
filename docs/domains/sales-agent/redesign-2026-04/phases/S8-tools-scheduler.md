# S8 · Tools: Scheduler integration

## Objetivo

Sales_agent puede **agendar reuniones**: genera link único per lead, trackea reserva, envía recordatorios automáticos pre-meeting, verifica asistencia post-meeting. Integración con módulo `scheduling` interno + (opcional) Cal.com / Google Calendar / Calendly externos.

## Dependencias

- S7 cerrado: agente habla voz de marca al ofrecer la cita.
- (Opcional) S6 ratchet — ayuda a no introducir tech debt durante expansion.

## Criterios de éxito

1. Tools nuevos en `sales_agent/application/tools/scheduling/`:
   - `create_booking_link(lead_id, duration_minutes, channel)` → URL única + `tracking_id`.
   - `verify_booking_status(tracking_id)` → `{status: pending|confirmed|attended|missed, when, ...}`.
   - `get_available_slots(tenant_id, days_ahead)` → solo si scheduler module expone.
2. Webhook IN del scheduler (o cron) actualiza `lead_state.scheduled_meetings` JSONB.
3. Cron `verify_pending_bookings_task` (ARQ) corre cada 15min — actualiza estados + emite domain event `BookingConfirmedEvent` / `BookingMissedEvent`.
4. Follow-up cadence extendida: `follow_up_engine` reconoce booking confirmado → schedules recordatorio T-24h + T-1h.
5. Post-meeting: cron T+1h pregunta "¿Cómo estuvo la reunión?" para verify atendido (consume CRM si scheduling marca attended) o pregunta directo al lead.
6. Closer Studio muestra meeting status per conversation.
7. Voz de marca respetada en mensajes generados (lee del slot 4).
8. Tools registrados en `tools/registry.py` + scoped por stage (e.g. solo en `discovery` o `closing`).
9. Tests cobertura completa.
10. Spanish neutro LATAM en mensajes default; respeta voz de marca tenant.

## Research mandate

### Queries WebSearch obligatorias

1. `Cal.com API booking link single-use lead tracking 2026` — verificar API vigente.
2. `Google Calendar API bookings appointment links 2026 authentication` — endpoints.
3. `Calendly API webhooks events scheduled canceled rescheduled 2026` — webhook shape.
4. `LATAM time zones meeting scheduling UX 2026` — zonas horarias múltiples.
5. `meeting reminder cadence sales SDR best practice 2026` — T-24h/T-1h vs otros patrones.

### Tessl tiles

- Si hay tile de scheduler integration → instalar.

### Lectura obligatoria

- Aprendizajes S7.
- `backend/src/modules/scheduling/` (entero) — qué expone.
- `backend/src/modules/connections/` — cómo se autentica con calendar providers.
- `backend/src/modules/sales_agent/workers/follow_up_engine.py`.
- `backend/src/modules/sales_agent/application/services/closer_studio_service.py`.
- `backend/src/modules/sales_agent/application/agents/sales/tools.py` — patrón `tool_check_schedule` actual.
- `.claude/rules/copilot-resilience.md` (módulo provider pattern aplicable).

### Hallazgos research

> COMPLETAR. **Validar qué provider scheduler tiene cada tenant** — Nicolify probablemente soporta múltiples (Cal.com, Google Calendar, Calendly). Strategy pattern requerido.

---

## Diseño

### Tool `create_booking_link`

```python
@tool
async def create_booking_link(
    lead_id: UUID,
    duration_minutes: int = 30,
    purpose: str = "discovery_call",  # mapea a event_type del scheduler
    channel: str | None = None,
) -> dict:
    """Crea link único para que el lead reserve una reunión.

    Returns:
        {
            "url": "https://cal.com/tenant/abc?lead=xyz&t=...",
            "tracking_id": "...",
            "expires_at": "...",
        }
    """
    tenant_id = get_tenant_id()
    scheduler = scheduler_provider_for_tenant(tenant_id)  # strategy
    booking = await scheduler.create_booking_link(
        lead_id=lead_id, duration_minutes=duration_minutes, purpose=purpose,
    )
    await lead_state_repo.append_meeting_link(
        tenant_id, lead_id, booking.tracking_id, booking.expires_at,
    )
    await event_bus.publish(BookingLinkCreatedEvent.create(...))
    return booking.as_tool_response()
```

### Strategy pattern para providers

```python
# src/modules/sales_agent/application/tools/scheduling/providers.py
class SchedulerProvider(Protocol):
    async def create_booking_link(...) -> Booking: ...
    async def verify_booking_status(tracking_id: str) -> BookingStatus: ...

class CalcomSchedulerProvider: ...
class GoogleCalendarSchedulerProvider: ...
class CalendlySchedulerProvider: ...

def scheduler_provider_for_tenant(tenant_id) -> SchedulerProvider:
    config = await connections_repo.get_scheduler_config(tenant_id)
    return PROVIDERS[config.provider]
```

### Webhook IN

```python
# src/modules/sales_agent/api/scheduler_webhooks.py
@router.post("/webhooks/scheduler/{provider}")
async def scheduler_webhook(provider: str, payload: dict, ...):
    parsed = PROVIDERS[provider].parse_webhook(payload)
    if parsed.event_type == "booking_confirmed":
        await event_bus.publish(BookingConfirmedEvent.create(
            tenant_id=parsed.tenant_id, lead_id=parsed.lead_id,
            tracking_id=parsed.tracking_id, scheduled_at=parsed.when,
        ))
    # idempotency via natural key (provider, tracking_id, event_type, occurred_at)
```

### Cron `verify_pending_bookings_task`

Actively poll provider para booking sin webhook visible (race / provider down). Idempotente.

### Follow-up cadence extension

```python
# follow_up_engine.py extension
@subscribes_to(BookingConfirmedEvent)
async def schedule_reminders(event):
    schedule_at(event.scheduled_at - timedelta(hours=24), task=send_reminder_t_24h, lead_id=event.lead_id)
    schedule_at(event.scheduled_at - timedelta(hours=1), task=send_reminder_t_1h)
    schedule_at(event.scheduled_at + timedelta(hours=1), task=verify_attendance)
```

### Mensajes con voz de marca

`send_reminder_t_24h` invoca `compose_system_prompt(state)` para slot 4 lighthouse → genera mensaje en voz del tenant.

### Stage scoping

Tools solo disponibles en stages:
- `create_booking_link`: `discovery`, `presentation`
- `verify_booking_status`: cualquier stage post-creación
- `get_available_slots`: `discovery` para discovery_call, `closing` para sales_call

---

## Plan TDD

### RED tests

1. `tests/modules/sales_agent/tools/scheduling/test_create_booking_link.py`:
   - Provider Cal.com: link generado con tracking_id único.
   - Lead state actualizado.
   - Event publicado.
   - Idempotencia: invocar 2x retorna mismo link si pendiente.

2. `tests/modules/sales_agent/tools/scheduling/test_verify_booking_status.py`:
   - Status pending / confirmed / attended / missed / canceled.

3. `tests/modules/sales_agent/api/test_scheduler_webhooks.py`:
   - Webhook Cal.com `booking.confirmed` → event published.
   - Idempotency: replay webhook 2x → solo 1 event.

4. `tests/modules/sales_agent/workers/test_verify_pending_bookings_task.py`:
   - Lead con booking pending + provider report confirmed → state updated.

5. `tests/modules/sales_agent/workers/test_follow_up_reminders_with_brand_voice.py`:
   - Mensaje generado contiene `summary_text` del tenant.
   - Spanish neutro default.

6. `tests/architecture/test_scheduler_provider_strategy.py`:
   - `PROVIDERS` dict con todos los providers.
   - Cada provider implementa `SchedulerProvider` Protocol.

---

## Implementación step-by-step

1. Define `SchedulerProvider` Protocol + dataclasses.
2. Implementar Cal.com provider primero (verificar API research).
3. Migración Alembic: tabla `lead_meeting` o JSONB en `agent_state_checkpoint.scheduled_meetings`.
4. Tools `create_booking_link`, `verify_booking_status` en `tools/scheduling/`.
5. Webhook handler con idempotency key.
6. Domain events.
7. ARQ task `verify_pending_bookings`.
8. Extender `follow_up_engine` para reminders.
9. Stage scoping en `tools/registry.py`.
10. UI Closer Studio: mostrar meetings.
11. Smoke test live: lead reserva en Cal.com sandbox → verificar evento + reminders.

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Provider auth tokens expiran | `connections` module ya maneja refresh — heredar. |
| Webhook spoof / replay | Signature verification por provider. Idempotency natural key. |
| Lead reserva 2x → 2 reminders | Idempotency del meeting check. |
| Time zone de tenant ≠ time zone de lead | Use `TenantLocale.timezone` para reminders. |
| Provider API lentos / down → bloquea turn | Tool tiene timeout 5s + structlog warning + fallback "intentá más tarde". |

---

## Tech debt watchpoints

- Si `scheduling` module no expone `create_booking_link` semantics → coordinar (NO crear shadow API).
- Si `follow_up_engine` está acoplado a un solo cadence → strategy pattern.
- Si Closer Studio FE no tiene "meetings" tab → loggear como tech debt (S+1).
- Si `connections` module no permite multi-provider per tenant → escalar.

---

## Ajustes vs plan original

> COMPLETAR.
