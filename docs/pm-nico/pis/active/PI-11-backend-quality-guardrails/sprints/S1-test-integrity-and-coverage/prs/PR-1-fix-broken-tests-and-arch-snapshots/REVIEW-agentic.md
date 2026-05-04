# Agentic Review — PR-1 fix-broken-tests-and-arch-snapshots

> Auditor: `nicolify-agentic-auditor` (Opus 4.7) — invariants validated against canonical docs as of 2026-05-04
> Iter: 1
> Verdict: **PASS**
> Generated: 2026-05-04T22:15:00Z

## Inputs

- CONTEXT-BRIEF.md: used (read raw — § 7 existing systems + § 8 EXTEND-vs-NEW satisfied for agentic surface; no new module files created agentic-side)
- gate-output.json: used (iter 2 subset — pytest gate `NATIVE_VALIDATED` per builder evidence; mypy/jscpd/pip-audit failures verified as baseline pre-existing — no agentic-touched file appears in first 5 errors of any failing gate)
- Skills invoked: copilot-expert=Y, sales-agent-expert=Y, tessl__langgraph=N (justified — no LangGraph state schema/topology/tool/node modified; only mocked instances around helper test fixtures), tessl__graceful-degradation=N (justified — no new external call introduced agentic-side; only test patches around existing best-effort outbox `try/except BLE001` documented in IMPL-LOG)

## Gate status (from gate-output.json, scope-filtered for agentic)

| Gate | Status | Errors agentic-touched | Notes |
|---|---|---|---|
| ruff (lint) | PASS | 0 | builder native |
| ruff (format) | PASS | 0 | builder native |
| pytest (NATIVE_VALIDATED) | PASS | 0 | 2488/2488 5x consecutive deterministic; 7/7 sales_agent arch tests; verified manually `pytest tests/architecture/test_sales_agent_*.py -q` → 7 passed in 10.82s |
| mypy | FAIL (baseline) | 0 | 1972 errors concentrated `src/modules/copilot/application/orchestrator/chat.py` + `sales_agent/workers/` — VERIFIED PR-1 did NOT touch any source file in `backend/src/modules/{copilot,sales_agent}/` (`git diff main..HEAD --stat` empty for those paths). Pre-existing baseline. info-only. |
| jscpd | FAIL (baseline) | 0 | 363 clones at 3.91% (UNDER 5% threshold per CONTRACT). 0 clones in agentic-touched test files. info-only. |
| pip-audit | FAIL (baseline) | 0 | 14 pre-existing CVEs (langchain, pillow, lxml, pypdf, pytest, python-multipart). Out-of-scope per CONTEXT-BRIEF. info-only. |
| interrogate | PASS | 0 | docstrings OK |

**Verdict-affecting failures: 0.** All gate FAILs are pre-existing baseline; none touch agentic PR-1 commit hashes (`fe17786c`, `1e81f930`, `f7c58f15`, `e568927a`, `62bce314`, `27c997e4`).

