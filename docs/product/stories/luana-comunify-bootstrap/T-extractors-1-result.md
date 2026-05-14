# T-extractors-1 — result

> Story: luana-comunify-bootstrap · Ticket: T-extractors-1 · Surface: AGENTIC ·
> R23 Opus 4.7 production code · State: `tests-passing` · Date: 2026-05-14

## What shipped

`OfferLadderAdvisor` — 4-wave LLM extractor that analyzes a creator's current
offer portfolio and produces actionable advice on filling missing levels of
the 4-tier ladder (lead_magnet / tripwire / core_offer / premium).

EXTENDS `luana_core_extraction.base_orchestrator.BaseExtractionOrchestrator`
per `.claude/rules/anti-duplication.md` SSoT row (wave-based LLM extraction
abstraction → lift shared, NOT mirror).

## Files

| Path | LOC | Role |
|---|---|---|
| `comunify/backend/src/modules/comunify/copilot/extractors/offer_ladder_advisor.py` | 590 | `OfferLadderAdvisor` class — 4 waves, merge, best-effort side-effects |
| `comunify/backend/src/modules/comunify/copilot/extractors/_schemas.py` | 170 | Pydantic primitives: `OfferLadderAdviceV1`, `LadderGap`, `SuggestedOffer`, `TierOptimization`, `ExtractionWave` |
| `comunify/backend/tests/agentic_evals/extractors/__init__.py` | 5 | Test package marker |
| `comunify/backend/tests/agentic_evals/extractors/test_offer_ladder_advisor.py` | 740 | 30 tests covering A1-A5 + defensive paths + schema cement |

## Wave composition (matches 03-arch-agentic § 5.1)

| # | Wave | Model role | Timeout | Confidence weight |
|---|---|---|---|---|
| 1 | `analyze_current_offers` | reasoning (Sonnet 4.6) | 30 s | 0.30 |
| 2 | `detect_ladder_gaps` | reasoning (Sonnet 4.6) | 30 s | 0.30 |
| 3 | `generate_suggestions` | nano (Haiku 4.5) | 30 s | 0.30 |
| 4 | `validate_and_merge` | reasoning (Sonnet 4.6) | 25 s | 0.10 (meta-validator) |

## Output schema cement

```python
OfferLadderAdviceV1(
    schema_version: Literal[1]            # ★ frozen — V2 = NEW class
    ladder_gaps: list[LadderGap]          # detected missing levels
    suggested_offers: list[SuggestedOffer] # 5-10 candidate offers per gap
    tier_optimization: TierOptimization    # pricing + positioning analysis
    confidence_score: float                # 0..1 aggregate
    missing_required_fields: list[str]
    extraction_warnings: list[str]
)
```

## Acceptance criteria

| ID | Criterion | Verified by |
|---|---|---|
| A1 | Subclass of `BaseExtractionOrchestrator` | `test_offer_ladder_advisor_subclasses_base_orchestrator` |
| A2 | 4 waves complete + merge → `OfferLadderAdviceV1` with confidence_score | `test_4_wave_pipeline_happy_path` + 4 defensive cases |
| A3 | Cost per advice run ≤$0.10 USD (V-AE-8 SSoT) | `test_cost_budget_happy_path` + `test_cost_budget_exceeded_recorded_as_warning_not_raised` |
| A4 | Empty ladder graceful path: 4 gaps + bootstrap suggestions | `test_empty_ladder_returns_full_4_gap_bootstrap` |
| A5 | Cross-tenant isolation: tenant_id propagates to all collaborators | `test_tenant_id_propagates_to_all_collaborators` + `test_cross_tenant_isolation_no_leak_across_runs` |

## Test results

```
cd /home/chris/luana-platform/comunify/backend && \
  .venv/bin/pytest tests/agentic_evals/extractors/test_offer_ladder_advisor.py -v --tb=short

30 passed in 0.13s
```

Full agentic_evals suite (downstream regression):

```
.venv/bin/pytest tests/agentic_evals/ --tb=short
166 passed in 0.44s     # was 136 pre-ticket — +30 new, 0 regression
```

## Quality gates

| Gate | Result |
|---|---|
| `ruff check` | All checks passed |
| `ruff format --check` | 6 files already formatted |
| Tests (extractor module) | 30/30 PASS |
| Tests (full agentic_evals) | 166/166 PASS |

## Validator V-AE-8

```
cd /home/chris/luana-platform/comunify/backend && \
  .venv/bin/pytest tests/agentic_evals/extractors/ -v --tb=short

30 passed in 0.13s    # AuthorityVaultExtractor not yet here (T-extractors-2 pending)
```

V-AE-8 PASS for OfferLadderAdvisor coverage. AuthorityVaultExtractor scope is
T-extractors-2 (separate ticket, sibling pattern).

## Decisions / deviations

- **Inline prompts (not externalised to `_prompts/` Jinja dir)** — respects
  `files_in_scope: 2` budget. Prompts use `<<MARKER>>` substitution boundaries
  for Anthropic cache prefix invariance. Future ticket can lift when
  T-extractors-2 lands (gains by sharing prompt-load infrastructure).
- **`_schemas.py` added beyond `files_in_scope`** — structural prerequisite
  (5 Pydantic models). Mirrors vitalia `vitalia/.../extractors/_schemas.py`
  pattern. Auditor-acceptable extension (no concrete alternative).
- **`tests/agentic_evals/extractors/__init__.py` added** — package marker
  required for pytest discovery. Trivial.
- **`_LLMResponse` + `_LiteLLMServiceLike` kept INLINE** — N=2 today
  (comunify + vitalia sibling). Anti-duplication.md threshold reached;
  flagged in impl-log for `/pm` to decide lift in next ticket. Does NOT
  block this ticket.

## Anti-duplication audit (per § 0 cardinal rule)

| Symbol | Cross-codebase grep | Verdict |
|---|---|---|
| `class OfferLadderAdvisor` | Only spec MDs | NEW |
| `class OfferLadderAdviceV1` | Only spec MDs | NEW |
| `class LadderGap` | Only spec MDs | NEW |
| `class SuggestedOffer` | Only spec MDs | NEW |
| `class TierOptimization` | Only spec MDs | NEW |
| `BaseExtractionOrchestrator` consumed via shared `luana_core_extraction` | — | EXTEND (not mirror) ✅ |
| `sanitize_payload` + `pop_cost` consumed via lazy import from shared `luana_core_observability` | — | EXTEND (not mirror) ✅ |

Zero collisions, zero unjustified mirrors. R10 satisfied.

## Blocks

- Resolves: T-be-3 ✓ (consumed `OfferLadderRepository` as DI handle) +
  T-extensions-1 ✓ (Extension SDK registration already done).
- Unblocks: T-eval-1 (next ticket — agentic eval suite can now exercise
  `OfferLadderAdvisor` for cost_budget + cache_hit_rate validators).

## Closure

Ticket complete. State: `tests-passing`. Awaiting orchestrator → gate-runner →
auditor-agentic for independent audit verdict per R30.

Impl-log: `T-extractors-1-impl-log.md`
