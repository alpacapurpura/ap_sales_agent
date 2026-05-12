---
outcome_id: luana-platform-migration
slug: luana-platform-migration
state: developing                               # 10-state v4 — Story 1 done 2026-05-11, Phase B Story 2 in flight
phase: story_5_done_phase_c_active
created_at: 2026-05-09
created_by: chris + claude-opus-4-7
last_modified: 2026-05-12
stories_done: [luana-foundation, luana-shared-lift, luana-iam-tenancy-content, luana-crm-analytics-landing-connections, luana-brand-offer-studios, luana-copilot-engine, luana-sales-agent-engine, luana-campaigns-extension-sdk, luana-v0-1-0-publish]   # 2026-05-12 all 9 (Stories 1-4 session 1 + Story 5 session 2 + Stories 6+7 session 3 + Stories 8+9 session 4 secuencial autonomous)
stories_active: [luana-nicolify-migration]   # 2026-05-12 Session 5 — Story 10 ratified Chris (10 business decisions cemented §7.6) transition parked→refining
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

### 7.2 Autonomous execution policies ratified 2026-05-11 (extended session 2 + session 3 2026-05-11)

Para que /pm + /po + /architect + /dev-team + /auditor + /pm merge ejecuten en una sola conversación sin Chris approval per story.

| Policy | Valor ratificado | Aplica a |
|---|---|---|
| **Pre-auth spec/design ratification** | **AUTO** si stay within ADR-001 + outcome §3.3 anti-island + 3 scope decisions §7.1 + lift mode §7.3 | Stories 2-4 (sesión 1) + **Story 5** (sesión 2) + **Stories 6+7** (sesión 3 extension, Chris mandate 2026-05-11: secuencial autonomous, R23 Opus mandatory all tickets) |
| **Audit failure response** | Auto-fix Opus cap 3 iter, después escalar Chris | Todas autonomous stories |
| **Sonnet cap_reached on ticket** | Auto-rescate Opus puntual SOLO en ese ticket | Todas autonomous stories (Stories 6+7 R23 → Opus only, no Sonnet eligibility) |
| **Budget per session** | **NO HARD CAP** — Chris tracking externo. Soft check-ins a $500 / $1000 / $1500 / $2500 cumulative (Claude reporta progress + cost a Chris pero no para) | Todas autonomous stories |

**Story 5 autonomy rationale (sesión 2):** Story 5 nominalmente Tier 3 (§7.4) — design surface posible (voice compiler v2 elevation + voice cloning feature flag). Mitigación: ambas decisiones ya ratificadas en ADR-001 §2.4 (compiler elevado a core-brand-studio, cloning flag declarativo por brand en BrandConfig). Por tanto Story 5 ejecuta como lift-mode con design-decisions pre-ratificadas. NO surface design decisions cardinales → autonomy segura.

**Stories 6+7 autonomy rationale (sesión 3, 2026-05-11):** Cap §7.4 extendido a **2 stories Tier 3 secuencial** esta sesión, análogo a §7.2 Story 5 extension. R23 Opus mandatory all tickets (agentic production code) — esperado ~$2000-3500 sesión.

**3 ratificaciones business sesión 3:**
1. **§7.4 cap extendido a 2 stories Tier 3** — Stories 6+7 secuencial autonomous, análogo Story 5
2. **Story 7 eval gate WAIVED a Luana v0.2.0** — Story E (sales-agent-voice-fidelity-ci-gate) bloqueada por PI-12 eval-foundation incompleta. Lift Story 7 sales_agent runtime SIN Story E done; voice fidelity CI gate diferido hasta v0.2.0 ship completo del eval framework. Documentar como blocker WAIVED en Story 7 checkpoint + DEFERRED-FILES
3. **R23 Opus mandatory all tickets** — Stories 6+7 production agentic code. ALL tickets owner=builder-agentic Opus 4.7. NO Sonnet eligibility

**6 decisiones técnicas Chris mandate "cero deuda + máxima escalabilidad" (baked en architect prompt):**

