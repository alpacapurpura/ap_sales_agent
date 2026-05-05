---
level: story
id: sales-agent-eval-runner-foundation
phase: PO_RATIFIED
status: in-progress
last_artifact: 01-spec.md
last_modified: 2026-05-05T03:01:12Z
next_action: "/architect lee 01-spec.md → spawnea /architect-be (+ /architect-agentic si aplica) → produce 04-tickets.yaml"
spawned_at: 2026-05-04T20:00:00Z
spawned_by: /pm
parallel_safe: false
blocked_reason: null
audit_iterations: 0
ratified_by_chris: true
po_version: 2
---

## Bitácora

- 2026-05-04 20:00 — `/pm` creó folder + `00-story.md`. Phase=PM_DRAFT, status=pending.
- 2026-05-04 20:30 — `/po` produjo `01-spec.md` (4 scenarios Gherkin AI-resistant: smoke-multi-layer-pass + flag-omitted-skips-eval-suite + agent-degraded-output-detected + cross-tenant-leak-on-mock-tenant). Multi-layer rico (5 capas: trajectory + tool_calls + output + cost + latency). Tenant fijo Visionarias + DB real + LiteLLM real (cost > 0 verifica Story A). Phase=PO_SPEC. 7 open questions para Chris.
- 2026-05-04 20:30 — `/po` creó `docs/product/stories/sales-agent/sales-agent-eval-runner-foundation.yaml` con scenarios espejo del spec.
- 2026-05-04 20:30 — `/po` actualizó `docs/product/stories/sales-agent/INDEX.md` (+1 row planned).
- 2026-05-04 20:30 — `/po` actualizó `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (`stories_planned: 1`, `stories_total: 4`, story_ids +1, gap "Eval suite agentic faltante" tachado + apuntado a este story como addressing).

## Notas

- 2026-05-04: Chris delegó las 13 open questions al /po; /po ratificó 13+2 decisiones (Story A: A1-A6+X1+X2; Story B: B1-B7). Spec lockeada. Handoff /architect.
- 7 open questions abiertas en `01-spec.md` § "Open questions" — Chris debe responder antes de pasar a `/architect`. Defaults recomendados por PO incluidos.
- Scope NO incluye UX (service-story, no UI). Se salta `/ux-ui` y `/ux-agentico`.
- Esta story bloquea Stories 2/3/5/6/7/8/9 del PI-12. Es foundation hard-gate.
- Anti-duplication: el callback handler del harness DEBE heredar `shared/agent_observability/recording/base_callback_handler.py::BaseAgentCallbackHandler`. Step 0 grep obligatorio en architect phase per `.claude/rules/anti-duplication.md`.
- Cost real esperado: < $0.01 por corrida del smoke (1 turno DeepSeek V4-Flash).
