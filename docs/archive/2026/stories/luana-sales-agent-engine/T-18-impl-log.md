# T-18 impl-log

**Ticket:** T-18 (Story 7 luana-sales-agent-engine)
**Owner:** builder-agentic Opus 4.7 (R23)
**Started:** 2026-05-12
**Completed:** 2026-05-12
**Commit:** `9d497d6` (luana-platform)

## Scope

Create 8 NEW architectural fitness tests cementing Story 7 invariants
(V-AG-1 through V-AG-8) + sha256 snapshot v1 for §3 protected surfaces.

## Skills Consulted

- **copilot-expert**: arch fitness ratchet pattern — confirmed shrink-only
  for ratchet tests; new tests for Story 7 are additive, not ratchet
  candidates (Story 7 is lift, not delta on existing surface).
- **sales-agent-expert**: §3 protected surfaces list (13 files
  canonical) + D-T3 + D-T6 cardinals.
- **tessl__langgraph**: not invoked — pure file-scanning tests.
- **tessl__pytest-api-testing**: not invoked — pure assertion-style tests.

## Templates Source

Story 6 V-AG-* tests in `core/tests/architecture/`:
- `test_story6_brand_agnostic_engine.py` — template for V-AG-1
- `test_story6_no_forward_module_imports.py` — template for V-AG-2
- `test_no_mirror_observability_in_copilot.py` — template for V-AG-6
- `test_voice_compiler_ssot_still_intact.py` — template for V-AG-7

## 8 NEW Tests Created

### V-AG-1: `test_story7_brand_agnostic_engine.py` (4 assertions)

luana-core-sales-agent must be brand-agnostic. Patterns flagged:
- `if brand ==`, `if tenant.brand ==`, `if self.brand ==`
- `brand == "{nicolify|vitalia|comunify|lupulo}"`
- Hardcoded Clerk app IDs (`app_[A-Za-z0-9]{10,}`)
- Hardcoded API_KEY/SECRET/TOKEN literals (must reference env/settings)

Story 7 parity of Story 6 V-AG-1.

### V-AG-2: `test_story7_no_forward_module_imports.py` (3 assertions)

luana-core-sales-agent must not import forward stories:
- `luana_core_campaigns` (Story 8): NO imports at all
- `luana_core_advertising` (Story 8): NO imports at all
- `luana_core_social_media` (Story 9): NO imports at all
- `luana_core_scheduling` (Story 8): only TYPE_CHECKING / function-local
  imports allowed (AST walk verifies top-level imports flagged).
- No `from src.modules.*` AISALESHT paths.

### V-AG-3: `test_sales_agent_uses_voice_port_no_direct_compiler_import.py` (2 assertions)

D-T3 cardinal — luana-core-sales-agent MUST NOT:
- Import `luana_core_brand_studio.domain.personality.PersonalityCompiler`
- Use any active code reference to `PersonalityCompiler(...)` or
  `PersonalityCompiler.X` attribute access.

Docstring + comment mentions are ALLOWED (using triple-quote-aware
lexer in test that strips docstrings before scan). compose_prompt must
import + declare `voice_port: BrandVoicePort` arg.

**Issue resolved during T-18:** initial regex `\bPersonalityCompiler\b`
flagged 4 docstring mentions. Refined to require executable reference
patterns (`PersonalityCompiler(`, `PersonalityCompiler.[a-z_]`) + AST/
lexer-aware docstring stripping.

### V-AG-4: `test_voice_port_interface_complete.py` (4 assertions)

