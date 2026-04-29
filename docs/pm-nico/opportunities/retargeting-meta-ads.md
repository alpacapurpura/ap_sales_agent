# Retargeting CRM → Meta Ads

## Meta

| Campo | Valor |
|---|---|
| Slug | retargeting-meta-ads |
| Tier legacy | Tier 1F |
| Estado | capturada — PI-3 |
| Owner módulo | advertising + campaigns |
| Última edición | 2026-04-29 |

## Job-to-be-done

> Como emprendedor que ya pago en Meta Ads, quiero **subir un segmento de mi CRM** (ej: MQL sin convertir hace 30d, top 10% LTV customers) como Custom Audience o Lookalike, para que Meta no me cobre por encontrarlos genéricamente.

## Dolor user

- Hoy ads van a audiencia fría → 29% peor ROI vs custom audience CRM.
- Hasta 73% mejor ROAS con listas de alta calidad. Sin retargeting = quema presupuesto.
- Crear Custom Audience manual en Ads Manager = 15 pasos por export.

## Outcome deseado

1 frase a copilot ("exporta mi top 100 customers a Meta Ads como Custom Audience") → ejecuta:
- Resolve segment.
- Hash emails + phones (SHA-256 lowercase trimmed).
- POST Meta Marketing API `/customaudiences` + `/users`.
- Audiencia disponible en Ads Manager 5 min después.
- Bonus: crear Lookalike desde top customers (1-3% ratio LATAM).

## Solución elegida

`RETARGETING_EXPORT` campaign type en orchestrator + `MetaAdsService`:
- `meta_ads_service.create_custom_audience(name, ad_account_id)` — POST /customaudiences
- `meta_ads_service.upload_audience_members(audience_id, emails, phones)` — POST /users con SHA-256
- `meta_ads_service.create_lookalike(origin_audience_id, countries, ratio)` — POST /customaudiences (LOOKALIKE)
- `advertising/api/audience_exports.py` — POST + GET status

## Surface impactada

- BE: `advertising/application/services/meta_ads_service.py` (placeholder hoy → real)
- BE: `advertising/api/audience_exports.py` (nuevo)
- BE: `campaigns/application/services/campaign_orchestrator.py` — RETARGETING_EXPORT branch
- Copilot tool: `export_segment_to_meta(segment_id)`, `create_lookalike(audience_id)`
- FE: CRM Hub button "Exportar a Meta Ads" en vista segmento (PI-3)

## Riesgos

- Tenant sin Meta Business connected → feature gates closed. Verificar `connections/` Meta Ads scope.
- Hashing incorrecto → audiencia rechazada por Meta. Test exhaustivo lowercase + trim antes hash.
- Privacy: customer data sale del sistema. Audit log obligatorio (S2). Compliance check: opt-in del lead permite uso ad targeting.

## Métricas

- # audiencias exportadas / tenant / mes
- ROI ads con custom audience vs cold (A/B)
- Lookalike conversion rate

## Cuándo

PI-3. Requiere validar # tenants con Meta Ads ya connected (decisión pendiente data).

## Links

- Research legacy: `docs/pm/campaigns/03-otros-tipos/research.md` (retargeting section)
- FOUNDATION: `docs/pm/campaigns/05-arquitectura-agente/FOUNDATION.md` §FASE 8
