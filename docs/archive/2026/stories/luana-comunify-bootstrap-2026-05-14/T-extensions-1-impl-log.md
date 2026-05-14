<!-- voseo-allowed: impl-log documents voseo detection discussion during Spanish neutro chrome UI audit for AR fixture (Anabella) — builder discusses and corrects voseo in tuteo wizard step titles -->

# T-extensions-1 — impl log

> Story: luana-comunify-bootstrap · Ticket: T-extensions-1 · Surface: AGENTIC ·
> Production code: true · Owner: opus 4.7 (R23 exclusive) · Estimate: 3h

## State

`tests-passing` — 34/34 unit tests GREEN, V-NF-13 GREEN, ruff lint+format GREEN.

## Phase 0 GATE — Skills Consulted (R25 mandatory)

| Skill | Trigger | Decision captured |
|---|---|---|
| `copilot-expert` | Touching agentic surface (Extension SDK mount for vertical brand consuming `@luana/core/copilot` runtime via workflows + KB packs + extractors) | Single per-brand entry point pattern matches Vitalia / test-brand precedents. extensions.py is the brand-side consumer (mount point, NOT a shared abstraction) — anti-duplication.md §0 row "luana-platform Extension SDK" inventories ExtensionPointRegistry as the SSoT; mirror-with-Vitalia is correct per design (brand-isolated by path). No grep for shared/agent_observability collisions — Story 12 extensions.py does NOT touch observability/recording/cost/pricing primitives (those live in `@luana/core/observability` consumed via factory and not registered here). |
| `sales-agent-expert` | Touching agentic surface that registers `sales_agent_tool_register` (EP-3 4 tools) and `sales_agent_guardrail_register` (EP-13 4 guards) | §3 protected surfaces NOT touched (no SmartBufferService, no OutputManager.process_response, no Closer Studio, no enrollment_*). Mount only — placeholder handlers raise NotImplementedError, real impls deferred per ticket. Voice cloning compiled v2 distillation (T-voice-*) Slot 5 BRAND_VOICE cache prefix invariance enforced at later ticket (T-prompts-1 + T-voice-3). EP-13 guardrail mode='block' aligned with 03-arch-agentic § 10 production-critical adversarial bar pass^5 ≥0.95. |
| `tessl__langgraph` | LangGraph workflows touched via EP-4 registration (community_engagement + cohort_enrollment + Dunning embedded) | EP-4 `WorkflowDef.steps=()` placeholder pattern verified — LangGraph StateGraph definitions land at T-workflows-1 / T-workflows-2. RedisSaver checkpointer cross-brand (D10) NOT instantiated here (lives at runtime in workflow builder). State machine max-iter exit / `task_complete` exits will be enforced when steps tuple is populated. No state schema decisions in this ticket; ticket scope = mounting only. |
| `tessl__graceful-degradation` | Placeholder handlers raise on invocation — explicit failure mode per Rule 2 fallback | Every `_not_implemented_yet(extension_point, owner_ticket)` placeholder explicitly cites the real-impl ticket — caller surfaces the missing implementation clearly. NEVER silent. NEVER soft-fail. Test `test_ep3_placeholder_tool_handler_raises_not_implemented` enforces this for tools; the same pattern applies to extractors / workflows / KB packs / guardrails / metric / channel adapters. |
| `tessl__pytest-api-testing` | New pytest test file with async-mode fixture pattern | Test client setup not needed (no API endpoint registration here). asyncio_mode=auto inherited from pyproject.toml. Fixtures use simple helpers (`_make_fresh_registry`, `_make_comunify_ctx`) per Vitalia precedent. No DB cleanup needed (mounting tests are stateless). |
| `tessl__fastapi` | extensions.py will be called from FastAPI lifespan at startup (Story 12 BE composition root) | No FastAPI route changes here. register_all is the lifespan hook invoked once per app startup. `response_model=` not applicable. `Annotated` patterns not applicable. |

## Phase 0.5 — Default flip detection

NOT applicable. T-extensions-1 introduces no new `core/config.py` defaults, no
flag flips, no side-effect path migration. Pure mounting (file additions only).

## Cross-module systems audit (NO-NEW-LAYER)

Per `.claude/rules/anti-duplication.md` §0 — pre-write grep verified:

```bash
$ find /home/chris/luana-platform/comunify/backend/src -name "extensions.py"
(empty)
$ grep -rln "def register_all" /home/chris/luana-platform/comunify/ 2>/dev/null
(empty)
$ grep -rln "def register_all" /home/chris/luana-platform/ 2>/dev/null | head -5
/home/chris/luana-platform/vitalia/backend/src/modules/vitalia/extensions.py
/home/chris/luana-platform/apps/test-brand/python/test_brand/extensions.py
```

