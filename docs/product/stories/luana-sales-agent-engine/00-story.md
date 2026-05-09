# Story 7 — Sales Agent Engine lift

> **Outcome:** luana-platform-migration · **Sequence:** 7/14 · **AGENTIC PRODUCTION CODE — Opus mandatory (R23)**

## Critical pre-flight

**BLOCKED BY Story E** (`sales-agent-voice-fidelity-grader-runtime`) → state `done`. Per ADR-001 §6 + OQ1 decision.

## What

Lift `modules/sales_agent/` (engine, 17k LOC) → `luana-core-sales-agent`.

**Engine al core:**
- LangGraph orchestrator + state machine
- Brand voice consumer via `BrandVoicePort` (compiler vive en `core-brand-studio` per Story 5)
- Slot architecture (5 slots, prompt cache prefix)
- Tool registry (scheduler, payment, knowledge, qualification, follow-up base)
- Specialist routing semantic (NANO/FAST/REASONING/AGENT)
- Closer Studio API + WS
- Buffer service + output manager
- Follow-up engine + scheduler
- Observability (traces, cost)
- Channel format registry
- Intent detector
- Semantic router
- PII sanitization

**Eval framework NO migra esta story** (deferred to Luana v0.2.0 per OQ1):
- Eval simulator dual-LLM
- MAJ-EVAL grader runtime
- Personas catalog
- Goldens dataset infra

→ Eval queda en `nicolify` repo hasta estabilizar post Story E `done`. Promueve a Luana v0.2.0 (~Sem 9).

**Brand-extension reservado:**
- Vitalia tools: `prepaid_payment_check`, `treatment_followup_check`, `medical_consent_request`
- Comunify tools: `qualify_for_cohort`, `link_to_community`, `nurture_via_authority_content`
- Lupulo tools: `book_table`, `place_order`, `query_menu`, `kitchen_eta`

## Acceptance

- 1 package publicado v0.0.7-alpha
- FE: `@luana/sales-ui` + `@luana/closer-studio-ui` v0.0.7-alpha
- Smoke: stub brand registers tool via `SalesAgent.toolRegister(stub_tool)` → agent calls it
- BrandVoicePort funcional (consume voz desde core-brand-studio)
- §3 protected surfaces preservadas
- Cost tracking + observability funcional post-lift

## Effort: 16-22 tickets, ~6 días Opus
