# ADR-001 — Luana Platform: Multi-Brand Vertical SaaS Architecture

> **Status:** PROPOSED — awaiting Chris ratification
> **Date:** 2026-05-09
> **Decision-makers:** Chris (alpacapurpura@) + Claude Opus 4.7 (CTO advisory)
> **Supersedes:** none
> **Superseded by:** none
> **Related docs:**
> - `01-core-audit.md` — module-by-module BE+FE inventory
> - `02-extension-points.md` — formal hook signatures (pending)
> - `03-migration-plan.md` — week-by-week execution plan (pending)
> - `04-brand-config-spec.md` — BrandConfig schema (pending)
> - `05-cross-repo-tooling.md` — `.claude-shared/` strategy (pending)

## 1. Context

Chris (single founder, AI-augmented developer) plans to operate **4 distinct SaaS brands** in parallel, each targeting a different vertical:

| Brand | Vertical | Target customer | Differentiation |
|---|---|---|---|
| **Nicolify** | SaaS marketing/sales (generic) | Marketers, agencies | Canonical horizontal product |
| **Vitalia** | Medical/dental/wellness clinics | Doctors, clinic owners | Prepaid bookings, medical KB, HIPAA-lite guardrails, treatment follow-up |
| **Comunify** | Creator/expert economy + community | Coaches, online educators | Offer ladder long-form, authority vault, community engine |
| **Lupulo Labs** | Gastronomy (booking + ordering agentic) | Restaurant owners | Table booking + ordering + kitchen integration via AI agent |

**Constraints:**
- Single human (Chris) + 5 Claude Code subscriptions for parallel work
- Each brand requires deployment isolation (separate K8s clusters + DBs) for compliance and blast radius
- Core capabilities (copilot, sales_agent, brand_studio, offer_studio, scheduling, analytics) must be **shared SSoT** across brands so improvements ripple
- Brand-specific divergence must NOT contaminate the core ("brand quirks shall not leak into shared code")
- Brand-specific adaptations must NOT become invalidated when core evolves
- Operating budget ~$1100-1400/mo for 4 brands (infra + AI dev tooling)

**Existing state (2026-05-09):**
- Single repo `AISALESHT` (= Nicolify codebase, ~290k LOC)
- Modular monolith DDD backend (18 modules, 4 layers each)
- FSD-Lite Next.js 16 frontend (16 features)
- `shared/` already pre-extracted (~20k LOC, ~50% of future Luana foundation)
- Multitenancy via `X-Tenant-ID` header + Clerk JWT
- 16 cross-cutting transversals codified in `.claude/rules/`
- /pm v4 paradigm with 10-state machine + ready package + validators

