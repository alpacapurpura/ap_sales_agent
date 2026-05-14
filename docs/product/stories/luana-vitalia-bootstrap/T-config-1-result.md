---
ticket: T-config-1
story: luana-vitalia-bootstrap
state: done
date: 2026-05-13
builder: builder-backend (Claude Sonnet 4.6)
---

# T-config-1 Result — BrandConfig declarative YAML

## Verdict: DONE

## Acceptance gates

| Gate | Status | Evidence |
|---|---|---|
| A1 — YAML parseable + schema valid | PASS | `.venv/bin/python -c 'import yaml; yaml.safe_load(open("../config/brand.yaml"))'` — no exception |

## Decisions honored

| # | Decision | Implementation |
|---|---|---|
| D7 | compliance_level=hipaa_lite | `compliance_level: hipaa_lite` + comment `NOT hipaa_full` + stripe_healthcare excluded from payment_gateways |
| D8 | voice_cloning_enabled=false | `voice_cloning_enabled: false` + `features.voice_cloning: false` |
| D9 | Spanish neutro tuteo | `multi_language_ui: false` (LatAm Spanish only) |
| D12 | wellness_deep defer | `features.wellness_deep_coverage: false` |
| D13 | multi_site defer | `features.multi_site_ui: false` |
| D14 | insurance defer | `features.insurance_integration: false` |

## Files produced

| Repo | File | Action |
|---|---|---|
| luana-platform | `vitalia/config/brand.yaml` | CREATED |
| AISALESHT | `docs/product/stories/luana-vitalia-bootstrap/T-config-1-impl-log.md` | CREATED |
| AISALESHT | `docs/product/stories/luana-vitalia-bootstrap/T-config-1-result.md` | CREATED |

## Commits

- luana-platform: `vitalia/config/brand.yaml` committed to main
- AISALESHT: docs committed to development

## Unblocks

- T-extensions-1 (extensions.py register_all — reads brand.yaml for brand_slug + feature flags)
- T-be-4 (backend services that consume BrandConfig)
- T-fe-3 (frontend feature flag reads)

## Notes for T-extensions-1

`offer_studio.preset_pack: medical_services_v1` is a slug reference. The actual
`OfferTypePreset` catalog entries for the medical_services_v1 pack are NOT yet
registered in `OFFER_TYPE_PRESET_CATALOG`. T-extensions-1 or a dedicated preset
ticket should register the medical presets and wire `preset_pack` lookup.

`plan_tiers.multi_site` backend support is included (price_usd_monthly: 599,
max_doctors: 50) but `features.multi_site_ui: false` correctly defers UI
federation per D13.
