# PLAN — Generic Async Extraction Feedback

v1 bundle implementation order. Every phase is independently shippable and revertible.

## Phase 0 — LLM prompt delta (XS, ship first — instant UX win)

| File | Change |
|---|---|
| `backend/src/modules/copilot/application/tools/extraction_tools.py:231-253` | Rewrite docstring to two-axis clarify example (scope + mode) with section fallback. |
| `backend/src/modules/copilot/application/prompts/extraction_flow.md` (NEW if absent, else update) | Add few-shot: user on `/brand-studio/identity` says "analiza visionarias.pe" → LLM calls `clarify` with section-aware options. |
| `backend/src/modules/copilot/application/tools/mutations.py` + editable-fields | No change. |

**Acceptance:**
- Manual: from `/brand-studio/identity` ask "analiza mi sitio" → receive ClarifyCard with 3 scope options including "Solo Identidad (esta página)".
- `.venv/bin/pytest backend/tests/modules/copilot/ -k extract` green.

---

## Phase 1 — Foundation hook + store (M, ~1d)

**Backend — tool contract extension (backwards-compatible):**

| File | Change |
|---|---|
| `backend/src/modules/copilot/application/tools/extraction_tools.py:222-262` | Extend literals: `module` adds `"asset"`, `"persona"`; `scope` adds `"section"`, `"field"`; `mode` adds `"suggest"`. Add `section`, `field`, `entity_id` params. Keep `offer_id` as deprecated alias. |
| `backend/src/modules/copilot/application/tools/extraction_tools.py:_validate_extract_args` | Validate new combinations; reject `scope="section"` without `section`. |
| `backend/src/modules/copilot/application/tools/extraction_tools.py` (return JSON) | Enrich with `target_label_es`, `source_kind`, `source_ref`, `eta_seconds`. |
| `backend/src/modules/copilot/application/tools/extract_from_doc.py` (NEW, ≈80 LOC) | Parallel to `extract_from_url` — wraps `extract_document_to_fields` in `guided/extract.py` with unified contract. |
| `backend/src/modules/copilot/application/tools/registry.py` | Register `extract_from_doc`. Add to `ROUTE_TOOL_MAP` under `extraction` group. |
| `backend/src/modules/brand/workers/tasks.py:75-88` (`on_progress`) | Enrich payload: `filled_fields`, `filled_fields_by_section`, `sections_touched`, `sections_completed`, `newly_completed_section`. |
| `backend/src/modules/offer/workers/tasks.py` (mirror) | Same enrichment. |
| `backend/src/modules/brand/api/extraction_status.py` | Return enriched Redis payload verbatim. |
| `backend/src/modules/offer/api/extraction_status.py` | Same. |

**Frontend — polling + state:**

| File | Change |
|---|---|
| `frontend/src/lib/api/ai-actions.ts:92-101` | Generalize `pollExtractionStatus` → `pollJobStatus`. Keep old export as `@deprecated` alias for one release. |
| `frontend/src/features/copilot/store/copilot-store.ts` | Add `activeJobs: Record<string, AsyncJobState>` + actions `registerJob`, `updateJob`, `completeJob`, `clearJob`. |
| `frontend/src/features/copilot/hooks/use-async-tool-job.ts` (NEW) | Polling loop (2s → 5s after 60s); selectors `useAsyncToolJob(id)`, `useActiveJobs()`, `useActiveJobsForModule(module)`; React Query invalidation on complete; `copilot:field-update` dispatch; tab-blur notification trigger. |
| `frontend/src/features/copilot/lib/job-invalidation-map.ts` (NEW) | `JOB_INVALIDATION_MAP: Record<module, readonly string[][]>`. |
| `frontend/src/features/copilot/hooks/use-copilot-chat.ts:175-177` (`onToolResult`) | If result JSON has `job_id` + `poll_endpoint` → `registerJob` + start polling. |

**Architecture/quality:**

