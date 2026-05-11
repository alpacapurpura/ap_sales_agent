---
story_id: luana-sales-agent-engine
guidelines_version: 1
last_modified: 2026-05-11
drafted_by: /architect-orchestrator (claude-opus-4-7)
authority: 03-arch.md + 03-arch-agentic.md + 00-story.md + outcome §7.3 lift mode + §7.2 Stories 6+7 autonomy + ADR-001 §2.4 BrandVoicePort + 6 D-T decisiones + 3 ratificaciones + sales-agent-expert SKILL.md §3 protected surfaces + Story 5+6 05-guidelines.md pattern reference
---

# 05-guidelines.md — luana-sales-agent-engine

> **/dev-team reads this BEFORE picking ANY ticket.** R23 mandate: ALL Story 7 tickets owner = builder-agentic Opus 4.7 (NO Sonnet — production agentic code). **CRITICAL: Story 7 introduces D-T3 BrandVoicePort + adapter in luana-core-brand-studio package — this is the ONLY story-7 ticket that modifies brand-studio.**

## §1. Patterns Required

### §1.1 Lift mode (outcome §7.3)

Same as Story 6 §1.1 — verbatim, preserve names, preserve DDD, preserve tests, preserve registries, preserve protected surfaces, version 0.0.7-alpha.

**KEY EXCEPTION:** Story 7 introduces D-T3 NEW abstractions:
- `BrandVoicePort` Protocol in `luana-core-brand-studio.application.ports.brand_voice_port`
- `BrandVoiceService` adapter in `luana-core-brand-studio.application.services.brand_voice_service`

This is the ONLY scope expansion permitted Story 7. Per ADR-001 §2.4 + Story 5 §9.4 deferral resolution + Session 3 ratificación.

### §1.2 Workspace registration (T-1)

Add `core/luana-core-sales-agent` to root pyproject.toml — same template Stories 2-6.

### §1.3 D-T3 BrandVoicePort introduction (T-3 — CRITICAL UNIQUE TICKET)

**This is the ONLY ticket that modifies luana-core-brand-studio package.** Per ADR-001 §2.4 pre-ratified design.

Create files:

```python
# core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/__init__.py
# (new __init__ if ports/ subfolder doesn't exist)

# core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/brand_voice_port.py
from __future__ import annotations
from typing import Protocol, runtime_checkable
from uuid import UUID

@runtime_checkable
class BrandVoicePort(Protocol):
    """Voice compiler port — consumed by luana-core-sales-agent slot 5 BRAND_VOICE prefix.

    Per ADR-001 §2.4: PersonalityCompiler lives in luana-core-brand-studio.domain.personality.
    BrandVoicePort wraps it for cross-module consumption — sales-agent never imports
    PersonalityCompiler directly (hexagonal DDD boundary).
    
    Public methods FROZEN at Story 7 introduction.
    """

    async def compile_system_instruction(self, tenant_id: UUID) -> str:
        """Compile tenant's PersonalityProfile to 5-block system_instruction.
        Returns empty string if tenant has no PersonalityProfile (fallback to default voice).
        """
        ...

    async def get_voice_metadata(self, tenant_id: UUID) -> dict:
        """Return voice metadata for prompt cache invalidation:
        - personality_profile_version: int (bumps on profile update)
        - last_compiled_at: datetime | None
        - dimensions_summary: dict (energy, warmth, humor — for routing decisions)
        """
        ...
```

```python
# core/luana-core-brand-studio/src/luana_core_brand_studio/application/services/brand_voice_service.py
from __future__ import annotations
import structlog
from uuid import UUID

from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort
from luana_core_brand_studio.domain.personality import PersonalityCompiler
from luana_core_brand_studio.infrastructure.repositories.personality_repository import PersonalityRepository

logger = structlog.get_logger()


class BrandVoiceService:
    """Concrete adapter implementing BrandVoicePort.
    
    Per ADR-001 §2.4 — engine lives here in core-brand-studio. Consumer
    (luana-core-sales-agent) injects this via DI factory pattern.
    """
    
    def __init__(self, repo: PersonalityRepository, compiler: PersonalityCompiler):
        self._repo = repo
        self._compiler = compiler

    async def compile_system_instruction(self, tenant_id: UUID) -> str:
        profile = await self._repo.get_for_tenant(tenant_id)
        if profile is None:
            logger.debug("brand_voice_service.no_profile_fallback_empty", tenant_id=str(tenant_id))
            return ""  # fallback to specialist default voice
        return self._compiler.compile(profile)

    async def get_voice_metadata(self, tenant_id: UUID) -> dict:
        profile = await self._repo.get_for_tenant(tenant_id)
        if profile is None:
            return {"personality_profile_version": 0, "last_compiled_at": None, "dimensions_summary": {}}
        return {
            "personality_profile_version": getattr(profile, "version", 1),
            "last_compiled_at": getattr(profile, "last_compiled_at", None),
            "dimensions_summary": profile.dimensions.summary() if hasattr(profile, "dimensions") and hasattr(profile.dimensions, "summary") else {},
        }
```

