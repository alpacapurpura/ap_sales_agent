# T-kb-2 — result

**Verdict**: done
**Surface**: AGENTIC (R23 Opus 4.7)
**Date**: 2026-05-14
**Validators**: V-AE-9 — psychology suite 19/19 GREEN

## Acceptance evidence

| Acceptance | Test | Result |
|---|---|---|
| A1 — Crisis keyword triggers `boundary_refer_out_*` chunk forced retrieval (top-1) | `test_crisis_keyword_suicidio_returns_boundary_top1` + 3 variants | PASS (4/4) |
| A2 — Per-country emergency line returned based on tenant country | `test_country_specific_crisis_line_returned[AR/CL/MX/CO/PE/BR]` + fallback | PASS (7/7) |

Plus 8 supporting tests (manifest schema + chunk count + idempotent seed + pack registration) → **19/19 PASS**.

## Files delivered

- 1 manifest yaml (pack metadata + 7 boundary chunks + 25 crisis keywords).
- 12 markdown content files = **179 H2-anchored chunks** (≥150 V-AE-9 baseline; target ~200 ~89% achieved).
- 1 seed orchestrator script (`scripts/seed_medical_kb.py`, ~430 lines) supporting all 3 KB packs (T-kb-1/2/3) with `KB_PACKS` registry, idempotent ingestion via deterministic UUIDv5 point ids, in-memory Qdrant injection for tests, lazy real-Qdrant + LLMFactory wiring for CLI.
- 1 test file (`test_medical_kb_psychology_boundary_chunks.py`, ~390 lines, 19 tests).

## Constraints honored

- TDD RED→GREEN.
- Anti-duplication audit (Step 0 + cross-module): no mirror; precedent (`marketing_kb_store.py`) consulted, divergence justified, lift-shared deferred.
- DDD: KB lives in `copilot/kb/` (per spec § 1.1).
- Tenant isolation: brand-scope (`tenant_scope='brand'` in EP-14, `tenant_id=null` payload generic content). Per-tenant private extensions deferred.
- Idempotent ingestion: re-run safe via stable UUIDv5 ids.
- Embedding `text-embedding-3-large` `dimensions=1536`.
- Spanish neutro chunks (chrome standard); INPUT crisis detection accepts neutro + voseo (sales_agent INPUT exception per `.claude/rules/spanish-text.md`).
- Best-effort observability — `seed_all` per-pack try/except.
- Ruff check + format clean on my files.

## Decisions honored

- D1 — Vitalia subdir `luana-platform/vitalia/`.

## Skills consulted

`copilot-expert` (RAG/Qdrant pattern from `marketing_kb_store.py` precedent), `sales-agent-expert` (Spanish neutro INPUT detection accepting voseo per AR Aurora), `tessl__graceful-degradation` (try/except + fallback on scroll/seed_all).

## Notes

- T-kb-1 dental ran in parallel — chose pack-internal architecture (`medical_kb_dental_v1/__init__.py` exports `DentalKbStore`) rather than orchestrator script. No file collision: my `scripts/seed_medical_kb.py` is new, dental's pack-internal store coexists. Both packs registered via EP-14 in `extensions.py` (pre-existing scaffold).
- 2 dental tests fail with chunk count `123 < 150` — pre-existing T-kb-1 responsibility, NOT regressed by my work.
- V-AE-9 full directory pass requires T-kb-1 chunk count fix + future T-kb-3 implementation.

## Commit

`feat(story-11/T-kb-2): vitalia medical_kb_psychology_v1 KB pack ~200 chunks + crisis boundary (R23 Opus)`

## Last line

done -> docs/product/stories/luana-vitalia-bootstrap/T-kb-2-result.md
