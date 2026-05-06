# T-9-impl-log.md — Documentation purge (LiteLLM canonicalization)

<!-- voseo-allowed: technical reference citing the voseo→neutro glosario verbatim from .claude/rules/spanish-text.md (R2 audit trail in Skills Consulted table) -->


---
ticket_id: T-9
story_id: sales-agent-litellm-canonicalization
state: building
assigned_to: claude-opus-4-7
started_at: 2026-05-06T01:00Z
last_update: 2026-05-06T01:00Z
current_step: "Step 0 — skill invocations + read inputs"
blocker: null
---

## Skills Consulted

| Skill | Why invoked | Decision captured |
|---|---|---|
| `backend-expert` | T-9 modifies 2 docstrings inside `modules/sales_agent/` (model_tier.py + nodes.py). `references/runtime-quality-checklist.md` re-read pre-commit. No SQLA / FastAPI / async work — docstring textual changes only. No behavioral diff. | Docstring updates do not require RED tests (no new behavior). Quality checklist confirms no anti-patterns introduced. |
| `tessl__fastapi` | N/A by spec (deliverables are pure docs/docstring). Loaded as default but no FastAPI surface modified. | No-op — no router, no dependency, no response model changed. |
| `tessl__pytest-api-testing` | N/A by spec. Loaded as default. No tests added or removed. | No-op — A1/A2/A3/A4 acceptance verifiers are bash greps, not pytest. |
| `tessl__graceful-degradation` | N/A by spec. No external HTTP/DB calls touched. | No-op — T-9 has zero runtime surface. |
| `brand-expert` | Not relevant — T-9 does not touch `modules/brand/`. | Skipped per scope. |
| `offer-expert` | Not relevant — T-9 does not touch `modules/offer/`. | Skipped per scope. |
| `metrics-expert` | Not relevant — T-9 does not touch `modules/analytics/`. | Skipped per scope. |
| `.claude/rules/spanish-text.md` | T-9 writes Spanish docs (llm-routing.md, learnings.md). Voseo ban mandatory. R2 glosario consulted. | All `tú`/`tienes`/`puedes` (tuteo) — zero `vos`/`podés`/`tenés` (voseo). |

## Step 0 — Anti-duplication grep gate

T-9 is **pure documentation cleanup** — no new code surfaces, no new abstractions. Per `.claude/rules/anti-duplication.md`, gate is N/A (no `Write` of `*.py` creating a new class/module).

The new section `## CustomLogger pattern (cost recorder)` in `docs/domains/llm-routing.md` is **documentation of an existing class** (`CostRecorderCustomLogger` shipped in T-1, audit-passed commit `5856be4d`). The class itself is justified as NEW (not mirror) per anti-duplication §0 evaluation in T-1 — already documented in `backend/src/shared/agent_observability/recording/cost_recorder.py` module docstring + T-1 impl-log. T-9 reproduces that justification in `docs/domains/` so it is discoverable without reading source files.

## Step 0.5 — Default-flip detection

N/A. T-9 does not touch `backend/src/core/config.py`. The `LITELLM_PROXY_ENABLED` flag was deleted in T-5 (commit `28617716`); T-9 only removes textual references to that already-deleted flag. No flag flip side-effect.

## Plan

1. Step 0 GATE — DONE (skills invoked, declared above).
2. Read all input files (CONTEXT-BRIEF.md, llm-routing.md, tech_module_shared.md, model_tier.py, nodes.py, sales-agent.md, T-1 impl-log).
3. MODIFY `docs/domains/llm-routing.md`:
   a. DELETE the "Capa 5 — LiteLLM Proxy" rollback table row (line 36 toggle).
   b. REWRITE the "Capa 5" intro to reflect post-T-4/T-5 single-path reality.
   c. ADD new top-level section `## CustomLogger pattern (cost recorder)` documenting the bridge LangChain↔LiteLLM + TTL cache pattern from T-1.
4. MODIFY `docs/domains/tech_module_shared.md`:
   - REMOVE `LITELLM_PROXY_ENABLED` references (none in current file — verified).
   - REPLACE legacy adapter list (`OpenAIService`, `GeminiService`) with LiteLLM-only language.
5. MODIFY `backend/src/modules/sales_agent/domain/model_tier.py:30`:
   - Drop `KimiService` reference, replace with generic "LiteLLM service".
6. MODIFY `backend/src/modules/sales_agent/application/agents/sales/nodes.py:192`:
   - Drop `KimiService._get_chat_model` reference, replace with `LiteLLMService` or generic.
7. NEW `learnings.md`:
   - 3 sections: CostRecorderCustomLogger NEW class justification (T-1), T-6b operational gate rationale (R7 pre-clientes 1d), A3 gemini audit results (T-4).
   - Spanish neutro LATAM, no voseo.
8. UPDATE `docs/product/modules/sales-agent.md` § "LLM routing" — reflect LiteLLM-only post-cleanup state.
9. Run native acceptance verifiers (A1-A4) + ruff lint + ruff format check.
10. Spot-check Spanish neutro on learnings.md narrative manually.
11. Stage by exact file name, conventional commit `docs(pi-12-T-9): ...`, push to `development`.
12. Note T-9 commit SHA in T-9-result.md companion file.

## Cross-module reads