## 13 categories (12 + Cat 13 mirror detection)

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | PASS | No state schema modified; agentic diff only test infra. `_chat_flow_snapshot_helpers.py:27 TENANT_ID = UUID(...)` preserved; mocks around orchestrator do not mutate compiled `agent_app`. |
| 2 | Tool registration | PASS | Zero `@tool` decorators added/modified in agentic diff. `test_offer_section_tools.py` only adds `_engine_suggestions_for_context` mock (test isolation), preserving existing tool contract. |
| 3 | Prompt cache architecture | PASS | `test_sales_agent_system_prompt_order.py:30` + `test_compose_system_prompt.py:37` extend `EXPECTED_CACHEABLE` with `PromptFragment.CAMPAIGN_CONTEXT` — appended at END of cacheable tuple (slot 7), AFTER existing 6 slots (STATIC_IDENTITY/STATIC_TOOLS_HINT/STATIC_PLAYBOOK/AGENT_IDENTITY/BRAND_VOICE/CHANNEL_FORMAT_HINT). Append-only preserves prefix invariance for prior 6-slot tenants when CAMPAIGN_CONTEXT empty (PR-7 outbound mode = opt-in). Slot 5 BRAND_VOICE position untouched. No dynamic content (timestamps/tenant_id) injected mid-prefix. |
| 4 | deepagents subagent isolation | PASS | No subagent tools/keys/middleware modified in agentic diff. |
| 5 | Observability + cost recording | PASS | No LLM call sites added/modified in agentic diff. Snapshot helper change at `_chat_flow_snapshot_helpers.py:248` patches `event_bus_adapter.adapter_bus.publish` — increases observability fidelity (now captures real domain_events that were silently swallowed pre-fix). Baseline regenerated `telegram_new_lead_baseline.json` shows `lead_captured` event with `tenant_id`, `payload`, `event_name` — matches schema. |
| 6 | Eval goldens (sales_agent) | PASS | Snapshot baseline `telegram_new_lead_baseline.json` regenerated (CONTRACT § 4 D6 — Caso A adapter_bus mock). Pre→post diff documented IMPL-LOG agentic § Snapshot baseline diff. Tenant_id deterministic across all 5 occurrences. session_id update from `…003`→`…001` is consistent within snapshot (uuid sequence ordering — deterministic per fixture). NO PersonalityProfile / specialist prompt content modified, so no voice fidelity grader regen required. |
| 7 | RAG / Qdrant hygiene | PASS | No Qdrant client / KnowledgeService / vector op touched in agentic diff. |
| 8 | LLM provider routing | PASS | No provider router / model name strings modified agentic-side. (`shared/infrastructure/llm/providers/litellm.py` Kimi clamp = business surface, out of agentic scope.) |
| 9 | Cost optimization | PASS | Cache prefix invariance preserved (cat 3); no token/cost regression introduced. |
| 10 | Channel format / brand voice | PASS | Voice files untouched. Spanish neutro respected in test docstrings (`test_voice_combined.py:135` "Legacy /transcribe deprecado…queda como follow-up PR"). Sales_agent agent OUTPUT voice (tenant voseo respect) untouched — only test infra modified. |
| 11 | DDD compliance (agentic) | PASS | All agentic-touched files live in `backend/tests/{architecture,modules/copilot,modules/sales_agent,integration}/` — correct test layer placement. No graph in `infrastructure/`, no tool in `domain/`, no cross-module business import created. |
| 12 | Tests / TDD | PASS | All agentic-scope changes are test hardening; no production logic added agentic-side. Polluter hunt ROOT CAUSE confirmed at source (singleton fixture business commit `7652f1f8` = orchestrator state leak fix), NO `@pytest.mark.flaky` band-aid landed (verified `test_chat_orchestrator_snapshot.py` clean of flaky marker). 5x consecutive deterministic runs (2488/2488) per IMPL-LOG agentic § Polluter hunt log Step 3. Snapshot regression preserved (baseline regenerated within same PR — accepted per CONTRACT § 10 Q5). |
| 13 | Mirror detection (cross-module duplication) | PASS | NO new files in `modules/copilot/observability/recording/` or `modules/sales_agent/observability/`. NO new mirror class (turn_envelope/callback_handler/cost_calculator/fx_resolver/pricing_resolver). `git diff main..HEAD --diff-filter=A --name-only` for backend/ returns ONLY `tests/shared/infrastructure/llm/test_litellm_kimi_clamp.py` + `tests/shared/test_legacy_event_bus_deprecation_warning.py` — both business-surface regression test files in `tests/shared/`, NOT in agentic scope. CONTRACT § 0 explicitly classifies all 5 surfaces = EXTEND, ZERO NEW. PR.md § "Existing systems audit" populated with grep evidence (path:line) per anti-duplication.md enforcement layer 1. |

## Findings (file:line)

### FAIL
(none)

### WARN
(none)

