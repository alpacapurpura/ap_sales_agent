<!-- voseo-allowed: merge doc cites voseo strings verbatim from auditor REVIEW per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
---
story_id: luana-copilot-engine
outcome: luana-platform-migration
merge_date: 2026-05-11
merged_by: /pm (claude-opus-4-7)
auditor_verdict: APPROVED (3 info-level docs cleanups non-blocking + 2 waiver acceptances documented)
auditor: auditor-agentic Opus 4.7
final_state: done
---

# Merge — luana-copilot-engine

## Resumen

Story 6 cierra DONE. 15 luana-platform commits + 9 AISALESHT closure commits (impl-logs + results + checkpoint transitions + merge doc).
auditor-agentic Opus APPROVED. Copilot engine 33k LOC lifted intact to `luana-core-copilot` v0.0.6-alpha. D-T1 registry contracts FROZEN via golden snapshot (V-AG-3). D-T6 anti-mirror cardinal honored (zero shared/agent_observability mirror in copilot src/). T-16 UNLIFT brought 30 deferred files from Stories 2-5 copilot_provider/ subfolders to 8 luana-core packages.

T-17 R26 hotfix-repro-mandatory exemplary deferral: architect spec premised MessageModel lived in copilot, repro confirmed FALSE (MessageModel lives in sales_agent → Story 7 territory). Builder correctly halted + deferred to Story 7 per `.claude/rules/hotfix-repro-mandatory.md`. Documented in T-17-impl-log.md + DEFERRED-FILES.md + V-AG-4 allowlist with Story 7 reference.

Hard invariants live-verified:
- AISALESHT `backend/src/modules/copilot/` source untouched 21 tickets (V-NF-4)
- 30 deferred files correctly unlifted via T-16 (8 packages copilot_provider/ + offer_ai.py + 4 cross-coupling tests)
- 0 brand-specific control flow (V-AG-1)
- 0 forward imports a Stories 7/8+ (V-AG-2)
- ToolRegistry + WorkflowRegistry + ExtractorRegistry + ModuleRegistry + SuggestionRegistry public APIs frozen (V-AG-3 golden snapshot)
- 0 residual stubs (V-AG-4 — MessageModel allowlisted with Story 7 reference)
- 0 observability mirror in copilot (V-AG-5)
- ModuleDescriptor complete for lifted packages (V-AG-6)
- PersonalityCompiler SSoT regression Story 5 intact (V-AG-7)
- 36 [COPILOT-*] anchors stable (V-AG-8 — 33 copilot proper + 3 in unlifted business modules)
- Workspace 22 packages registered (21 prev + 1 Story 6)
- pyproject version 0.0.6-alpha
- No publishConfig / .releaserc / release.yml (V-NF-5/6/7 deferred Story 9)
- 1640 pytest collected luana-core-copilot

## Commits aplicados

Repo `alpacapurpura/luana-platform` (main, 15 commits range 8506a45..3d4f872):
- T-1 8506a45 chore(workspace) register Story 6 luana-core-copilot
- T-2 a1180ce feat skeleton + pyproject + README
- T-3 63b069c feat copilot domain layer (33 files lifted)
- T-6 917c362 feat copilot infrastructure repositories + models
- T-7 a60fa7b feat copilot infrastructure persisters
- T-8 e1e446f feat copilot infrastructure channels + voice + qdrant + cache + prompts + web + workers
- T-9 8602ae0 feat copilot application orchestrator (LangGraph + deepagents + prompt slot composer)
- T-10 c0040be feat copilot application tools (ToolRegistry + 24 tools + 3 subfolders)
- T-11 3fcd317 feat copilot application 9 subfolders (router/suggestions/workflows/procedures/data_access/extraction/guided/memory/observability)
- T-12 7f03cda feat copilot application services + discovery + extraction_card_flow
- T-13 200cb97 feat copilot observability subfolder (D-T6 anti-mirror cardinal subclass pattern)
- T-14 9a06818 feat copilot api 21 files (11 routers + 9 DTOs + _dependencies)
- T-15 4c98bfe feat lift evals + utils + aggregate GREEN finalize (1603 pass / 25 skipped DAG-deferred T-16)
- T-16 ca3cd18 feat UNLIFT Stories 2-5 copilot_provider/ + offer_ai.py + 4 cross-coupling tests (30 files)
- T-19 9a7a0df test brand-agnostic + no-forward-module-imports arch fitness
- T-20 eaa1446 test D-T1+D-T2+D-T6 cement (6 NEW arch fitness V-AG-3..V-AG-8 + entry-points wiring 8 pyprojects)
- T-21 3d4f872 docs DEFERRED-FILES + README polish + ruff per-file-ignores pyproject + ~230 file ruff --fix idempotent cleanup

Repo AISALESHT (development):
- Multiple commits 3e8aaeb7, 3310c76b, 67f418e6, 9c695d96, 58f5ace5, fd109230, 550c2965, fea92ce4, 98dd4748 — Story 6 ready package + 21 impl-logs + 19 result docs + checkpoint state transitions (refining → refined → ready → developing → developed → reviewing → done)

## Validators outcome

- 24 validators total per 04-validators.yaml
- 22/24 GREEN (V-NF-1..V-NF-7 + V-AG-1..V-AG-8 + V-F-langgraph + V-F-prompt-cache + V-F-tools + V-F-workflows + V-F-registry-1/2 + V-F-trace + V-F-cost + V-F-py-1 + V-F-py-2 + V-F-marketing-kb + V-F-x-1 + V-D-1 + V-D-2)
- 2 waiver acceptances (info-level, pre-existing):
  - **V-F-x-2** (aggregate pytest core/) — conftest plugin collision al correr 22 packages junto desde repo root. Pre-existing Story 4/5 territory per session 2 retro-audit precedent. Per-package runs all GREEN.
  - **V-F-x-1 partial** — API surface adaptation (lift-verbatim outcome §7.3 mandate)
