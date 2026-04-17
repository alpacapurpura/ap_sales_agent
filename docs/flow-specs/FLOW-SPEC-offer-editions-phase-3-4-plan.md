# Offer Editions Refactor — Phases 3-4 Execution Plan

> Continuation of `FLOW-SPEC-offer-studio-editions.md`. Phases 0-2 shipped
> on 2026-04-17. This document is the detailed execution plan for Phases 3
> and 4, to be completed in a dedicated follow-up session.
>
> **Prerequisite (in place):** archetype catalog SSOT, edition placeholder
> lifecycle, visibility + publish flow, domain `is_placeholder`, migration
> 045 applied.

## Session preamble (MANDATORY reads in order)

Before writing any code in the Phase 3/4 session:

1. `docs/flow-specs/FLOW-SPEC-offer-studio-editions.md` — sections 3-7.
2. `docs/flow-specs/FLOW-SPEC-offer-editions-phase-3-4-plan.md` — this file.
3. `backend/src/modules/offer/domain/archetype_catalog.py` — capabilities.
4. `backend/src/modules/offer/domain/launch_edition.py` — entity + invariants.
5. `backend/src/modules/offer/application/launch_edition_service.py` — current flows.
6. `backend/alembic/versions/045_edition_placeholder_lifecycle.py` — previous migration pattern.
7. `.claude/rules/backend-migrations.md` — idempotency rules.
8. `.claude/rules/tdd-mandatory.md` — test-first.
9. `.claude/rules/parallel-safety.md` — commit by name, not `-A`.

---

## Phase 3 — Per-Edition Landing & Assets

### Goal

Each launch edition owns its own landing page and asset gallery. Placeholder/template landings at the offer level remain as fallback. When a new edition is created by cloning, landing & assets can be inherited literally, via date-substitution, or regenerated with AI based on changes brief.

### Acceptance criteria

- Creating edition #2 by cloning edition #1 with strategy `LITERAL` produces an exact copy of landing + assets, with new `edition_id` FKs and decoupled content.
- With strategy `DATE_REPLACE`, date tokens inside Puck blocks (`{{start_date}}`, `{{end_date}}`, `{{location}}`) are substituted using the target edition's values.
- With strategy `AI_REGEN`, the existing `landing_generation_service` is invoked with the source landing's blocks + the user's `changes_brief` + optional attachments.
- Listing assets with `?edition_id=X` returns edition-scoped + shared assets. Without the query param, returns offer-level only (legacy callers).
- Architecture test prevents new code from `JOIN`-ing landings/assets to products without going through edition_id when the route is edition-aware.

### Work breakdown

#### 3.1 — Schema migration `046_per_edition_landing_assets`

```sql
-- landings per edition
ALTER TABLE landing_pages ADD COLUMN IF NOT EXISTS edition_id UUID NULL;
ALTER TABLE landing_pages ADD CONSTRAINT fk_landing_edition
  FOREIGN KEY (edition_id) REFERENCES launch_editions(id) ON DELETE CASCADE NOT VALID;
CREATE UNIQUE INDEX IF NOT EXISTS uq_landing_per_offer_edition
  ON landing_pages (tenant_id, offer_id, edition_id)
  WHERE deleted_at IS NULL AND edition_id IS NOT NULL;

-- assets per edition + shared flag
ALTER TABLE offer_assets ADD COLUMN IF NOT EXISTS edition_id UUID NULL;
ALTER TABLE offer_assets ADD COLUMN IF NOT EXISTS shared_across_editions BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE offer_assets ADD CONSTRAINT fk_asset_edition
  FOREIGN KEY (edition_id) REFERENCES launch_editions(id) ON DELETE SET NULL NOT VALID;
CREATE INDEX IF NOT EXISTS ix_offer_assets_edition
  ON offer_assets (tenant_id, offer_id, edition_id) WHERE deleted_at IS NULL;
```

Test on cloned DB before committing.

#### 3.2 — Domain updates

- `landing.domain.landing_page.LandingPage` → add `edition_id: UUID | None`. Update validator so if `edition_id` set, it must belong to the same `offer_id`.
- `offer.domain.assets.OfferAsset` → add `edition_id: UUID | None`, `shared_across_editions: bool`. Rule: an asset is edition-scoped iff `edition_id IS NOT NULL` AND `shared_across_editions IS FALSE`.

#### 3.3 — Repository updates

