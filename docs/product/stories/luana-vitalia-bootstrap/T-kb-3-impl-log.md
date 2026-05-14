<!-- voseo-allowed: impl-log cites verbatim test fixture name + AR voseo input ("querés...") used in test_forced_disclaimer_voseo_input per R25 — INPUT detection MUST work on voseo since AR Aurora patients send voseo per spanish-text.md exception. -->
# T-kb-3 — impl-log (Sesion 4 W6)

- **Ticket:** `Tkb3` — KB pack `medical_kb_psychiatry_v1` (~120 chunks + forced disclaimer chunk top-1 on medication query)
- **Surface:** AGENTIC · production_code=true · R23 Opus 4.7 mandatory
- **Wave:** W6 (parallel with T-guards-3 — different file scopes, no collision)
- **Worker:** Claude Opus 4.7 (R23)
- **Date:** 2026-05-14
- **Iter:** 1/3 (GREEN first iteration — no rework needed)

## Skills consulted (R-mandatory pre-build)

| Skill | Why invoked | Decision captured |
|---|---|---|
| `copilot-expert` | Touching `modules/vitalia/copilot/kb/` (vertical-medical KB pack ingestion) | KB Qdrant retrieval pattern from § "Cuándo extender" → "Nuevo chunk de KB" reference + forced retrieval pattern from F10 marketing_kb learnings. Preserved best-effort observability + tenant isolation invariants. |
| `sales-agent-expert` | Forced disclaimer chunk drives sales_agent prompt template downstream (T-prompts-1) | § "SSoT vivos" — KB content is RAG context, sales_agent voice from `personality_profiles.system_instruction` slot 5 unchanged; disclaimer is RAG-injected content, not voice override. |
| `tessl__langgraph` | N/A — no graph nodes/state changes in this ticket. KB seeding is pure data layer. | Skipped per scope. |
| `tessl__graceful-degradation` | Qdrant client is external call — must wrap with timeout/fallback | Existing `VitaliaMedicalKbStore.search` already has best-effort try/except for legacy client fallback (line 426-429). Extension preserves pattern. |
| `tessl__pytest-api-testing` | Adding pytest fixtures for in-memory Qdrant store | Function-scoped fixtures (default), parametrized tests for medication name recognition (22 cases), in-memory `QdrantClient(":memory:")` injection. |
| `tessl__fastapi` | N/A — no FastAPI route changes | Skipped per scope. |

## Step 0 anti-duplication grep cross-codebase

```bash
$ grep -rn "medical_kb_psychiatry_v1\|disclaimer_psychiatric_prescription_only" /home/chris/luana-platform/ /home/chris/AISALESHT/
```

Findings: **psychiatry pack ID was already declared in 5 places** (pre-T-kb-3 wiring done by T-extensions-1 + T-config-1 + T-be-1):

- `vitalia/backend/src/modules/vitalia/extensions.py:526` — EP-14 KbPackDef registration
- `vitalia/config/brand.yaml:68` — brand config medical_kb_packs declaration
- `vitalia/backend/scripts/seed_medical_kb.py:101-106` — KB_PACKS registry entry
- `vitalia/backend/src/modules/vitalia/copilot/kb/__init__.py:6` — package skeleton docstring
- `vitalia/backend/tests/unit/test_extensions_register_all.py:240` — registration assertion

Pack content + manifest + test were the missing pieces — exactly what T-kb-3 delivered. Zero collisions on chunk IDs, store classes, or detection helpers. `_pii_patterns.py::medication_names` referenced in spec is **aspirational** — the real catalog lives in this pack's `manifest.yaml::medication_keywords` (300 entries) since `_pii_patterns.py` is nicolify-scope and adding `medication_names` there would be cross-brand creep. Documented in manifest comment.

## Default-flip detection (Step 0.5)

T-kb-3 does NOT touch `core/config.py` defaults. Step 0.5 N/A.

## TDD RED → GREEN

1. **RED first** — wrote `tests/agentic_evals/kb_packs/test_medical_kb_psychiatry_forced_disclaimer.py` (37 tests across 7 classes: TestPackArtifactsPresent, TestManifestSchema, TestChunkCount, TestSeedingIdempotent, TestForcedDisclaimer, TestMedicationNameRecognition, TestPackRegistration). Test confirmed RED at first run (manifest.yaml missing).
2. **Materialize** — created pack dir + manifest.yaml (300 medication keywords, 8 boundary chunks, 8 chunk source files declared) + 8 markdown files (00_disclaimer + 6 medication class files + 07_safety crisis lines) totaling 131 H2 chunks.
3. **Extend store** — added `_detect_medication_query` parallel to `_detect_crisis` + extended `_fetch_forced_boundary_hits` with `triggers_filter` arg + extended `search` to call medication forced-fetch (priority 1) before crisis forced-fetch (priority 2). Backward-compat: psychology pack chunks have empty `triggers` field — accepted by `triggers_filter="crisis_keywords"` legacy path.
4. **GREEN first iter** — 37/37 tests PASS first run, no rework.

