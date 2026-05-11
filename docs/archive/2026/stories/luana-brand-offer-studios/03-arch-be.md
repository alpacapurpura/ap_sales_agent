---
story_id: luana-brand-offer-studios
sub_arch: backend
last_modified: 2026-05-11
drafted_by: /architect (claude-opus-4-7)
authority: 03-arch.md (consolidated) — this sub-document folds BE detail back into the main 03-arch.md
---

# 03-arch-be.md — Backend sub-architecture (lift-mode story)

Story 5 is **backend-only lift** (per 00-story.md acceptance "Form-runtime engine FE refactorizado en `@luana/brand-studio-ui` + `@luana/offer-studio-ui` (separate per OQ4)" → Story 10/11+ territory). All sub-architecture detail (DAG, layout, sed mapping, deferrals, fitness gates, voice compiler placement, catalogs SSoT) is consolidated in `03-arch.md` to mirror Stories 2-4 BE-only lift precedent.

## Why a separate file exists at all

Per /pm template §3 (`ready` package = `01-spec.md` + `03-arch.md` + `04-validators.yaml` + `05-guidelines.md` + `06-tickets.yaml`), a `03-arch.md` MUST exist. When a story has both BE + FE + agentic surfaces, sub-files (`03-arch-be.md` + `03-arch-fe.md` + `03-arch-agentic.md`) can split the burden. Story 5 has only BE surface → main `03-arch.md` is sufficient; this stub exists for /pm template parity.

## Pointers

- Architecture topology + DAG: see `03-arch.md` §1
- Per-package layout (brand-studio + offer-studio file inventories): `03-arch.md` §3
- Import path mapping (sed patterns): `03-arch.md` §5
- Test lift strategy + deferrals: `03-arch.md` §6 + §9
- Architecture fitness gates: `03-arch.md` §7 + §11
- pyproject.toml templates: `03-arch.md` §8
- Voice compiler ELEVATION per ADR-001 §2.4: `03-arch.md` §10
- Cross-cutting (tenant isolation + currency + Spanish neutro + PII): `03-arch.md` §13

## FE sub-architecture (NOT in Story 5 scope)

Frontend lift (`@luana/brand-studio-ui` + `@luana/offer-studio-ui`) is deferred per outcome §2 Story sequence:
- Story 10 = Nicolify migration (rename AISALESHT → nicolify, swap imports to `@luana/*`)
- Story 11-13 = brand bootstrap (vertical-specific FE themes/extensions)
- Story 14 = brand-voice elevation refactor (post-merge cleanup)

When FE lift starts, an `03-arch-fe.md` sub-document will detail TypeScript package layout (`@luana/brand-studio-ui`, `@luana/offer-studio-ui`), pnpm workspace registration, FSD-Lite preservation per `.claude/rules/frontend-fsd.md`, and form-runtime engine refactor per `.claude/rules/form-runtime-array.md`.

## Agentic sub-architecture (NOT in Story 5 scope)

Brand has an in-package `application/agents/style_analyzer/` LangGraph agent (extraction onboarding). This is **NOT agentic-runtime production code** (per outcome §7.3 + R23) — it's an extraction utility that lifts verbatim with the rest of the brand package. NO new agentic logic in Story 5; preserve topology.

`production_code: false` is correct for Story 5 tickets touching `application/agents/style_analyzer/` because they lift existing code, NOT introduce new LangGraph nodes or agentic behavior. R23 Opus requirement does NOT trigger.

When Story 6 (copilot lift) + Story 7 (sales-agent lift) start, those stories WILL have `03-arch-agentic.md` sub-documents detailing LangGraph topology, prompt cache slots, observability writes, eval goldens — all per `copilot-expert` + `sales-agent-expert` skill SSoTs.
