---
story_id: eval-foundation-tenant-seed-data
type: service-story
subtype: data-seeding
module: sales_agent
capability: sales-conversational-engine  # provides ground truth context for eval
estimate: 3-4d
priority: 1  # blocker absoluto post skill-audit
links:
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  pre_requisite: "../maintenance-skill-sales-agent-audit/checkpoint.md"
  consumers:
    - "../eval-foundation-simulator-homologation/"
    - "../sales-agent-personas-instrumented-runtime/"
    - "../sales-agent-goldens-3-tenants-dataset/"
    - "../sales-agent-voice-fidelity-grader-runtime/"
    - "../sales-agent-eval-pass-k-tracking/"
    - "../sales-agent-eval-cost-budget-cap/"
    - "../sales-agent-voice-fidelity-ci-gate/"
    - "../sales-agent-adversarial-jailbreak-suite/"
---

# Story — Eval Foundation A: 3 tenants seed con data realística completa

## Job-To-Be-Done

**Como** equipo eval (architect + dev-team + judges) que va a validar el sales_agent pre-launch
**Quiero** 3 tenants seed checked-in con data realística completa (brand identity + offer ladder + personality_profile + pricing + buyer_personas)
**Para** que el sales_agent corra sobre data NO mockeada, las simulaciones reflejen variedad real de mercado LatAm, y los judges puedan evaluar voice fidelity + tool trajectory + completeness contra ground truth concreto

## Por qué importa

Sin tenants seed con data realística, todo lo posterior (simulator, personas as simulators, goldens, graders, CI gate) es teatro:
- El agente no tiene a quién representar (sin `personality_profile` rico → voz genérica)
- No tiene qué vender (sin offer ladder → tool calls vacías)
- No tiene a quién atender (sin buyer_personas → personas simulator no calibran)
- Los judges no pueden gradear voice fidelity vs nada

Esta story es el FUNDAMENTO. Sin ella, las 8 stories siguientes son inalcanzables. Con ella, todas se destraban.

## Outcome esperado — 3 tenants seed (A1/A2/A3)

Cada tenant seed checked-in en `backend/tests/fixtures/eval/tenants/{archetype_slug}/` con estructura:

```
backend/tests/fixtures/eval/tenants/
├── tenant_coach_lat/                  # A1 — Visionarias-style
│   ├── brand.yaml                     # identity, visuals, story, strategy, positioning, narrative, brand_personality, communication_assets
│   ├── personality_profile.yaml       # SSoT system_instruction (compiler v2 6 bloques)
│   ├── offer_ladder.yaml              # 5 offers (lead-magnet → entry → core → community → high-ticket)
│   ├── pricing.yaml                   # PEN currency, all tiers
│   ├── buyer_personas.yaml            # 2-3 personas multi-archetype
│   ├── communication_assets.yaml      # podcast YouTube/Spotify, IG, lead magnets
│   └── README.md                      # rationale per data point + reference real
├── tenant_medico_dental/              # A2 — Dr/Dra/Dental con personal brand
│   ├── ... mismo schema
└── tenant_agencia_growth/             # A3 — Agencia influencer-CEO
    └── ... mismo schema
```

### Loaders + tests

- `backend/tests/fixtures/eval/tenants/loader.py` — función `load_eval_tenant(archetype_slug) → TenantContext` que mergea los YAMLs y produce un objeto consumible por `sales_agent` runtime sin tocar BD real
- `backend/tests/fixtures/eval/tenants/test_loader.py` — verifica que los 3 tenants cargan sin error, schemas válidos contra Pydantic models existentes (`brand.domain.models`, `offer.domain.models`, `personality_profiles.domain.*`)
- `backend/tests/fixtures/eval/tenants/test_realism_smoke.py` — smoke test: cada tenant tiene mínimo 5 campos no-null en cada YAML (no shells vacías)

### Capability link

- Story bumpea `capability: sales-conversational-engine` con campo `eval.seed_tenants_path: "backend/tests/fixtures/eval/tenants/"`

### A1 — `tenant_coach_lat` (Visionarias-style)

- Referencia real: https://visionarias.lat (PE / PEN, 2 founders)
- `brand.yaml`: identity humana cercana, mujeres founders, posicionamiento "comunidad de empresarias LatAm"
- `personality_profile.yaml`: voz emocional, voseo opcional según contexto cultural PE (voseo NO aplica PE — usar tuteo cálido per spanish-text.md), audio personalizado declarado en `audio_clone_planned: true`
- `offer_ladder.yaml`:
  - L0: lead magnet PDF "5 errores que cometes al emprender" (gratis)
  - L1: workshop online (PEN 49)
  - L2: curso "Visionaria emprendedora" (PEN 297)
  - L3: comunidad mensual Mighty Networks (PEN 89/mes)
  - L4: mentoría 1:1 (PEN 1,490)