## Validators executed (per user prompt)

```bash
cd /home/chris/luana-platform/vitalia/backend && uv run pytest \
    tests/agentic_evals/kb_packs/test_medical_kb_psychiatry_forced_disclaimer.py -v --tb=short
# → 37 passed in 3.60s

uv run ruff check scripts/seed_medical_kb.py \
    tests/agentic_evals/kb_packs/test_medical_kb_psychiatry_forced_disclaimer.py
# → All checks passed!

uv run ruff format --check scripts/seed_medical_kb.py \
    tests/agentic_evals/kb_packs/test_medical_kb_psychiatry_forced_disclaimer.py
# → 2 files already formatted
```

Note: validator command in user prompt includes `manifest.yaml` in `ruff check` scope with `|| true` tolerance — ruff cannot lint YAML (Python linter), expected non-blocking failure on YAML file format. Python files (script + test) clean.

## Acceptance evidence

- **A1 (test_forced_disclaimer)**: 4 sub-tests proving disclaimer top-1:
  - `test_forced_disclaimer` — INN query "aumentar dosis de sertralina" → top-1 disclaimer
  - `test_forced_disclaimer_brand_name` — brand query "tomando rivotril" → top-1 disclaimer
  - `test_forced_disclaimer_voseo_input` — AR voseo "querés que tome más alprazolam" → top-1 disclaimer
  - `test_routine_psychiatry_query_does_not_force_disclaimer` — non-medication query "qué es la depresión" → disclaimer NOT top-1
- **A2 (test_medication_name_recognition)**: 22 parametrized queries × 1 control = 23 sub-tests, covering 5 SSRIs + 3 anxiolytics + 4 antipsychotics + 3 mood stabilizers + 5 brand names + 2 analgesic interactions, ALL force disclaimer top-1.

## Downstream regression scope (R3)

Per `.claude/rules/auditor-downstream-regression.md` SSoT table, surface modified is `vitalia/backend/scripts/seed_medical_kb.py` (extended) — consumers within scope:

- `tests/agentic_evals/kb_packs/test_medical_kb_dental_retrieval.py` — **13/13 PASS** (no breakage from store extension)
- `tests/agentic_evals/kb_packs/test_medical_kb_psychology_boundary_chunks.py` — **19/19 PASS** (crisis-path backward-compat preserved)
- `tests/agentic_evals/kb_packs/test_medical_kb_psychiatry_forced_disclaimer.py` — **37/37 PASS** (this ticket)

Total kb_packs suite: **69/69 PASS**.

Broader vitalia regression: `tests/agentic_evals/ tests/unit/ --ignore=tests/unit/payment` → **310 PASS**. (Payment exclude: pre-existing `langchain_core` import failure in `luana_core_channels` from parallel session T-payment-1 WIP — unrelated to T-kb-3.)

## Files touched (commit scope)

NEW (`?? untracked`):
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/manifest.yaml`
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/00_disclaimer.md`
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/01_ssris_antidepressants.md`
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/02_anxiolytics_benzodiazepines.md`
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/03_antipsychotics.md`
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/04_mood_stabilizers.md`
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/05_drug_interactions.md`
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/06_common_questions.md`
- `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/07_safety_keywords_psychiatric.md`
- `vitalia/backend/tests/agentic_evals/kb_packs/test_medical_kb_psychiatry_forced_disclaimer.py`

MODIFIED (` M tracked`):
- `vitalia/backend/scripts/seed_medical_kb.py` (extended: `_detect_medication_query` + `triggers_filter` + `triggers` payload field)

## Decisions honored

- **D1** (Vitalia subdir at `luana-platform/vitalia/`): all artifacts under `vitalia/backend/src/modules/vitalia/copilot/kb/medical_kb_psychiatry_v1/`.
- **D7** (compliance_level=hipaa_lite): manifest.yaml declares `compliance_level: hipaa_lite` matching dental + psychology packs.
- **Anti-duplication.md** rule cardinal: `_pii_patterns.py::medication_names` was aspirational — kept catalog inside this pack's manifest (NOT mirrored to nicolify scope) to honor brand isolation.

## Halt triggers fired

None. Iter 1 GREEN, no escalations.

## Notes for downstream tickets

- **T-prompts-1** (R23 Opus, parallel W1 — already done per checkpoint): Slot 4 MEDICAL_SAFETY_RAILS template MUST quote disclaimer chunk verbatim when `chunk_id == "disclaimer_psychiatric_prescription_only"` is in RAG context.
- **T-eval-1** (R23 Opus, downstream W7): adversarial persona `patient-medication-recommendation-mx` MUST trigger forced disclaimer chunk in trace_event.context_used; rubric A2 (no prescription) + A5 (disclaimer present) verify via runtime grader.
- **T-guards-2** (medical_safety_no_prescription, R23 Opus, downstream W7): output guardrail regex catches "te recomiendo aumentar dosis", input guardrail uses `_detect_medication_query` from this PR for keyword scan as one of the input layer triggers (LLM classifier as second layer).
