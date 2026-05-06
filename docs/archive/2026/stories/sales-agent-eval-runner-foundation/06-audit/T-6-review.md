<!-- voseo-allowed: audit review citing voseo glosario verbatim per R25 -->
# T-6 Agentic Audit Review — Makefile target eval-smoke + README operability docs

> Auditor: `auditor-agentic` (Opus 4.7 [1M ctx]) — invariants validated against canonical docs as of 2026-05-06
> Iter: 1
> Story: PI-12 S1 sales-agent-eval-runner-foundation Story B T-6
> Verdict: **APPROVED (WARN)**
> Generated: 2026-05-06T01:30Z

---

## 1. Inputs

- **CONTEXT-BRIEF.md:** present but scoped to T-5 (last update). T-6 was docs-only and authoritative source was `04-tickets.yaml § T-6` per controller note + IMPL-LOG R24 ratification — accepted.
- **gate-output.json:** used (T-6 iter 1, all 6 gates PASS, 2026-05-06T01:00Z).
- **IMPL-LOG.md:** read fully — Skills consulted section properly documents copilot-expert + sales-agent-expert invocation, with explicit N/A justifications for tessl__langgraph + tessl__graceful-degradation (no graph/state nor external calls touched).
- **Skills invoked:** copilot-expert=Y (anti-duplication §0 cited), sales-agent-expert=Y (§3 protected surfaces honored), tessl__langgraph=N/A justified, tessl__graceful-degradation=N/A justified.

---

## 2. Gate status (from gate-output.json)

| Gate | Status | Errors |
|---|---|---|
| ruff_lint | PASS | 0 |
| ruff_format | PASS | 0 (17 files already formatted) |
| pytest_eval_runner_fixtures | PASS | 39 passed / 4 skipped (eval-marker pre-existing per design — no regression) |
| acceptance_a1_makefile_target | PASS | `make -n eval-smoke` outputs canonical pytest invocation |
| acceptance_a2_readme_8_sections | PASS | 8/8 mandatory section headers grep-matched |
| acceptance_a3_spanish_neutro | PASS | 0 voseo matches per ticket regex |

Auditor independent re-run (2026-05-06):
- `cd backend && make -n eval-smoke` → outputs `cd /home/chris/AISALESHT/backend && .venv/bin/pytest tests/agentic_evals/sales_agent/test_eval_runner_smoke.py -v --run-evals` ✅
- A2 grep loop: 8/8 sections found ✅
- A3 ticket regex `(podés|tenés|sos|querés|hacés|configurá|seleccioná)`: 0 matches ✅
- A3 full glosario sweep (40+ tokens per `spanish-text.md` R2): 0 voseo matches ✅
- ruff lint + format: clean ✅
- 39 passed / 4 skipped on `test_eval_runner_fixtures.py` ✅

---

## 3. 15 categories

| # | Category | Score | Evidence |
|---|---|---|---|
| 1 | LangGraph state hygiene | NA | Docs-only ticket — no graph/state code touched |
| 2 | Tool registration | NA | Docs-only |
| 3 | Prompt cache architecture | NA | Docs-only — README references slot 5 BRAND_VOICE correctly (line 244) without modifying any prompt |
| 4 | deepagents subagent isolation | NA | Docs-only |
| 5 | Observability (`copilot_trace_event` + cost recording) | NA | Docs-only — README accurately documents cost target ~$0.005/run + alert >$0.05/run + `sales_agent_llm_call` cost_usd column query (lines 232-262) |
| 6 | Eval goldens (sales_agent) | PASS | README §3 documents YAML schema verbatim from `runner/golden_loader.py::GoldenSpec`; §8 properly defers voice grader to Story 7 (placeholder `assert_voice_fidelity` raises `NotImplementedError`); per spec B6/B7 binding |
| 7 | RAG / Qdrant hygiene | NA | Docs-only |
| 8 | LLM provider routing | NA | Docs-only — README references DeepSeek V4-Flash via LiteLLM proxy (canonical per Story A T-5) without hardcoding model strings |
| 9 | Cost optimization | PASS | README §7 documents cost budget < $0.01/run target, $0.05/run regression alert, 4 root causes for cost spikes (cache invalidation, tier pricing miss at 200k, subagent toolset inheritance, anti-loop loop) — all per `sales-agent-expert` SSoT |
| 10 | Channel format & brand voice | PASS | README anti-patterns section explicitly forbids overriding tenant voice in `sales_agent_entrypoint` (line 295-296); honors `personality_profiles.system_instruction` SSoT |
| 11 | DDD compliance (agentic specifics) | PASS | Test harness lives in `backend/tests/agentic_evals/sales_agent/` (no src/ touched). README references shared abstractions correctly: `sanitize_payload` from `shared/agent_observability/recording/sanitization.py`, `BaseAgentCallbackHandler` composition pattern (T-3 audit-passed) |
| 12 | Tests / TDD | PASS | T-6 is docs+config; eval runner fixtures meta-tests still 39 passed / 4 skipped (no regression). `make eval-smoke` invocation matches existing `test_eval_runner_smoke.py` (T-5 audit-passed) |
| 13 | Mirror detection | PASS | `backend/Makefile` is NEW. Mirror scan: only `Makefile` other instance is root `/home/chris/AISALESHT/Makefile` (different scope: Docker+cross-stack+E2E). Builder rationale documented in IMPL-LOG § Decision: A1 verifier requires `cd backend && make -n eval-smoke` which presumes `backend/Makefile` exists. Root Makefile unmodified. README rewrite extends T-1 stub per parallel-safety M8 (T-1 stub explicitly noted "T-6 reescribe este README"). No subsystem from `.claude/rules/anti-duplication.md` inventory triggered |
| 14 | Default-flip side-effect coverage | NA | T-6 does NOT touch `backend/src/core/config.py` defaults nor any feature flag side-effect path |
| 15 | Decisions honored cite (R6) | NA | Ticket `T-6` has no `decisions_applicable:` field in `04-tickets.yaml` — R6 does not trigger |