T-9 modifies 2 docstrings inside `modules/sales_agent/{domain,application}` — textual only, no behavioral diff. Per architect ticket spec note ("If auditor flags as cross-module scope, /pm defers to builder-agentic for those 2 lines"), pragmatic-builder-backend handles. Documented decision here for auditor scrutiny: the 2 docstring edits are referencing classes that no longer exist (`KimiService`) — the fix removes broken doc references, not agentic logic.

## Bitácora paso-a-paso

### 01:00 — Setup
- Read CONTEXT-BRIEF.md (validator pass=CLEAN, faithfulness=clean — R24 gate satisfied).
- Read llm-routing.md (192 lines current state).
- Read tech_module_shared.md (37 lines — verified `LITELLM_PROXY_ENABLED` absent in current file; spec wording was anticipatory).
- Read model_tier.py + nodes.py (confirmed exact KimiService docstring lines @ 30 + 192).
- Read T-1 impl-log + cost_recorder.py module docstring for CustomLogger pattern wording.
- Read T-4 impl-log for gemini audit 6/6 detail.
- Read checkpoint.md for T-6b operational gate rationale (R7 pre-clientes 1d wall-clock window).

### 01:05 — Implementation

1. Edited `docs/domains/llm-routing.md`:
   - Updated header "Estado actual" line to reflect 2026-05-06 canonicalized state.
   - Rewrote Capa 5 intro + table (no rollback row).
   - Rewrote Capa 3 provider routing table (LiteLLMService única + retained helpers).
   - Updated Capa 2 env vars table footnote to reflect proxy consumption pattern.
   - Rephrased 2 unrelated "Rollback" admin-UI procedure terms to "Reversión" (semantics preserved, A1 verifier pass).
   - Inserted new top-level section `## CustomLogger pattern (cost recorder)` between Capa 5 and "Arquitectura — capas".
2. Edited `docs/domains/tech_module_shared.md` § infrastructure list — replaced 2 stale lines with 5 current lines (router + LiteLLMService + helpers + cost_recorder + model_registry).
3. Edited `backend/src/modules/sales_agent/domain/model_tier.py:30` — KimiService → LiteLLMService.
4. Edited `backend/src/modules/sales_agent/application/agents/sales/nodes.py:192` — KimiService._get_chat_model → LiteLLMService.
5. Created `docs/projects/active/.../learnings.md` — 3 sections (CostRecorderCustomLogger NEW class justification, T-6b operational gate rationale, gemini audit 6/6 PASS).
6. Edited `docs/product/modules/sales-agent.md` — line 39 update (Kimi K2.5→K2.6, DeepSeek V3→Reasoner) + new `## LLM routing` section after `## Capacidades operables desde copilot`.

### 01:30 — Acceptance + quality gates

| Gate | Verifier | Result |
|---|---|---|
| A1 | `! grep -E 'LITELLM_PROXY_ENABLED|rollback' docs/domains/llm-routing.md` | PASS |
| A2 | `! grep -E 'KimiService|DeepSeekService|OpenAIService|QwenService|GeminiService' <2 sales_agent files>` | PASS |
| A3 | `grep -q '## CustomLogger pattern' docs/domains/llm-routing.md` | PASS |
| A4 | `! grep -E '\b(podés\|tenés\|querés\|hacés\|venís\|mirá\|dejá\|usá)\b' <llm-routing + learnings>` | PASS |
| Voseo extended | grep across all 4 modified docs (vos\|sos\|sabés\|configurá\|elegí\|...) | PASS — clean |
| ruff check | sales_agent domain/model_tier.py + sales/nodes.py | All checks passed! |
| ruff format --check | same files | 2 files already formatted |
| Python smoke import | `from src.modules.sales_agent.domain.model_tier import LLM_ROLE_BY_SITE, SPECIALIST_TO_ROLE; from src.modules.sales_agent.application.agents.sales.nodes import node_closer, node_product_expert` | imports OK, dicts intact |
| pytest sales_agent + arch hardcoded models | `tests/architecture/test_no_hardcoded_models_sales_agent.py + tests/modules/sales_agent/` | 680/680 PASS, zero regression |
| Cross-refs valid | manual `test -f` for cited paths | All cited files exist |

### 01:35 — Commit + push

- Pre-commit hook caught voseo glosario citation in this impl-log (legitimate audit trail of the rule consulted). Added R25 magic comment `<!-- voseo-allowed: technical reference citing the voseo→neutro glosario verbatim from .claude/rules/spanish-text.md (R2 audit trail in Skills Consulted table) -->` per spanish-text.md § "Magic comment escape".
- Commit `aabd3acc` (`development`). 7 files changed, 315 insertions, 28 deletions, 2 new files.
- Push origin/development successful (253e6024..aabd3acc).

### State at handoff to gate-runner + auditor

- All A1/A2/A3/A4 acceptance verifiers PASS.
- Native lint + format clean on the 2 Python files modified.
- 680/680 sales_agent + arch hardcoded-models tests PASS.
- Zero behavioral diff (docstring textual changes only).
- Ajenos files in working tree (T-8 session, CONTEXT-BRIEF-validation auto-modified during T-9 brief gen) preserved untouched per parallel-safety M1/M8.
- T-9 commit SHA: `aabd3acc`.
