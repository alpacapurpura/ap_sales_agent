# CHECKPOINTS — sales-agent-personas-instrumented-runtime (Story C)

**Date:** 2026-05-08
**Story:** sales-agent-personas-instrumented-runtime (Story C of outcome pi-12-sales-agent-eval-foundation)
**Tickets audited:** T-1 … T-9 (9 tickets across AGENTIC + BE + DOCS surfaces)
**Sub-auditors:** auditor-agentic (T-1, T-3, T-4, T-5, T-6, T-7, T-8) · auditor-backend (T-2 + T-9)
**Surface verdicts:**
- AGENTIC → **PASS** (2 non-blocking WARN: Cat 15 decisions cite + Cat 1 informational)
- BE + DOCS → **PASS** (1 non-blocking WARN: R6 decisions cite block missing in commits)

**Verdict:** **APPROVED**

## Audit method

2 sub-auditors paralelos (AGENTIC + BE+DOCS). Per-surface REVIEW-{agentic,be-docs}.md plus this CHECKPOINTS.md story-level grid. Approach matches Story 2B pattern — coherent test-infrastructure refactor, single-pass per surface for cost efficiency.

## Gate Status (gate-output.json iter-1)

| Surface | Gate | Result |
|---|---|---|
| BE | ruff check (test-infra scope) | PASS (0 errors) |
| BE | ruff format --check | PASS |
| BE | mypy strict (test-infra) | PASS |
| BE | pytest tests/architecture/ | PASS (980 tests) |
| BE+AGENTIC | pytest sales_agent/copilot/shared `-m "not integration"` | PASS (3492 tests + 29 SKIP-with-escalation) |

iter-1 clean — no env-only failures (postgres not consumed by Story C tests since synthetic data + non-integration scope).

## C1-C5 grid

| Checkpoint | Scope | Evidence | Verdict |
|---|---|---|---|
| **C1: Code** | AGENTIC + BE + DOCS; 9 tickets pushed; ruff/format/mypy strict GREEN; PersonalityProfile.system_instruction SSoT untouched; H9 surface frozen 7 names; H10 frozen golden v1 byte-equal; H6 cost-bucket separation; arch fitness +1 NEW gate (test_personas_yaml_completeness) | tsc N/A · ruff 0 errors ✓ · mypy strict ✓ · 980 arch fitness PASS ✓ · Story B 6 invariants preserved ✓ | **APPROVED** |
| **C2: Spec** | 4 Gherkin scenarios (Scenarios 4/5/6 + happy/negative/edge/adversarial) + 17 ADs D1-D17 + 10 D-AG-* + 5 D-BE-*; 21 validators 4 categories | scenario_4 (T-8 adversarial) PASS · scenario_5 (T-6) cement + SKIP-with-escalation · scenario_6 (T-7) cement + SKIP-with-escalation · 17 ADs implementados (T-{4,5} commit-body cite WARN — substance present in result.md "Decisions / cement" sections) | **APPROVED** |
| **C3: Architecture** | Test-infrastructure under backend/tests/agentic_evals/sales_agent/simulator/_internal/; ActorProfile schema v1→v2; SCHEMA_MIGRATIONS registry extension; Customer Prompt V2 additive; customer_node V1/V2 dispatch; eval_metadata 3 NEW keys; cross-module audit anti-duplication.md (personas_loader.py NEW per architect grep — no precedent) | Story B EXTEND not mirror ✓ · personas_loader genuinely NEW ✓ · ActorProfile EXTEND ✓ · CustomerPrompt V2 ADDITIVE ✓ · customer_node EXTEND ✓ · 4 NEW downstream regression rows tabla SSoT (commit 415db986) | **APPROVED** |
| **C4: Cross-cutting** | Spanish neutro (3 AR YAMLs voseo magic comment line 2; 12 non-AR neutro tuteo); R23 enforcement (7 AGENTIC commits Opus 4.7); cache prefix safety V2 (NO {tenant_name}); brand-voice compliance; PII (synthetic only — no PII risk) | 0 voseo violations non-AR ✓ · 3 AR magic comment R25-compliant ✓ · 7 AGENTIC commits Opus 4.7 ✓ · cache safety V2 PASS ✓ · 1 WARN R6 (commit body decisions cite missing — non-blocking, substance present in result.md) | **APPROVED** |
| **C5: Trace** | All 9 commits SHAs documented; transitions per ticket; validator_ids cited; T-6/T-7 SKIP-with-escalation legitimately documented (qualify_lead/tag_lead_status missing in TOOL_REGISTRY = real dep); R3 downstream regression 4 NEW rows added | T-1 34f0ce69 · T-2 b92b5871 · T-3 cbd98b76 · T-4 4fb355b7 · T-5 ed671c99 · T-6 0fbe5121 · T-7 c705695d · T-8 c7873887 · T-9 415db986 · all transitions in 06-tickets.yaml ✓ · downstream regression 4 NEW rows ✓ | **APPROVED** |

