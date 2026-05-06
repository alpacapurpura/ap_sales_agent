# CLAUDE.md

**Nicolify** — Multitenant SaaS marketing/sales automation. Modular Monolith DDD + Docker-First.

@AGENTS.md cubre stack/commands/architecture/git/quality/native-first/skills/constraints. Esto = overlay project-specific.

## Modules

Brand/Offer: `brand`, `offer` · Assets: `landing`, `assets` · Growth: `analytics`, `advertising`, `social_media` · Sales: `sales_agent`, `scheduling` · Config: `connections` · Support: `iam`, `crm`, `core`, `shared`, `copilot`. Detalle → `docs/domains/INDEX.md`.

## Spec-Driven Development (SDD Level 3) — paradigma actual

SSoT funcional vive en `docs/{product,process,specs}/`. Migración Mayo 2026 (`pm-nico/` eliminado Wave 2; `docs/projects/active/PI-12-...` es la última carpeta legacy y cierra paradigma viejo).

| Carpeta | Significado | Owner |
|---|---|---|
| `docs/product/` | SSoT vivo del producto. `BACKLOG.{yaml,md}` (auto-gen), `ideas-pool.yaml`, `outcomes/`, `stories/{id}/`, `capabilities/{module}/`, `modules/`. | `/pm` |
| `docs/process/` | Reglas transversales: ticket-states, checkpoint-protocol, parallel-sessions, learnings, pm-redesign. | `/pm` |
| `docs/specs/` | Templates + Rubrics + Personas (reusable cross-stories). | varios |
| `docs/projects/active/PI-12-...` (legacy) | Última iniciativa estructura PI/Sprint. Cierra paradigma viejo, no migra mid-flight. | `/pm` |
| `docs/archive/{year}/` | Stories `done` snapshot inmutable + legacy PIs preservados. | `/pm` |

### Vocabulary (NEW paradigma)

7 estados macro unificados cross-nivel (idea/outcome/story/capability):

| Estado | Significado | Trigger entry | WIP cap |
|---|---|---|---|
| `idea` | Spark crudo, no validado | Chris tira | sin cap |
| `validated` | Problem worth solving (OST aplicado) | `/pm` confirma | ≤ 10 |
| `ready` | Paquete autocontenido completo para autonomous build | `/architect` cierra | ≤ 5 |
| `building` | Autonomous loop opencode + Sonnet iterando contra `04-validators.yaml` | opencode pickup | ≤ 3 |
| `review` | Validators GREEN, audit pendiente | autonomous build cierra | ≤ 2 |
| `done` | Merged a development + scenarios migrados a capability | `/auditor` APPROVED → `/pm` merge | rolling 90d |
| `parked` | De-prioritized, NO abandonado | manual | sin cap |
| `dropped` | Won't do (terminal) | manual | sin cap |

Outcome (epic) = agrupación semántica de stories por objetivo común. Story = work unit. Ticket = sub-unit. Outcome cierra event-driven (no time-driven). NO PI/Sprint.

### `ready` package (5 archivos autocontenidos por story)

```
docs/product/stories/{story-id}/
├── 01-spec.md              # /po-ux fusión: Gherkin + wireframes inline (UI std)
│                           # /po: service-stories (no UI)
│                           # /po + /ux-agentico: agentic-stories (spec.md + 02-design-agentic.md)
├── 03-arch.md              # /architect: technical design (incluye sub-arquitecturas BE/FE/AGENTIC)
├── 04-validators.yaml      # ★ CRITICAL ★ tests ejecutables, must_pass:true c/u
├── 05-guidelines.md        # patterns required/forbidden + files in scope + skills/rules a cargar
├── 06-tickets.yaml         # T-1, T-2, ... work units atómicos
└── checkpoint.md           # state + phase + next_action vivo
```

Tickets flat dentro: `T-{n}-impl-log.md`, `T-{n}-result.md`, `T-{n}-review.md`. Si > 10 tickets → story es demasiado grande, split.

### Flujo extremo-a-extremo (3 conversaciones)

