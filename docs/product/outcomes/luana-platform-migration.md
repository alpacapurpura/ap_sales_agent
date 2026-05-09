---
outcome_id: luana-platform-migration
slug: luana-platform-migration
state: refining                                # 10-state v4
phase: outcome_decomposition
created_at: 2026-05-09
created_by: chris + claude-opus-4-7
last_modified: 2026-05-09
target_close_window: 2026-07-31                # 8 sem migration + 4 sem stabilization
priority: P0                                    # blocks all other product work
business_outcome: "Operate 4 vertical SaaS brands (Nicolify + Vitalia + Comunify + Lupulo Labs) on shared Luana core with brand-isolated deployments, enabling core improvements to ripple to 4 brands automatically while preserving vertical-specific adaptations via formal extension points"
hypothesis: "Multi-Brand Vertical SaaS pattern (canonical industry pattern: ServiceTitan, Toast, Mindbody) reduces cost to launch new vertical from months to weeks while preserving SSoT discipline. Validated by 14 atomic stories shipping incrementally with /pm v4 state machine + validators + auditor checkpoints."
success_metrics:
  - "Luana core v0.1.0 published to GitHub Packages with 22+ versioned packages and 5 critical extension points"
  - "Nicolify migrated to consume Luana with zero functional regression (all current tests pass)"
  - "3 new brand apps (Vitalia, Comunify, Lupulo) bootstrapped with vertical-specific extensions registered"
  - "Each brand deployed to isolated K8s cluster + Postgres + Qdrant with own Clerk app"
  - "Operating cost stays within $1100-1400/mo budget"
  - "Zero core code branches conditional on brand identity (arch fitness enforced)"
related_adrs:
  - "docs/architecture/luana-platform/adr/ADR-001-luana-platform.md"
related_audits:
  - "docs/architecture/luana-platform/01-core-audit.md"
ratified_by_chris: false                       # ★ awaiting Chris ratification post Sunday 2026-05-11 ★
legacy_exempt: false                            # this outcome uses v4 paradigm fully
---

# Outcome: Luana Platform Migration

## 1. Resumen ejecutivo

Migrar de **single-repo Nicolify multi-tenant** a **multi-brand Vertical SaaS architecture** con `luana-core` SSoT compartido + 4 brand apps deployment-isolated. Pattern canónico industria (ServiceTitan, Toast, Mindbody, Procore). Detalle arquitectónico: ADR-001.

**4 brands target:**
- Nicolify (SaaS marketing/sales — caso canónico horizontal)
- Vitalia (medical/dental/wellness clinics — prepaid bookings, medical KB)
- Comunify (creator/expert economy — offer ladder, authority vault, community)
- Lupulo Labs (gastronomy agentic — booking + ordering + kitchen integration)

**Mecánica:** `luana-core` publica packages versionados (semver) a GitHub Packages. Cada brand consume `luana-core-*` (Python) + `@luana/*` (TypeScript). Brands materializan divergencia via (a) `BrandConfig` declarativo o (b) extension points formales. Cero `if (brand === ...)` en core (arch fitness enforce).

**Por qué este outcome:** sin esta migración, agregar brand #2 (Vitalia) crea fork-pain o lasagna de condicionales. Con migration completada, brand #5 marginal cost decrece (skeleton + extension registration). SSoT real = mejoras al copilot + sales_agent rippean a 4 brands automáticamente.

## 2. Stories propuestas (14 stories — DAG)

