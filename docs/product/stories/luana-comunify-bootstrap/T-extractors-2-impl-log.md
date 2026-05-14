# T-extractors-2 — impl-log

**Story:** luana-comunify-bootstrap
**Ticket:** T-extractors-2 (AGENTIC, production_code=true, **R23 Opus 4.7 mandatory**)
**Estimate:** 4h · **Spent:** ~2h
**Builder:** builder-agentic (Opus 4.7 1M)
**Started:** 2026-05-14 (UTC)
**Closed:** 2026-05-14 (UTC)

---

## Step 0 GATE — Skills Consulted

| Skill | Reason invoked | Decision |
|---|---|---|
| `copilot-expert` | Extractor lives under `comunify/.../copilot/extractors/` — parallel pattern to T-extractors-1. | EXTEND `BaseExtractionOrchestrator` pattern. Best-effort observability writes via `try/except + structlog.warning`. Tenant_id forwarded to every side-effect collaborator. |
| `sales-agent-expert` | No sales_agent surface touched directly, but cost-recorder canonicalization (`pop_cost(litellm_call_id)` per PI-12 S1 T-1 cement) honored. | Cost bridge via lazy import of `luana_core_observability.recording.cost_recorder.pop_cost`. `None` returns surface as "cost_unknown" warnings — NEVER default to 0 USD silently. |
| `tessl__langgraph` | N/A — no StateGraph in this extractor. LangGraph wraps wave-based orchestrator only at higher level (cohort/community workflows, separate tickets). | Skipped per scope. |
| `tessl__graceful-degradation` | Every external call (LLM service) needs timeout + fallback. | Every wave wrapped in `asyncio.wait_for(timeout=wave.timeout_sec + 2.0)` + per-wave exception isolation (timeout → degraded confidence + warning; exception → empty wave + warning). All 4 side-effects (repo, qdrant, outbox, audit) isolated in independent `try/except` blocks. |
| `tessl__pytest-api-testing` | Async fixtures factory patterns. | `_build_extractor()` factory + FIFO `FakeLLMResponseSpec` queues per role. No real DB. Function-scoped fixtures. `pytest.mark.asyncio` (auto-mode via pyproject). |
| `tessl__fastapi` | N/A — no FastAPI route in this ticket. | Skipped per scope. |
| `anti-duplication.md` (rule, not skill) | Mandatory cross-codebase grep BEFORE creating any new file. | Verified zero collisions for `AuthorityVaultExtractor`, `AuthorityVaultExtractedV1`, `Credential`, `CaseStudy`, `PressMention`, `SocialProofSignals`, `Award`, `SpeakingEngagement`. `PressMentionResponse`/`AwardResponse` existing in `api/dtos/authority_vault_dtos.py` are API-layer Response DTOs — DIFFERENT purpose. Extractor primitives live in `_schemas.py` as domain-level extraction-output entities. EXTEND existing `_schemas.py` (M8 — never replace). Re-export `_LLMResponse` from sibling `offer_ladder_advisor.py` to keep N=1 source-of-truth inside the comunify extractors package; lift-to-shared deferred to 3rd consumer surface. |

---

## Step 0.5 — Default-flip detection

NO `core/config.py` defaults flipped in this ticket. R23 + R26 not triggered. No flag inventory update needed.

---

## Anti-duplication pre-write audit (verbatim grep evidence)

```bash
# Cross-codebase grep — luana-platform + AISALESHT
$ grep -rn "class AuthorityVaultExtractor\|class AuthorityVaultExtractedV1\|class Credential\b\|class CaseStudy\b\|class PressMention\b\|class SocialProofSignals\|class Award\b" \
  /home/chris/AISALESHT/backend/src/ /home/chris/luana-platform/ 2>/dev/null
# (only matches: api/dtos/authority_vault_dtos.py::PressMentionResponse + AwardResponse — DIFFERENT purpose)

$ grep -rn "AuthorityVaultExtractor\|AuthorityVaultExtractedV1" \
  /home/chris/AISALESHT/backend/ /home/chris/luana-platform/ 2>/dev/null
# (only matches: docs/product/stories/luana-comunify-bootstrap/01-spec.md
#                docs/product/stories/luana-comunify-bootstrap/02-design-agentic.md
#                docs/product/stories/luana-comunify-bootstrap/03-arch-agentic.md
#                docs/product/stories/luana-comunify-bootstrap/06-tickets.yaml
#                comunify/config/brand.yaml::extractors[]
#                comunify/backend/src/modules/comunify/extensions.py::EP-7 placeholder
#                comunify/backend/tests/test_extensions_register_all.py::test_ep7_extractors_count_two
#                comunify/backend/src/modules/comunify/copilot/__init__.py
#                comunify/backend/src/modules/comunify/copilot/extractors/__init__.py
#                comunify/backend/tests/agentic_evals/extractors/__init__.py)
```