**Per BrandVoiceService init:**
- Verify Protocol conformance via duck-typing — `BrandVoicePort` is `@runtime_checkable` Protocol; `BrandVoiceService` satisfies by method signatures.
- If `PersonalityProfile` doesn't have `version` / `last_compiled_at` attrs (Story 5 lift didn't add) — graceful default via `getattr`.

**Add test file (T-3):**
```python
# core/luana-core-brand-studio/tests/test_brand_voice_service.py
import pytest
from luana_core_brand_studio.application.services.brand_voice_service import BrandVoiceService
from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort

# Test contract conformance + behavior (mock repo + compiler) — ~6 tests
```

**KEY:** D-T3 introduction does NOT modify PersonalityCompiler. SSoT cement (Story 5 V-AG-3) intact.

### §1.4 Import path rewriting (mechanical sed) — Story 7

Same template as Story 6 §1.3 with substitutions:

```bash
cd ~/luana-platform/core/luana-core-sales-agent

# Self-imports
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.sales_agent\.|from luana_core_sales_agent.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|import src\.modules\.sales_agent\.|import luana_core_sales_agent.|g' {} \;

# Cross-module Stories 2-6
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.iam\.|from luana_core_iam.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.brand\.|from luana_core_brand_studio.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.offer\.|from luana_core_offer_studio.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.crm\.|from luana_core_crm.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.modules\.copilot\.|from luana_core_copilot.|g' {} \;

# Shared → luana-core-platform / observability / events / etc.
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.|from luana_core_observability.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain_events\.|from luana_core_events.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.idempotency\.|from luana_core_idempotency.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.billing\.|from luana_core_billing.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.compliance\.|from luana_core_compliance.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.llm\.|from luana_core_llm.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.agent_observability\.channels\.|from luana_core_channels.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.domain\.|from luana_core_platform.domain.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.links\.|from luana_core_platform.links.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.infrastructure\.|from luana_core_platform.infrastructure.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.application\.|from luana_core_platform.application.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.shared\.workers\.|from luana_core_platform.workers.|g' {} \;
find src tests -name "*.py" -exec sed -i 's|from src\.core\.|from luana_core_platform.core.|g' {} \;

# CRITICAL: scheduling deferred imports — leave src.modules.scheduling.* as-is in deferred-import contexts
# (TYPE_CHECKING + inside-method-body imports — they reference future luana_core_scheduling which lifts Story 8)
# But: src.shared.links.ports.scheduling → luana_core_platform.links.ports.scheduling (already in §1.4 above via shared.links rewrite)
```

### §1.5 D-T6 observability subclass invariant (CRITICAL — same as Story 6 §1.4)

When lifting `sales_agent/observability/recording/callback_handler.py`:

1. Verify inherits, not redefines:
   ```python
   from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler
   class SalesAgentCallbackHandler(BaseAgentCallbackHandler):
       ...
   ```

2. Verify via grep post-lift:
   ```bash
   grep -rE "class (FXResolver|CostCalculator|PricingResolver|BaseObservabilityContext|BaseAgentCallbackHandler)\b" \
       core/luana-core-sales-agent/src/luana_core_sales_agent/
   # → expected: empty
   ```

3. T-3 + T-14 arch tests V-AG-6 enforces.

### §1.6 Eval framework EXCLUSION (per ratificación 2 + outcome §2 OQ1)

When lifting sales_agent, **SKIP `observability/eval_simulator/` subfolder entirely**:

```bash
# Explicit per-subfolder copy (NOT cp -r module/*):
SRC=/home/chris/AISALESHT/backend/src/modules/sales_agent

for sub in __init__.py domain infrastructure application observability/recording observability/persistence observability/workers observability/domain_events observability/__init__.py workers api copilot_provider; do
    if [ -e "$SRC/$sub" ]; then
        DST=~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/$(dirname "$sub")
        mkdir -p "$DST"
        cp -r "$SRC/$sub" "$DST/"
    fi
done

# DO NOT lift: $SRC/observability/eval_simulator (entire subfolder)
# Verify:
test -d ~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/observability/eval_simulator \
    && echo "FAIL: eval_simulator leaked into Story 7 lift" || echo "OK: eval_simulator NOT lifted"
```

**Test lift EXCLUSIONS (per §9.1 +  V-AG-5):**