```
Story 1 — Foundation (GitHub Org + 5 repo skeletons + CI baseline + .claude-shared subtree)
   ↓
Story 2 — Lift `shared/` (~10 cores: observability, billing, compliance, idempotency, llm, events, channels, extraction, platform, ui-kit base)
   ↓
Story 3 — Lift IAM + Tenancy + Content (iam, tenant_profile, tenant_domains, commercial_calendar, social_proof, assets)
   ↓
Story 4 — Lift CRM + Analytics + Landing + Connections engine
   ↓
Story 5 — Lift Brand Studio + Offer Studio (catalogs DAG, form-runtime, presets, voice compiler v2 elevated)
   ↓
Story 6 — Lift Copilot engine (LangGraph + observability + tool/workflow/extractor registries)
   ↓
Story 7 — Lift Sales Agent engine (post Story E `done`; eval framework deferred to v0.2.0)
   ↓
Story 8 — Lift Campaigns engine + define Extension SDK (EP-1..EP-5 formal)
   ↓
Story 9 — Publish Luana v0.1.0 to GitHub Packages (production-grade alpha)
   ↓
Story 10 — Migrate Nicolify (rename AISALESHT → nicolify, swap imports to @luana/*, zero regression)
   ↓ ─────────────────┐ ─────────────────┐ ─────────────────┐
   ↓                  ↓                  ↓                  ↓
Story 11 — Vitalia   Story 12 — Comunify   Story 13 — Lupulo   Story 14 — Brand-voice elevation refactor
   bootstrap            bootstrap             bootstrap            (post-merge cleanup;
   (vertical-medical)   (vertical-creator-    (vertical-           PersonalityProfile +
                        economy)              gastronomy)          voice cloning to core-brand-studio)
```

### 2.1 Story dependencies (blocked_by)

| Story ID | Blocks | Blocked by |
|---|---|---|
| `luana-foundation` | 2 | — |
| `luana-shared-lift` | 3 | 1 |
| `luana-iam-tenancy-content` | 4 | 2 |
| `luana-crm-analytics-landing-connections` | 5 | 3 |
| `luana-brand-offer-studios` | 6 | 4 |
| `luana-copilot-engine` | 7 | 5 |
| `luana-sales-agent-engine` | 8 | 6 + Story E `done` (sales_agent eval) |
| `luana-campaigns-extension-sdk` | 9 | 7 |
| `luana-v0-1-0-publish` | 10 | 8 |
| `luana-nicolify-migration` | 11, 12, 13, 14 | 9 |
| `luana-vitalia-bootstrap` | — | 10 |
| `luana-comunify-bootstrap` | — | 10 |
| `luana-lupulo-bootstrap` | — | 10 |
| `luana-brand-voice-elevation` | — | 10 (can run parallel to 11-13) |

### 2.2 State + WIP cap honored

- Stories 11-14 pueden correr paralelo (4 Claude subs distintos)
- WIP `developing` ≤ 3 → Stories 11-13 corren paralelo, 14 espera o se intercala
- WIP `reviewing` ≤ 2 → /auditor procesa de a 2 stories simultáneas máx

### 2.3 Skills + cost routing

| Story | Surface | /dev-team skill | Modelo |
|---|---|---|---|
| 1-9 (Luana lift) | mixed (BE/FE infra + agentic engine cores) | `dev-team` | **Opus 4.7** (R23 — sales_agent + copilot production code) |
| 10 (Nicolify migration) | BE imports + FE imports + tests | `dev-team` | Sonnet OK (no agentic production code, mostly mechanical refactor) |
| 11-13 (brand bootstraps) | BE config + FE theme + vertical extensions | `dev-team` | Sonnet for FE/config; Opus for vertical agentic (medical KB, kitchen tools) |
| 14 (brand voice elevation) | BE refactor (port-based) | `dev-team` | Opus (touches sales_agent surface) |

## 3. Risks + dependencies

