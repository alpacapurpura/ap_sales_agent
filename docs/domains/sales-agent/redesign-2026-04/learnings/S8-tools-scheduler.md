# Learnings · S8 · tools-scheduler

> Doc para S9. Si S9 sería igual de eficiente sin esta nota → sobra.

---

## Resumen (3 líneas)

- **Entregado**: 3 scheduling tools (`create_booking_link` con idempotency, `verify_booking_status`, `get_available_slots`) + `SchedulerProvider` Strategy + `InternalSchedulerProvider` impl + `WebhookProvider` Strategy con endpoint genérico registry-driven + `MeetingStateService` (SSoT JSONB) + 2 ARQ crons (verify_pending_bookings 15min + appointment_reminder_engine T-24h/T-1h/T+1h) + 3 Jinja templates con voz de marca + stage scoping `STAGE_TOOL_SCOPE` + 5 arch tests Strategy/anchors + 30 unit tests verde.
- **Decisión no obvia**: el plan v1 asumía Cal.com / Calendly como providers externos. Realidad: Nicolify TIENE su propio scheduler (`BookingLink` + `Appointment` + `AvailabilityService` integrando Google Calendar). Strategy pattern queda con 1 impl `InternalSchedulerProvider` hoy + Protocol + endpoint preparados para Cal.com / Calendly cuando llegue tenant real (NO stub vacío — YAGNI).
- **Listo para S9**: payment lifecycle puede mirror el mismo Strategy pattern (`PaymentProvider` Protocol + `MercadoPagoPaymentProvider` / `StripePaymentProvider` impls + webhook endpoint registry-driven). El `_resolve_signing_secret` env-var stub espera S9 para promoverlo a per-tenant config lookup en `connections.ChannelConnectionModel`.

---

## Decisiones clave

- **Strategy pattern con 1 impl real hoy vs 3 stubs (Cal.com / Calendly / GCal push)**:
  - Tomada: Protocol + `InternalSchedulerProvider` único + registry vacío para webhook providers.
  - Razón: research confirmó que Nicolify ya construyó su propio scheduler (BookingLink + AvailabilityService + book endpoint). Stubear Cal.com / Calendly sin tenant real introduce código muerto + tests inflados + riesgo drift contra API real cuando llegue.
  - Alternativa descartada: stubs vacíos para "validar pattern". Razón: Protocol + arch test cumplen el contrato sin código sin uso.

- **`MeetingStateService` como SSoT del JSONB vs múltiples mutadores**:
  - Tomada: 1 servicio owner — tools + workers + webhook handlers leen/escriben solo via `MeetingStateService`.
  - Razón: alta cohesión (1 lugar interpreta el shape), bajo acoplamiento (agregar `recording_url` toca un archivo), DRY (idempotency + serialization en un sitio).
  - Alternativa descartada: dict literal mutation desde cada caller. Razón: violación cohesión + bug-prone (forget `flag_modified` + race conditions).

- **`scheduled_meetings` JSONB en checkpoint vs tabla nueva `lead_meeting`**:
  - Tomada: JSONB column en `agent_state_checkpoints`.
  - Razón: 1-N por checkpoint (típicamente 1-3 entries activos), reads casi siempre cargan checkpoint anyway, append-only audit trail. Migration idempotente trivial.
  - Alternativa descartada: tabla `lead_meeting` con FK. Razón: scope creep — segundo modelo + repo + tests sin beneficio (queries cross-checkpoint son raras).

- **2 cron workers separados (verify + reminders) vs 1 worker monolítico**:
  - Tomada: separados, cadencia offset (verify on `:07/:22/:37/:52`, reminders on `:12/:27/:42/:57`).
  - Razón: cohesión semántica. `verify_pending_bookings` = reconciler puro (no LLM, no HTTP outbound). `appointment_reminder_engine` = generative (LLM call + ChannelResolver send). Acoplarlos mezcla concerns + dificulta tunear cadencias separadas.
  - Alternativa descartada: 1 worker que primero reconciles + después send. Razón: reminder failure no debe abortar reconciler. El offset de 5 min garantiza que los entries verificados están frescos cuando reminders los procesa.

- **Webhook endpoint genérico vs endpoint per-provider**:
  - Tomada: 1 endpoint `POST /webhooks/scheduler/{provider}` con dispatch via `webhook_provider_for(provider)`.
  - Razón: agregar Cal.com / Calendly = `register_webhook_provider(...)` en startup. Sin tocar el endpoint. Arch test bloquea inline branches.
  - Alternativa descartada: `/webhooks/scheduler/calcom`, `/webhooks/scheduler/calendly` separados. Razón: duplicación signature verify + parse + dedup + dispatch pipeline.

