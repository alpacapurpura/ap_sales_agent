<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# REVIEW-agentic.md — Story 12 Comunify AGENTIC audit

**State input:** developed (Phase 3 closed 2026-05-14, 39/39 GREEN per checkpoint)
**Auditor:** auditor-agentic Opus 4.7
**Date:** 2026-05-14
**Scope (agentic only):** T-extensions-1, T-prompts-1, T-tools-{1..4}, T-extractors-{1,2}, T-workflows-{1,2}, T-kb-1, T-guards-{1..4}, T-voice-{1..4}, T-rubric-1, T-eval-1
**Excluded:** BE (T-be-*, T-payment-1, T-scaffold-1, T-config-1 → REVIEW-be.md WARN) · FE (T-fe-*, T-widget-1, T-e2e-1) · cross-cutting (T-deploy-1, T-docs-1)
**Code dir:** `/home/chris/luana-platform/comunify/backend/src/modules/comunify/{agentic,copilot,brand}/`
**Skills invoked:** copilot-expert ✅ · sales-agent-expert ✅ · tessl__langgraph ✅ · tessl__graceful-degradation ✅

**Verdict: WARN**

PASS criteria fail by 1 HIGH operational (uncommitted agentic surface in luana-platform working tree). Zero CRITICAL, zero tenant-iso/PII/security failures. Code quality + tests + arch invariants 100% GREEN. Mechanical math: 1 HIGH (operational, not security) + 2 MEDIUM + 3 LOW + 2 INFO → WARN.

## Inputs

- CONTEXT-BRIEF.md: not used (re-read raw checkpoint + 03-arch-agentic + REVIEW-be)
- gate-output.json: not used (spawned new run inline — see Gates table)
- Skills invoked: copilot-expert=Y, sales-agent-expert=Y, tessl__langgraph=Y, tessl__graceful-degradation=Y

## Gates executed (agentic-scope)

| Gate | Result | Detail |
|---|---|---|
| Architecture fitness (agentic invariants) | PASS | 144/144 tests pass in 0.23s — including `test_comunify_voice_distillation_inherits_base_orchestrator`, `test_comunify_no_pii_in_cacheable_slots` (35 tests), `test_comunify_slot_4_safety_markers_present` (13 tests), `test_comunify_cost_bucket_invariant`, `test_comunify_no_query_without_tenant_filter`, `test_comunify_rubric_md_v1_schema` (16 tests), `test_comunify_personas_yaml_completeness` (9 tests). |
| Agentic eval suite (full) | PASS | 502/502 tests pass in 3.34s — covers tools (75 tests), extractors (52), workflows (28), guardrails (56), voice cloning (56), KB pack (50), grader (46), observability trace invariants (10), cache hit rate (4), cost budget (15), compliance smoke (12). |
| Slot 4 safety markers + no-PII | PASS | Sandbox markers `<<TRANSCRIPT_BEGIN>>`/`<<TRANSCRIPT_END>>` cement-enforced; 35 PII-in-cacheable-slot tests GREEN. |
| Voice distillation inherits BaseExtractionOrchestrator | PASS | 5 assertions (wave count, log prefix, confidence weights, schema_version, base class identity) — arch ratchet. |
| R23 routing verification | PASS | All 11 reviewable agentic commits trail `Co-Authored-By: Claude Opus 4.7 (1M context)`. T-voice-{1..4} + T-extensions-1 + T-kb-1 have no commit (see [H1] below) — but their builder spawn metadata in result.md cites `production_code=true → Opus mandatory` and impl-log shows Opus-routed work. |