| ID | Decisión | Implicación architect |
|---|---|---|
| **D-T1** | Lift mode con preservación de contratos para Story 8 EP formalization | Tool/workflow/extractor registries (copilot) interfaces preserved EXACTLY. Story 8 wrappea como EP-1..EP-5 sin refactor mayor. Arch fitness Story 6: `test_copilot_registry_contracts_stable.py` |
| **D-T2** | Cross-module mapper cleanup Stories 5→6→7 | Story 6 lifta `MessageModel` (copilot owns) → offer-studio conftest MIGRA stub a real import. Arch fitness `test_no_residual_test_stubs_post_story_6.py`. Zero deuda técnica residual |
| **D-T3** | Voice compiler integration Story 7 via BrandVoicePort hexagonal | Story 7 introduce port + impl + consumer per ADR-001 §2.4. `BrandVoicePort` interface en luana-core-brand-studio + concrete `BrandVoiceCompilerAdapter` + DI consumer en luana-core-sales-agent. Arch fitness `test_sales_agent_uses_voice_port_no_direct_compiler_import.py` |
| **D-T4** | Single architect spawn para AMBAS stories | UN solo architect-orchestrator Opus produce ready packages 6+7 en una pasada — cross-Story decisiones coordinadas |
| **D-T5** | builder-agentic + auditor-agentic specialists | Build Stories 6+7 = `builder-agentic` Opus. Audit Stories 6+7 = `auditor-agentic` Opus. Schema-mirror exception (backend-ddd §"Schema-mirror exception") sigue válido si shared/ migration ripple |
| **D-T6** | Cross-module mapper Story 6 specific solutions | Copilot lift toca LangGraph 2.0 StateGraph + checkpointers (verbatim), Anthropic prompt cache slots 5min/1h TTL (preserve), copilot_trace_event + copilot_llm_call observability (lift via shared/agent_observability inherit per anti-duplication.md), tool/workflow/extractor registries (D-T1), Qdrant RAG tenant filtering, module registry. ready package 03-arch.md tabula cada subsystem + lift strategy + tests downstream regression per R3 auditor-downstream-regression.md |

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
| Tier 3 mid-flight check-in | 5-7 (brand-offer + copilot + sales-agent — R23 Opus para 6+7) | 1 story per session DEFAULT, up to 2 per session if pre-ratified (sesión 3 precedent — Stories 6+7 secuencial autonomous) | Decisiones design surfacing — Chris check-in mid-flight |
| Tier 4 per-story ratify | 8-14 (extension SDK + brand bootstraps) | 1 story per session | Decisiones verticales/architectural |

**Realistic session 1 plan:** Stories 1 + 2 + 3 + 4 closed = 4 stories cumulative (~$700-1600, ~30h tool-time wall). **Real:** 4/4 closed ~10.5h ~$390 (2026-05-11).

**Session 2 plan (2026-05-11):** Story 5 sola autonomous per Chris mandate. §7.2 extended Story 5 lift-mode pre-auth (design decisions ya ratificadas ADR-001 §2.4). ~14-20 tickets, target ~3-6h. **Real:** 1 story closed ~3h ~$390 (ish — Session 2 stats en 07-merge.md).

**Session 3 plan (2026-05-11):** Stories 6+7 secuencial autonomous per Chris mandate. §7.2 extended Stories 6+7 lift-mode pre-auth con 6 decisiones técnicas (D-T1..D-T6) + 3 ratificaciones business pre-baked. R23 Opus mandatory all tickets. ~33-47 tickets total (18-25 Story 6 + 15-22 Story 7). Target ~$2000-3500 cumulative session 3.

Después: Chris evaluates session 3 stats, ratifica Stories 8+ individualmente.

**Session 4 plan (2026-05-12):** Stories 8+9 secuencial autonomous per Chris mandate. §7.4 extended to **3 stories Tier 3 sequencial** with pre-ratified design decisions §7.5 (Story 8 SDK design) + §7.1 scope (Story 9 publish — license proprietary + GH Packages + monorepo already ratified). R23 NOT triggered (Story 8 SDK + campaigns engine = production_code=false; Story 9 = pure infra/CI). Sonnet eligible for non-agentic tickets, Opus for agentic surfaces (EP-3 sales_agent tool wrappers + EP-4 copilot workflow wrappers freeze contracts from Stories 6+7 frozen registries). Target ~$2000-3500 cumulative session 4.

### 7.5 Session 4 — Story 8 SDK design decisions (ratified 2026-05-12 — Chris delegated `toma tú todas las decisiones`)

7 business decisions + 13 backlog EP signatures + 5 cross-cutting policies cemented BEFORE refining→refined transition. Architect Story 8 consumes §7.5 as binding spec.

