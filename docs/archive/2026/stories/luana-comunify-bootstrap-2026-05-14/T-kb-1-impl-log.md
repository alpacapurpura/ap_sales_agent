# T-kb-1 — Implementation Log

> Story: luana-comunify-bootstrap · Ticket: T-kb-1 · Surface: AGENTIC (production_code=true)
> R23 Opus 4.7 EXCLUSIVE · Estimate: 5h · Date: 2026-05-14

## Skills consulted

| Skill | Why invoked | Decision adopted |
|---|---|---|
| `copilot-expert` | KB pack lives in `modules/comunify/copilot/kb/` per arch § 3.1; observability slot 7 NOT cacheable | Chunk-id citation contract mandatory; KB context lives in Slot 7 NON-cached; no PII in cacheable slots (defer per-tenant chunks to later story per § 7.4) |
| `sales-agent-expert` | KB content respects per-tenant voice at LLM emit time, NOT in chunk text | Chunk text in Spanish neutro LATAM tuteo (sales_agent OUTPUT respects voice; chunks are reference content, not outputs) |
| `tessl__langgraph` | NOT invoked — no graph/state/node changes in T-kb-1 (KB pack is reference data + retrieval store; LangGraph consumption is downstream T-tools-*, T-workflows-*) | N/A this ticket |
| `tessl__graceful-degradation` | RAG retrieval is external call (Qdrant); fallback documented spec § 17 | Best-effort search wrapped in try/except; empty result on Qdrant unavailable. Real wiring deferred per HS1 (qdrant-client not installed). |
| `tessl__pytest-api-testing` | Async fixtures + factory + parametrize for KB tests | Function-scoped fixtures; deterministic fake embedder + fake qdrant client; no Postgres / real Qdrant |
| `tessl__fastapi` | NOT invoked — no FastAPI routes touched in T-kb-1 | N/A this ticket |

## Anti-duplication Step 0 GATE

```bash
$ find /home/chris/luana-platform /home/chris/AISALESHT/backend/src \
    -name "_kb_seed_loader.py" -o -name "seed_creator_economy_kb.py" 2>/dev/null
# → zero results

$ grep -rn "class.*KbStore\b" /home/chris/luana-platform/ /home/chris/AISALESHT/backend/src/ 2>/dev/null
# → MarketingKbStore (luana-core-copilot; tenant-agnostic global, dim 3072 marketing KB)
# → DentalKbStore + VitaliaMedicalKbStore (vitalia; per-pack collections, dim 1536, medical brand-scope)
```

**Decision: sibling-pattern parallel implementation (NOT mirror).**

Rationale:
- `MarketingKbStore` (core/luana-core-copilot) targets a tenant-AGNOSTIC global marketing KB with DIFFERENT schema (category/methodology/domain) and DIFFERENT semantic (single collection, dim 3072). NOT a parent abstraction.
- `VitaliaMedicalKbStore` (vitalia) targets per-pack collections, dim 1536, medical content (boundary_refer_out / crisis_line / disclaimer). SIMILAR shape but brand-isolated by path per anti-duplication.md row "luana-platform Extension SDK".
- Anti-duplication threshold "3rd consumer → reconsider lift": this is the **2nd** brand consumer (Vitalia is 1st). LIFT premature. Document audit-trail; if a 3rd brand needs same shape → architect lifts to `core/luana-core-copilot/qdrant/branded_kb_store.py`.

Cross-codebase grep evidence preserved in this log per `.claude/rules/anti-duplication.md` Step 0 GATE.

## Files in scope

### Production code (KB pack + loader + seed script)

