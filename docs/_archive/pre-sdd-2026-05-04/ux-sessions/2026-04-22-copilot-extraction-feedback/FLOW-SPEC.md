# FLOW-SPEC — Generic Async Extraction Feedback

**Scope:** Behavioral layer for any long-running copilot extraction (URL scraping, document ingestion, future audio/video).
**Mode:** Micro-connection. Tool- and source-agnostic.
**Constraint:** Preserve existing chat rail + brand-studio + offer-studio form layouts. Behavior layer only.

## 1. Problem

User runs extraction. Assistant returns `"Inicié el análisis. Tarda entre 1 y 2 minutos. Te aviso cuando termine..."` (verbatim from `extract_from_url` at `backend/src/modules/copilot/application/tools/extraction_tools.py:205-208`). Then silence.

No signal of progress. No notification on completion. No awareness that fields in other sections are being populated while the user sits on Identidad. No explicit scope confirmation (full entity vs. current section vs. replace vs. fill-empty).

The same problem applies to every async worker tool: brand extraction, offer extraction, document ingestion, future audio transcription, bulk import.

## 2. Root cause

1. **Silent async.** Tool dispatches ARQ job (`enqueue_job("run_brand_extraction", ...)` or `"run_offer_extraction"`), returns `{job_id, poll_endpoint}` — and the frontend never polls.
2. **Orphan helper.** `frontend/src/lib/api/ai-actions.ts:92-101` exports `pollExtractionStatus(jobId, token)` — nobody imports it.
3. **No cross-section awareness.** `BrandStudioNavRail.tsx:19` has a comment *"optional completion preview"* — the slot exists in design but was never wired.
4. **No scope affordance.** The tool's own docstring says: *"Antes de llamar esta tool: si el usuario no especificó el alcance, llama primero a `clarify` con opciones..."*. The LLM often skips that hint or offers only `mode` options (initial/update), never scope granularity.

## 3. Generic AsyncToolJob contract

### 3.1 Source tools (backend)

Family: `extract_from_{url,doc,media}`. **Extend** the existing `extract_from_url` rather than rewriting — it already accepts `module: Literal["brand", "offer"]` and returns `{job_id, poll_endpoint, ...}` (see `extraction_tools.py:222-262`). Minimum delta:

```python
# BEFORE (extraction_tools.py:222-262, simplified)
@tool
async def extract_from_url(
    module: Literal["brand", "offer"],
    url: str,
    scope: Literal["full", "visuals"] = "full",
    mode: Literal["initial", "update"] = "initial",
    update_instructions: str | None = None,
    offer_id: str | None = None,
) -> str: ...

# AFTER — extended literals, new section/field params, entity_id alias
@tool
async def extract_from_url(
    module: Literal["brand", "offer", "asset", "persona"],
    url: str,
    scope: Literal["full", "visuals", "section", "field"] = "full",
    mode: Literal["initial", "update", "suggest"] = "initial",
    section: str | None = None,                # required when scope="section"
    field: str | None = None,                  # required when scope="field"
    update_instructions: str | None = None,
    entity_id: str | None = None,              # generic replacement for offer_id
    offer_id: str | None = None,               # DEPRECATED alias → entity_id
) -> str: ...
```

Backwards-compatible: existing calls with `offer_id` keep working (internal aliasing).

**New tool** (parallel signature, different source):
```python
@tool
async def extract_from_doc(
    module: Literal["brand", "offer", "asset", "persona"],
    asset_id: str,                             # existing Asset entity
    scope: Literal["full", "section", "field"] = "full",
    mode: Literal["initial", "update", "suggest"] = "initial",
    section: str | None = None,
    field: str | None = None,
    update_instructions: str | None = None,
    entity_id: str | None = None,
) -> str: ...
```

This wraps (or replaces) the existing `extract_document_to_fields` under `backend/src/modules/copilot/application/tools/guided/extract.py` with the unified contract.

**Reserved** (future, same shape): `extract_from_media(asset_id, ...)`.

### 3.2 Tool result JSON shape

Every tool in the family MUST return:

```json
{
  "status": "dispatched" | "error",
  "job_id": "uuid",
  "poll_endpoint": "/api/v1/{module}/extract-full-{module}/status/{job_id}",
  "module": "brand" | "offer" | "asset" | "persona",
  "scope": "full" | "section" | "field" | "visuals",
  "mode": "initial" | "update" | "suggest",
  "section": "identity" | ... | null,
  "target_label_es": "Brand Studio · Identidad",   // NEW — user-facing label
  "source_kind": "url" | "doc" | "media",           // NEW
  "source_ref": "https://visionarias.pe" | asset_id,// NEW
  "eta_seconds": 90,                                 // NEW
  "message": "Inicié el análisis..."
}
```

The `message` field is kept for backward-compat; the chat no longer relies on it as the only communication channel.

