---
level: story
id: sales-agent-litellm-canonicalization
phase: AUDIT_T1_APPROVED
status: pending
last_artifact: 06-audit/T-1-review.md
last_modified: 2026-05-05T07:00Z
next_action: "/dev-team toma T-2 (sync-pricing extends litellm_sync.py) — puede correr en paralelo con T-7 (tests audit). T-2 + T-7 están desbloqueados por T-1 APPROVED."
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: false
blocked_reason: null
audit_iterations: 1
ratified_by_chris: true
po_version: 2
arch_version: 1
total_tickets: 11
estimated_total_hours: 38
critical_path: "T-1 ✅ → T-7 → T-4 → T-5 → T-6a → T-6b (operational gate, ~5 working days) → T-6c"
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md` (scope original: deepseek-fix, owner qwen). Phase=PM_DRAFT, status=pending.
- 2026-05-04 21:00 — `/po` (Opus) reframe completo post-ratificación Chris: scope expandido a `sales-agent-litellm-canonicalization` (LiteLLM canonical único path + zero tech debt cleanup, 9 sub-tickets T1..T9). Folder renamed `sales-agent-cost-tracking-deepseek-fix → sales-agent-litellm-canonicalization` via `git mv`. Owner pool changed `qwen-opencode → claude-opus-4-7`. Reescrito `00-story.md` (po_version=2). Generado `01-spec.md` (po_version=1, 4 scenarios obligatorios + 6 open questions + service_contract type=event_handler). Generado `docs/product/stories/sales-agent/sales-agent-litellm-canonicalization.yaml`. Actualizado INDEX.md sales-agent + capability YAML. Phase=PO_SPEC, status=pending Chris ratification.
- 2026-05-04 22:00 — Chris delegó las 13 open questions al `/po` con criterio "robustez/escalabilidad > costo hoy". `/po` ratificó 13+2 decisiones: A1 (slashed model field), A2 (3-step expand-contract migration), A3 (mandatory gemini audit pre-delete), A4 (drop 4 cols sin rename), A5 (T2 EXTENDS existing litellm_sync.py), A6 (ARQ worker primary + GHA backup), X1 (keep proxy mode), X2 (calculate_cost removed from runtime path). Phase=PO_RATIFIED.
- 2026-05-05 03:30 — `/architect` (Opus, acting standalone for service-story BE-only) produjo `03-arch-be.md` (995 líneas) + `04-tickets.yaml` (877 líneas, 11 tickets). Phase=ARCHITECT_COMPLETE.
- 2026-05-05 06:30 — `/dev-team` (claude-opus-4-7) implementó T-1 cost recorder canonicalization. Commit `5856be4d` push a `development`. Phase=DEV_T1_DONE.
- 2026-05-05 07:00 — `/auditor` (claude-opus-4-7, auditor-be) revisó T-1 commit `5856be4d`. Verdict: **APPROVED**. 11/12 categories PASS (Cat 3 N/A — no soft delete operations). Re-ran tests independently: 13/13 ticket tests PASS, 1015/1015 regression PASS, 823/823 arch fitness PASS, ruff lint+format clean, coverage 73% (>43% threshold). Anti-duplication grep evidence verified. Anti-default-flip-audit N/A (T-1 NO flipea ningún flag). Scope creep audit: copilot/sales_agent file changes son schema mirrors + regression adaptations only, autorizados por architect doc § 3.4 + § 5. Phase=AUDIT_T1_APPROVED. Last artifact: `06-audit/T-1-review.md`.

## Notas

- Story B (`sales-agent-eval-runner-foundation`) está siendo escrita por agente paralelo en este sprint S1. Sus archivos NO han sido tocados por esta sesión.
- Architect produjo 11 tickets totales (no 9 como en story sub_tickets summary): T-1 + T-2 + T-3 + T-4 + T-5 + T-6a + T-6b (operational gate, NOT code) + T-6c + T-7 + T-8 + T-9. T-6a/T-6b/T-6c materializan A2 expand-contract 3-step.
- All owner_eligibility = `claude-opus-4-7` (sales_agent observability surface, agentic-adjacent). qwen banned per CLAUDE.md hard rule.
- Critical path: T-1 ✅ → T-7 → T-4 → T-5 → T-6a → T-6b (5 working days operational gate) → T-6c. Estimated wall-clock: ~22h dev + 5 days T-6b gate. T-2/T-3 parallel-able after T-1. T-8/T-9 tail.
- Reglas mandatorias aplicables al dev-team + auditor: `.claude/rules/anti-default-flip-audit.md` (T-5), `.claude/rules/anti-duplication.md` (T-1 NEW class justified, NOT mirror), `.claude/rules/backend-migrations.md` (T-3 + T-6a + T-6c idempotentes), `.claude/rules/tdd-mandatory.md` (RED tests per layer, default flag flip 4-step), `.claude/rules/architectural-fitness.md` (T-8 ratchet shrink + 3 new assertions).
- T-4 BLOQUEANTE: gemini.py audit checklist 6/6 must PASS pre-delete (function calling, safety_settings, system_instruction, generation_config, vision multipart, streaming chunks). ANY FAIL → ESCALATE Chris BLOCK.
- T-6b NOT a code ticket: operational gate (PM owner). 5 working days zero-read window OR Chris ratification + Streamlit query + structlog aggregation evidence in checkpoint.md.
- `CostRecorderCustomLogger` is NEW class (justified — not mirror) at NEW surface (LiteLLM CustomLogger conceptually distinct from LangChain BaseCallbackHandler; bridged by litellm_call_id + thread-safe TTL cache 60s).
- Anti-flip audit T-5 special case: flag deletion (True → removed), NOT flip. Tests mocking `LITELLM_PROXY_ENABLED=False` were probing dead path post-S3 → DELETE not migrate. Inventory in `.claude/rules/anti-default-flip-audit.md` REMOVES the row + adds footnote.
- pm-nico/current-state updates required post-merge: `docs/product/modules/sales-agent.md` § "LLM routing", `docs/product/capabilities/sales-agent/sales-observability-cost-tracking.yaml` (gaps removal), `docs/domains/llm-routing.md` (Capa 5 reescrita).
- T-1 audit PASS observations (no blocking): coverage cost_recorder.py 72% (defensive paths uncovered, OK); result.md menciona "diff es solo model field" — realidad incluye también cost_usd null en snapshots (intencional per X2, doc imprecisión leve); `# noqa: F401` para calculate_cost retained — válido (utility de reconciliation); fixture `_reset_cache` accede `_cache` private — aceptable para tests.

## Tickets unblocked post-T1 APPROVED

| Ticket | Status | Note |
|---|---|---|
| T-2 | UNBLOCKED | Puede empezar inmediato (extends litellm_sync.py + Makefile target) |
| T-7 | UNBLOCKED | Puede empezar en paralelo con T-2 (tests audit ~20 files) |
| T-3 | STILL BLOCKED | aguarda T-2 (blocked_by [T-1, T-2]) |
| T-4 | STILL BLOCKED | aguarda T-7 |
| T-5 | STILL BLOCKED | aguarda T-4 + T-7 |
| T-6a | STILL BLOCKED | aguarda T-5 |
| T-8 | STILL BLOCKED | aguarda T-4 + T-5 |
| T-9 | STILL BLOCKED | aguarda T-8 |