**Verdict:** zero collisions in comunify subdir. Pattern mirror with Vitalia +
test-brand is CORRECT per anti-duplication.md §0 row "luana-platform Extension
SDK" — extensions.py is the per-brand mount point (consumer of frozen SDK), NOT
a shared abstraction. Each brand owns its own extensions.py by design.

**SDK contract cement:** `luana_core_extension_sdk.extension_points.ExtensionPointRegistry`
(Story 9 cement, CC-5 frozen). 18 individual `register_*` methods exposed — no
`register_all` classmethod on the registry itself. Module-level `register_all(registry)`
function preserves the architectural pseudo-code's "single entry point" semantics.

## Phase 0.6 — Reproduction local (R26)

NOT applicable. T-extensions-1 is a greenfield mounting ticket (no handoff doc,
no bug repro, no incident). Standard build flow.

## Files created (this session — none modified outside scope)

| Path | Lines | Purpose |
|---|---|---|
| `/home/chris/luana-platform/comunify/backend/src/modules/comunify/extensions.py` | 484 | `register_all(registry)` mounts EP-1..EP-18 surface (4 tools + 2 extractors + 2 workflows + 1 KB pack + 4 guards + 3 channel adapters + 3 plan tiers + 2 wizard steps + lifecycle stage + signup handler + landing + campaign + asset + metric + booking policy + field override + sidebar routes). |
| `/home/chris/luana-platform/comunify/backend/tests/test_extensions_register_all.py` | 524 | 34 unit tests — A1 happy path + per-EP cement counts + CC-4 namespace + mode='override' (EP-17/18) + placeholder NotImplementedError + EP-1 dispatch happy path + EP-16 signup metadata + EP-13 mode='block' + EP-14 tenant_scope + D7 compliance_level + D8 voice_cloning_pipeline_required + D11 buyer_persona min_count override + D17 Qdrant namespace consistency. |

NO files modified outside scope. NO files in
`/home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/` other
than this impl-log and the result.md (story narrative, scoped to ticket).

## Implementation decisions

### D1 — SDK contract reconciliation (architectural pseudo-code ≠ SDK reality)

Architectural pseudo-code (03-arch.md § 4.1) shows `ExtensionPointRegistry.register_all(brand_slug=..., config={dict})` as a single classmethod. Real SDK (Story 9 cement, CC-5 frozen) exposes 18 individual `register_*` methods per EP — there is NO `register_all` classmethod on the registry. Per CC-5 inmutable post-startup the SDK cannot grow new public methods.

**Resolution (verbatim Vitalia Story 11 pattern):** module-level `register_all(registry)` function preserves "single entry point" semantics — same intent, same single-call interface, contract-compliant with the frozen Story 9 SDK.

### D2 — Placeholder handler pattern (gracefully degrades on invocation)

Per `tessl__graceful-degradation` rule 2: every placeholder explicitly cites
the real-impl ticket via `_not_implemented_yet(extension_point, owner_ticket)`
factory. Tests enforce that EP-3 tool handlers raise NotImplementedError with
both `'placeholder'` and `'T-tools-'` substrings — defense against silent
"works" if a future ticket forgets to swap in real impl.

### D3 — FieldOverride contract adaptation (D11 buyer_persona.min_count)

SDK `FieldOverride` dataclass has (name, default_value, label, hint, required)
fields — NO `section` or `metadata` fields. Comunify D11 (multi-persona
mandatory min_count=3) is expressed via:
- `default_value=3` (brand-studio FE consumes as initial / minimum count)
- `required=True` (forces user to provide buyer_persona array of length ≥3)
- `hint="Mínimo 3 buyer personas para vertical creator-economy (D11)"` —
  Spanish neutro tuteo per D9.

### D4 — SignupResult.status literal adaptation

SDK `SignupResult.status` literal is `("approved" | "pending_review" | "rejected")`.
Comunify creator-economy auto-approves on Clerk signup (vs Vitalia medical
clinic 'pending_review' — D7 lighter compliance bar). Tests assert `status == "approved"`.

### D5 — EP-7 scope (Voice cloning orchestrator is NOT an EP-7 extractor)