## 12 categories

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph 2.0 state hygiene | PASS | `community_engagement_workflow.py:79-112` TypedDict `CommunityEngagementState` includes `tenant_id`, `iterations` anti-loop counter; nodes return partial dicts (no in-place mutation); `cohort_enrollment_workflow.py:840-906` 8 `add_conditional_edges` all terminate to `END`; `CheckpointerProtocol` D10 swap-ready (MemorySaver default, RedisSaver-compat). Composite thread_id `f"{tenant_id}:{subscriber_id}"` enforces cross-subscriber isolation at checkpointer boundary. |
| 2 | deepagents subagent isolation | N/A | Comunify does NOT use deepagents `task` tool — pure LangGraph StateGraph workflows + tool functions with explicit DI. No subagent sandboxing surface to audit. |
| 3 | Anthropic prompt cache slot architecture | PASS | `agentic/prompts/compose.py:308-356` 10-slot architecture per 03-arch § 8: slots 1-6 carry `cache_control: {"type":"ephemeral"}`, slots 7-10 NOT cached. Slot 5 BRAND_VOICE per-tenant via LiteLLM `prompt_cache_key=tenant_id` (caller wiring). `tenant_id` intentionally NOT injected mid-block (`compose.py:304-306`). `cacheable_prefix_blocks()` helper for byte-equality tests. Cache hit rate test `test_cache_hit_rate.py` PASS 4/4 (synthetic ≥85%). |
| 4 | `copilot_trace_event` observability writes | PASS | All 4 tools (`qualify_for_cohort.py:627-675`, `link_to_community.py:802-869`, `nurture_via_authority_content.py:794-870`, `book_discovery_call.py`) emit best-effort `trace_event_repo.add(...)` with PII-scrubbed payload via `_scrub_pii` defense-in-depth + `_sanitize_payload` lazy fallback. Every write wrapped `try/except + structlog.warning` (R17 best-effort). Workflows emit structlog node events (`community_engagement_workflow.py:199,244,307,360,378`); production trace_event persist deferred to tool dispatch (workflow boundary best-effort). |
| 5 | Eval goldens fidelity (sales_agent parity) | PASS | `tests/agentic_evals/grader/test_voice_fidelity_per_fixture.py` 9 tests PASS — per-fixture voice fidelity per `qualification-accuracy.md` (Story E rubric) + `creator_economy_fidelity.md` (T-rubric-1). 8 personas YAML completeness arch-enforced. Adversarial fidelity grader 19 tests PASS (`test_vertical_creator_economy_fidelity_adversarial.py`). |
| 6 | Qdrant RAG tenant filtering (KB pack) | PASS | `tests/agentic_evals/kb_pack/test_tenant_filter_at_query.py` 7 tests PASS — every KB query filters tenant scope. `creator_economy_kb_v1` is tenant-agnostic (analogous to copilot `nicolify_marketing_kb` F10 pattern) — confirmed by `test_seed_idempotent.py` (15 tests). `test_vulnerable_disclosure_forced.py` 28 tests PASS (forced disclaimer policy). |
| 7 | LLM provider routing | PASS | Tools use `_LLMClientLike` Protocol DI (`qualify_for_cohort.py:316-332`); concrete LiteLLM adapter injected by caller. Default models declared as constants per-tool (`_DEFAULT_FIT_ASSESSMENT_MODEL = "anthropic/claude-sonnet-4-6"` line 96, etc.). No hardcoded model strings in workflows or extractors. Voice distillation 4-wave declares `dialect_detection=Haiku 4.5 nano`, `vocabulary/register/validate=Sonnet 4.6 reasoning` per `voice_distillation_orchestrator.py` docstring + wave config. |
| 8 | Cost recording | PASS | `voice_distillation_orchestrator.py:117-122` per-wave `_PER_WAVE_COST_CEILING_USD` Decimal ceilings sum ≤ V-AE-21 $0.18 budget. Cost accumulator pattern in workflow `cost_accumulated_usd` state field. `test_cost_budget_*` 15/15 tests PASS (lead_qualification, drift_reengagement, moderation, voice_distillation, voice_distillation_full). `test_comunify_cost_bucket_invariant` arch gate enforces eval calls write only to `eval_simulator_llm_call` bucket. |
| 9 | Brand-voice compliance (voice cloning + Slot 5) | PASS | `voice_distillation_orchestrator.py` 4-wave compiler produces `CompiledVoice` (6 v2 blocks: identidad/dialecto/vocabulario/registro/asi_no/anclajes) bridged via `compiler_integration.py` (T-voice-3) to `personality_profiles.system_instruction` SSoT. Raw chat samples DELETED post-success (D15 privacy — `_raw_samples_remover.delete_raw_samples` line 1014). `test_voice_samples_pii_sanitized.py` 21 tests PASS — payloads carry counts/confidence/cost only, NEVER message bodies. Slot 4 j2 sanity: NO `{tenant_name}` interpolated mid-block (LLM-side template markers `{brand_name}` `{creator_name}` only). |
| 10 | R10 anti-duplication (mirror shared/ check) | WARN | Voice distillation correctly extends `luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator` ✅ (arch gate). `_LLMResponse` re-imported from sibling `offer_ladder_advisor` (N=2 within comunify; lift trigger N=3 documented) ✅. **BUT** `prompt_injection_block_reuse.py` is a 95%-byte mirror of `vitalia/.../prompt_injection_block_reuse.py` — documented as intentional N=2 sibling pattern with lift trigger at 3rd vertical. Mirror diff = only docstring header + brand reference; ~250 LOC of pattern catalog + Protocol + check function duplicated. Decision NOT-LIFT justified in module docstring (small surface, per-vertical audit_log adapter differs). Per Cat 13 rule — file nuevo en `modules/{X}/<subsystem>/` con docstring "mirror del pattern X" → WARN (not FAIL because lift trigger explicitly documented + auditor of Story 13+ owns re-litigation). |
| 11 | R3 downstream regression | N/A | Comunify is isolated under `luana-platform/comunify/`. `git diff` shows zero changes to AISALESHT `backend/src/shared/` or `core/luana-core-*` cross-consumer surfaces touched **by agentic scope**. No path in `.claude/rules/auditor-downstream-regression.md` table is modified by agentic tickets. Downstream gate-runner spawn not required. |
| 12 | R23 enforcement (Opus exclusive) | PASS | 11/17 committed agentic tickets carry `Co-Authored-By: Claude Opus 4.7 (1M context)` trailer (verified via `git log` on each SHA: c30faf8, 2bcdc35, 825d98d, 96af3c4, 8edb6ed, 1898bf2, 52c12ac, 9d2030b, b0b19d9, b1fcdc5, + module_registry_entry portions of T-workflows-2). Remaining 6 agentic tickets (T-voice-1..4, T-extensions-1, T-kb-1) have IMPL-LOG + RESULT cite Opus routing per R23 but lack a committed SHA (see [H1] below). |

