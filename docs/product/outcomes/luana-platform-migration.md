---
outcome_id: luana-platform-migration
slug: luana-platform-migration
state: developing                               # 10-state v4 — Story 1 done 2026-05-11, Phase B Story 2 in flight
phase: story_1_done_phase_b_active
created_at: 2026-05-09
created_by: chris + claude-opus-4-7
last_modified: 2026-05-11
stories_done: [luana-foundation, luana-shared-lift, luana-iam-tenancy-content]   # 2026-05-11 all 3
stories_active: [luana-crm-analytics-landing-connections]     # 2026-05-11 — Phase D autonomous batch session 1
target_close_window: 2026-09-15                # 14-16 sem migration + 4 sem stabilization (1 Claude sequential, no parallel)
priority: P0                                    # blocks all other product work
repo_topology: monorepo                         # ★ ratified 2026-05-10 ★ alpacapurpura/luana-platform single repo with subfolders core/ + nicolify/ + vitalia/ + comunify/ + lupulo/
repo_url: https://github.com/alpacapurpura/luana-platform.git
license: proprietary                            # ★ ratified 2026-05-10 ★ All rights reserved, private repo
gh_packages_strategy: deferred                  # ★ ratified 2026-05-10 ★ workspace-internal (uv + pnpm) until Story 9 publishing
claude_subs: 1                                  # ★ ratified 2026-05-10 ★ scope reduced from 5 to 1, sequential build, progressive sub additions Q3-Q4 2026
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
ratified_by_chris: true                        # ★ ratified 2026-05-10 ★ ADR-001 + scope decisions confirmed
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

### 2.2 State + WIP cap honored (REVISED 2026-05-10 — 1 Claude sequential)

- 1 Claude Code Max sub disponible. Stories ejecutan **secuencialmente**, no paralelo.
- Chris compra subs adicionales progresivamente Q3-Q4 2026 — cuando lleguen Stories 11-13 (~Sem 9-10), tal vez ya 2-3 subs disponibles, recuperar paralelo si aplicable.
- WIP `developing` ≤ 3 cap intacto pero usage actual = 1 con 1 sub.
- WIP `reviewing` ≤ 2 cap intacto.
- Timeline original (8 sem) extendido a **14-16 sem migration + 4 sem stabilization** = target close ~2026-09-15.

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

### 3.2 Dependencies externas (REVISED 2026-05-10)

- ✅ Chris ratificó ADR-001 + scope decisions (2026-05-10)
- ✅ Chris creó repo `alpacapurpura/luana-platform` (private, empty)
- ⏸ Subs adicionales Claude Code Max — progressive, NO bloqueante (1 sub OK para arrancar)
- ⏸ Story E sales-agent-voice-fidelity-grader-runtime → `done` (bloquea solamente Story 7, no Stories 1-6)

## 3.3 Anti-island pattern (futuros colaboradores)

Cuando Chris contrate colaboradores (TBD), aplicar pattern para preservar SSoT discipline:

| # | Pattern | Mecánica |
|---|---|---|
| 1 | **CODEOWNERS** | Paths críticos (`core/copilot/`, `core/sales-agent/`, `core/shared/`) requieren review Chris. Generated en Story 1 T-X. |
| 2 | **ADR mandatory** | Todo cambio core (cross-module behavior, schema, API contract) requiere ADR en `docs/architecture/ADR/`. Sin ADR → PR rejected. |
| 3 | **Conventional Commits + PR template** | Colaborador responde "qué + por qué + qué módulos toca". Auto-link a outcome/story id. |
| 4 | **Branch protection main** | PR mandatory + required checks (lint+test+arch-fitness) + 1 review (Chris) + signed commits. |
| 5 | **/pm SSoT enforcement** | Todo feature pasa por outcome → story → ready package. NO commits sueltos a core sin ticket asociado. |
| 6 | **Brand isolation por path** | Colaborador asignado a `vitalia/` no toca `core/` ni `nicolify/`. CODEOWNERS bloquea. |
| 7 | **No new patterns sin lift shared** | Si colaborador-A en vitalia/ inventa patrón útil, antes de agregar en core → /pm review + lift formal. Anti-mirror per `.claude/rules/anti-duplication.md`. |

Cuando 2+ devs onboard → formalizar `docs/process/collaboration-protocol.md`. Por ahora pattern arriba alcanza.

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
| Founder + CEO | Chris | 2026-05-10 | ✅ ratified ADR-001 + 3 scope decisions (monorepo + proprietary + defer GH Packages) |
| Outcome curator | /pm skill (Opus 4.7) | 2026-05-09 → updated 2026-05-10 | drafted + revised post ratification |
| Architecture | ADR-001 ratification | 2026-05-10 | ✅ ratified by Chris (verbal) |

### 7.1 Scope decisions ratified 2026-05-10

| Decisión | Valor | Razón |
|---|---|---|
| Repo topology | **Monorepo** (`alpacapurpura/luana-platform`) | 1 Claude sub + Chris solo + colaboradores TBD. Refactor a multi-repo cuando contrate equipo per-brand. |
| License | **Proprietary** | Estándar SaaS B2B. Repos privados. Tu IP. |
| GH Packages publishing | **Diferido** hasta Story 9 | Workspace-internal (uv + pnpm) sin overhead publishing inicial. Story 9 introduce publish pipeline. |
| Claude subs | **1 actual**, progressive Q3-Q4 2026 | Stories ejecutan secuencial. Timeline +6 sem. |