#### 7.5.1 Cross-cutting policies (apply to all 18 EPs)

| ID | Policy | Rationale |
|---|---|---|
| **CC-1** | Signature pattern **per-EP natural** — data (DataClass) for declarative metadata, Callable for behavior handlers | matches EP-1..EP-5 hybrid pattern. Forced uniformity = artificial. |
| **CC-2** | **Default append + override case-by-case** via explicit `mode='append'\|'override'` flag (where applicable per EP) | brand mostly extends core menu. Override exception, not norm. |
| **CC-3** | **Startup-only registration** universal for all 13 backlog EPs | fail-fast at FastAPI lifespan event. Type-safe. Runtime-dynamic register deferred v0.2.x if surfaces. |
| **CC-4** | **Strict raise on duplicate + namespaced obligatorio** (`vitalia.foo_extractor`, never bare `foo_extractor`) | brand isolation cross-brand. Cross-brand learning happens via /pm core promotion path, never via cross-namespace consumption. |
| **CC-5** | **Inmutable post-startup** — no `unregister_*` API | simple. State mutation bugs prevented. Brand re-deploys for changes. |

#### 7.5.2 Decisions 2-7 (Phase 0 questions resolved)

| # | Question | Decision | Rationale |
|---|---|---|---|
| 1 | SDK Scope | **B — EP-1..EP-5 críticos + EP-6..EP-18 signatures-only** | Chris ratified 2026-05-12. Contrato público estable desde v0.1.0 Story 9 publish. |
| 2 | Discovery mechanism | **B — Explicit register in brand startup** via FastAPI lifespan event (`registry = ExtensionRegistry(); register_all(registry); app = create_app(registry=registry)`) | type-checked, debuggable, no setuptools magic. Each brand controls if/when/how. |
| 3 | BrandContext shape | **Full + extensible frozen dataclass** — fields: `tenant_id, brand_slug, plan_tier, locale, feature_flags, tenant_profile_id, vertical_kind, compliance_flags, pii_policy`. Future fields opcionales agregables sin breaking bump (handler ignora si no usa) | handlers ricos en metadata. Pagar precio hoy vs refactor mañana. |
| 4 | SDK versioning | **C — Strict alpha minor/patch from v0.0.8 + flip real SemVer Story 9 publish** | hábito disciplinado pre-publish + lockdown post-publish con tests downstream R3. |
| 5 | Examples docs | **B — Per-vertical concrete examples** (Vitalia + Comunify + Lupulo) + **vertical-agent-recipe doc** Story 8 ships en `docs/extension-points.md` | pre-think Stories 11-13 bootstraps. Docs son docs, fácil update si decisión cambia. |
| 6 | Stub brand test pack | **A — Includes Story 8** `apps/test-brand/` smoke test EP-1..EP-5 ejecutables + EP-6..EP-18 NotImplementedError graceful smoke (registry receives all, handler raises if invoked) | SDK ships v0.0.8-alpha with live integration test. Riesgo silente eliminado. |
| 7 | Pre-auth scope Session 4 | **B — Stories 8+9 secuencial autonomous** (cap §7.4 extended to **3 stories Tier 3 secuencial**). Halt si Story 9 GH Packages config requiere Chris token/org setup | Story 9 = lift-mode-equivalent (decisiones §7.1 ya ratificadas: proprietary + GH Packages + monorepo). 1 sesión cierra v0.1.0 publish. |

#### 7.5.3 Per-EP backlog signature decisions (EP-6..EP-18)

Architect Story 8 emits `luana-core-extension-sdk/python/extension_points.py` + `@luana/extension-sdk/src/index.ts` con estos contratos cementados:

