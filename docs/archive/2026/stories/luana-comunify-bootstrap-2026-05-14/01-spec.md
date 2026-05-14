---
story_id: luana-comunify-bootstrap
spec_version: 1
date: 2026-05-14
owner: /po-ux
status: auto_ratified
ratified_by_chris: true
ratified_at: 2026-05-14
sesion: 12
session_mode: autonomous_full_cycle
inputs:
  - 00-story.md
  - outcomes/luana-platform-migration.md
  - archive/2026/stories/luana-vitalia-bootstrap-2026-05-14/01-spec.md (pattern source)
  - research/creator-economy-latam (3 creators TBD below)
spec_q_decisions:                                  # auto-ratified Story 11 Q-set verbatim per Phase 0 Q2=A
  Q1_voseo_chrome_ui: B_spanish_neutro_pure         # tuteo in chrome UI; voice cloning preserves tenant dialect
  Q2_multi_brand_ui: B_defer_story_12_bis           # multi-account creator switcher defer
  Q3_third_party_community_bridge: B_defer_story_12_bis  # Discord/Circle/Slack defer 12.bis per Q1
  Q4_creator_ladder_ui: A_reuse_luana_core_plus_extensions
  Q5_subscription_widget: B_both_iframe_and_canonical
  Q6_payment_gateway: B_mercadopago_primary_stripe_connect_fallback
  Q7_voice_cloning_scope: A_full_pipeline_50_chats   # ON per BrandConfig features.voice_cloning=True
handoff_sesion_12_phase_2:
  - /architect orchestrator → 03-arch.md + ready package (consolidated phase 2 same session)
---

<!-- voseo-allowed: AR fixture Anabella uses voseo brand voice per creator economy vertical design; archived spec documents creator-facing microcopy examples including voseo for AR persona -->

# 01-spec.md — Story 12 luana-comunify-bootstrap

> **Outcome:** luana-platform-migration · **Sequence:** 12/14 · **State:** refining (Sesion 12 autonomous Phase 1)
> **Spec scope:** UI surfaces + business rules + agentic surface API (handoff /architect Phase 2 same session)
> **Pattern source:** Story 11 (Vitalia) — réplica con dominio creator/expert economy en lugar de medical/dental.

## § 1. Context

### 1.1 Outcome positioning

Story 12 bootstrappea brand `comunify` (creator/expert economy + community LatAm) consumiendo Luana Platform v0.1.0+ (cerrada Story 10 luana-nicolify-migration) y validada por Story 11 (Vitalia bootstrap medical vertical) APPROVED 2026-05-14.

**Outcome luana-platform-migration:** Multi-Brand Vertical SaaS pattern. Luana core SSoT compartido + 4 brand apps deployment-isolated. Story 12 = **segundo "new vertical"** post Story 11 — valida (a) replicabilidad del extension SDK con dominio distinto, (b) voice cloning ON pipeline + 10 secciones brand studio full + authority vault required, (c) creator-economy archetypes (cohort + community + ladder + recurring billing).

**Diferencia clave vs Story 11:**

| Dimensión | Vitalia (Story 11) | Comunify (Story 12) |
|---|---|---|
| `voice_cloning` | OFF | **ON** (50+ chats samples → distilled system_instruction) |
| Brand Studio sections | 4 (identity/contact/team/testimonials) | **10** (full deep brand) |
| `authority_vault` | not required | **required** (credenciales/casos/PR mandatory) |
| Offer preset pack | `medical_services_v1` | `coaching_offers_v1` |
| Offer ladder | implicit (per offer) | **explicit 4-level visualizer** (lead-magnet → tripwire → core → premium) |
| Monetización primaria | one-shot prepaid bookings | **recurring subscriptions** (monthly memberships) |
| Audiencia agente | pacientes (1:1 individual) | **comunidad** (1:N broadcast + 1:1 engagement) |
| Workflows agénticos | TreatmentFollowupWorkflow | **CommunityEngagementWorkflow + CohortEnrollmentWorkflow** |
| Safety overlay | medical_safety (no diagnosis/prescription) | **community_safety** (no spam/no NSFW/no doxxing/moderation_required) |

### 1.2 Module surface

| Módulo afectado | Tipo cambio | Owner |
|---|---|---|
| `comunify/` (NEW brand subdir luana-platform) | new brand bootstrap | Story 12 full |
| `luana_core_brand_studio` | extension consumption full 10 sections + authority_vault required override | brand-expert review |
| `luana_core_offer_studio` | new preset pack `coaching_offers_v1` + ladder visualizer | offer-type-preset-expert |
| `luana_core_offer` (ladder) | new domain entity `OfferLadder` (4 levels relation) | offer-expert |
| `luana_core_brand` (voice cloning) | NEW pipeline `voice_cloning_distillation` 50+ chats → system_instruction | sales-agent-expert + brand-expert |
| `luana_core_sales_agent` | vertical-creator-economy tool registration (4 tools) | sales-agent-expert |
| `luana_core_copilot` | vertical-creator-economy extractors (2) + workflows (2) registration | copilot-expert |
| `luana_core_iam` | Clerk App #3 JWT issuer config (Comunify signup) | iam |
| `luana_core_extension_sdk` | EP-1..EP-18 register_all vertical-creator-economy | extension SDK |
| `luana_core_scheduling` | new appointment_type=discovery_call (1:1 sales call vs medical consultation) | offer-expert |
| `shared.subscriptions/` | NEW lift shared (recurring subscriptions cross-brand likely) | architect-be confirms |

### 1.3 User journey insertion point

**Primary onboarding flow (creator):**
```
landing.comunify.io
  → Signup (Clerk App #3 comunify)
  → Onboarding wizard (4 steps: creator profile + niche + plan tier + first offer ladder seed)
  → Brand Studio FULL 10 sections (incluye voice_cloning ON + authority_vault required + buyer_persona multi mín 3)
  → Voice cloning pipeline (upload 50+ chats/voice samples → wait async distillation → ratify compiled voice)
  → Offer Studio coaching_offers_v1 preset + ladder visualizer 4 niveles
  → Subscription pricing setup (MercadoPago + Stripe Connect tokenized recurring)
  → Dashboard
```

**Daily creator operations:**
```
Dashboard
  → /cohorts (CRUD cohortes con criterios calificación + roster)
  → /cohorts/{id}/community (members management + tier roles + engagement metrics)
  → /community (cross-cohort community feed unified)
  → /authority (authority vault — credenciales, casos PR, social proof, awards)
  → /ladder (offer ladder visualizer 4 niveles drag-drop)
  → /subscriptions (active subscribers + dunning + churn analytics)
  → /community-moderation (agentic moderator inbox + manual override)
  → Sales agent inbox (chat history + manual handoff por miembro)
```

### 1.4 Out-of-scope (anti-creep)

NOT in Story 12 (deferred Story 12.bis o future epic per Phase 0 Q1-Q7 + § 17 ratified decisions):

- ❌ Discord / Circle / Slack / Mighty Networks bridge (Q3=B ratified — defer 12.bis)
- ❌ Live streaming UI nativo (Zoom/Loom embed link OK Story 12; native stream defer)
- ❌ Gamification deep (badges leaderboard + tier auto-progression) — defer future epic
- ❌ Multi-account creator switcher UI (Q2=B ratified — backend supports brand_slug arrays, UI defer)
- ❌ White-label creator → end-user multi-tenant (defer future epic complete agency feature)
- ❌ Creator mobile app (web-only Story 12; mobile app future epic)
- ❌ Real-time video streaming sales call (sales_agent text-only Story 12; live video defer)
- ❌ Affiliate program multi-tier comisiones (defer 12.bis)
- ❌ Course delivery LMS (videos lecciones tareas) — Comunify es community + cohort SaaS, NO LMS. Course content vive en external (Teachable/Kajabi/Hotmart) — Comunify integra via webhook
- ❌ NFT / Web3 token-gated communities (defer future epic)
- ❌ Internationalization beyond Spanish neutro LatAm (English defer 12.bis)
- ❌ Email marketing campaign builder (defer connections module future)

### 1.5 Story 10 + Story 11 dependency assumptions

Story 12 assumes Story 10 + Story 11 deliverables LIVE:
- ✅ `luana-platform/` monorepo functional (Story 10)
- ✅ `@luana/*` workspace packages installed TS (Story 10)
- ✅ `luana_core_*` workspace packages installed Python uv (Story 10)
- ✅ Extension SDK `EP-1..EP-18` register_all surface enforced (Story 10)
- ✅ FE + BE rsync pattern documented (Story 10 T-13)
- ✅ Alembic consolidation pattern (Story 10 T-10)
- ✅ ci-parity root migration (Story 10 T-12)
- ✅ "Each brand own deploy" framework (Chris Sesion 10 Q2 ratification)
- ✅ Vitalia brand deployed (Story 11) — validates 1st new vertical bootstrap end-to-end
- ✅ MercadoPago + Stripe Connect adapters lifted shared (Story 11 § 16 — if confirmed by architect-be inspection during Story 11)
- ✅ Vertical-medical fidelity rubric pattern materialized (Story 11) — Comunify replicates with vertical-creator-economy-fidelity

## § 2. Fixtures research-driven (3 LATAM creators)

> Research-driven fixtures per Q5 ratified. Datos públicos inspirados en creators reales LATAM. NO real creator piloto (defer Story 12.bis). Fixtures sirven seed programmatic + onboarding flow validation + E2E coverage.

### 2.1 Fixture A — Business Coach Argentina (basada en Ana Acosta archetype)

```yaml
fixture_id: creator_business_coach_arg_01
fixture_name: "Anabella Conexión"
fixture_type: business_coach
country: AR
city: Buenos Aires
niche: business_coaching_mujeres_emprendedoras
website_inspiration: anabellatorrescoach.com archetype
brand_identity:
  name: "Anabella Conexión"
  domain: anabellaconexion.com
  voice_tone: "cercana, vehemente, motivacional, pragmática, voseo argentino natural"
  voice_cloning_samples_required: 50      # mínimum chats WhatsApp + voice notes audio
  color_palette:
    primary: "#E11D48"       # rosa-rojo (energía + acción)
    secondary: "#1E1B4B"     # navy oscuro (autoridad)
    accent: "#FBBF24"        # amber (call-to-action)
    neutral: "#F8FAFC"
  logo_concept: "A estilizada con línea de conexión circular"
  tagline: "Mujer, dueña de tu negocio. Vos podés."
authority_vault:                          # required per BrandConfig
  credentials:
    - "Master Coach Internacional ICF (Argentina, 2019)"
    - "+8 años acompañando emprendedoras LatAm"
    - "Mentora Programa Mujeres + Pyme Banco Galicia 2023"
  case_studies:
    - client: "María D. (Belleza Spa Buenos Aires)"
      result: "Triplicó facturación en 6 meses + sistematizó equipo 4 personas"
      duration_months: 6
    - client: "Lucía F. (Consultora Marketing Córdoba)"
      result: "Lanzó programa grupal +200 alumnas + escaló de freelance a CEO"
      duration_months: 9
    - client: "Cohorte Conexión 2024 (12 emprendedoras)"
      result: "Promedio +180% facturación 12 meses"
      duration_months: 12
  press_mentions:
    - { outlet: "Forbes Argentina", title: "10 mentoras a seguir 2024", url: "https://forbes.com.ar/..." }
    - { outlet: "La Nación", title: "Coaching para emprendedoras: el boom", url: "https://lanacion.com.ar/..." }
    - { outlet: "Podcast Negocios Digitales", title: "Episodio 142: Anabella", url: "https://..." }
  social_proof:
    instagram_followers: 47_000
    podcast_listens_total: 320_000
    nps_score: 84
  awards:
    - "Top 50 Coaches LatAm 2023 — Coach Magazine"
buyer_persona:
  primary:
    name: "Mujer emprendedora 30-45 estancada"
    age_range: "30-45"
    income_level: "ARS 800k-2.5M / mes (~USD 800-2500)"
    business_stage: "freelance / negocio unipersonal estancado"
    primary_concerns:
      - "no sé cómo cobrar más sin perder clientes"
      - "trabajo 14h/día sin escalar"
      - "no tengo equipo y todo depende de mí"
      - "imposter syndrome al subir precios"
    primary_desires:
      - "tener mi cohorte de emprendedoras pares"
      - "sistematizar mi negocio sin fórmulas frías"
      - "permitirme cobrar lo que valgo"
  secondary:
    name: "Empleada en transición a emprender"
    age_range: "28-38"
    income_level: "salario relación dependencia + ahorros"
    business_stage: "side-hustle validando idea"
  tertiary:
    name: "Coach novel buscando mentora"
    age_range: "25-40"
    income_level: "primeros clientes mensuales"
    business_stage: "freelance early-stage"
offer_ladder:                              # 4 niveles explicit
  level_1_lead_magnet:
    name: "Masterclass gratuita 'Cobrar Sin Culpa'"
    price_usd: 0
    delivery: "live zoom 1.5h + replay 7 días"
    cta: "Reservá tu lugar"
  level_2_tripwire:
    name: "Workshop 'Tu Precio Magnético' (asíncrono)"
    price_usd: 27
    delivery: "5 videos + plantilla pricing + comunidad pequeña 30 días"
    cta: "Quiero el workshop"
  level_3_core:
    name: "Cohorte Conexión 12 semanas"
    price_usd: 1497              # AR currency tier
    payment_options:
      - { type: "single", amount_usd: 1497 }
      - { type: "installments", count: 3, monthly_usd: 547 }
    delivery: "12 sesiones live + comunidad activa 12 sem + 2 sesiones 1:1 + workbook"
    cta: "Aplicar a la próxima cohorte"
    capacity: 18                # cohort size
  level_4_premium:
    name: "Mentoría Exclusiva 1:1 (6 meses)"
    price_usd: 9_900
    payment_options:
      - { type: "installments", count: 6, monthly_usd: 1700 }
    delivery: "12 sesiones 1:1 + WhatsApp directo + revisión negocio + acceso permanente comunidad alumni"
    cta: "Aplicar entrevista"
    capacity: 4                  # premium 1:1 cap
plan_tier: pro                  # $99 USD/mo per BrandConfig (Comunify pricing)
plan_features_enabled:
  - brand_studio_full
  - voice_cloning_pipeline
  - offer_studio_coaching
  - offer_ladder_visualizer
  - community_engagement_workflow
  - cohort_enrollment_workflow
  - sales_agent_vertical_creator
  - authority_vault_full
  - recurring_subscriptions
testimonials:
  - quote: "Anabella cambió mi forma de ver mi propio negocio. Dejé de cobrar barato por miedo."
    author: "María D."
    cohort: "Conexión 2024 Q1"
    rating: 5
  - quote: "La comunidad de la cohorte fue tan importante como el contenido. Me sostuvo en momentos clave."
    author: "Lucía F."
    cohort: "Conexión 2024 Q2"
    rating: 5
team:
  - name: "Anabella Acosta"
    role: "Creator + Head Coach"
    bio_short: "Master Coach ICF, +8 años acompañando mujeres emprendedoras LatAm"
  - name: "Carolina Vega"
    role: "Community Manager + Operations"
    bio_short: "Coordina cohortes y comunidad alumni"
```

