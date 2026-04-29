# Email Drip / Automation (MailerLite Bridge)

## Meta

| Campo | Valor |
|---|---|
| Slug | email-drip-mailerlite |
| Tier legacy | Tier 1C+1D |
| Estado | capturada — PI-2 |
| Owner módulo | campaigns + connections (MailerLite) |
| Última edición | 2026-04-29 |

## Job-to-be-done

> Como emprendedor, cuando un lead llega a un estado del lifecycle (suscriptor / MQL / customer / inactivo), quiero que **automáticamente** entre en una secuencia de emails, sin que yo lo agregue manualmente al grupo correcto en MailerLite.

## Dolor user

- Hoy MailerLite y Nicolify CRM están desconectados. Emprendedor agrega manual a grupos = no escala.
- Sin trigger automático = leads frescos no reciben welcome sequence, churn más rápido.

## Outcome deseado

- 7 trigger mappings automáticos lifecycle → MailerLite group:
  - SUBSCRIBER → "nuevos-suscriptores" → welcome sequence
  - MQL (score≥40) → "leads-calificados" → nurture
  - CUSTOMER → "clientes" + "compra-{oferta}" → onboarding
  - INACTIVO 14d → "reenganche" → re-engagement
  - webinar_attended → "asistio-webinar-{slug}"
  - webinar_no_show → "no-asistio-webinar-{slug}"
  - email_clicked (webhook ML→Nicolify) → JourneyEvent (+3 score)

## Solución elegida

`MailerLiteService` completar (hoy stub) + EMAIL_DRIP campaign type:
- `add_to_group(email, group_slug)` — POST /subscribers/{id}/groups
- `update_subscriber_field(email, field, value)` — PATCH
- `get_automation_status(email, automation_id)` — GET
- Lifecycle event handlers en `crm/` → call MailerLiteService.

## Webhooks MailerLite → Nicolify

- `email_opened` → JourneyEvent (+2 score)
- `email_clicked` → JourneyEvent (+3 score)
- `unsubscribed` → CustomerProfile.traits["mailerlite_subscribed"] = false
- `automation_step_sent` → log analytics

## Surface impactada

- BE: `connections/infrastructure/mailerlite_service.py` (existing stub → real)
- BE: `campaigns/application/services/campaign_orchestrator.py` — EMAIL_DRIP branch
- BE: `crm/application/services/lifecycle_event_handler.py` — 7 mappings
- BE: `connections/api/mailerlite_webhooks.py` — email events

## Riesgos

- MailerLite API rate limits (tier dependent). Mitigación: BudgetGuard / RateLimiter S0.3 cubre.
- Group naming convention: propuesta `nicolify:{tipo}:{slug}` para separar de grupos manuales del tenant.
- Tenant que NO tiene MailerLite conectado → feature gracefully degrades (skip sin error).

## Métricas

- # leads movidos a grupo automático / día
- Open / click rate de sequences disparadas por Nicolify trigger
- % tenants con MailerLite conectado (gate adoption)

## Cuándo

PI-2. Requiere S0 primitivas (BudgetGuard ya cuenta uso, ComplianceService no aplica directo).

## Links

- Research legacy: `docs/pm/campaigns/02-email-marketing/research.md`
- FOUNDATION: `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md` §FASE 5