| File | Change |
|---|---|
| `backend/tests/modules/copilot/test_extract_from_url_contract.py` (NEW) | Validates extended shape: all fields present, backwards-compat with old calls (only `module`+`url`+`offer_id`), section/field validation edges. |
| `backend/tests/architecture/test_async_job_contract.py` (NEW) | Ratchet: every tool emitting `job_id` must also return the full AsyncToolJob shape. |
| `frontend/src/features/copilot/__tests__/use-async-tool-job.test.ts` (NEW) | Polling cadence, backoff, invalidation firing, completion terminal, error branch. |

**Acceptance:**
- Backend tests: `cd backend && .venv/bin/pytest tests/modules/copilot/ tests/architecture/test_async_job_contract.py -x`.
- Frontend tests: `cd frontend && npx vitest run src/features/copilot/__tests__/use-async-tool-job.test.ts`.
- Arch: `cd backend && .venv/bin/pytest tests/architecture/ -x -q`; `cd frontend && npx vitest run src/__tests__/architecture/`.
- Manual: trigger extraction on `/brand-studio/identity` → Redux DevTools shows `activeJobs[id]` mutating every 2s with populated `filled_fields_by_section`.

---

## Phase 2 — Live ToolCallChip + Summary Card + completion wiring (S, ~6h)

| File | Change |
|---|---|
| `frontend/src/features/copilot/components/messages/ToolCallChip.tsx` | Add optional `jobId?: string` prop. When set, subscribe to `useAsyncToolJob(jobId)`, render extended layout: progress bar + stage + counters. On `status="completed"` collapse to single-line counters + success tint. |
| `frontend/src/features/copilot/store/copilot-store.ts` — `addToolCallToLastAssistant` | Accept optional `jobId` (read from tool_result JSON). Store on the toolCall entry. |
| `frontend/src/features/copilot/hooks/use-copilot-chat.ts` `onToolResult` | Parse `job_id` from tool result JSON and pass to store when attaching toolCall. |
| `frontend/src/features/copilot/types/message-blocks.ts` | Extend `CardKind` union with `"extraction_summary"`. |
| `frontend/src/features/copilot/components/blocks/CardBlock.tsx` | Dispatch case for `extraction_summary` → `<ExtractionSummaryCard />`. |
| `frontend/src/features/copilot/components/cards/ExtractionSummaryCard.tsx` (NEW, ≈90 LOC) | Mirror `ClarifyCard` tokens. Props typed by `ExtractionSummaryData`. |
| `backend/src/modules/copilot/domain/card_kinds.py` (or equivalent) | Register `extraction_summary` kind + Pydantic data shape. |
| `backend/src/modules/brand/workers/tasks.py` (end of `run_brand_extraction`) | After `on_progress(progress=100, status="completed")`, insert assistant message with `blocks: [CardBlock{card_kind="extraction_summary", data: {...}}]` via conversation repo. |
| `backend/src/modules/offer/workers/tasks.py` | Mirror. |

**Acceptance:**
- Manual: run extraction, chip shows live progress each 2s, final summary card auto-appears in chat. Page reload → card persists.
- Vitest: `use-async-tool-job.test.ts` asserts `invalidateQueries(['brand-settings'])` fired on completion.
- Playwright smoke: `e2e/specs/regression/copilot-extraction-progress.spec.ts` (NEW) mocks status endpoint with scripted progress + final completion payload; asserts chip updates + summary card visible.

---

## Phase 3 — NavRail section badges (M, ~4h)

| File | Change |
|---|---|
| `frontend/src/features/copilot/hooks/use-section-status.ts` (NEW, ≈30 LOC) | Pure selector over `useActiveJobsForModule(module)` — returns `Record<sectionSlug, SectionStatus>` |
| `frontend/src/features/brand-studio/components/BrandStudioNavRail.tsx:20-45` | Read `useSectionStatus("brand")`; pass `status` to each `SectionRow`. |
| `frontend/src/features/brand-studio/components/BrandStudioNavRail.tsx:53-81` | Extend `SectionRow` to render badge between label and chevron (spinner + count / check + count / dim dot). Hover tooltip with field list. |
| `frontend/src/features/offer-studio/components/OfferStudioNavRail.tsx` | Mirror. |
| `frontend/src/features/brand-studio/components/__tests__/BrandStudioNavRail.test.tsx` | Add cases for each status. |
| `frontend/src/features/offer-studio/components/__tests__/OfferStudioNavRail.test.tsx` | Mirror. |

