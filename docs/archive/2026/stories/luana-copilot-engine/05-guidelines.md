---
story_id: luana-copilot-engine
guidelines_version: 1
last_modified: 2026-05-11
drafted_by: /architect-orchestrator (claude-opus-4-7)
authority: 03-arch.md + 03-arch-agentic.md + 00-story.md + outcome §7.3 lift mode + §7.2 Stories 6+7 autonomy + ADR-001 + 6 D-T decisiones + Story 5 05-guidelines.md pattern reference
---

# 05-guidelines.md — luana-copilot-engine

> **/dev-team reads this BEFORE picking ANY ticket.** Defines patterns required/forbidden, files in scope, skills to load, halt criteria. Sub-builders inherit this guidance verbatim. **R23 mandate: ALL Story 6 tickets owner = builder-agentic Opus 4.7 (NO Sonnet eligibility — agentic production code).**

## §1. Patterns Required

### §1.1 Lift mode (per outcome §7.3, identical to Stories 2-5 §1.1)

- **Verbatim file copy.** `cp -r` for directories. NO rewrites, reformats, line renumbering.
- **Preserve DDD layering.** domain/ → infrastructure/ → application/ → api/ + observability/ + evals/ + utils/.
- **Preserve class/function/module names.** `ToolRegistry` stays `ToolRegistry`. `CopilotState` stays `CopilotState`. `build_deep_agent_graph` stays `build_deep_agent_graph`. **`[COPILOT-*]` anchors preserved verbatim (36 total).**
- **Preserve public API surface** — `__init__.py` re-exports match AISALESHT verbatim.
- **Preserve tests** — lift `backend/tests/modules/copilot/` (~213 files) alongside source. NONE deferred (all copilot tests lift).
- **Preserve registries SSoT** (D-T1 FROZEN): `ToolRegistry`, `WorkflowRegistry`, `ExtractorRegistry`, `ModuleRegistry`, `SuggestionRegistry` public signatures locked at lift moment. Golden snapshot V-AG-3 enforces.
- **Preserve LangGraph state shape** — `CopilotState(TypedDict)` keys preserved verbatim. `add_messages` + `operator.add` reducers preserved.
- **Preserve prompt cache slot order 1-11** — `compose_system_prompt` signature FROZEN.
- **Preserve [COPILOT-*] anchors** — exactly 36 anchors post-lift. Bump only with architect ratification.
- **Per-package `pyproject.toml` at version `"0.0.6-alpha"`** (template in 03-arch.md §3.2).
- **Import paths internal-to-luana-platform only.** Use sed mapping in 03-arch.md §5.

### §1.2 Workspace registration (T-1 single ticket)

- Add `core/luana-core-copilot` to `~/luana-platform/pyproject.toml` `[tool.uv.workspace] members` + `[tool.uv.sources]`.
- Run `cd ~/luana-platform && uv sync --all-packages` post-update. Tolerates missing src files temporarily; full GREEN comes post-T-2..T-15.

### §1.3 Import path rewriting (mechanical sed)

```bash
# Inside lifted copilot package — execute from package root
cd ~/luana-platform/core/luana-core-copilot

# 1. Self-imports: src.modules.copilot.<X> → luana_core_copilot.<X>
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.copilot\.|from luana_core_copilot.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.copilot\.|import luana_core_copilot.|g' {} \;

# 2. Cross-module to Stories 2-5 packages
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.brand\.|from luana_core_brand_studio.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.offer\.|from luana_core_offer_studio.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.iam\.|from luana_core_iam.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.assets\.|from luana_core_assets.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.crm\.|from luana_core_crm.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.analytics\.|from luana_core_analytics_engine.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.landing\.|from luana_core_landing.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.connections\.|from luana_core_connections.|g' {} \;

# 3. Shared → luana-core-platform / observability / events / etc.
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.|from luana_core_observability.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain_events\.|from luana_core_events.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.idempotency\.|from luana_core_idempotency.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.billing\.|from luana_core_billing.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.llm\.|from luana_core_llm.|g' {} \;
# CHANNEL FORMAT registry was lifted Story 2 to luana_core_channels
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.channels\.|from luana_core_channels.|g' {} \;
# Generic shared.* → luana_core_platform.*
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain\.|from luana_core_platform.domain.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.links\.|from luana_core_platform.links.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.|from luana_core_platform.infrastructure.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.application\.|from luana_core_platform.application.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.workers\.|from luana_core_platform.workers.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.api\.|from luana_core_platform.api.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.core\.|from luana_core_platform.core.|g' {} \;

# 4. NOTE: NEVER touch:
#    - admin/ pages (Story 10 territory — admin shell migration)
#    - Streamlit imports (out of scope)
#    - sales_agent imports — copilot doesn't import sales_agent (verified empty grep)
```