BrandVoicePort surface FROZEN at Story 7 introduction:
- Is `typing.Protocol` (hexagonal port discipline)
- `compile_system_instruction(tenant_id: UUID) -> str` async exists
- `get_voice_metadata(tenant_id: UUID) -> dict` async exists
- Exactly 2 public methods (extra methods = drift = halt criterion #2)

### V-AG-5: `test_no_eval_framework_lifted.py` (3 assertions)

Per outcome §2 OQ1 + Session 3 ratificación 2. WAIVED to Luana v0.2.0:
- `src/observability/eval_simulator/` subfolder MUST NOT exist
- `src/eval_simulator/` subfolder MUST NOT exist
- `src/application/eval_simulator/` subfolder MUST NOT exist
- `tests/eval_simulator/` empty allowed but no .py files
- `tests/agentic_evals/` empty allowed but no .py files
- No `eval_runner.py`, `maj_eval.py`, `grader.py`,
  `voice_fidelity_grader.py`, `personas_loader.py`, `judge_prompts.py`
  anywhere in lifted src.

### V-AG-6: `test_no_mirror_observability_in_sales_agent.py` (4 assertions)

D-T6 anti-mirror cement — NO class redeclarations of:
- FXResolver, PricingResolver, CostCalculator,
  BaseObservabilityContext, BaseAgentCallbackHandler

No function declaration of `sanitize_payload` (only import allowed).
SalesAgentCallbackHandler subclasses BaseAgentCallbackHandler.
SalesAgentObservabilityContext subclasses BaseObservabilityContext.

Story 7 parity of Story 6 V-AG-5.

### V-AG-7: `test_voice_compiler_ssot_still_intact_story7.py` (3 assertions)

Stories 5+6+7 regression cement — `class PersonalityCompiler` exists
ONLY in `luana_core_brand_studio.domain.personality`. NO mirror in
luana-core-sales-agent. NO mirror anywhere in core/ workspace.

### V-AG-8: `test_sales_agent_protected_surfaces_intact.py` (3 assertions)

§3 13 canonical files sha256 hash-stable via snapshot v1.

Snapshot file: `_snapshots/sales_agent_protected_surfaces_v1.json`.
Generated at T-18 lift moment (post-sed post-ruff hashes).

13 files snapshotted:

1. `api/closer_studio.py`
2. `api/ws.py`
3. `api/enrollments.py`
4. `application/orchestrator/smart_debounce_runner.py`
5. `application/orchestrator/tool_call_dedup.py`
6. `application/services/enrollment_service.py`
7. `application/tools/payment/webhook_providers.py`
8. `application/tools/scheduling/webhook_providers.py`
9. `domain/enrollment.py`
10. `infrastructure/external/output_manager.py`
11. `infrastructure/models/enrollment_model.py`
12. `infrastructure/models/prompt_version_model.py`
13. `workers/follow_up_engine.py`

Hash drift = halt (sales-agent-expert SKILL.md §3 cardinal).

## Results

```
$ cd ~/luana-platform && uv run pytest \
    core/tests/architecture/test_story7_brand_agnostic_engine.py \
    core/tests/architecture/test_story7_no_forward_module_imports.py \
    core/tests/architecture/test_sales_agent_uses_voice_port_no_direct_compiler_import.py \
    core/tests/architecture/test_voice_port_interface_complete.py \
    core/tests/architecture/test_no_eval_framework_lifted.py \
    core/tests/architecture/test_no_mirror_observability_in_sales_agent.py \
    core/tests/architecture/test_voice_compiler_ssot_still_intact_story7.py \
    core/tests/architecture/test_sales_agent_protected_surfaces_intact.py \
    -v --tb=short

============================== 26 passed in 0.48s ==============================
```

26/26 assertions PASS aggregate Story 7 V-AG-* suite.

## Files Created (luana-platform)

```
A core/tests/architecture/_snapshots/sales_agent_protected_surfaces_v1.json
A core/tests/architecture/test_no_eval_framework_lifted.py
A core/tests/architecture/test_no_mirror_observability_in_sales_agent.py
A core/tests/architecture/test_sales_agent_protected_surfaces_intact.py
A core/tests/architecture/test_sales_agent_uses_voice_port_no_direct_compiler_import.py
A core/tests/architecture/test_story7_brand_agnostic_engine.py
A core/tests/architecture/test_story7_no_forward_module_imports.py
A core/tests/architecture/test_voice_compiler_ssot_still_intact_story7.py
A core/tests/architecture/test_voice_port_interface_complete.py
```

9 files created, 1064 insertions(+).

## AISALESHT Impact

**ZERO** — V-NF-4 invariant preserved.

## Halt Criteria Status

- [x] AISALESHT UNTOUCHED
- [x] D-T3 cardinal cemented (V-AG-3, V-AG-7)
- [x] D-T6 anti-mirror cemented (V-AG-6)
- [x] §3 hash-stable cemented (V-AG-8)
- [x] No forward imports cemented (V-AG-2)
- [x] Brand-agnostic cemented (V-AG-1)
- [x] BrandVoicePort interface frozen (V-AG-4)
- [x] No eval framework lifted (V-AG-5)
- [x] All 26 assertions GREEN
