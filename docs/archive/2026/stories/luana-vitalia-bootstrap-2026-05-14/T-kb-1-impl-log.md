# T-kb-1 — vitalia medical_kb_dental_v1 KB pack — impl log

**Story:** luana-vitalia-bootstrap
**Ticket:** T-kb-1 (R23 Opus 4.7 production AGENTIC code)
**Date:** 2026-05-14
**Owner:** Claude Opus 4.7 builder-agentic
**Estimate:** 4h
**Decision class:** D1 (subdir layout)
**Validators:** V-AE-9

---

## Step 0 GATE — skills consulted

Per anti-duplication.md + R23 mandate.

| Skill | Why invoked | Decision |
|---|---|---|
| `copilot-expert` (loaded via prompt) | Touching `modules/vitalia/copilot/kb/` — KB pack is copilot-side surface (extractors + workflows + KB) | Reused MarketingKbStore SSoT pattern from luana_core_copilot (lazy init, stable_id UUIDv5, contextual chunking) but built tenant-aware variant DentalKbStore (per-pack collection, tenant_id payload filter). Lift-shared to BasePerPackKbStore deferred to T-kb-3 (need 3 packs to confirm shared abstraction). |
| `sales-agent-expert` (loaded via prompt) | KB pack consumed by sales_agent at retrieval time → understand RAG contract + slot architecture | Slot 7 KB_CONTEXT_RAG NOT cached. Citation contract: chunk_id MUST land in trace_event.context_used. Score threshold 0.72 is per-spec § 9. Forced retrieval is psychiatry-only (T-kb-3) — dental pack has NO forced retrieval, simpler search path. |
| `tessl__langgraph` (loaded via prompt) | NOT INVOKED — no graph code in T-kb-1 (KB pack is pure data + Qdrant wrapper, retrieval consumed by graph nodes elsewhere) | N/A |
| `tessl__graceful-degradation` (loaded via prompt) | DentalKbStore wraps external Qdrant calls — needs lazy init + explicit failure mode | Constructor injection (`client=`, `embedder=`) mandatory at runtime. `_get_client()` raises RuntimeError if no client injected (loud failure beats silent fallback). Tests inject `QdrantClient(":memory:")` + stub embedder — no network, no flakiness. |
| `tessl__pytest-api-testing` (loaded via prompt) | New test file `tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py` | Function-scope fixture for in-memory QdrantClient (clean state per test). Factory helpers `_generic_chunk()` + `_tenant_chunk()` for builder pattern. `pytest.skip(allow_module_level=True)` for qdrant_client missing fallback. |
| `tessl__fastapi` (loaded via prompt) | NOT INVOKED — no FastAPI routes in T-kb-1 (KB pack is internal infra, not exposed via HTTP) | N/A |
| `claude-api` (NOT in prompt skills) | Not invoked — no Anthropic SDK / cache_control changes in T-kb-1 | N/A |

---

## Anti-duplication grep (Step 0 evidence)

```bash
$ grep -rln "medical_kb_dental_v1\|vitalia_medical_kb_dental_v1" /home/chris/luana-platform/ 2>/dev/null
# only references found:
#   vitalia/config/brand.yaml                              (config declaration)
#   vitalia/backend/tests/unit/test_extensions_register_all.py  (registration test)
#   vitalia/backend/src/modules/vitalia/extensions.py      (CC-4 EP-14 registration)
#   vitalia/backend/src/modules/vitalia/copilot/kb/__init__.py  (skeleton docstring)

$ grep -rln "medical_kb_dental_v1\|vitalia_medical_kb_dental_v1" /home/chris/AISALESHT/backend/src/ 2>/dev/null
# (empty — zero collisions)

$ grep -rln "class DentalKbStore\|class DentalKbChunk" /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/ 2>/dev/null
# (empty — both classes NEW)
```

**Verdict:** zero collisions. Pattern reuses `MarketingKbStore` SSoT (luana_core_copilot/qdrant) — DentalKbStore is a per-pack tenant-aware variant, NOT a mirror (different invariants per spec § 7.1).