| EP | Name | Surface | Pattern | Mode | Key signature decision |
|---|---|---|---|---|---|
| **EP-6** | `sidebar_routes_register` | BE+FE sync | DataClass | append | `SidebarRouteDef = {slug, label, icon, parent_slug?, role_required?, order}`. BE expone `/api/v1/_sdk/sidebar` que FE Next.js consume. Una sola registración cubre ambos lados. |
| **EP-7** | `extractor_register` | BE | DataClass | append | `ExtractorDef = {name, target_module, wave_position, prompt_template_ref, output_schema_ref, dependencies}`. Inyectado en `BaseExtractionOrchestrator` wave position. Reusa infra Stories 5 (brand/offer/landing/buyer_persona extractors lifted). |
| **EP-8** | `channel_adapter_register` | BE | DataClass+Callables | append | `ChannelAdapterDef = {channel_slug, send: Callable, receive: Callable, format_for_channel: Callable, webhook_handler?}`. **Cubre sales_agent + copilot + cualquier vertical agent del brand (treatment_agent, kitchen_agent, etc.)** — ampliado por Vitalia recipe §7.5.4. |
| **EP-9** | `metric_register` | BE | DataClass | append | `MetricDef = {name, module, aggregation, unit, currency_aware, sql_query? \| python_compute?, stage_assignment, refresh_freq}`. ETL pipeline level — corre en stage service ciclo, persiste en `official_metrics` table. |
| **EP-10** | `landing_template_register` | BE | DataClass | append | `LandingTemplateDef = {template_id, vertical_hint, sections_schema, preview_url}`. **JSON schema declarativo** — single Landing Engine FE consume schema. Brands no shipean React components custom. |
| **EP-11** | `campaign_template_register` | BE | DataClass | append | `CampaignTemplateDef = {template_id, channel: ['email'\|'whatsapp'\|'sms'], steps: list[CampaignStepDef], trigger_event, conditions}`. Drip pattern (secuencia ordered con triggers + conditions). |
| **EP-12** | `asset_template_register` | BE | DataClass | append | `AssetTemplateDef = {template_id, asset_type: ['image'\|'video'\|'pdf'\|'kit'], placeholders: dict, source_path}`. **Static template + placeholder replacement**. AI gen NOT scope SDK. |
| **EP-13** | `sales_agent_guardrail_register` | BE | Callable | append | `GuardrailDef = {name, pre_send_check: Callable[[str, BrandContext], GuardrailResult], pre_receive_check?: Callable[[str, BrandContext], GuardrailResult], priority: int, mode: 'block'\|'warn'\|'rewrite'}`. **Pre-send + pre-receive ambos** desde v0.1.0 (Chris "pagar precio hoy"). |
| **EP-14** | `copilot_kb_pack_register` | BE | DataClass | append | `KbPackDef = {pack_id, documents_path, embedding_model_ref, qdrant_collection_name, tenant_scope: 'brand'\|'tenant'\|'both', metadata}`. **Lazy-load + background warm-up** post-startup. `tenant_scope='both'` replica pack per-tenant (Vitalia: brand-scope medical-protocols + tenant-scope clínica-internal-KB). |
| **EP-15** | `crm_lifecycle_stage_register` | BE | DataClass | append | `LifecycleStageDef = {stage_id, label, after_stage: str, before_stage: str, transition_rules: list[Callable]}`. **Declarativa pura insert-between** (append). Brand inserta entre stages core. No remove. |
| **EP-16** | `iam_signup_handler` | BE | Callable | append | `register(handler: Callable[[ClerkUser, BrandContext], SignupResult])` donde `SignupResult = {status: 'approved'\|'pending_review'\|'rejected', metadata, blocking_reason?}`. **Async background + pending_review state**. Requires CRM lifecycle support `pending_review` (EP-15 brand registers). |
| **EP-17** | `tenant_plan_tier_register` | BE | DataClass | **override** | `PlanTierDef = {tier_id, label, price_monthly, currency, features: list[str], limits: dict, stripe_price_id?}`. **Brand replaces core tiers completamente**. Cada brand su pricing model. Core no impone tiers — solo expone API + enforcement. |
| **EP-18** | `onboarding_wizard_steps_register` | FE+BE | DataClass | **override** | `WizardStepDef = {step_id, title, component_ref, prereqs: list[str], skippable: bool, post_action_event?}`. **Brand replaces wizard completamente**. Cada vertical flow muy distinto. Core ships `default-wizard` Nicolify, otros brands shipean sus wizards. |

#### 7.5.4 Vitalia treatment-agent recipe insight (NO EP-19 — pattern doc only)

Chris example (2026-05-12): Vitalia post-migration feature = "treatment follow-up agent" pre/post operatorio. Será agente NUEVO (no parte de sales_agent), usa infra base, requiere "tacto + conocimiento médico", NO recomendaciones legales (informa como enfermera). Multi-session offer consumption (numero predefinido o doctor estima → UI doctor/enfermera para tracking).

**Decisión: NO crear EP-19 `vertical_agent_register`.** Pattern hexagonal puro — vertical agent ES un APP del brand, NO un EP del core.

