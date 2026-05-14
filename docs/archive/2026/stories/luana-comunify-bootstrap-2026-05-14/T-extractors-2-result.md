# T-extractors-2 — result

**Status:** tests-passing → awaiting orchestrator → gate-runner → auditor-agentic

**Surface:** AGENTIC · **production_code:** true · **R23 Opus 4.7 mandatory:** ✅

## Acceptance summary

| # | Acceptance | Validator | Status |
|---|---|---|---|
| A1 | Subclass of `BaseExtractionOrchestrator` | `test_authority_vault_extractor_subclasses_base_orchestrator` + 3 corollaries | ✅ |
| A2 | 4 waves complete + merge → `AuthorityVaultExtractedV1` + confidence_score | `test_4_wave_pipeline_happy_path` + `test_wave_called_with_correct_role_routing` | ✅ |
| A3 | Happy path bio: 3 credentials + 2 case studies + 1 press extracted | `test_4_wave_pipeline_happy_path` (exact count + value assertions) | ✅ |
| A4 | Empty bio → no false positives + low_signal warning | `test_empty_bio_returns_empty_extraction_no_false_positives` | ✅ |
| A5 | Cost per extraction ≤$0.08 USD (V-AE-8 SSoT) | `test_cost_budget_happy_path` (in-budget) + `test_cost_budget_exceeded_recorded_as_warning` (overbudget surfacing) + `test_cost_unknown_wave_does_not_break_run` | ✅ |
| A6 | PII (emails/phones) NOT leaked verbatim to outbox/audit payloads | `test_pii_in_bio_masked_in_outbox_payload` | ✅ |
| A7 | `schema_version=1` Literal cement frozen | `test_schema_version_is_literal_1_frozen` + 5 enum/range cement tests | ✅ |
| A8 | Cross-tenant isolation (tenant_id propagation + no inter-run leak) | `test_tenant_id_propagates_to_all_collaborators` + `test_cross_tenant_isolation_no_leak_across_runs` | ✅ |
| A9 | Pre-fills `authority_vault_repo` rows with `status='extracted_pending_ratification'` | `test_pre_fills_authority_vault_repo_with_pending_ratification_status` | ✅ |

## Validator V-AE-8 status

```
$ cd /home/chris/luana-platform/comunify/backend && .venv/bin/pytest tests/agentic_evals/extractors/ -v --tb=short
63 passed in 0.15s
```

GREEN. (33 new T-extractors-2 + 30 pre-existing T-extractors-1.)

## Files

- **Created:**
  - `luana-platform/comunify/backend/src/modules/comunify/copilot/extractors/authority_vault_extractor.py`
  - `luana-platform/comunify/backend/tests/agentic_evals/extractors/test_authority_vault_extractor.py`
- **Extended (M8 — never replace):**
  - `luana-platform/comunify/backend/src/modules/comunify/copilot/extractors/_schemas.py` (added Credential / CaseStudy / PressMention / SpeakingEngagement / Award / SocialProofSignals / AuthorityVaultExtractedV1)
  - `luana-platform/comunify/backend/src/modules/comunify/copilot/extractors/__init__.py` (docstring sync — "3-wave" was a stale stub, corrected to "4-wave")
  - `AISALESHT/.claude/rules/auditor-downstream-regression.md` (3 new SSoT rows)

## Quality gates

- `ruff check`: All checks passed (extractors + tests)
- `ruff format --check`: 8 files already formatted
- Broader regression: 584 passed, 9 skipped in 1.47s (zero new regressions)

## Notes for orchestrator → auditor

1. `_LLMResponse` is re-imported from sibling `offer_ladder_advisor.py` (intra-package N=1 SSoT). Lift-to-shared deferred per anti-duplication rule.
2. `SpeakingEngagement` primitives persist under `press_mentions` kind with `content.subkind` discriminator (polymorphic table contract — documented in extractor + schema docstrings).
3. `status` field is in repo Protocol contract today; alembic materialization is a downstream T-be-* concern (per ticket spec — extractor surface owns the contract).
4. No comunify arch fitness gate for `BaseExtractionOrchestrator` subclass invariant yet. Recommend follow-up — NOT a T-extractors-2 blocker.

done -> docs/product/stories/luana-comunify-bootstrap/T-extractors-2-result.md