### §1.4 D-T6 observability subclass invariant (CRITICAL)

When lifting `copilot/observability/recording/callback_handler.py`:

1. **Verify it inherits, never redefines.** Top of file MUST be:
   ```python
   from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler
   class CopilotCallbackHandler(BaseAgentCallbackHandler):
       ...
   ```
2. **If sed-rewrite leaves a redundant class definition of FXResolver, CostCalculator, PricingResolver, sanitize_payload, etc. (because AISALESHT was the original location pre-Story 2)** — DELETE the redundant definition. Import from `luana_core_observability` instead.
3. **Verify via grep post-lift:**
   ```bash
   grep -rE "class (FXResolver|CostCalculator|PricingResolver|BaseObservabilityContext|BaseAgentCallbackHandler)\b" \
       core/luana-core-copilot/src/luana_core_copilot/
   # → expected: empty (all are imports, NEVER declarations)
   ```
4. **Story 6 D-T6 arch test V-AG-5 enforces this.** If fails → re-apply sed + clean up redundant class defs.

### §1.5 T-16 UNLIFT recipe (Stories 2-5 copilot_provider/ → home packages)

This is the most delicate ticket. **Inverse of standard sed pattern.**

For each Story 2-5 package with previously-deferred `copilot_provider/`:

```bash
# Example for brand-studio (Story 5 deferral — 8 files)
SRC=/home/chris/AISALESHT/backend/src/modules/brand/copilot_provider
DST=~/luana-platform/core/luana-core-brand-studio/src/luana_core_brand_studio/copilot_provider

mkdir -p "$DST"
cp "$SRC"/__init__.py "$SRC"/{context_inject,module_data,provider,summary,tools,workflow_handlers,workflows}.py "$DST/"

# sed rewrite — DIFFERENT for each subfolder (target = own package + luana_core_copilot)
cd ~/luana-platform/core/luana-core-brand-studio
# Self → brand_studio
find src/luana_core_brand_studio/copilot_provider -name "*.py" -exec sed -i \
  's|from src\.modules\.brand\.|from luana_core_brand_studio.|g' {} \;
# copilot ports → luana_core_copilot
find src/luana_core_brand_studio/copilot_provider -name "*.py" -exec sed -i \
  's|from src\.modules\.copilot\.|from luana_core_copilot.|g' {} \;
# shared → luana_core_platform (etc.)
find src/luana_core_brand_studio/copilot_provider -name "*.py" -exec sed -i \
  's|from src\.shared\.|from luana_core_platform.|g' {} \;

# Run brand-studio aggregate tests GREEN
cd ~/luana-platform && uv run pytest core/luana-core-brand-studio/tests/ -x -q
```

**Repeat for 8 packages** (brand-studio, offer-studio, commercial-calendar, social-proof, crm, analytics-engine, landing, connections) + lift offer-studio `api/offer_ai.py` (Story 5 deferral).

**Critical:** Each package's `copilot_provider/__init__.py` must expose `provider` symbol for `ModuleRegistry.discover()` pkgutil scan.

**Plus lift 4 cross-coupling tests (Story 5 deferrals):**
```bash
cp /home/chris/AISALESHT/backend/tests/modules/brand/test_brand_context_injector.py \
   ~/luana-platform/core/luana-core-brand-studio/tests/
cp /home/chris/AISALESHT/backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py \
   ~/luana-platform/core/luana-core-brand-studio/tests/
cp /home/chris/AISALESHT/backend/tests/modules/brand/test_worker_emits_summary_and_pills.py \
   ~/luana-platform/core/luana-core-brand-studio/tests/
cp /home/chris/AISALESHT/backend/tests/modules/offer/test_offer_data_access_provider.py \
   ~/luana-platform/core/luana-core-offer-studio/tests/
# Apply sed on all 4 (substitute copilot → luana_core_copilot)
```

### §1.6 T-17 MessageModel stub cleanup (D-T2 cement)

`core/luana-core-offer-studio/tests/conftest.py` lines 145-157 currently declare:

```python
if "messages" not in _Base.metadata.tables:
    class MessageModel(_Base):
        """Stub for sales_agent.MessageModel (Story 7 lift). FK target only."""
        __tablename__ = "messages"
        id = _sa.Column(MockUUID(as_uuid=True), primary_key=True)
        lead_id = _sa.Column(MockUUID(as_uuid=True), _sa.ForeignKey("leads.id"), nullable=True)
```

