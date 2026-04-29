# TikTok DM Automation (Comment-to-DM)

## Meta

| Campo | Valor |
|---|---|
| Slug | tiktok-dm-automation |
| Tier legacy | Tier 1G |
| Estado | capturada — PI-2/3 (depende ManyChat TikTok config) |
| Owner módulo | connections + campaigns + sales_agent |
| Última edición | 2026-04-29 |

## Job-to-be-done

> Como creator LATAM que crece más rápido en TikTok que en IG, cuando alguien comenta una keyword en mi video, quiero que **automático** reciba un DM, entre a flow de qualification, y termine handoff a WhatsApp con mi Sales Agent.

## Dolor user

- TikTok creators LATAM crecen 3x más rápido que IG en 2025 (creator economy data).
- Comment-to-DM manual = imposible a escala. Pierde leads.
- ManyChat ya tiene capacidad TikTok (LATAM no bloqueado como UK/US).

## Outcome deseado

1. Creator publica video TikTok.
2. Comment con keyword ("QUIERO") en video.
3. ManyChat captura → auto-DM en TikTok.
4. Lead qualification flow (preguntas básicas).
5. Lead da número WhatsApp → handoff a Sales Agent.
6. CRM: lead aterriza con `source_campaign_id = "tiktok-{video-slug}"`, `source_channel = "tiktok-dm"`.

## Solución elegida

ManyChat TikTok integration (ya hay infra ManyChat, falta TikTok specific):
- `connections/` — agregar TikTok Business config alongside Instagram/Facebook.
- ManyChat webhook `tiktok_dm.received` → handler en `connections/api/marketing_webhooks.py`.
- Lead profile creation con source tracking (depende `source-aware-treatment.md`).
- Handoff a Sales Agent: ManyChat trigger envía WhatsApp con context.

## Surface impactada

- BE: `connections/` — TikTok Business OAuth (verificar si distinto de ManyChat ya existente).
- BE: `connections/api/marketing_webhooks.py` — TikTok DM webhook handler.
- BE: `crm/` — source tracking (cubierto por `source-aware-treatment.md`).
- Copilot: nada nuevo (provider ya conoce manychat).

## Riesgos

- TikTok API changes / approval flow para Business — validar # tenants ya con TikTok Business.
- Cross-channel handoff (TikTok DM → WhatsApp) requiere ManyChat flow setup en cada video keyword. Tenant fricción inicial.
- Compliance: TikTok DM no tiene 24h window pero sí policy contra spam. Rate limit S0.3 aplica.

## Métricas

- # comments → DMs / tenant / mes
- DM → WhatsApp handoff conversion
- Source-attributed conversion (compras con `source_campaign_id` TikTok)

## Cuándo

PI-2/3. Bloqueado por:
- Validar TikTok Business connection en `connections/` (data faltante).
- `source-aware-treatment.md` capturado (PI-1 Sprint 1).
- Multi-canal infra (PI-2).

## Links

- Research legacy: `docs/pm/campaigns/01-conversacional/research.md` + `docs/pm/campaigns/00-framework/campaign-types.md` §G
- FOUNDATION: `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md` (TikTok mention)
