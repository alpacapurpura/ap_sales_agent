# T-kb-2 — impl log

**Ticket**: medical_kb_psychology_v1 KB pack ~200 chunks + boundary refer-out
**Surface**: AGENTIC (R23 Opus 4.7 production code)
**Owner**: claude-opus-4-7
**Started**: 2026-05-14
**Closed**: 2026-05-14
**State**: GREEN — verified 19/19 native pytest psychology suite

## Skills Consulted

| Skill | Why invoked | Decision applied |
|---|---|---|
| `copilot-expert` | KB pack ingestion lives in copilot module; need RAG pattern + tenant isolation invariants | Followed Qdrant collection pattern from `core/luana-core-copilot/.../marketing_kb_store.py` precedent — per-collection store with lazy client/embedder injection, deterministic UUIDv5 point ids, ensure_collection idempotent. Diverged on: per-pack collection (vs global), tenant-aware payload tags (vs tenant-agnostic), forced retrieval bypass for boundaries (NEW). |
| `sales-agent-expert` | KB consumed by sales_agent at runtime → Spanish neutro INPUT detection MUST accept voseo per `.claude/rules/spanish-text.md` exception (sales_agent voice respects tenant) | Crisis_keywords list includes neutro `matarme` + voseo-compatible variants (`hacerme daño`). Boundary chunks themselves are Spanish neutro tuteo per chrome standard. |
| `tessl__langgraph` | Not invoked — no LangGraph node touched | N/A |
| `tessl__graceful-degradation` | Qdrant scroll + query_points are external Qdrant calls | `_fetch_forced_boundary_hits` wraps scroll in try/except with fallback to unfiltered scroll (legacy clients). `seed_all` per-pack try/except so one pack failure doesn't abort others. Best-effort throughout — never breaks the seeding orchestration. |

## Step 0 — Anti-duplication GATE

Pre-write grep:

```
grep -rn "medical_kb_psychology_v1\|boundary_refer_out\|crisis_line" /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/
```

Results: only mentions in `vitalia/config/brand.yaml` (declared) + `vitalia/backend/src/modules/vitalia/extensions.py` (registered EP-14 placeholder) + `vitalia/backend/tests/unit/test_extensions_register_all.py` (count assertion). No prior implementation. **GATE PASS.**

`scripts/seed_medical_kb.py` did NOT exist before this ticket — T-kb-1 chose a different architecture (pack-internal `__init__.py` exports `DentalKbStore`). No file collision. My orchestrator-style script + dental's per-pack module coexist; both packs registered to EP-14 in `extensions.py` (already present pre-ticket).

Anti-duplication audit vs `marketing_kb_store.py` (precedent): different shape (`kb_pack` + `topic_tags` + `forced_retrieval` + `applies_to_countries` payload vs `category` + `methodology` + `domain`), different scope (per-pack vs global), different vector dim (1536 vs 3072). NOT a mirror — parallel implementation. Lift-shared deferred per ticket scope.

## Step 0.5 — Default flip detection

No `core/config.py` defaults touched. N/A.

## Cross-module systems audit (NO-NEW-LAYER)