## Findings (scored)

### CRITICAL — 0

None. No security/PII/tenant-iso/cache-prefix-leak/cost-overrun violation.

### HIGH — 1

**[H1] T-voice-1..4 + T-extensions-1 + T-kb-1 + part of T-workflows-1 NOT committed to luana-platform git**

- **Location:** `/home/chris/luana-platform/` working tree shows 27 untracked paths covering:
  - `comunify/backend/src/modules/comunify/brand/voice_cloning/` (4 .py files — T-voice-1..3)
  - `comunify/backend/src/modules/comunify/extensions.py` (T-extensions-1)
  - `comunify/backend/src/modules/comunify/copilot/kb/creator_economy_kb_v1/` (manifest.py — T-kb-1)
  - `comunify/backend/src/modules/comunify/copilot/workflows/community_engagement_workflow.py` (T-workflows-1)
  - `comunify/backend/src/modules/comunify/copilot/__init__.py` + `workflows/__init__.py`
  - `comunify/backend/scripts/seed_creator_economy_kb.py`
  - `comunify/backend/tests/agentic_evals/{voice_cloning,kb_pack,workflows,smoke}/` (test suites)
  - `comunify/backend/tests/test_extensions_register_all.py`
- **Evidence:**
  - `git log --all --oneline --diff-filter=A -- comunify/backend/src/modules/comunify/brand/voice_cloning/voice_distillation_orchestrator.py` → empty
  - `git log --all --diff-filter=A -- comunify/backend/src/modules/comunify/extensions.py` → empty
  - `git log --all --diff-filter=A -- comunify/backend/src/modules/comunify/copilot/kb/creator_economy_kb_v1/manifest.py` → empty
  - But T-voice-1-result.md / T-extensions-1-result.md / T-kb-1-result.md all claim `state: done · Verdict: tests-passing` with file paths matching the untracked tree.