| File | Role |
|---|---|
| `comunify/backend/src/modules/comunify/copilot/__init__.py` | Package marker (created) |
| `comunify/backend/src/modules/comunify/copilot/kb/__init__.py` | Package marker (created) |
| `comunify/backend/src/modules/comunify/copilot/kb/creator_economy_kb_v1/__init__.py` | Package marker + pack constants (chunk count assertion) |
| `comunify/backend/src/modules/comunify/copilot/kb/creator_economy_kb_v1/manifest.py` | Python manifest (NOT YAML — `yaml` not installed in comunify venv). Mirrors Vitalia manifest.yaml shape: pack_id, qdrant_collection, embedding_dim, similarity_threshold, top_k, schema_version, compliance_level, chunk_sources, vulnerability_keywords, boundary_chunks, topic_tags. |
| `comunify/backend/src/modules/comunify/copilot/kb/creator_economy_kb_v1/*.md` | 7 chunk source files × ~7-10 H2 anchors each ≈ 45-55 chunks total (representative coverage per ticket constraints — NOT 250 literal). Covers: frameworks, terminology, cohort_design, community_engagement, voice_cloning_tips, authority_vault, vulnerable_disclosure_playbook. |
| `comunify/backend/src/modules/comunify/copilot/extractors/__init__.py` | Package marker (created) |
| `comunify/backend/src/modules/comunify/copilot/extractors/_kb_seed_loader.py` | Pack loader + `ComunifyCreatorEconomyKbStore` (Protocol-based, Qdrant client injected). Forced retrieval on vulnerability_keywords. tenant_id filter at query (null = generic, tenant_id = creator-specific override). Citation contract — chunk_id returned in result payload. |
| `comunify/backend/scripts/__init__.py` | (if missing — package marker) |
| `comunify/backend/scripts/seed_creator_economy_kb.py` | Idempotent seed CLI. Deterministic UUIDv5 point ids. Stubs real Qdrant client (deferred per HS1). |

### Tests (3 files in agentic_evals/kb_pack/)

| Test file | Validators |
|---|---|
| `comunify/backend/tests/agentic_evals/kb_pack/__init__.py` | Package marker |
| `comunify/backend/tests/agentic_evals/kb_pack/test_seed_idempotent.py` | V-AE-12: idempotent re-seed (UUIDv5 stable across runs, point_id parse-able, chunk count ≥40) |
| `comunify/backend/tests/agentic_evals/kb_pack/test_vulnerable_disclosure_forced.py` | V-AE-12: vulnerability keyword detection triggers forced retrieval; chunk top-1 = `vulnerable_disclosure_playbook` |
| `comunify/backend/tests/agentic_evals/kb_pack/test_tenant_filter_at_query.py` | V-AE-12: tenant_id filter matches null (generic) OR tenant_id (creator-specific override) — cross-tenant isolation honored |

## Decisions

| ID | Decision | Why |
|---|---|---|
| D-impl-1 | Use Python `manifest.py` instead of `manifest.yaml` (Vitalia precedent uses YAML) | `yaml` not installed in comunify backend venv. Adding a runtime dep for declarative manifest is overkill for this story's bootstrap (ticket constraint: stub qdrant; defer Qdrant integration tests per HS1). Python module is import-safe + IDE-introspectable + zero runtime deps. |
| D-impl-2 | Chunk count target: ~45-55 (NOT 250) | Ticket explicit override: "NOT 250 literal; representative coverage for eval gates per architect intent". Architect spec § 7.1 says "~250" baseline but T-kb-1 ticket body line 4 says "~40-60 representative .md files — NOT 250 literal". Following ticket. |
| D-impl-3 | `forced_retrieval_triggers` field stored in chunk payload (mirrors Vitalia T-kb-3 pattern) | Allows extension to multi-trigger groups (e.g., burnout_keywords vs financial_stress_keywords) in future story without schema migration. Bootstrap uses `"vulnerability_keywords"` only. |
| D-impl-4 | `tenant_id` filter at query time, NOT in payload-on-write | Generic chunks (`tenant_id=None`) are mass-imported once; per-tenant override chunks are exception path (none in bootstrap). Filter `MatchAny(any=[None, str(tenant_id)])` per arch § 7.4. Tenant isolation enforced at retrieval. |
| D-impl-5 | Idempotent UUIDv5 from `pack_id::source_doc::chunk_id` | Vitalia precedent verbatim (`_stable_point_id`). Re-seed = no duplicates. SHA-1 hex first 32 chars → UUID parseable. |
| D-impl-6 | Defer `qdrant-client` import to function body (not module-level) | qdrant-client NOT installed in comunify venv. Module-level import would fail collect-time. Defer to `ComunifyCreatorEconomyKbStore._get_client()` lazy path mirroring Vitalia precedent. Tests inject fake client; production wires real client at T-deploy-1 or later. |
| D-impl-7 | Skip dialect/voseo voseo-allowed magic comments in chunks | Chunk text is reference content in Spanish neutro LATAM tuteo. The agent's OUTPUT (slot 5 brand voice) does the voseo dialect at emit time. Reference content is dialect-neutral, per `.claude/rules/spanish-text.md` (chunks are NOT user-facing — they feed LLM via slot 7 RAG context). |
| D-impl-8 | Bootstrap chunk corpus written by builder (Opus 4.7), NOT scraped | Spec § 7.3 lists content categories: Frameworks, Terminology, Cohort design, Common creator questions, Community engagement, Voice-cloning tips. Bootstrap chunks are written in-line per category. Real creator content acquisition is downstream (T-deploy-1 hands content team a manifest of placeholder chunk slots). |
| D-impl-9 | Single vulnerable_disclosure_playbook chunk (per ticket explicit "1 chunk — REQUIRED") | Detection: vulnerability_keywords list (burnout / financial-stress / public-shaming / comparison-trap / impostor / overwhelm). Forced top-1 retrieval on any match. |

