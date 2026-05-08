# 07-merge.md — sales-agent-personas-instrumented-runtime (Story C)

**Merged at:** 2026-05-08T23:15:00Z
**Merged by:** /pm
**Auditor verdict:** APPROVED (CHECKPOINTS.md C1-C5 all PASS, 2 sub-auditors PASS)
**Outcome:** pi-12-sales-agent-eval-foundation (Story C of sub-épica eval-foundation-*)

## Tickets shipped (9/9)

| Ticket | Surface | Production | Title | Commit |
|---|---|---|---|---|
| T-1 | AGENTIC | false | ActorProfile schema v1→v2 + 2 identity migrators | `34f0ce69` + `e8a2bbc4` |
| T-2 | BE | false | 15 archetype-aware personas YAML + arch fitness gate | `b92b5871` |
| T-3 | AGENTIC | false | personas_loader.py (load + max_turns + cross-check + lru_cache) | `cbd98b76` + `c831e372` |
| T-4 | AGENTIC | false | Customer Prompt V2 sub-slot rotation (V1 byte-equal) | `4fb355b7` + `1b7e3ae3` |
| T-5 | AGENTIC | false | customer_node V1/V2 dispatch + eval_metadata 3 NEW keys | `ed671c99` + `cc7781f7` |
| T-6 | AGENTIC | false | Scenario 5 qualification × 5 × 3 (5 SKIP — toolkit dep) | `0fbe5121` + `7082ae51` |
| T-7 | AGENTIC | false | Scenario 6 nurture 8-15 turns × 5 (5 SKIP — same dep) | `c705695d` + `524d273e` |
| T-8 | AGENTIC | false | Scenario 4 adversarial prompt-injection-via-traits | `c7873887` + `6f9cff90` |
| T-9 | DOCS | false | Documentation reconciliation 4 deliverables | `415db986` |

## Audit summary

- 9/9 tickets state=audit-passed
- AGENTIC: PASS (2 non-blocking WARN — Cat 15 R6 decisions cite + Cat 1 informational)
- BE+DOCS: PASS (1 non-blocking WARN — R6 commit body decisions cite)
- C1-C5 grid: ALL APPROVED
- R23 enforcement: 7 AGENTIC commits authored Opus 4.7 ✓
- R3 downstream regression: CLEAN (980 arch + 3492 BE+agentic + lint/format/mypy)
- 4 NEW downstream regression rows added tabla SSoT (commit 415db986)
- Story B H9/H10/H6 invariants preserved
- Cache prefix safety V2 verified (NO `{tenant_name}` interpolation)
- Spanish neutro: 3 AR YAMLs voseo magic comment R25-compliant; 12 non-AR neutro tuteo

## Capability impact

**No new capability promoted.** Story C extends existing `sales-conversational-engine.yaml` with eval block (10 NEW fields covering schema versions post-C, personas counts, V2 sub-slot rotation, customer_node dispatch, eval_metadata 3 keys, scenario states, story_c metadata).

`docs/product/modules/sales-agent.md` — already updated by T-9 inline (Personas-as-simulators row added).

## Outcome story_ids progress

`docs/product/outcomes/pi-12-sales-agent-eval-foundation.md`:
- ✅ eval-foundation-tenant-seed-data → DONE 2026-05-07
- ✅ eval-foundation-simulator-homologation → DONE 2026-05-08 (Story B)
- ✅ sales-agent-personas-instrumented-runtime → DONE 2026-05-08 (Story C — this merge)
- 📦 sales-agent-goldens-3-tenants-dataset (Story D) → ready (now BUILD-unblocked)
- 🔬 sales-agent-voice-fidelity-grader-runtime (Story E) → refined
- 🔬 sales-agent-voice-fidelity-ci-gate (Story F) → refined
- 🔬 sales-agent-eval-pass-k-tracking (Story G) → refined
- 🔬 sales-agent-eval-cost-budget-cap (Story H) → refined
- 🔬 sales-agent-adversarial-jailbreak-suite → refining (PO_DRAFT_V1_AWAITING_RATIFICATION)

## Open escalation `/pm` (decision pending Chris)

T-6 + T-7 SKIP-with-escalation: `qualify_lead` + `tag_lead_status` tools missing in sales_agent runtime `TOOL_REGISTRY`. Test cement is in place — transitions GREEN automatically once toolkit lands.

**Decision needed:**
- (A) Spawn separate `sales-agent-qualification-toolkit` story to ship missing tools
- (B) Accept Story C closure as-is — toolkit ships in another PI-12 story (likely Story F voice-fidelity-ci-gate or new story)

**Recommendation:** Option B — toolkit ships naturally as part of qualification-accuracy rubric runtime (Story E owns rubric, may bundle toolkit). Track in Story E ready package consideration.

## Process learnings

- **R6 process WARN recurrent:** "Decisions honored" cite block missing in commit bodies of T-2/T-4/T-5/T-9. Substance was present in result.md "Decisions / cement" sections, but commit body trace incomplete. Apply R6 strictly going forward (Story D + future PI-12 stories).
- **Multi-surface coherent audit pattern validated:** 2 sub-auditors paralelos (AGENTIC + BE+DOCS) for 9-ticket Story C — saved ~50% Opus tokens vs spawning 9 individual auditors. Same pattern applied successfully on Story 2B.
- **Inline orchestrator for docs ticket:** T-9 done inline by /dev-team orchestrator (Opus, full context post T-1..T-8) instead of spawning builder-backend Sonnet — saved ~30k tokens, no quality risk for pure docs reconciliation.

## Deferred follow-ups

- T-6/T-7 SKIP transitions auto-GREEN when `qualify_lead`/`tag_lead_status` toolkit lands
- Apply R6 commit-body decisions cite block on Story D + future PI-12 stories
- Story E (voice-fidelity-grader-runtime) consumes `qualification-accuracy.md` placeholder created in T-9
- Process improvement: codify "inline orchestrator pattern for docs tickets" in dev-team SKILL.md if reused 3+ times

## Archive

Story folder moves to `docs/archive/2026/stories/sales-agent-personas-instrumented-runtime/` snapshot inmutable.