**Verdict:** zero code collisions. EP-7 / brand.yaml / extensions.py / docs simply reference the symbol name — none implement it. All NEW.

---

## Files touched

### Created

| Path | Lines | Purpose |
|---|---|---|
| `luana-platform/comunify/backend/src/modules/comunify/copilot/extractors/authority_vault_extractor.py` | ~825 | `AuthorityVaultExtractor` class — 4-wave extension of `BaseExtractionOrchestrator`. |
| `luana-platform/comunify/backend/tests/agentic_evals/extractors/test_authority_vault_extractor.py` | ~830 | 33 tests covering A1-A9 acceptance + defensive paths + schema cement. |

### Extended (no replacement — M8 rule honored)

| Path | Change |
|---|---|
| `luana-platform/comunify/backend/src/modules/comunify/copilot/extractors/_schemas.py` | Added 7 NEW Pydantic primitives: `Credential`, `CaseStudy`, `PressMention`, `SpeakingEngagement`, `Award`, `SocialProofSignals`, `AuthorityVaultExtractedV1`. Updated docstring header to reflect both T-extractors-1 + T-extractors-2 sources. Existing `OfferLadderAdvisor` family symbols untouched. |
| `luana-platform/comunify/backend/src/modules/comunify/copilot/extractors/__init__.py` | Updated docstring: "T-extractors-2 (3-wave)" → "T-extractors-2 (4-wave)" + added authority_vault_extractor.py to active modules list. |
| `AISALESHT/.claude/rules/auditor-downstream-regression.md` | 3 NEW rows in SSoT table for comunify extractors (R3 downstream-regression rule). |

---

## Implementation summary

### Class structure

```
AuthorityVaultExtractor(BaseExtractionOrchestrator)
├── log_prefix = "comunify_authority_vault_extractor"
├── default_wave_delay_seconds = 0.0
├── __init__(llm_service, authority_vault_repo?, qdrant_indexer?, outbox?, audit_log?, cost_budget_usd)
├── _define_waves() → 4 ExtractionWave (Sonnet/Sonnet/Haiku/Sonnet)
├── run(tenant_id, source_text) → AuthorityVaultExtractedV1
├── _run_one_wave(wave, prompt_inputs) → wave result dict
├── _absorb_wave_result(...) → folds into aggregated state
├── _resolve_wave_cost(response, wave_name) → Decimal | None
├── _parse_wave_json(content, wave_name) → dict (tolerant to fences)
├── _merge_outputs(wave_outputs, wave_confidences, wave_warnings) → AuthorityVaultExtractedV1
├── _merge_and_save(extracted, tenant_id, ...) → 4 best-effort side-effects (repo + qdrant + outbox + audit)
└── _build_pending_rows(extracted, tenant_id, extraction_id) → list[dict] (polymorphic kind mapping)
```

### 4-wave pipeline (per 03-arch-agentic § 5.2)

| Wave | Name | Role | Timeout | Cost ceiling |
|---|---|---|---|---|
| W1 | credentials_and_awards | reasoning (Sonnet 4.6) | 30s | $0.030 |
| W2 | case_studies | reasoning (Sonnet 4.6) | 30s | $0.030 |
| W3 | press_and_social_proof | nano (Haiku 4.5) | 30s | $0.015 |
| W4 | validate_and_merge | reasoning (Sonnet 4.6) | 25s | $0.010 |

Total budget cap: **$0.08 USD per extraction** (V-AE-8 SSoT, 03-arch-agentic § 5.2). Per-wave caps sum ≤ budget.

### Side-effects (best-effort, isolated try/except)

1. `authority_vault_repo.save_pending_ratification(tenant_id, rows)` — pre-fills `comunify_authority_vault_items` rows with `status='extracted_pending_ratification'`. Creator reviews + ratifies via Brand Studio before activation. Polymorphic single-table mapping: 4 kinds (credentials / case_studies / press_mentions / awards) + `content.subkind` discriminator for speaking_engagements within press_mentions.
2. `qdrant.index_authority_vault_extracted(tenant_id, extraction_id, payload)` — indexes sanitised payload to per-tenant Qdrant collection (RAG context for `nurture_via_authority_content` tool).
3. `outbox.publish(AuthorityVaultExtractedV1, tenant_id, sanitised_payload)` — domain event emission. **Payload carries ONLY counts + confidence + cost + duration — NEVER raw source_text.**
4. `audit_log.log(authority_vault_extracted, tenant_id, sanitised_payload)` — includes `needs_manual_review` flag when `confidence_score < MIN_ACCEPTABLE_CONFIDENCE (0.7)`.