**Acceptance:**
- Vitest suites green.
- Visual: with mock `activeJobs` state, rail shows mixed statuses correctly. No layout shift on idle→running→completed.

---

## Phase 4 — Inline section-complete pills (S, ~2h)

| File | Change |
|---|---|
| `backend/src/modules/brand/workers/tasks.py` | On each wave where `newly_completed_section` is set, insert an assistant message with `blocks: [CardBlock{card_kind="navigation", data: {...}}]` pointing to `/brand-studio/{section_slug}` and `page_label: "✓ {label} lista · {N} campos"`. |
| `backend/src/modules/offer/workers/tasks.py` | Mirror. |
| `frontend/src/features/copilot/components/messages/NavigationCard.tsx` | Zero changes (already fits). |

**Acceptance:**
- Manual: trigger full-brand extraction from `/brand-studio/identity` → chat receives ≥1 pill per completed section, clicking navigates.

---

## Phase 5 — Tab-blur notification (S, ~1h)

| File | Change |
|---|---|
| `frontend/src/features/copilot/hooks/use-tab-notification-permission.ts` (NEW, ≈20 LOC) | Prompt + persist permission. |
| `frontend/src/features/copilot/hooks/use-async-tool-job.ts` | On terminal status + `document.hidden`: fire `toast.success()` (persistent) + `new Notification()`; mutate `document.title`. Restore title on `visibilitychange → visible`. |

**Acceptance:** Manual — start extraction, switch tab, wait. Browser tab title flashes, OS notification fires (if granted), sonner toast visible on return.

---

## Risk / Rollback

- **Polling cost:** 2s × ~60s = 30 requests per job. Acceptable. Scales fine on current infra.
- **Redis TTL:** already 3600s (see `extraction_tools.py:137`). Orphan jobs auto-clean.
- **Backward compat:** every backend change is additive. Old `offer_id`-only calls keep working.
- **Worker idempotency:** inserting assistant messages from the worker must be tenant-scoped + deduplicated if worker retries. Add `idempotency_key = f"summary:{job_id}"` and a unique index on `(conversation_id, idempotency_key)` in the messages table if not present.
- **Rollback:** each phase is independent. Phase 2 with Phase 1 only → chip works, sidebar badges remain idle. Reverting Phase 3/4 leaves Phase 2 intact.

## Cross-stack tests

| Test | Phase |
|---|---|
| `backend/tests/modules/copilot/test_extract_from_url_contract.py` | 1 |
| `backend/tests/architecture/test_async_job_contract.py` | 1 |
| `backend/tests/modules/brand/test_worker_emits_summary_and_pills.py` | 2, 4 |
| `frontend/src/features/copilot/__tests__/use-async-tool-job.test.ts` | 1 |
| `frontend/src/features/copilot/components/cards/__tests__/ExtractionSummaryCard.test.tsx` | 2 |
| `frontend/src/features/brand-studio/components/__tests__/BrandStudioNavRail.test.tsx` | 3 |
| `frontend/src/features/offer-studio/components/__tests__/OfferStudioNavRail.test.tsx` | 3 |
| `frontend/e2e/specs/regression/copilot-extraction-progress.spec.ts` | 2, 3, 4 |

All must run native-WSL (`.venv/bin/pytest`, `npx vitest`, `npx playwright`) — never in Docker (per `.claude/rules/debugging.md`).

## Commit hygiene

- Phase 0 in one commit: docstring + few-shot.
- Phase 1 in ≤3 commits: contract extension; hook+store; tests.
- Phase 2+ each own commit(s). Conventional Commits (`feat(copilot): …`, `feat(brand-studio): …`).
- No force-push main. `development` branch only.
