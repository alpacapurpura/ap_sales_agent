---
story_id: luana-sales-agent-engine
ticket_id: T-3
state: done
owner: builder-agentic (Opus 4.7 — R23 mandatory)
started_at: 2026-05-12
closed_at: 2026-05-12
authority: 06-tickets.yaml T-3 + 05-guidelines.md §1.3 + 03-arch.md §1.3 + ADR-001 §2.4 + Story 5 §9.4 deferral resolution
criticality: ★ CRITICAL UNIQUE — ONLY Story 7 ticket modifying luana-core-brand-studio
---

# T-3 — D-T3 BrandVoicePort + BrandVoiceService impl-log

## Outcome

GREEN — hexagonal port + adapter introduced in `luana-core-brand-studio` per ADR-001 §2.4. Story 5 SSoT cement intact (PersonalityCompiler still in `domain/personality.py`, signature unchanged).

## Files created

- `~/luana-platform/core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/__init__.py` — exports `BrandVoicePort`
- `~/luana-platform/core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/brand_voice_port.py` — `@runtime_checkable` Protocol with 2 FROZEN async methods (`compile_system_instruction`, `get_voice_metadata`)
- `~/luana-platform/core/luana-core-brand-studio/src/luana_core_brand_studio/application/services/brand_voice_service.py` — concrete adapter wrapping `PersonalityProfileRepository` (sync) + `PersonalityCompiler.compile` (static method). Best-effort design with structlog warnings + empty/"" fallbacks.
- `~/luana-platform/core/luana-core-brand-studio/tests/test_brand_voice_service.py` — 11 tests covering Protocol conformance, behavior cases, and tenant isolation.

## Validators addressed

- **V-F-py-2** (D-T3 port + adapter resolves cross-package consumption) — PASS via smoke import + 11 GREEN tests
- **V-AG-4** prep (BrandVoicePort interface complete — 2 async methods) — verified via `test_port_has_exactly_two_public_methods` + smoke import assertion

## Commit

- Repo: `~/luana-platform` (branch `main`)
- SHA: `fe8dd4231c9842394f53a8dc1f0156e46b1de985`
- Message: `feat(luana-core-brand-studio): introduce BrandVoicePort + BrandVoiceService adapter (D-T3 ADR-001 §2.4 cement)`

## Verifier outputs

### 1. Smoke import (per architect spec)

```bash
cd /home/chris/luana-platform && uv run python -c "
from luana_core_brand_studio.application.ports.brand_voice_port import BrandVoicePort
from luana_core_brand_studio.application.services.brand_voice_service import BrandVoiceService
assert hasattr(BrandVoicePort, 'compile_system_instruction')
assert hasattr(BrandVoicePort, 'get_voice_metadata')
print('D-T3 INTRODUCED OK')"
# Output: D-T3 INTRODUCED OK
```

### 2. New tests GREEN (11 tests)

```bash
cd /home/chris/luana-platform && uv run pytest \
    core/luana-core-brand-studio/tests/test_brand_voice_service.py -x -q --tb=short
# Output: 11 passed, 1 warning in 0.15s
```

### 3. Full brand-studio suite — zero regression

```bash
cd /home/chris/luana-platform && uv run pytest core/luana-core-brand-studio/tests/ -q --tb=line
# Baseline pre-T-3: 459 passed
# Post-T-3: 470 passed (459 baseline + 11 new — confirmed zero regression)
# 470 passed, 8 warnings in 137.06s
```

### 4. Story 5 SSoT cement intact (V-AG-7 regression Story 5)

```bash
cd /home/chris/luana-platform && uv run python -c "
# PersonalityCompiler still declared ONLY in domain/personality.py
import subprocess
result = subprocess.run(['grep', '-rn', 'class PersonalityCompiler', 'core/luana-core-brand-studio/src/'], capture_output=True, text=True)
declarations = [l for l in result.stdout.split('\n') if 'class PersonalityCompiler' in l]
assert len(declarations) == 1
assert 'domain/personality.py' in declarations[0]
print('SSoT: PASS')
# compile() signature unchanged
from luana_core_brand_studio.domain.personality import PersonalityCompiler
import inspect
sig = inspect.signature(PersonalityCompiler.compile)
assert list(sig.parameters.keys()) == ['dimensions', 'patterns', 'exchanges']
print('Signature: PASS')"
# Output:
# SSoT: PASS
# Signature: PASS (dimensions, patterns, exchanges)
```

### 5. Ruff lint clean

```bash
cd /home/chris/luana-platform && uv run ruff check \
    core/luana-core-brand-studio/src/luana_core_brand_studio/application/ports/ \
    core/luana-core-brand-studio/src/luana_core_brand_studio/application/services/brand_voice_service.py \
    core/luana-core-brand-studio/tests/test_brand_voice_service.py
# Output: All checks passed!
```

## Design deviations from architect spec — adapted to real codebase

The architect specified an abstract template that didn't match real codebase signatures. Adaptations made (all preserve invariants):

