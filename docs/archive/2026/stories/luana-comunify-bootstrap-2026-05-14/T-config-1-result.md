---
ticket: T-config-1
story: luana-comunify-bootstrap
surface: config
state: done
implemented_at: 2026-05-14
---

# T-config-1 Result — BrandConfig declarative YAML

## Artifact

`/home/chris/luana-platform/comunify/config/brand.yaml`

## Acceptance verifier

```bash
cd /home/chris/luana-platform/comunify && python3 -c 'import yaml; yaml.safe_load(open("config/brand.yaml"))'
```

**Result: PASS** (exit 0, no exception)

## Key content summary

| Section | Value |
|---|---|
| brand_slug | comunify |
| compliance_level | creator_economy |
| voice_cloning_enabled | true |
| features flags | 15 (+ multi_account_creator_switcher = 16 total) — 4 deferred to 12.bis |
| brand_studio.enabled_sections | 10 (identity, story, narrative, voice, buyer_persona, authority_vault, team, testimonials, communication_assets, contact) |
| brand_studio.required | [authority_vault] |
| brand_studio.buyer_persona.min_count | 3 |
| offer_studio.preset_pack | coaching_offers_v1 |
| ladder.levels | [lead_magnet, tripwire, core, premium] |
| ladder conversions | lead_magnet→tripwire 8%, tripwire→core 12%, core→premium 6% |
| subscriptions.plan_tiers | creator $29, pro $99, agency $299 |
| community_safety thresholds | spam 0.85, nsfw 0.85, auto_reject_spam 0.95, pre_mod_count 3 |
| payment_gateways | mercadopago (primary), stripe_connect (fallback), tokenized_recurring (recurring) |
| kb_packs | [creator_economy_kb_v1] |
| agentic_tools | 4 (qualify_for_cohort, link_to_community, nurture_via_authority_content, book_discovery_call) |
| extractors | 2 (OfferLadderAdvisor, AuthorityVaultExtractor) |
| workflows | 2 (CommunityEngagementWorkflow, CohortEnrollmentWorkflow) |
| guardrails | 4 (no_spam, no_nsfw, no_doxxing, prompt_injection_block) |

## Blocks unblocked

- T-extensions-1 (extensions.py register_all)
- T-be-4 (BE services consume brand.yaml)
- T-fe-3 (FE feature flags consume brand.yaml)