```
Conv 1 — DISCOVERY + READY  (Chris + /pm + /po-ux + /architect)
  → idea (ideas-pool.yaml)
  → validated (OST aplicado, outcome creado)
  → /po-ux | /po | /ux-agentico produce 01-spec.md (+ 02-design-agentic.md si agentic)
  → /architect spawna /architect-{be,fe,agentic} en paralelo → 03-arch.md
  → /architect emite 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml
  → state=ready

Conv 2 — AUTONOMOUS BUILD   (opencode + Sonnet iterando contra validators)
  → /dev-team toma 06-tickets.yaml ticket-por-ticket
  → loop: implement → run validators → fix targeted file → repeat hasta GREEN o cap_reached
  → on GREEN: state=building→review, append iteration_log
  → on cap reached: state=building→blocked, escalate Chris

Conv 3 — REVIEW + MERGE     (/auditor + /pm merge)
  → /auditor spawna auditor-{be,fe,agentic}
  → CHECKPOINTS.md C1-C5 grid: Code | Spec | Architecture | Cross-cutting | Trace
  → APPROVED → /pm aplica merge → scenarios migran a capability → story archive a docs/archive/{year}/stories/{id}/
  → state=review→done
```

### Skills ejes

| Skill | Modelo | Rol |
|---|---|---|
| `/pm` | Opus 4.7 | Director orquesta. Owner BACKLOG.{yaml,md}, ideas-pool, outcomes/, capabilities/, modules/, learnings.md. Ratifica merges. NO redacta specs/diseño/arq/código. |
| `/po-ux` | Opus 4.7 | **NEW (fusión).** UI standard stories (CRUD/list/detail/form/dashboard). Produce 01-spec.md con Gherkin + wireframes inline (ASCII / HTML / Figma link). |
| `/po` | Opus 4.7 | Service-stories only (no UI). Spec gherkin AI-resistant. |
| `/ux-agentico` | Opus 4.7 | Agentic-story design. State machine + slot architecture + voice constraints. Produce 02-design-agentic.md. |
| `/architect` | Opus 4.7 | Orquesta /architect-{be,fe,agentic}. Produce 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml = `ready` package. |
| `/dev-team` | opencode + Sonnet (BE/FE no-agentic + tests/docs sobre agentic) o Opus 4.7 (agentic production code) | Conv 2 autonomous build. Toma 06-tickets.yaml → TDD → push. |
| `/auditor` | Opus 4.7 | Conv 3. Spawna auditor-{be,fe,agentic}. CHECKPOINTS.md C1-C5. Verdict APPROVED/CHANGES_REQUESTED/ESCALATED. |

**Hard rule:** AGENTIC tickets con `production_code: true` (modules/copilot, modules/sales_agent runtime) → Opus 4.7 SIEMPRE. opencode/Sonnet ban absoluto. AGENTIC tickets con `production_code: false` (tests/docs sobre agentic) → Sonnet OK (R23).

### Resume protocol

`BACKLOG.md` es SSoT visible — UN read da estado completo:

```bash
git status --short && git branch --show-current && git log --oneline -3
cat docs/product/BACKLOG.md     # Roadmap + Mermaid kanban + Caps snapshot
```

Para drill-down a story específica:

```bash
cat docs/product/stories/{story-id}/checkpoint.md
```

Schema checkpoint: `docs/process/checkpoint-protocol.md`. Detalle paradigma + waves: `docs/process/pm-redesign-2026-05.md`.

### Anti-telephone-game (subagent return contract)

Cada subagent (builder-*, auditor-*, gate-runner, context-builder) MUST devolver UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Ejemplos: `done -> docs/product/stories/foo/T-1-result.md`, `blocked -> docs/product/stories/foo/checkpoint.md`, `failed -> tests/scripts/test_x.py:42`.

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Critical Rules (auto-loaded)

