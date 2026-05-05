---
level: story
id: sales-agent-litellm-canonicalization
phase: PO_RATIFIED
status: pending
last_artifact: 01-spec.md
last_modified: 2026-05-05T03:01:12Z
next_action: "/architect lee 01-spec.md → spawnea /architect-be (+ /architect-agentic si aplica) → produce 04-tickets.yaml"
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: false                              # PI-12 entero parallel_safe=false
blocked_reason: null                              # Independiente — puede arrancar inmediatamente. Story B (eval-runner-foundation) NO toca los mismos archivos; ambas paralelizables a nivel branch development
audit_iterations: 0
ratified_by_chris: true
po_version: 2
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md` (scope original: deepseek-fix, owner qwen). Phase=PM_DRAFT, status=pending.
- 2026-05-04 21:00 — `/po` (Opus) reframe completo post-ratificación Chris: scope expandido a `sales-agent-litellm-canonicalization` (LiteLLM canonical único path + zero tech debt cleanup, 9 sub-tickets T1..T9). Folder renamed `sales-agent-cost-tracking-deepseek-fix → sales-agent-litellm-canonicalization` via `git mv`. Owner pool changed `qwen-opencode → claude-opus-4-7`. Reescrito `00-story.md` (po_version=2). Generado `01-spec.md` (po_version=1, 4 scenarios obligatorios + 6 open questions + service_contract type=event_handler). Generado `docs/product/stories/sales-agent/sales-agent-litellm-canonicalization.yaml`. Actualizado INDEX.md sales-agent + capability YAML `sales-observability-cost-tracking.yaml` (story_ids + count + gaps). Phase=PO_SPEC, status=pending Chris ratification.

## Notas

- 2026-05-04: Chris delegó las 13 open questions al /po; /po ratificó 13+2 decisiones (Story A: A1-A6+X1+X2; Story B: B1-B7). Spec lockeada. Handoff /architect.
- Folder renamed from `sales-agent-cost-tracking-deepseek-fix` → `sales-agent-litellm-canonicalization` on 2026-05-04 (git mv preserves history).
- Owner pool changed `qwen-opencode → claude-opus-4-7` por scope reframe (toca callback shared cross-agent + Alembic destructivo + flag deletion + tests audit ~20 archivos).
- Story B (`sales-agent-eval-runner-foundation`) está siendo escrita por agente paralelo en este sprint S1. Sus archivos NO han sido tocados por esta sesión PO.
- 6 open questions (Q1..Q6) en `01-spec.md` que requieren ratificación Chris ANTES de pasar a `/architect`. Algunas son críticas (Q2 = strategy migration drop tenant cols → 2-step recomendado por safety).
- Reglas mandatorias aplicables al architect + dev-team: `.claude/rules/anti-default-flip-audit.md` (T5), `.claude/rules/anti-duplication.md` (T1 callback shared), `.claude/rules/backend-migrations.md` (T3+T6), `.claude/rules/tdd-mandatory.md`, `.claude/rules/architectural-fitness.md` (T8 ratchet shrink).