- Per-package: 1640 pytest collected luana-core-copilot (1603 pass + 25 skipped DAG-deferred + 12 conftest discovery)
- 8 NEW arch fitness Story 6 GREEN: V-AG-1..V-AG-8 (22 cases passed in 138s at audit re-run)
- Downstream regression Stories 2-5 packages: 2218 passed / 19 skipped / **zero regressions**

## Findings auditor

### Info-level (non-blocking, docs cleanup)

| ID | Cat | Path:line | Issue | Acción |
|---|---|---|---|---|
| INFO-1 | C5 | Multiple `T-*-impl-log.md` files | Process drifts surfaced (sed gap unittest.mock.patch + anchor count math + R26 catch + V-F-x-2 conftest collision) properly documented but spread across batches | Aggregate to `docs/process/learnings.md` post-session 3 closure |
| INFO-2 | C2 | `04-validators.yaml` V-F-x-2 | Pre-existing workspace constraint inherited from Story 4/5 — waiver pattern OK | Address Story 9 aggregate test isolation cleanup |
| INFO-3 | C3 | `core/tests/architecture/test_no_residual_test_stubs_post_story_6.py` | MessageModel stub allowlisted with Story 7 reference (R26 deferral correct) | Verify Story 7 T-X cement when sales_agent.MessageModel lifts |

### Strengths surfaced

1. **R26 hotfix-repro-mandatory exemplary execution** at T-17 — builder correctly REPRO-FAILED + deferred to Story 7 instead of implementing wrong-scope fix. Companion arch fitness test `test_allowlisted_stubs_still_present` for drift detection
2. **D-T1 golden snapshot byte-stable registry contract** with `_generate_copilot_registry_snapshot.py` write-once script + "own attrs only" filter (architect-grade engineering depth)
3. **D-T6 cardinal anti-mirror discipline** rigorously enforced via V-AG-5 (5 forbidden classes + 1 forbidden function = zero declarations in copilot src/)

### Cross-Story-7 handoff documented

- D-T2 cement deferred T-17 → Story 7 (MessageModel lift cements V-AG-4 stub removal)
- D-T3 BrandVoicePort introduction Story 7 (per ADR-001 §2.4 + 06-tickets.yaml T-3 Story 7)
- connections/api/dependencies real ChatOrchestrator wiring → Story 7 T-16 (needs luana_core_sales_agent)
- AppointmentModel stub in offer-studio conftest → Story 8 (scheduling lift)

## Capabilities promovidas

1 package tracked at outcome level:
- `luana-core-copilot` v0.0.6-alpha — Copilot engine + LangGraph 2.0 StateGraph + deepagents harness + Anthropic prompt cache 11-slot architecture (TTL 1h slots 1-3, 5min slots 4-6) + 5 frozen registries (Tool/Workflow/Extractor/Module/Suggestion) + Qdrant marketing KB tenant-agnostic + observability subclass pattern (CopilotCallbackHandler + CopilotObservabilityContext) + 24 tools + suggestions engine + workflows engine + procedures (brand_setup + offer_creation + first_setup) + extraction (doc + cards) + 11-router API + 11-DTO schema + voice transcription + Telegram bot + arq workers + 4 evals (golden_dataset + 3 scorers) + memory + data_access + guided creation

Plus 8 packages with new copilot_provider/ subfolders (T-16 UNLIFT):
- `luana-core-brand-studio` (8 files), `luana-core-offer-studio` (5 + offer_ai.py), `luana-core-crm` (2), `luana-core-analytics-engine` (2), `luana-core-landing` (2), `luana-core-connections` (2), `luana-core-commercial-calendar` (2), `luana-core-social-proof` (2)

Final outcome capabilities cumulative: **33** (5 Story 1 + 15 Story 2 + 6 Story 3 + 4 Story 4 + 2 Story 5 + 1 Story 6).

## DEFERRED files Story 6 (track DEFERRED-FILES.md)

5 deferrals registered:
- T-17 MessageModel D-T2 cleanup → Story 7 (R26 correction: MessageModel lives in sales_agent NOT copilot)
- Streamlit admin pages → Story 10 (nicolify shell migration)
- connections/api/dependencies real ChatOrchestrator wiring → Story 7 (needs luana_core_sales_agent)
- AppointmentModel stub in offer-studio conftest → Story 8 (scheduling lift)
- V-F-x-2 conftest collision workspace constraint pre-existing → Story 9 cleanup

## Session 3 stats (Story 6 portion)

- Total spawns Story 6: 8 (1 architect Opus + 6 builder-agentic Opus batches + 1 auditor-agentic Opus)
- Total wall clock Story 6: ~14h Opus across 6 batches
- Builder pattern: T-1+T-2+T-3 / T-6+T-7+T-8 / T-9+T-10+T-11 / T-12+T-13+T-14 / T-15 / T-16+T-17+T-18 / T-19+T-20+T-21
- AISALESHT untouched verified post-merge (V-NF-4 bulletproof 21 tickets)
- R23 honored: builder-agentic + auditor-agentic Opus throughout, NO Sonnet fallback, NO --no-verify

## Próximo paso

- Outcome `luana-platform-migration` continúa state=developing
- 6/14 stories DONE (Stories 1-6)
- Next story unblocked: `luana-sales-agent-engine` (Story 7) — was blocked_by [Story 6 + Story E waived per ratificación 2]. Story E gate WAIVED to Luana v0.2.0. Story 7 unblocked.
- Session 3 continues with Story 7 — **handed off to new conversation per Chris mandate 2026-05-11** (memory budget control).
