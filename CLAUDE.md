# CLAUDE.md

**Nicolify** — Multitenant SaaS marketing/sales automation. Modular Monolith DDD + Docker-First.

@AGENTS.md cubre stack/commands/architecture/git/quality/native-first/skills/constraints. Esto = overlay project-specific.

## Modules

Brand/Offer: `brand`, `offer` · Assets: `landing`, `assets` · Growth: `analytics`, `advertising`, `social_media` · Sales: `sales_agent`, `scheduling` · Config: `connections` · Support: `iam`, `crm`, `core`, `shared`, `copilot`. Detalle → `docs/domains/INDEX.md`.

## Critical Rules (auto-loaded)

| # | Trigger | File |
|---|---|---|
| 1 | Anti-hallucination | leer `docs/domains/INDEX.md` antes coding |
| 2 | Tenant isolation | `.claude/rules/tenant-isolation.md` |
| 3 | BE DDD | `.claude/rules/backend-ddd.md` |
| 4 | FE FSD | `.claude/rules/frontend-fsd.md` |
| 5 | Migrations idempotentes | `.claude/rules/backend-migrations.md` |
| 6 | Git/Conventional Commits | `.claude/rules/git-safety.md` |
| 7 | Parallel safety multi-instancia | `.claude/rules/parallel-safety.md` |
| 8 | TDD obligatorio | `.claude/rules/tdd-mandatory.md` |
| 9 | Debugging | `.claude/rules/debugging.md` |
| 10 | Spanish neutro LatAm | `.claude/rules/spanish-text.md` |
| 11 | PII (`response_model=`) | `@AGENTS.md` → Tessl pii-sanitisation |
| 12 | Anti-duplication | `.claude/rules/anti-duplication.md` |

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
| PM/SSoT funcional | `pm` skill | `rules/pm-nico-ssot.md` |
| BE config flag flips (`core/config.py` defaults) | (none — `pm` skill ratification) | `rules/anti-default-flip-audit.md` |

## Vision

`docs/domains/vision/product-vision.md`.

@AGENTS.md