`apps/vitalia/agents/treatment_agent/` vive en brand repo, consume luana-core piecewise:
- `luana-core-observability` (subclass `VitaliaTreatmentCallbackHandler(BaseAgentCallbackHandler)` + `VitaliaTreatmentObservabilityContext(BaseObservabilityContext)` — pattern Story 6+7 cement)
- `luana-core-scheduling` (job queue + reminders pre/post-session)
- `luana-core-channels` via **EP-8** (treatment agent registers channels)
- `luana-core-marketing-kb` via **EP-14** (medical-protocols-kb-pack-v1 brand-scope + clínica-internal-KB tenant-scope)
- `luana-core-prompt-cache` (slot composer — slot 5 BRAND_VOICE via BrandVoicePort Story 7 D-T3)
- `luana-core-extension-sdk` (register treatment-specific tools via **EP-3**, guardrails via **EP-13** — "no medical recommendations" hard guardrail)

**Multi-session offer model:** offer-studio `VariantStructure` ya soporta packs (Story 5 lifted). Doctor/enfermera tracking UI = Story 11.5+ Vitalia-specific scope, NOT Story 8 SDK scope.

**Documentation deliverable Story 8:** `docs/extension-points.md` section "Recipe: Build a vertical agent on top of luana-core". Includes Vitalia treatment-agent as worked example. Stories 11-13 bootstrap consumers.

#### 7.5.5 Dev infra dummy domains (Story 11-13 scope, NOT Story 8)

Dev domain plan (Chris owns `alpacapurpura.lat` registrar):

| Brand | Dev | Prod |
|---|---|---|
| Nicolify | dev-app.nicolify.com (existing CF tunnel) | app.nicolify.com (existing) |
| Vitalia | dev-app.vitalialat.com (Chris compra) o fallback `dev-vitalia.alpacapurpura.lat` | app.vitalialat.com (Chris compra Q3-Q4 2026) |
| Comunify | dev-comunify.alpacapurpura.lat (fallback gratis subdomain) | TBD post Story 12 |
| Lupulo | dev-lupulo.alpacapurpura.lat (fallback gratis subdomain) | TBD post Story 13 |

CF tunnel concurrent 5 services: `cloudflared` con multiple `--config` per brand, distintas ports locales. Setup en Stories 11-13 brand bootstraps, NO Story 8.

**Production deployment isolation (Chris ratified 2026-05-12):** cada brand su propio servidor (GCP / AWS / etc independiente), env vars, Docker Compose + Dockerfile, Clerk app, API keys LLM, Stripe account, Sentry project, Postgres + Qdrant instance, centro de costos operación. Dev compartido (monorepo, 1+ Claude subs). Producción aislada total.

#### 7.5.6 Cross-brand learning principle (core promotion path)

Brand A invents feature → /pm evaluates if generalizable → if yes, lift to core → brands B, C, D consume via SDK. NEVER cross-brand direct import. Namespace isolation (CC-4) enforces this.

Example: Vitalia treatment agent (Story 11.5+) battle-tested → learnings surface (e.g., "all verticals need pre/post engagement reminders") → /pm promotes generic abstraction to `luana-core-engagement-scheduler` package → Comunify cohort retention + Lupulo dietary follow-up consume same primitive.

Architect Story 8 emits docs Section "How features graduate to core" — guideline document, NOT formal mechanic.

### 7.6 Session 5 — Story 10 luana-nicolify-migration business decisions (ratified 2026-05-12)

10 business decisions ratified by Chris **before** spec/architect/build spawns. Architect Story 10 consumes §7.6 as binding spec. Future stories 10b/11/12/13/14 inherit applicable decisions by default (re-ratify only if vertical-specific deviation needed).

