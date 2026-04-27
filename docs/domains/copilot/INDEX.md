# Copilot — Docs Index

Navigation map for the Copilot module docs. Load only the doc relevant to your
task; do **not** load all docs at once. Cross-doc work? Check the "See also"
links inside each doc.

## Contracts (authoritative)

| Doc | Scope | Status |
|---|---|---|
| [CONTRACT.md](./CONTRACT.md) | Data model v2 + agentic plugins + sidebar v2 (routing, skills, rules, hooks, sub-agents, conversation CRUD) | Approved + merged (see `REVIEW.md`) |
| [CONTRACT-MULTIMODAL.md](./CONTRACT-MULTIMODAL.md) | Multimodal content rearchitecture: canonical `MessageBlock` schema (11 types), SSE v2 protocol, media upload delegation, outbound assets tools, voice dual-mode, citations, quote-reply, smart-chips stub, channel-agnostic renderer | Design — ready for parallel implementation |

## Operational guides

| Doc | When to read |
|---|---|
| [message-blocks.md](./message-blocks.md) | Adding a new block type. Understanding block validation. Writing a renderer. |
| [channel-adapters.md](./channel-adapters.md) | Adding a new outbound channel. Mapping blocks to a channel's native API (WA, Telegram, email). Fallback strategy for unsupported block types. |
| [sse-protocol.md](./sse-protocol.md) | Consuming or emitting SSE events. Understanding v1 → v2 migration window. |
| [outbound-assets.md](./outbound-assets.md) | How the assistant references existing assets. `search_assets` / `get_asset` tool semantics. Tenant isolation rules. |
| [suggestions-engine.md](./suggestions-engine.md) | Smart chips: current stub + future engine options. `Suggestion` interface + hook contract. |

## Specs & reviews

| Doc | Purpose |
|---|---|
| [UI-SPEC.md](./UI-SPEC.md) | Frontend UI behavior — sidebar states, chat panel, message rendering, composer, voice recorder UI. Owned by ux-designer. |
| [copilot-refactor-spec.md](./copilot-refactor-spec.md) | Product-level refactor spec (the "why" behind CONTRACT.md §1–§22). |
| [REVIEW.md](./REVIEW.md) | Self-audit of the data-model v2 refactor. Baseline for external review. |

## Active redesign (2026-04)

| Doc | Purpose |
|---|---|
| [redesign-2026-04/README.md](./redesign-2026-04/README.md) | Plan completo refactor copilot → "Claude Code de Marketing": 11 fases (F0-F10), provider pattern, deep agents harness, workflow unification. |
| [redesign-2026-04/00-vision-and-non-goals.md](./redesign-2026-04/00-vision-and-non-goals.md) | Visión target + lista exhaustiva §3 lo que NO se toca. |
| [redesign-2026-04/02-architecture-target.md](./redesign-2026-04/02-architecture-target.md) | Topología destino post-F10. |
| [redesign-2026-04/learnings/](./redesign-2026-04/learnings/) | Aprendizajes acumulados por fase. |

## Observability rebuild (2026-04, cerrado)

| Doc | Purpose |
|---|---|
| [observability-rebuild-2026-04/README.md](./observability-rebuild-2026-04/README.md) | Refactor 3-fase del módulo observability: switch atómico al callback handler de LangChain, schema OTel-compatible, costo LLM por tenant en ciclo billing 25-25. |
| [observability-rebuild-2026-04/ARCHITECTURE.md](./observability-rebuild-2026-04/ARCHITECTURE.md) | Estado objetivo: estructura `backend/src/modules/copilot/observability/` (recording / pricing / cost / persistence / reporting / workers / api), schema DB final, MV diaria. |
| [observability-rebuild-2026-04/PRINCIPLES.md](./observability-rebuild-2026-04/PRINCIPLES.md) | 15 principios no-negociables (cohesión, migración total, switch atómico, best-effort, TDD, OTel-compatible, PII redaction, tenant isolation). |
| [observability-rebuild-2026-04/phase-{1,2,3}-*/](./observability-rebuild-2026-04/) | Plans + research-checklists + completion-checklists + learnings + deferred-debt por fase. |

**Live dashboard:** `/costo-copilot` en el admin Streamlit. Tres vistas — Comando Central (KPIs + tabla de tenants + CSV export), Detalle por tenant (series temporales 60d + breakdown por modelo + delta vs ciclo anterior), Top conversaciones (drill-down a `/trazas`).

**Reglas asociadas:** `.claude/rules/copilot-observability.md` (cómo agregar domain events / providers / pricing manual / retention / PII), `.claude/rules/copilot-resilience.md` §"Debug copilot" (queries a `copilot_llm_call` post-Phase-2).

## Reading order by task

- **Implementing a new block type:** `CONTRACT-MULTIMODAL.md §1` → `message-blocks.md` → (FE) `UI-SPEC.md`.
- **Implementing media upload (FE or BE):** `CONTRACT-MULTIMODAL.md §7` → `outbound-assets.md` (for how the assistant consumes assets).
- **Implementing SSE v2 consumer or producer:** `CONTRACT-MULTIMODAL.md §6` → `sse-protocol.md`.
- **Implementing the voice dual-mode UI:** `CONTRACT-MULTIMODAL.md §9` → `UI-SPEC.md` (recorder section).
- **Adding WhatsApp as an active channel (future):** `channel-adapters.md` → `CONTRACT-MULTIMODAL.md §1.5, §5.3`.
- **Understanding routing / tiers / skills / rules:** `CONTRACT.md` (existing, approved).

## Anchor comments

Anchor comments `[COPILOT-*]` in source code map to this documentation set.
See `CONTRACT-MULTIMODAL.md §12` for the authoritative table. Arch test
`test_copilot_anchors_have_docs` enforces alignment.

## Change policy

- **Contracts** (`CONTRACT.md`, `CONTRACT-MULTIMODAL.md`): edits require an
  architect sign-off; bump version at the top; update `REVIEW.md` if the
  approved contract changes.
- **Operational guides**: PRs welcome; keep them short and task-oriented.