```bash
# DO NOT lift these test paths:
# backend/tests/modules/sales_agent/eval_simulator/  ← SKIP
# backend/tests/agentic_evals/                       ← SKIP (entire tree)

# Use rsync with explicit excludes:
rsync -av \
      --exclude='eval_simulator/' \
      --exclude='**/eval_*.py' \
      /home/chris/AISALESHT/backend/tests/modules/sales_agent/ \
      ~/luana-platform/core/luana-core-sales-agent/tests/
```

### §1.7 §3 protected surfaces preservation (sales-agent-expert SKILL.md §3)

**12 files require sha256 hash-stable lift** — DO NOT MODIFY beyond mechanical sed rewrites of imports:

1. `api/closer_studio.py` + `api/ws.py`
2. `application/orchestrator/smart_debounce_runner.py`
3. `infrastructure/external/output_manager.py`
4. `application/services/enrollment_service.py`
5. `domain/enrollment.py`
6. `infrastructure/models/enrollment_model.py`
7. `api/enrollments.py`
8. `application/tools/payment/webhook_providers.py`
9. `application/tools/scheduling/webhook_providers.py`
10. `workers/follow_up_engine.py`
11. `infrastructure/models/prompt_version_model.py`
12. `application/orchestrator/tool_call_dedup.py`

T-18 arch test V-AG-8 verifies sha256 against AISALESHT source.

**Sed-only allowed changes:** import path rewrites per §1.4. NO logic refactor, NO formatting, NO renames.

### §1.8 T-16 connections wiring resolution

`luana-core-connections/api/dependencies/__init__.py` has `NotImplementedError` stub from Story 4 (per Story 4 §9.2 + Story 6 §9.2 deferred to Story 7).

**Replace stub with real wiring:**

```python
# core/luana-core-connections/src/luana_core_connections/api/dependencies/__init__.py
"""ChatOrchestrator dependency injection — Story 7 resolution."""

from luana_core_copilot.application.orchestrator.graph import build_deep_agent_graph
from luana_core_sales_agent.application.orchestrator.graph import build_sales_agent_graph
from luana_core_platform.domain.ports import MessageHandlerPort

# concrete wiring per AISALESHT pattern (read backend/src/modules/connections/api/dependencies/__init__.py
# AISALESHT version for exact composition root code — preserve verbatim, just sed paths)

async def get_message_handler() -> MessageHandlerPort:
    """Resolve MessageHandlerPort concrete impl — replaces Story 4 NotImplementedError stub."""
    # Composition root logic from AISALESHT — lift verbatim with sed
    ...
```

Read AISALESHT `backend/src/modules/connections/api/dependencies/__init__.py` for exact composition root code. Lift verbatim with sed.

Run connections tests GREEN post-T-16:
```bash
cd ~/luana-platform && uv run pytest core/luana-core-connections/tests/ -x -q
```

### §1.9 Spanish neutro EXCEPTION (sales-agent output)

Per `.claude/rules/spanish-text.md` § "Excepción sales_agent":
- Sales agent OUTPUT respects tenant voice (voseo OK if tenant AR — depends on PersonalityProfile)
- ALL OTHER strings (error messages, tool descriptions, internal copy) follow Spanish neutro LatAm

Pre-commit voseo check applies to:
- Tool descriptions (`description=` in @tool decorators)
- Error messages in raise statements
- Comments user-facing
- API DTO error responses

Does NOT apply to:
- specialist .j2 templates (these load PersonalityProfile.system_instruction at runtime — voice already compiled there)
- knowledge_builder.build_identity output (compiled voice)
- Agent prompts in compose.py slot 5 (BrandVoicePort dynamic output)

### §1.10 Test execution per package

After lift, run isolated:
```bash
cd ~/luana-platform && uv run pytest core/luana-core-sales-agent/tests/ -x -q --tb=short \
    --ignore=core/luana-core-sales-agent/tests/eval_simulator/ \
    --ignore=core/luana-core-sales-agent/tests/agentic_evals/
```

GREEN per-package before proceeding next ticket.

### §1.11 Brand-agnostic engine verification

Pre-T-18 local smoke:
```bash
cd ~/luana-platform/core/luana-core-sales-agent/src
grep -rEn 'if\s+brand\s*==|brand\s*==\s*"(nicolify|vitalia|comunify|lupulo)"' luana_core_sales_agent/ \
    && echo "FAIL" || echo "OK"
```

If FAILs → escalate per §6 halt #7.

## §2. Patterns Forbidden

### §2.1 Lift mode violations (auto-FAIL)

Same as Story 6 §2.1 +:
- ❌ Adding methods to BrandVoicePort beyond `compile_system_instruction` + `get_voice_metadata`. Surface FROZEN at Story 7 introduction. If gap detected → halt + escalate.
- ❌ Importing PersonalityCompiler from luana-core-brand-studio.domain.personality in any luana_core_sales_agent file (D-T3 cardinal).
- ❌ Mirroring PersonalityCompiler class in luana_core_sales_agent (regression Story 5 SSoT cement).