| # | Decisión | Opción | Implicancia binding |
|---|---|---|---|
| 1 | **Scope completeness** | **A — Full migration big bang** (BE + FE + tests + smoke E2E) | Sub-agent decomposition smart blast radius isolation. Cap paralelización **≤2 agentes simultaneous** (NOT 3 — Chris framing). Opus mayoritario en críticos. Halt-and-ask Chris si surprise surface. Admin Streamlit + workers diferidos Story 10b. |
| 2 | **DB migration strategy** | **B — Fresh nicolify DB + purge total + alembic restart limpio** | Sin clientes prod/dev real → ventana oportunidad clean break. Sub-tickets: (a) crear `nicolify_dev` DB nueva, (b) consolidar alembic history en `001_initial_snapshot.py` reflecting current schema (no replay 150+ migrations), (c) update env vars + docker-compose.dev.yml `POSTGRES_DB=nicolify`, (d) drop AISALESHT DB al cierre Story 10 después tests green. |
| 3 | **AISALESHT repo lifecycle** | **A — Archive read-only post-Story-10** | GitHub Settings → Archive. History accesible read-only para arqueología. Reversible 1-click si surge necesidad. |
| 4 | **/pm SSoT location** | **A — Migrates atómicamente con Story 10 Fase 4 merge** | Sub-ticket dedicated: `git mv docs/product/ → luana-platform/docs/product/` + commit en luana-platform. **"Muy cuidadoso"** — snapshot final pre-move en AISALESHT como audit trail + verify scripts (`generate_backlog.py`, `reconcile_capabilities.py`, pre-commit hooks) corren post-move sin path hardcoded breakage + test BACKLOG regen + cap reconcile en nueva ubicación ANTES archive AISALESHT. Halt-and-ask si Claude descubre path hardcoded raro. Story 10 archive dir vive en `luana-platform/docs/archive/2026/stories/luana-nicolify-migration/`. |
| 5 | **Test parity bar** | **B — Match baseline + fix-on-discovery oportunista trivial only** | T-1 build captura baseline snapshot (`pytest --json-report` + estado actual). T-N final: delta=0 new failures requirement enforcement (auditor verifica). 40 pre-existing sales_agent failures NO bloquean merge → siguen deferred. Si sub-agent durante import rewrite ENCUENTRA failure trivial-de-fixear (5 min, no rabbit hole) → arregla on-the-fly. Si requiere más → documenta + defer. |
| 6 | **FE Next.js strategy** | **B — FE workspace member luana-platform monorepo** | `git mv AISALESHT/frontend/ → luana-platform/nicolify/frontend/`. Add to `pnpm-workspace.yaml`: `- 'nicolify/frontend'`. `package.json`: `"name": "@nicolify/web"` + deps `"@luana/X": "workspace:*"`. Find/replace imports `@/components/ui` → `@luana/ui-kit`. Vercel reconfig: root directory monorepo → `nicolify/frontend/`. Custom domain dev-app.nicolify.com (CF tunnel) preserved. Sub-ticket dedicated con halt-and-ask si Vercel surprise. |
| 7 | **Streamlit admin** | **B — Defer Story 10b dedicated cleanup** | Admin Streamlit low-traffic (Chris only). Post-Story-10 admin "no migrated" estado aceptable 1-2 semanas. Story 10b dedicada hace migration luego. **Escape hatch:** architect Story 10 puede proponer incluir admin SI trivial (3-5 archivos, imports clean) con halt-and-ask Chris. Default: deferred. |
| 8 | **CI parity gate location** | **B — luana-platform root, cross-brand gates** | `Makefile` en root orquesta validation cross-brand. Hoy: solo Nicolify post-migration. Stories 11-13 heredan beneficio automático (cada brand nuevo agrega su target sin reconfig root). Defense-in-depth para refactors core (R3 downstream regression executable gate, no solo principio). Pre-push hook apunta a root Makefile. |
| 9 | **40 sales_agent pre-existing failures** | **B — Continue defer Story 14 brand-voice-elevation natural home** | Story 14 explicitly toca sales_agent surface (PersonalityProfile + voice cloning refactor). T-N final Story 10 genera `docs/product/stories/luana-nicolify-migration/DEFERRED-FAILURES-STORY-10.md` con paths exactos + nota "see Story 14 for fix plan". Auditor verifica delta=0 sin tocar esos 40. |
| 10 | **Pre-auth scope Sesión 5** | **A — Story 10 solo (default Tier 3-4 per §7.4)** | Sesión 5 cierra Story 10 únicamente. Stories 10b/11/12/13/14 awaiting per-story ratification next sessions. **Handoff prompt Story 10b** generated al cierre sesión 5 (Chris request explícito). |

#### 7.6.1 Cross-Story precedent inheritance (Stories 10b/11-14 default values)

Decisiones aplicables horizontal heredan default. Re-ratify SOLO si vertical-specific deviation:

