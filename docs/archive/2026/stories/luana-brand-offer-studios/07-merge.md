<!-- voseo-allowed: merge doc cites voseo strings verbatim from auditor REVIEW per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
---
story_id: luana-brand-offer-studios
outcome: luana-platform-migration
merge_date: 2026-05-11
merged_by: /pm (claude-opus-4-7)
auditor_verdict: APPROVED (2 WARN non-blocking, V-F-x-2 waiver accepted per session 1 precedent)
auditor: auditor-backend Opus 4.7
final_state: done
---

# Merge — luana-brand-offer-studios

## Resumen

Story 5 cierra DONE. 13 luana-platform commits + 1 AISALESHT closure (69de9265).
auditor-backend Opus APPROVED. Voice compiler v2 elevated a `luana-core-brand-studio.domain.personality` per ADR-001 §2.4 (cemented via arch fitness V-AG-3 SSoT test).

Hard invariants live-verified:
- AISALESHT brand/ + offer/ source untouched (V-NF-4)
- 14 deferred files correctly excluded
- 0 brand-specific control flow (V-AG-1)
- 0 forward imports a Stories 6/7+ (V-AG-2)
- PersonalityCompiler único en core/luana-core-brand-studio (V-AG-3 cement)
- 7 catalogs DAG smoke (V-F-cat-1) GREEN — 84 presets (≥76 floor)
- Workspace 21 packages registrados (19 prev + 2 Story 5)
- pyproject versions 0.0.1-alpha both packages
- No publishConfig / .releaserc / release.yml (V-NF-5/6/7 deferred Story 9)

## Commits aplicados

Repo `alpacapurpura/luana-platform` (main, 13 commits range 9139f7c..34496ae):
- T-1 9139f7c chore(workspace) register Story 5 packages
- T-2 07f622a feat brand-studio skeleton + pyproject + README
- T-3 3fa6445 feat brand domain lift + tests
- T-4 27b0286 feat brand infrastructure lift + tests
- T-5 e4ceab7 + 30ae844 feat brand application + services + refinements + uv.lock
- T-6 558daf5 feat brand voice_fidelity + agents/style_analyzer + T-7 partial api stub + test infra
- T-7+T-8 e0bee63 feat brand api layer + workers + in-source tests
- T-9+T-10+T-11 1fc55cb feat offer-studio skeleton + domain + infrastructure + application
- T-12+T-13 ff1c9f8 feat offer api + workers + tests; resolve cross-module mapper (Opus rescue)
- T-14 1d56bfb test(arch) Story 5 brand-agnostic + no-forward-imports + voice-compiler-SSoT + catalogs-DAG
- T-15+T-16 8c28706 feat DEFERRED-FILES entries + ruff format + tests/__init__.py cleanup
- T-17 34496ae test fix test imports + coverage verification

Repo AISALESHT (development):
- 69de9265 — Story 5 DEVELOPED closure commit (45 files: ready package + impl-logs + results + checkpoint + outcome update)

## Validators outcome

- 21 validators total per 04-validators.yaml
- 20/21 GREEN
- 1 waiver: V-F-x-2 (aggregate pytest core/) — pytest conftest plugin collision al correr 19 packages junto desde repo root. Causa: analytics tests/__init__.py missing + connections conftest name conflict. Per-package runs all GREEN. Pre-existing limitation per session 1 retro-audit "aggregate test isolation deferred Story 9 cleanup".
- Per-package tests: 420 GREEN brand-studio (8 warnings) + 628 GREEN offer-studio (12 skipped deferred, 1 warning) = 1048 total
- 4 arch fitness Story 5 NEW GREEN: V-AG-1, V-AG-2, V-AG-3, V-F-cat-1
- Downstream regression Stories 2+3+4 subset: 723 passed / 11 skipped (no regression)

## Findings auditor

### WARN (non-blocking)

| ID | Cat | Path:line | Issue | Acción |
|---|---|---|---|---|
| WARN-1 | C1/C4 | `core/luana-core-offer-studio/src/luana_core_offer_studio/domain/section_catalog.py:160,283` | Pre-existing voseo strings (`Describí`, `subí pares`) lifted verbatim del source AISALESHT (offer/domain/section_catalog.py:160,283). Lift mode (outcome §7.3) forbids fixing in destination — must remediate AISALESHT first. | Cleanup AISALESHT source futuro + re-lift OR Story 9 batch cleanup. NOT Story 5 regression. |

### Cross-module mapper resolution (T-12 Opus rescue accepted)

Cross-module SA relationships `LeadModel↔MessageModel/AppointmentModel` resolved via test stubs in offer-studio conftest (sales_agent + scheduling not lifted hasta Stories 7). No production runtime impact. Pattern razonable, documenta deferral correctamente.

## Capabilities promovidas

2 packages tracked at outcome level:
- `luana-core-brand-studio` — Brand domain engine + Identity + Personality (PersonalityCompiler v2 + StyleAnalyzer agent + voice_fidelity grader) + BuyerPersona + StoryBrand narrative + Authority + Communication assets + Strategy + Story + Positioning + Team + extraction orchestrator
- `luana-core-offer-studio` — Offer domain engine + 7 catalogs DAG (archetype + value_level + section + variant_structure + format + ladder_hints + type_preset) + 84 presets + form-runtime + conditional questions + extraction orchestrator + multi-currency wizard

Final outcome capabilities cumulative: 32 (5 Story 1 + 15 Story 2 + 6 Story 3 + 4 Story 4 + 2 Story 5).

## DEFERRED files Story 5 (track DEFERRED-FILES.md)

14 files deferred:
- `brand/copilot_provider/` (multiple files) → Story 6
- `offer/copilot_provider/` (multiple files) → Story 6
- `offer/api/offer_ai.py` → Story 6 (LLM-dependent)
- `offer/api/counts.py` → Story 6 (cross-package query)
- `offer/api/campaigns.py` → Story 8
- 3 brand test files + 1 offer test file (depend on copilot_provider) → Story 6
- Reserved Story 7: BrandVoicePort interface intro + voice_cloning flag
- Reserved Stories 11-13: voice cloning pipeline + per-brand voice clones

## Session 2 stats

- Total spawns: 6 (1 architect Opus + 4 builder Sonnet + 1 builder Opus rescue + 1 auditor Opus)
- Total wall clock: ~3h
- Builder model split: T-1..T-11 Sonnet (5 spawns), T-12..T-14 Opus rescue (cross-module mapper), T-15..T-18 Sonnet
- AISALESHT untouched verified post-merge

## Próximo paso

- Outcome `luana-platform-migration` continúa state=developing
- 5/14 stories DONE (Stories 1-5)
- Next story unparkable: `luana-copilot-engine` (Story 6) — Chris evaluates if Tier 3 autonomous OR per-story ratify