- **Brand voice via system prompt slot 5 (S7) vs prompt overrides per tenant**:
  - Tomada: reminder LLM call usa `prompt_cache_key=tenant_id` y hereda voz de slot 5 sin templates per-tenant.
  - Razón: SSoT consolidada en S7. Reminder template Jinja solo emite la **instrucción de qué decir**; el **cómo decirlo** viene del compilado de personality_profiles.
  - Alternativa descartada: `appointment_reminder_t24h_warm.j2` + `appointment_reminder_t24h_minimalist.j2`. Razón: explosión combinatoria 6 presets × 3 reminder kinds = 18 templates. Anti-DRY.

---

## Sorpresas / gotchas críticos

- **`BookingLink` model no declara `tenant_id` aunque la tabla prod sí lo tiene**: helper `create_personalized_booking_link` aceptaba `tenant_id` kwarg y lo pasaba al constructor → `TypeError` en runtime nuevo. Pre-S8 nunca surfaceó (uso indirecto). Fix temporal: helper descarta el kwarg con `_ = tenant_id  # reserved for parity`. DDD fix completo (declarar columna + migration normalizadora) → DEFERRED-S11.

- **SQLite test conftest** no preserva tz-aware en `DateTime(timezone=True)` columns. `_derive_status` comparaba `appointment_start` (naive desde SQLite) contra `now` (UTC-aware) → `TypeError can't compare offset-naive and offset-aware datetimes`. Fix: coerce a UTC-aware en helper antes de comparar grace. **Patrón general**: cuando un test fixture inserta un datetime tz-aware y el modelo lo reads back, validá con `.tzinfo` antes de comparar.

- **`AppointmentModel.summary` no es FK a event_slug** — es texto libre con título legible. `InternalSchedulerProvider._lookup_appointment` acepta `event_slug` como hint pero NO filtra. Heurística most-recent-by-lead funciona hoy (1 appointment activo por lead típico). Si crece a multi-event, agregar FK explícita. FLAGGED-S11.

- **Cross-module DDD violation arch test bloquea imports directos** desde `sales_agent` a `scheduling`. Solución: helpers extraídos a `shared/links/ports/scheduling.py` (`lookup_booking_link_by_token`, `lookup_latest_appointment_for_lead`, `list_event_type_slots`). Provider concreto importa solo del port. Pattern reusable para S9 (payment).

- **Logger stdlib vs structlog**: `logger.warning("msg", provider=...)` rompe stdlib (`unexpected keyword argument`). `test_consistent_logging` arch test bloquea `import logging` fuera de allowlist. Sales_agent debe usar `structlog.get_logger()` siempre.

---

## Recomendaciones accionables para S9

- [x] **Mirror Strategy pattern**: `PaymentProvider` Protocol + dataclasses (`PaymentLinkOutput`, `PaymentStatus`, `Refund`) + `MercadoPagoPaymentProvider` / `StripePaymentProvider` impls + registry `PAYMENT_PROVIDERS` + `payment_provider_for_tenant(db, tenant_id)`. NO branch on `provider_id` en tools.
- [x] **Webhook endpoint genérico** `POST /api/v1/sales-agent/webhooks/payment/{provider}` con `WebhookProvider` Protocol mirror — same dedup pattern (`payment_webhook_event` table con UNIQUE natural key). Reuse `_resolve_signing_secret` patrón (env-var stub hoy → tenant config lookup en S9 wiring).
- [x] **Reuse `MeetingStateService` pattern** para JSONB `payment_state` en checkpoint (entries con `link_created` / `pending` / `paid` / `failed` / `refunded`). Crear `PaymentStateService` análogo.
- [x] **Reuse `LLM_ROLE_BY_SITE['appointment_reminder_*']=NANO` mental model** para mensajes de payment (link enviado, pago confirmado, gracias). Brand voice from slot 5 hereda gratis.
- [x] **Reuse port pattern** — agregar `payment_provider_helpers` a `shared/links/ports/payment.py` para evitar cross-module imports directos a `enrollment` / payment models.
- [x] **NO crear webhook provider stubs vacíos**. Hasta que tenant real configure MP/Stripe, registry queda vacío + Protocol + endpoint listos.
- [x] **Stage scoping**: payment tools (`create_payment_link`, `verify_payment_status`, `grant_access`) — closing stage primarily. Update `STAGE_TOOL_SCOPE`.
- [x] **`grant_access` cron de retry** post-payment para casos race condition: payment confirmed pero grant_access falló (recurso external down). Idempotent + best-effort + max retries.
- [x] **Coordinar con S+1 FE** — tab Closer Studio mostrará tanto `scheduled_meetings` (S8) como `payments` (S9). Diseñar UI conjunto en S9 closeout.

---

## Hooks listos