- `shared/agent_observability/*` — not touched (KB writes don't emit observability events at seed time; runtime sales_agent writes copilot_trace_event citing chunk_id per RAG citation contract).
- `shared/infrastructure/llm/*` — not touched. Embedder is injected at construction time; production wiring uses `LLMFactory.get_service().get_embedding_model()` (lazy, in `main()`).
- `core/luana-core-copilot/qdrant/marketing_kb_store.py` — precedent consulted; diverged structurally (see anti-duplication audit). Lift-shared deferred.

## TDD RED → GREEN

**RED phase** (tests written first):

1. Wrote 19 tests in `tests/agentic_evals/kb_packs/test_medical_kb_psychology_boundary_chunks.py`:
   - `TestPackArtifactsPresent` (2): manifest.yaml + .md files present.
   - `TestManifestSchema` (3): yaml parseable, declares boundary_chunks + crisis_keywords.
   - `TestChunkCount` (1): pack ≥150 chunks (V-AE-9 baseline).
   - `TestSeedingIdempotent` (1): chunk_id + point_id deterministic across runs; UUIDs parseable.
   - `TestCrisisRefersOut` (4): A1 acceptance — crisis triggers boundary forced top-1 (suicidio/voseo-matarme/autolesion + non-crisis negative).
   - `TestPerCountryReferral` (7): A2 acceptance — per-country crisis_line_AR/CL/MX/CO/PE/BR + US fallback to general.
   - `TestPackRegistration` (1): seed script lists psychology pack.

2. Ran tests → all FAIL (manifest missing, scripts missing) → RED confirmed.

**GREEN phase** (implementation):

1. `manifest.yaml` — pack metadata + 7 boundary_chunks + 25 crisis_keywords (neutro + voseo-tolerant) + topic_tag taxonomy.
2. 12 .md content files — 179 H2-anchored chunks total (target ~200, baseline ≥150 met):
   - `boundaries_referral.md` (5 chunks) — boundary_refer_out_general + 4 referral protocols.
   - `boundaries_crisis.md` (7 chunks) — per-country crisis_line_{AR,CL,MX,CO,PE,BR} + general fallback.
   - `boundaries_setting.md` (12 chunks) — encuadre + confidentiality + emergency protocol.
   - `therapy_approaches_cbt.md` (16 chunks) — TCC overview + indications + techniques + protocols.
   - `therapy_approaches_systemic.md` (17 chunks) — sistémica + couples + family + interventions.
   - `therapy_approaches_gestalt.md` (17 chunks) — gestalt + body work + dream work + polarities.
   - `therapy_approaches_psychoanalysis.md` (20 chunks) — Freud/Klein/Lacan/relational + indications.
   - `condition_descriptions_anxiety.md` (15 chunks) — TAG/pánico/social/TOC/TEPT.
   - `condition_descriptions_depression.md` (17 chunks) — episodes + treatment + suicide assessment.
   - `condition_descriptions_grief.md` (16 chunks) — normal/complicated + perinatal/post-suicide.
   - `condition_descriptions_relationship.md` (18 chunks) — communication + EFT/Gottman + LGBT.
   - `common_questions.md` (19 chunks) — FAQs for clinic_owner + patient education.
3. `scripts/seed_medical_kb.py` — orchestrator with `KB_PACKS` registry (alphabetical to avoid parallel-session merge churn), `load_chunks_from_pack()` H2-parser, `VitaliaMedicalKbStore` Qdrant wrapper, `_FakeEmbedder`-injectable for tests, `seed_all()` best-effort entry.
4. Re-ran tests:
   - First iteration: `chunk_id` UUID assertion failed — chunk_id is human-readable (e.g. `boundary_refer_out_general`), `point_id` is UUIDv5 → adjusted test to assert UUID on `point_id`.
   - Second iteration: crisis test failed — `client.scroll(limit=64)` returned random first 64 of 179 chunks, missing boundary chunks → added `Filter(must=[FieldCondition(key="forced_retrieval", match=MatchValue(value=True))])` to scroll.
   - Third iteration: per-country test failed — query "estoy en crisis, necesito ayuda urgente" wasn't triggering `_detect_crisis()` because manifest lacked standalone "crisis" keyword → appended `crisis`/`en crisis`/`estoy en crisis`/`ayuda urgente` to crisis_keywords.
   - Fourth iteration: TestPerCountryReferral fixture wasn't passing manifest to store → fixed `in_memory_store` fixture in both test classes to load manifest yaml + pass to constructor (consistent with TestCrisisRefersOut fixture).
5. **Final: 19/19 GREEN.**

## Validators

```bash
# V-AE-9 (kb_packs scope — psychology only, my surface):
cd /home/chris/luana-platform/vitalia/backend && \
  .venv/bin/pytest tests/agentic_evals/kb_packs/test_medical_kb_psychology_boundary_chunks.py -v
# → 19 passed in 2.26s

# Ruff check (my files):
.venv/bin/ruff check scripts/seed_medical_kb.py scripts/__init__.py \
  tests/agentic_evals/kb_packs/test_medical_kb_psychology_boundary_chunks.py
# → All checks passed!

# Ruff format check:
.venv/bin/ruff format --check scripts/seed_medical_kb.py scripts/__init__.py \
  tests/agentic_evals/kb_packs/test_medical_kb_psychology_boundary_chunks.py
# → 3 files already formatted
```

V-AE-9 full kb_packs/ directory (my 19 + dental's 11 + dental's 2 fail) → my surface 19/19 PASS. Dental 2/13 FAIL (chunk count 123 < 150 baseline) — **NOT my regression**. Dental ticket T-kb-1 owns that chunk count gap.

## Acceptance evidence

- **A1 — Crisis keyword triggers boundary_refer_out_* chunk forced retrieval (top-1):**
  - `test_crisis_keyword_suicidio_returns_boundary_top1` PASS
  - `test_crisis_keyword_voseo_matarme_returns_boundary` PASS (voseo input from AR persona)
  - `test_crisis_keyword_autolesion_returns_boundary` PASS
  - `test_non_crisis_query_does_not_force_boundary` PASS (negative case)
- **A2 — Per-country emergency line returned based on tenant country:**
  - parametrized 6× over (AR,CL,MX,CO,PE,BR) × expected `crisis_line_<XX>` PASS
  - `test_unknown_country_falls_back_to_general` PASS

## Constraints honored

- ✅ TDD RED→GREEN — wrote tests first.
- ✅ Crisis detection list — Spanish neutro + voseo-tolerant (sales_agent INPUT exception per spanish-text.md R2).
- ✅ Per-country routing via `applies_to_countries` payload filter.
- ✅ DDD: KB lives in `copilot/kb/` (per spec § 1.1 Inside-Out + ticket files_in_scope).
- ✅ Tenant isolation: brand-scope (cross-tenant medical reference, NOT per-tenant PHI). `tenant_id=None` in payload for all generic chunks. Per-tenant private extensions deferred Story 11.bis.
- ✅ Idempotent: stable UUIDv5 point ids derived from `{pack_id}::{source_doc}::{chunk_id}`. Re-run safe.
- ✅ Embedding model `text-embedding-3-large` with `dimensions=1536` (per arch § 7.1).
- ✅ Spanish neutro chrome chunks (sales_agent voice exception preserved at LLM output time, not at KB content time).
- ✅ Best-effort observability — `seed_all()` per-pack try/except.
- ✅ Anti-duplication: precedent audited, divergence justified, lift-shared deferred.

## Decisions honored (per 06-tickets.yaml)

- **D1** — Vitalia subdir at `luana-platform/vitalia/` (Q3=B). All artifacts under that subdir.

## Parallel race protocol notes

- T-kb-1 dental ran in parallel. Both tickets touched `scripts/seed_medical_kb.py` per spec, BUT T-kb-1 chose pack-internal architecture (`medical_kb_dental_v1/__init__.py` exports `DentalKbStore`) and did NOT create the orchestrator script. My T-kb-2 created it from scratch — no merge conflict.
- Both packs are independently registered in `extensions.py::register_all` EP-14 (pre-existing scaffold from T-extensions-1). Both pack collections coexist in Qdrant.
- The 2 dental test failures (`test_chunk_count`, `test_chunk_count_post_upsert`) are T-kb-1's responsibility (123 < 150 baseline). NOT regressed by my work.

## Files created/modified

| Path | Action |
|---|---|
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/manifest.yaml` | NEW |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/boundaries_referral.md` | NEW (5 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/boundaries_crisis.md` | NEW (7 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/boundaries_setting.md` | NEW (12 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/therapy_approaches_cbt.md` | NEW (16 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/therapy_approaches_systemic.md` | NEW (17 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/therapy_approaches_gestalt.md` | NEW (17 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/therapy_approaches_psychoanalysis.md` | NEW (20 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/condition_descriptions_anxiety.md` | NEW (15 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/condition_descriptions_depression.md` | NEW (17 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/condition_descriptions_grief.md` | NEW (16 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/condition_descriptions_relationship.md` | NEW (18 chunks) |
| `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/common_questions.md` | NEW (19 chunks) |
| `vitalia/backend/scripts/__init__.py` | NEW (package marker) |
| `vitalia/backend/scripts/seed_medical_kb.py` | NEW (~430 lines orchestrator) |
| `vitalia/backend/tests/agentic_evals/kb_packs/__init__.py` | NEW |
| `vitalia/backend/tests/agentic_evals/kb_packs/test_medical_kb_psychology_boundary_chunks.py` | NEW (~390 lines, 19 tests) |

Total chunks: **179** (≥150 floor met; ~200 target ~89% achieved).

## Outcome

**done** — all psychology suite GREEN, scope clean, anti-duplication audited, ruff clean.