### PII handling (defense-in-depth)

Source_text typically carries creator-public bio content (intentionally self-disclosed). Defense-in-depth invariant:

- Outbox + audit payloads carry **only** structured statistics — never any string slice of source_text.
- `sanitize_payload` applied to every observability write as final guard.
- Test `test_pii_in_bio_masked_in_outbox_payload` injects `anabella@example.com` + `+54 9 11 5555-5555` into the source_text and asserts NEITHER substring appears in outbox.published[].payload nor audit.logged[].payload.

### Tenant isolation (R2)

- `tenant_id` propagates to every collaborator (verified by `test_tenant_id_propagates_to_all_collaborators`).
- Cross-tenant runs do not leak state (verified by `test_cross_tenant_isolation_no_leak_across_runs`).
- Repo `save_pending_ratification` asserts row.tenant_id == call.tenant_id (defense-in-depth invariant in the fake; production repo enforces via `WHERE tenant_id =` clauses).

### Anti-duplication intra-package

`_LLMResponse` re-imported FROM `offer_ladder_advisor.py` (sibling extractor). Anti-duplication threshold N=2 across siblings → resolved by intra-package re-export (cheaper than mirror, deferred lift-to-shared to 3rd consumer per `_schemas.py` SSoT note). `_sanitize_payload` + `_pop_cost` lazy-import wrappers ARE mirrored from sibling — same content, different file — because they protect against the optional `luana_core_observability` import in minimal test environments. Lift target identified: extract a shared `_lazy_observability.py` helper when 3rd extractor surfaces.

---

## Test results

```
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/extractors/ -v --tb=short
============================== 63 passed in 0.15s ==============================

# 33 NEW tests (T-extractors-2) + 30 pre-existing (T-extractors-1) = 63 total
```

Specific NEW coverage breakdown:

| Acceptance | Tests | Status |
|---|---|---|
| A1 — subclass of BaseExtractionOrchestrator | `test_authority_vault_extractor_subclasses_base_orchestrator`, `test_extractor_inherits_base_methods`, `test_extractor_log_prefix_is_comunify_specific`, `test_wave_definitions_match_spec` | ✅ 4/4 |
| A2 — 4 waves complete + merge | `test_4_wave_pipeline_happy_path`, `test_wave_called_with_correct_role_routing` | ✅ 2/2 |
| A3 — bio with 3 credentials + 2 case studies + 1 press | `test_4_wave_pipeline_happy_path` (asserts counts + values) | ✅ |
| A4 — empty bio: no false positives | `test_empty_bio_returns_empty_extraction_no_false_positives` | ✅ |
| A5 — cost ≤$0.08 USD | `test_cost_budget_happy_path`, `test_cost_budget_exceeded_recorded_as_warning`, `test_cost_unknown_wave_does_not_break_run` | ✅ 3/3 |
| A6 — PII sanitisation | `test_pii_in_bio_masked_in_outbox_payload` | ✅ |
| A7 — schema_version=1 frozen | `test_schema_version_is_literal_1_frozen` + 5 enum/range cement tests | ✅ 6/6 |
| A8 — cross-tenant isolation | `test_tenant_id_propagates_to_all_collaborators`, `test_cross_tenant_isolation_no_leak_across_runs` | ✅ 2/2 |
| A9 — pending-ratification status | `test_pre_fills_authority_vault_repo_with_pending_ratification_status` | ✅ |
| Defensive paths | `test_returns_extraction_v1_even_on_all_wave_failures`, `test_partial_wave_failure_yields_partial_extraction`, `test_malformed_credential_dropped_with_warning`, `test_wave_invalid_json_yields_empty_wave_with_warning` | ✅ 4/4 |
| Best-effort side-effects isolation | `test_repo_failure_does_not_raise`, `test_qdrant_failure_isolated`, `test_outbox_failure_isolated`, `test_audit_failure_isolated`, `test_audit_log_records_extraction_event`, `test_low_confidence_triggers_manual_review_flag_in_audit`, `test_outbox_emits_authority_vault_extracted_v1`, `test_qdrant_indexed_when_supplied` | ✅ 8/8 |

V-AE-8 GREEN.

### Quality gates

```
$ .venv/bin/ruff check src/modules/comunify/copilot/extractors/ tests/agentic_evals/extractors/ --no-cache
All checks passed!

$ .venv/bin/ruff format --check src/modules/comunify/copilot/extractors/ tests/agentic_evals/extractors/
8 files already formatted
```

### Broader regression (entire comunify suite)

```
$ .venv/bin/pytest tests/ --tb=short
584 passed, 9 skipped in 1.47s
```

