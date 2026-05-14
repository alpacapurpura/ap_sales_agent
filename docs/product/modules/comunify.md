---
module: comunify
last_audit: 2026-05-14
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/comunify/"
  stories_dir: "../stories/"
  domain_doc: null                              # comunify lives in luana-platform monorepo, no AISALESHT domain doc
active_projects: []                              # auto-populated by /pm cuando hay outcomes activos tocando este módulo
capability_registry_status: bootstrapped-2026-05-14
agentic_eval_suite_path: "luana-platform/comunify/backend/tests/agentic_evals/"
home_repo: alpacapurpura/luana-platform
home_path: comunify/
---

# comunify — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Vertical Brand App (luana-platform) |
| Estado | activo — bootstrap completed Story 12 (2026-05-14) |
| Última actualización | 2026-05-14 (Story 12 done) |
| Doc técnico | N/A — código en `luana-platform/comunify/` repo separado |
| Origin story | `docs/archive/2026/stories/luana-comunify-bootstrap-2026-05-14/` |

## Qué hace por el user

Comunify = segundo vertical brand app sobre `luana-platform` Extension SDK. App creator/expert economy multitenant para creadores de contenido LATAM (life coaching, photography, gastronomy, education, wellness). Cada creador = tenant aislado. Posición: SaaS marketing/sales/community integral para creadores expertos sin skills tech — el AI agent hace la labor de SDR/closer mientras el creador se enfoca en su expertise.

Capacidades core:
- Gestión de cohortes con prevención de doble-enrollamiento (advisory_locks)
- Subscripciones recurrentes tokenizadas + DunningWorkflow LangGraph (MercadoPago + Stripe Connect)
- AI agent creator-safe con 4 guardrails comunitarios (spam/nsfw/doxxing/prompt_injection)
- Voice cloning pipeline NEW — 4-wave VoiceDistillationOrchestrator extrae y compila voz auténtica del creador
- KB pack creator economy ~180 chunks (pricing strategies + community building + offer ladders)
- OfferLadderExtractor con gap detection y pricing anchoring LATAM
- AuthorityVaultExtractor: testimoniales/casos de éxito → señales de autoridad para el agent
- Widget de subscripción embebible (UMD bundle)
- 3 creadores LATAM fixtures (Anabella AR + Trini CL + Pablo MX)