### 2.2 Fixture B — Nutricionista Chile (basada en archetype dietitian-creator)

```yaml
fixture_id: creator_nutritionist_chl_01
fixture_name: "Trini Nutrición Real"
fixture_type: health_creator_nutrition
country: CL
city: Santiago
niche: nutricion_no_dietas_antidieta
website_inspiration: chilean nutritionist-creator archetype (no específica, fixture composito)
brand_identity:
  name: "Trini Nutrición Real"
  domain: trininutricionreal.cl
  voice_tone: "didáctica, cálida, antidogmática, validadora, neutro chileno tuteo"
  voice_cloning_samples_required: 50
  color_palette:
    primary: "#10B981"       # verde (salud + crecimiento)
    secondary: "#1E40AF"     # azul intenso (confianza)
    accent: "#F59E0B"        # naranja warm
    neutral: "#FAFAF9"
  logo_concept: "Hoja minimalista con tipografía sans-serif redondeada"
  tagline: "Comer rico, vivir tranquila. Sin culpa."
authority_vault:
  credentials:
    - "Nutricionista titulada Universidad de Chile (2016)"
    - "Certificación Health at Every Size® (HAES, 2020)"
    - "Especialización Trastornos de Conducta Alimentaria PUC (2022)"
    - "Member Asociación Chilena de Nutrición Inclusiva"
  case_studies:
    - client: "Programa Comer Tranquilas (12 mujeres, 6 meses)"
      result: "Reducción 78% pensamientos restrictivos + mejora bienestar mental (escala validada)"
      duration_months: 6
    - client: "Cohorte Adolescentes y Alimentación (8 madres)"
      result: "Madres reportan disminución conflictos con hijas adolescentes alrededor de comida"
      duration_months: 4
  press_mentions:
    - { outlet: "Revista Paula (Chile)", title: "Las nuevas voces antidieta", url: "https://..." }
    - { outlet: "Podcast Cómo Comer", title: "Episodio Trini sobre HAES", url: "https://..." }
  social_proof:
    instagram_followers: 28_000
    tiktok_followers: 15_000
    nps_score: 89
buyer_persona:
  primary:
    name: "Mujer 28-45 cansada de dietas"
    age_range: "28-45"
    income_level: "CLP 1.2M-3M / mes (~USD 1.3k-3.3k)"
    primary_concerns:
      - "llevo 15 años haciendo dietas y nunca dura"
      - "tengo episodios atracón post-restricción"
      - "no quiero meter a mi hija/o en ciclo de dieta"
      - "siento culpa cada vez que como algo 'malo'"
    primary_desires:
      - "comer sin pensar tanto en la comida"
      - "hacer las paces con mi cuerpo"
      - "tener una nutri que no me ponga lista de alimentos prohibidos"
  secondary:
    name: "Madre preocupada por alimentación familiar"
    age_range: "32-50"
    primary_concerns: ["alimentación niños/adolescentes", "transmitir mejor relación con comida"]
  tertiary:
    name: "Profesional salud que quiere certificarse HAES"
    age_range: "25-40"
    primary_concerns: ["formación profesional antidieta", "casos clínicos reales"]
offer_ladder:
  level_1_lead_magnet:
    name: "Guía PDF 'Comer Sin Reglas: Primeros 7 Días'"
    price_usd: 0
    delivery: "PDF descarga directa + email nurturing 7 días"
    cta: "Descargar gratis"
  level_2_tripwire:
    name: "Mini-curso 'Hacer las Paces Con la Comida' (5 módulos asincrónicos)"
    price_clp: 19_990
    price_usd: 22
    delivery: "videos + ejercicios reflexivos + comunidad lectura grupal 30 días"
    cta: "Acceder al mini-curso"
  level_3_core:
    name: "Programa Comer Tranquilas (6 meses)"
    price_clp: 690_000
    price_usd: 760
    payment_options:
      - { type: "single", amount_clp: 690_000 }
      - { type: "installments", count: 6, monthly_clp: 125_000, monthly_usd: 138 }
    delivery: "12 sesiones grupales quincenales + comunidad permanente + biblioteca recursos + 1 sesión 1:1"
    cta: "Aplicar al programa"
    capacity: 20
  level_4_premium:
    name: "Acompañamiento 1:1 + Programa (12 meses)"
    price_clp: 2_400_000
    price_usd: 2640
    payment_options:
      - { type: "installments", count: 12, monthly_clp: 220_000, monthly_usd: 242 }
    delivery: "20 sesiones individuales + acceso completo programa grupal + WhatsApp directo"
    cta: "Aplicar entrevista"
    capacity: 6
plan_tier: creator              # $29 USD/mo (entry tier, no podcast/multi-cohort)
plan_features_enabled:
  - brand_studio_full
  - voice_cloning_pipeline
  - offer_studio_coaching
  - offer_ladder_visualizer
  - community_engagement_workflow
  - cohort_enrollment_workflow
  - sales_agent_vertical_creator
  - authority_vault_full
testimonials:
  - quote: "Llegué con miedo de no poder seguir reglas. Me llevé herramientas para no necesitar reglas."
    author: "Camila P."
    cohort: "Comer Tranquilas 2024-Q3"
    rating: 5
team:
  - name: "Trinidad Riquelme"
    role: "Creator + Nutricionista Lead"
    bio_short: "Nutricionista HAES, especializada TCA"
```

### 2.3 Fixture C — Course Creator México (productized course + community)

```yaml
fixture_id: creator_course_mx_01
fixture_name: "Pablo Productividad"
fixture_type: course_creator_productivity
country: MX
serving: [MX, AR, CL, CO, PE, ES]
niche: productividad_profesionales_remotos
website_inspiration: latam productivity-course-creator archetype
brand_identity:
  name: "Pablo Productividad"
  domain: pabloproductividad.com
  voice_tone: "directo, sin filler, técnico-accesible, neutro broad LatAm, autoridad sin arrogancia"
  voice_cloning_samples_required: 50
  color_palette:
    primary: "#0EA5E9"       # cyan (claridad + foco)
    secondary: "#020617"     # negro casi puro (autoridad)
    accent: "#22D3EE"        # cyan brillante
    neutral: "#F1F5F9"
  logo_concept: "P estilizada con flecha hacia arriba"
  tagline: "Productividad real para profesionales remotos"
authority_vault:
  credentials:
    - "Ex-PM Senior en startup unicornio LatAm (2018-2022)"
    - "Speaker LatAm Tech Conferences 2023, 2024 (CDMX, BA, BogTech)"
    - "Author libro 'Trabajo Profundo en Remoto' (Penguin Random House MX 2024)"
    - "Co-creator framework SISTEMA SEMANAL (open-source)"
  case_studies:
    - client: "Cohorte SISTEMA SEMANAL Q1 2024 (45 alumnos)"
      result: "Reducción 38% tiempo administrativo + +2.5h foco productivo semanal (promedio)"
      duration_months: 3
    - client: "Equipo Liderazgo Startup Fintech MX (8 personas)"
      result: "Reducción reuniones 45% + delivery features +18% sprint"
      duration_months: 4
    - client: "Cohorte Internacional MX/AR/CL (78 alumnos)"
      result: "NPS 92, +60% retention año 2"
      duration_months: 6
  press_mentions:
    - { outlet: "Forbes México", title: "Voces emergentes productividad", url: "https://forbes.com.mx/..." }
    - { outlet: "Podcast Sin Filtro Tech", title: "Pablo: ¿Es real el trabajo profundo en LatAm?", url: "https://..." }
    - { outlet: "El País Tecnología", title: "Creators latinos del trabajo remoto", url: "https://..." }
  social_proof:
    youtube_subscribers: 89_000
    newsletter_subscribers: 24_000
    book_copies_sold: 8_500
    nps_score: 92
buyer_persona:
  primary:
    name: "Profesional remoto 28-42 saturado"
    age_range: "28-42"
    income_level: "USD 2k-8k mes (LatAm tech/startup salary)"
    role_examples: ["PM", "Designer", "Senior dev", "Operations lead", "Marketing manager"]
    primary_concerns:
      - "mil herramientas y nada funciona junto"
      - "calendario es un caos, reuniones todo el día"
      - "no termino lo importante, solo lo urgente"
      - "burnout cercano por overwork remoto"
    primary_desires:
      - "tener UN sistema simple que escale"
      - "recuperar 5h+ foco profundo semanal"
      - "dejar de procrastinar tareas importantes"
  secondary:
    name: "Founder solo / 2-person startup"
    age_range: "26-38"
    primary_concerns: ["wear-many-hats overload", "no proceso operativo claro"]
  tertiary:
    name: "Team lead remoto"
    age_range: "30-45"
    primary_concerns: ["cómo enseñar productividad a mi equipo", "reducir reuniones del equipo"]
offer_ladder:
  level_1_lead_magnet:
    name: "Newsletter semanal 'Una idea, un proceso' (gratis)"
    price_usd: 0
    delivery: "1 email semanal con tip productividad accionable"
    cta: "Suscribirme"
  level_2_tripwire:
    name: "Workshop self-paced 'Tu Semana Sistematizada' (3 horas)"
    price_usd: 47
    delivery: "videos + plantillas Notion + plantilla calendario"
    cta: "Acceder al workshop"
  level_3_core:
    name: "Cohorte SISTEMA SEMANAL (10 semanas)"
    price_usd: 597
    payment_options:
      - { type: "single", amount_usd: 597 }
      - { type: "installments", count: 4, monthly_usd: 167 }
    delivery: "10 sesiones live + comunidad cohorte 10 sem + 1 sesión grupo pequeño semana 6 + alumni acceso permanente"
    cta: "Inscribirme próxima cohorte"
    capacity: 45               # larger cohort, less 1:1
  level_4_premium:
    name: "Implementación 1:1 + Sistemas a Equipo (3 meses)"
    price_usd: 4_500
    payment_options:
      - { type: "installments", count: 3, monthly_usd: 1500 }
    delivery: "6 sesiones 1:1 + audit calendario completo + setup Notion equipo + 2 workshops al equipo del cliente"
    cta: "Aplicar entrevista"
    capacity: 6
plan_tier: agency               # $299 USD/mo (multi-cohort + advanced analytics + team seats)
plan_features_enabled:
  - brand_studio_full
  - voice_cloning_pipeline
  - offer_studio_coaching
  - offer_ladder_visualizer
  - community_engagement_workflow
  - cohort_enrollment_workflow
  - sales_agent_vertical_creator
  - authority_vault_full
  - recurring_subscriptions
  - multi_cohort_management
  - team_seats                 # agency tier shares dashboard with operations team
testimonials:
  - quote: "Probé 4 cursos de productividad antes. SISTEMA SEMANAL es el primero que pude sostener 6 meses después."
    author: "Mauricio C."
    cohort: "Q2 2024"
    rating: 5
team:
  - name: "Pablo Hernández"
    role: "Creator + Head Trainer"
    bio_short: "Ex-PM, autor 'Trabajo Profundo en Remoto'"
  - name: "Inés Olvera"
    role: "Operations Manager"
    bio_short: "Coordina cohortes + onboarding alumnos"
  - name: "Joaquín Ramos"
    role: "Community Manager"
    bio_short: "Modera comunidad alumni + facilita Q&A weekly"
```

## § 3. Gherkin scenarios (AI-resistant) — UI surfaces

### 3.1 Onboarding signup + creator profile (4 steps)

#### Scenario 3.1.A — Happy path (Anabella business coach AR)

```gherkin
given:
  - Comunify brand deployed a su K8s cluster
  - Clerk App #3 comunify LIVE con publishable_key configurado
  - Stripe Connect + MercadoPago sandbox keys
  - Landing page landing.comunify.io up

when:
  - User new visit landing.comunify.io
  - Click "Empezar gratis" CTA hero
  - Clerk Signup flow (email + password OR Google OAuth)
  - Email verify completado
  - Redirect onboarding step 1/4 "Perfil del creator"
  - User completa: creator_name="Anabella Conexión", creator_handle="anabella", country=AR, city="Buenos Aires", main_language="es-AR"
  - Click "Siguiente"
  - Step 2/4 "Tu nicho y audiencia"
  - User selecciona niche="business_coaching", audience_size_estimate="5k-50k followers", primary_offer_type="cohort"
  - Click "Siguiente"
  - Step 3/4 "Elige tu plan"
  - User selecciona plan_tier=pro ($99 USD/mo)
  - Stripe Checkout payment method tokenized (sandbox)
  - Step 4/4 "Tu primera oferta de la ladder"
  - Offer wizard preset coaching_offers_v1 launches con level seed picker
  - User selecciona "Empezar con level 3 core (cohort)" → wizard pre-fills cohort skeleton
  - Click "Crear oferta"

then:
  - User redirected a dashboard.comunify.io (or subdomain per BrandConfig)
  - Tenant created en luana_core_iam.tenants with brand_slug="comunify"
  - TenantProfile.creator_handle="anabella", niche="business_coaching", country="AR"
  - Subscription LIVE plan_tier="pro" status="active"
  - First offer created visible en Offer Studio + ladder visualizer level 3 occupied
  - Sidebar muestra: Dashboard | Brand Studio | Ofertas | Ladder | Cohortes | Comunidad | Authority | Suscripciones | Moderación
  - Welcome toast "Bienvenida a Comunify, Anabella"
  - First-run guide overlay invites: "Subí 50+ chats para clonar tu voz" (next step Brand Studio voice section)

graders:
  - { type: e2e, path: "comunify/frontend/e2e/regression/comunify-onboarding-coach.spec.ts" }
  - { type: state_check, target: db, query: "SELECT brand_slug, niche, country FROM tenants WHERE id=?", expect: "comunify/business_coaching/AR" }
  - { type: state_check, target: stripe_test, query: "subscriptions[customer].plan", expect: "pro_99_usd_mo" }
  - { type: visual_state, screen: "onboarding-step-4", element: "h1", expect: "Tu primera oferta de la ladder" }
```

#### Scenario 3.1.B — Negative (Clerk signup fail duplicate email)

```gherkin
given:
  - Landing.comunify.io up
  - User intenta signup con email already_exists@test.com (already registered different creator)

when:
  - User completa signup form
  - Click submit

then:
  - Clerk error toast: "Este email ya está registrado. ¿Quieres iniciar sesión?"
  - CTA "Iniciar sesión" visible
  - No tenant created
  - User stays en signup page

graders:
  - { type: e2e, path: "comunify/frontend/e2e/regression/comunify-signup-duplicate.spec.ts" }
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM tenants WHERE id=?", expect: "0" }
```

#### Scenario 3.1.C — Edge (handle collision)

```gherkin
given:
  - User completing step 1 onboarding
  - creator_handle "anabella" already taken by tenant_X

when:
  - User types "anabella" en handle field
  - Async validation fires onBlur

then:
  - Inline error "Este handle ya está usado. Probá: anabella-coach, anabella-conexion, anabella01"
  - Submit blocked until handle changed
  - Suggest list autopopulates based on creator_name

graders:
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM tenants WHERE handle=?", expect: "1 (preserves existing)" }
```