**Replace with:**
```python
# Story 6 — MessageModel now lifted to luana_core_copilot
# (D-T2 cleanup: Story 5 stub removed, real model registered)
from luana_core_copilot.persistence.models.message_model import MessageModel  # noqa: F401
```

**AppointmentModel stub (lines 160-172) STAYS** — scheduling = Story 8 territory. Stub comment updated to:
```python
# Stub for scheduling.AppointmentModel (Story 8 lift). FK target only.
# Story 6 D-T2 evaluation: AppointmentModel stub remains because scheduling
# module not lifted until Story 8 (campaigns-extension-sdk lift batch).
```

Run `cd ~/luana-platform && uv run pytest core/luana-core-offer-studio/tests/ -x -q` → GREEN. Cementing V-AG-4 arch fitness.

### §1.7 Brand-agnostic engine verification (Story 6-specific)

Pre-commit local smoke before T-19:

```bash
cd ~/luana-platform/core/luana-core-copilot/src
grep -rEn 'if\s+brand\s*==|if\s+tenant\.brand\s*==|brand\s*==\s*"(nicolify|vitalia|comunify|lupulo)"' \
    luana_core_copilot/ \
    && echo "FAIL: brand control flow detected" || echo "OK: brand-agnostic"
grep -rEn '(API_KEY|SECRET|TOKEN)\s*=\s*"(?!\$|os\.|settings\.|env|getenv).{8,}"' luana_core_copilot/ \
    && echo "FAIL: hardcoded secret" || echo "OK"
```

If either FAILs → escalate per §6 halt #7 (lift mode violation — AISALESHT source has brand contamination shouldn't have merged).

### §1.8 D-T1 registry contract snapshot (T-20)

Generate golden snapshot ONCE in T-20:

```python
# core/tests/architecture/_snapshots/copilot_registry_v1.json
{
  "ToolRegistry": {
    "class_name": "ToolRegistry",
    "module": "luana_core_copilot.application.tools.registry",
    "methods": ["register", "get", "list", "groups", "reset"],
    "frozen_dataclasses": {"Tool": ["name", "description", "function", "groups", "schema", "tenant_scoped", "external_calls"]}
  },
  "WorkflowRegistry": { ... },
  "ExtractorRegistry": { ... },
  "ModuleRegistry": { ... },
  "SuggestionRegistry": { ... },
  "constants": {
    "ALWAYS_AVAILABLE_GROUPS": ["always_available", "navigation", "memory"],
    "_BASE_TOOL_GROUPS_KEYS": [...],
    "ROUTE_TOOL_MAP_KEYS": [...]
  }
}
```

Snapshot generation script: `core/tests/architecture/_snapshots/_generate_copilot_registry_snapshot.py` (write once, run when registries intentionally change with arch ratification).

### §1.9 [COPILOT-*] anchor preservation

Pre-T-21 smoke:
```bash
grep -roE "\[COPILOT-[A-Z0-9-]+\]" ~/luana-platform/core/luana-core-copilot/src/ | sort -u | wc -l
# Expected: 36
```

If count ≠ 36 → sed pattern corrupted anchors (likely false). Investigate. **Bump cap requires architect ratification.**

## §2. Patterns Forbidden

### §2.1 Lift mode violations (auto-FAIL — outcome §7.3)

- ❌ Renaming any class, function, module, registry, anchor.
- ❌ Refactoring logic during lift (even "obvious improvements").
- ❌ Splitting modules. Two files stay two files.
- ❌ Merging modules. One file stays one file.
- ❌ **Adding new abstractions** — NO EP-1..EP-5 SDK formalization (that's Story 8). NO new BrandVoicePort (that's Story 7). NO new mirrors of observability bases.
- ❌ Changing registry public signatures (D-T1 FROZEN). Bumping `Tool` dataclass fields, `Workflow.handler_ref` mechanism, `ModuleDescriptor` fields — all FORBIDDEN.
- ❌ Reformatting beyond `ruff format` auto-on-save.
- ❌ Changing LangGraph state TypedDict keys (CopilotState). Adding new keys = scope expansion.
- ❌ Reordering prompt cache slots (1-11 order FROZEN — F8 cement).
- ❌ Bumping `[COPILOT-*]` anchor count beyond 36 without explicit architect ratification.
- ❌ Removing legacy SSE event types (e.g., dropping `ui_action` compat) — FE consumers (nicolify shell) still depend until Story 10.

### §2.2 Mutating AISALESHT (auto-FAIL — outcome §7.3)