## Findings

### AGENTIC — WARN (Cat 15 R6) non-blocking
**File:** commits 4fb355b7 (T-4) + ed671c99 (T-5)
**Issue:** Commit bodies lack explicit "Decisions: D17, D-AG-4" enumeration. Substance present in T-{4,5}-result.md "Decisions / cement" sections.
**Status:** R6 process improvement — apply strictly on subsequent stories.
**Fix:** Not blocking. Auditor-agentic confirmed implementation honors decisions.

### BE+DOCS — WARN (R6) non-blocking
**File:** commits b92b5871 (T-2) + 415db986 (T-9)
**Issue:** R6 "Decisions honored" cite block missing in commit bodies. D14, D2, D-BE-1..5 honored implementation-side, just not cited verbatim.
**Status:** Below WARN-count threshold for overall WARN. Mergeable.
**Fix:** Same as above — apply R6 strictly going forward.

### Open escalation `/pm` (informational, not auditor finding)
T-6 + T-7 SKIP-with-escalation: `qualify_lead` + `tag_lead_status` tools missing in `TOOL_REGISTRY`. Test cement is in place — transitions GREEN automatically once toolkit lands. PM decision pending:
- (A) Spawn separate `sales-agent-qualification-toolkit` story
- (B) Accept Story C closure as-is — toolkit ships in another PI-12 story

## Allowlist Movement

- BE arch fitness: 979 → 980 (+1 NEW test `test_personas_yaml_completeness.py`)
- KNOWN_VIOLATIONS_PERSONAS_YAML: empty (new arch gate, zero allowlist)
- Story B 6 arch fitness gates STILL GREEN (H9/H10/H6 + simulator gates)

## Native-First Audit

- ✓ All commits use `cd backend && .venv/bin/{ruff,pytest,mypy}` native WSL
- ✓ No `docker exec ... pytest` invocations
- ✓ No `make e2e*` (N/A — Story C is BE+agentic, no FE)
- ✓ No `git add .` / `-A` / `-u` (parallel-safety)
- ✓ Conventional commits format (lacking R6 cite — see WARN)

## Cross-cutting Compliance

- ✓ Spanish neutro: 3 AR YAMLs voseo magic comment línea 2 R25-compliant; 12 non-AR es-MX/CO/PE/419 neutro tuteo
- ✓ R23 enforcement: 7 AGENTIC commits authored Opus 4.7 (verified Co-Authored-By footer)
- ✓ Cache prefix safety: V2 customer prompt zero `{tenant_name}` interpolation (test_v2_no_tenant_name_interpolation PASS)
- ✓ Story B H9 7 names frozen + H10 frozen golden v1 byte-equal + H6 cost-bucket separation
- ✓ Anti-duplication: 4 NEW downstream regression rows added to .claude/rules/auditor-downstream-regression.md tabla SSoT (commit 415db986)
- ✓ Tessl skills consulted: sales-agent-expert + copilot-expert + tessl__langgraph + tessl__graceful-degradation + tessl__pytest-api-testing + claude-api

## Verdict Math

- 0 FAIL across AGENTIC + BE + DOCS surfaces
- 2 AGENTIC WARN (Cat 15 R6 + Cat 1 informational) — non-blocking
- 1 BE WARN (R6 commit body cite) — non-blocking, below WARN threshold
- R23 enforcement confirmed (7 Opus 4.7 commits)
- R3 downstream regression CLEAN (gate-runner full suite GREEN)
- T-6/T-7 SKIP escalation legitimate + documented + transitions GREEN auto when toolkit lands

→ **VERDICT: APPROVED**

## Closing recommendations for `/pm` at merge

1. **Capability impact** — Story C extends existing `sales-conversational-engine.yaml` with Story C eval block (10 NEW fields). NO new capability promoted (extension only).
2. **Module SSoT refresh** — `modules/sales-agent.md` already updated by T-9 (Personas-as-simulators row added).
3. **Outcome story_ids** — pi-12-sales-agent-eval-foundation.md mark Story C done.
4. **learnings.md** — append entry: "Process WARN R6 (decisions cite missing in commit bodies) recurrent — subsequent stories enforce strictly. Substance was present in result.md sections, but commit body trace was incomplete."
5. **T-6/T-7 escalation decision pending Chris:** Option A (spawn qualification-toolkit story) vs Option B (accept closure, toolkit ships elsewhere PI-12).

## Deferred follow-ups

- Apply R6 commit-body decisions cite block on Story D + future PI-12 stories
- T-6/T-7 SKIP transitions auto-GREEN when toolkit lands — track in `qualify_lead`/`tag_lead_status` story
- Story E (voice-fidelity-grader-runtime) consumes qualification-accuracy.md placeholder created in T-9