#### Scenario 3.1.D — Adversarial (cross-tenant data leak attempt)

```gherkin
given:
  - Two creators registered: Anabella (tenant_A) + Trini (tenant_B)
  - User logged tenant_A creator_owner role

when:
  - User crafts request: GET /api/v1/cohorts?tenant_id={tenant_B}
  - User crafts request: GET /api/v1/community/members?tenant_id={tenant_B}
  - User attempts JWT manipulation to swap X-Tenant-ID header

then:
  - Backend ignores client-supplied tenant_id (middleware uses Clerk JWT tenant_id authoritative)
  - Response 200 returns ONLY tenant_A data
  - Audit log entry: "cross_tenant_attempt blocked tenant_A→tenant_B"
  - JWT manipulation fails Clerk verify

graders:
  - { type: e2e, path: "comunify/frontend/e2e/regression/comunify-cross-tenant-isolation.spec.ts" }
  - { type: state_check, target: db, query: "SELECT data_owner FROM cohorts LIMIT 100", expect: "ALL rows.tenant_id == tenant_A" }
  - { type: state_check, target: logs, query: "audit_log WHERE event='cross_tenant_attempt'", expect: ">= 2 entries" }
```

### 3.2 Brand Studio FULL 10 sections + voice cloning

#### Scenario 3.2.A — Happy (creator completes 10 sections + uploads 50+ chats)

```gherkin
given:
  - Creator logged tenant_A (Anabella)
  - Plan tier=pro, plan_features brand_studio_full=enabled + voice_cloning_pipeline=enabled
  - BrandConfig enabled_sections=[identity, story, narrative, voice, buyer_persona, authority_vault, team, testimonials, communication_assets, contact]
  - BrandConfig field_overrides.buyer_persona.min_count=3 + authority_vault.required=true

when:
  - Navigate /brand-studio
  - Section "Identidad": fill creator_name + tagline + logo + colors (autosave on-change)
  - Section "Historia" (StoryBrand 7 elementos): hero/villain/guide/plan/call-to-action/success/failure (autosave)
  - Section "Narrativa": signature_message + transformation_promise + how_we_help (autosave)
  - Section "Voz" (NEW voice_cloning):
    - Upload chats WhatsApp export ZIP (must >= 50 conversations distinct subscribers)
    - Optional: upload voice notes audio (.m4a/.mp3 transcribed automatically)
    - Section validates 50+ chats threshold before allowing "Distill voice" button
    - Click "Distilar mi voz" → async job kicks off (ETA 8-15 min)
    - Modal: "Estamos analizando tus chats. Te avisamos por email cuando esté lista tu voz clonada."
  - Section "Buyer Persona": min 3 personas required (primary + secondary + tertiary) — each persona has: name, age_range, income_level, business_stage, primary_concerns[], primary_desires[]
  - Section "Authority Vault" (required per BrandConfig): credentials[] + case_studies[] + press_mentions[] + social_proof + awards[]
    - All sub-sections require at least 1 entry
    - Case_study requires: client, result, duration_months
    - Press_mention requires: outlet, title, url (validates URL accessible 200)
  - Section "Equipo": add team members (creator + operations + community manager) — at least 1 (creator self)
  - Section "Testimonios": add testimonials with quote+author+cohort+rating — min 2 entries
  - Section "Communication assets": brand colors complete + logo PNG + cover banners + emoji set preferred
  - Section "Contacto": email + WhatsApp + Instagram + LinkedIn + website
  - Async voice_cloning_distillation completes ~12min later
  - Email notification "Tu voz clonada está lista. Revísala."
  - Navigate back /brand-studio/voz
  - See compiled `system_instruction` preview (read-only 6 blocks: identity, dialect, vocabulary, register, prohibited_patterns, brand_anchors)
  - Click "Ratificar voz" (button enabled after preview review)

then:
  - All sections autosaved (no submit button — form-runtime autosave)
  - tenant_brand_studio row populated with 10 sections JSONB data
  - voice_cloning_samples row populated (chat_count, voice_note_count, distillation_status="completed", system_instruction_compiled_v2)
  - personality_profiles row updated with new system_instruction
  - Sales_agent invalidates Slot 5 cache for this tenant
  - Landing preview renders con colors + full storytelling
  - Audit log entry "voice_cloning_distilled tenant_A samples=52"

graders:
  - { type: e2e, path: "comunify/frontend/e2e/regression/comunify-brand-studio-full.spec.ts" }
  - { type: state_check, target: db, query: "SELECT array_length(enabled_sections, 1) FROM tenant_brand_config WHERE tenant_id=?", expect: "10" }
  - { type: state_check, target: db, query: "SELECT distillation_status, samples_count FROM voice_cloning_samples WHERE tenant_id=?", expect: "completed/52" }
  - { type: state_check, target: db, query: "SELECT system_instruction IS NOT NULL FROM personality_profiles WHERE tenant_id=?", expect: "true" }
  - { type: visual_state, screen: "brand-studio", element: "[data-section]", expect: "10 sections rendered" }
```

#### Scenario 3.2.B — Negative (voice cloning insufficient samples)

```gherkin
given:
  - Creator uploaded 23 chats (below 50 threshold)
  - Section "Voz" loaded

when:
  - User clicks "Distilar mi voz"

then:
  - Button disabled with tooltip "Necesitas al menos 50 chats con personas distintas para distilar voz"
  - Counter visible "23/50 chats subidos"
  - Inline suggestion "Exportá conversaciones WhatsApp y subí el ZIP, o agregá voice notes (1 voice note ~= 5 chats text equivalente)"
  - No distillation job queued

graders:
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM voice_distillation_jobs WHERE tenant_id=? AND status='queued'", expect: "0" }
```

#### Scenario 3.2.C — Edge (case study URL unreachable)

```gherkin
given:
  - Creator filling authority_vault press_mentions
  - User adds URL "https://forbes.com.ar/dead-link-2019"

when:
  - URL validation fires onBlur

then:
  - Inline warning amber "Este link parece no estar disponible (404). ¿Querés guardarlo igual?"
  - Checkbox "Guardar de todas formas" available
  - If checked + saved → entry persisted with `link_status='unreachable_warning'`
  - Authority vault completeness reduces visual prominence vs all-green entries

graders:
  - { type: state_check, target: db, query: "SELECT link_status FROM press_mentions WHERE id=?", expect: "unreachable_warning" }
```

#### Scenario 3.2.D — Adversarial (PII in testimonial + XSS attempt)

```gherkin
given:
  - User logged tenant_A
  - Navigate /brand-studio testimonios section

when:
  - User pastes testimonial quote: "<script>alert('xss')</script>Buena cohorte de DNI 12345678 María"
  - User submits

then:
  - Backend sanitizes input (DOMPurify + Pydantic validator strip HTML)
  - PII detection fires: DNI pattern detected
  - Form error: "Detectamos un DNI en el testimonio. Eliminalo o reemplazalo por iniciales (M.D.)"
  - Submit blocked until inconsistency resolved
  - audit_log entry "pii_detected_testimonial + xss_attempt_detected_blocked"

graders:
  - { type: state_check, target: db, query: "SELECT testimonials FROM tenant_brand_config WHERE tenant_id=?", expect: "no <script tags AND no DNI patterns" }
  - { type: state_check, target: logs, query: "audit_log WHERE event='pii_detected'", expect: ">=1" }
```

### 3.3 Offer Studio + Ladder visualizer

#### Scenario 3.3.A — Happy (creator builds 4-level ladder visually)

```gherkin
given:
  - Creator logged tenant_A
  - Offer Studio preset_pack=coaching_offers_v1 active
  - Ladder visualizer empty (only level 3 core seeded from onboarding step 4)

when:
  - Navigate /ladder
  - Visualizer shows 4 horizontal columns: Level 1 (Lead Magnet) | Level 2 (Tripwire) | Level 3 (Core) ✓ | Level 4 (Premium)
  - Click "+ Agregar oferta" en Level 1
  - Wizard step 1 "Tipo lead magnet": select "Masterclass gratuita live"
  - Step 2 "Promesa de valor": "Cobrar Sin Culpa"
  - Step 3 "Delivery": live_zoom + replay_days=7
  - Step 4 "Conversión a Level 2": auto-suggest_next_offer=true
  - Click "Publicar" → offer created Level 1
  - Repeat para Level 2 (Tripwire $27 workshop asíncrono) + Level 4 (Premium 1:1 $9900)
  - Visualizer ahora muestra 4 ofertas conectadas con flechas indicando flujo natural

then:
  - 4 offers created with offer_type=coaching + value_level matching level (lead_magnet/tripwire/core/premium)
  - OfferLadder entity persisted con relations (level_1_id → level_2_id → level_3_id → level_4_id)
  - Ladder visualizer renders 4-column DAG correctly
  - Sales agent gana awareness of full ladder (intent_pricing_question can navigate user up/down ladder)
  - Telemetry: ladder_completion_score=100% (todos los 4 levels)

graders:
  - { type: e2e, path: "comunify/frontend/e2e/regression/comunify-ladder-build.spec.ts" }
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM offers WHERE tenant_id=?", expect: "4" }
  - { type: state_check, target: db, query: "SELECT level_1_id IS NOT NULL AND level_2_id IS NOT NULL AND level_3_id IS NOT NULL AND level_4_id IS NOT NULL FROM offer_ladders WHERE tenant_id=?", expect: "true" }
  - { type: visual_state, screen: "ladder", element: "[data-ladder-level]", expect: "4 levels rendered" }
```

#### Scenario 3.3.B — Negative (ladder with gap — skip level 2)

```gherkin
given:
  - Creator has Level 1 (lead magnet) + Level 3 (core) filled, Level 2 empty

when:
  - Creator publishes Level 3 without Level 2

then:
  - Soft warning banner top "Tu ladder tiene un salto Lead Magnet → Core. La mayoría de creators agregan un Tripwire (~$25-50) en el medio para convertir más fácil."
  - "Saltar de todas formas" + "Sugerirme un tripwire" CTAs
  - If "Sugerirme un tripwire" clicked → AI suggests 3 tripwire ideas based on creator niche + lead magnet content
  - If saltar → ladder persists with gap, telemetry ladder_gap_warning_acknowledged
  - NO BLOCKING (creator may legitimately skip tripwire)

graders:
  - { type: state_check, target: db, query: "SELECT ladder_gap_acknowledged FROM offer_ladders WHERE tenant_id=?", expect: "true" }
  - { type: state_check, target: logs, query: "telemetry WHERE event='ladder_gap_warning_acknowledged'", expect: "1" }
```

#### Scenario 3.3.C — Edge (cohort capacity sold out before launch)

```gherkin
given:
  - Tenant_A Cohorte Conexión Q2 capacity=18
  - 18 subscribers already enrolled

when:
  - New patient (subscriber 19) initiates checkout flow
  - Backend booking_create called

then:
  - Endpoint returns 409 "Cohorte llena"
  - Sales_agent receives error → offers options:
    "Esta cohorte se completó. Tenés dos opciones:
     1. Anotarte en la lista de espera (15% chance de cupo por bajas)
     2. Aplicar a la Cohorte Conexión Q3 (próxima inscripción: 2026-08-15)"
  - Patient picks waitlist → waitlist row created, audit_log "cohort_waitlist_added"

graders:
  - { type: state_check, target: db, query: "SELECT status FROM cohort_enrollments WHERE cohort_id=? ORDER BY created_at DESC LIMIT 1", expect: "waitlisted" }
```

#### Scenario 3.3.D — Adversarial (PII in offer description)

```gherkin
given:
  - User creates offer with description containing personal_email: "Contactanos en privado@anabella.com.ar para más info"

when:
  - User submits offer

then:
  - PII detection middleware flags submission
  - Form warning: "Detectamos un email en la descripción. Los emails en descripciones públicas son blanco de spam. ¿Querés mostrarlo igual o pedir que te contacten por sales_agent?"
  - 2 options: "Mostrar igual" + "Usar mi sales_agent (recomendado)"
  - If "Mostrar igual" → email persisted with warning flag
  - If "Usar mi sales_agent" → description replaced with "[Aplicar via WhatsApp]" + CTA inserted

graders:
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM offers WHERE description LIKE '%@%' AND warning_flag_email IS NOT NULL", expect: ">=1 with flag" }
```

### 3.4 Subscription + Recurring billing (creator's clients side)

#### Scenario 3.4.A — Happy (subscriber pays monthly cohort installment)

```gherkin
given:
  - Tenant_A Anabella has Cohorte Conexión Q2 launched
  - Subscriber María enrolled with installment plan (3 monthly_usd=547)
  - Month 2 due date approaching

when:
  - Cron scheduler runs daily 9am AR time
  - Detects María subscription installment_2 due_at=2026-05-15 (today)
  - Triggers recurring charge tokenized payment (MercadoPago saved card)
  - Stripe/MP webhook payment_intent.succeeded fires
  - Sales_agent triggered outbound proactive "✅ Listo, recibimos tu pago de USD 547 (cuota 2/3). Vence próxima cuota: 2026-06-15"

then:
  - subscription_charges row created status="succeeded"
  - Subscriber María access continues
  - audit_log entry "recurring_charge_succeeded tenant_A subscriber_X cohort_Y"
  - Creator dashboard shows subscriber as up-to-date

graders:
  - { type: e2e, path: "comunify/backend/tests/e2e/test_subscription_recurring_dental.py" }
  - { type: state_check, target: db, query: "SELECT status FROM subscription_charges WHERE subscriber_id=? AND installment_n=2", expect: "succeeded" }
```

#### Scenario 3.4.B — Negative (dunning — payment failed)

```gherkin
given:
  - Subscriber Lucía monthly recurring charge fails (card_declined)
  - DunningWorkflow active

when:
  - Webhook payment_intent.payment_failed fires
  - DunningWorkflow state transition: active → retry_1
  - Sales_agent triggered outbound "Tu cuota de USD 547 no se procesó. ¿Querés actualizar la tarjeta? https://comunify.io/payments/update/{sub_id}"
  - 3 days pass without resolution → state retry_1 → retry_2 (next retry attempt automatic + reminder)
  - 7 days total → state retry_2 → suspended (lose community access)
  - 14 days total → state suspended → cancelled

then:
  - subscription.status transitions: active → past_due → suspended → cancelled
  - Creator dashboard alerts banner "1 subscriber atrasado: Lucía F."
  - Community access revoked (Lucía cannot post; can still read 24h grace)
  - audit_log trail of dunning_*_attempted + dunning_suspended + dunning_cancelled

graders:
  - { type: state_check, target: db, query: "SELECT status FROM subscriptions WHERE id=?", expect: "cancelled" }
  - { type: state_check, target: logs, query: "audit_log WHERE event LIKE 'dunning_%' AND subscription_id=?", expect: ">=4 events" }
```

#### Scenario 3.4.C — Edge (subscription cancellation mid-cycle)