| # | Trigger | File |
|---|---|---|
| 1 | Anti-hallucination | leer `docs/domains/INDEX.md` antes coding |
| 2 | Tenant isolation | `.claude/rules/tenant-isolation.md` |
| 3 | BE DDD | `.claude/rules/backend-ddd.md` |
| 4 | FE FSD | `.claude/rules/frontend-fsd.md` |
| 5 | Migrations idempotentes | `.claude/rules/backend-migrations.md` |
| 6 | Git/Conventional Commits | `.claude/rules/git-safety.md` |
| 7 | Parallel safety multi-instancia | `.claude/rules/parallel-safety.md` (canonical en `docs/process/parallel-sessions-protocol.md`) |
| 8 | TDD obligatorio | `.claude/rules/tdd-mandatory.md` |
| 9 | Debugging | `.claude/rules/debugging.md` |
| 10 | Spanish neutro LatAm | `.claude/rules/spanish-text.md` |
| 11 | PII (`response_model=`) | `@AGENTS.md` → Tessl pii-sanitisation |
| 12 | Anti-duplication | `.claude/rules/anti-duplication.md` |
| 13 | Ticket states + checkpoint protocol + crash recovery (R27) | `docs/process/{ticket-states,checkpoint-protocol}.md` |
| 14 | Auditor downstream regression scope (R3 + R21) | `.claude/rules/auditor-downstream-regression.md` |
| 15 | Hot-fix repro mandatory (R26) | `.claude/rules/hotfix-repro-mandatory.md` |

## Conditional Rules (stub → skill)

| Tocas | Skill | Stub |
|---|---|---|
| `modules/copilot/` | `copilot-expert` | `rules/copilot-{resilience,observability}.md` |
| `modules/sales_agent/` | `sales-agent-expert` | `rules/sales-agent-brand-voice.md` |
| `modules/offer/` catalogs | `offer-expert` / `offer-type-preset-expert` | `rules/offer-catalogs.md` |
| `modules/analytics/` ETL | `metrics-expert` | `rules/{etl-extraction-contract,analytics-metrics,data-reliability}.md` |
| BE quality/master-data/currency/arch-fitness | `backend-expert` | `rules/{backend-quality,master-data,currency-handling,architectural-fitness}.md` |
| FE quality/form-runtime | `frontend-expert` / `brand-expert` | `rules/{frontend-quality,form-runtime-array}.md` |
| Streamlit admin | `backend-expert` | `rules/admin-panel.md` |
| E2E Playwright + Clerk auth + smoke tests | `playwright-expert` | `rules/e2e-testing.md` |
| PM/SSoT funcional | `pm` skill | `docs/product/BACKLOG.md` + `docs/product/{outcomes,stories,ideas-pool.yaml}` |
| BE config flag flips (`core/config.py` defaults) | (none — `pm` skill ratification) | `rules/anti-default-flip-audit.md` |
| User story redacción (UI std) | `po-ux` skill (NEW fusión) | `docs/specs/templates/01-spec-template.md` |
| User story redacción (service-only) | `po` skill | `docs/specs/templates/01-spec-template.md` |
| Conversational flow design | `ux-agentico` skill | `docs/specs/templates/02-design-agentic-template.md` |
| Tech architecture + ready package | `architect` skill (orchestra `architect-{be,fe,agentic}`) | `docs/specs/templates/03-arch-template.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml` |
| Code implementation (autonomous build) | `dev-team` skill | `docs/specs/templates/T-handoff-template.md` |
| Code review (Conv 3) | `auditor` skill | `docs/specs/templates/T-review-template.md` |
| Process metrics emission (R12 layer 1) | `dev-team` + `auditor` Step 5.5/4.5 | `scripts/emit_process_metric.py` + `docs/process/metrics/README.md` |
| Hot-fix ticket origen handoff doc (R26) | `dev-team` Step 0.5 + `po` Step 2.5 | `.claude/rules/hotfix-repro-mandatory.md` |
| Backlog freshness (R33) | `pm` skill bootstrap + pre-commit hook Section 6 | `scripts/generate_backlog.py` |
| Capability reconciliation (R32) | `pm` skill | `scripts/reconcile_capabilities.py` |

## Vision

`docs/product/vision.md`. Glossary: `docs/product/glossary.md`. Story-map backbone: `docs/product/story-map/backbone.md`.

@AGENTS.md
