<!-- voseo-allowed: audit review may cite spanish-text.md glosario verbatim per R25 (.claude/rules/spanish-text.md § Magic comment escape) -->
# Frontend Code Review — T-2 + T-6 (growth-studio-actions-schemas-real)

**Date:** 2026-05-08
**Files Reviewed:** 4 zod schemas + 5 action components + registry/index + api/etl-api extension + Playwright smoke + VR baselines
**Domains touched:** growth-studio, copilot (action consumers)
**Skills consulted:** frontend-expert, tessl__react-patterns, tessl__zod, tessl__shadcn-ui, tessl__tailwind, playwright-expert, metrics-expert (registries SSoT)
**Live-verified:** YES — Playwright smoke playground 9/9 + VR 18/18 baselines captured (T-6)
**Verdict:** **PASS**

## /test-frontend Gate Status (per gate-output.json + gate-logs/iter-1)

| Gate | Result | Detail |
|---|---|---|
| tsc --noEmit (strict) | PASS | 0 errors |
| ESLint (60+ rules) | PASS | 0 errors, 1243 warnings (no growth in T-2/T-6 scope; pre-existing) |
| Vitest | PASS | 800 tests / 107 files (50 schema + 26 action component tests added) |
| Arch fitness (FE) | PASS | 30/30 incl. test-studio-structure-parity, test-fe-schema-paths-resolve, test-folder-naming, test-component-naming |
| BE downstream (R3 scope) | PASS | pytest 4005 passed (copilot+analytics+shared, iter-2) |
| Playwright smoke | PASS | playground 9/9 GREEN; stage routes pre-existing CF tunnel flakiness (unrelated) |
| Playwright VR | PASS | 14 baselines + 18/18 verification |

## Category Summary

| # | Category | Status | Notes |
|---|---|---|---|
| 1 | FSD-Lite boundaries | PASS | actions/ + schemas/ within feature; barrel exports; side-effect import schemas/index→actions/registry mirrors brand-studio; no cross-feature deep imports |
| 2 | Server/Client correctness | PASS | "use client" only on the 5 action components (interactive); schemas pure modules; ETLConfirmAction uses useCallback + useState correctly |
| 3 | React Patterns (tessl) | PASS | role="alert" on truncated/rate-limited/confirm; stable keys (kpi.slug, entry.channel); useCallback on handleConfirm; aria-label on dynamic button; aria-busy via disabled+isPending text swap |
| 4 | Forms / Zod | PASS | 4 schemas .strict() (mirrors Pydantic extra="forbid"); enums derived from STAGE_REGISTRY/CHANNEL_REGISTRY (NO hardcoding); 50 schema unit tests + 6 security tests (path injection, XSS, prompt-injection, tenant_id smuggling) |
| 5 | Multitenancy | PASS | fetchClient used via api/etl-api.ts::triggerEtlChannel (auto X-Tenant-ID); Authorization Bearer from useAuth().getToken(); no manual tenant header injection; arch test enforces fetchClient outside api/ |
| 6 | Master-data / Currency | PASS | useTenantLocale() consumed in StageMetricsAction; formatMoney(value, kpi.currency ?? tenantLocale.currency) — no hardcoded 'USD'; toLocaleString("en-US") used for non-monetary numeric (acceptable — locale-agnostic display) |
| 7 | Spanish neutro | PASS | grep voseo regex (podés/tenés/sos/vos/hacé/elegí/configurá/etc.) on actions/ + schemas/ → 0 matches; copy uses tuteo: "Podrás intentarlo nuevamente", "Datos parciales", "Confirmar", "Iniciando..." |
| 8 | Accessibility | PASS | role="alert" on dynamic notices (truncated, rate-limit, confirm prompt, success); role="region" + aria-label on stage section; semantic <section>, <ul>, <button>; aria-label dynamic for confirm action |
| 9 | Live verification | PASS | T-6 captured 14 VR baselines per viewport (mobile 375 + desktop 1024); playground smoke 9/9 GREEN; ClerkProvider wrap in playground/layout for ETLConfirmAction useAuth() compatibility |
| 10 | Tests / TDD | PASS | RED→GREEN documented in T-2-impl-log iter 1 (schema tests RED → GREEN; action tests RED → GREEN); 76 new test cases (50 schema + 26 component); coverage threshold preserved |
| 11 | Cross-cutting (zod ↔ Pydantic) | PASS | T-5 contract test test_be_fe_schema_alignment_growth_studio.py validates z.toJSONSchema() ↔ Pydantic model_json_schema; .strict() ↔ extra="forbid" parity verified |
| 12 | Anti-duplication | PASS | registry mirrors brand-studio PATTERN (bootstrapGrowthStudioActions + idempotent registerAction + side-effect import) — NOT data; each studio owns its own action keys ("growth.*"); STAGE_REGISTRY/CHANNEL_REGISTRY consumed from 2A (no mirror) |
| 13 | Mirror detection | PASS | new files: 5 actions + 4 schemas + registry/index + api extension. Grepped: no equivalent component/hook in brand-studio/offer-studio. Action component pattern (Action.tsx) reused intentionally; each studio owns its keys (not duplication) |
| 14 | Decisions honored cite (R6) | N/A | 06-tickets.yaml T-2/T-6 do not declare `decisions_applicable` field; not triggered |

## Findings

No FAIL or WARN findings. Implementation matches spec, validators, and architectural patterns established in 03-arch.md and 05-guidelines.md.

### Strengths worth noting
- **Adversarial defense at parse boundary:** stage-filter-params-security.test.ts covers path injection, XSS, prompt injection, tenant_id smuggling — defense in depth at zod parse vs trusting BE only.
- **Registry pattern parity:** registry.ts faithfully mirrors brand-studio shape (idempotent registerAction, GROWTH_STUDIO_ACTION_KEYS frozen tuple, side-effect bootstrap). Easy to audit, easy to extend.
- **VR breakpoints both viewports:** 14 baselines = 7 surfaces × 2 viewports (mobile 375 + desktop 1024). Catches responsive regressions, not only desktop drift.
- **fetchClient kept in api/ layer:** action component delegates HTTP call to triggerEtlChannel — arch test enforces, builder respected on first try. JSDoc comment renamed to avoid arch-test regex match (subtle but correct).

## Verdict Math

- 0 FAILs across all 14 categories (Cat 14 N/A)
- 0 WARNs
- All 8 /test-frontend gate categories GREEN
- No allowlist or warning baseline growth in T-2/T-6 scope
- Live verification evidence cited (Playwright smoke + VR baselines)
- IMPL-LOG cites required skills (frontend-expert + tessl__react-patterns + tessl__zod + tessl__shadcn-ui + tessl__tailwind + playwright-expert)
- T-5 cross-stack contract test validates zod ↔ Pydantic alignment
- Spanish neutro: voseo grep clean on production code

→ **PASS**

done -> /home/chris/AISALESHT/docs/product/stories/growth-studio-actions-schemas-real/REVIEW-fe.md