### 3.1 Risks materiales

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | Story E (`sales-agent-voice-fidelity-grader-runtime`) `developed (pending audit)` blocks Story 7 lift | High | /auditor dispatch immediate (2026-05-09); track verdict by 2026-05-11 |
| 2 | Coupling oculto entre módulos no documentado | High | Story 1 incluye dependency-graph audit task |
| 3 | Brand voice contract estable cross-brand | High | Semver enforcement + tests downstream R3 obligatorios en Luana CI |
| 4 | Migration data Nicolify → split (DB schema acoplado entre módulos) | Medium | Dual-write 2-week cutover window, scripts idempotentes |
| 5 | 2 de 4 brands pueden no validar mercado | Medium | Monthly go/no-go review, parked state available per brand |
| 6 | 5 paralelos Claude Code subs sin overlap | Low (positivo) | Cada uno en SU repo, cero parallel-safety pain heredado |
| 7 | Trough Sem 1-5 sin features nuevos Nicolify | Medium | Communicate to existing customers, freeze feature requests |
| 8 | Costos Sentry per-brand + Postgres backups | Low | Budget reviewed +$150-200/mo, included in $1100-1400/mo total |

### 3.2 Dependencies externas

- Chris ratifica ADR-001 (target 2026-05-11)
- Chris compra 4 Claude Code Max subs adicionales (5 totales)
- Chris crea GitHub Org `luana-platform` (Story 1 deliverable)
- Story E sales-agent-voice-fidelity-grader-runtime → `done` (target 2026-05-12 post /auditor)

## 4. Stories archive map (post-completion)

Cuando outcome cierre `done` (estimado 2026-07-31):

```
docs/archive/2026/outcomes/luana-platform-migration/
├── outcome.md (frozen snapshot)
├── stories/
│   ├── luana-foundation/                 ← all 14 stories archived here
│   ├── luana-shared-lift/
│   └── ...
├── adr-001-luana-platform.md (frozen snapshot)
└── core-audit-final.md
```

**Critical:** post-Story-11, /pm SSoT promotes from `AISALESHT/docs/product/` to `luana-core/docs/product/`. This outcome is the LAST major outcome managed in `nicolify` repo. After it: each brand has its own `docs/product/` for vertical-specific stories.

## 5. Capabilities promotion

Al cerrar outcome:

| Capability path | Status promotion |
|---|---|
| `docs/product/capabilities/luana-core/multi-brand-platform.yaml` | NEW — bootstrapped |
| `docs/product/capabilities/luana-core/extension-sdk.yaml` | NEW — bootstrapped |
| `docs/product/capabilities/copilot/` (existing) | Migrated to `luana-core/docs/product/capabilities/copilot/` |
| `docs/product/capabilities/sales-agent/` (existing) | Migrated to `luana-core/docs/product/capabilities/sales-agent/` |
| `docs/product/capabilities/{brand,offer,...}/` (todos) | Migrated to luana-core |
| Brand-specific capabilities | Bootstrapped en cada brand repo |

## 6. Backlog post-outcome (Luana v0.2.0+)

Stories que NO entran en este outcome pero quedan registradas en backlog:
- Eval framework lift (post Story E stabilization, ~Sem 9)
- Voice cloning feature flip per-tenant (Sem 10+)
- 13 backlog extension points (EP-6..EP-18, formalizar incrementalmente)
- Cross-brand telemetry aggregation (OpenTelemetry Grafana Cloud, Sem 12+)
- Brand #5 onboarding template (cuando business justifique)

## 7. Ratification

| Role | Person | Date | Status |
|---|---|---|---|
| Founder + CEO | Chris | _PENDING_ | awaiting ratification 2026-05-11 |
| Outcome curator | /pm skill (Opus 4.7) | 2026-05-09 | drafted |
| Architecture | ADR-001 ratification | _PENDING_ | docs/architecture/luana-platform/adr/ADR-001 |

---

**Next steps post-ratification:**
1. /po service-stories (no UI) opens 01-spec.md per Story 1-9 (engine lifts, no UI work)
2. /po-ux opens 01-spec.md per Story 10-14 (brand bootstraps incluyen UI theming)
3. /architect spawns architect-orchestrator per story → 03-arch + 04-validators + 05-guidelines + 06-tickets = ready package
4. /dev-team picks Story 1 first → autonomous build → /auditor → done
5. Repeat ticket-por-ticket per story per /pm v4 paradigm