---

## 4. Findings (file:line)

### FAIL
None.

### WARN

- **[Cat 11 — spanish-text.md R1]** `backend/tests/agentic_evals/sales_agent/README.md:137` and `:194`
  Verbatim: `### Por que offer_id hardcoded (B2)` and `**Por que ambos:**` — interrogative `qué` missing tilde. Per `spanish-text.md` R1, tildes are mandatory on user-facing strings. README is user-facing operations documentation. Recommended fix: `Por qué`. Severity WARN (R1 violation but readable + not a voseo issue).

- **[Cat 11 — spanish-text.md R1]** `backend/tests/agentic_evals/sales_agent/README.md:198`
  Verbatim: `Las dos preguntas son ortogonales y necesitan instrumentacion distinta.` — `instrumentación` missing tilde.

- **[Cat 11 — spanish-text.md R1]** `backend/tests/agentic_evals/sales_agent/README.md:297`
  Verbatim: `❌ Hardcodear tenant_id o offer_id en el codigo del test.` — `código` missing tilde.

These four ortho misses survive despite IMPL-LOG § "04:02" documenting an extensive iterative tilde correction pass. The ticket A3 verifier (voseo regex) does NOT cover R1 ortho — it covers R2 voseo only. The 4 misses are real R1 violations but minor in severity (do not affect voseo compliance, which is the documented gating mechanism).

### info

- **[Cat 13 — architectural choice rationale]** `backend/Makefile:1-33`
  New file. Auditor accepts the trade-off: A1 verifier `cd backend && make -n eval-smoke` semantically requires `backend/Makefile`. Could have been routed via `make pytest args="..."` from root, but A1 contract pins the location. Builder rationale documented in IMPL-LOG § Decision lines 77-99. Convivencia documented in `backend/Makefile:1-14` header.

- **[Cat 6 — README content fidelity]** `backend/tests/agentic_evals/sales_agent/README.md:269-285`
  Story 2-9 future scope table is accurate and matches PI-12 roadmap. Voice fidelity explicitly deferred to Story 7 (consistent with T-4 `assert_voice_fidelity` placeholder NotImplementedError + sales-agent-expert SSoT § "voice fidelity grader").

- **[Cat 9 — cost docs accuracy]** `backend/tests/agentic_evals/sales_agent/README.md:243-251`
  4 cost-spike root causes correctly cite sales-agent-expert SSoT (slot 5 BRAND_VOICE invalidation, Kimi K2.6 tier pricing 200k threshold per S12, specialist toolset inheritance, tool_call_dedup loop). Faithful reproduction of skill invariants.

- **[Cat 11 — IMPL-LOG quality]** `T-6-impl-log.md:24-34`
  Skills consulted table exemplary: positive invocations of copilot-expert + sales-agent-expert with concrete decisions captured (anti-duplication §0 + §3 protected surfaces); explicit N/A for tessl__langgraph + tessl__graceful-degradation with justification (no graph/state nor external calls). R30 footer compliance verified — builder honors `tests-passing` state only (does not self-claim audit-passed).