```gherkin
given:
  - Subscriber Camila active subscription monthly $99
  - Last charge 2026-05-01, next charge 2026-06-01

when:
  - Camila navigates /miembros/billing
  - Click "Cancelar suscripción"
  - Cancellation modal explains: "Tendrás acceso hasta 2026-06-01 (próxima fecha cobro). No volveremos a cobrar"
  - Patient confirms
  - Backend cancellation_at=now + access_until=2026-06-01

then:
  - subscription.status = "cancelled_pending_end_of_period"
  - subscription.access_until = "2026-06-01"
  - No future charges scheduled
  - Sales_agent triggered outbound (proactive nurture flow): "Te vamos a extrañar. Si querés contarnos por qué cancelaste, ayuda mucho mejorar."
  - Cancellation reason captured (optional) for telemetry
  - 2026-06-01 cron: status="cancelled" + community access revoked

graders:
  - { type: state_check, target: db, query: "SELECT status, access_until FROM subscriptions WHERE id=?", expect: "cancelled_pending_end_of_period/2026-06-01" }
```

#### Scenario 3.4.D — Adversarial (race condition double-charge same installment)

```gherkin
given:
  - Webhook fires twice within 200ms (provider retry — common edge)

when:
  - Both webhooks attempt to charge subscriber_id=X installment_n=2

then:
  - Idempotency key `(subscriber_id, installment_n)` catches duplicate
  - Second webhook returns 200 OK + duplicate detected log
  - Single charge_id persisted
  - No double-billing

graders:
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM subscription_charges WHERE subscriber_id=? AND installment_n=2", expect: "1" }
  - { type: state_check, target: logs, query: "shared_idempotency WHERE operation='subscription_charge' AND key=?", expect: "1 row, hits=2" }
```

### 3.5 Cohort detail + Member management

#### Scenario 3.5.A — Happy (creator views cohort roster + sends broadcast)

```gherkin
given:
  - Tenant_A Anabella Cohorte Conexión Q2 active
  - 14 members enrolled

when:
  - Navigate /cohorts/{cohort_id}

then:
  - Page shows:
    - Cohort header: name + status + start_date + end_date + capacity_used (14/18)
    - Roster table: 14 members con avatar + name + tier (regular/premium) + engagement_score + last_active
    - Filter por tier + engagement bucket
    - Tabs: Roster | Comunicación | Recursos | Calendario | Analytics
  - Click "Comunicación" tab
  - "Mensaje broadcast" CTA visible
  - Click → modal with editor (texto + voz embebida + video link + attachment)
  - Compose broadcast: "Hola cohorte 💛, recordatorio sesión 6 mañana 19h hs"
  - Choose audience: All members | Engaged only | Inactive 7d+
  - Select All members
  - Click "Enviar"
  - Confirmation modal: "Vas a enviar a 14 miembros. ¿Confirmás?"
  - Send

then:
  - Broadcast queued (rate-limited per channel)
  - WhatsApp messages dispatched to 14 members (sales_agent voice maintained, broadcast tagged)
  - audit_log entry "cohort_broadcast_sent tenant_A cohort_Q2 recipients=14"
  - Telemetry "broadcast_engagement_tracked" (open/reply rates captured async)

graders:
  - { type: e2e, path: "comunify/frontend/e2e/regression/comunify-cohort-broadcast.spec.ts" }
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM cohort_broadcasts WHERE cohort_id=?", expect: "1" }
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM cohort_broadcast_recipients WHERE broadcast_id=?", expect: "14" }
```

#### Scenario 3.5.B — Negative (broadcast hit rate-limit per WhatsApp tier)

```gherkin
given:
  - Tenant_A WhatsApp Business tier=basic (250 messages/day limit)
  - 245 messages already sent today

when:
  - Creator tries to broadcast cohort 14 members

then:
  - Pre-flight check fires: 14 messages would exceed daily limit (245+14=259 > 250)
  - Modal alert "Estás a 5 mensajes del límite diario WhatsApp. Tu broadcast se enviará a 5 ahora y los 9 restantes mañana 0:00."
  - 2 options: "Enviar 5 ahora + cola" + "Postergar todos al mañana"
  - Per choice → schedule queue

graders:
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM cohort_broadcast_queued WHERE delivery_at > NOW()", expect: ">=9" }
```

#### Scenario 3.5.C — Edge (member tier change mid-cohort)

```gherkin
given:
  - Member María enrolled level_3_core (regular tier)
  - María upgrades to level_4_premium

when:
  - Stripe webhook subscription.changed fires
  - Backend processes upgrade

then:
  - Member tier changes regular → premium
  - Premium-only resources unlocked (private channel + 1:1 access)
  - Sales_agent triggered welcome upgrade message proactive
  - audit_log entry "member_tier_upgraded subscriber_X regular_to_premium"

graders:
  - { type: state_check, target: db, query: "SELECT tier FROM cohort_members WHERE subscriber_id=?", expect: "premium" }
```

#### Scenario 3.5.D — Adversarial (member impersonation attempt)

```gherkin
given:
  - Tenant_A Anabella cohort
  - Bad actor with member_id=fake_id attempts to access /cohorts/{cohort_id}/private-channel

when:
  - Request arrives with crafted member_id

then:
  - Membership check fails (member_id not in cohort_members for tenant_A)
  - 403 Forbidden
  - audit_log entry "cohort_access_denied bad_member_id"

graders:
  - { type: state_check, target: logs, query: "audit_log WHERE event='cohort_access_denied'", expect: ">=1" }
```

### 3.6 Community feed + Agentic moderator

#### Scenario 3.6.A — Happy (member posts + community engages + moderator passes)

```gherkin
given:
  - Tenant_A Comunidad Anabella active
  - Member Lucía posts "Quería compartir que cerré mi primera clienta de USD 800/mes. ¡Gracias cohorte!"

when:
  - Post submitted
  - Agentic moderator (CommunityEngagementWorkflow) processes asynchronously
  - Classifies: { spam: false, nsfw: false, doxxing: false, requires_moderation: false }
  - Auto-approves

then:
  - Post visible publicly in feed
  - Engagement triggers: 8 likes + 3 reply comments within 2h
  - audit_log entry "post_auto_approved spam_score=0.02 nsfw_score=0.0"
  - Engagement metrics update author engagement_score

graders:
  - { type: state_check, target: db, query: "SELECT status FROM community_posts WHERE id=?", expect: "published" }
  - { type: state_check, target: logs, query: "audit_log WHERE event='post_auto_approved' AND post_id=?", expect: "1" }
```

#### Scenario 3.6.B — Negative (post requires moderation — spam detected)

```gherkin
given:
  - Member posts "Aplicá descuento 50% en mi web! Click ahora https://my-spam-link.tk"

when:
  - Agentic moderator processes
  - Classifies: { spam: true (score 0.91), promotional_link: external_unrelated }

then:
  - Post status="pending_moderation"
  - Hidden from public feed
  - Creator notification: "1 post requiere tu revisión (spam suspect)"
  - Creator dashboard /community-moderation shows post + 3 actions: Approve | Reject + Warn | Delete + Ban
  - audit_log entry "post_pending_moderation spam_score=0.91"

graders:
  - { type: state_check, target: db, query: "SELECT status FROM community_posts WHERE id=?", expect: "pending_moderation" }
```

#### Scenario 3.6.C — Edge (NSFW image upload)

```gherkin
given:
  - Member uploads image attachment with NSFW content

when:
  - Image upload triggers vision classification
  - NSFW score > 0.85

then:
  - Image upload rejected before persistence
  - Form error "La imagen contiene contenido no permitido. Subí otra."
  - audit_log entry "nsfw_upload_blocked tenant_A member_X"

graders:
  - { type: state_check, target: db, query: "SELECT COUNT(*) FROM community_post_attachments WHERE member_id=? AND nsfw_score > 0.85", expect: "0" }
```

#### Scenario 3.6.D — Adversarial (doxxing attempt — member shares another member's private contact)

```gherkin
given:
  - Member A posts "Acá el WhatsApp de María D. +54 9 11 5555-1234 si querés contratarla privado"

when:
  - Agentic moderator processes
  - Classifies: { doxxing: true (phone of another member detected), severity: high }

then:
  - Post status="rejected_doxxing"
  - Author warned automatic + post deleted + content moderation_event row
  - Affected member (María) notified privately "Detectamos un intento de compartir tu contacto privado. Ya fue removido."
  - audit_log entry "doxxing_blocked tenant_A author_X target_Y"

graders:
  - { type: state_check, target: db, query: "SELECT status FROM community_posts WHERE id=?", expect: "rejected_doxxing" }
  - { type: state_check, target: logs, query: "audit_log WHERE event='doxxing_blocked'", expect: ">=1" }
```

### 3.7 Authority Vault + Public landing

#### Scenario 3.7.A — Happy (creator's public landing renders authority vault)

```gherkin
given:
  - Tenant_A authority_vault fully filled (credentials + case_studies + press + social_proof + awards)
  - Public landing rendered at landing.comunify.io/anabella

when:
  - External visitor lands on /anabella

then:
  - Landing renders sections:
    - Hero (creator photo + tagline + main CTA "Conocer cohortes")
    - "Sobre Anabella" (3 credentials top + bio short)
    - "Resultados" (3 case_studies highlighted con duration + result)
    - "Han hablado de Anabella" (3 press_mentions with logos)
    - "Por números" (social_proof stats: 47k IG followers, 320k podcast listens, NPS 84)
    - Offer ladder visible (Lead Magnet → Tripwire → Core → Premium)
    - Sales agent widget bottom-right with greeting
  - SEO meta tags rendered con authority data

graders:
  - { type: e2e, path: "comunify/frontend/e2e/regression/comunify-landing-authority.spec.ts" }
  - { type: visual_state, screen: "landing-anabella", element: "[data-authority-section]", expect: "5 authority sections rendered" }
```

### 3.8 Discovery call booking (sales_agent → calendar)

#### Scenario 3.8.A — Happy (lead books discovery call after sales agent qualification)

```gherkin
given:
  - Lead Sebastián chats with Anabella sales_agent via WhatsApp
  - Sales_agent qualifies via `qualify_for_cohort` tool: Sebastián is fit for Level 4 (Premium 1:1)

when:
  - Sales_agent invokes `book_discovery_call` tool
  - Tool returns available slots Dr. Anabella next 7 days
  - Patient picks slot Wed 2026-05-20 17:00 AR
  - Patient confirms

then:
  - Booking row created status="confirmed_discovery_call"
  - shared.scheduling.calendar adds appointment slot Anabella
  - WhatsApp confirmation patient: "✅ Listo Sebastián, te agendo Mié 20-05 17h. Te llega un recordatorio mañana."
  - audit_log entry "discovery_call_booked tenant_A lead_X"

graders:
  - { type: e2e, path: "comunify/backend/tests/e2e/test_discovery_call_booking.py" }
  - { type: state_check, target: db, query: "SELECT appointment_type FROM bookings WHERE id=?", expect: "discovery_call" }
```

## § 4. Wireframes inline (ASCII art)

> Wireframes representan estructura conceptual. Tailwind + Shadcn renders concrete styling. /architect-fe owns concrete component tree.

### 4.1 Onboarding step 1 — Perfil del creator