### §2.2 Mutating AISALESHT (auto-FAIL)

- ❌ Any file under `backend/src/modules/sales_agent/` READ-ONLY.
- ❌ Any file under `backend/tests/modules/sales_agent/` READ-ONLY.
- ❌ Any file under `backend/tests/agentic_evals/sales_agent/` READ-ONLY (eval tests stay in nicolify until Luana v0.2.0).

### §2.3 Anti-mirror discipline (D-T6 + anti-duplication.md cardinal)

Same as Story 6 §2.3.

### §2.4 Forward-Story coupling (auto-FAIL)

- ❌ Importing from luana_core_campaigns, luana_core_advertising, luana_core_social_media (Stories 8+).
- ❌ Importing from luana_core_scheduling at top-level (allowed only as TYPE_CHECKING + method-body deferred imports — verified by V-AG-2 AST check).
- ❌ Importing from src.modules.* (lift incomplete).

### §2.5 Voice compiler architectural violations (D-T3 + ADR-001 §2.4)

- ❌ Introducing `BrandVoicePort` methods beyond 2 specified (compile_system_instruction, get_voice_metadata). Surface FROZEN.
- ❌ Sales-agent importing `from luana_core_brand_studio.domain.personality import PersonalityCompiler`.
- ❌ Sales-agent declaring `class PersonalityCompiler` (regression Story 5).
- ❌ Modifying `PersonalityCompiler.compile()` signature in luana-core-brand-studio. SSoT cement Story 5.
- ❌ Modifying `PersonalityRepository.get_for_tenant()` signature.

### §2.6 Eval framework lift violations (per ratificación 2)

- ❌ Lifting `observability/eval_simulator/` subfolder to luana_core_sales_agent. Defer Luana v0.2.0.
- ❌ Lifting `agentic_evals/sales_agent/` tests. Stay in AISALESHT/nicolify until v0.2.0.
- ❌ Creating eval-related tables in luana-core-observability migration: `eval_simulator_llm_call`, `eval_simulator_trace_event`, `eval_simulator_grade`, `eval_simulator_grade_cache`, `eval_synthetic_tenants` — all Luana v0.2.0 territory.

### §2.7 §3 protected surfaces violations (sales-agent-expert SKILL.md)

- ❌ Modifying closer_studio API + WS signatures.
- ❌ Modifying SmartBufferService.smart_debounce_runner logic.
- ❌ Modifying OutputManager.process_response chunking.
- ❌ Modifying enrollment_* end-to-end paths.
- ❌ Modifying agent_state_checkpoints schema.
- ❌ Modifying webhook adapter auth/signature.
- ❌ Modifying follow_up_engine cadence math.
- ❌ Modifying PromptVersionModel schema.
- ❌ Modifying tool_call_dedup.py logic.
- ❌ Modifying typing_simulation_cpm registry fallback (S12 cement).

V-AG-8 arch test verifies via file sha256 hash.

### §2.8 Observability writes anti-patterns

Same as Story 6 §2.6 +:
- ❌ Computing tier pricing >200k inside `calculator.py` runtime (sales_agent calculator already wires LiteLLM input_cost_per_token_above_200k_tokens — preserve cement per S12).
- ❌ Bypassing `sanitize_payload` on `sales_agent_trace_event` + `sales_agent_llm_call` writes.

### §2.9 Slot architecture violations

- ❌ Inserting volatile content (timestamps, conversation_id, tenant_name) in slots 1-5 cacheable prefix.
- ❌ Reordering 5 slots.
- ❌ Removing cache_control breakpoint after slot 5.
- ❌ Failing to record cache_creation_input_tokens + cache_read_input_tokens to `sales_agent_llm_call`.

## §3. Files in Scope

### §3.1 AISALESHT (READ-ONLY source)

**Lift these:**

```
backend/src/modules/sales_agent/
├── __init__.py
├── api/                  (8 files: closer_studio, enrollments, audit, scheduler_webhooks, payment_webhooks, ws + dto/)
├── application/          (orchestrator, agents/sales/, tools/, quality, prompts, services + 16 service files)
├── domain/               (10 files: model_tier, events, message, base_entity, semantic_routes, exceptions, enums, tuning, enrollment, memory/)
├── infrastructure/       (models, repositories, memory, monitoring, prompts, external, db, ws_manager)
├── observability/
│   ├── __init__.py
│   ├── recording/        (callback_handler, turn_envelope, factory)
│   ├── persistence/      (llm_call_repo, trace_event_repo, routing_log_repo, models/)
│   ├── workers/          (dual_write_reconciliation_task)
│   ├── domain_events/    (subscribers)
│   ├── eval_simulator/   ★ DO NOT LIFT ★ (defer Luana v0.2.0 per ratificación 2)
├── workers/              (follow_up_engine, appointment_reminder_engine, frozen_detection, payment_reminder_engine, verify_pending_*)
└── copilot_provider/     (1 file: provider.py)

backend/tests/modules/sales_agent/         (~75 files — EXCLUDE eval_simulator/ subfolder)
backend/tests/agentic_evals/sales_agent/   ★ DO NOT LIFT ★ (defer Luana v0.2.0)
```

