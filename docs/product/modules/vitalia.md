---
module: vitalia
last_audit: 2026-05-14
status: active                                  # active | maintenance | placeholder
links:
  capabilities_dir: "../capabilities/vitalia/"
  stories_dir: "../stories/"
  domain_doc: null                              # vitalia lives in luana-platform monorepo, no AISALESHT domain doc
active_projects: []                              # auto-populated by /pm cuando hay outcomes activos tocando este módulo
capability_registry_status: bootstrapped-2026-05-14
agentic_eval_suite_path: "luana-platform/vitalia/backend/tests/agentic_evals/"
home_repo: alpacapurpura/luana-platform
home_path: vitalia/
---

# vitalia — Estado funcional

## Meta
| Campo | Valor |
|---|---|
| Studio padre | Vertical Brand App (luana-platform) |
| Estado | activo — bootstrap completed Story 11 (2026-05-14) |
| Última actualización | 2026-05-14 (Story 11 done) |
| Doc técnico | N/A — código en `luana-platform/vitalia/` repo separado |
| Origin story | `docs/archive/2026/stories/luana-vitalia-bootstrap-2026-05-14/` |

## Qué hace por el user

Vitalia = primer vertical brand app sobre `luana-platform` Extension SDK. App medical/wellness multitenant para clínicas LATAM (dental, psicología, psiquiatría, wellness). Cada clínica = tenant aislado. Posición: SaaS marketing/sales/booking integral para profesionales de salud sin skills tech.

Capacidades core:
- Booking online con prevención doble-reserva (advisory_locks)
- Pago prepaid + tokenized recurring (MercadoPago + Stripe Connect)
- AI agent medical-safe con 4 guardrails (no diagnóstico, no prescripción, disclaimer obligatorio, prompt-injection block)
- 3 KB packs especializados (dental ~150 chunks + psicología ~200 + psiquiatría 131)
- Workflow follow-up tratamientos vía LangGraph + cron
- Widget booking embebible con postMessage protocol
- 3 clínicas LATAM fixtures (Aurora AR + Mindful CL + Sanaré MX)

## Capacidades
> Auto-list generated from `docs/product/capabilities/vitalia/`.
> See `docs/product/BACKLOG.md` "Capabilities snapshot" for current count + status.

## Capacidades operables desde copilot

- Ver bookings del día (live)
- Configurar tratamientos + precios (live)
- Ver historial paciente (live, con PII masking)
- Activar/pausar AI agent medical (live)
- Ajustar voz vía Brand Studio communication-style (live, sales-agent voice exception OK)
- **Gap:** integración insurance LATAM (deferred Story 11.bis)

## Extension SDK mounting

Vitalia es el **primer vertical brand consumer** del Extension SDK (`core/luana-core-extension-sdk/`, Story 6). Implementa register_all entrypoint mounting EP-1..EP-18:

- BrandConfig declarative YAML (`vitalia/config/brand.yaml`)
- 4 AGENTIC tools (prepaid_payment_check + medical_consent_request + appointment_reschedule_with_doctor + treatment_followup_check)
- 2 PDF extractors (MedicalKBExtractor + DentalHistoryExtractor)
- 1 LangGraph workflow (TreatmentFollowupWorkflow)
- 4 guardrails (prompt_injection_block reuse + medical_safety_no_diagnosis + medical_safety_no_prescription + medical_disclaimer_required)
- 3 KB packs Qdrant tenant-filtered
- Offer preset medical-services
- Slot 4 MEDICAL_SAFETY_RAILS (10-slot prompt architecture extension)

## LLM routing

Reusa `luana-core-llm` (LiteLLM Proxy single dispatch). Mismo cost tracking runtime que sales_agent (`CostRecorderCustomLogger`). Cost bucket: vitalia agentic writes `copilot_llm_call` for production runtime; eval simulator writes `eval_simulator_llm_call` (separation cemented).

## R23 compliance

100% — los 14 production_code:true AGENTIC tickets de Story 11 spawn-con `builder-agentic` Opus 4.7 EXCLUSIVE. Tests-over-agentic R23 exempt: T-eval-1 + T-e2e-1.

## Estado calidad funcional

| Capacidad | Estado | Notas |
|---|---|---|
| Booking + advisory_locks | sólido | T-be-5 unit tests PASS, integration deferred (Postgres) |
| Pago MercadoPago | sólido | T-payment-1 LIFT shared, 38/38 + 100/100 core regression |
| Pago Stripe Connect | sólido | T-payment-2, 16/16 (integration skip) |
| Webhooks HMAC + idempotency | sólido | T-be-8 21/21 |
| 4 AGENTIC tools | sólido | All R23 Opus, downstream tests GREEN |
| 4 guardrails | sólido | T-guards-1/2/3, 47+47+64 tests + 99/367 regression |
| 3 KB packs | sólido | ~481 chunks total Qdrant tenant-filtered |
| 2 PDF extractors | sólido | MedicalKB + DentalHistory FDI 4-wave vision |
| TreatmentFollowupWorkflow | sólido | LangGraph 2.0 + RedisSaver-ready + cron |
| Prompt 10-slot + MEDICAL_SAFETY_RAILS | sólido | T-prompts-1 51/51 V-AE-22 |
| Booking widget UMD | sólido | T-widget-1 25/25 + 594.84 kB bundle |
| FE 21 routes + 567 vitest | sólido | T-fe-1..5 all PASS |
| E2E Playwright 112 tests | tsc clean | runtime deferred Story 11.bis |
| Spanish neutro chrome UI | sólido | T-fe-3 microcopy SSoT + voseo arch test |
| PII masking + ComplianceEvent | sólido | HIPAA-lite posture documented |
| Postgres integration tests | deferred | Story 11.bis runtime sprint OR CI Postgres step |
| Multi-site clinic UI | deferred | Q2 spec deferred Story 11.bis |
| Insurance LATAM | deferred | Q3 spec deferred Story 11.bis |
| Wellness deep coverage | partial | Q7 ratificó UI-enabled básico; deep coverage Story 11.bis |

## Deferred to Story 11.bis runtime sprint

- Postgres integration tests execution (idempotency `upgrade head` × 2 not runtime-exercised yet)
- Playwright dev server runtime (tsc + list clean, runtime needs `npm run dev`)
- Multi-site clinic UI (Q2 ratified deferred)
- Insurance LATAM module (Q3 ratified deferred)
- Wellness deep coverage
- W9 parallel git race mitigation (serialize push per-wave via Haiku worker OR worktrees ratificación)

## Cross-repo working model

- **Code:** `/home/chris/luana-platform/vitalia/` (luana-platform monorepo, branch=main, 38 feature commits)
- **Docs/SSoT:** `/home/chris/AISALESHT/docs/product/{capabilities/vitalia/, modules/vitalia.md, stories/luana-vitalia-bootstrap → archived 2026-05-14}/`
- **Tests:** `luana-platform/vitalia/backend/tests/` (unit + integration + agentic_evals)
- **Deploy:** `luana-platform/vitalia/deploy/` (K8s manifests + CF tunnel + Clerk app #2 + DNS)

## Outcome lineage

Story 11 closes vertical-medical bootstrap. Outcome `luana-platform-migration` 11/14 stories complete (~79% complete). Remaining 3 stories: Comunify (vertical-community), [TBD], [TBD].