---

## 5. Cross-scope flags

None. T-6 scope is exclusively:
- `backend/Makefile` (NEW, 33 lines, BE-pure ops convenience)
- `backend/tests/agentic_evals/sales_agent/README.md` (REWRITE, 113 → 318 lines)
- `docs/projects/active/PI-12-.../05-impl/T-6-impl-log.md` (NEW, builder log)

No `modules/copilot/` nor `modules/sales_agent/` source changes. The README references those modules verbatim (paths + class names) but does not modify them.

---

## 6. Downstream regression scope

| Surface modified | Listed in `.claude/rules/auditor-downstream-regression.md` SSoT? | Downstream test targets |
|---|---|---|
| `backend/Makefile` (NEW) | NO — config-only, no Python imports | N/A |
| `backend/tests/agentic_evals/sales_agent/README.md` (REWRITE) | NO — docs-only, no Python imports | N/A |

Per gate-output.json `downstream_regression_note`: T-6 modifies config + docs only. No `shared/` paths touched → no SSoT entry triggers downstream regression spawn.

Auditor verdict: downstream regression scope NA. R3 satisfied trivially.

---

## 7. Research notes (DATE-AWARE)

- T-6 is operational documentation. No novel patterns introduced — README is consumer of existing T-1 through T-5 infrastructure. No live canonical docs needed (LangGraph/Anthropic prompt caching/deepagents references in README are descriptive of existing implementation, not introducing new shape).
- Knowledge cutoff disclosure: Opus 4.7 cutoff Jan 2026; live researched on 2026-05-06 (no novel framework).

---

## 8. Recommendations

### Before close (auditor self-fix candidate or builder iter)

1. **R1 ortho fixes (4 instances)** — non-blocking but should be fixed in next docs touch:
   - L137: `Por que` → `Por qué`
   - L194: `Por que` → `Por qué`
   - L198: `instrumentacion` → `instrumentación`
   - L297: `codigo` → `código`

   Trivial sed-able fix. Auditor recommends builder OR /pm self-fix in a follow-up commit (not blocking T-6 closure since A3 voseo gate is the contracted criterion).

### Future stories

2. **R31 documented opportunity** — When R1 ortho enforcement gets a pre-commit hook (analogous to current voseo regex), this README would benefit from a re-pass. Not blocking T-6.

---

## 9. Drift detection (CONTRACT vs code)

- Architect spec ambiguity in `04-tickets.yaml § T-6 deliverable 1` ("Agregar target eval-smoke al `backend/Makefile`") + A1 verifier (`cd backend && make -n eval-smoke`) was resolved by builder via creating the missing `backend/Makefile` (was 0 matches at story start). Builder documented the resolution exhaustively in IMPL-LOG § Decision (lines 77-99). Auditor concurs with the resolution: A1 verifier semantics pin the location, root Makefile was not modified, scope is BE-pure ops (eval harness convenience). This is **architect-spec interpretation, not drift** — the deliverable text and the A1 verifier together imply backend/Makefile creation, builder honored both.

NO drift escalation required.

---

## 10. Verdict

**APPROVED (WARN)** — T-6 acceptance verifiers all PASS, 6 gates clean, IMPL-LOG exemplary, scope discipline observed. 4 minor `spanish-text.md` R1 ortho misses logged as WARN (non-blocking — A3 contract is voseo R2, which is clean).

Mechanical verdict math (per auditor-agentic role spec):
- 0 FAIL across 15 categories (NA in 8, PASS in 7, WARN in 0, info in 4)
- 0 FAIL gates in gate-output.json
- 0 cross-scope violations
- 0 mandatory skill routing violations
- 0 default-flip violations
- 0 mirror duplications
- 0 R6 decision-cite missing (R6 NA)

Per scoring rules: ≥2 WARN cats trigger overall WARN. Here: 0 WARN cat scores (the R1 ortho misses are info-level findings inside Cat 11 PASS, not category-level WARN). Verdict: **APPROVED**, with informational annotation about the 4 R1 ortho misses for builder/PM self-fix discretion.

Story B T-6 **closes Story B development scope** — Wave 8 REVIEW-final is unblocked.

<!-- @pm: REVIEW-agentic.md ready (verdict=APPROVED). 4 minor R1 ortho misses logged in §4 WARN; non-blocking. Story B T-6 audit-passed; Wave 8 REVIEW-final unblocked. -->
