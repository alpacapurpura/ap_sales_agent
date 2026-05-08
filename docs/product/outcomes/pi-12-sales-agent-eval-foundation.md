---
id: pi-12-sales-agent-eval-foundation
state: refining
title: Sales Agent — eval foundation (synthetic-first eval architecture pre-launch)
why_now: |
  Sales_agent NO está en producción + NO hay conversaciones reales (no podemos
  lanzar algo que funcione a medias — una venta perdida = cliente perdido).
  Necesitamos validar el agente PRE-LAUNCH con synthetic-first eval (dual-LLM
  simulator pattern, state-of-the-art mayo 2026). State-of-the-art (Anthropic
  Bloom + AWS Strands Evals + τ-Bench + PersonaGym): empezar con tenants seed
  realistas + personas como simulators + 20-30 goldens curados manualmente +
  pass^k all-trials threshold. CI gate bloquea regressions. Cuando salgamos
  a prod con clientes reales, layer "production-replay" se agrega encima sin
  tirar nada.
target_end: null
priority: 1
created: 2026-05-04
last_modified: 2026-05-07
migrated_from: docs/projects/active/PI-12-sales-agent-eval-foundation/
reframe_date: 2026-05-06
reframe_reason: |
  Discovery con Chris reveló que paradigma original ("extraer goldens de
  producción") era inviable — sales_agent no está en producción. Reframe
  completo a synthetic-first basado en research mayo 2026.
story_ids:
  # done (archived 2026-05-06):
  - sales-agent-eval-runner-foundation
  - sales-agent-litellm-canonicalization

  # foundation new (NEW — sub-épica eval-foundation-*):
  # - maintenance-skill-sales-agent-audit        # DONE 2026-05-06 (archived, skill SSoT auditado)
  # - eval-foundation-tenant-seed-data           # DONE 2026-05-07 (archived, 5 tenants seed curados densamente — story A foundation)
  # - eval-foundation-simulator-homologation     # DONE 2026-05-08 (archived, Story B — dual-LLM simulator + 3 cost-bucket tables + 5 NEW arch fitness gates + frozen golden v1 + R3 SSoT update)

  # spawned 2026-05-06 from tenant-seed-data Q7 (placeholder, state=idea):
  - sales-agent-dialect-configuration            # TBD, feature UX tenant config dialecto BCP-47 + runtime injection

  # foundation reframe (story IDs originales preservados — slug intact, narrative reframed):
  - sales-agent-personas-instrumented-runtime    # → role C: personas-as-simulators (REFINED 2026-05-08 — spec v3 + design v2 + delta v1 ratified, awaiting /architect)
  - sales-agent-goldens-3-tenants-dataset        # → role D: goldens-generated-from-simulation
  - sales-agent-voice-fidelity-grader-runtime    # → role E: MAJ-EVAL voice fidelity grader
  - sales-agent-eval-pass-k-tracking             # → role F: Bloom-style pass^k
  - sales-agent-voice-fidelity-ci-gate           # → role G: CI gate w/ dynamic threshold
  - sales-agent-eval-cost-budget-cap             # → role H: cost cap (no major change)
  - sales-agent-adversarial-jailbreak-suite      # → role I: PersonaGym Toxicity Control axis
success_metrics:
  - "3 tenants seed con data realística completa (brand+offer+personality+pricing+buyer_personas) checked-in y consumibles por sales_agent runtime sin mocks"
  - "client_simulator/ homologado a backend/tests/agentic_evals/sales_agent/simulator/ con dual-LLM pattern (1 LLM=user persona, 1 LLM=sales_agent real)"
  - "20-30 goldens generados desde simulación + curados manualmente por Chris, checked-in"
  - "pass^k=3 trials all-pass threshold enforced en CI (Bloom 4-stage Understanding/Ideation/Rollout/Judgment)"
  - "Voice fidelity grader MAJ-EVAL multi-judge debate >= 0.7 promedio. Falla → PR bloqueado"
  - "Cost <= $0.50/session p95, 0% trials cost_usd=0"
  - "PersonaGym 5-axis coverage: Action Justification, Expected Action, Linguistic Habits, Persona Consistency, Toxicity Control"
tags:
  - module:sales-agent
  - type:agentic-eval-foundation
  - paradigm:synthetic-first
  - reframe:2026-05-06
legacy_exempt: true  # WIP cap exempt — pre-paradigma v4 (2026-05-06)
---

# Sales Agent — Eval Foundation (synthetic-first, reframe 2026-05-06)

> **Reframe 2026-05-06** desde paradigma original "extraer goldens de producción"
> a synthetic-first eval architecture. Razón: sales_agent NO está en producción
> + clientes reales NO usan el sistema todavía. State-of-the-art mayo 2026
> (Anthropic Bloom + AWS Strands Evals + τ2-Bench + PersonaGym + MAJ-EVAL)
> recomienda exactamente este enfoque para pre-launch validation.

> **Migrated 2026-05-06** (Wave 5 Punto 4) desde `docs/projects/active/PI-12-sales-agent-eval-foundation/`
> (paradigma legacy PI/Sprint) a paradigma v4 (`docs/product/outcomes/` flat).
> 2 stories ya hechas archivadas. 7 stories pendientes preservadas con slug
> original (no rename masivo per R9 — el reframe es narrativa, no estructural).

## Vision

Cada PR a `modules/sales_agent/` se gradea automáticamente vs eval suite synthetic:
- 3 tenants seed (Coach LatAm humano + Consultorio médico + Agencia growth+influencer)
- 5+ personas como simulators (lead-frio, lead-tibio, lead-caliente, tenant-experto, tenant-novato)
- Dual-LLM multi-turn (1 LLM persona ↔ sales_agent real)
- Voice fidelity per tenant (MAJ-EVAL multi-judge debate threshold 0.7)
- No-hallucination, no-overpromise rubrics en scenarios adversarial
- Tool trajectory correcta (closer specialist sequence)
- Pass^k=3 all-trials para customer-facing (no any-trial)
- Cost <= budget per session sin cost tracking degraded
- PersonaGym 5-axis coverage

Resultado: confianza para lanzar sales_agent con clientes reales SIN ansiedad
"puede que rompa la voz tenant" o "puede que cueste más" o "puede que diga algo
inapropiado". CI gate bloquea regressions automáticamente.

## 3 Archetypes seed (ratificados Chris 2026-05-06)

> Detalle completo en `docs/product/stories/eval-foundation-tenant-seed-data/00-story.md`.

### A1 — Coach LatAm humano (Visionarias-style)

- Referencia real: https://visionarias.lat (PE / PEN, 2 founders)
- Driver: comunidad + transformación, no venta-por-venta
- Tono: cercano, emocional, voz humana (audio personalizado planificado)
- Ticket: bajo-medio. Volumen: alto. Multi-product offer ladder real.
- Stack:
  - Comunidad en Mighty Networks o Skool (membresía)
  - Productos digitales (cursos, workshops)
  - Lead magnets (PDFs, masterclasses gratis)
  - Podcast YouTube + Spotify + otros
  - Multi-persona (2 chicas → 2 voces distintas para clone futuro)
- Offer ladder:
  - L0 lead magnet (PDF gratis "5 errores que cometes...")
  - L1 entry product (workshop $19)
  - L2 core product (curso $97)
  - L3 community (membresía mensual $29/m)
  - L4 high-ticket (mentoría 1:1 $497)
- Buyer personas target: emprendedoras LatAm 25-45, mujeres, buscan transformación + comunidad

### A2 — Consultorio médico/dental con personal brand

- Referencias reales:
  - https://www.instagram.com/dr.cardiometabolico/ (cardiólogo)
  - https://www.instagram.com/dr.juandiegovigo/ (médico)
  - https://www.tiktok.com/@dr.wagnerwilliams (dermatólogo, TikTok-first)
  - https://www.instagram.com/dra.andreacuya/ (dermatóloga)
  - https://www.instagram.com/dentalindo/ (clínica dental)
- Driver: autoridad clínica + confianza + cercanía
- Tono: profesional cálido, paciente-céntrico (NO "cliente"). Lenguaje cuidado.
- Ticket: medio-alto. Volumen: medio. Recurrencia (controles, tratamientos).
- Stack:
  - Consultas individuales
  - Tratamientos paquete (ortodoncia 12m, blanqueamiento, etc)
  - Paquetes preventivos / control anual
  - Educación gratis (reels, lives) → conversión a consulta
- Funnel típico: descubre por reel → DM consulta → agenda primera cita → tratamiento
- Buyer personas target: pacientes con dolencia específica + paciente preventivo + paciente referido

### A3 — Agencia growth/marketing con influencer-CEO

- Referencias reales:
  - https://www.instagram.com/brander.studio/ (branding)
  - https://www.instagram.com/toga.pe/ (growth)
  - https://www.instagram.com/brandtech.pe/ (brand tech)
- Driver: autoridad técnica + casos de éxito + ROI demostrable
- Tono: B2B confidente, ROI-driven, frameworks-based. Casual-pro.
- Ticket: alto. Volumen: bajo. Retainers recurrentes.
- Stack:
  - Productized services (paquetes branding $X, growth audit $Y)
  - Retainers mensuales (gestión + estrategia)
  - Workshops/masterclasses (lead magnet)
  - Casos de éxito como motor (testimonios + métricas)
- Funnel típico: ve casos en feed → descarga lead magnet → agenda discovery call → propuesta → cierra retainer
- Buyer personas target: emprendedor LatAm con negocio establecido buscando escalar + agencia/freelance que tiene presupuesto

> Estos 3 son los iniciales. Chris confirmó (2026-05-06) que después agregaremos
> más archetypes según fricción real. Cada nuevo archetype = 1 story sub-tipo de
> `eval-foundation-tenant-seed-data` con slug `eval-foundation-tenant-seed-{slug}`.

## Stories — re-decomposición synthetic-first

### ✅ Done (5 — archivadas a docs/archive/2026/stories/)

| Story | Done date | Capability promoción |
|---|---|---|
| `sales-agent-eval-runner-foundation` | 2026-05-06 | sales-conversational-engine (eval suite path establecido) |
| `sales-agent-litellm-canonicalization` | 2026-05-06 | sales-observability-cost-tracking (LiteLLM canonical path) |
| `maintenance-skill-sales-agent-audit` | 2026-05-06 | NA (maintenance — skill `sales-agent-expert` SSoT auditado, 9 stories downstream desbloqueadas) |
| `eval-foundation-tenant-seed-data` | 2026-05-07 | sales-conversational-engine (5 archetypes seed + dialect_catalog BCP-47) |
| `eval-foundation-simulator-homologation` | 2026-05-08 | sales-conversational-engine (dual-LLM simulator + 3 cost-bucket tables + 5 NEW arch fitness gates + frozen golden v1 + R3 SSoT update) |

### 🔬 Refining — 8 stories (synthetic-first eval foundation, dependency graph below)

#### Foundation (paths críticos)

| Story | Role | Type | Estimate | Spec status |
|---|---|---|---|---|
| ~~`eval-foundation-tenant-seed-data`~~ | **A** — DONE 2026-05-07 (archived) | service | 3-4d | done |
| ~~`eval-foundation-simulator-homologation`~~ | **B** — DONE 2026-05-08 (archived) | service | 2-3d | done |
| `sales-agent-personas-instrumented-runtime` | **C** — 15 archetype-aware personas (3 kinds × 5 tenants) + ActorProfile schema v2 + customer prompt v2 sub-slots + Scenarios 5+6 (qualification accuracy + nurture multi-question) | agentic | 3-4d (post v3 expansion) | **refined** 2026-05-08 (spec v3 + design v2 + delta v1 ratified) |
| `sales-agent-goldens-3-tenants-dataset` | **D** — generar 20-30 goldens desde simulación + curación Chris (reframe v1→v2) | service | 4-5d | refining (01-spec.md v1 archivado, v2 awaiting reframe) |

#### Eval layer

| Story | Role | Type | Estimate | Spec status |
|---|---|---|---|---|
| `sales-agent-voice-fidelity-grader-runtime` | **E** — MAJ-EVAL multi-judge debate sobre voice fidelity vs personality_profile | agentic | 3d | refining |
| `sales-agent-eval-pass-k-tracking` | **F** — Bloom 4-stage pass^k=3 all-trials threshold | service | 2d | refining |
| `sales-agent-eval-cost-budget-cap` | **H** — cost cap por run (sin cambio mayor) | service | 1d | refining |

#### CI + adversarial

| Story | Role | Type | Estimate | Spec status |
|---|---|---|---|---|
| `sales-agent-voice-fidelity-ci-gate` | **G** — CI gate con threshold dinámico (daily→weekly→monthly per Q8) | service | 2d | refining |
| `sales-agent-adversarial-jailbreak-suite` | **I** — PersonaGym Toxicity Control axis + jailbreak/injection probes | agentic | 3d | refining |

**Total restante:** ~25-30d (vs 18d original — alcance ampliado por reframe).

### Dependency graph

```
maintenance-skill-sales-agent-audit  (PRE — ✅ DONE 2026-05-06)
                  │
                  ▼
   eval-foundation-tenant-seed-data  (A — 3-4d, blocker absoluto)
                  │
                  ├──▶ eval-foundation-simulator-homologation  (B — 2-3d)
                  │                  │
                  │                  └──▶ sales-agent-personas-instrumented-runtime  (C — 2d)
                  │                                            │
                  │                                            ▼
                  └──▶ sales-agent-goldens-3-tenants-dataset  (D — 4-5d)
                                            │
                  ┌─────────────────────────┼─────────────────────────────┬─────────────────────┐
                  ▼                         ▼                             ▼                     ▼
   sales-agent-voice-fidelity-grader   sales-agent-eval-pass-k    sales-agent-eval-cost   sales-agent-adversarial
                  (E — 3d)                  (F — 2d)                  (H — 1d)                (I — 3d)
                  │                         │                             │                     │
                  └─────────────────────────┴─────────────┬───────────────┴─────────────────────┘
                                                          ▼
                                  sales-agent-voice-fidelity-ci-gate  (G — 2d)
```

### Política de update dataset (Q8 ratificado Chris 2026-05-06)

NO calendarizado fijo. Frecuencia dinámica:

- **Lanzamiento → 1-2 semanas**: review diario goldens vs runtime real (high-volatility)
- **Mes 1-3**: review semanal (estabilizando)
- **Mes 3+**: review mensual (estable)
- **Triggers ad-hoc**:
  - Voice fidelity grader saturate >0.95 promedio (overfitting signal)
  - Cambio mayor en `personality_profiles` schema
  - Nuevo archetype tenant agregado

> Como startup, cada día hay nuevas funcionalidades + nuevos pedidos. Revisar
> "cada 6 meses" no aplica — para esa fecha ya estamos en otra versión.

## Migration note

Migrado de paradigma legacy PI/Sprint (2026-05-04 → 2026-05-06) a paradigma v4 (10 estados). Razón: cap WIP `refining ≤ 3` excedida pero `legacy_exempt: true` aplica forward-only enforcement. Reframe synthetic-first 2026-05-06 trajo 3 stories nuevas (skill-audit + tenant-seed + simulator-homologation) y reframe narrativo de 7 stories existentes (slugs preservados — no rename masivo per R9).

Original PI.md preservado en `docs/archive/2026/legacy-pis/PI-12-sales-agent-eval-foundation/PI.md` (Wave 4 archive).

## Bitácora

- 2026-05-04 — `/pm` creó PI-12 paradigma legacy + 9 stories en sprints S1-S4
- 2026-05-06 — Story `sales-agent-eval-runner-foundation` shipped (state=done)
- 2026-05-06 — Story `sales-agent-litellm-canonicalization` shipped (state=done)
- 2026-05-06 — Migración a paradigma v4: outcome creado en `docs/product/outcomes/`, 7 stories pendientes movidas a `docs/product/stories/{id}/` flat con `state=refining`, 2 stories done archivadas, legacy folder eliminado
- 2026-05-06 17:11Z — **Reframe synthetic-first** (Chris ratificó 3 archetypes A1/A2/A3). Outcome narrative re-escrito post-research mayo 2026. 3 stories nuevas: maintenance-skill-sales-agent-audit + eval-foundation-tenant-seed-data + eval-foundation-simulator-homologation. 7 stories existentes preservadas con slug original — reframe narrativo en outcome.
- 2026-05-06 19:55Z — Story `maintenance-skill-sales-agent-audit` cerró ready package (`/po` v2 ratified → `/architect` consolidado). State refining→refined→ready en una sesión.
- 2026-05-06 20:55Z — Story `eval-foundation-tenant-seed-data` cerró spec ratification (`/po` v2). **Scope expandido por Chris 3→5 archetypes** (A1 Coach PE + A2 Medicina estética MX + A3 Clínica dental CO + A4 Growth Marketing video+RRSS AR + A5 Agencia Automatización IA neutro 419). State refining→refined. Handoff a `/architect` pendiente. Spawned `sales-agent-dialect-configuration` (placeholder state=idea) durante Q7 — feature UX tenant config dialecto BCP-47, refinement futuro.