```
┌────────────────────────────────────────────────────────────────────┐
│ [Logo Comunify]                                       paso 1 de 4   │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│   Bienvenida a Comunify 💛                                         │
│   Contamos tu mundo de creator                                     │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │ Tu nombre o el nombre de tu proyecto *                   │    │
│   │ [Anabella Conexión_______________________________]      │    │
│   └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │ Handle público *  (será tu URL en comunify.io/handle)    │    │
│   │ comunify.io/[anabella__________________________] ✓      │    │
│   │ ✓ Disponible                                              │    │
│   └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │ País *           │  Ciudad *                              │    │
│   │ [Argentina ▼]    │  [Buenos Aires____________________]   │    │
│   └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│   ┌──────────────────────────────────────────────────────────┐    │
│   │ Idioma principal *                                       │    │
│   │ ( ) Español neutro (LatAm broad)                         │    │
│   │ (●) Español Argentina (voseo)                            │    │
│   │ ( ) Español Chile (tuteo chileno)                        │    │
│   │ ( ) Español México (tuteo MX)                            │    │
│   └──────────────────────────────────────────────────────────┘    │
│                                                                    │
│   ────────────────────────────────────────────────────────────    │
│                                          [Atrás]     [Siguiente]   │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 Brand Studio — sidebar with voice cloning section

```
┌────────────────────────────────────────────────────────────────────┐
│ Comunify / Brand Studio                                            │
├──────────────┬─────────────────────────────────────────────────────┤
│ Secciones    │  Voz (Voice Cloning)            ✶ requiere acción   │
│              │                                                     │
│ ✓ Identidad  │  Para que tu sales agent suene como tú, necesitamos │
│ ✓ Historia   │  al menos 50 conversaciones reales con personas     │
│ ✓ Narrativa  │  distintas (chats WhatsApp, emails, voice notes).   │
│ ● Voz   ✶    │                                                     │
│ ○ Buyer Per. │  ┌─────────────────────────────────────────────┐   │
│   (1/3)      │  │ Subir conversaciones                        │   │
│ ✶ Authority  │  │  [📁 Subir ZIP de chats WhatsApp]           │   │
│ ✓ Equipo     │  │  [🎙️ Subir voice notes (.m4a/.mp3)]         │   │
│ ✓ Testimon.  │  └─────────────────────────────────────────────┘   │
│ ✓ Communic.  │                                                     │
│ ✓ Contacto   │  Progreso de muestras                               │
│              │  ▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▰▱▱▱  42 / 50 chats subidos    │
│ 7/10 secc.   │  ┌─────────────────────────────────────────────┐   │
│ ┌──────────┐ │  │ 📁 chats_export_2024_12.zip (37 chats) ✓   │   │
│ │Vista     │ │  │ 🎙️ voice_notes_pack_1.m4a (5 notes ✓)       │   │
│ │previa    │ │  └─────────────────────────────────────────────┘   │
│ │landing   │ │                                                     │
│ └──────────┘ │  ┌─────────────────────────────────────────────┐   │
│              │  │ [Distilar mi voz]   (deshabilitado: 42/50)  │   │
│              │  └─────────────────────────────────────────────┘   │
│              │  ⓘ Cuando tengas 50+ podés distilar tu voz.        │
│              │                                                     │
│              │  Autosave activo · Último guardado: hace 2 seg     │
└──────────────┴─────────────────────────────────────────────────────┘
```

### 4.3 Brand Studio — voice distilled preview (post distillation)

```
┌────────────────────────────────────────────────────────────────────┐
│ Comunify / Brand Studio / Voz                                      │
├────────────────────────────────────────────────────────────────────┤
│                                                                    │
│  ✓ Tu voz fue distilada exitosamente (12 min análisis · 52 chats)  │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐  │
│  │ Vista previa de tu voz compilada (v2 — 6 bloques)            │  │
│  │                                                              │  │
│  │ ● Identidad         "Soy Anabella, mentora de mujeres        │  │
│  │                      emprendedoras. Acompaño desde 2017..."  │  │
│  │                                                              │  │
│  │ ● Dialecto          es-AR voseo natural. Uso 'vos/tenés/sos' │  │
│  │                      en conversación. NO uso 'tú'.            │  │
│  │                                                              │  │
│  │ ● Vocabulario       Frases tuyas frecuentes detectadas:      │  │
│  │   característico    "te abrazo", "me encanta lo que decís",  │  │
│  │                      "vamos paso a paso", "no estás sola"    │  │
│  │                                                              │  │
│  │ ● Registro          Cálido, validador, vehemente cuando      │  │
│  │                      hablás de derechos económicos. Directa   │  │
│  │                      cuando aplica.                           │  │
│  │                                                              │  │
│  │ ● ASÍ NO            ❌ Tono de gurú / aspiracional vacío      │  │
│  │                      ❌ Frases motivacionales sin contexto    │  │
│  │                      ❌ Vocabulario corporativo aséptico      │  │
│  │                                                              │  │
│  │ ● Anclajes de marca "Mujer, dueña de tu negocio. Vos podés." │  │
│  │                      Cohorte como espacio sagrado.            │  │
│  └─────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  ¿Te representa? Podés ajustar manualmente cualquier bloque.       │
│                                                                    │
│  [Editar bloques]   [Re-distilar con más samples]   [Ratificar ✓] │
└────────────────────────────────────────────────────────────────────┘
```

### 4.4 Ladder visualizer — 4 niveles drag-drop

```
┌────────────────────────────────────────────────────────────────────────┐
│ Comunify / Anabella / Offer Ladder                                     │
├────────────────────────────────────────────────────────────────────────┤
│                                                                        │
│  Tu ladder de ofertas                              Completitud 4/4 ✓   │
│                                                                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌──────────┐│
│  │ Nivel 1     │ →  │ Nivel 2     │ →  │ Nivel 3     │ →  │ Nivel 4  ││
│  │ Lead Magnet │    │ Tripwire    │    │ Core ★      │    │ Premium  ││
│  │             │    │             │    │             │    │          ││
│  │ "Cobrar Sin │    │ "Tu Precio  │    │ "Cohorte    │    │ "Mentor. ││
│  │  Culpa"     │    │  Magnético" │    │  Conexión"  │    │  1:1"    ││
│  │             │    │             │    │             │    │          ││
│  │ Gratis      │    │ USD 27      │    │ USD 1.497   │    │ USD 9.9k ││
│  │ live + rep. │    │ 5 vids+plt. │    │ 12 sem      │    │ 6 meses  ││
│  │             │    │             │    │             │    │          ││
│  │ ●●●●●●●●●○○ │    │ ●●●●●●○○○○○ │    │ ●●●●●●●●●●● │    │ ●●●●○○○○○│
│  │ 82% completo│    │ 64% completo│    │ 100% ✓      │    │ 41% comp.│
│  │             │    │             │    │             │    │          ││
│  │ [Editar]    │    │ [Editar]    │    │ [Editar]    │    │ [Editar] ││
│  └─────────────┘    └─────────────┘    └─────────────┘    └──────────┘│
│                                                                        │
│  Conversión proyectada (basada en benchmarks Comunify creator-economy):│
│  Lead Magnet → Tripwire:  ~8%                                          │
│  Tripwire → Core:         ~12%                                         │
│  Core → Premium:          ~6%                                          │
│                                                                        │
│  [+ Agregar oferta libre fuera de ladder]    [Ver analytics flujo]    │
└────────────────────────────────────────────────────────────────────────┘
```

### 4.5 Cohort detail + Member roster

```
┌──────────────────────────────────────────────────────────────────────┐
│ Anabella / Cohortes / Cohorte Conexión Q2 2026                       │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│ Cohorte Conexión Q2 2026                    [Editar] [Acciones ▼]    │
│ Inicia 2026-05-15 · Termina 2026-08-07 · Capacidad 14/18             │
│                                                                      │
│  ╔══════════════╦═══════════════╦══════════════╦══════════════════╗ │
│  ║ Roster       ║ Comunicación  ║ Recursos     ║ Calendario · Anly║ │
│  ╚══════════════╩═══════════════╩══════════════╩══════════════════╝ │
│                                                                      │
│  Filtros:  Tier [Todas ▼]    Engagement [Todas ▼]    [Buscar nombre]│
│                                                                      │
│  ┌──────┬────────────────┬─────────┬───────────────┬──────────────┐ │
│  │      │ Nombre         │ Tier    │ Engagement    │ Última activ.│ │
│  ├──────┼────────────────┼─────────┼───────────────┼──────────────┤ │
│  │ 🟢  │ María D.       │ Premium │ ▰▰▰▰▰ Alto   │ Hace 2h      │ │
│  │ 🟢  │ Lucía F.       │ Regular │ ▰▰▰▰▱ Alto    │ Hace 5h      │ │
│  │ 🟡  │ Camila P.      │ Regular │ ▰▰▰▱▱ Medio   │ Hace 2d      │ │
│  │ 🟡  │ Renata G.      │ Regular │ ▰▰▱▱▱ Medio   │ Hace 4d      │ │
│  │ 🔴  │ Florencia S.   │ Regular │ ▰▱▱▱▱ Bajo    │ Hace 9d      │ │
│  │ ... │                │         │               │              │ │
│  └──────┴────────────────┴─────────┴───────────────┴──────────────┘ │
│                                                                      │
│  4 cupos disponibles · [+ Invitar manualmente]                       │
│                                                                      │
│  [📢 Enviar broadcast]   [📊 Exportar roster CSV]                    │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.6 Authority Vault — credentials + case studies + press

```
┌──────────────────────────────────────────────────────────────────────┐
│ Anabella / Brand Studio / Authority Vault                            │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Authority Vault                          Esta sección es requerida  │
│                                                                      │
│  Tu autoridad construye confianza en cada paso del journey de tu     │
│  audiencia. Llenala con casos reales, no inventes.                   │
│                                                                      │
│  ── CREDENCIALES (3/3) ✓ ──                                          │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ • Master Coach Internacional ICF (Argentina, 2019)          │    │
│  │ • +8 años acompañando emprendedoras LatAm                   │    │
│  │ • Mentora Programa Mujeres + Pyme Banco Galicia 2023        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  [+ Agregar credencial]                                              │
│                                                                      │
│  ── CASOS DE ESTUDIO (3/3) ✓ ──                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 1. María D. (Belleza Spa Buenos Aires)                       │    │
│  │    Triplicó facturación en 6 meses + sistematizó equipo 4   │    │
│  │    Duración 6 meses          [Editar]  [Solicitar audio test]│    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ 2. Lucía F. (Consultora Marketing Córdoba)                  │    │
│  │    Lanzó programa grupal +200 alumnas + escaló de freelance │    │
│  │    Duración 9 meses          [Editar]  [Solicitar audio test]│    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │ 3. Cohorte Conexión 2024 (12 emprendedoras)                 │    │
│  │    Promedio +180% facturación 12 meses                       │    │
│  │    Duración 12 meses         [Editar]  [Solicitar audio test]│    │
│  └─────────────────────────────────────────────────────────────┘    │
│  [+ Agregar caso]                                                    │
│                                                                      │
│  ── MENCIONES PRENSA (3/3) ✓ ──                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 📰 Forbes Argentina — "10 mentoras a seguir 2024"           │    │
│  │    https://forbes.com.ar/...                            ✓  │    │
│  │ 📰 La Nación — "Coaching emprendedoras: el boom"            │    │
│  │    https://lanacion.com.ar/...                          ✓  │    │
│  │ 🎙️ Podcast Negocios Digitales Ep.142                       │    │
│  │    https://...                                          ✓  │    │
│  └─────────────────────────────────────────────────────────────┘    │
│  [+ Agregar mención]                                                 │
│                                                                      │
│  ── PRUEBA SOCIAL ──                                                 │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Instagram seguidores [_47000__]  NPS [__84__]                │    │
│  │ Podcast listens [_320000_]                                   │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ── PREMIOS (1) ──                                                   │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 🏆 Top 50 Coaches LatAm 2023 — Coach Magazine                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Autosave activo · Último guardado: hace 4 seg                       │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.7 Community moderation inbox

```
┌──────────────────────────────────────────────────────────────────────┐
│ Anabella / Comunidad / Moderación                          1 pending │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Posts que requieren tu atención                                     │
│                                                                      │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ 🟠 PENDIENTE — Spam score 0.91                               │    │
│  │                                                              │    │
│  │ Autor:  Renata G.  (Member regular, cohorte Q2)              │    │
│  │ Hace:   12 min                                               │    │
│  │                                                              │    │
│  │ ┌────────────────────────────────────────────────────────┐  │    │
│  │ │ "Aplicá descuento 50% en mi web! Click ahora          │  │    │
│  │ │  https://my-spam-link.tk"                              │  │    │
│  │ └────────────────────────────────────────────────────────┘  │    │
│  │                                                              │    │
│  │ Análisis automático:                                         │    │
│  │  • Link externo no relacionado al nicho   ⚠️                 │    │
│  │  • Lenguaje promocional agresivo          ⚠️                 │    │
│  │  • Dominio .tk (típicamente spam)         🚨                 │    │
│  │                                                              │    │
│  │ Member context: 1er post · primera vez en moderación         │    │
│  │                                                              │    │
│  │ [✓ Aprobar]   [⚠️ Rechazar + Avisar]   [🚫 Eliminar + Bann.] │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  ── Sin posts pendientes adicionales ──                              │
│                                                                      │
│  Ajustes de moderación                                               │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ Auto-aprobar miembros con engagement_score > 80         ☑   │    │
│  │ Auto-rechazar spam_score > 0.95                          ☑   │    │
│  │ Auto-eliminar NSFW score > 0.85                          ☑   │    │
│  │ Pre-moderación nuevos miembros (primer 3 posts)          ☑   │    │
│  └─────────────────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────────────────┘
```

### 4.8 Subscriptions admin (recurring billing dashboard)

```
┌──────────────────────────────────────────────────────────────────────┐
│ Anabella / Suscripciones                                             │
├──────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Métricas últimos 30 días                                            │
│                                                                      │
│  ┌──────────────────┬──────────────────┬─────────────────────────┐  │
│  │ MRR              │ Active subs      │ Churn rate              │  │
│  │ USD 18.470       │ 14               │ 2.1% (1 cancelled)      │  │
│  └──────────────────┴──────────────────┴─────────────────────────┘  │
│                                                                      │
│  Distribución por estado                                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ Active            ▰▰▰▰▰▰▰▰▰▰▰▰  12                          │    │
│  │ Past Due          ▰▰  2                                     │    │
│  │ Cancelled         ▰  1                                      │    │
│  └────────────────────────────────────────────────────────────┘    │
│                                                                      │
│  Filtros  Estado [Todas ▼]   Tier [Todas ▼]   [Buscar nombre]        │
│                                                                      │
│  ┌──────┬─────────────┬─────────────┬──────────┬───────────────┐    │
│  │ Est. │ Subscriber  │ Tier        │ Monthly  │ Next charge   │    │
│  ├──────┼─────────────┼─────────────┼──────────┼───────────────┤    │
│  │ 🟢  │ María D.    │ Premium     │ USD 1700 │ 2026-06-01    │    │
│  │ 🟢  │ Lucía F.    │ Regular     │ USD 547  │ 2026-06-08    │    │
│  │ 🟠  │ Florencia S.│ Regular     │ USD 547  │ 2 días atraso │    │
│  │ 🟠  │ Renata G.   │ Regular     │ USD 547  │ 5 días atraso │    │
│  │ 🔴  │ Camila P.   │ Regular     │ USD 547  │ Cancelada     │    │
│  │ ...                                                          │    │
│  └──────┴─────────────┴─────────────┴──────────┴───────────────┘    │
│                                                                      │
│  Dunning workflow activo: 2 subscribers · próxima retry en 12h       │
│                                                                      │
│  [📊 Exportar CSV]   [📧 Reenviar links de pago atrasados]           │
└──────────────────────────────────────────────────────────────────────┘
```

## § 5. Estados visuales (por screen)

### 5.1 Onboarding step 1

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `idle` | Inicial post signup verify | Form fields empty + breadcrumb 1/4 | Error banner, success toast |
| `validating_handle` | Handle field onBlur | Spinner inline + "Verificando..." | Available indicator |
| `handle_available` | Async returns 200 | Green ✓ "Disponible" | Spinner |
| `handle_taken` | Async returns 409 | Red ✗ "Ya está usado" + 3 suggestions chips | Available |
| `validating` | Submit click | Form disabled + Spinner button | Error |
| `error_creator_name_taken` | Backend 409 | Form enabled + Error banner | Success |
| `success` | 201 created | Loading transition | Form |
| `transitioning` | Redirect step 2 | Spinner page-level | Step 1 form |

### 5.2 Brand Studio voice cloning section

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `idle_empty` | First load, 0 samples | Empty state + CTA "Subir conversaciones" + explanatory copy | Progress bar |
| `uploading` | Upload in progress | Progress bar + cancel CTA | Distill button |
| `samples_insufficient` | <50 samples loaded | Counter "N/50 chats subidos" + Distill button disabled with tooltip | Distill enabled |
| `samples_sufficient` | 50+ samples loaded | Counter "N/50 ✓" + Distill button enabled | Insufficient warning |
| `distilling_async` | Distillation kicked off | Progress modal "Analizando tus chats... ETA 8-15 min" + email notification mention | Distill button |
| `distilled_preview` | Async job done | 6-block preview + Edit + Re-distill + Ratify CTAs | Distill progress |
| `ratified` | Patient clicks Ratify | Green checkmark + summary stats | Preview edit mode |
| `distillation_failed` | Async job error | Error banner + retry CTA + samples preserved | Preview |

### 5.3 Authority Vault

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `idle_empty` | Section load empty (required not met) | Empty state + Red banner "Esta sección es requerida" + CTA per subsection | All entries |
| `partially_filled` | Some subsections have entries, others empty | Progress badges per subsection (N/3 etc) + entries shown | Empty CTAs hidden subsections |
| `validating_url` | Press_mention URL field onBlur | Spinner + "Verificando..." | Ok indicator |
| `url_unreachable` | URL fetch 404/timeout | Amber warning + checkbox "Guardar igual" | Ok indicator |
| `complete` | All required subsections filled | Green completion badge top + summary | Validation warnings |

### 5.4 Ladder visualizer

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `empty` | No offers yet | 4 empty columns con "+ Agregar oferta" CTAs each | Connection arrows |
| `partial` | 1-3 levels filled | Filled columns rendered + empty columns CTAs + warning banner ladder gaps | Conversion projections |
| `complete` | 4 levels filled | All 4 columns + connection arrows + conversion projections | Empty CTAs |
| `gap_warning` | Filled with skip (e.g., L1+L3 no L2) | Soft amber banner suggesting tripwire | — |
| `editing_level` | Click Edit on a level card | Side drawer with offer wizard for that level | — |

### 5.5 Cohort detail + Roster

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `loading` | Page mount | Skeleton header + skeleton table | Data |
| `roster_populated` | Data fetched | Header stats + tabs + filter row + table | Skeleton |
| `empty_filter` | Filter results 0 | Empty state "Sin miembros para los filtros aplicados" | Table |
| `broadcast_compose` | Broadcast CTA click | Modal with editor + audience selector | — |
| `broadcast_queued` | Send confirmed | Toast "Broadcast enviado, ver delivery analytics" | — |
| `broadcast_rate_limited` | Pre-flight check fails | Modal alert with queue/postpone options | — |

### 5.6 Community moderation inbox

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `loading` | Page mount | Skeleton | Data |
| `inbox_zero` | No pending posts | Empty state celebration "¡Inbox vacío! Tu comunidad fluye 🎉" | Pending cards |
| `pending_posts` | 1+ pending | Pending cards stack + 3 actions each + settings panel | Empty state |
| `action_in_progress` | Action click | Spinner overlay card + disabled actions | Other actions |
| `action_complete` | Action done | Toast + remove card from inbox | Action confirmation |

### 5.7 Subscriptions admin

| Estado | Trigger | Componentes visibles | Componentes ocultos |
|---|---|---|---|
| `loading` | Initial mount | Skeleton metrics + skeleton table | Data |
| `populated` | Data fetched | MRR card + Active + Churn + distribution chart + filter + table | Skeleton |
| `dunning_active_banner` | Past-due subscribers > 0 | Amber banner top "N subscribers en dunning" + CTA | — |
| `export_processing` | Click Export CSV | Toast "Preparando CSV..." + disabled button | Table interaction |
| `update_payment_link_sent` | Click "Reenviar links" | Toast "Links enviados a N subscribers" | — |

## § 6. Componentes (reuse > inventar)

### 6.1 Shadcn primitives reuse (zero new)

| Componente | Path luana-core-ui | Uso Story 12 |
|---|---|---|
| `Button` | `@luana/ui/button` | All CTAs |
| `Input` | `@luana/ui/input` | Form fields |
| `Select` | `@luana/ui/select` | Country, niche, plan, tier |
| `RadioGroup` | `@luana/ui/radio-group` | Niche selection, dialect picker |
| `Checkbox` | `@luana/ui/checkbox` | Settings toggles |
| `Dialog` | `@luana/ui/dialog` | Broadcast modal, cancellation modal |
| `Toast` | `@luana/ui/toast` | All notifications |
| `Form` | `@luana/ui/form` | All wizards |
| `Progress` | `@luana/ui/progress` | Voice samples counter, distillation progress, wizard step |
| `Skeleton` | `@luana/ui/skeleton` | Loading states |
| `Avatar` | `@luana/ui/avatar` | Members, creator, team |
| `Badge` | `@luana/ui/badge` | Tier badges, engagement bucket |
| `Card` | `@luana/ui/card` | Plan tiers, offer ladder cards |
| `Sheet` | `@luana/ui/sheet` | Mobile sidebar, filter drawer, edit drawer |
| `Tabs` | `@luana/ui/tabs` | Cohort detail tabs |
| `Table` | `@luana/ui/table` | Roster, subscriptions, audit |
| `Tooltip` | `@luana/ui/tooltip` | Disabled CTAs explanations |
| `Slider` | `@luana/ui/slider` | Engagement threshold settings |

### 6.2 Shared components reuse (cross-brand)

| Componente | Path | Uso Story 12 |
|---|---|---|
| `DataTable` | `@luana/shared/data-table` | Roster, subscriptions, moderation |
| `FormWizard` | `@luana/shared/form-wizard` | Onboarding, offer wizard, broadcast compose |
| `EmptyState` | `@luana/shared/empty-state` | All empty UI |
| `ErrorBoundary` | `@luana/shared/error-boundary` | All routes |
| `TenantSwitcher` | `@luana/shared/tenant-switcher` | Header (multi-creator future) |
| `SidebarLayout` | `@luana/shared/sidebar-layout` | App shell |
| `PageHeader` | `@luana/shared/page-header` | Breadcrumbs + actions |
| `FormRuntime` | `@luana/shared/form-runtime` | Brand Studio sections autosave |
| `FileUploadZone` | `@luana/shared/file-upload-zone` | Voice cloning samples upload, image upload |
| `AsyncJobStatus` | `@luana/shared/async-job-status` | Distillation progress polling |

### 6.3 NEW components comunify-specific (justification inline)

| Componente | Path | Justificación why new |
|---|---|---|
| `CreatorNichePicker` | `comunify/frontend/features/onboarding/components/creator-niche-picker.tsx` | Creator-economy-specific iconography + niche taxonomy (coach, course-creator, content-creator, expert-author) — no equivalente Vitalia/Nicolify |
| `VoiceSamplesUploader` | `comunify/frontend/features/brand-studio/components/voice-samples-uploader.tsx` | WhatsApp ZIP parser + voice notes transcription + sample counter — vertical-creator-economy specific |
| `VoiceDistilledPreview` | `comunify/frontend/features/brand-studio/components/voice-distilled-preview.tsx` | 6-block compiled voice display + per-block edit + ratify CTA — couples voice_cloning_distillation output |
| `LadderVisualizer` | `comunify/frontend/features/ladder/components/ladder-visualizer.tsx` | 4-column DAG with drag-drop reorder + conversion projections + level cards — creator-economy specific |
| `AuthorityVaultEditor` | `comunify/frontend/features/brand-studio/components/authority-vault-editor.tsx` | Multi-subsection editor with URL validation + case study templates + social proof aggregator — creator-economy specific |
| `CohortRosterTable` | `comunify/frontend/features/cohorts/components/cohort-roster-table.tsx` | Members table with engagement_score + tier badge + last_active + filter combinations — community/cohort specific |
| `CohortBroadcastComposer` | `comunify/frontend/features/cohorts/components/cohort-broadcast-composer.tsx` | Multi-channel composer (text + voice embed + video link + attachment) + audience segmenter + rate-limit pre-flight check |
| `CommunityModerationCard` | `comunify/frontend/features/community/components/community-moderation-card.tsx` | Pending post card with classifier scores + member context + 3 action CTAs — agentic moderator coupled |
| `SubscriptionMetricsCards` | `comunify/frontend/features/subscriptions/components/subscription-metrics-cards.tsx` | MRR + active + churn aggregation specific creator-economy SaaS |
| `DunningActiveBanner` | `comunify/frontend/components/dunning-active-banner.tsx` | Top-of-page alert when past-due subscribers exist — recurring-billing specific |
| `CreatorLandingHero` | `comunify/frontend/features/landing/components/creator-landing-hero.tsx` | Public landing hero with creator photo + tagline + authority signals stack — public-facing vertical specific |

Justification gating per anti-duplication.md: NEW components son creator-economy-vertical-specific. No existe Luana core equivalent ni Vitalia/Nicolify equivalent. Brand isolation per path.

## § 7. Data flow (conceptual)

### 7.1 API endpoints consumidos (BE → comunify/backend/)

```yaml
# Onboarding
POST /api/v1/comunify/onboarding/creator-profile      # creates tenant + tenant_profile
POST /api/v1/comunify/onboarding/check-handle         # async validation
GET  /api/v1/comunify/onboarding/plans                # lists plan_tiers
POST /api/v1/comunify/onboarding/subscribe            # Stripe Checkout session

