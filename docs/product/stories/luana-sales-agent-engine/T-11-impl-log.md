# T-11 Implementation Log

**Ticket:** T-11 — Lift sales_agent application/quality/judge + application/prompts/compose (D-T3 BrandVoicePort consumer wiring slot 5 BRAND_VOICE)
**Owner:** builder-agentic (Opus 4.7)
**State transitions:** ready → developing → developed (T-11 GREEN)
**Date:** 2026-05-12
**Estimated:** 60min — **Actual:** ~80min (includes D-T3 hexagonal refactor + conftest pre-existing-bug fix)

## Skills Consulted

- **copilot-expert** — Stop. Lee primero. Anti-duplication cardinal (BrandVoicePort lifted Story 7 — sales_agent consumes Protocol, never imports PersonalityCompiler).
- **sales-agent-expert** — §3 protected surfaces (compose.py is NOT §3 — only orchestrator/graph.py + smart_debounce + OutputManager + closer_studio + WS are §3). Slot architecture preserved exactly (S3 cement). PersonalityCompiler SSoT in domain/personality.py untouched (Story 5 cement). Anti-pattern check: no `from __future__ import annotations` violation (only banned in `*/orchestrator/graph.py`, not prompts/compose.py).
- **tessl__langgraph** — Not directly invoked: compose.py operates on state TypedDict already lifted T-8, no graph topology changes here.
- **tessl__graceful-degradation** — APPLIED: voice_port.compile_system_instruction wrapped in try/except + structlog warning + best-effort fallback (state["brand_voice"] preserved from prior turn if voice port fails). NO external HTTP/LLM call directly — BrandVoicePort is in-process abstraction.
- **tessl__pytest-api-testing** — APPLIED: factory-style fake port (`_FakeVoicePort`) tracking calls. pytest-asyncio for async tests. Parametrized cases for enum vs string specialist.

## Decisions

### D-1: compose_prompt as NEW async function (not refactor existing compose_system_prompt)

**Context:** V-F-slot-5-voice-port validator (04-validators.yaml) requires `compose_prompt` function accepting `voice_port` parameter. AISALESHT has `compose_system_prompt` (fragments-based pure helper) + `build_specialist_system_prompt` (sync state-based assembler). Neither is named `compose_prompt`.

**Decision:** Add NEW `compose_prompt(specialist, state, voice_port)` async function on top of existing primitives. Delegates to `build_specialist_system_prompt` for slot composition — only logic added is voice_port consumption + state mutation.

**Rationale:**
- Preserves ALL existing AISALESHT tests (S3 cement byte-equal output for `compose_system_prompt` + `build_specialist_system_prompt`)
- Minimal new code surface (single async wrapper ~50 lines including docstring)
- Async signature mandatory: `BrandVoicePort.compile_system_instruction` is async per port contract
- D-T3 hexagonal abstraction: BrandVoicePort import is TYPE_CHECKING only — pure Protocol consumption, no runtime brand_studio dependency

**Alternatives rejected:**
- A. Rename `build_specialist_system_prompt` → `compose_prompt`: would force sync-to-async change in all upstream callers (chat.py + outbound_orchestrator.py — already lifted T-8). Massive ripple.
- B. Inject voice_port DI through state["voice_port"]: anti-pattern (state is data, not behavior). Violates LangGraph state purity.

### D-2: AISALESHT compose.py architecture clarification

**Discovery:** Ticket description assumed compose.py directly imports `PersonalityCompiler`. Reading AISALESHT code shows the actual flow:

```
chat.py / outbound_orchestrator.py
  → ConversationPipeline.build_brand_voice(db, tenant_uuid)         # sync
    → knowledge_builder.build_brand_voice(tenant_id)                # reads brand_port.get_brand_knowledge
      → brand_knowledge_repo returns personality_profile["system_instruction"]
  → state["brand_voice"] = brand_voice
  → compose.py reads state["brand_voice"]                            # slot 5 already pre-populated
```

compose.py was ALREADY hexagonal — reads from `state["brand_voice"]`, never imports PersonalityCompiler. The actual upstream coupling lives in `knowledge_builder.build_brand_voice()` (services/, T-12 territory).

**Decision:** T-11 introduces `compose_prompt` as the new canonical entry point where voice_port is consumed. T-12 will refactor `knowledge_builder` to consume voice_port. The dual existence is intentional: `build_specialist_system_prompt` remains for AISALESHT byte-equal test parity; `compose_prompt` is the new D-T3 canonical entry that orchestrator T-12 will wire.

### D-3: TYPE_CHECKING import for BrandVoicePort

**Decision:** `from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort` inside `if TYPE_CHECKING:` block.

