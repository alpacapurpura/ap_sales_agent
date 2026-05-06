# Source-Aware Treatment (Inbound diferenciado por origen)

## Meta

| Campo | Valor |
|---|---|
| Slug | source-aware-treatment |
| Tier legacy | Tier 1B |
| Estado | capturada — PI-1 Sprint 1+ |
| Owner módulo | sales_agent + crm + campaigns |
| Última edición | 2026-04-29 |

## Job-to-be-done

> Como emprendedor, cuando un lead me escribe primero (inbound), quiero que el Sales Agent **sepa de dónde vino** (qué anuncio, qué webinar, qué campaña) para tratarlo con contexto, no como genérico.

## Dolor user

- Hoy todo lead inbound entra al mismo flow de qualifier. Lead que vio webinar específico recibe mismo tratamiento que random visitor.
- Resultado: leads warm convierten 2-3x menos que cuando son tratados con contexto.

## Outcome deseado

- Lead con `source_campaign_id` → Sales Agent abre con "Vi que te interesó {oferta de la campaña}" — flow tratado con override.
- Sin source → flow genérico actual.

## Solución elegida

CRM extension + Sales Agent flow override:
- `CustomerProfile.source_campaign_id` (FK a campaigns) — first-touch, NUNCA sobreescribir.
- `CustomerProfile.source_ref` — UTM/ref param del primer toque.
- `CustomerProfile.source_ad_id` — Meta ad_id desde CTWA.
- ChatOrchestrator inbound: si `source_campaign_id` set → cargar `campaign.agent_instructions` como CAMPAIGN_CONTEXT slot.

## Captura del origen

- ManyChat: `ref` parameter del webhook `subscriber.new` (handler ya existe parcial, falta escribir a CRM).
- UTM landing: form submit → `CustomerProfile.source_ref = utm_campaign`.
- Meta CTWA: `entry_point.ad_id` desde webhook → `source_ad_id`.

## Surface impactada

- DB: `customer_profiles` ADD COLUMN `source_campaign_id`, `source_ref`, `source_ad_id` (idempotente).
- BE: `sales_agent/application/orchestrator/chat.py` — inbound branch lee source.
- BE: `connections/api/marketing_webhooks.py` — completar `_resolve_manychat_profile` con source capture.
- BE: `landing/` — form handler escribe source_ref.

## Riesgos

- First-touch attribution conflict si lead tocó múltiples campañas — convención: NUNCA sobreescribir, primer toque gana.
- UTM perdido si user llega vía link sin params — ok, fallback flow genérico.

## Métricas

- % leads inbound con source_campaign_id no-null
- Conversion rate de leads source-aware vs genérico (A/B)

## Cuándo

PI-1 Sprint 1 — capturable junto al dominio campaigns (campos en customer_profiles + handler ManyChat). Override flow Sales Agent → Sprint 3 con MVP 1.

## Links

- Research legacy: `docs/pm/campaigns/00-framework/campaign-types.md` §B + `architecture.md` "Source-Aware Treatment"
- FOUNDATION: `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md` §5.1