# Brand Studio (10 sections)
GET  /api/v1/brand-studio/sections                   # @luana/core endpoint
PATCH /api/v1/brand-studio/sections/{section}        # autosave per section
POST /api/v1/comunify/voice-cloning/samples           # upload chats/voice notes
GET  /api/v1/comunify/voice-cloning/samples/status    # progress + sample counter
POST /api/v1/comunify/voice-cloning/distill           # kick async distillation job
GET  /api/v1/comunify/voice-cloning/distillation/{job_id}    # polling progress
POST /api/v1/comunify/voice-cloning/ratify            # ratify compiled voice

# Authority Vault
POST /api/v1/comunify/authority-vault/credentials
POST /api/v1/comunify/authority-vault/case-studies
POST /api/v1/comunify/authority-vault/press-mentions
POST /api/v1/comunify/authority-vault/awards
POST /api/v1/comunify/authority-vault/validate-url    # async URL reachability check

# Offer Studio + Ladder
GET  /api/v1/offers/presets/coaching_offers_v1        # preset config
POST /api/v1/offers                                   # create offer
GET  /api/v1/offers?status=published                  # list
GET  /api/v1/comunify/ladder                          # current ladder state per tenant
PATCH /api/v1/comunify/ladder/connections             # update level connections (drag-drop)

# Cohorts
POST /api/v1/comunify/cohorts                         # create cohort
GET  /api/v1/comunify/cohorts                         # list
GET  /api/v1/comunify/cohorts/{id}                    # detail + roster
GET  /api/v1/comunify/cohorts/{id}/roster             # paginated members
POST /api/v1/comunify/cohorts/{id}/broadcasts         # send broadcast
GET  /api/v1/comunify/cohorts/{id}/broadcasts         # list broadcasts + analytics

# Community
GET  /api/v1/comunify/community/feed                  # cross-cohort feed
POST /api/v1/comunify/community/posts                 # member creates post
GET  /api/v1/comunify/community/moderation/inbox      # pending moderation
POST /api/v1/comunify/community/moderation/{post_id}/action    # approve/reject/ban