---

## Default flip detection (Step 0.5)

NONE. T-kb-1 introduces no feature flag flips. Pure new infra.

---

## Cross-module systems audit (NO-NEW-LAYER)

Audited cross-codebase (per architect's NO-NEW-LAYER rule):

- `luana_core_copilot.infrastructure.qdrant.marketing_kb_store::MarketingKbStore` — closest SSoT. CONSIDERED for direct reuse, but rejected:
  - `MarketingKb` is global singleton collection (no tenant_id field, no per-pack collections)
  - `MarketingKb` vector dim is 3072 (dental needs 1536 per spec § 7.1)
  - `MarketingKb` has methodology/category/domain enums (curated by Nicolify staff — irrelevant to medical KB)
  - Spec § 9.4 mandates per-pack tenant-aware retrieval semantics
- **Decision:** EXTEND (subclass) rejected because MarketingKb's `payload()` schema diverges. NEW class `DentalKbStore` with the SAME architectural invariants (lazy init, stable_id UUIDv5, contextual chunking). Lift-shared to `BasePerPackKbStore` deferred to T-kb-3 — need all 3 packs (dental, psychology, psychiatry) to confirm shared abstraction.
- IMPL-LOG entry "Why existing didn't work": file:line evidence above.

---

## Implementation order (Inside-Out per backend-ddd.md)

T-kb-1 is *infrastructure* layer (KB pack as Qdrant store wrapper) + *bundled data* (markdown chunks). No domain entities, no application services touched.

```
vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_dental_v1/
├── __init__.py              # DentalKbChunk dataclass + DentalKbStore wrapper + load_dental_kb_chunks() loader
├── manifest.yaml            # SSoT metadata (pack_id, qdrant_collection, dim, threshold, etc.)
├── 01_procedures.md         # 32 chunks (procedures: profilaxis, endodoncia, ortodoncia, implantes, etc.)
├── 02_materials.md          # 31 chunks (resinas, amalgamas, zirconio, brackets, anestésicos, etc.)
├── 03_recovery.md           # 30 chunks (post-op care, cicatrización, higiene)
├── 04_common_questions.md   # 30 chunks (FAQ pre-agendamiento)
└── 05_complications.md      # 28 chunks (alveolitis, periimplantitis, derivación urgente)

TOTAL: 151 chunks (≥150 baseline V-AE-9 A1)

vitalia/backend/tests/agentic_evals/kb_packs/
└── test_medical_kb_dental_retrieval.py   # 13 tests covering A1, A2, A3
```

---

## TDD trace (RED → GREEN)

### RED phase
1. Wrote `test_medical_kb_dental_retrieval.py` first with 13 tests covering A1 (chunk count + post-upsert), A2 (tenant filter), A3 (citation contract + top-k + threshold), idempotency invariants, manifest sanity.
2. Initial run: `pytest collected 0 items / 1 skipped` (qdrant_client not installed → module-level skip).
3. Installed qdrant_client>=1.10 via `uv pip install`. Re-ran: `ERROR cannot import 'DENTAL_KB_PACK_ID' from 'medical_kb_dental_v1'` — confirmed RED.

### GREEN phase
1. Wrote `__init__.py` with `DentalKbChunk` (frozen dataclass) + `DentalKbStore` (Qdrant wrapper, lazy init) + `load_dental_kb_chunks()` (markdown parser).
2. Wrote `manifest.yaml` with pack_id, qdrant_collection, vector_size=1536, default_score_threshold=0.72, default_top_k=5, version=1.
3. Wrote 5 markdown files (~30 chunks each) totaling 151 chunks.
4. Ran tests → 13/13 PASS.
5. Initially used `---chunk---` delimiter parser. After review of T-kb-2's `seed_medical_kb.py`, refactored to `## H2` anchor parsing for parity with T-kb-2's `_split_md_into_h2_chunks()`.
6. Aligned `stable_id()` derivation with T-kb-2's `_stable_point_id()` (format: `SHA1({pack_id}::{source_doc}::{anchor})[:32]` → UUIDv5). Removed `version` from seed.
7. Verified parity: 151/151 chunk_ids match between my `DentalKbChunk.stable_id()` and T-kb-2's `_stable_point_id()` for the same input.

### REFACTOR phase
1. Stripped intro segment (everything before first `## H2`) — file-level metadata not indexable.
2. Added `chunk_anchor` field to `DentalKbChunk` for semantic chunk_ids.
3. Lint cleanup: removed unused `QdrantClient as _QdrantClient` import; ruff format applied.

---

## T-kb-2 parallel race handling

**Race detected at scripts/seed_medical_kb.py write time:** when about to create the seed script, found T-kb-2 already created it with `KB_PACKS` list including dental pack registration at index 0 (alphabetical: dental < psychiatry < psychology).

**Resolution per parallel-safety.md M8 (extend, no destroy):**
- Did NOT touch `scripts/seed_medical_kb.py` (T-kb-2 owns it; it already mounts dental pack).
- Refactored my `__init__.py` to use the SAME `## H2` anchor convention + SAME `_stable_point_id` formula as T-kb-2's seed script → unified chunk identity across loaders.
- Verified end-to-end: T-kb-2's `seed_all()` flow loads my dental pack manifest + chunks correctly + indexes 151 chunks via in-memory Qdrant.

**Post-write verification:** T-kb-2 commit `592df20` landed during my work. Confirmed:
- `scripts/seed_medical_kb.py` committed (T-kb-2 owns)
- `tests/agentic_evals/kb_packs/__init__.py` committed empty (matches my pre-create)
- `tests/agentic_evals/kb_packs/test_medical_kb_psychology_boundary_chunks.py` committed (T-kb-2)
- `src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/` committed (T-kb-2)

Ran joint test suite: **32 tests pass (13 mine + 19 T-kb-2's)** — peaceful coexistence.

---

## Acceptance criteria evidence

### A1 — Qdrant collection has ≥150 chunks post-seed

**Test:** `test_chunk_count` + `test_chunk_count_post_upsert`

```
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/python -c "
from src.modules.vitalia.copilot.kb.medical_kb_dental_v1 import load_dental_kb_chunks
print('Total chunks:', len(load_dental_kb_chunks()))
"
Total chunks: 151
```

PASS — 151 chunks ≥ 150 baseline. Distribution:
- 01_procedures.md: 32 chunks (clinical procedures + materials)
- 02_materials.md: 31 chunks (dental materials reference)
- 03_recovery.md: 30 chunks (post-op care + healing timelines)
- 04_common_questions.md: 30 chunks (FAQ pre-agendamiento)
- 05_complications.md: 28 chunks (complications + when-to-derive-to-doctor — CRITICAL safety chunks)

### A2 — Tenant_id payload filter returns generic + tenant-specific chunks

**Test:** `test_tenant_filter` + `test_chunk_payload_includes_tenant_id`

Setup: 3 generic chunks (tenant_id=None) + 2 tenant-A chunks + 1 tenant-B chunk, all about same topic. Query as tenant A → assert receives 3 generic + 2 tenant-A. NO tenant-B chunks. Query as tenant B → assert receives 3 generic + 1 tenant-B. NO tenant-A chunks.

PASS — cross-tenant isolation verified. Per spec § 9.4 invariant.

Note on implementation: `Qdrant MatchAny` does NOT match `None` payload values. Used over-fetch + Python-side filter pattern (limit*5 fetched, filtered to caller's tenant_id + None). Documented in search() docstring. Future optimization possible with Qdrant `Filter(should=[null_match, value_match])` if perf measurable.

### A3 — RAG retrieval top-5 + similarity ≥0.72 + citation contract

**Test:** `test_citation_contract` + `test_top_k_default_is_5` + `test_score_threshold_default_is_0_72`

- `chunk_id` always exposed in search hits (string-stable, derived from `_stable_point_id`)
- `score` always exposed (float for similarity threshold enforcement)
- `source_doc` + `text` always exposed (provenance for trace_event)
- Default `limit=5` per spec § 7.5
- Default `score_threshold=0.72` per spec § 9 + manifest

PASS — citation contract fully satisfied; downstream consumer (sales_agent) records `chunk_id` in `copilot_trace_event.context_used` per spec.

---

## Validators run

```
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/pytest tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py -v --tb=short
============================= test session starts ==============================
collected 13 items

tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_chunk_count PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_chunk_count_post_upsert PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_pack_id_constant PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_qdrant_collection_constant PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_vector_size_constant PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_tenant_filter PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_chunk_payload_includes_tenant_id PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_citation_contract PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_top_k_default_is_5 PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_score_threshold_default_is_0_72 PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_chunk_stable_id_is_deterministic PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_reseed_does_not_create_duplicates PASSED
tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py::test_manifest_yaml_exists PASSED

============================== 13 passed in 1.01s ==============================
```

```
$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/ruff check src/modules/vitalia/copilot/kb/medical_kb_dental_v1/ tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py
All checks passed!

$ cd /home/chris/luana-platform/vitalia/backend && .venv/bin/ruff format --check src/modules/vitalia/copilot/kb/medical_kb_dental_v1/__init__.py tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py
2 files already formatted
```

V-AE-9 PASS (entire kb_packs test suite green: 32 tests across both packs).

---

## Tenant isolation invariants

- `DentalKbChunk.tenant_id` defaults to `None` (generic chunk, visible all tenants).
- `DentalKbChunk.payload()` renders `tenant_id` as `str(UUID) | None` for stable JSONB equality across Qdrant payload index implementations.
- `DentalKbStore.search(tenant_id=...)` filters payload — generic + tenant-specific chunks merged, OTHER tenants' chunks excluded.
- Cross-tenant leak test enforced (`test_tenant_filter`).

---

## Idempotency invariants

- `DentalKbChunk.stable_id()` deterministic UUIDv5 derived from `pack_id + source_doc + chunk_anchor` (matches T-kb-2's `_stable_point_id()`).
- `upsert_chunks()` uses stable_ids — re-runs overwrite in place, no duplicates.
- Test enforced (`test_reseed_does_not_create_duplicates`, `test_chunk_stable_id_is_deterministic`).

---

## Observability hooks

KB store writes are infra calls. No direct trace_event emission from DentalKbStore; downstream consumer (sales_agent) emits `rag_retrieval` / `rag_no_match` trace events with `chunk_id` citations from search hits.

---

## Constraints honored

- ✅ Spanish neutro LatAm (chunk text uses tuteo / clinical Spanish)
- ✅ Tenant isolation per `.claude/rules/tenant-isolation.md`
- ✅ Anti-duplication per `.claude/rules/anti-duplication.md` (audited, lift-deferred to T-kb-3)
- ✅ TDD per `.claude/rules/tdd-mandatory.md` (RED → GREEN → REFACTOR)
- ✅ R23 Opus 4.7 production AGENTIC code per `05-guidelines.md` § 0
- ✅ Native WSL execution (NO Docker for tests/lint per AGENTS.md)
- ✅ Idempotent ingestion (stable_id UUIDv5)
- ✅ Lazy init pattern per F4 gotcha (no Qdrant connection at module-import)
- ✅ Parallel-safety M8 (T-kb-2's seed_medical_kb.py untouched, harmonized via stable_id format)

---

## Files modified

```
A vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_dental_v1/__init__.py
A vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_dental_v1/manifest.yaml
A vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_dental_v1/01_procedures.md
A vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_dental_v1/02_materials.md
A vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_dental_v1/03_recovery.md
A vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_dental_v1/04_common_questions.md
A vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_dental_v1/05_complications.md
A vitalia/backend/tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py
```

UNTOUCHED (T-kb-2 owns, parallel-safety):
```
- vitalia/backend/scripts/seed_medical_kb.py
- vitalia/backend/tests/agentic_evals/kb_packs/__init__.py
- vitalia/backend/tests/agentic_evals/kb_packs/test_medical_kb_psychology_boundary_chunks.py
- vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychology_v1/
```

UNTOUCHED (other parallel sessions WIP):
```
- core/DEFERRED-FILES.md
- core/luana-core-platform/src/luana_core_platform/{infrastructure/model_registry.py,links/ports/calendar.py}
- core/tests/architecture/test_*.py (8 files)
- pyproject.toml
- nicolify/backend/uv.lock
- vitalia/backend/uv.lock
- vitalia/backend/tests/integration/__init__.py
```

NOTE: vitalia/backend/uv.lock has updates from `uv pip install qdrant-client` (added 5 deps: qdrant-client, grpcio, h2, hpack, hyperframe, numpy, portalocker, protobuf, urllib3). Lock file owned by infra session — not committed by me.

---

## Iter log

| iter | action | outcome |
|---|---|---|
| 1 | Initial RED test write | 13 tests collected, 1 skipped (no qdrant_client) |
| 1 | Installed qdrant_client>=1.10 | tests now error on missing imports — confirmed RED |
| 1 | Wrote __init__.py + manifest.yaml + 5 markdown files | 13 tests run, 1 fail (chunk_count: 146 < 150) |
| 1 | Added 4 chunks across 4 files | 151 chunks, 13/13 PASS GREEN |
| 1 | Refactor: H2 anchor parsing for T-kb-2 parity | 151 chunks unchanged, 13/13 PASS, stable_id parity 151/151 |
| 1 | Lint fix: removed unused import | ruff clean |
| 1 | Final verification: full kb_packs suite | 32/32 PASS (mine + T-kb-2) |

Iter cap not reached — closed in iter 1.

---

## Post-merge follow-ups (not in T-kb-1 scope)

1. **T-kb-3 LIFT-SHARED opportunity**: when psychiatry pack lands, confirm 3 packs share enough structure → extract `BasePerPackKbStore` to luana_core_copilot or vitalia/backend/.../kb/_shared/. Update DentalKbStore + PsychologyKbStore + PsychiatryKbStore to subclass.
2. **Real Qdrant integration**: composition root in vitalia BE startup (not in T-kb-1 scope) wires production `QdrantClient(url=settings.QDRANT_URL)` + real `OpenAIEmbeddings(model="text-embedding-3-large", dimensions=1536)`. T-kb-2's `seed_medical_kb.py::main()` already drafted this path.
3. **Per-tenant clinic chunks**: Story 11.bis or later — clinic_owner upload UI + ingestion pipeline for clinic-specific protocols (chunks with `tenant_id=specific_uuid`).
4. **Vitalia pyproject.toml**: add `qdrant-client>=1.10` declaratively (parallel session may already do this; deferred to avoid race).

---

## Citation contract verification (V-AE-9 A3)

Every search hit dict from `DentalKbStore.search()` exposes:
- `chunk_id`: stable UUIDv5 string (citation in `copilot_trace_event.context_used`)
- `score`: float (similarity threshold gate)
- `text`: full chunk text (LLM context injection)
- `source_doc`: filename (provenance for audit log)
- `chunk_anchor`: H2 heading (semantic citation, more useful than UUID for human review)
- `topic_tags` + `procedure_codes`: optional structured metadata
- `kb_pack`: `"medical_kb_dental_v1"` (pack provenance)

Downstream sales_agent specialist receives `list[dict]` and emits per spec § 12.1 trace event:

```python
TraceEvent(
    event_type="rag_retrieval",
    metadata={
        "chunk_ids": [hit["chunk_id"] for hit in retrieved],
        "kb_pack": "medical_kb_dental_v1",
        "tenant_id": ctx.tenant_id,
        "scores": [hit["score"] for hit in retrieved],
        # NO PII — chunk text not in trace metadata
    },
)
```

Anti-hallucination grader (per spec § 13.2 `no-hallucination.md` rubric) checks chunk_ids presence in `context_used` field. Future eval coverage in T-eval-1.