| Decisión | Hereda? | Notas |
|---|---|---|
| 1 (full big bang vs phases) | No — story-specific | Story 10b puede ser phased si admin tiene módulos múltiples |
| 2 (fresh DB + purge) | **Sí Stories 11-13** — Vitalia/Comunify/Lupulo bootstrap fresh DBs from scratch | Per §7.5.5 each brand own DB isolated server |
| 3 (archive AISALESHT) | One-time decision | N/A |
| 4 (/pm SSoT in luana-platform) | **Sí permanent** | Future stories live there |
| 5 (match baseline) | **Sí** — default test parity bar | Override only if explicit Chris ratification |
| 6 (FE workspace member) | **Sí Stories 11-13** — cada brand FE workspace member | Vitalia/Comunify/Lupulo FE viven `nicolify-pattern` |
| 7 (admin deferred) | Story 10b specific | N/A |
| 8 (ci-parity root) | **Sí permanent** | Story 11+ heredan automático |
| 9 (defer 40 failures) | One-time decision Story 10 | Story 14 inherits as scope |
| 10 (story-only per session) | **Default Tier 3-4** — re-ratify per-session | Pre-auth case-by-case |

#### 7.6.2 Session 5 halt-and-ask triggers (per Chris explicit framing)

Chris explicit mandate: **"si detectas algo que pueda requerir mi intervención paraliza y pregunta"**.

Triggers que escalate Chris durante Fases 1-3 (no proceed sin ratificación):

1. Architect descubre coupling oculto cross-module no documentado en outcome §2 dependencies
2. Builder import rewrite descubre que un módulo tiene cross-module dependency a otro módulo en grupo DIFERENTE (sharded Wave 1 viola disjoint principle)
3. Vercel reconfig surface unexpected issue (custom domain, env vars, secrets, build config)
4. CF tunnel `dev-app.nicolify.com` mapping rompe post-FE-move
5. Alembic snapshot consolidation surface schema inconsistency (e.g., model definitions ≠ DB state)
6. Tests pass locally pero ci-parity root falla (env divergence)
7. Pipeline release-please primer execution falla en GitHub Actions
8. luana-platform monorepo state inesperado (e.g., uncommitted changes, branch mismatch)
9. Cumulative cost sesión > $5000 (soft check-in, continuar pero report Chris)
10. Auditor + 2 auto-fix iter all fail → escalate (no 3rd iter sin Chris)
11. **Sub-agent rewrite descubre test mock apuntando a path `src.shared.X` SIN equivalent en luana-core packages** (legacy test infra mock, distinto de Trigger #1 que cubre production imports missing). Halt-and-ask Chris entre: (A) inline mock value into test sin patch, (B) lift symbol Story 14 deferred, (C) skip test temporalmente con magic comment `# luana-migration-defer` + Story 14 ticket. **Ratified Chris 2026-05-12 Session 5 Phase 1.**

#### 7.6.3 Session 5 success criteria

Story 10 reaches `done` state when ALL true:
- BE: imports rewritten `from src.modules.X` → `from luana_core_X` en 26 packages target
- FE: imports rewritten `@/...` → `@luana/...` + FE workspace member luana-platform
- Fresh `nicolify_dev` DB + alembic snapshot consolidated + AISALESHT DB dropped
- Tests BE: same coverage threshold 43% + delta=0 new failures vs baseline
- Tests FE: same coverage threshold 20% + delta=0 new failures vs baseline
- Playwright smoke E2E green (Chris journey end-to-end through nicolify app)
- ci-parity root green (luana-platform/Makefile orchestrates)
- /pm SSoT migrated to luana-platform/docs/product/ + scripts verified
- AISALESHT repo archived GitHub UI
- 07-merge.md + capability promoted + outcome §1 stories_done 10/14 appended
- Handoff prompt Story 10b generated for Chris next session

---

**Next steps post-ratification (REVISED 2026-05-10):**
1. ✅ /pm spawns architect-orchestrator → revise Story 1 ready package for monorepo + proprietary + defer GH Packages (in progress 2026-05-10)
2. /pm Story 1 state refining → refined → ready post architect re-emit
3. /dev-team picks Story 1 T-1 → autonomous build (Sonnet OK, no R23 trigger — infra only)
4. /auditor when Story 1 developed → CHECKPOINTS C1-C5
5. /pm merge → capability promoted → Story 2 unparked → repeat per /pm v4 paradigm
6. Stories 11-14 originally paralelas → secuenciales 1 Claude (revisit cuando subs adicionales lleguen Q3-Q4)