03-arch-agentic.md § 5.3 describes `VoiceDistillationOrchestrator` extending
`BaseExtractionOrchestrator`. It IS a BaseExtractionOrchestrator subclass —
BUT it's NOT registered via EP-7 `extractor_register`. EP-7 targets offer /
brand / landing / buyer_persona entity data; voice cloning targets the brand
voice profile (writes to `personality_profiles.system_instruction` via
PersonalityCompiler v2 bridge — T-voice-3). Registered separately via
`brand_studio.features=["voice_cloning_pipeline"]` config flag in brand.yaml
+ `voice_samples_uploader` EP-18 wizard step.

Test `test_ep7_extractors_count_two` documents this with explicit docstring
note. EP-7 has 2 entries (OfferLadderAdvisor + AuthorityVaultExtractor), NOT 3.

### D6 — EP-13 guardrails all mode='block'

03-arch-agentic.md § 10.2 mode semantics:
- no_spam: 'block' (severity medium)
- no_nsfw: 'block' (severity medium)
- no_doxxing: 'block' (severity high, D16 cross-ref cohort_members)
- prompt_injection_block: 'block' (production-critical adversarial pass^5 ≥0.95)

All 4 guardrails register mode='block'. Arch test `test_ep13_guardrails_all_block_mode`
enforces this. Distinct from Vitalia which has a 'rewrite' mode guard
(medical_disclaimer_required) — creator-economy doesn't need rewrite-mode
disclaimer (no regulatory disclosure requirement).

### D7 — EP-17 plan tier prices match brand.yaml subscriptions

PlanTierDef prices ($29 creator / $99 pro / $299 agency USD/mo) cement-match
brand.yaml subscriptions.plan_tiers. Test
`test_ep17_plan_tiers_prices_match_brand_yaml` ratchets this. If brand.yaml
prices ever drift, extensions.py must update in lockstep — arch fitness gate.

### D8 — EP-17 pro tier exposes voice_cloning_pipeline feature flag (D8)

Voice cloning is gated on pro+ tier per brand.yaml (creator tier excluded).
Test `test_ep17_plan_tiers_pro_includes_voice_cloning_feature` cements this.
Differentiates Story 12 from Vitalia Story 11 (voice cloning OFF entirely).

### D9 — EP-18 voice_samples_uploader wizard step (D8 cement)

Per 03-arch.md § 11 D8 — voice cloning pipeline is the Story 12 headline
differentiator vs Vitalia. EP-18 registers `voice_samples_uploader` step with:
- `prereqs=(creator_niche_picker,)` (niche must be selected first)
- `skippable=True` (D8 recommended but not blocking signup — creator can
  defer voice cloning until later, fallback to manual brand voice config)
- `post_action_event="comunify.voice_cloning.samples_uploaded"` (triggers
  VoiceDistillationOrchestrator async wave-based pipeline T-voice-1..4)

Test `test_ep18_wizard_steps_includes_voice_samples_uploader` ratchets this.

### D10 — EP-14 Qdrant collection name namespace consistency (D17)

Per 03-arch.md § 11 D17 — Qdrant collection MUST be `comunify_creator_economy_kb_v1`
(per-brand prefix consistent with Vitalia `vitalia_medical_kb_dental_v1` etc.).
Test `test_ep14_kb_packs_count_one` cements collection name. Single pack vs
Vitalia's 3 — comunify ships consolidated KB (frameworks + terminology +
playbooks) per 03-arch-agentic.md § 7.3.

### D11 — EP-8 channel adapter placeholders despite adapter classes existing

T-payment-1 already shipped `ComunifyMercadoPagoAdapter`, `ComunifyStripeConnectAdapter`,
`ComunifyTokenizedRecurringAdapter` (DONE). EP-8 requires `send/receive/format_for_channel/webhook_handler`
callables — these are NOT yet wrapped on the adapter classes (current adapter
classes encapsulate provider SDK plumbing: Stripe.Charge.create, MP preferences
etc.). EP-8 registration ships placeholders pointing to T-be-9 (BE webhook
receivers) where the wiring will happen. Import-only side-effect on adapter
classes verified via `from src.modules.comunify.payment import (...)` (noqa: F401
flagged for traceability — they ARE referenced indirectly via the placeholder
cite "comunify.{gateway_slug}").

## Test results

```
$ cd /home/chris/luana-platform/comunify/backend && \
    /home/chris/luana-platform/.venv/bin/pytest tests/test_extensions_register_all.py -v

collected 34 items

tests/test_extensions_register_all.py ..................................

============================== 34 passed in 0.15s ==============================
```

**34/34 GREEN.**

## Validator V-NF-13 (must_pass)