### 7.2 Autonomous execution policies ratified 2026-05-11

Para que /pm + /po + /architect + /dev-team + /auditor + /pm merge ejecuten en una sola conversación sin Chris approval per story.

| Policy | Valor ratificado | Aplica a |
|---|---|---|
| **Pre-auth spec/design ratification** | **AUTO** si stay within ADR-001 + outcome §3.3 anti-island + 3 scope decisions §7.1 + lift mode §7.3 | Stories 2-4 (shared-lift, iam-tenancy-content, crm-analytics-landing-connections) |
| **Audit failure response** | Auto-fix Opus cap 3 iter, después escalar Chris | Todas autonomous stories |
| **Sonnet cap_reached on ticket** | Auto-rescate Opus puntual SOLO en ese ticket | Todas autonomous stories |
| **Budget per session** | **NO HARD CAP** — Chris tracking externo. Soft check-ins a $500 / $1000 / $1500 cumulative (Claude reporta progress + cost a Chris pero no para) | Todas autonomous stories |

### 7.3 Lift mode constraint precise (Stories 2-4)

Para que auto-spec/design/arch ratification sea segura, "lift mode" significa EXACTAMENTE:

**MUST DO:**
- Lift código existente AISALESHT (`backend/src/{shared,modules/X}/`) → `luana-core/python/luana-core-{name}/src/luana_core_{name}/` preservando boundaries DDD verbatim
- Preserve file names + class names + function signatures + public API surface
- Preserve tests verbatim (`tests/modules/X/` → `luana-core/python/luana-core-{name}/tests/`) — same structure
- Preserve module imports topology (no merging modules, no splitting modules)
- Add per-package: `pyproject.toml` (uv workspace member, version 0.0.1-alpha) + `__init__.py` + `README.md` stub
- Add per-package: `package.json` (pnpm workspace member, version 0.0.1-alpha) si hay TS deliverable
- Update import paths: `from src.shared.X` → `from luana_core_X` (Python) o `@luana/x` (TS)
- Register in workspace root: `pyproject.toml` workspace members + `pnpm-workspace.yaml` packages
- Tests pass: same coverage threshold as AISALESHT (BE 43% / FE 20%)

**MUST NOT DO (escalate Chris if needed):**
- ❌ Scope expansion (don't add features, don't introduce new abstractions)
- ❌ Refactor module boundaries (don't merge brand+offer into one package)
- ❌ Rename modules or change public API (anti-anti-island principle)
- ❌ Change tech stack defaults (Python 3.12, SQLA 2.0, FastAPI, Pydantic v2 — same as AISALESHT)
- ❌ New patterns not in AISALESHT (don't introduce dependency injection framework if AISALESHT doesn't have one)
- ❌ Schema migration changes (Stories 2-4 lift code, NOT migrations — migrations stay in brand apps)
- ❌ Cross-brand architecture decisions (schema ownership ambiguous → STOP, escalate)
- ❌ Drop/deprecate code without explicit Chris ratify

**Halt criteria (auto-stop + escalate Chris):**
1. Scope expansion needed (mechanical lift impossible without refactor)
2. Cross-brand architecture decision discovered
3. New tech stack decision required
4. Auditor REJECTED + 3 auto-fix Opus iter all fail
5. Cascade fail: Sonnet cap_reached → Opus rescue also fail
6. Cumulative session cost exceeds $1500 → soft check-in (yo reporto, Chris confirma continuar)

### 7.4 Stories per session capacity (1 Claude)

| Tier | Stories | Per-conversation cap | Notes |
|---|---|---|---|
| Tier 1 fully autonomous | 1 (luana-foundation, ready) | 1 story session 1 | Build only — ready package existe |
| Tier 2 lift-mode autonomous | 2-4 (shared-lift + iam-tenancy + crm-analytics) | up to 3 stories session 1 | /pm spec → /architect → /dev-team → /auditor → merge |
| Tier 3 mid-flight check-in | 5-7 (brand-offer + copilot + sales-agent — R23 Opus para 6+7) | 1 story per session | Decisiones design surfacing — Chris check-in mid-flight |
| Tier 4 per-story ratify | 8-14 (extension SDK + brand bootstraps) | 1 story per session | Decisiones verticales/architectural |

**Realistic session 1 plan:** Stories 1 + 2 + 3 + 4 closed = 4 stories cumulative (~$700-1600, ~30h tool-time wall).

Después: Chris evaluates, ratifica Stories 5-7 individualmente.

---

**Next steps post-ratification (REVISED 2026-05-10):**
1. ✅ /pm spawns architect-orchestrator → revise Story 1 ready package for monorepo + proprietary + defer GH Packages (in progress 2026-05-10)
2. /pm Story 1 state refining → refined → ready post architect re-emit
3. /dev-team picks Story 1 T-1 → autonomous build (Sonnet OK, no R23 trigger — infra only)
4. /auditor when Story 1 developed → CHECKPOINTS C1-C5
5. /pm merge → capability promoted → Story 2 unparked → repeat per /pm v4 paradigm
6. Stories 11-14 originally paralelas → secuenciales 1 Claude (revisit cuando subs adicionales lleguen Q3-Q4)