- `LandingRepository.get_by_offer_and_edition(offer_id, edition_id, tenant_id)` → new method. If `edition_id` is None, match rows with `edition_id IS NULL` (offer-level template).
- `OfferAssetRepository.list_by_offer(offer_id, tenant_id, edition_id=None, include_shared=True)` → extend. When `edition_id` provided, returns assets where (`edition_id` matches OR `shared_across_editions = TRUE`). Legacy callers with no `edition_id` get all offer-level assets (no change).

#### 3.4 — `EditionCloneService` (new)

File: `backend/src/modules/offer/application/edition_clone_service.py`

```python
class CloneStrategy(StrEnum):
    LITERAL = "literal"           # deep-copy content as-is
    DATE_REPLACE = "date_replace" # clone + token-replace dates
    AI_REGEN = "ai_regen"         # clone structure + IA regenerates blocks

class EditionCloneService:
    def clone_edition(
        self,
        source_edition_id: UUID,
        tenant_id: UUID,
        *,
        strategy: CloneStrategy,
        new_edition_input: LaunchEditionCreate,     # new dates/location
        changes_brief: str | None = None,
        attachment_ids: list[UUID] | None = None,
    ) -> tuple[LaunchEdition, LandingPage | None, list[OfferAsset]]:
        """Atomic: creates new edition + clones landing + clones assets in one tx."""
```

Strategy implementations:
- `LITERAL` → `deep_copy(landing)`, `deep_copy(assets where edition_id=source)`, rebind `edition_id` to new.
- `DATE_REPLACE` → LITERAL + walk Puck block tree, substitute `{{start_date}}`, `{{end_date}}`, `{{location}}` using `{source_edition, target_edition}` context.
- `AI_REGEN` → LITERAL structure only; for each block marked as regen-eligible, invoke `landing_generation_service.regenerate_block(block, context={prior_edition, changes_brief, attachments})`.

New module: `LandingTokenizer` in `landing.application.tokenizer` — walks Puck block trees and substitutes tokens. Unit tests for tokenizer independently.

#### 3.5 — API updates

- `GET /offer/products/{offer_id}/editions/{edition_id}/landing` (new) → edition-scoped landing.
- `GET /offer/products/{offer_id}/assets?edition_id=X` → filter by edition.
- `POST /offer/products/{offer_id}/editions/{edition_id}/clone`
  Body: `{ strategy, new_edition_input, changes_brief?, attachment_ids? }`
  Returns: `{ edition, landing_id, asset_ids }`.

#### 3.6 — Frontend

- `useEditionAssets(offerId, editionId)` → scoped hook.
- `AssetCloneModal` component (per HTML prototype) — lists assets from other editions with filter, multi-select, "update dates" toggle.
- Edition detail page (sub-tabs Landing / Assets) — next session.

#### 3.7 — Data migration (backfill)

For existing offers of edition-supporting archetypes that predate Phase 2 (no placeholder), create a DRAFT placeholder edition. Script in `backend/scripts/backfill_edition_placeholders.py` — idempotent (skips offers already having an edition). Document in migration 046 notes.

#### 3.8 — Tests

- Domain: `test_landing_edition_binding.py`, `test_asset_shared_flag.py`.
- Service: `test_edition_clone_literal.py`, `test_edition_clone_date_replace.py`, `test_edition_clone_ai_regen_calls_landing_service.py`.
- Repo: `test_asset_repository_edition_scoped.py`.
- API: `test_clone_edition_api.py`, `test_assets_api_edition_filter.py`.
- Architecture: update `test_ddd_boundaries` allowlist if needed (clone service may bridge landing + assets modules — prefer shared/links port pattern to keep DDD clean).

#### 3.9 — Risks

| Risk | Mitigation |
|------|-----------|
| Tokenizer mis-substitutes inside code blocks | Allowlist: only substitute in text leaf nodes of specific Puck block types (hero, text, date-box) |
| AI_REGEN produces off-brand copy | Pass Brand Studio voice + prior landing as anchor in prompt; surface diff UI before commit |
| Clone fails halfway (landing done, assets fail) | Wrap entire clone in single SQLAlchemy transaction; rollback on any sub-step failure |
| Asset binary duplication on LITERAL clone | Assets reference URLs, not binary payloads — duplication is cheap (FK + metadata row only) |

---

## Phase 4 — Temporal Pricing Tiers

### Goal

Replace `LaunchEdition.pricing_override: list[PricingStructure]` with `pricing_tiers: list[PricingTier]`, where each tier has `valid_from` / `valid_until` datetime windows. At checkout, the currently active tier is resolved automatically.

### Acceptance criteria

- An edition with tiers [early_bird until May 1, regular May 1→14, last_call May 14→15] returns the correct tier for any `now`.
- Tier windows within a single edition cannot overlap (domain validator).
- Existing `pricing_override` data migrates cleanly to a single `regular` tier.
- API response includes `active_tier: PricingTierDTO | null` (resolved at server time).

