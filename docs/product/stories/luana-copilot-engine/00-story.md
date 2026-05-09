# Story 6 — Copilot Engine lift

> **Outcome:** luana-platform-migration · **Sequence:** 6/14 · **AGENTIC PRODUCTION CODE — Opus mandatory (R23)**

## What

Lift `modules/copilot/` (33k LOC) → `luana-core-copilot`.

**Engine al core:**
- LangGraph state machine + `CopilotOrchestrator`
- DeepAgents subagent harness + `SubAgentMiddleware` isolation
- Anthropic prompt cache slot architecture (5min/1h TTL)
- Observability completa (`copilot_trace_event`, `copilot_llm_call`, cost recorder)
- Tool registry pattern + base classes
- Workflow registry pattern + base classes
- Extractor registry pattern + base classes
- Module registry (lazy-load per brand)
- Suggestion engine + provider registry
- Mutation journal + persistence
- Doc extraction pipeline
- Voice transcription endpoint
- Streamlit admin (LLM virtual keys, conversaciones, costo, etc.)

**Brand-extension reservado** (NO migra a core):
- Vitalia: `MedicalKBExtractor`, `PrepaidPaymentChecker`, `TreatmentFollowupWorkflow`
- Comunify: `OfferLadderAdvisor`, `AuthorityVaultExtractor`, `CommunityEngagementWorkflow`
- Lupulo: `MenuExtractor`, `KitchenStatusTool`, `ReservationOrderWorkflow`

## Critical pre-flight

- Story 5 completed (brand-studio + offer-studio cores live)
- Story 4 completed (crm + analytics + landing + connections cores live)
- ModuleDescriptor lazy-load mechanism designed (registry per-brand)
- Tools generic vs brand-specific audit complete (cleanup item §6.1)

## Acceptance

- 1 package publicado v0.0.6-alpha
- FE: `@luana/copilot-ui` v0.0.6-alpha
- Smoke: stub brand registers tool via `Copilot.toolRegister(stub_tool)` → tool callable
- Eval: golden classifier+summarizer pass post-lift
- Cost recorder funcional post-lift (zero degradation)
- §3 protected surfaces preservadas

## Effort: 18-25 tickets, ~7 días Opus