### §3.2 luana-platform (CREATE)

**Create:**
- `~/luana-platform/core/luana-core-sales-agent/{pyproject.toml,README.md,src/luana_core_sales_agent/**,tests/**}`
- `~/luana-platform/core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/{__init__,brand_voice_port}.py` (D-T3 — T-3)
- `~/luana-platform/core/luana-core-brand-studio/src/luana_core_brand_studio/application/services/brand_voice_service.py` (D-T3 — T-3)
- `~/luana-platform/core/luana-core-brand-studio/tests/test_brand_voice_service.py` (D-T3 — T-3)
- `~/luana-platform/core/tests/architecture/test_story7_brand_agnostic_engine.py`
- `~/luana-platform/core/tests/architecture/test_story7_no_forward_module_imports.py`
- `~/luana-platform/core/tests/architecture/test_sales_agent_uses_voice_port_no_direct_compiler_import.py`
- `~/luana-platform/core/tests/architecture/test_voice_port_interface_complete.py`
- `~/luana-platform/core/tests/architecture/test_no_eval_framework_lifted.py`
- `~/luana-platform/core/tests/architecture/test_no_mirror_observability_in_sales_agent.py`
- `~/luana-platform/core/tests/architecture/test_voice_compiler_ssot_still_intact_story7.py`
- `~/luana-platform/core/tests/architecture/test_sales_agent_protected_surfaces_intact.py`

**Modify:**
- `~/luana-platform/pyproject.toml` (workspace + sources)
- `~/luana-platform/core/DEFERRED-FILES.md` (Story 7 + D-T3 INTRODUCED + connections UNLIFTED + eval framework deferred + Story E waiver)
- `~/luana-platform/core/luana-core-connections/src/luana_core_connections/api/dependencies/__init__.py` (T-16 — replace NotImplementedError stub with real ChatOrchestrator wiring)

### §3.3 DEFERRED list Story 7 — DO NOT LIFT

**Defer to Luana v0.2.0 (eval framework — per ratificación 2 + outcome §2 OQ1):**
```
backend/src/modules/sales_agent/observability/eval_simulator/  (entire subfolder — 8 files)
backend/tests/agentic_evals/sales_agent/                       (entire tree)
backend/tests/modules/sales_agent/eval_simulator/              (if exists — entire subfolder)
backend/scripts/{generate_golden_candidates,promote_golden}.py (Story D goldens infra — Luana v0.2.0)
backend/tests/scripts/test_{generate_golden_candidates,promote_golden,seed_pii_scanner}.py
docs/specs/personas/                                            (Story C personas catalog — Luana v0.2.0)
```

**Defer to Story 8 (scheduling lift — campaigns-extension-sdk batch):**
- Scheduling concrete provider runtime resolution — sales_agent's `application/tools/scheduling/providers.py` lifts WITH deferred-import pattern. Runtime fails on scheduler invocation in Luana standalone until Story 8 lifts scheduling module.

**Defer to Story 10 (nicolify migration):**
- `backend/src/admin/pages/{sales-routing,sales-agent-quality,costo-agentes,llm-virtual-keys,llm-models}.py` — Streamlit admin shell.

### §3.4 Skip during cp -r — mechanical recipe

```bash
SRC=/home/chris/AISALESHT/backend/src/modules/sales_agent
DST_SRC=~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent

mkdir -p "$DST_SRC"
cp "$SRC"/__init__.py "$DST_SRC/"

for sub in api application domain infrastructure workers copilot_provider; do
  [ -e "$SRC/$sub" ] && cp -r "$SRC/$sub" "$DST_SRC/"
done

# observability — explicit subfolder lift, SKIP eval_simulator
mkdir -p "$DST_SRC/observability"
cp "$SRC"/observability/__init__.py "$DST_SRC/observability/"
for obs_sub in recording persistence workers domain_events; do
  [ -e "$SRC/observability/$obs_sub" ] && cp -r "$SRC/observability/$obs_sub" "$DST_SRC/observability/"
done

# Verify eval_simulator NOT copied:
test -d "$DST_SRC/observability/eval_simulator" \
    && echo "FAIL: eval_simulator leaked" || echo "OK: eval_simulator skipped"

# Tests lift, EXCLUDE eval-related
rsync -av \
      --exclude='eval_simulator/' \
      /home/chris/AISALESHT/backend/tests/modules/sales_agent/ \
      ~/luana-platform/core/luana-core-sales-agent/tests/
# DO NOT lift backend/tests/agentic_evals/sales_agent/ — defer Luana v0.2.0
```