**Rationale:**
- BrandVoicePort is `@runtime_checkable Protocol` — duck typing at runtime, no isinstance() needed
- Avoids hard dependency on brand_studio package at import time (sales_agent → brand_studio coupling minimized)
- Test isolation: `_FakeVoicePort` test class doesn't need to inherit from BrandVoicePort (Protocol structural compat)

### D-4: Conftest pre-existing bug fix (M8 extend pattern)

**Discovery:** Running tests revealed `sqlalchemy.exc.InvalidRequestError: Table 'messages' is already defined for this MetaData instance.` This is **pre-existing tech debt** from prior batches (T-5 lifted real `MessageModel` but conftest still has fallback stub block).

**Root cause:** conftest.py:158 `if "messages" not in _Base.metadata.tables:` evaluates True at conftest import (real model not imported yet). Stub registers `messages` table. Later, `_reset_singletons_between_tests` fixture triggers `_do_singleton_reset` → imports chat → conversation_pipeline → graph → infrastructure/models/message_model.py → tries to register `messages` AGAIN → collision.

**Fix (minimal, M8 compliant):** Eager-import the real `luana_core_sales_agent.infrastructure.models.message_model` BEFORE the stub guard. This populates `_Base.metadata.tables["messages"]` first → guard evaluates False → stub creation skipped → no collision later.

**Why include in T-11:** Blocks ALL test execution. Pre-existing batch 2 bug was masked because batches 2/3 didn't run pytest on the full test suite (per their impl-logs, validators stamped GREEN via grep + import checks only, not full pytest run). T-11 needed actual pytest runs for the new `test_compose_prompt_voice_port.py`. Fixing it is the minimum unblock — left a clear inline comment documenting the prior-batch origin.

**Note:** AppointmentModel stub remains as-is per D-T2 (Story 8 scheduling not yet lifted).

### D-5: Pre-existing test failures noted but out of T-11 scope

**Discovery:** `tests/prompts/test_build_specialist_system_prompt.py::TestSpecialistRoleAffectsPlaybookSlot::*` fails with Jinja `TemplateNotFound: 'specialist_product_expert.j2' not found in search path: '/home/chris/luana-platform/src/modules/sales_agent/infrastructure/prompts/templates'`.

**Root cause:** `infrastructure/prompts/base.py` line 32 hardcodes default `templates_dir = "src/modules/sales_agent/infrastructure/prompts/templates"` — an AISALESHT-style path. Templates ARE present in luana_core_sales_agent at `infrastructure/prompts/templates/` but the relative path resolves wrong.

**Decision:** Out of T-11 scope. This is **pre-existing tech debt from T-7 batch 2 commit `400cbb3`**. Logged here for T-12+ to address. T-12 may need to make templates_dir package-relative via `importlib.resources` or `pathlib.Path(__file__).parent / "templates"`.

**Impact:** 2 tests fail, 84 pass. Does not block D-T3 cardinal validation.

## Cross-module audit (NO-NEW-LAYER)

| Surface I touched | Existing in shared/ or cross-module | Decision |
|---|---|---|
| `luana_core_sales_agent.application.prompts.compose.compose_prompt` (NEW) | No analog — first hexagonal entry point for sales_agent voice consumption | NEW (per D-T3 ADR-001 §2.4 pre-ratified) |
| `BrandVoicePort` consumption | Port exists in `luana_core_brand_studio.application.ports.brand_voice_port` (Story 7 T-3 introduced) | EXTEND (consume Protocol from existing port — exactly what hexagonal abstraction is for) |
| conftest message_model stub | Real `MessageModel` lifted T-5 batch 2 at `luana_core_sales_agent.infrastructure.models.message_model` | EXTEND (eager-import existing real model before guard — no new layer) |

Zero new infrastructure layers introduced. compose_prompt is a new application-layer function consuming an existing application-layer port.

## Files created (luana-platform)

### src — 4 files
- `core/luana-core-sales-agent/src/luana_core_sales_agent/application/quality/__init__.py`
- `core/luana-core-sales-agent/src/luana_core_sales_agent/application/quality/judge.py` (SalesAgentJudge S10, 5 dimensions, NANO, fail-soft — verbatim sed)
- `core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/__init__.py`
- `core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py` (S3 6-slot + CACHE_BOUNDARY_MARKER + NEW `compose_prompt` async D-T3 entry point)