**Driving force:** Chris cannot afford to operate 4 separate codebases with copy-pasted core (technical debt explodes); cannot afford to operate 1 codebase with `if (brand === ...)` branches (becomes lasagna by brand #3); cannot afford to fork (adaptations become invalidated when core evolves).

The mature industry pattern for this is **Vertical SaaS 2.0** (canonical examples: ServiceTitan, Toast, Mindbody, Procore, Veeva, Clio).

## 2. Decision

Adopt a **Multi-Brand Vertical SaaS architecture** organized as:

### 2.1 Repository topology

```
github.com/luana-platform/                ← GitHub Organization
├── luana-core                            ← SHARED CORE (private)
├── nicolify                              ← Brand #1 (current AISALESHT renamed)
├── vitalia                               ← Brand #2 (medical/wellness)
├── comunify                              ← Brand #3 (creator/expert economy)
└── lupulo-labs                           ← Brand #4 (gastronomy agentic)
```

5 separate repos. **Trunk-based development** (`main` only + PR mandatory) per repo. No `development` branch (legacy patch for single-repo multi-session, no longer needed).

### 2.2 Three-layer architecture

**Layer 1 — Luana Core** (`luana-platform/luana-core`):
- Internal monorepo: **uv workspaces (Python) + pnpm + Turborepo (TypeScript)**
- Versioned packages published to **GitHub Packages** (private registry, free with org plan)
- Python packages: `luana-core-iam`, `luana-core-platform`, `luana-core-llm`, `luana-core-events`, `luana-core-billing`, `luana-core-compliance`, `luana-core-idempotency`, `luana-core-observability`, `luana-core-channels`, `luana-core-extraction`, `luana-core-brand-studio`, `luana-core-offer-studio`, `luana-core-scheduling`, `luana-core-crm`, `luana-core-analytics-engine`, `luana-core-landing`, `luana-core-connections`, `luana-core-copilot`, `luana-core-sales-agent`, `luana-core-campaigns`, `luana-core-content` (assets, social_proof, commercial_calendar, tenant_domains, tenant_profile), `luana-core-extension-sdk`, `luana-core-admin-streamlit`, `luana-core-evals` (post-Story-E)
- TypeScript packages: `@luana/ui-kit`, `@luana/ui-shared`, `@luana/design-tokens`, `@luana/format`, `@luana/hooks`, `@luana/api-client`, `@luana/schemas`, `@luana/copilot-ui`, `@luana/brand-studio-ui`, `@luana/offer-studio-ui`, `@luana/growth-studio-ui`, `@luana/sales-ui`, `@luana/closer-studio-ui`, `@luana/connections-ui`, `@luana/crm-hub-ui`, `@luana/settings-ui`, `@luana/extension-sdk`

**Layer 2 — Vertical Packages** (live inside each brand repo):
- `apps/{brand}/vertical-{niche}/` — vertical-specific tools, extractors, KB packs, guardrails, channel adapters, landing templates, campaign templates
- Examples: `vitalia/vertical-medical/`, `comunify/vertical-creator-economy/`, `lupulo-labs/vertical-gastronomy/`
- Nicolify likely has minimal vertical extension (it IS the canonical horizontal case)

**Layer 3 — Brand Apps** (deployments):
- Each brand repo contains: `apps/api/` (FastAPI consuming `luana-core-*`) + `apps/web/` (Next.js consuming `@luana/*`) + `vertical-{niche}/` + `brand.config.{ts,py}` + `deployments/` (K8s manifests)
- Each brand deploys to its own Kubernetes cluster + Postgres DB + Qdrant + Redis
- Each brand has its own Clerk Application (separate JWT issuer, separate user base)

### 2.3 Versioning + extension model

**Semver internal** for `luana-core-*` packages:
- MAJOR = breaking API change (extension point signature change, removed function)
- MINOR = additive feature (new extension point, new optional param, new package)
- PATCH = bug fix
- Automated via `semantic-release` from Conventional Commits

**Extension Points** (formal API contracts):
- 5 critical EPs at v0.1.0: `BrandStudio.fieldOverride`, `Offer.presetPackRegister`, `SalesAgent.toolRegister`, `Copilot.workflowRegister`, `Scheduling.bookingPolicy.canConfirm`
- 13 backlog EPs (sidebar routes, extractors, channel adapters, metrics, templates, guardrails, KB packs, lifecycle stages, signup handlers, plan tiers, onboarding wizard, admin tools)
- Brands register handlers via SDK; core never knows about brand-specific behavior
- Versioning rule: when an EP needs to change shape, deprecate v1 + introduce v2 (`canConfirmV2`), maintain both for 2 minor releases minimum

**BrandConfig** (declarative config, no code):
- Per-brand TypeScript + Python file declaring `enabled_sections`, `field_overrides`, `preset_packs`, `enabled_metrics`, `plan_tiers`, `voice_cloning: bool`, `theme_tokens`, `sidebar_routes`, `clerk_app_credentials`
- Loaded at brand app boot, materializes brand divergence without forking core

### 2.4 Brand voice ownership (decision Q2)

**`PersonalityProfile` engine + voice compiler v2 live in `core-brand-studio`** (not `core-sales-agent`).

`core-sales-agent` consumes voice via port: `BrandVoicePort.compileSystemInstruction(tenant_id) → str` → injected into Slot 5 BRAND_VOICE.

**Voice cloning** (LLM-distilled from chat samples) is a feature flag per BrandConfig:
- Comunify: ON (creator economy = personality is the product)
- Nicolify: ON (full feature for canonical case)
- Vitalia: OFF (medical = standardized voice, not personality-driven)
- Lupulo Labs: OFF (functional voice, no need for cloning depth)

### 2.5 Multi-tenancy isolation (decision Q3)

**Cluster-level isolation** (decided OQ8 + OQ3 confirmed):
- Each brand operates its own Kubernetes cluster + Postgres + Qdrant + Redis + LiteLLM Proxy svc
- Each brand has its own Clerk Application (separate JWT issuer, signing keys, user base, Org table)
- `core-iam` is brand-agnostic engine; each brand wires its own Clerk credentials via env
- `tenants` table is brand-local (a tenant in Vitalia is NOT a tenant in Comunify)
- No cross-brand SSO, no cross-brand data sharing — by design

### 2.6 Process model (decision: meta-orchestrate via /pm v4)

The migration itself is wrapped as an outcome (`luana-platform-migration`) with **14 stories** governed by /pm v4 state machine:

```
state machine: refining → refined → ready → developing → developed → reviewing → done
caps: refining ≤3, refined ≤5, developing ≤3, reviewing ≤2
gates: ready package mandatory, validators must_pass:true, CHECKPOINTS C1-C5 APPROVED
```

This guarantees **nothing left half-done**: no story advances without explicit state transition, validators are real test commands, auditor enforces APPROVED for `done`. Once Story 11 (Nicolify migrated) closes, /pm SSoT promotes from AISALESHT to luana-core.

## 3. Alternatives considered

### 3.1 Alternative A — Single multi-tenant codebase, brand = `tenant_attribute`
- **What:** keep single Nicolify repo, add `brand_id` column on tenants, theme overlay + preset packs per-brand, all 4 brands deploy from same codebase
- **Pros:** lowest cost, fastest to launch (~2-3 sprints), single codebase to maintain
- **Cons:** lasagna of `if (brand === ...)` branches by brand #3, no compliance isolation (Vitalia medical data shares DB with others), brand-specific extensions become invalidated when core touches the same code path, blast radius shared
- **Rejected because:** breaks "adaptations shall not become invalidated" constraint by brand #3; impossible to add HIPAA-lite to Vitalia without fragmenting the codebase or violating other brands

### 3.2 Alternative B — Fork-and-merge per brand
- **What:** each brand = git fork of Nicolify, periodic merge of upstream improvements
- **Pros:** maximum isolation, brand can diverge fully
- **Cons:** merge hell perpetual, every core improvement requires manual reconciliation per fork, cherry-pick fatigue, drift inevitable
- **Rejected because:** explicitly contradicts Chris's stated requirement ("core mejore constantemente y alimente el core de todas sin dejarlas inutilizadas las adaptaciones individuales")

### 3.3 Alternative C — Microservices with shared SDK
- **What:** core capabilities as independent microservices (copilot service, sales_agent service, brand service), brands consume via REST/gRPC + shared SDK
- **Pros:** maximum scale, independent deploy per service, language-agnostic
- **Cons:** distributed-system complexity (network failures, distributed tracing, eventual consistency), deployment ops 4x, latency cross-service, premature for solo founder + 4 brands
- **Rejected because:** sobre-ingeniería for current scale; ServiceTitan, Toast, Mindbody all started monolithic + extracted services later when team size justified it

### 3.4 Alternative D — Single monorepo with 5 Claude Code subscriptions on it
- **What:** one giant repo containing all 4 brands + core, 5 Claude Codes work on different folders
- **Pros:** atomic cross-brand refactors trivial, single CI
- **Cons:** parallel-safety pain that already plagues Nicolify single-repo multi-session amplifies 5x, deployment coupled (cannot release Vitalia without affecting others), no cluster isolation possible
- **Rejected because:** parallel-safety burden grows superlinearly with concurrent agents

## 4. Consequences

### 4.1 Positive

- **SSoT real:** core improvements ripple to 4 brands automatically (when brands bump version)
- **Adaptations preserved:** brand extensions registered via formal extension points are not affected by core internal refactors as long as semver is respected
- **Compliance per brand:** Vitalia HIPAA-lite isolation via separate cluster + DB, no shared compute risk
- **Blast radius zero:** a bug in Lupulo cannot impact Vitalia or Comunify
- **Team scaling:** when a brand becomes profitable enough to hire dedicated team, that team owns its repo + cluster, autonomy preserved
- **Add brand #5 marginal cost:** drops with each brand (skeleton template + extension registration, no core re-architecture)
- **Clear onboarding:** new collaborator sees `luana-core` (the shared library) and one brand repo (the consumer) — clean conceptual model
- **Process discipline forced:** /pm v4 state machine + validators + auditor checkpoints prevent half-done work

### 4.2 Negative

- **Trough Sem 1-5 (~5-6 weeks):** zero net new features in Nicolify during carve-out + migration
- **Operating cost +$150-200/mo** vs current single-stack (Sentry per-brand, GH Actions paid tier, Postgres backups × 4)
- **5x CI/CD complexity:** each repo has its own pipeline, monitoring, deploy
- **Versioning discipline mandatory:** breaking semver in `luana-core` cascades to 4 brands; requires CI gates for downstream impact
- **Coordinator load:** 5 parallel Claude Code conversations require Chris (or PM Claude) to maintain alignment
- **Risk: 2 of 4 brands may not validate market** — sunk infra cost for unvalidated brands; mitigation: monthly brand-level review with go/no-go decision
- **Migration risk:** schema coupling between modules may surface during carve-out, requires dual-write windows + rollback plan

### 4.3 Neutral / mitigations

- **Cross-repo `.claude/` rules:** managed via git subtree from `luana-core/.claude-shared/`. Updates flow `luana-core` → 4 brands via `git subtree pull`. Acceptable friction.
- **GitHub Project v2 cross-repo Roadmap:** single board with brand-tagged issues for cross-repo PM visibility.
- **Eval framework (sales_agent Stories B-E):** stays in `nicolify` initially; promotes to Luana v0.2.0 once Story E reaches `done` and stabilizes (per OQ1 decision).
- **LiteLLM Proxy:** per-brand instance in each cluster; pricing snapshot SSoT inmutable in `core-llm`. Acceptable footprint cost.

## 5. Decision rules cementadas

The following rules are cemented and not subject to revision without superseding ADR:

1. **Brand-aware code lives in `vertical-{niche}/` packages, never in `luana-core/`.** Zero `if (brand === ...)` in core. Violation = arch fitness fail.
2. **Cross-brand SSO is forbidden.** Each brand has its own Clerk app, user base, tenant table.
3. **Core never imports vertical packages.** Dependency arrow: `apps/{brand}/` → `vertical-{niche}/` → `luana-core-*`. Reverse direction = arch fitness fail.
4. **Extension points are versioned API contracts.** Breaking change requires deprecation + parallel v2 + 2-minor-release migration window.
5. **Brand divergence materializes via** (a) `BrandConfig` declarative config OR (b) extension point handlers — never via core code branching.
6. **`core-iam` is the only Clerk integration point.** Each brand passes its own credentials via env. No multi-Clerk logic in core.
7. **Migrations Alembic baseline = snapshot frozen v1 per brand repo.** No cross-repo Alembic history sharing.
8. **Process: /pm v4 governs migration itself** (outcome `luana-platform-migration` with 14 stories) until Story 11 closes; then /pm SSoT promotes from AISALESHT to luana-core.
9. **Brand voice contract is stable.** `personality_profiles.system_instruction` semantics + Slot 5 BRAND_VOICE format must not change without major version bump in `core-brand-studio`.
10. **Anthropic prompt cache TTL respected.** No `{tenant_name}` interpolation mid-block; cache prefix integrity preserved.

## 6. Roll-out timeline

| Week | Milestone | Output |
|---|---|---|
| Sem 0 (now → 2026-05-11) | Pre-flight: Story E /auditor closure, freeze PI-12 sub-stories F-I, ratify ADR-001 | Story E `done`, /pm freeze, ADR ratified |
| Sem 1 (2026-05-12) | GitHub Org + 5 repos + Luana skeleton + lift `shared/` (10 packages) | luana-core@0.0.1-alpha published |
| Sem 2 (2026-05-19) | Lift iam, tenancy, content, crm, analytics, landing, connections | luana-core@0.0.2-alpha published |
| Sem 3 (2026-05-26) | Lift brand, offer, copilot engine, sales_agent engine (post Story E `done`), campaigns, extension SDK | **luana-core@0.1.0 (production-grade alpha)** |
| Sem 4 (2026-06-02) | Migrate Nicolify to consume Luana | Nicolify v2.0.0 deployed, zero regression |
| Sem 5-8 (2026-06-09 → 2026-07-04) | Bootstrap Vitalia + Comunify + Lupulo (parallel via 3 dedicated Claude subs) | 4 brands live |
| Sem 9+ | Continuous: feedback from brands → core improvements → Luana v0.2.0 | Add brand #5 if business justifies |

## 7. Ratification

| Role | Person | Date | Signature |
|---|---|---|---|
| Founder + CEO | Chris | _PENDING (target 2026-05-11)_ | _____ |
| CTO advisory | Claude Opus 4.7 | 2026-05-09 | (advisory only — final decision Chris) |

## 8. Revision history

| Version | Date | Change | Author |
|---|---|---|---|
| 0.1 | 2026-05-09 | Initial draft. PROPOSED status. | Claude Opus 4.7 |

---

**Next docs:** `02-extension-points.md`, `03-migration-plan.md`, `04-brand-config-spec.md`, `05-cross-repo-tooling.md`.