## §4. Skills + Rules to Load

| Skill / Rule | When | Owner |
|---|---|---|
| `backend-expert` | All Story 7 tickets | universal |
| `sales-agent-expert` | All Story 7 tickets — §3 protected surfaces + S0-S12 cement + voice SSoT + observability subclass | **mandatory** |
| `brand-expert` | T-3 (D-T3 BrandVoicePort + adapter creation) — verify hexagonal DDD + PersonalityCompiler not moved | mandatory |
| `copilot-expert` | T-15 (sales_agent copilot_provider/provider.py subclass) — verify BaseCopilotProvider conformance | conditional |
| `tessl__langgraph` | T-8, T-9 (LangGraph orchestrator + supervisor specialist pattern) | mandatory |
| `claude-api` (Anthropic prompt caching) | T-11 (compose.py slot 5 BRAND_VOICE via BrandVoicePort) | mandatory |
| `tessl__fastapi` | T-13 (API routers — closer_studio + enrollments + webhooks) | mandatory |
| `tessl__graceful-degradation` | T-10 (payment + scheduling provider strategy — external calls with timeout/fallback) + T-7 (webhook adapters) | mandatory |
| `.claude/rules/anti-duplication.md` | T-3 (port intro — verify ADR-001 §2.4 + Story 5 SSoT intact) + T-14 (D-T6 anti-mirror observability) | mandatory |
| `.claude/rules/sales-agent-brand-voice.md` | T-11 (slot 5 BRAND_VOICE — D-T3 consumer wiring) | mandatory |
| `.claude/rules/auditor-downstream-regression.md` | All tickets — brand-studio + connections re-test post T-3 + T-16; aggregate post T-17 | mandatory |
| `.claude/rules/tdd-mandatory.md` | T-3 (port + adapter + test), T-18 (arch fitness) | mandatory |
| `.claude/rules/parallel-safety.md` | All tickets | mandatory |
| `.claude/rules/spanish-text.md` | Sales agent OUTPUT exception (voseo OK if tenant voice) — internal copy follows neutro | mandatory |
| `.claude/rules/copilot-observability.md` | T-14 (sales agent observability subfolder — module-scoped repos extends luana-core-observability) | mandatory |

## §5. Commit conventions

```
chore(workspace): register Story 7 luana-core-sales-agent package                       # T-1
feat(luana-core-sales-agent): skeleton + pyproject.toml + README                        # T-2
feat(luana-core-brand-studio): introduce BrandVoicePort + BrandVoiceService adapter (D-T3 ADR-001 §2.4)  # T-3
feat(luana-core-sales-agent): lift sales_agent domain layer                             # T-4
feat(luana-core-sales-agent): lift sales_agent infrastructure models + db               # T-5
feat(luana-core-sales-agent): lift sales_agent infrastructure repositories + memory + monitoring + prompts  # T-6
feat(luana-core-sales-agent): lift sales_agent infrastructure external (output_manager + buffer_service + safety_service) + ws_manager  # T-7
feat(luana-core-sales-agent): lift sales_agent application orchestrator (LangGraph supervisor specialists)  # T-8
feat(luana-core-sales-agent): lift sales_agent application agents/sales (specialist subgraph)  # T-9
feat(luana-core-sales-agent): lift sales_agent application tools (payment + scheduling providers strategy pattern + registry)  # T-10
feat(luana-core-sales-agent): lift sales_agent application quality + prompts (D-T3 BrandVoicePort consumer wiring slot 5)  # T-11
feat(luana-core-sales-agent): lift sales_agent application services layer (16 files)    # T-12
feat(luana-core-sales-agent): lift sales_agent api layer + workers (§3 protected surfaces hash-stable)  # T-13
feat(luana-core-sales-agent): lift sales_agent observability subfolder (subclasses luana-core-observability)  # T-14
feat(luana-core-sales-agent): lift sales_agent copilot_provider/provider.py (subclasses luana-core-copilot BaseCopilotProvider)  # T-15
chore(luana-core-connections): replace NotImplementedError stub with real ChatOrchestrator wiring (Stories 4+6 deferral resolved)  # T-16
test(luana-platform): Story 7 cross-package smoke + aggregate pytest GREEN (23 packages)  # T-17
test(arch): Story 7 D-T3+D-T6 cement + brand-agnostic + no-forward-imports + no-eval-framework + §3 protected surfaces hash + voice-port-interface  # T-18
chore(luana-platform): Story 7 lint + AISALESHT untouched + DEFERRED-FILES update (D-T3 INTRODUCED + eval framework + Story E waiver + connections wiring)  # T-19
```