- `pricing.yaml`: currency=PEN, todos los precios + IGV LatAm context
- `buyer_personas.yaml`: 2 personas — "emprendedora-frustrada" (25-35, busca propósito), "emprendedora-establecida" (35-45, busca escalar con red)
- `communication_assets.yaml`: podcast YouTube (https://www.youtube.com/@visionarias.oficial), podcast Spotify, IG, lead magnets

### A2 — `tenant_medico_dental` (Dr/Dra con personal brand)

- Referencias reales aggregate: dr.cardiometabolico, dr.juandiegovigo, dra.andreacuya, dentalindo
- Decisión Chris pendiente: ¿especialidad concreta? (cardio | dermato | dental | medicina interna). Sugerencia: **dental** (más volumen de leads + ticket medio + recurrencia clara) o **dermato** (visual fuerte en IG)
- `brand.yaml`: identity profesional cercana, lenguaje paciente-céntrico (NO "cliente"), authority medical strong
- `personality_profile.yaml`: voz profesional cálida, evita promesas absolutas (ético médico), incluye disclaimer médico en triggers específicos
- `offer_ladder.yaml`: consulta primera vez → tratamiento individual → paquete preventivo → control anual recurrente
- `pricing.yaml`: currency=PEN (o moneda según localización Chris confirme)
- `buyer_personas.yaml`: paciente-con-dolencia + paciente-preventivo + paciente-referido
- `communication_assets.yaml`: IG + TikTok según especialidad

### A3 — `tenant_agencia_growth` (Agencia influencer-CEO)

- Referencias aggregate: brander.studio, toga.pe, brandtech.pe
- Decisión Chris pendiente: ¿nicho concreto? (branding | growth | marketing tech). Sugerencia: **growth marketing** (casos de éxito más medibles + lenguaje ROI-driven)
- `brand.yaml`: identity influencer-CEO B2B, casos de éxito como motor, frameworks-based
- `personality_profile.yaml`: voz B2B confidente casual-pro, ROI-driven, frameworks references
- `offer_ladder.yaml`: lead magnet workshop → discovery call → propuesta → retainer mensual + servicios productized one-shot
- `pricing.yaml`: currency=PEN, ticket alto (PEN 2,000+ retainers)
- `buyer_personas.yaml`: emprendedor-establecido + agencia-buscando-tooling
- `communication_assets.yaml`: IG + LinkedIn + casos de éxito en website

## Antecedentes / Contexto

- **Origen:** discovery 2026-05-06 — Chris explicó que NO hay producción + reframe a synthetic-first
- **Stack:** read-only — escribe YAML + loader + tests. NO tocar `modules/sales_agent/{domain,application,api}/`
- **Stakeholder primario:** Chris (oracle de "qué tenant es realista para LatAm")
- **Skills que cargar:** `brand-expert` (schema brand.yaml), `offer-expert` (schema offer_ladder.yaml), `sales-agent-expert` (schema personality_profile.yaml — POST audit story 1)
- **Skills que NO cargar todavía:** ninguno extra
- **PII:** ninguna real — todos los datos son sintéticos basados en archetypes públicos. No hay riesgo de leak.
- **Spanish neutro:** README + system messages aplican. `personality_profile` puede tener voz tenant (excepción sales_agent voice).

## Out of scope (explícito)

- NO incluir tenants reales de prod (esa story va aparte cuando salgamos a prod)
- NO crear más de 3 archetypes en este sprint (Chris ratificó: "estos para empezar, luego agregamos más")
- NO build tooling para "agregar tenant nuevo" (esa story es `eval-foundation-tenant-seed-extension` futura, post-launch)
- NO simular conversaciones todavía — eso es story B (simulator-homologation)
- NO escribir personas as simulators todavía — eso es story C
- NO escribir goldens todavía — eso es story D
- NO seed BD real — solo YAMLs checked-in (loader produce TenantContext en memoria)

## Riesgos / Asunciones

- **Riesgo:** schemas Pydantic actuales (`brand.domain.models`, `offer.domain.models`) cambian post-merge → seed YAMLs invalidan. **Mitigación:** test `test_loader.py` corre en CI, falla rápido cuando hay drift.
- **Riesgo:** Chris no dispone de tiempo para curar los 3 tenants completos (3-4d trabajo + ~2-3h tuyas concentradas en review). **Mitigación:** `/po` redacta 01-spec con scope crystal-clear, build-team puede hacer drafts iniciales y Chris solo ratifica/ajusta.
- **Riesgo:** archetypes A2 y A3 ambiguos (Chris dijo "como"). **Mitigación:** `/po` lista en 01-spec las decisiones pendientes (especialidad médica concreta, nicho agencia concreto) como Q1/Q2/Q3 y pide ratificación antes de empezar build.
- **Asunción:** Visionarias.lat es referencia real explícita Chris ratificó (verificable visitando URL). Otros referencias son inspiraciones, NO copiar literal.

## Próximo paso

`→ Espera maintenance-skill-sales-agent-audit refined → /po lee 00-story + skill sales-agent-expert + brand-expert + offer-expert → redacta 01-spec.md service-story con scenarios:
  happy (3 tenants checked-in, loader carga los 3 sin error, schemas válidos),
  negative (YAML con campo requerido faltante → schema validation fail),
  edge (offer_ladder sin L0 lead magnet → ¿error o warning?),
  adversarial (datos PII reales detectados accidentalmente en YAML → pre-commit hook bloquea — defense in depth aunque seed sea sintético)`

Open questions para Chris previas a 01-spec:
- A2 especialidad concreta (dental | dermato | cardio | medicina general)
- A3 nicho concreto (branding | growth | marketing tech)
- Currency cross-tenant (¿los 3 en PEN o cada uno con su moneda local?)
- ¿Loader produce TenantContext in-memory o también seed BD vía fixture conftest?