Zero regressions in EP-7 registration test, downstream tools (`test_nurture_via_authority_content.py`), repo unit tests, or service tests.

---

## Iteration log

| Iter | Action | Result |
|---|---|---|
| 1 | Wrote 33-test RED suite + extractor implementation in one pass | 32/33 GREEN, 1 FAIL on `test_cross_tenant_isolation_no_leak_across_runs` |
| 2 | Fixed test bug: `{**_happy_specs(), **_empty_bio_specs()}` was clobbering reasoning+nano keys (dict merge overrides same key). Switched to explicit per-run extractor LLM swap via existing `extractor._llm = ...` seam | 33/33 GREEN |
| 3 | Fixed SyntaxWarning `'\|'` in docstring (escape backslash) + ran ruff format normalization | clean |

---

## Notes for auditor

1. **Anti-duplication intra-package re-export of `_LLMResponse`.** `authority_vault_extractor.py` imports `_LLMResponse` from `offer_ladder_advisor.py` to avoid mirror. This is a deliberate intra-package consolidation — when a 3rd extractor surfaces in `comunify/copilot/extractors/`, the right move is to lift `_LLMResponse` + `_LiteLLMServiceLike` + lazy observability wrappers into `_transport.py` shared helper within the package. Documented in extractor docstring.

2. **`SpeakingEngagement` persistence under `press_mentions` kind.** The polymorphic table `ComunifyAuthorityVaultItemModel` accepts 4 kinds (credentials / case_studies / press_mentions / awards). SpeakingEngagement primitives surface as a separate Pydantic class (different fields: `venue`, `format` enum) but persist under `press_mentions` kind with `content.subkind = "speaking_engagement"`. This is documented in BOTH `_schemas.py::SpeakingEngagement` docstring and `authority_vault_extractor.py::_build_pending_rows`. The test `test_pre_fills_authority_vault_repo_with_pending_ratification_status` verifies the kind allowlist invariant.

3. **`status='extracted_pending_ratification'` field is NOT yet in alembic.** Per ticket spec: "writes pre-filled rows to authority_vault_items with status='extracted_pending_ratification'". The current `ComunifyAuthorityVaultItemModel` does NOT have a `status` column — rows are returned to caller as dicts. Production wiring (T-be-* future ticket) will either (a) add a `status` column via alembic migration, or (b) store it under `content.status` JSONB. Extractor's contract surface is the repo Protocol — alembic schema parity is a downstream concern. Documented in extractor docstring + `_AuthorityVaultRepoLike` Protocol docstring.

4. **No arch fitness gate yet for `BaseExtractionOrchestrator` subclass invariant in comunify.** Vitalia has `tests/architecture/test_extraction_orchestrator_inheritance.py`. Comunify does not (T-be-3 left it implicit). Recommend the auditor flag this as a follow-up (NOT a T-extractors-2 blocker — invariant is asserted at unit-test level via `test_authority_vault_extractor_subclasses_base_orchestrator`).

5. **Voseo compliance.** Extractor output content (Credential.title, CaseStudy.outcome, etc.) is supplied verbatim by the LLM from creator's source_text. No hardcoded user-facing strings in the extractor — all log events use English snake_case event names (per `structlog` convention) and Spanish content emerges only from LLM responses (which respect the brand voice). No voseo violations.

---

## Conventional commit message draft

```
feat(comunify/copilot): AuthorityVaultExtractor (T-extractors-2)

4-wave extension of BaseExtractionOrchestrator extracting credentials,
case studies, press mentions, speaking engagements, awards + social
proof signals from creator bio/LinkedIn/interview text. Pre-fills
comunify_authority_vault_items rows with status='extracted_pending_
ratification' for creator review in Brand Studio.

Waves: credentials_and_awards (Sonnet) + case_studies (Sonnet) +
press_and_social_proof (Haiku) + validate_and_merge (Sonnet). Cost
budget ≤$0.08 USD per extraction (V-AE-8 SSoT).

Anti-duplication: EXTENDS shared BaseExtractionOrchestrator (NOT
mirror). _LLMResponse re-imported from sibling offer_ladder_advisor
to keep N=1 source-of-truth inside comunify extractors package; lift-
to-shared deferred to 3rd consumer surface.

PII defense-in-depth: outbox + audit payloads carry only sanitised
counts/metrics — never raw source_text. Tenant_id propagates to every
side-effect collaborator (R2).

33 new tests (A1-A9 acceptance + defensive paths + schema cement) ·
V-AE-8 GREEN · 63 extractor tests total · 584 comunify suite GREEN.
R3 downstream regression rule updated.
```

---

**State after ticket close:** developing (Story 12 transitions on next /dev-team pickup per protocol).