## §6. Halt criteria

Halt + escalate Chris if:

1. **Cross-Story-7 coupling** — sales_agent imports campaigns/advertising/scheduling top-level. (Verified only deferred imports OK.)
2. **D-T3 BrandVoicePort scope expansion** — gap detected requiring methods beyond `compile_system_instruction` + `get_voice_metadata`. Halt + architect re-evaluates port API surface.
3. **D-T3 cardinal violation** — sales-agent imports PersonalityCompiler directly. V-AG-3 detects.
4. **D-T6 observability mirror** — V-AG-6 detects. Investigate.
5. **§3 protected surface hash mismatch** — V-AG-8 detects modification beyond sed import rewrites. Investigate.
6. **Eval framework leak** — V-AG-5 detects eval_simulator/ or agentic_evals/ in luana-core-sales-agent. Revert + re-lift with §1.6 explicit subfolder loop.
7. **Auditor REJECTED + 3 auto-fix Opus iter fail** — escalate per outcome §7.4.
8. **Scope expansion** — any "small refactor" touching files beyond §3 list. Includes EP-1..EP-5 SDK abstractions (Story 8), voice cloning pipeline (Stories 11-13).
9. **Cumulative cost > $1500 + Story 6 cumulative** — soft check-in.
10. **Brand-specific code in supposedly brand-agnostic engine** — V-AG-1 fails.
11. **DEFERRED file leaks into lift** — `grep "from src.modules.(campaigns|advertising|social_media)"` post-sed.
12. **Test count drop > 5%** — preserve test count from AISALESHT baseline (~75 sales_agent tests excluding eval).
13. **PersonalityCompiler signature change** — V-AG-7 regression Stories 5+6 detects. SSoT cement.
14. **T-3 brand-studio tests regression** — 34 existing Story 5 tests must stay GREEN. New BrandVoicePort + BrandVoiceService adds tests, doesn't break existing.
15. **T-16 connections wiring breaks connections tests** — V-F-py-3 fails. Investigate composition root.
16. **Scheduling tool runtime broken in standalone Luana** — expected post-Story-7 until Story 8. Document as known-limitation in README + DEFERRED-FILES.

## §7. Sub-builder spawn template

```
Agent({
  description: "Lift sales_agent <surface> — T-N",
  subagent_type: "builder-agentic",
  model: "opus",  // R23 MANDATORY — production agentic code
  prompt: "
    <pr_folder>: /home/chris/AISALESHT/docs/product/stories/luana-sales-agent-engine
    <ticket>: T-N

    Lift sales_agent <surface> from AISALESHT to luana-platform per:
    - 00-story.md scope + ratificación 2 (eval WAIVED Luana v0.2.0)
    - 03-arch.md §3 + §5 + §9 + ADR-001 §2.4
    - 03-arch-agentic.md (supervisor pattern + slot 5 BRAND_VOICE via D-T3 + observability subclass)
    - 05-guidelines.md §1.4 (sed) + §1.5 (D-T6 critical) + §1.6 (eval EXCLUDE) + §1.7 (§3 protected) + §3.4 (cp -r recipe)
    - Validators GREEN: V-NF-2 + V-F-py-1 + addressed_by per ticket

    DO NOT TOUCH AISALESHT.
    DO NOT lift eval_simulator/ or agentic_evals/ (Luana v0.2.0).
    DO NOT modify §3 protected surfaces beyond import sed.
    DO NOT introduce abstractions beyond D-T3 (BrandVoicePort + BrandVoiceService in T-3 only).
    DO NOT mirror observability bases (D-T6 cardinal — V-AG-6 enforces).
    DO NOT import PersonalityCompiler directly from sales_agent (D-T3 cardinal — V-AG-3 enforces).
    DO NOT mirror PersonalityCompiler in sales_agent (regression Story 5 SSoT cement).
    DO NOT modify PersonalityCompiler signature in luana-core-brand-studio.
    Conventional commit per §5.
    Last line: 'done -> <commit-sha>' or 'failed -> <reason>'.
  "
})
```

## §8. Verification recipe per ticket close

