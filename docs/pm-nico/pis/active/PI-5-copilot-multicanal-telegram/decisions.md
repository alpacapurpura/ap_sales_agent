# PI-5 — Decisiones registradas

> Append-only durante PI. Owner: `/pm`. Captura razón, alternativas, fecha.

## D-PI5-001 — Bot global Nicolify único, NO per-tenant copilot

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | `@nicolify_copilot_bot` global (1 token env var). Cero per-tenant tokens copilot |
| Alternativas descartadas | A) per-tenant bot copilot — costo setup + onboarding fricción + escalabilidad 1000+ peor. B) compartir número con sales_agent — auth fragil, voz mezclada, leak risk |
| Razón | Pattern Linear/Notion. Auth limpio via magic link `chat_id`↔tenant. $0 incremental Telegram. Anti-cruce con sales_agent (sales_agent será per-tenant en su PI futuro) |
| Owner | Chris + /pm |

## D-PI5-002 — Sales_agent Telegram queda OUT OF SCOPE este PI

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | Sales_agent telegram bot (per-tenant, atiende leads + grupos venta) = PI separado futuro. PI-5 SOLO copilot |
| Razón | Scope cohesivo separado. Diferente identidad bot, diferente capa connection, diferente audiencia. Asegurar arquitectura no-cruce vía 2 webhooks distintos + arch fitness test |
| Owner | Chris + /pm |

## D-PI5-003 — Open + auth in-message

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | Bot accesible público. Sin link → response CTA hacia signup. Con link → copilot funcional |
| Alternativas descartadas | Closed (silencio sin link) — peor discovery, no CTA |
| Razón | Pattern industria. Sin leak (bot sin link no expone tenant data). Onboarding fricción menor |
| Owner | Chris confirma 2026-04-30 |

## D-PI5-004 — WhatsApp out of scope PI-5

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | WA queda futuro PI separado. PI-5 = Telegram only |
| Razón | Meta Cloud API limits + auth model distinto + costo número per-tenant. Mejor cohesivo Telegram first, capturar learnings, luego WA con base sólida |
| Owner | Chris confirma 2026-04-30 |

## D-PI5-005 — Switch sales_agent ↔ copilot = separación física por bot identity

| Campo | Valor |
|---|---|
| Fecha | 2026-04-30 |
| Decisión | Cero shared state. 2 bots distintos = 2 tokens = 2 webhooks. Telegram routing nativo asegura no cruce |
| Razón | Más simple que routing runtime ("este mensaje para quién"). Auth + voz + observabilidad limpios. Schemas separados (`copilot_channel_link` ≠ `sales_agent_channel_link`) |
| Mitigación edge case | Sales_agent bot detecta phone dueño → responde "andá a `@nicolify_copilot_bot`" con deep link |
| Owner | /pm 2026-04-30 |