- ❌ Any file under `backend/src/modules/copilot/` is READ-ONLY in Story 6.
- ❌ Any file under `backend/tests/modules/copilot/` is READ-ONLY.
- ❌ Modifying AISALESHT root pyproject.toml, alembic migrations, root conftest.
- ❌ Running `make ci-parity` against AISALESHT (Story 10 territory).
- ❌ **EXCEPTION: 4 cross-coupling tests Story 5 deferred** (test_brand_context_injector, test_buyer_persona_fields_dropped_regression, test_worker_emits_summary_and_pills, test_offer_data_access_provider) — these are READ-ONLY for copy purposes (lift to luana-platform Stories 2-5 packages), the AISALESHT originals stay intact.

### §2.3 Anti-mirror discipline (D-T6 + anti-duplication.md cardinal)

- ❌ **Declaring `class FXResolver`, `class PricingResolver`, `class CostCalculator`, `class BaseObservabilityContext`, `class BaseAgentCallbackHandler`, function `sanitize_payload`** anywhere in `luana_core_copilot/`. ALL these MUST be `from luana_core_observability...` imports.
- ❌ Re-implementing tenant billing config repository, base_trace_event_repo, base_llm_call_repo. SUBCLASS the bases from luana_core_observability with module-specific concrete repos.
- ❌ Re-registering channel formats (those live in luana_core_channels Story 2). Channel ADAPTER classes (TelegramBotChannel, InMemoryChannel) lift to copilot.infrastructure.channels — these are different from format registry.
- ❌ Re-creating PII regex (sanitization.PATTERNS in luana_core_observability is global). copilot uses `sanitize_payload(payload)` import.
- ❌ Re-implementing LLM router (luana_core_llm Story 2). copilot/application/router/model_router.py CONSUMES `LLMRouter` from luana_core_llm.

### §2.4 Forward-Story coupling (auto-FAIL)

