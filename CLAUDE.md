# CLAUDE.md

**Nicolify** — Multitenant SaaS marketing/sales automation. Modular Monolith DDD + Docker-First.

@AGENTS.md cubre stack/commands/architecture/git/quality/native-first/skills/constraints. Esto = overlay project-specific.

## Modules

Brand/Offer: `brand`, `offer` · Assets: `landing`, `assets` · Growth: `analytics`, `advertising`, `social_media` · Sales: `sales_agent`, `scheduling` · Config: `connections` · Support: `iam`, `crm`, `core`, `shared`, `copilot`. Detalle → `docs/domains/INDEX.md`.

## Spec-Driven Development (SDD Level 3) — paradigma actual

SSoT funcional vive en `docs/{product,projects,specs,process}/`. Migración Mayo 2026.

| Carpeta | Significado | Owner |
|---|---|---|
| `docs/product/` | Estado vivo del producto. Capability registry, modules, stories YAML SSoT, opportunities, ideas. | `/pm` |
| `docs/projects/active/PI-N/` | Iniciativas en curso. Stories con artefactos versionados (00-story → 07-merge). | `/pm` orchestra, otros skills escriben |
| `docs/specs/` | Templates + Rubrics + Personas (reusable cross-stories). | varios |
| `docs/process/` | Reglas transversales: ticket-states, checkpoint-protocol, parallel-sessions, learnings. | `/pm` |
| `docs/pm-nico/` (legacy) | PIs activos PI-3..11 cierran aquí. PI-12+ en estructura nueva. | `/pm` lee on-demand |

### Flujo extremo-a-extremo

```
/pm crea 00-story.md →
  /po redacta 01-spec.md (Gherkin AI-resistant: happy + negative + edge + adversarial) →
  /ux-ui o /ux-agentico produce 02-design-{ui,agentic}.md →
  /architect spawna /architect-{be,fe,agentic} en paralelo → 03-arch-* + 04-tickets.yaml →
    por cada ticket: /dev-team toma → 05-impl/T-{n}-result.md →
    /auditor revisa → 06-audit/T-{n}-review.md
  cuando todos audit-passed: /auditor REVIEW-final.md → /pm 07-merge.md
```

### Skills ejes

| Skill | Modelo | Owner |
|---|---|---|
| `/pm` | Opus 4.7 | Director orquesta. Crea PI/sprint/story. Aplica merges. |
| `/po` | Opus 4.7 | Spec gherkin AI-resistant. Loop iterativo Chris. |
| `/ux-ui` | Opus 4.7 | Diseño UI + mockups HTML. |
| `/ux-agentico` | Opus 4.7 | Flujo conversacional + state machine + slot architecture. |
| `/architect` | Opus 4.7 | Orquesta /architect-{be,fe,agentic}. Produce 04-tickets.yaml. |
| `/dev-team` | Opus 4.7 (agentic) o qwen-opencode (BE/FE) | Toma 1 ticket → TDD → push. |
| `/auditor` | Opus 4.7 | Spawna auditor-{be,fe,agentic}. Verdict APPROVED/CHANGES_REQUESTED/ESCALATED. |

**Hard rule:** AGENTIC tickets (modules/copilot, modules/sales_agent) → Opus 4.7 SIEMPRE. qwen ban absoluto.

### Resume protocol

Cada nivel (PI/sprint/story) tiene `checkpoint.md`. Cualquier sesión nueva:

```bash
ls docs/projects/active/                                              # PIs activos
cat docs/projects/active/PI-N/checkpoint.md                           # PI-level
cat docs/projects/active/PI-N/sprints/SN/checkpoint.md                # sprint
cat docs/projects/active/PI-N/sprints/SN/stories/{id}/checkpoint.md   # story
```

Schema + protocolo: `docs/process/checkpoint-protocol.md`.

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
| PM/SSoT funcional | `pm` skill | `docs/product/INDEX.md` + `docs/projects/INDEX.md` |
| BE config flag flips (`core/config.py` defaults) | (none — `pm` skill ratification) | `rules/anti-default-flip-audit.md` |
| User story redacción | `po` skill | `docs/specs/templates/01-spec-template.md` |
| UI design | `ux-ui` skill | `docs/specs/templates/02-design-ui-template.md` |
| Conversational flow design | `ux-agentico` skill | `docs/specs/templates/02-design-agentic-template.md` |
| Tech architecture | `architect` skill (orchestra `architect-{be,fe,agentic}`) | `docs/specs/templates/03-arch-template.md` |
| Code implementation | `dev-team` skill | `docs/specs/templates/T-handoff-template.md` |
| Code review | `auditor` skill | `docs/specs/templates/T-review-template.md` |
| Process metrics emission (R12 layer 1) | `dev-team` + `auditor` Step 5.5/4.5 | `scripts/emit_process_metric.py` + `docs/process/metrics/README.md` |
| Hot-fix ticket origen handoff doc (R26) | `dev-team` Step 0.5 + `po` Step 2.5 | `.claude/rules/hotfix-repro-mandatory.md` |

## Vision

`docs/product/vision.md` (PI-12+) o `docs/domains/vision/product-vision.md` (legacy reference).

@AGENTS.md