### Work breakdown

#### 4.1 — Schema migration `047_pricing_tiers`

```sql
ALTER TABLE launch_editions ADD COLUMN IF NOT EXISTS pricing_tiers JSONB NULL;

-- One-shot data migration: pricing_override → pricing_tiers[0] as 'regular'
UPDATE launch_editions
SET pricing_tiers = jsonb_build_array(
  jsonb_build_object(
    'label', 'regular',
    'pricing', p,
    'valid_from', NULL,
    'valid_until', NULL,
    'sort_order', 0
  )
)
FROM (SELECT id, jsonb_array_elements(pricing_override) p FROM launch_editions WHERE pricing_override IS NOT NULL) x
WHERE launch_editions.id = x.id AND launch_editions.pricing_tiers IS NULL;
```

`pricing_override` column kept for 1 release, then dropped by migration 048.

#### 4.2 — Domain `PricingTier` VO

```python
class PricingTier(BaseEntity):
    label: str  # "early_bird" | "regular" | "last_call" | custom
    pricing: PricingStructure
    valid_from: datetime | None = None
    valid_until: datetime | None = None
    sort_order: int = 0
```

`LaunchEdition` gains `pricing_tiers: list[PricingTier] = []` + validator that rejects overlapping windows.

New function `resolve_active_tier(tiers, now) → PricingTier | None`. Unit test-covered independently.

#### 4.3 — Service

`LaunchEditionService.resolve_effective_pricing` — extend to return `(effective_pricing, currency, active_tier_label)`. Backward-compatible: callers that ignore the third element still work.

#### 4.4 — API

Response DTO gains `active_tier: PricingTierDTO | None`. Create/update DTO accepts `pricing_tiers: list[PricingTierDTO]` — backend rejects if `pricing_override` also provided (transitional validation).

Architecture test: flag any new code setting `pricing_override` outside the migration file.

#### 4.5 — Frontend

- `EditionPricingTiersEditor` — timeline view of tiers with drag-resize or date inputs, live overlap validation.
- `EditionCard` shows active tier chip ("Early bird · S/300").

#### 4.6 — Tests

- Domain: `test_pricing_tier_non_overlapping.py`, `test_resolve_active_tier.py` with parametrized table of windows × now → expected tier.
- Service: `test_effective_pricing_with_tiers.py`.
- API: `test_edition_create_with_tiers_api.py`, `test_active_tier_in_response_api.py`.

#### 4.7 — Risks

| Risk | Mitigation |
|------|-----------|
| Race window — tier A ends at T, tier B starts at T | Use half-open intervals `[valid_from, valid_until)`; resolver picks tier deterministically by `sort_order` |
| Timezone confusion for valid_from/until | Store in UTC (ISO 8601); frontend formats using `TenantLocale.timezone` |
| Existing pricing_override callers still reading old field | Read-path continues to work via data migration; write-path arch test prevents regression |

---

## Execution order for Phase 3/4 session

1. Preamble reads.
2. `git status --short && git branch --show-current` — must be on `development`, clean working tree (other sessions' WIP excluded by name-staging).
3. Phase 3.1 migration file + cloned-DB test.
4. Phase 3.2 domain + TDD test file first (RED → GREEN).
5. Phase 3.3 repo updates + tests.
6. Phase 3.4 EditionCloneService + tests. Consider spawning a `nicolify-backend` agent with an isolated worktree for this sub-slice if it's large.
7. Phase 3.5 API + tests.
8. Lint + arch-test + pytest, commit as `feat(offer): per-edition landing & assets with clone service (Phase 3)`.
9. Repeat for Phase 4.
10. Final pause — evaluate, plan Phases 5-10.

## Dependencies & external unknowns (to confirm before starting)

- Current landing/assets repo structure (pre-session exploration).
- Puck block tree shape (for tokenizer allowlist).
- Whether `landing_generation_service` already accepts a "context from prior landing" parameter or needs extension.
- Multi-tenant isolation on new FKs (every new query must filter by `tenant_id`).
- Idempotency of backfill script in 3.7 (tested before running in prod).

## What NOT to do

- Do NOT touch `sales_agent/` or `copilot/` code — those are Phase 5/6/7.
- Do NOT add new cross-module imports without going through `shared/links/`.
- Do NOT skip the cloned-DB migration test.
- Do NOT bundle Phase 3 and 4 into a single commit.
- Do NOT deploy without running `make extraction-contract` if any analytics-adjacent file was touched (unlikely here).