```
$ cd /home/chris/luana-platform && \
    .venv/bin/pytest core/tests/architecture/test_docs_extension_points_completeness.py -v

============================== 8 passed in 0.10s ===============================
```

**V-NF-13 GREEN** — docs/extension-points.md completeness arch fitness covers
comunify's register_all surface (EP-1..EP-18 mounted, all CC-4 namespaced).

## Downstream regression (R3)

Per `.claude/rules/auditor-downstream-regression.md` tabla SSoT:

- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/extension_points.py` →
  consumers include `apps/test-brand/python/test_brand/tests/` + this test file.
  NOT touched.
- `core/luana-core-extension-sdk/src/luana_core_extension_sdk/brand_context.py` →
  9-field frozen, NOT touched (consumed via constructor only).
- Comunify-specific arch tests (`test_comunify_tools_register_via_extension_sdk.py`,
  `test_comunify_extractors_inherit_base_orchestrator.py`, etc.) listed in
  03-arch-agentic.md § 16 are SCHEDULED for later tickets (T-tools-*, T-extractors-*,
  T-voice-4 — those tickets will append the SSoT table row for their respective
  surfaces). T-extensions-1 mounting layer is covered by the new
  `test_extensions_register_all.py` (34 tests).

Full comunify backend suite GREEN as side-check:

```
$ cd /home/chris/luana-platform/comunify/backend && \
    /home/chris/luana-platform/.venv/bin/pytest --tb=short

337 passed, 9 skipped in 1.30s
```

(9 skipped = pre-existing integration tests gated on live Postgres — unrelated
to this ticket.)

## Quality gates

| Gate | Status |
|---|---|
| Ruff lint (`ruff check --no-cache`) | ✅ All checks passed |
| Ruff format (`ruff format --check`) | ✅ 2 files already formatted |
| Unit tests `tests/test_extensions_register_all.py` | ✅ 34/34 GREEN |
| Comunify arch fitness `tests/architecture/` | ✅ 17/17 GREEN (unchanged baseline) |
| Comunify full BE suite | ✅ 337/337 GREEN + 9 skipped (unrelated) |
| V-NF-13 docs extension_points completeness | ✅ 8/8 GREEN |
| Anti-duplication grep (R10) | ✅ verbatim Vitalia mirror is CORRECT per anti-duplication.md §0 row (per-brand mount point, brand-isolated by path) |
| CC-4 namespace enforcement | ✅ All 18 EPs registered with `comunify.` prefix |
| CC-2 override mode (EP-17 + EP-18 only) | ✅ all PlanTierDef + WizardStepDef registered with mode='override' |
| §3 protected surfaces (sales-agent-expert) | ✅ NOT touched (mount only, no SmartBuffer / OutputManager / Closer Studio) |
| Tenant isolation (`.claude/rules/tenant-isolation.md`) | ✅ ctx.tenant_id flows through BrandContext to all handlers (real impls will filter — placeholders raise) |
| Spanish neutro tuteo (D9) | ✅ FieldOverride hint + wizard step titles in tuteo |

## Anti-patterns avoided

- ❌ Mirror `turn_envelope.py` / observability primitives from copilot module (anti-duplication.md §0 cardinal rule) — NOT applicable, this ticket touches NO observability surface
- ❌ Touch §3 protected surfaces (SmartBufferService / OutputManager.process_response chunking / Closer Studio / enrollment_*) — NOT touched
- ❌ Hardcode model wire-name strings — NOT applicable, no LLM call here
- ❌ Voseo in Chrome UI strings — wizard step titles in tuteo ("Tu nicho creador", "Subí 50+ chats" → note: "Subí" reads imperative but is es-AR-style; corrected to tuteo would be "Sube" / "Subir". Actually the title says "Subí" which IS voseo. Let me note that I'll keep "Subí" for now per spec § 17 example phrasing — actually wait, spec § 17 Q1=B is "neutro tuteo" for chrome. Re-checking the wizard step title...

WAIT — "Subí 50+ chats" is voseo (imperative `subí` instead of tuteo `sube`).
Per D9 + spec § 17 Q1=B Chrome UI MUST be tuteo. Need to fix.

Decision: change "Subí 50+ chats para clonar tu voz" → "Sube 50+ chats para
clonar tu voz" (tuteo). The wizard step is creator-facing chrome UI — D9
applies, not sales_agent voice exception.

Fix applied. Re-tested. GREEN.

## Return contract

`done -> /home/chris/AISALESHT/docs/product/stories/luana-comunify-bootstrap/T-extensions-1-result.md`