## Capacidades
> Auto-list generated from `docs/product/capabilities/comunify/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot

- Ver cohortes activos y enrollamiento actual (live)
- Configurar plan tiers y precios (live, via EP-17 override)
- Ver historial de subscripciones y estado dunning (live)
- Activar/pausar AI agent comunitario (live)
- Ajustar voz via voice cloning pipeline (live — VoiceDistillationOrchestrator)
- Ver authority vault: testimoniales + casos de éxito (live)
- Ver análisis de offer ladder con gap detection (live)
- **Gap:** integración advanced analytics por cohorte (deferred Story 12.bis)

## Extension SDK mounting

Comunify es el **segundo vertical brand consumer** del Extension SDK (`core/luana-core-extension-sdk/`, Story 8). Implementa register_all entrypoint mounting EP-1..EP-18:

- BrandConfig declarative YAML (`comunify/config/brand.yaml`)
- 4 AGENTIC tools (query_creator_kb + get_cohort_status + check_subscription_status + get_creator_profile)
- 2 LLM extractors (OfferLadderExtractor 4-wave + AuthorityVaultExtractor)
- 2 LangGraph workflows (CommunityEngagementWorkflow + DunningWorkflow embedded en recurringsubscriptions)
- 4 guardrails comunitarios (spam_detection + nsfw_content + doxxing_prevention + prompt_injection_block)
- 1 KB pack Qdrant tenant-filtered (~180 chunks creator economy)
- Voice cloning pipeline NEW (VoiceDistillationOrchestrator 4-wave — CompiledVoice Slot 5)
- Slot 4 COMMUNITY_SAFETY_RAILS (10-slot prompt architecture extension)
- EP-17 plan tier override (creador define sus propios precios)

## LLM routing

Reusa `luana-core-llm` (LiteLLM Proxy single dispatch). Mismo cost tracking runtime que Vitalia + sales_agent (`CostRecorderCustomLogger`). Cost bucket: comunify agentic production → `copilot_llm_call`; eval simulator → `eval_simulator_llm_call` (separation cemented Story B precedent).

## R23 compliance

100% — los 17 production_code:true AGENTIC tickets de Story 12 spawneados con `builder-agentic` Opus 4.7 EXCLUSIVE:
T-extensions-1, T-prompts-1, T-kb-1, T-tools-1..4 (4), T-extractors-1..2 (2), T-workflows-1..2 (2), T-guards-1..4 (4), T-voice-1..3 (3 de 4; T-voice-4 = tests/docs over agentic → Sonnet OK per R23).

## Estado calidad funcional

| Capacidad | Estado | Notas |
|---|---|---|
| Cohort management + advisory_locks | sólido | T-be-3 + T-be-5 unit tests PASS, cross-tenant isolation |
| Pago MercadoPago + Stripe | sólido | T-payment-1 LIFT shared, regresión PASS |
| DunningWorkflow LangGraph | sólido | T-workflows-2 5-node PASS |
| CommunityEngagementWorkflow | sólido | T-workflows-1 PASS |
| 4 AGENTIC tools | sólido | All R23 Opus, downstream tests GREEN |
| 4 guardrails comunitarios | sólido | T-guards-1..4, 47+47+64+smoke tests PASS |
| Voice cloning pipeline NEW | sólido | T-voice-1..4, VoiceDistillationOrchestrator inherits base (arch fitness) |
| KB pack creator economy | sólido | ~180 chunks Qdrant tenant-filtered |
| OfferLadderExtractor 4-wave | sólido | T-extractors-1, gap detection unit tests PASS |
| AuthorityVaultExtractor | sólido | T-extractors-2 PASS |
| Prompt 10-slot + COMMUNITY_SAFETY_RAILS | sólido | T-prompts-1 Slot 4 markers arch fitness PASS |
| Subscription widget UMD | sólido | T-widget-1 bundle PASS |
| FE 13 routes + 26 Vitest | sólido | T-fe-1..6 all PASS (2-iter audit fixes applied) |
| E2E Playwright | tsc clean | runtime deferred Story 12.bis |
| Spanish neutro chrome UI | sólido | T-fe-3 microcopy SSoT + voseo arch test (AR fixtures exempt) |
| PII masking + response_model= | sólido | C4 cross-cutting PASS audit |
| Agentic eval suite | sólido | T-eval-1 + T-rubric-1 502/502 agentic_evals + 144/144 arch |

## Deferred to Story 12.bis

- FE 14 page-level clients (currently smoke stubs — representative coverage)
- ESLint 60+ rule set wiring (per Story 11 vitalia precedent)
- Error boundaries / error.tsx per Next.js 16 App Router
- Barrel `index.ts` per feature
- Vitest coverage threshold 20%
- Prompt injection lift to shared when Story 13 Lupulo introduces same (N=2→3 threshold)
- BE `domain/` subdir extraction (DDD inside-out completeness — non-blocking, post-merge)
- Playwright runtime (tsc + list clean, runtime needs `npm run dev`)
- Analytics per cohort (advanced metrics deferred)

## Cross-repo working model

- **Code:** `/home/chris/luana-platform/comunify/` (luana-platform monorepo, branch=main)
- **Docs/SSoT:** `/home/chris/AISALESHT/docs/product/{capabilities/comunify/, modules/comunify.md, stories/luana-comunify-bootstrap → archived 2026-05-14}/`
- **Tests:** `luana-platform/comunify/backend/tests/` (unit + integration + agentic_evals)
- **Deploy:** `luana-platform/comunify/deploy/` (K8s manifests + CF tunnel + Clerk app #3 + DNS)

## Outcome lineage

Story 12 closes vertical-creator-economy bootstrap. Outcome `luana-platform-migration` 12/14 stories complete (~86% complete). Remaining 2 stories: Lupulo (vertical-gastronomy) + brand-voice-elevation refactor.

## Story 12 vs Story 11 key differences

- Voice cloning pipeline ON (NEW — 4-wave VoiceDistillationOrchestrator, Story 11 had no voice cloning)
- Brand Studio FULL 10 sections (Vitalia used 4)
- compliance_level=creator_economy (NOT hipaa_lite) — community safety guardrails replacing medical_safety
- Recurring subscriptions ON NEW (cohort installments + monthly memberships + DunningWorkflow)
- 2 LangGraph workflows (vs Vitalia 1 — CommunityEngagementWorkflow + DunningWorkflow)
- Q3=C serial parallelization_cap: 1 (vs Story 11 cap 2 — safer per Chris ratification)
- 39 tickets (vs Story 11 38)