- ❌ Importing from `luana_core_sales_agent` (Story 7 — doesn't exist yet at Story 6 build time).
- ❌ Importing from `luana_core_campaigns`, `luana_core_advertising`, `luana_core_social_media`, `luana_core_scheduling` (Stories 8+).
- ❌ Importing from `src.modules.*` in any Story 6 source file (lift incomplete; caller forgot sed).

### §2.5 Registry contract violations (D-T1 FROZEN)

- ❌ Adding methods to ToolRegistry, WorkflowRegistry, ExtractorRegistry, ModuleRegistry, SuggestionRegistry beyond AISALESHT current shape.
- ❌ Modifying dataclass fields of Tool, Workflow, ExtractorDomain, ModuleDescriptor, Suggestion.
- ❌ Changing `_BASE_TOOL_GROUPS`, `ALWAYS_AVAILABLE_GROUPS`, `ROUTE_TOOL_MAP` shape (content can grow via tool addition — shape doesn't).
- ❌ Renaming public constants. Renaming module paths.

### §2.6 Observability writes anti-patterns (preserve F11 + S0-S11A discipline)

- ❌ Bypassing `sanitize_payload` on any write to `*_trace_event` or `*_llm_call` tables.
- ❌ Removing `try/except` + `structlog.warning` + `db.rollback()` resilience pattern in callback handler hooks.
- ❌ Computing `cost_usd` via `calculate_cost()` runtime — must use `pop_cost(litellm_call_id)` per S12 + PI-12 S1 T-1 cement.
- ❌ Hardcoding model wire names — must use `luana_core_llm.providers._chat_model_resolver` SSoT.

### §2.7 Prompt cache architecture violations

- ❌ Inserting volatile content (timestamps, conv IDs, tenant_name interpolation) into slots 1-6 (cacheable prefix).
- ❌ Reordering slots 1-11.
- ❌ Moving cache_breakpoint marker — stays after slot 6.
- ❌ Removing min 4096-token floor verification — Opus 4.7 silently no-caches below floor.
- ❌ Failing to record `cache_creation_input_tokens` + `cache_read_input_tokens` to `copilot_llm_call` table.

## §3. Files in Scope

### §3.1 AISALESHT (READ-ONLY source)

**Lift these:**

```
backend/src/modules/copilot/
├── __init__.py
├── api/                                 # 22 files — routers + DTOs
├── application/                         # ~100 files — orchestrator + tools + workflows + suggestions + router + procedures + extraction + memory + guided + services + observability + data_access + discovery
├── domain/                              # 33 files — module_registry + ports + workflow + extractors + hooks + rules + skills + message + events + etc.
├── evals/                               # 4 files — golden_dataset + runner + scorers
├── infrastructure/                      # ~40 files — repositories + models + persisters + channels + voice + qdrant + cache + prompts + web + workers + in_memory_registries
├── observability/                       # ~10 files — recording + persistence + api (subclasses of luana_core_observability bases)
└── utils/                               # 1 file
```

`backend/tests/modules/copilot/` (~213 test files) lifts ALL.

**Plus per T-16 UNLIFT:**

```
backend/src/modules/brand/copilot_provider/          (8 files — Story 5 deferral)
backend/src/modules/offer/copilot_provider/          (5 files — Story 5)
backend/src/modules/offer/api/offer_ai.py            (1 file — Story 5)
backend/src/modules/crm/copilot_provider/            (2 files — Story 4)
backend/src/modules/analytics/copilot_provider/      (2 files — Story 4)
backend/src/modules/landing/copilot_provider/        (2 files — Story 4)
backend/src/modules/connections/copilot_provider/    (2 files — Story 4)
backend/src/modules/commercial_calendar/copilot_provider/ (2 files — Story 3)
backend/src/modules/social_proof/copilot_provider/   (2 files — Story 3)
backend/tests/modules/brand/test_brand_context_injector.py  (Story 5 deferral)
backend/tests/modules/brand/test_buyer_persona_fields_dropped_regression.py  (Story 5)
backend/tests/modules/brand/test_worker_emits_summary_and_pills.py  (Story 5)
backend/tests/modules/offer/test_offer_data_access_provider.py  (Story 5)
```

### §3.2 luana-platform (CREATE)

- `~/luana-platform/core/luana-core-copilot/{pyproject.toml,README.md,src/luana_core_copilot/**,tests/**}`
- `~/luana-platform/core/tests/architecture/test_story6_brand_agnostic_engine.py`
- `~/luana-platform/core/tests/architecture/test_story6_no_forward_module_imports.py`
- `~/luana-platform/core/tests/architecture/test_copilot_registry_contracts_stable.py`
- `~/luana-platform/core/tests/architecture/_snapshots/copilot_registry_v1.json`
- `~/luana-platform/core/tests/architecture/test_no_residual_test_stubs_post_story_6.py`
- `~/luana-platform/core/tests/architecture/test_no_mirror_observability_in_copilot.py`
- `~/luana-platform/core/tests/architecture/test_module_descriptor_complete_for_lifted_packages.py`
- `~/luana-platform/core/tests/architecture/test_voice_compiler_ssot_still_intact.py`
- `~/luana-platform/core/tests/architecture/test_copilot_anchors_count_stable.py`

**Modify:**
- `~/luana-platform/pyproject.toml` (workspace + sources)
- `~/luana-platform/core/DEFERRED-FILES.md` (Story 6 entries + UNLIFTED section)
- `~/luana-platform/core/luana-core-offer-studio/tests/conftest.py` (MessageModel stub → real import per T-17)
- T-16 affects 8 packages' src/ + tests/ (add copilot_provider/ subfolders + 4 cross-coupling tests).

### §3.3 DEFERRED list Story 6 — DO NOT LIFT, DO NOT TOUCH

**Defer to Story 10 (nicolify migration):**
- `backend/src/admin/pages/{trazas,copilot-routing,costo-copilot,copilot-limits,copilot-quality,marketing-kb,brand-summaries}.py` (Streamlit admin shell — moves with nicolify in Story 10).
- `backend/src/admin/app.py`, `backend/src/admin/modules/`, `backend/src/admin/pages/__init__.py`.

**Defer to Story 7 (sales_agent lift — Story 6's blocked downstream):**
- `backend/src/modules/connections/api/dependencies/__init__.py` real wiring of `ChatOrchestrator` (Story 4 deferred this; Story 6 unblocks luana_core_copilot, but full `ChatOrchestrator` instantiation needs luana_core_sales_agent's MessageHandlerPort impl which arrives Story 7). Stub `NotImplementedError` in luana-core-connections stays until Story 7.

**Defer to Story 8 (scheduling lift — campaigns-extension-sdk batch):**
- AppointmentModel stub in offer-studio conftest STAYS (per D-T2 evaluation — scheduling = Story 8).

### §3.4 Skip during cp -r — mechanical recipe

```bash
# brand mod lift (full module, NO subfolder skip needed — there's no copilot_provider IN copilot)
mkdir -p ~/luana-platform/core/luana-core-copilot/src/luana_core_copilot \
         ~/luana-platform/core/luana-core-copilot/tests

for sub in api application domain evals infrastructure observability utils __init__.py; do
  if [ -e "/home/chris/AISALESHT/backend/src/modules/copilot/$sub" ]; then
    cp -r "/home/chris/AISALESHT/backend/src/modules/copilot/$sub" \
          ~/luana-platform/core/luana-core-copilot/src/luana_core_copilot/
  fi
done

# Lift ALL copilot tests (213 files — none deferred for Story 6)
rsync -av \
      /home/chris/AISALESHT/backend/tests/modules/copilot/ \
      ~/luana-platform/core/luana-core-copilot/tests/

# Verify zero leaks AFTER sed
grep -rEn "from src\.modules\.(sales_agent|campaigns|advertising|social_media|scheduling)" \
    ~/luana-platform/core/luana-core-copilot/src/ \
    && echo "FAIL: forward-Story leak" || echo "OK"
```

## §4. Skills + Rules to Load

| Skill / Rule | When | Owner |
|---|---|---|
| `backend-expert` (this skill) | All Story 6 tickets | universal |
| `copilot-expert` | All Story 6 tickets — F0-F11 phases + 36 anchors + slot order + registries SSoT | mandatory |
| `tessl__langgraph` | T-9, T-10 (LangGraph orchestrator + tools graph) | mandatory |
| `claude-api` (Anthropic prompt caching) | T-9 (compose_system_prompt + slot architecture) | mandatory |
| `brand-expert` | T-16 (brand-studio copilot_provider unlift) | conditional |
| `offer-expert` + `offer-type-preset-expert` | T-16 (offer-studio copilot_provider unlift + offer_ai.py lift) | conditional |
| `metrics-expert` | T-16 (analytics-engine copilot_provider unlift) | conditional |
| `tessl__fastapi` | T-14 (API routers lift) | mandatory |
| `tessl__graceful-degradation` | T-8 (web crawler + Qdrant client) + T-10 (external tool calls) | mandatory |
| `.claude/rules/anti-duplication.md` | T-13, T-20 (D-T6 anti-mirror observability) | mandatory |
| `.claude/rules/auditor-downstream-regression.md` | All tickets — tests lift alongside source + Stories 2-5 packages re-test post-T-16 | mandatory |
| `.claude/rules/tdd-mandatory.md` | T-19, T-20 (new arch fitness + smoke tests) | mandatory |
| `.claude/rules/parallel-safety.md` | All tickets — single development branch, no force push | mandatory |
| `.claude/rules/copilot-resilience.md` | T-9, T-10, T-13 (callback handler + trace recorder + cost recorder) | mandatory |
| `.claude/rules/copilot-observability.md` | T-13 (observability subfolder + module-scoped repos) | mandatory |
| `.claude/rules/spanish-text.md` | Pre-commit voseo check (some tool descriptions are user-facing) | mandatory |

## §5. Commit conventions (per ticket)

```
chore(workspace): register Story 6 luana-core-copilot package                                # T-1
feat(luana-core-copilot): skeleton + pyproject.toml + README                                 # T-2
feat(luana-core-copilot): lift copilot domain layer (registries + ports + workflow base)     # T-3
feat(luana-core-copilot): lift copilot infrastructure repositories + models                  # T-6
feat(luana-core-copilot): lift copilot infrastructure persisters                             # T-7
feat(luana-core-copilot): lift copilot infrastructure channels + voice + qdrant + cache + prompts + web + workers  # T-8
feat(luana-core-copilot): lift copilot application orchestrator (LangGraph + deepagents)     # T-9
feat(luana-core-copilot): lift copilot application tools registry + 28 tools + 3 subfolders  # T-10
feat(luana-core-copilot): lift copilot application workflows + suggestions + router + procedures + extraction + memory + guided + observability  # T-11
feat(luana-core-copilot): lift copilot application services layer                            # T-12
feat(luana-core-copilot): lift copilot observability subfolder (subclasses of luana-core-observability bases)  # T-13
feat(luana-core-copilot): lift copilot api layer + DTOs                                      # T-14
feat(luana-core-copilot): lift copilot evals + utils                                         # T-15
feat(luana-core-copilot): unlift Stories 2-5 copilot_provider/ subfolders + 4 cross-coupling tests  # T-16
chore(luana-core-offer-studio): D-T2 cleanup — replace MessageModel stub with real luana_core_copilot import  # T-17
test(luana-platform): cross-package smoke + aggregate pytest GREEN (22 packages)             # T-18
test(arch): Story 6 brand-agnostic engine + no-forward-imports invariants                    # T-19
test(arch): Story 6 D-T1+D-T2+D-T6 cement — registry contracts + stub cleanup + anti-mirror + ModuleDescriptor + voice compiler SSoT + 36 anchors  # T-20
chore(luana-platform): Story 6 lint + AISALESHT untouched + DEFERRED-FILES update + README polish  # T-21
```

Conventional Commits format. All on `development` branch in `~/luana-platform/`. Push after each ticket GREEN.

## §6. Halt criteria (per outcome §7.4 + 03-arch.md)

Halt + escalate Chris if:

1. **Cross-Story-6 coupling discovered** — if copilot imports sales_agent or vice-versa, DAG breaks → escalate. (Verified empty grep — should not trigger.)
2. **D-T6 observability mirror detected** — V-AG-5 fails. Indicates sed missed redundant class def OR AISALESHT has true mirror (impossible per anti-duplication.md cardinal). Investigate.
3. **Registry contract change required** — if AISALESHT has subtle inconsistency (e.g., one ToolRegistry method has different sig than expected), surface to architect — D-T1 contract frozen requires arch ratification to bump.
4. **Auditor REJECTED + 3 auto-fix Opus iter fail** — per outcome §7.4 cap_reached.
5. **Scope expansion needed** — any "small refactor" touching files beyond §3 list. Includes: introducing EP-1..EP-5 SDK abstraction, introducing BrandVoicePort (Story 7), new registries, new arch boundaries.
6. **Cumulative cost > $1500** — soft check-in with Chris.
7. **Brand-specific code in supposedly brand-agnostic engine** — arch fitness V-AG-1 fails after lift → source has pre-existing brand contamination → escalate (shouldn't have merged).
8. **DEFERRED file leaks into lift** — `grep "from src.modules.(sales_agent|campaigns|advertising|scheduling|social_media)"` in lifted code post-sed reveals leak → revert + re-lift.
9. **Test count drop > 5%** — preserve test count from AISALESHT baseline (213 copilot tests + 4 cross-coupling). Drop indicates lost files or excessive per-test skips. Escalate.
10. **[COPILOT-*] anchor count ≠ 36** — investigate sed corruption OR intentional bump (architect ratification only).
11. **`compose_system_prompt` signature deviation** — slot architecture FROZEN. Reorder = breaking change.
12. **LangGraph state TypedDict key change** — `CopilotState` keys FROZEN. Add/remove = scope expansion.
13. **T-16 unlift breaks Stories 2-5 aggregate tests** — copilot_provider/ subfolders that aren't compatible with their home package after sed → investigate per-package.
14. **T-17 MessageModel cleanup breaks offer-studio aggregate tests** — verify imports correct + run aggregate. AppointmentModel allowlist preserved.

## §7. Sub-builder spawn template

```
Agent({
  description: "Lift copilot <surface> — T-N",
  subagent_type: "builder-agentic",
  model: "opus",  // R23 MANDATORY — production agentic code, NO Sonnet
  prompt: "
    <pr_folder>: /home/chris/AISALESHT/docs/product/stories/luana-copilot-engine
    <ticket>: T-N

    Lift copilot <surface> from AISALESHT to luana-platform per:
    - 00-story.md scope
    - 03-arch.md §3 (package structure) + §5 (sed mapping) + §9 (DEFERRED list)
    - 03-arch-agentic.md (LangGraph state + slot order + registries + observability subclass pattern + Qdrant tenant-agnostic)
    - 05-guidelines.md §1.3 (sed) + §3.4 (cp -r recipe) + §3.3 (deferred) + §1.4 (D-T6 anti-mirror critical) + §1.5 (T-16 unlift only) + §1.6 (T-17 stub cleanup only)
    - Validators GREEN: V-NF-2 + V-F-py-1 + addressed_by per ticket

    DO NOT TOUCH AISALESHT.
    DO NOT lift admin/ pages (Story 10 territory).
    DO NOT introduce new abstractions (EP-1..EP-5 SDK = Story 8; BrandVoicePort = Story 7).
    DO NOT modify registry public contracts (D-T1 FROZEN — V-AG-3 enforces).
    DO NOT mirror observability bases (D-T6 cardinal — V-AG-5 enforces).
    DO NOT change slot order 1-11 or compose_system_prompt signature.
    DO NOT bump [COPILOT-*] anchor count beyond 36.
    Conventional commit per §5.
    Last line: 'done -> <commit-sha>' or 'failed -> <reason>'.
  "
})
```

## §8. Verification recipe per ticket close

After each ticket:

```bash
# 1. Package tests GREEN
cd ~/luana-platform && uv run pytest core/luana-core-copilot/tests/ -x -q --tb=short

# 2. Ruff clean
cd ~/luana-platform && uv run ruff check core/luana-core-copilot/

# 3. No leaked src.modules.* or forward-Story imports
grep -rEn "from src\.modules\." ~/luana-platform/core/luana-core-copilot/src/ && echo "FAIL: src.modules leak" || echo "OK"
grep -rEn "from luana_core_(sales_agent|campaigns|advertising|social_media|scheduling)" ~/luana-platform/core/luana-core-copilot/src/ && echo "FAIL: forward Story import" || echo "OK"

# 4. AISALESHT untouched
cd /home/chris/AISALESHT
git diff HEAD --name-only | grep -E '^(backend/src/modules/copilot|backend/tests/modules/copilot)/' && echo "FAIL: AISALESHT mutated" || echo "OK"

# 5. (after T-13) D-T6 subclass invariant
cd ~/luana-platform && uv run python -c "
from luana_core_copilot.observability.recording.callback_handler import CopilotCallbackHandler
from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler
assert issubclass(CopilotCallbackHandler, BaseAgentCallbackHandler)
print('D-T6 subclass OK')"

# 6. (after T-16) Stories 2-5 still GREEN
cd ~/luana-platform && uv run pytest core/luana-core-brand-studio/tests/ core/luana-core-offer-studio/tests/ core/luana-core-crm/tests/ core/luana-core-analytics-engine/tests/ core/luana-core-landing/tests/ core/luana-core-connections/tests/ core/luana-core-commercial-calendar/tests/ core/luana-core-social-proof/tests/ -x -q

# 7. (after T-17) offer-studio aggregate GREEN with real MessageModel import
cd ~/luana-platform && uv run pytest core/luana-core-offer-studio/tests/ -x -q

# 8. (after T-20) all 8 NEW arch fitness tests GREEN
cd ~/luana-platform && uv run pytest core/tests/architecture/test_story6_*.py core/tests/architecture/test_copilot_*.py core/tests/architecture/test_no_*.py core/tests/architecture/test_module_descriptor_*.py core/tests/architecture/test_voice_compiler_*.py -x -q

# 9. [COPILOT-*] anchor count exactly 36
grep -roE "\[COPILOT-[A-Z0-9-]+\]" ~/luana-platform/core/luana-core-copilot/src/ | sort -u | wc -l
# Expected: 36
```

All checks GREEN → close ticket. ANY FAIL → halt per §6.

## §9. Common pitfalls + remedies

| Pitfall | Symptom | Remedy |
|---|---|---|
| Over-broad sed corrupts test fixtures/docstrings | Strings inside docstrings replaced unintentionally | Use exact patterns §1.3 anchored on `from src\.` / `import src\.`. Verify with `git diff` pre-commit. |
| `monkeypatch.setattr("src.modules.copilot.X")` left in tests | Tests pass but mock targets wrong module post-lift | Run sed on tests too. `grep "src.modules" tests/` post-lift = empty. |
| LangGraph imports module-load fail | T-9 pytest collection fails on missing langgraph | Verify `langgraph>=0.2` + `deepagents>=0.5.3` + `langchain-core>=0.3` in pyproject. |
| Qdrant client missing | T-8 test_marketing_kb_store fails ImportError | Verify `qdrant-client>=1.10` in pyproject. |
| arq missing for workers | T-8 workers import error | Verify `arq>=0.26` in pyproject. |
| jinja2 missing for prompts templates | Prompt rendering fails | Verify `jinja2>=3.1`. |
| tiktoken missing for token_counter | memory/token_counter fails | Verify `tiktoken>=0.7`. |
| D-T6 anti-mirror arch fails | V-AG-5 detects `class BaseAgentCallbackHandler` declaration in copilot | Sed left redundant class; delete it, use `from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler`. |
| ModuleDescriptor discovery fails | V-AG-6 reports missing module_keys | T-16 didn't lift one of the copilot_provider/ subfolders; verify all 8 packages. |
| Voice compiler V-AG-7 regression | test_voice_compiler_ssot_still_intact fails | Copilot accidentally declared PersonalityCompiler mirror; check `grep "class PersonalityCompiler" core/luana-core-copilot/` → empty. |
| [COPILOT-*] anchor count != 36 | V-AG-8 detects N anchors | If N < 36: sed corrupted comment markers; if N > 36: builder added new without registry update. Investigate. |
| compose_system_prompt slot order drift | V-F-prompt-cache fails | Reorder/rename = breaking. Revert + preserve verbatim. |
| Stories 2-5 aggregate tests fail post-T-16 | V-F-py-2 fails on brand-studio/offer-studio/etc. | copilot_provider/ subfolder sed leaves dangling imports; per-package sed validation needed. |
| AppointmentModel stub accidentally removed during T-17 | offer-studio tests fail on appointments FK | Only MessageModel stub removed; AppointmentModel stays per D-T2 evaluation. |
| Cumulative cost > $2000 mid-Story | Soft check-in trigger | Report cumulative to Chris, await confirm continue. |