- `backend/src/modules/sales_agent/application/tools/scheduling/providers.py::SchedulerProvider` — Protocol pattern reusable para PaymentProvider.
- `backend/src/modules/sales_agent/application/tools/scheduling/webhook_providers.py::WebhookProvider` — Protocol pattern reusable para inbound payment webhooks.
- `backend/src/modules/sales_agent/application/services/meeting_state_service.py::MeetingStateService` — pattern para `PaymentStateService`.
- `backend/src/modules/sales_agent/api/scheduler_webhooks.py::_persist_dedup` — pattern para `payment_webhook_event` dedup (idempotency natural key).
- `backend/src/modules/sales_agent/api/scheduler_webhooks.py::_resolve_signing_secret` — env-var stub pattern, promover a tenant config en S9.
- `backend/src/shared/links/ports/scheduling.py::{lookup_*, list_*}` — pattern para `shared/links/ports/payment.py`.
- `backend/src/modules/sales_agent/application/tools/registry.py::STAGE_TOOL_SCOPE` — agregar payment tools al closing stage.
- `backend/src/modules/sales_agent/workers/appointment_reminder_engine.py` — pattern para futuros workers `payment_reminder_engine` (link no usado T-24h, pago vencido).
- `backend/src/shared/domain/events.py::BookingLinkCreatedEvent`, `BookingMissedEvent` — pattern para `PaymentLinkCreatedEvent`, `PaymentReceivedEvent`, `PaymentFailedEvent`, `AccessGrantedEvent`.
- `.claude/rules/sales-agent-brand-voice.md` — voz de marca rule. Reminder templates ya respetan slot 5; payment templates deben respetar también.

---

## Riesgos abiertos

- **Cal.com / Calendly / GCal push notifications** sin impl concreta. Si tenant pide en S9 (raro pero posible), agregar provider impl + register en startup. Endpoint listo.
- **Multi-tenant signing secret** no resuelto (env var global). Cuando S9 wireé MP/Stripe per-tenant, generalizar `_resolve_signing_secret` a lookup en `ChannelConnectionModel.config`.
- **`BookingLink` tenant_id column**: prod tiene la columna pero el modelo SA no. Bug pre-existente — DEFERRED-S11. Si alguien add `tenant_id=...` al constructor antes del fix, romperá. Documentado en helper con `_ = tenant_id  # reserved for parity`.
- **Reminder timing windows** (±15 min) podrían skip o duplicar si el cron deriva. Hoy ARQ cadence es estable. Monitor post-deploy.
- **`AppointmentModel.summary` heurística** para resolver event_slug — multi-appointment por lead puede mismatch. FLAGGED-S11.

---

## Tech debt detectado (NO arreglado)

- [MEDIUM] `BookingLink` model sin `tenant_id` column → `05-tech-debt-log.md` (DEFERRED-S11).
- [LOW] AppointmentModel sin FK explícita event_slug → `05-tech-debt-log.md` (FLAGGED-S11).
- [LOW] Webhook signing secret env-var stub → `05-tech-debt-log.md` (DEFERRED-S9).
- [LOW] Closer Studio FE meetings tab → `05-tech-debt-log.md` (DEFERRED-S+1).
- [LOW] Reminder LLM temperature hardcoded 0.5 → `05-tech-debt-log.md` (FLAGGED).

---

## Fuentes research útiles

- [Cal.com API v2 docs · 2026-02-25 version] — confirmó booking endpoint POST /v2/bookings con custom metadata. Cambió: NO stubear sin tenant real (Cal.com cambia API muy seguido).
- [Calendly webhooks 2026 · developer.calendly.com] — invitee.created / invitee.canceled, signing key per webhook subscription. Cambió: WebhookProvider Protocol incluye `verify_signature(body, headers, secret)` con shape provider-específico.
- [Google Calendar push notifications · developers.google.com/workspace/calendar/api/guides/push] — channel expira 1 semana, requires manual renewal, payload no incluye event data (callback API). Cambió: GCal push es complejo (renewal cron + 2da llamada API) — diferido hasta tenant real.
- [HMAC webhook verification best practices 2026 · oneuptime.com / dev.to] — constant-time comparison + per-tenant secrets. Cambió: `_resolve_signing_secret` patrón env-var stub hasta config per-tenant.
- [SDR sales cadence 2026 · conquer.io / willbe.ai] — T-24h / T-1h reminders no son standard explícito pero best practice general. Cambió: ventanas ±15min sobre target time, postcheck T+30min..T+3h.

---

## Métricas medidas

- 30/30 unit tests S8 verde.
- 1121/1121 sales_agent + arch tests verde post-S8 (incluye 5 arch tests S8 nuevos).
- 0 ruff errors en S8 files (`src/modules/sales_agent/`, `src/shared/domain/events.py`, `src/shared/links/ports/scheduling.py`, `src/main.py`, `src/workers/settings.py`, tests S8).
- Migration 080 aplicada idempotente (clone + re-run = 0 changes).
- Tablas verificadas en prod: `agent_state_checkpoints.scheduled_meetings JSONB NOT NULL DEFAULT '[]'` + `scheduler_webhook_event` con UNIQUE `(provider, tracking_id, event_type, occurred_at)` + index `(tenant_id, received_at DESC)`.
- 4 ARQ cron jobs registrados en `scheduler_webhook_event` + workers `verify_pending_bookings` (`:07/:22/:37/:52`) + `appointment_reminders` (`:12/:27/:42/:57`).