```bash
# 1. Package tests GREEN (excluding eval per V-F-py-1)
cd ~/luana-platform && uv run pytest core/luana-core-sales-agent/tests/ -x -q --tb=short \
    --ignore=core/luana-core-sales-agent/tests/eval_simulator/ \
    --ignore=core/luana-core-sales-agent/tests/agentic_evals/

# 2. Ruff clean
cd ~/luana-platform && uv run ruff check core/luana-core-sales-agent

# 3. No leaked src.modules.* or forward-Story imports
grep -rEn "from src\.modules\." ~/luana-platform/core/luana-core-sales-agent/src/ && echo "FAIL: src.modules leak" || echo "OK"
grep -rEn "from luana_core_(campaigns|advertising|social_media)" ~/luana-platform/core/luana-core-sales-agent/src/ && echo "FAIL: forward Story" || echo "OK"
# Top-level scheduling forbidden — TYPE_CHECKING + method-body deferred OK
grep -rEn "^from luana_core_scheduling" ~/luana-platform/core/luana-core-sales-agent/src/ && echo "FAIL: top-level scheduling" || echo "OK"

# 4. AISALESHT untouched
cd /home/chris/AISALESHT
git diff HEAD --name-only | grep -E '^(backend/src/modules/sales_agent|backend/tests/modules/sales_agent|backend/tests/agentic_evals/sales_agent)/' && echo "FAIL" || echo "OK"

# 5. eval_simulator NOT lifted
test -d ~/luana-platform/core/luana-core-sales-agent/src/luana_core_sales_agent/observability/eval_simulator \
    && echo "FAIL: eval_simulator leaked" || echo "OK: eval excluded"

# 6. (after T-3) brand-studio still GREEN with new port + adapter
cd ~/luana-platform && uv run pytest core/luana-core-brand-studio/tests/ -x -q

# 7. (after T-14) D-T6 subclass invariant
cd ~/luana-platform && uv run python -c "
from luana_core_sales_agent.observability.recording.callback_handler import SalesAgentCallbackHandler
from luana_core_observability.recording.base_callback_handler import BaseAgentCallbackHandler
assert issubclass(SalesAgentCallbackHandler, BaseAgentCallbackHandler)
print('D-T6 subclass OK')"

# 8. (after T-16) connections GREEN with real wiring
cd ~/luana-platform && uv run pytest core/luana-core-connections/tests/ -x -q

# 9. (after T-18) all 8 NEW arch fitness tests GREEN
cd ~/luana-platform && uv run pytest core/tests/architecture/test_story7_*.py \
    core/tests/architecture/test_sales_agent_*.py \
    core/tests/architecture/test_voice_port_*.py \
    core/tests/architecture/test_no_eval_framework_lifted.py \
    core/tests/architecture/test_voice_compiler_ssot_still_intact_story7.py \
    core/tests/architecture/test_no_mirror_observability_in_sales_agent.py \
    -x -q

# 10. §3 protected surface hashes
cd ~/luana-platform && uv run pytest core/tests/architecture/test_sales_agent_protected_surfaces_intact.py -x -q
```

## §9. Common pitfalls + remedies

| Pitfall | Symptom | Remedy |
|---|---|---|
| eval_simulator/ accidentally lifted | V-AG-5 fails / dir exists in src/ | rm -r src/luana_core_sales_agent/observability/eval_simulator; re-verify §1.6. |
| §3 surface hash mismatch | V-AG-8 fails | Check sha256 of suspect file vs AISALESHT. If sed altered comments/strings, narrow sed pattern. |
| Slot 5 BRAND_VOICE compose_prompt signature missing voice_port | V-F-slot-5-voice-port fails | T-11 must wire voice_port: BrandVoicePort param. Re-read 03-arch-agentic.md §3. |
| BrandVoicePort missing method | V-AG-4 fails | T-3 port spec frozen at 2 methods (compile_system_instruction, get_voice_metadata). If gap → halt. |
| PersonalityCompiler accidentally imported in sales_agent | V-AG-3 fails | grep "PersonalityCompiler" core/luana-core-sales-agent/ → must be empty. Replace with BrandVoicePort. |
| connections/api/dependencies stub not replaced | V-F-py-3 fails | T-16 must complete. Read AISALESHT version for composition root code. |
| LangGraph supervisor specialist routing tests fail | V-F-langgraph fails | Verify state TypedDict has current_specialist key. State graph compiles. |
| sales_agent_llm_call vs eval_simulator_llm_call confusion | Cost bucket invariant broken | These ARE separate tables. Sales agent runtime writes to sales_agent_llm_call (Story 2 lifted to luana-core-observability). Eval framework writes to eval_simulator_llm_call (NOT lifted Story 7). Cost-bucket separation preserved at lift moment for v0.2.0 future. |
| typing_simulation_cpm registry not preserved | OutputManager chunking broken on tenant override | S12 cement preserved. Verify fallback CPM_SPEED_DEFAULT path intact. |
| Spanish voseo violation in tool description | Pre-commit hook FAIL | Tool descriptions follow Spanish neutro (NOT tenant voice). Agent OUTPUT respects voice. See spanish-text.md §Excepción sales_agent + magic comment R25. |
| Scheduling concrete provider runtime fails standalone | Expected per §9.2 — Story 8 lifts scheduling | Document in README. nicolify shell wires scheduling pre-Story 8. |