### 3.3 Redis progress payload (worker-written, polled by frontend)

Currently written by `run_brand_extraction` at `backend/src/modules/brand/workers/tasks.py:75-88` with `{status, progress, stage, started_at}`. Extend to:

```json
{
  "status": "queued" | "running" | "completed" | "failed",
  "progress": 0..100,
  "stage": "Analizando sección 'Nosotros'...",
  "started_at": "2026-04-22T23:28:00Z",
  "finished_at": null | ISO,
  "filled_fields": ["brand_name", "tagline"],          // NEW — cumulative
  "filled_fields_by_section": {                         // NEW — cumulative bucketed
    "identity": ["brand_name", "tagline"],
    "strategy": ["mission"]
  },
  "sections_touched": ["identity", "strategy"],        // NEW — cumulative
  "sections_completed": ["identity"],                  // NEW — transitions to complete
  "newly_completed_section": "identity" | null,        // NEW — one-shot flag per poll
  "error": null
}
```

Key that was already set:
```
brand_extract:{tenant_id}:{job_id}
offer_extract:{tenant_id}:{job_id}
```
Extended to:
```
extract:{tenant_id}:{kind}:{job_id}        # kind = brand|offer|asset|persona
```
Backward-compat read layer accepts both formats.

### 3.4 Worker completion contract

On job `completed`, the worker MUST also:

1. **Insert a summary card** into the conversation as an assistant message with `blocks: [CardBlock{card_kind="extraction_summary", data: {...}}]` — new `CardKind` variant.
2. **Emit per-section navigation pills** as each section transitions `touched → completed`: assistant message with `blocks: [CardBlock{card_kind="navigation", data: {route, page_label, section_id, section_complete_meta: {fields_count}}}]`. Reuses existing `NavigationCard.tsx` (no new component).

Both are persisted messages — full parity with conversation history, survive page reload.

### 3.5 Cache invalidation registry (frontend)

New `frontend/src/features/copilot/lib/job-invalidation-map.ts`:

```ts
export const JOB_INVALIDATION_MAP: Record<string, readonly string[][]> = {
  brand:   [["brand-settings"], ["brand-sections"]],
  offer:   [["offer"]],
  asset:   [["assets"]],
  persona: [["personas"]],
};
```

Keyed by `module` (mirrors `target.kind`). On job `completed`, `useAsyncToolJob` invalidates all listed React Query keys so forms re-render with fresh data.

## 4. Proposed behaviors (re-ranked post scope discussion)

| # | Behavior | Impact | Effort | Tier | Notes |
|---|---|---|---|---|---|
| 0 | LLM prompt: enrich clarify scope options (section/all/replace/fill/suggest) | High | XS | P1 | Edit docstring + add few-shot |
| 1 | `useAsyncToolJob` hook + `activeJobs` store slice | foundation | M | P1 | |
| 2 | `ToolCallChip` live progress (extend existing) | High | S | P1 | |
| 3 | `ExtractionSummaryCard` (new `CardKind`) | High | S | P1 | |
| 4 | **NavRail section badges** — Brand + Offer | Very high | M | P1 (promoted from P3) | Cross-section awareness |
| 5 | **Inline section-complete pills in chat** via `navigation` card_kind | High | S | P1 (new) | Reuses `NavigationCard` |
| 6 | Tab-blur → sonner toast + Notification API + title flash | High for real async | S | P1 | |
| 7 | Field shimmer + global counter (form header) | Very high | M | P2 | Reuses `copilot-highlight` |
| 8 | Ambient footer bar in chat rail | Medium | S | P3 | |

**v1 bundle = 0+1+2+3+4+5+6.** Fixes: phantom "te aviso" (#3+6), silent progress (#2), cross-section blind spot (#4+5), ambiguous scope (#0). ~3 days.

## 5. Current route → default scope inference

Copilot already receives `ClientContextDTO.current_route` (`backend/src/modules/copilot/api/dto.py:19`). The LLM's enriched clarify prompt uses it to pre-select a default:

| Current route | Default option shown | Alternative offered |
|---|---|---|
| `/brand-studio/{section}` | "Solo **{section_label}** (esta página)" | "Todo Brand Studio" |
| `/brand-studio` (root) | "Todo Brand Studio" | "Solo una sección específica…" |
| `/offer-studio/{id}/{section}` | "Solo **{section_label}** de esta oferta" | "Toda la oferta" |
| `/offer-studio` (root) | "Elegir oferta…" | — |

Section slug lookup uses existing `BRAND_SECTIONS`/`OFFER_SECTIONS` catalogs (`frontend/src/features/brand-studio/lib/section-catalog.ts` and equivalent).

## 6. Prototype

`prototype/index.html` — animated simulation of the full v1 bundle on Brand Studio/Identidad with extraction scoped to the whole brand (cross-section case). Served on `http://localhost:8888`.