- **Impact:** Story 12 checkpoint claims `developed` with 39/39 GREEN — verified locally by re-running 502/502 agentic_evals + 144/144 arch tests against the filesystem state. Code quality is intact; the gap is purely operational (not pushed to `development` branch). When `/pm` proceeds to Phase 5 merge, these files MUST be committed first OR the merge artifact is incomplete.
- **Severity:** HIGH (operational, not security). Code reviewed and verified GREEN; commit-and-push step pending. Same gap was NOT flagged by REVIEW-be.md because BE tickets (T-be-1..9, T-payment-1, T-scaffold-1, T-config-1) are all committed (commits 8606028..1b62ec5).
- **Remediation:** Before Phase 5 merge, Chris delegates Haiku worker (per `.claude/rules/git-haiku-delegation.md`) to commit the 27 untracked files in 6 logical conventional commits matching ticket boundaries: `feat(comunify/T-voice-1..4)`, `feat(comunify/T-extensions-1)`, `feat(comunify/T-kb-1)`, `feat(comunify/T-workflows-1)`. Each commit MUST include the R23 Opus 4.7 trailer + cite `decisions_applicable` per R6.

### MEDIUM — 2

**[M1] R10 anti-duplication WARN — `prompt_injection_block_reuse.py` 95%-byte mirror vitalia↔comunify**

- **Locations:**
  - `/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/agentic/guardrails/prompt_injection_block_reuse.py` (Story 11)
  - `/home/chris/luana-platform/comunify/backend/src/modules/comunify/agentic/guardrails/prompt_injection_block_reuse.py` (this PR)
- **Diff:** module docstring + brand references only (~50 lines diff across ~250 LOC file). Regex catalogs, Protocol definitions, refusal phrasing, sandbox markers constants — all duplicated.
- **Documented rationale (file docstring lines 28-40):** Pattern is small (~5KB regex catalog); per-vertical `_AuditLogLike` adapter differs (ComplianceEventService vs MedicalAuditLogRepository); lift trigger explicitly set at "3rd vertical needs the same guard". Story 13+ owner re-litigates.
- **Per Cat 13 rule WARN clause:** "Una clase con suffix `…Handler`/`…Resolver`/`…Factory`/`…Service` similar en otro módulo sin shared abstraction explicit." This guard predates Story 13 — N=2 mirror is acceptable at WARN with documented lift trigger.
- **Remediation:** Track lift-to-`core/luana-core-guardrails/` ticket in BACKLOG.md for Story 13+ (Pulse/Plenum/etc. vertical onboarding). Auditor recommends ratify the documented rationale as a Comunify-scoped Pattern (analog to compose.py NOT-LIFT decision in same docstring family).
- **Severity:** MEDIUM (rule WARN clause, fully documented + tested).

**[M2] R6 "Decisions honored" cite incomplete in commit bodies**

- **Ticket convention:** `06-tickets.yaml` declares `decisions_applicable: [D#]` per agentic ticket (e.g. T-tools-1: `[D1]`; T-workflows-2: `[D3, D10, D19]`; T-prompts-1: `[D5]`; T-extractors-1: `[D17]`; T-extractors-2: `[D16]`; T-voice-1: `[D8, D15]`).
- **Commit bodies (verified via `git show --pretty=%B`):**
  - ✅ `52c12ac` (T-workflows-2) cites D3 + D10 + D19 explicitly in narrative — full coverage of declared decisions.
  - ✅ `b0b19d9` (T-prompts-1) cites D5 (NEW Slot 4 overlay) explicitly.
  - ⚠️ `c30faf8` (T-tools-1) declares `decisions_applicable: [D1]` but commit body has NO mention of D1 (in narrative or formal "## Decisions honored" section).
  - ⚠️ `2bcdc35` (T-tools-2), `825d98d` (T-tools-3), `96af3c4` (T-tools-4) — no formal Decisions honored section; partial implicit citation in feature description.
  - ⚠️ `8edb6ed` (T-extractors-1) declares `[D17]` but commit body lacks formal section.
  - ⚠️ `1898bf2` (T-extractors-2) declares `[D16]` likewise.
  - ⚠️ `9d2030b` (T-guards-1..4) lists 4 batched tickets — partial coverage of `[D4]`, `[D8,D15]`, `[D15]`, `[D8]`.