### tests — 9 files
- `core/luana-core-sales-agent/tests/application/quality/__init__.py`
- `core/luana-core-sales-agent/tests/application/prompts/__init__.py`
- `core/luana-core-sales-agent/tests/application/prompts/test_compose_slot_campaign_context.py` (PR-7 lift)
- `core/luana-core-sales-agent/tests/application/prompts/test_compose_prompt_voice_port.py` ★ NEW (15 D-T3 tests — signature, voice consumption, state mutation, resilience, slot invariants)
- `core/luana-core-sales-agent/tests/prompts/__init__.py`
- `core/luana-core-sales-agent/tests/prompts/test_brand_voice_slot.py` (S7 slot 5 lift)
- `core/luana-core-sales-agent/tests/prompts/test_build_specialist_system_prompt.py` (S3 lift)
- `core/luana-core-sales-agent/tests/prompts/test_channel_format_hint_slot.py` (S5 lift)
- `core/luana-core-sales-agent/tests/prompts/test_compose_system_prompt.py` (S3 cement lift)

### Modified — 1 file
- `core/luana-core-sales-agent/tests/conftest.py` (D-4 fix: eager-import real MessageModel before stub guard)

## Verification

### V-F-slot-5-voice-port — GREEN

```bash
$ cd /home/chris/luana-platform && uv run python -c "
import inspect
from luana_core_sales_agent.application.prompts.compose import compose_prompt
sig = inspect.signature(compose_prompt)
assert 'voice_port' in sig.parameters
print('Signature:', sig)
"
Signature: (specialist: 'SpecialistRole | str', state: 'AgentState', voice_port: 'BrandVoicePort') -> 'str'
```

### D-T3 cardinal — GREEN

```bash
$ grep -rn "PersonalityCompiler" core/luana-core-sales-agent/src/
core/luana-core-sales-agent/src/luana_core_sales_agent/__init__.py:8:    never imports ``PersonalityCompiler`` directly. Arch fitness V-AG-3
core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py:397:    ``PersonalityCompiler`` directly. ``BrandVoicePort`` lives in
core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py:407:    Story 5 PersonalityCompiler-backed via brand-studio service binding).
```

All 3 matches are **docstring text explicitly documenting that we don't import PersonalityCompiler**. Zero actual Python import statements.

```bash
$ grep -rn "^[[:space:]]*from luana_core_brand_studio" core/luana-core-sales-agent/src/
core/luana-core-sales-agent/src/luana_core_sales_agent/application/prompts/compose.py:48:    from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort
```

Single match: the **port** (Protocol) inside `if TYPE_CHECKING:` block — exactly the hexagonal pattern D-T3 mandates.

### V-NF-2 — GREEN

Zero `from src.*` cross-module leaks in any T-11 touched file.

### Test execution — 84/86 PASS

```bash
$ cd /home/chris/luana-platform && uv run pytest \
    core/luana-core-sales-agent/tests/application/prompts/ \
    core/luana-core-sales-agent/tests/prompts/ \
    -p no:cacheprovider -q --tb=line
84 passed, 2 failed in 144.05s
```

- ALL 15 NEW `test_compose_prompt_voice_port.py` tests PASS — D-T3 cardinal fully validated
- 69 of 71 lifted AISALESHT tests PASS (S3 + S5 + S7 + PR-7 cement preserved)
- 2 failures = pre-existing T-7 batch 2 templates_dir absolute path issue (out of T-11 scope, documented in D-5)

## Validators addressed

- **V-F-slot-5-voice-port** ✅ — `compose_prompt(specialist, state, voice_port)` signature verified
- **V-F-prompt-cache** ✅ — 5-slot architecture preserved (`PROMPT_FRAGMENT_ORDER` cement, `CACHE_BOUNDARY_MARKER` placement unchanged)
- **V-NF-2** ✅ — zero `from src.*` cross-module leaks
- **V-AG-3 prep** ✅ — zero PersonalityCompiler direct imports (Story 7 arch fitness gate, validated later)

## Commit

```
042db79 feat(luana-core-sales-agent): lift application quality+prompts + D-T3 compose_prompt slot 5 BrandVoicePort consumer wiring (ADR-001 §2.4)
14 files changed, 1968 insertions(+), 3 deletions(-)
```

## Hard rules honored

- ★ AISALESHT UNTOUCHED — V-NF-4 cardinal preserved (zero AISALESHT writes)
- ★ Story 5 SSoT cement intact — `PersonalityCompiler` location at `luana_core_brand_studio.domain.personality` unchanged; signature unchanged
- ★ D-T3 cardinal cement — zero direct `PersonalityCompiler` imports in luana-core-sales-agent src/
- ★ 5-slot prompt cache architecture preserved exactly — only slot 5 source changes (via new D-T3 wrapper)
- ★ voice_port threaded via DI through new `compose_prompt` entry point (T-12 will wire knowledge_builder + orchestrator callers)
- NO git pull, NO --force, NO --no-verify
- Pre-commit hook honored (commit succeeded with hook checks)
