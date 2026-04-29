# Event Campaign / Launch Orchestration

## Meta

| Campo | Valor |
|---|---|
| Slug | event-campaign-orchestration |
| Tier legacy | Tier 1E |
| Estado | capturada — PI-3 |
| Owner módulo | campaigns + scheduling |
| Última edición | 2026-04-29 |

## Job-to-be-done

> Como infoproductor, cuando organizo un webinar o lanzamiento (1-4 al año, generan 60-80% de mi ingreso anual), quiero que **una secuencia multi-canal anclada a la fecha** corra sola: emails + WhatsApp + push, antes / durante / después del evento.

## Dolor user

- Hoy: emprendedor envía manualmente recordatorios D-7, D-1, D+0. Olvida pasos = pérdida directa de ingreso.
- Sin orquestación cross-canal: email lo manda en MailerLite, WhatsApp lo manda manual, push no existe.

## Outcome deseado

Template "launch-4day" o "webinar-sequence" → 1 frase a copilot ("lanza launch-4day para 15 mayo") → 9 steps disparan automático en canal correcto:

| Step | Offset | Canal | Mensaje |
|---|---|---|---|
| 1 | D-7 | email | "Se viene algo grande" |
| 2 | D-3 | email + WA | "Detalles + página de registro" |
| 3 | D-1 | email + WA | "Mañana es el día" |
| 4 | D+0 -1h | WA + push | "En 1h empieza" |
| 5 | D+0 +2h | email | "¿Cómo te fue?" + replay |
| 6 | D+1 | email | "Replay disponible 24h" |
| 7 | D+2 | email + WA | "Última oportunidad" |
| 8 | D+3 | email + WA | "Se cierra hoy" |
| 9 | D+4 | post-mortem | "Gracias + offer next" |

## Solución elegida

`EVENT_TRIGGER` campaign type + `CampaignStep[]` con `offset_hours`:
- `Campaign.anchor_event_date` = referencia.
- `CampaignStep` con `offset_hours` (negativo antes / positivo después).
- `CampaignSchedulerWorker` calcula `task.scheduled_at = anchor + offset`.
- Multi-canal: cada step declara `channel`, orchestrator rutea (Email→MailerLite, WA→Sales Agent, Push→OneSignal).
- Templates globales: `launch-4day`, `webinar-sequence`.

## Surface impactada

- DB: `campaign_steps` (idempotent, ver FOUNDATION §4 schema).
- BE: `campaigns/domain/campaign.py` — CampaignStep + EVENT_TRIGGER type.
- BE: `campaigns/workers/campaign_scheduler_worker.py` — scheduling math.
- BE: `campaigns/domain/template.py` — 5 templates (welcome, launch-4day, webinar, cold-reactivation, post-purchase).

## Riesgos

- Steps multi-canal requieren ChannelRouter completo (Telegram + WA + email + push) — esperar PI-2 multi-canal listo.
- Templates demasiado opinated → tenant con flow propio no encaja. Mitigación: customizable + clone pattern.
- Push opt-in requiere landing HTTPS dominio propio (decisión PI-3 dependencia tenant_domains).

## Métricas

- # eventos lanzados por tenant / mes
- Show-rate webinar (D+0 attendance) por campaña
- Revenue attributed a launch sequence
- Steps fallidos / steps total

## Cuándo

PI-3. Bloqueado por: PI-2 multi-canal + MailerLite + (parcial) push.

## Links

- Research legacy: `docs/pm/campaigns/03-otros-tipos/research.md` (launch-4day spec)
- FOUNDATION: `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md` §FASE 6