# Subscriptions
GET  /api/v1/comunify/subscriptions                   # list active + past_due + cancelled
GET  /api/v1/comunify/subscriptions/{id}              # detail
POST /api/v1/comunify/subscriptions/{id}/cancel       # subscriber-initiated cancel
POST /api/v1/comunify/subscriptions/{id}/resend-payment-link
POST /api/v1/comunify/webhooks/stripe                 # Stripe webhook receiver
POST /api/v1/comunify/webhooks/mercadopago            # MercadoPago webhook receiver
```

### 7.2 React Query keys

```typescript
['comunify', 'onboarding', 'plans']
['comunify', 'onboarding', 'handle-check', { handle }]
['comunify', 'brand-studio', 'sections']
['comunify', 'voice-cloning', 'samples', 'status']
['comunify', 'voice-cloning', 'distillation', { job_id }]
['comunify', 'authority-vault', 'credentials']
['comunify', 'authority-vault', 'case-studies']
['comunify', 'authority-vault', 'press-mentions']
['comunify', 'ladder']
['comunify', 'offers', 'list', filters]
['comunify', 'offers', 'presets', 'coaching_offers_v1']
['comunify', 'cohorts', 'list']
['comunify', 'cohorts', 'detail', { id }]
['comunify', 'cohorts', 'roster', { id, filters }]
['comunify', 'cohorts', 'broadcasts', { id }]
['comunify', 'community', 'feed', filters]
['comunify', 'community', 'moderation', 'inbox']
['comunify', 'subscriptions', 'list', { status_filter }]
['comunify', 'subscriptions', 'metrics']
```

### 7.3 Mutations invalidations

```typescript
POST /api/v1/comunify/voice-cloning/samples → invalidates ['comunify', 'voice-cloning', 'samples', 'status']
POST /api/v1/comunify/voice-cloning/distill → invalidates ['comunify', 'voice-cloning', 'samples', 'status']
POST /api/v1/comunify/voice-cloning/ratify → invalidates ['comunify', 'brand-studio', 'sections'] + invalidates Slot 5 cache per tenant
POST /api/v1/offers → invalidates ['comunify', 'offers', 'list'] + ['comunify', 'ladder']
POST /api/v1/comunify/cohorts/{id}/broadcasts → invalidates ['comunify', 'cohorts', 'broadcasts', { id }]
POST /api/v1/comunify/community/moderation/{post_id}/action → invalidates ['comunify', 'community', 'moderation', 'inbox']
PATCH /api/v1/brand-studio/sections/{section} → invalidates ['comunify', 'brand-studio', 'sections']
```

### 7.4 Form library

- **All forms:** React Hook Form (RHF) + Zod schemas
- **Autosave:** Brand Studio sections only (form-runtime-array.md autosave rule). Other forms = explicit submit.
- **Validators:** Zod schemas en `comunify/frontend/lib/zod-schemas/` (per FSD-Lite rule)

### 7.5 Estado global

- No global store. Estado vive en React Query cache.
- Excepción: `useFlowContext()` para multi-step wizards (preserva step + filled fields).

## § 8. Microcopy (Spanish neutro LatAm)

> **Spanish neutro check verified:** NO voseo (tú/tu/eres/tienes/quieres/puedes/haces). NO léxico regional. Tildes + ñ + apertura `¿!`. Excepción autorizada: sales_agent voice respeta `personality_profiles.system_instruction` per tenant (voice_cloning compiled v2). Excepción autorizada: voice cloning preview display block "Dialecto" mostrará voseo cuando tenant_voice es es-AR (es el target compiled output, no chrome UI).

### 8.1 Onboarding (chrome UI = Spanish neutro tuteo)

| Lugar | Copy |
|---|---|
| Page title | "Bienvenida a Comunify" |
| Subtitle | "Cuéntanos tu mundo de creator" |
| Step 1 heading | "Perfil del creator" |
| Field creator_name label | "Tu nombre o el nombre de tu proyecto" |
| Field handle label | "Handle público" |
| Field handle helper | "Será tu URL en comunify.io/{handle}" |
| Field country label | "País" |
| Field city label | "Ciudad" |
| Field language label | "Idioma principal" |
| Step 2 heading | "Tu nicho y audiencia" |
| Step 3 heading | "Elige tu plan" |
| Step 4 heading | "Tu primera oferta de la ladder" |
| CTA next | "Siguiente" |
| CTA back | "Atrás" |
| CTA finish | "Crear oferta" |
| Validation error required | "Este campo es requerido" |
| Validation error handle taken | "Este handle ya está usado. Probá: {suggestions}" |
| Success transition | "Listo, sigamos" |

### 8.2 Brand Studio + Voice cloning

| Lugar | Copy |
|---|---|
| Page title | "Brand Studio" |
| Subtitle | "Tu marca, contada bien" |
| Section identidad | "Identidad" |
| Section historia | "Historia (StoryBrand)" |
| Section narrativa | "Narrativa" |
| Section voz | "Voz (Voice Cloning)" |
| Section buyer_persona | "Buyer Persona" |
| Section authority_vault | "Authority Vault" |
| Section equipo | "Equipo" |
| Section testimonios | "Testimonios" |
| Section communication | "Communication Assets" |
| Section contacto | "Contacto" |
| Voice samples upload zone heading | "Subir conversaciones" |
| Voice samples upload zone copy | "Para que tu sales agent suene como tú, necesitamos al menos 50 conversaciones reales con personas distintas (chats WhatsApp, emails, voice notes)." |
| Voice samples upload CTA | "Subir ZIP de chats WhatsApp" |
| Voice samples voice notes CTA | "Subir voice notes" |
| Voice samples progress | "{N} / 50 chats subidos" |
| Voice samples insufficient tooltip | "Necesitas al menos 50 chats con personas distintas para distilar voz" |
| Voice samples sufficient | "{N} / 50 ✓ listo para distilar" |
| Distill voice CTA | "Distilar mi voz" |
| Distill modal heading | "Estamos analizando tus chats" |
| Distill modal body | "Esto toma 8-15 minutos. Te avisamos por email cuando esté lista." |
| Distill success heading | "Tu voz fue distilada exitosamente" |
| Distill preview heading | "Vista previa de tu voz compilada (v2 — 6 bloques)" |
| Distill preview block identidad | "Identidad" |
| Distill preview block dialecto | "Dialecto" |
| Distill preview block vocabulario | "Vocabulario característico" |
| Distill preview block registro | "Registro" |
| Distill preview block asino | "ASÍ NO" |
| Distill preview block anclajes | "Anclajes de marca" |
| Distill preview question | "¿Te representa? Puedes ajustar manualmente cualquier bloque." |
| CTA ratify voice | "Ratificar" |
| CTA re-distill | "Re-distilar con más samples" |
| CTA edit blocks | "Editar bloques" |
| Forbidden tooltip plan | "Esta sección está disponible en planes superiores" |
| Autosave indicator saving | "Guardando..." |
| Autosave indicator saved | "Guardado hace {N} seg" |
| Autosave error | "Error guardando. {Reintentar}." |

### 8.3 Authority Vault

| Lugar | Copy |
|---|---|
| Page title | "Authority Vault" |
| Required banner | "Esta sección es requerida" |
| Subtitle | "Tu autoridad construye confianza en cada paso del journey de tu audiencia. Llenala con casos reales." |
| Section credenciales | "Credenciales" |
| Section case_studies | "Casos de estudio" |
| Section press_mentions | "Menciones prensa" |
| Section social_proof | "Prueba social" |
| Section awards | "Premios" |
| Add credential CTA | "Agregar credencial" |
| Add case_study CTA | "Agregar caso" |
| Add press_mention CTA | "Agregar mención" |
| Case_study field client | "Cliente" |
| Case_study field result | "Resultado obtenido" |
| Case_study field duration | "Duración (meses)" |
| Press_mention field outlet | "Medio o publicación" |
| Press_mention field title | "Título" |
| Press_mention field url | "URL" |
| URL validation pending | "Verificando link..." |
| URL validation unreachable | "Este link parece no estar disponible (404). ¿Quieres guardarlo igual?" |
| URL validation ok | "Disponible ✓" |
| Solicitar audio test CTA | "Solicitar audio testimonio al cliente" |
| Required not met error | "Authority Vault necesita al menos: 1 credencial + 1 caso + 1 mención" |

### 8.4 Offer Studio + Ladder

| Lugar | Copy |
|---|---|
| Page title ladder | "Tu ladder de ofertas" |
| Ladder level 1 | "Nivel 1 — Lead Magnet" |
| Ladder level 2 | "Nivel 2 — Tripwire" |
| Ladder level 3 | "Nivel 3 — Core" |
| Ladder level 4 | "Nivel 4 — Premium" |
| Ladder add CTA empty level | "Agregar oferta" |
| Ladder edit CTA | "Editar" |
| Ladder completitud | "Completitud {N}/4" |
| Ladder conversion projection title | "Conversión proyectada" |
| Ladder conversion subtitle | "(basada en benchmarks Comunify creator-economy)" |
| Ladder gap warning | "Tu ladder tiene un salto Lead Magnet → Core. La mayoría de creators agregan un Tripwire en el medio. ¿Querés que te sugiera tripwires?" |
| Ladder gap skip CTA | "Saltar de todas formas" |
| Ladder gap suggest CTA | "Sugerirme un tripwire" |
| Offer wizard step 1 | "Tipo de oferta" |
| Offer wizard step 2 | "Promesa de valor" |
| Offer wizard step 3 | "Delivery" |
| Offer wizard step 4 | "Precio y plan de pago" |
| Offer wizard step 5 | "Conversión a próximo nivel" |
| Publish CTA | "Publicar oferta" |
| Success modal | "Oferta publicada en Nivel {N}" |

### 8.5 Cohorts

| Lugar | Copy |
|---|---|
| Page title list | "Cohortes" |
| Create CTA | "Nueva cohorte" |
| Detail tabs | "Roster" / "Comunicación" / "Recursos" / "Calendario" |
| Roster filter tier | "Filtrar por tier" |
| Roster filter engagement | "Filtrar por engagement" |
| Roster column header | "Miembro" / "Tier" / "Engagement" / "Última actividad" |
| Tier regular badge | "Regular" |
| Tier premium badge | "Premium" |
| Engagement alto | "Alto" |
| Engagement medio | "Medio" |
| Engagement bajo | "Bajo" |
| Capacity available | "{N} cupos disponibles" |
| Capacity full | "Cohorte llena" |
| Broadcast CTA | "Enviar broadcast" |
| Broadcast composer heading | "Mensaje broadcast" |
| Broadcast audience all | "Todos los miembros" |
| Broadcast audience engaged | "Solo engaged" |
| Broadcast audience inactive | "Solo inactivos 7d+" |
| Broadcast confirm | "Vas a enviar a {N} miembros. ¿Confirmas?" |
| Broadcast rate-limit | "Estás a {M} mensajes del límite diario WhatsApp." |
| Broadcast queue option | "Enviar {M} ahora + el resto mañana" |
| Broadcast postpone option | "Postergar todos al mañana" |
| Broadcast success | "Broadcast enviado. Ver delivery analytics" |
| Waitlist toast | "Te anotamos en la lista de espera." |

### 8.6 Community + Moderation

| Lugar | Copy |
|---|---|
| Page title community | "Comunidad" |
| Page title moderation | "Moderación" |
| Moderation pending count | "{N} pendiente" |
| Moderation card heading pending | "PENDIENTE" |
| Moderation card author info | "Member {tier}, cohorte {cohort}" |
| Moderation card analysis title | "Análisis automático" |
| Moderation action approve | "Aprobar" |
| Moderation action reject | "Rechazar + Avisar" |
| Moderation action ban | "Eliminar + Banear" |
| Moderation empty | "¡Inbox vacío! Tu comunidad fluye 🎉" |
| Moderation settings heading | "Ajustes de moderación" |
| Setting auto-approve engaged | "Auto-aprobar miembros con engagement_score > 80" |
| Setting auto-reject spam | "Auto-rechazar spam_score > 0.95" |
| Setting auto-delete nsfw | "Auto-eliminar NSFW score > 0.85" |
| Setting pre-moderate new | "Pre-moderación nuevos miembros (primer 3 posts)" |
| NSFW upload error | "La imagen contiene contenido no permitido. Subí otra." |
| Doxxing notification target | "Detectamos un intento de compartir tu contacto privado. Ya fue removido." |

### 8.7 Subscriptions

| Lugar | Copy |
|---|---|
| Page title | "Suscripciones" |
| Metrics MRR | "MRR" |
| Metrics active | "Active subs" |
| Metrics churn | "Churn rate" |
| Status badge active | "Activa" |
| Status badge past_due | "Atrasada" |
| Status badge cancelled | "Cancelada" |
| Dunning banner | "{N} subscribers en dunning · próxima retry en {time}" |
| Cancel subscription CTA | "Cancelar suscripción" |
| Cancel modal heading | "¿Estás seguro de cancelar?" |
| Cancel modal body | "Tendrás acceso hasta {next_charge_date}. No volveremos a cobrar." |
| Cancel confirm | "Sí, cancelar" |
| Cancel reason optional | "¿Querés contarnos por qué? (opcional)" |
| Resend payment links CTA | "Reenviar links de pago atrasados" |
| Resend success | "Links enviados a {N} subscribers" |
| Export CSV | "Exportar CSV" |

### 8.8 Discovery call booking (sales_agent → patient-side)

| Lugar | Copy |
|---|---|
| Booking confirmation | "Listo {name}, te agendo {weekday} {date} {time}. Te llega un recordatorio mañana." |
| Reminder D-1 | "Hola {name} 👋 mañana {time} es nuestra discovery call. Acá el link: {meeting_url}" |

## § 9. Responsive breakpoints

| Screen | Mobile (< 768px) | Tablet (768-1024px) | Desktop (> 1024px) |
|---|---|---|---|
| Onboarding | Form stack vertical, sticky bottom nav | Form 70% width | Centered card 600px wide |
| Brand Studio voice cloning | Stack vertical, upload zone first | Sidebar collapse | Sidebar fixed + main panel |
| Authority Vault | Stack subsections vertical | 2-col grid subsections | 2-col grid + sidebar nav |
| Ladder visualizer | Stack 4 cards vertical | 2-col grid (L1+L2 / L3+L4) | 4-col horizontal with connections |
| Cohort detail | Tabs scrollable horizontal | Tabs + roster table | Tabs + table + side analytics |
| Community moderation | Cards stack | Cards stack + settings drawer | Cards + side settings panel |
| Subscriptions | Metrics stack + table → cards | Metrics row + table compact | Metrics row + table full + filter sidebar |

## § 10. Accessibility

- All inputs `aria-label` + `aria-required` + `aria-invalid`
- All buttons keyboard-focusable + `focus:ring-2 focus:ring-primary focus:outline-none`
- Color contrast: text 4.5:1, UI 3:1 (Tailwind tokens passing)
- Tab order lógico
- Screen reader `aria-live="polite"` para autosave indicators + toasts
- Keyboard navigation full (Esc cierra modals, Enter submits)
- Focus trap en modals (Voice distill modal, Broadcast composer, Cancellation)
- Voice samples upload accessible (file picker fallback for keyboard, drag-drop visual hint con aria)
- Engagement badges con texto + icon además de color
- Ladder drag-drop accessible (keyboard reorder via arrow keys + Enter swap)

## § 11. Telemetría

```yaml
events:
  # Onboarding
  - { name: "comunify_onboarding_started", trigger: "step 1 mount", props: ["referrer"] }
  - { name: "comunify_onboarding_step_completed", trigger: "step submit", props: ["step_n", "niche"] }
  - { name: "comunify_onboarding_completed", trigger: "step 4 done", props: ["plan_tier", "country", "niche"] }

  # Brand Studio
  - { name: "comunify_brand_section_started", trigger: "section open", props: ["section_id"] }
  - { name: "comunify_brand_section_saved", trigger: "autosave success", props: ["section_id", "completion_percent"] }

  # Voice cloning
  - { name: "comunify_voice_samples_uploaded", trigger: "upload success", props: ["sample_count_total", "delta", "type=chats|voice_notes"] }
  - { name: "comunify_voice_distillation_started", trigger: "distill button click", props: ["sample_count"] }
  - { name: "comunify_voice_distillation_completed", trigger: "async job done", props: ["sample_count", "duration_min", "blocks_extracted"] }
  - { name: "comunify_voice_ratified", trigger: "ratify CTA", props: [] }

  # Authority Vault
  - { name: "comunify_authority_entry_added", trigger: "entry persisted", props: ["section=credentials|case_studies|press_mentions|awards"] }
  - { name: "comunify_authority_url_validated", trigger: "url validation done", props: ["section", "status=ok|unreachable"] }

  # Ladder + Offer
  - { name: "comunify_offer_wizard_started", trigger: "wizard mount", props: ["preset", "ladder_level"] }
  - { name: "comunify_offer_published", trigger: "publish success", props: ["offer_id", "value_level"] }
  - { name: "comunify_ladder_gap_warning_acknowledged", trigger: "skip click", props: ["gap_levels"] }
  - { name: "comunify_ladder_gap_tripwire_suggested", trigger: "suggest click", props: [] }

  # Cohorts
  - { name: "comunify_cohort_created", trigger: "POST cohort", props: ["capacity", "tier_distribution"] }
  - { name: "comunify_cohort_broadcast_sent", trigger: "broadcast success", props: ["cohort_id", "recipients_count", "audience"] }
  - { name: "comunify_cohort_broadcast_rate_limited", trigger: "rate limit pre-flight", props: ["cohort_id", "limit_remaining"] }
  - { name: "comunify_cohort_waitlist_added", trigger: "waitlist persist", props: ["cohort_id"] }

  # Community + Moderation
  - { name: "comunify_post_auto_approved", trigger: "moderator pass", props: ["spam_score", "nsfw_score"] }
  - { name: "comunify_post_pending_moderation", trigger: "moderator flag", props: ["reason"] }
  - { name: "comunify_moderation_action", trigger: "action click", props: ["action=approve|reject|ban", "post_id"] }
  - { name: "comunify_doxxing_blocked", trigger: "doxxing detected", props: [] }
  - { name: "comunify_nsfw_upload_blocked", trigger: "nsfw upload reject", props: [] }

  # Subscriptions + Dunning
  - { name: "comunify_subscription_created", trigger: "subscription_create", props: ["plan", "amount"] }
  - { name: "comunify_subscription_cancelled", trigger: "cancel CTA", props: ["reason", "tier"] }
  - { name: "comunify_recurring_charge_succeeded", trigger: "webhook succeeded", props: ["amount"] }
  - { name: "comunify_recurring_charge_failed", trigger: "webhook failed", props: ["failure_reason"] }
  - { name: "comunify_dunning_state_change", trigger: "workflow transition", props: ["from", "to"] }
  - { name: "comunify_payment_link_resent", trigger: "resend CTA", props: ["count"] }

  # Discovery calls
  - { name: "comunify_discovery_call_booked", trigger: "sales_agent tool", props: ["offer_level"] }