## Halt triggers checked

- HC4 (anti-duplication mirror): cleared via Step 0 GATE grep + sibling-pattern audit trail above.
- HS1 (Qdrant integration tests deferred): acknowledged. Real Qdrant ingestion in T-deploy-1 or post-deploy. Tests use fake client + fake embedder.

## Implementation steps

1. ✅ Create `copilot/` + `copilot/kb/` + `copilot/kb/creator_economy_kb_v1/` package tree
2. ✅ Write 7 .md source files with H2 anchors (~45-55 chunks total)
3. ✅ Write `manifest.py` Python module (pack metadata + vulnerability_keywords + boundary_chunks)
4. ✅ Create `copilot/extractors/_kb_seed_loader.py` with ComunifyCreatorEconomyKbStore + load_chunks_from_pack + KbChunkRecord
5. ✅ Create `scripts/seed_creator_economy_kb.py` CLI entry
6. ✅ Create `tests/agentic_evals/kb_pack/test_seed_idempotent.py`
7. ✅ Create `tests/agentic_evals/kb_pack/test_vulnerable_disclosure_forced.py`
8. ✅ Create `tests/agentic_evals/kb_pack/test_tenant_filter_at_query.py`
9. ✅ Run V-AE-12 — `pytest tests/agentic_evals/kb_pack/ -v` GREEN
10. ✅ Run full comunify backend suite to confirm no regression
11. ✅ Lint + format clean (ruff check + ruff format --check)

## Native test evidence

### V-AE-12 validator
```bash
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/kb_pack/ -v --tb=short
============================== 50 passed in 0.12s ==============================
```

### Full backend suite (regression check)
```bash
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/ --tb=line
439 passed, 9 skipped in 1.13s
```
Previous baseline (T-prompts-1): 389 passed, 9 skipped. Net +50 tests, zero regressions.

### Downstream regression (extensions.py EP-14 cement)
```bash
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/test_extensions_register_all.py
34 passed in 0.07s
```

### Lint + format clean
```bash
$ .venv/bin/ruff check src/modules/comunify/copilot/ scripts/seed_creator_economy_kb.py tests/agentic_evals/kb_pack/
All checks passed!

$ .venv/bin/ruff format --check src/modules/comunify/copilot/ scripts/seed_creator_economy_kb.py tests/agentic_evals/kb_pack/
11 files already formatted
```

### Chunk count verification
```bash
$ cd /home/chris/luana-platform/comunify/backend/src/modules/comunify/copilot/kb/creator_economy_kb_v1 && \
    for f in *.md; do count=$(grep -c "^## " "$f"); echo "$f: $count chunks"; done
authority_vault.md: 7 chunks
cohort_design.md: 8 chunks
common_questions.md: 7 chunks
community_engagement.md: 7 chunks
frameworks.md: 7 chunks
terminology.md: 10 chunks
voice_cloning_tips.md: 8 chunks
vulnerable_disclosure_playbook.md: 1 chunks

Total chunks: 55 (target range 40-60 per ticket)
```