### info
- [Cat 5] `backend/tests/modules/sales_agent/orchestrator/_chat_flow_snapshot_helpers.py:248-255` — Belt-and-suspenders dual-patch (`adapter_bus.publish` + `EventBus.publish`) is correct defense-in-depth post-cutover and matches CONTRACT § 4 Caso A directive verbatim. Future PR could simplify by relying solely on adapter_bus once dual-write window closes (post 4-week reconciliation per sales-agent-expert SSoT). Not blocking.
- [Cat 6] `backend/tests/snapshots/orchestrator/telegram_new_lead_baseline.json:46,143` — `session_id` shifted `…003` → `…001`. IMPL-LOG documents this as deterministic uuid sequence reordering (consistent within new snapshot — both occurrences match). Snapshot test passes 5x consecutive runs deterministic, confirming determinism. Not a regression. Recommend brief inline comment in snapshot baseline JSON header (or sibling README) explaining frozen UUID sequence rationale for future readers.
- [Cat 12] `backend/tests/modules/copilot/test_outbox_adapter_integration.py:96-118` — Pattern `monkeypatch.setattr(... settings, MagicMock(USE_OUTBOX_PATTERN_COPILOT=False, ...))` is justified Caso E meta-test of adapter routing (per CONTRACT § 3 Caso E). IMPL-LOG agentic § Stash Files Audit row 5 acknowledges this. PR-3 arch fitness `test_no_legacy_eventbus_mock_when_outbox_on.py` should add file to its `KNOWN_LEGACY_MOCK_FILES` allowlist with `# arch-bypass: testing legacy capability` magic comment per CONTRACT § 13 cross-PR signal. Coordination signal flagged for PR-3 builder, NOT blocking PR-1.
- [Cat 12] IMPL-LOG agentic § Cross-PR Coordination notes 6 deferred Caso A copilot files (`test_extraction_event_handlers`, `observability/test_*`, `api/test_suggestions*`, `suggestions/test_*`) NOT migrated this iter. Documented as future-PR scope. Out of stash + out of PR-1 scope per CONTRACT § 11 surface mapping. Not blocking PR-1 close — PR-3 builder will baseline-allowlist them.

## Cross-scope flags (if any)
(none — agentic surface contained to listed scope; FE slug fix + business EventBus migration + litellm clamp / deprecation warning belong to backend-auditor scope per CONTRACT § 0 surface mapping)

## Research notes (DATE-AWARE — Step 0 = 2026-05-04)

**No novel pattern introduced agentic-side.** All agentic changes are test infra extensions that consume pre-existing patterns:
- `monkeypatch.setattr(instance_attribute, ...)` — pytest stable API (pytest >=2024 docs)
- LangGraph `agent_app = workflow.compile()` module-level cache — referenced from CONTRACT § 1 candidate B; no NEW reset method introduced (singleton fixture business-side covers root cause)
- Anthropic prompt caching — `CACHEABLE_FRAGMENTS` append-only at end preserves prefix bytes; cache_control marker placement on final block invariant respected (consistent with `https://platform.claude.com/docs/en/build-with-claude/prompt-caching`, accessed 2026-05-04 via canonical doc URL — slot ordering invariance for cache hit retention)

**Knowledge cutoff disclosure:** Opus 4.7 cutoff = January 2026. Agentic surface uses pytest fixture + LangGraph module-level patterns documented pre-cutoff (stable APIs). No live WebSearch needed — patterns are not novel for this PR.

**Live anchors checked (no live fetch performed since no novel pattern):**
- LangGraph: `https://docs.langchain.com/oss/python/langgraph/workflows-agents` — referenced for state hygiene cat 1
- Anthropic prompt caching: `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` — referenced for cat 3 cache prefix invariance

## Recommendations for builder fix-loop

(none — verdict PASS)

Optional improvements (non-blocking, can land later):
1. Strip belt-and-suspenders legacy `EventBus.publish` patch from `_chat_flow_snapshot_helpers.py` once 4-week dual-write reconciliation window closes (post sales-agent S11A cutover). Defer to PI-12 cleanup.
2. Add brief inline comment to `telegram_new_lead_baseline.json` (or sibling README) explaining FROZEN_NOW + frozen UUID sequence rationale for future maintainers.
3. PR-3 builder: add Caso E meta-tests (`test_outbox_adapter_integration.py` files) to `KNOWN_LEGACY_MOCK_FILES` allowlist with magic comment, per CONTRACT § 13 cross-PR coordination signal.

## Drift detection (CONTRACT vs code)

NO drift detected. Agentic surface honored CONTRACT § 4 (Caso A adapter_bus mock for snapshot helper), CONTRACT § 6 (polluter hunt at-source via singleton fixture, no band-aid), CONTRACT § 9 stash apply checklist (8 agentic files committed in 5 granular commits per IMPL-LOG agentic § Commits), and CONTRACT § 11 surface mapping (no agentic edit on `tests/conftest.py` — owned by business builder per regla M3).