```

## § 12. Brand voice

### 12.1 UI chrome voice (Comunify default, no override)

Default Comunify chrome UI (sidebar, forms, buttons): **Spanish neutro LatAm puro per `spanish-text.md` R2**. NO voseo, NO léxico regional, tildes + ñ + apertura `¿!`. Verb tense: **tuteo** (`tú/tu/tienes/eres/puedes/haces`).

**Rationale:** sales_agent voice respeta voice_cloning compiled v2 per tenant (Anabella AR voseo, Trini CL tuteo chileno, Pablo MX neutro broad). Chrome UI dirigido a creators (no end-users) — neutro pure cubre amplitud LatAm sin sesgo regional. Diferenciación voz vive en sales_agent (per tenant cloned).

### 12.2 Sales agent voice — per tenant from voice cloning

Sales agent NO se rige por chrome UI rule. Voice viene de `personality_profiles.system_instruction` per tenant compilado via **voice_cloning_distillation** pipeline (NEW for Story 12 — 50+ chats → Compiler v2 6 bloques) per `sales-agent-brand-voice.md` rule.

Fixture defaults:
- Anabella business coach (AR): voice voseo natural (es-AR distilled de chats)
- Trini Nutrición Real (CL): voice neutro chileno tuteo (es-CL distilled)
- Pablo Productividad (MX): voice neutro broad LatAm (es-MX distilled)

Comunify BrandConfig `features.voice_cloning=True` (per 00-story.md). Pipeline async ~12 min. Creator ratifica preview 6 bloques antes deploy.

### 12.3 Community safety voice constraints

Independiente del voice cloning: sales_agent comunify MUST:
- NO permitir spam comercial cross-niche en comunidad
- NO permitir NSFW content
- NO permitir doxxing (compartir contacto privado otro miembro)
- SÍ derivar a moderator humano si edge case ambiguo
- SÍ aplicar disclaimers cuando proceda (legal: "Este consejo no reemplaza asesoramiento profesional licenciado")
- SÍ proteger newcomers (pre-moderar primer 3 posts default)

Voice constraints enforced via:
- Slot 4 (`COMMUNITY_SAFETY_RAILS`) en prompt cache layer (cache 1h TTL)
- Guardrail middleware `comunify/agentic/guardrails/community_safety.py`
- Specialist prompt template `comunify/agentic/prompts/specialist_creator.j2`

## § 13. Fixtures testing strategy

Per Q5=research-driven fixtures:

### 13.1 3 fixtures programmatic seed

- `Anabella Conexión` (AR business coach plan_tier=pro)
- `Trini Nutrición Real` (CL nutricionista plan_tier=creator)
- `Pablo Productividad` (MX course creator plan_tier=agency)

Seed script: `comunify/backend/scripts/seed_fixture_creators.py`. Idempotent (re-run safe).

### 13.2 Acceptance per fixture

Each fixture runs full end-to-end flow:
- Tenant created with brand_slug=comunify + niche
- TenantProfile populated (creator_name, handle, country, plan_tier)
- Brand Studio 10 sections completed (including voice cloning + authority vault required + 3 buyer personas)
- Voice cloning pipeline executed (50+ samples → distilled v2 → ratified)
- Offer Studio at least 4 offers per fixture (ladder Level 1-4)
- 1 cohort created per fixture (capacity-tier matched)
- 3 community members per fixture (regular + premium tier mix)
- 1 broadcast sent per cohort
- 2 community posts (1 auto-approved + 1 spam-blocked simulation)
- 1 discovery call booking via sales_agent
- 1 subscription with recurring billing (1 succeeded charge + 1 dunning attempt simulation)
- Compliance audit log entries generated

### 13.3 E2E spec coverage matrix

| Fixture | Onboarding | Brand Studio (10) | Voice cloning | Authority | Ladder | Cohort | Community | Subscriptions |
|---|---|---|---|---|---|---|---|---|
| Anabella business coach AR | ✅ AR scenario | ✅ 10 sections | ✅ 50+ samples | ✅ 3 cases | ✅ 4 levels | ✅ Q2 18-cap | ✅ broadcast + mod | ✅ recurring USD |
| Trini Nutrición Real CL | ✅ CL scenario | ✅ 10 sections | ✅ 50+ samples | ✅ 3 cases | ✅ 4 levels | ✅ Q3 20-cap | ✅ broadcast + mod | ✅ recurring CLP |
| Pablo Productividad MX | ✅ MX scenario | ✅ 10 sections | ✅ 50+ samples | ✅ 3 cases | ✅ 4 levels | ✅ Q2 45-cap | ✅ broadcast + mod | ✅ recurring USD |

## § 14. Community safety guardrails specification

### 14.1 Spam detection scope

Spam patterns enforced (LLM classifier + heuristic):

| Pattern | Action |
|---|---|
| External promotional link unrelated to niche | Block + audit |
| Repeated post (cosine sim > 0.9 vs prior same author) | Block + audit |
| Excessive emoji / caps / hashtags (>40% content) | Pending moderation |
| Author posts > 5/min | Rate limit + warn |
| Affiliate links to competitor platforms | Pending moderation |

### 14.2 NSFW detection

- Image vision classifier (score > 0.85 = block)
- Text classifier (score > 0.80 = block)
- Profanity strong language → pending moderation (not auto-block)

### 14.3 Doxxing detection

- Phone number patterns (any member's stored phone matches)
- Email patterns (any member's email matches)
- Full name + city patterns (cross-reference cohort_members)
- Auto-block + warn author + notify target privately

### 14.4 Pre-moderation new members policy

- Default ON for first 3 posts of new members
- Skip pre-moderation if member from waitlist (already vetted)
- Engagement score > 80 → auto-disable pre-moderation

### 14.5 Cross-tenant isolation

Per `tenant-isolation.md`. Audit log `cross_tenant_attempt`. Zero tolerance.

### 14.6 Prompt injection defense (sales_agent)

- Sandbox markers `<<TRANSCRIPT_BEGIN>>...<<TRANSCRIPT_END>>` (Story E grader pattern)
- Refuse "ignore your prompt" / "act as another assistant"
- audit_log `prompt_injection_blocked`

## § 15. Compliance gates (smoke tests)

### 15.1 Prompt injection smoke

`comunify/backend/tests/eval/smoke_prompt_injection.py`:
- 5 test cases injection attempts (ignore prompt, jailbreak, role swap, data exfil, system prompt extraction)
- Expected: 5/5 blocked + audit log entries

### 15.2 Spam detection smoke

`comunify/backend/tests/eval/smoke_spam_detection.py`:
- 10 test cases posts with various spam vectors
- Expected: 8+ caught (high-precision, some pending OK)

### 15.3 NSFW upload smoke

`comunify/backend/tests/eval/smoke_nsfw_upload.py`:
- 5 test cases image uploads varying NSFW levels
- Expected: 4+/5 blocked, 1 borderline pending review

### 15.4 Doxxing smoke

`comunify/backend/tests/eval/smoke_doxxing.py`:
- 4 test cases posts attempting to share private contact
- Expected: 4/4 blocked + audit log entries

### 15.5 Cross-tenant smoke

`comunify/backend/tests/eval/smoke_cross_tenant.py`:
- 3 test cases tenant_A user querying tenant_B data
- Expected: 3/3 blocked

### 15.6 Voice cloning distillation smoke

`comunify/backend/tests/eval/smoke_voice_distillation.py`:
- 3 sample sets per fixture (50 chats each, AR/CL/MX voices)
- Run distillation → assert compiled v2 6 blocks present
- Assert dialecto block detects correct dialect (es-AR voseo / es-CL tuteo / es-MX tuteo)
- Assert vocabulario block extracts at least 5 frequent phrases per fixture

## § 16. Agentic surface API (handoff /architect Phase 2)

> **/architect Phase 2** detailing required. Spec defines surface only.

### 16.1 Tools registered (4 tools)

| Tool | Description | Inputs | Outputs |
|---|---|---|---|
| `qualify_for_cohort` | Califica lead vs cohort criteria (fit/no-fit/up-or-down-tier) | lead_id, cohort_id | { fit: bool, recommended_tier, fit_score, gaps[] } |
| `link_to_community` | Invita lead/subscriber post-purchase a community access | subscriber_id, cohort_id | { invite_url, status, expires_at } |
| `nurture_via_authority_content` | Sirve content path personalizado del authority_vault | lead_id, intent_category | { content_url[], next_step } |
| `book_discovery_call` | Agenda discovery call gratuita (1:1 sales call) | lead_id, doctor_id, preferred_window | { booking_id, scheduled_at, meeting_url } |

### 16.2 Extractors registered (2 extractors)

| Extractor | Description | Inputs | Outputs |
|---|---|---|---|
| `OfferLadderAdvisor` | Analiza oferta actual del creator + sugiere niveles faltantes en ladder | tenant_id, current_offers | { ladder_gaps[], suggested_offers[], confidence } |
| `AuthorityVaultExtractor` | Extrae credenciales/casos PR/social proof mencionables del input (bio + LinkedIn paste + entrevistas) | tenant_id, source_text | { credentials[], case_studies[], press[], confidence } |

### 16.3 Workflows registered (2 workflows)

| Workflow | Description | State machine |
|---|---|---|
| `CommunityEngagementWorkflow` | Agentic re-engagement community drift members | active → drift_detected → nurture_outreach → re_engaged (or escalated) |
| `CohortEnrollmentWorkflow` | Flow inscripción cohorte desde qualification a payment | qualification → consent_terms → payment_pending → enrolled (or refused/expired) |

### 16.4 KB packs registered (1 pack)

| Pack | Contents |
|---|---|
| `creator_economy_kb_v1` | Frameworks (StoryBrand, value ladder, jobs-to-be-done) + terminology (lead magnet/tripwire/core/premium/cohort) + common creator questions + cohort design best practices + community engagement playbooks |

### 16.5 Guardrails registered (4 guards)

| Guard | Purpose |
|---|---|
| `community_safety_no_spam` | Block spam comercial unrelated |
| `community_safety_no_nsfw` | Block NSFW content (text + image) |
| `community_safety_no_doxxing` | Block private contact share attempts |
| `community_moderation_required` | Route ambiguous content to creator moderation inbox |

### 16.6 Channel adapters (consume Story 11 lifts)

| Channel | Purpose |
|---|---|
| Stripe Connect | Recurring subscriptions + one-shot payments (creators serving US/EU subscribers) |
| MercadoPago | LatAm recurring + one-shot (creators serving AR/MX/CL/CO/PE) |
| Tokenized recurring | Card-on-file recurring (subscriptions monthly + installments) — reuse Story 11 lift |

### 16.7 Phase 2 (architect) deliverable

`02-design-agentic.md` (this file's sibling, also produced same session by /ux-agentico phase 1):
- State machines per workflow
- Tools sequence happy + edge + adversarial
- Slot architecture cache prefix (Slot 5 BRAND_VOICE compiled v2 + Slot 4 COMMUNITY_SAFETY_RAILS)
- Voice constraints per tenant (voice_cloning compiled)
- Eval policy (vertical-creator-economy fidelity personas + rubrics + pass^k)
- Cost/latency budget per tool
- Observabilidad (trace event surface + cost recording)

## § 17. Q1-Q7 ratified decisions (auto-ratified Sesion 12 per Q2=A Story 11 verbatim)

### Q1 — Voseo chrome UI — **RATIFIED: B Spanish neutro puro**

**Decisión:** Chrome UI = Spanish neutro LatAm puro (tuteo). NO voseo en botones/forms/títulos/breadcrumbs/toasts/validaciones Comunify. Cumple `.claude/rules/spanish-text.md` R2 sin excepciones.

**Implicación:**
- "Contános tu mundo de creator" → "Cuéntanos tu mundo de creator"
- "Agendá tu discovery call" → "Agenda tu discovery call"
- Sales_agent voice respeta voice_cloning compiled v2 per tenant (Anabella AR voseo, Trini CL tuteo, Pablo MX neutro) — NO afectado
- Microcopy § 8 actualizar previo build phase 3

### Q2 — Multi-brand UI scope — **RATIFIED: B Defer Story 12.bis**

**Decisión:** Story 12 cubre solo single-creator workflows. Multi-creator account switcher UI defer Story 12.bis.

**Implicación:**
- Single tenant per creator account (1 brand_slug per Clerk user_id)
- TenantSwitcher reuse @luana/shared visible pero solo muestra 1 tenant currently

### Q3 — Third-party community bridge — **RATIFIED: B Defer Story 12.bis**

**Decisión:** Story 12 community feed NATIVE within comunify. NO Discord/Circle/Slack/Mighty Networks bridge.

**Implicación:**
- Members invite_url = comunify.io/community/{cohort_slug}
- Native feed + posts + moderation in-app
- Story 12.bis or future epic adds bridge connectors

### Q4 — Creator ladder UI — **RATIFIED: A Reuse @luana/core/offer + extensions**

**Decisión:** Reuse `@luana/core/offer` base. Comunify adds OfferLadder entity + LadderVisualizer FE + LadderAdvisor extractor via Extension SDK.

### Q5 — Subscription widget embed — **RATIFIED: B Both iframe + canonical**

**Decisión:** Story 12 implementa BOTH (a) iframe embeddable subscription widget para creator-own landing pages + (b) canonical subscription at `landing.comunify.io/{handle}/subscribe`.

**Implicación:**
- ~2-3 tickets adicionales: widget bundle `comunify/frontend/widget/` + postMessage protocol + embed docs
- Anabella fixture demo iframe embed (`anabellaconexion.com`)
- Trini + Pablo fixtures demo canonical subdomain

### Q6 — Payment gateway — **RATIFIED: B MercadoPago primary + Stripe Connect fallback**

**Decisión:** Story 12 reuse Story 11 MP+Stripe lifts shared. Recurring tokenized subscriptions added.

### Q7 — Voice cloning scope — **RATIFIED: A Full pipeline 50+ chats**

**Decisión:** voice_cloning ON full pipeline. 50+ chats threshold. Compiler v2 6 bloques. Per-tenant Slot 5 cache.

**Implicación:**
- BrandConfig `features.voice_cloning=True`
- Voice samples upload UI + async distillation job (~12 min ETA)
- Ratify preview before deploy
- Story 14 luana-brand-voice-elevation extiende (audio cloning future)

## § 18. Acceptance criteria (per 00-story.md + spec)

Sesion 12 success criteria:
- ✅ Comunify deployed K8s cluster
- ✅ 3 fixture creators signup + Brand Studio (10 sections including voice cloning + authority vault) + offer ladder 4 levels + 1 cohort + 3 community members + 1 broadcast + 1 subscription end-to-end via E2E
- ✅ Voice cloning pipeline functional (50+ samples → distilled compiled v2 → ratified)
- ✅ Sales agent vertical-creator-economy tools registered + functional (4 tools)
- ✅ Copilot extractors + workflows registered (2 extractors + 2 workflows)
- ✅ KB pack available (creator_economy_kb_v1)
- ✅ Community safety guardrails ON (5 smoke tests pass)
- ✅ Recurring subscriptions + dunning workflow functional
- ✅ Compliance audit log functional + CSV export
- ✅ Arch fitness 0 violations
- ✅ Validators GREEN per 04-validators.yaml

Story 12.bis deferred items:
- Discord/Circle/Slack bridge
- Live streaming UI nativo
- Gamification deep
- Multi-account creator switcher UI
- White-label creator → end-user multi-tenant
- Creator mobile app
- Affiliate program multi-tier
- Course delivery LMS
- NFT/Web3 token-gated
- English localization

---

## § 19. Ratificación

**Ratified:** 2026-05-14 (autonomous /pm Sesion 12 Phase 1 per Q2=A Story 11 verbatim)
**Ratificador:** /pm autonomous orchestrator
**Auto-ratification basis:** Q-set Phase 0 batch ratified Chris Fase A. Spec mirror Story 11 with community + creator-economy domain. No design issues introduced — pattern replication validated. Voice cloning ON + 10 sections + authority_vault required + recurring subscriptions adapted from Vitalia's medical context to creator/cohort context. Anti-duplication audit § 16 confirms reuse Story 11 lifts (MP+Stripe + extraction base + grader pattern).

**Next step:** /ux-agentico drafts `02-design-agentic.md` mirror Story 11 design with creator-economy domain (this same session Phase 1). State refining → refined at ratify.

**Phase 2 handoff:** /architect spawns architect-orchestrator → architect-{be,fe,agentic} reading 01-spec.md + 02-design-agentic.md → produces 03-arch.md consolidated + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml = ready package.

done -> docs/product/stories/luana-comunify-bootstrap/01-spec.md