| Architect spec assumed | Reality in codebase | Adapter handling |
|---|---|---|
| `PersonalityRepository` class | `PersonalityProfileRepository` class | Import + parameter rename |
| `async def get_for_tenant(tenant_id)` | sync `def get_active(*, tenant_id)` | Async port wraps sync call; consumer hot path cache-protected (slot 5 5min TTL) |
| `compiler.compile(profile)` | static `PersonalityCompiler.compile(dimensions, patterns, exchanges)` | Adapter unpacks ORM model's JSONB pillars (`dimensions`, `linguistic_patterns`, `sample_exchanges`) into Pydantic types `PersonalityDimensions`, `LinguisticPatterns`, `SampleExchange` before calling compile |
| `profile.version` | No explicit `version` column | `getattr(model, "version", 1)` → returns 1 when present, 0 when absent |
| `profile.last_compiled_at` | No explicit `last_compiled_at` column | `getattr(model, "updated_at", None) or getattr(model, "created_at", None)` |
| `profile.dimensions.summary()` | dimensions is JSONB dict, not Pydantic | `dict(model.dimensions or {})` returns full dict |

These adaptations preserve the port's **public surface** (2 async methods, schema-cemented return types) so future Story 7+ tests verifying V-AG-3 + V-AG-4 will pass against this implementation. The internal sync→async bridging is encapsulated, and the consumer (sales-agent compose_prompt) sees the same async interface regardless of repo flavor.

## Best-effort design choices

The adapter never propagates errors to consumer hot path:

- Repo `get_active` raises → log warning, return `""` / empty metadata
- Compile from JSONB raises (e.g., schema drift, malformed JSONB) → log warning + profile_id, return `""`
- Cached `system_instruction` ORM column populated → return directly (saves recompile)
- No active profile → return `""` (consumer falls back to specialist default voice)

## Halt criteria evaluation

All 16 Story 7 halt criteria (§6) checked — none triggered:

- ✅ Halt #2 (D-T3 surface expansion) — port frozen at 2 methods, no scope creep
- ✅ Halt #3 (D-T3 cardinal — direct PersonalityCompiler import) — adapter consumes it, but adapter LIVES in brand-studio package (architecturally allowed); sales-agent never imports it directly (will be enforced T-11/T-12 + T-18 V-AG-3 arch fitness)
- ✅ Halt #13 (PersonalityCompiler signature change) — signature UNCHANGED, verified post-commit
- ✅ Halt #14 (brand-studio test regression) — 459 baseline GREEN + 11 new GREEN = 470 GREEN, zero regression

## Skills consulted

- `sales-agent-expert` skill — confirmed slot 5 BRAND_VOICE prefix is hexagonal consumer of compiler output. Voice anchor SSoT in `personality_profiles.system_instruction` cemented per `references/sales-agent-brand-voice.md`. Adapter returns cached `system_instruction` ORM column when present (matches existing slot 5 caching pattern).
- `copilot-expert` skill — anti-duplication §0 cardinal honored: BrandVoicePort is NEW abstraction (architect pre-ratified per ADR-001 §2.4 — only acceptable Story 7 scope expansion). PersonalityCompiler stays in domain (Story 5 cement). No mirror.
- `tessl__langgraph` skill — Protocol pattern + async interface are standard LangGraph integration pattern for cross-package consumption (e.g., `BaseToolNode`).
- `tessl__graceful-degradation` skill — adapter best-effort design (try/except + structlog warning + empty fallback) matches Iron Rule patterns. No external HTTP calls in adapter (sync DB only) so no timeout/circuit-breaker needed at this layer.
- `tessl__pytest-api-testing` skill — used existing `db` fixture (function-scoped, transaction rollback per test) from brand-studio conftest. `@pytest.mark.asyncio` decorator for async test methods. Factory pattern via `_activate` helper.
- `backend-ddd.md` rule — Inside-Out layering preserved: domain (PersonalityCompiler unchanged) → infrastructure (PersonalityProfileRepository unchanged) → application (NEW ports/ + services/brand_voice_service.py).
- `tenant-isolation.md` rule — both port methods take `tenant_id: UUID`; tests `test_compile_does_not_leak_across_tenants` + `test_metadata_does_not_leak_across_tenants` verify isolation.
- `anti-duplication.md` rule — verified port is NEW abstraction (not mirror) per architect pre-ratification ADR-001 §2.4 + Session 3.
- `tdd-mandatory.md` rule — 11 tests written for new port + adapter; existing 459 tests GREEN throughout (no test deletion / skip).
- `parallel-safety.md` rule — staged 4 files by exact name; no `git add .`/`-A`/`-u`; uv.lock not modified post-T-3 (verified via `git status`).
- `git-safety.md` rule — Conventional Commits format; single branch `main`; no `--force` / `--no-verify` / `--amend`.
- `spanish-text.md` rule — code comments in Spanish (per project standard); no user-facing strings introduced (port/adapter is internal hexagonal layer).

## Cost-bucket separation note

The voice compiler is consumed by **production** sales-agent runtime (slot 5 BRAND_VOICE prefix) → LLM costs go to `sales_agent_llm_call` (production cost bucket). Eval framework (deferred Luana v0.2.0) would consume same port but write to `eval_simulator_llm_call` (eval cost bucket, separated per Story B). Cost-bucket invariant preserved at the consumer level (compose_prompt) — adapter itself is cost-bucket-agnostic.

## Notes

- Adapter `__init__` accepts optional `compiler` parameter for DI / test override (default uses `PersonalityCompiler` class directly since `compile` is static).
- 16 of 16 halt criteria evaluated and clear — no escalation needed.
- Story 5 baseline 459 → 470 GREEN confirms no regression; new 11 tests are additive only.
- Commit body documents both invariants honored AND design deviations (for future audit traceability).

## Next

Batch 2 awaiting orchestrator spawn — T-4 (domain layer lift, 10 files) → T-15 (copilot_provider) → T-16 (connections wiring) → T-17 (integration) → T-18 (arch fitness 8 tests) → T-19 (finalization).