- **Per Cat 15 rule WARN clause:** "Cite incompleto en commit body pero presente en IMPL-LOG.md o T-{n}-result.md" — IMPL-LOG.md files DO cite decisions per ticket. Hence WARN, not FAIL.
- **Remediation:** Auditor self-fix when Haiku commit worker runs for [H1] uncommitted tickets: add `## Decisions honored` formal section to commit bodies for T-voice-1..4 + T-extensions-1 + T-kb-1 + T-workflows-1 (the about-to-be-committed batch). Past commits (c30faf8, etc.) are immutable per `.claude/rules/git-safety.md` (no amend pushed commits) — log as process-improvement entry.
- **Severity:** MEDIUM (cite hygiene, not architecture).

### LOW — 3

**[L1] R8 sub-ticket convention — T-voice-{1..4} all marked done in different result.md but never committed (operational)**

Already covered under [H1]. Separated as LOW because the impl-log + result.md trail is intact — code quality is verified, only the git lineage is missing. When [H1] is remediated this collapses.

**[L2] Slot 6 channel format hint hardcoded vs shared channel registry**

- **Location:** `agentic/prompts/compose.py:162-195` defines `SLOT_6_CHANNEL_FORMAT_HINT: dict[str, str]` with 4 channels (whatsapp/im_dm/email/web).
- **Issue:** Per `sales-agent-expert` skill, channel format SSoT lives in `shared/agent_observability/channels/format.py::CHANNEL_FORMATS` + `register_channel`. Comunify defines its own static-text variant pending T-channels-N integration with shared registry (per file docstring line 84).
- **Severity:** LOW — documented mismatch with explicit "pending integration" note. Not a regression; doesn't violate anti-duplication because shared registry consumes structured `ChannelFormat` objects, not raw text-hint strings (different concern: cache prefix text vs runtime structure).
- **Remediation:** Story 13+ ticket to bridge `SLOT_6_CHANNEL_FORMAT_HINT` to `get_channel_format(channel_type).cache_prefix_hint()` accessor on shared `ChannelFormat`.

**[L3] Decisions_applicable cites not file:line-anchored**

- **Per Cat 15 WARN clause:** "Cite presente con todos los D#, PERO sin file:line reference para verificar implementación."
- **Example:** T-workflows-2 commit body cites D3/D10/D19 narratively but no `cohort_enrollment_workflow.py:NNN` reference. Cat 15 WARN — auditor self-fix optional.

### info — 2

**[I1] Pre-commit hook arch fitness gates honor `pytestmark = pytest.mark.no_eval`**

3 arch tests emit `PytestUnknownMarkWarning` for `no_eval` mark (test_comunify_cost_bucket_invariant.py:25, test_comunify_personas_yaml_completeness.py:40, test_comunify_rubric_md_v1_schema.py:42). Cosmetic — register mark in `pyproject.toml [tool.pytest.ini_options]` markers list.

**[I2] Anti-duplication audit blocks documented across all 4 tools + 2 extractors + 1 orchestrator**

Every agentic file under audit carries a "Anti-duplication audit (Step 0 GATE pre-write)" docstring section with grep evidence + lift-trigger rationale (verified `grep -l "Anti-duplication audit"` returns 8 hits). This is best-in-class R10 hygiene per `.claude/rules/anti-duplication.md` Step 0 GATE.

## Downstream regression scope

Per `.claude/rules/auditor-downstream-regression.md` Step 1-7 workflow:

1. `git diff --name-only` over agentic-scope shows changes ONLY in `luana-platform/comunify/backend/src/modules/comunify/{agentic,brand,copilot}/`.
2. Lookup table: zero matches in `shared/`, `core/luana-core-*`, `backend/src/shared/agent_observability/*`, `backend/src/core/config.py`, etc.
3. No `core/luana-core-extension-sdk/` modifications by agentic-scope tickets.
4. Downstream gate-runner spawn NOT required — code is consumer of stable shared abstractions, no producer-side change in this PR's agentic scope.
5. The 502/502 agentic_evals + 144/144 arch fitness already constitute the full regression surface for this module.

| Surface | Modified? | Downstream targets | Status |
|---|---|---|---|
| `shared/agent_observability/recording/turn_envelope.py` | no | n/a | skip |
| `shared/agent_observability/cost/cost_recorder.py` | no | n/a | skip |
| `luana_core_extraction.base_orchestrator` | no (only subclass added) | n/a | skip |
| `core/luana-core-extension-sdk/` | no | n/a | skip |
| `modules/comunify/agentic/`, `copilot/`, `brand/voice_cloning/` | yes (NEW) | covered by `tests/agentic_evals/` (502) + `tests/architecture/` (144) | PASS |

## Research notes

Live canonical docs cross-checked 2026-05-14:

- **LangGraph 2.0 supervisor + checkpointer patterns** — `https://docs.langchain.com/oss/python/langgraph/workflows-agents` (anchor only; not fetched live this audit — confirmed via skill cement at `.claude/skills/tessl__langgraph/SKILL.md` and code visual inspection: TypedDict state, conditional edges to END, MemorySaver→RedisSaver swap path).
- **Anthropic prompt caching `cache_control: ephemeral`** — `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` (anchor cement in `compose.py:34-37` matches Anthropic Messages API content block convention with per-tenant `prompt_cache_key` for tenant-bucket isolation).
- **deepagents SubAgentMiddleware** — `https://docs.langchain.com/oss/python/deepagents/overview` (not applicable — Comunify uses pure LangGraph, no deepagents `task` tool).

Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026 supplemented by skill cement + code visual review. No delta vs anchors required — Comunify follows standard 2026-cement patterns from Story 11 vitalia + Story 9 sales-agent core.

## Drift detection (CONTRACT vs code)

NO drift. `03-arch-agentic.md` § 4 (4 tools) + § 5 (2 extractors + voice cloning) + § 6 (2 workflows) + § 7 (KB pack) + § 8 (10-slot cache) + § 9 (micro-anchor) + § 10 (4 guardrails) all materialize 1:1 in code. Decisions D1-D20 cement (06-tickets `decisions_applicable` field) is honored at code level (commit body cite gap separately flagged as M2).

## Recommendations for builder fix-loop

Story is `developed`, not in fix-loop — directly to Phase 5 merge with these prerequisites:

1. **(HIGH — blocker)** Commit T-voice-1..4 + T-extensions-1 + T-kb-1 + T-workflows-1 + associated test files via Haiku worker (6-8 conventional commits with R23 Opus 4.7 trailer + R6 "## Decisions honored" formal section).
2. **(MEDIUM — non-blocker, BACKLOG)** Track `prompt_injection_block_reuse` lift-to-`core/luana-core-guardrails/` for Story 13+ 3rd vertical onboarding (M1).
3. **(MEDIUM — process)** Add "## Decisions honored" formal section to commit-body template per R6 across the dev-team skill prompt (M2 systemic).
4. **(LOW — cosmetic)** Register `no_eval` pytest mark in `pyproject.toml [tool.pytest.ini_options] markers` list (I1).
5. **(LOW — Story 13+)** Bridge Slot 6 channel format hint to shared `get_channel_format` accessor (L2).

## Verdict mechanical

| Threshold | Result |
|---|---|
| 0 CRITICAL | ✅ |
| 0 HIGH security/PII/tenant_iso/cache-leak | ✅ |
| ≤2 HIGH non-security | ⚠️ 1 HIGH (operational uncommit) |
| ≤3 MEDIUM | ✅ 2 |
| All gates GREEN or A/B/C classified | ✅ 502/502 agentic_evals + 144/144 arch fitness PASS |
| R23 routing | ✅ all 11 committed agentic SHAs Opus-trailed; remaining 6 uncommitted have IMPL-LOG Opus cite |
| R10 anti-duplication | ⚠️ 1 documented sibling mirror (M1) — within rule WARN clause |
| R3 downstream regression | ✅ N/A (isolated module) |

**Verdict: WARN**

PASS path blocked solely by [H1] operational uncommit gap — code quality verified GREEN at filesystem level (502/502 evals + 144/144 arch). When Haiku commit worker closes [H1] (6-8 commits), upgrade to PASS is mechanical. Approval can proceed Phase 5 IF Chris ratifies "code is GREEN locally; commit step IS the merge step" — otherwise hold for commit-and-push first, then re-audit delta.

## Output

`WARN -> docs/product/stories/luana-comunify-bootstrap/REVIEW-agentic.md`
