# 05-guidelines.md — Story sales-agent-personas-instrumented-runtime

> /architect orchestrator delivered (2026-05-08). Patterns required + forbidden + files in/out scope. Cero ambigüedad. Builders consultan ESTO antes de cada Edit.

## Patterns required (cero deuda — escala 1000+ tenants × N updates)

### Backend (Python 3.12 + Pydantic v2)

- **Pydantic v2 ConfigDict** — `model_config = ConfigDict(extra="forbid", frozen=True)` heredado Story B. Cero `class Config` inner.
- **`structlog`** logging — NUNCA `print` / `logging.{info,warn,error}`. Structured fields obligatorios (`tenant_slug`, `persona_id`, `persona_kind`, `error_class`).
- **`utc_now()` from `shared/domain/datetime_utils.py`** — NUNCA `datetime.utcnow()`.
- **YAML safe_load** — NUNCA `yaml.load()` sin Loader (security risk).
- **Anti-duplication §0** — antes Write nuevo file: grep cross-codebase + `cat .claude/rules/anti-duplication.md` inventario shared. Match → STOP escalate. Subclase desde shared, NO mirror.
- **`from __future__ import annotations` PERMITIDO en `personas_loader.py` SOLO** (no parte LangGraph runtime). NO en `customer_persona_prompt.py` ni `customer_node.py` (importados por LangGraph compose — Story B cement).

### LangGraph + agentic test-infra (Story B cement preserved)

- **NO `from __future__ import annotations`** en archivos LangGraph runtime: `simulator/state.py`, `actor_profile.py`, `_internal/graph.py`, `_internal/customer_node.py`, `_internal/customer_persona_prompt.py`. Romperá runtime introspection (Story B T-4..T-7 cementado).
- **Pydantic state** ConfigDict frozen=True (Story B preserved).
- **Reducers correctos** — `Annotated[list[ConversationTurn], operator.add]` para append-only transcript. NEVER mutate in-place.
- **`run_simulation` async** — Story C reuse as-is. Cero modificación topology.
- **Customer prompt cache prefix safety** — cero `{tenant_name}` interpolación, cero timestamps, cero conversation IDs en slots cacheable. Story C V2 sub-slots `current_turn` + `next_objection_hint` son variables aceptables (not cache prefix).

### Loader-specific (`_internal/personas_loader.py`)

- **`lru_cache(maxsize=None)`** en BOTH `_scan_personas_directory` + `load_actor_profile_for_tenant` — D6 ratificado.
- **Path resolution** — `Path(__file__).resolve().parents[5].parent` (parents[5]=backend/, parent=repo root, then `docs/specs/personas/`). Mirror Story B `runner.py` `_BACKEND_ROOT` pattern.
- **Recursive glob excluding `_legacy/`** — `_LEGACY_DIR_NAME = "_legacy"` constant; `if _LEGACY_DIR_NAME in path.parts: continue`.
- **Apply migrations chain** — `apply_migrations("ActorProfile", raw, target_version=CURRENT_SCHEMA_VERSIONS["ActorProfile"])` from Story B.
- **Cross-check D-AG-1** — `actor_profile.dialect_code == ARCHETYPE_DIALECT_MAP[tenant_slug]` strict; `ValueError` on mismatch.
- **Fail-fast tenant slug** — `tenant_slug ∉ _VALID_TENANT_SLUGS` → `KeyError(f"...listing valid: {sorted(...)}")`.

### Customer Prompt V2 specific

- **V1 preserved verbatim** — `CUSTOMER_PERSONA_PROMPT_V1` constant + `build_customer_prompt(actor)` UNCHANGED (backward-compat full).
- **V2 ADDITIVE** — `CUSTOMER_PERSONA_PROMPT_V2` NEW constant + `build_customer_prompt_v2(actor, current_turn=N)` NEW function.
- **Customer node dispatch** — `if state.actor_profile.schema_version >= 2: build_customer_prompt_v2(...) else: build_customer_prompt(...)`.
- **Sub-slot rotation** — `next_objection_hint = objections[(current_turn-1) % len(objections)] if objections and current_turn >= 1 else "ninguna pendiente"`.
- **Cache TTL slots** — slots 1+2 (persona invariant) 1h; slots 3a+3b (objection rotation) 5min. Variable slots 4-7 NO cache.

### Voice + Spanish

- **Customer prompt voseo permitido** SI `actor_profile.dialect_code == 'es-AR'`. Magic comment `<!-- voseo-allowed: archetype-aware AR persona Story C -->` línea 2 YAML.
- **Resto código Spanish neutro** — error messages CLI/structlog/comments/README en español neutro LatAm. Aplica `.claude/rules/spanish-text.md` glosario.
- **Customer prompt NUNCA interpolar `{tenant_name}` mid-block** — anti-pattern cache prefix sales-agent-expert §3.
- **Agent output voice = compiled per `tenant.personality_profile.system_instruction`** — heredado, NUNCA override. SSoT respetado.
- **Loader docstring** + structlog events + comments — Spanish neutro o English (no voseo).

### Tests (TDD obligatorio)

- **RED → GREEN → REFACTOR** per layer:
  1. Loader contract tests RED (5 tenants happy load + edge schema bump + negative malformed + adversarial leak)
  2. Implement loader minimal GREEN
  3. Customer Prompt V2 unit tests RED (sub-slot rotation parametrize)
  4. Implement V2 builder GREEN
  5. Scenarios 5+6 integration tests RED (qualification + nurture multi-question)
  6. Implement test scaffold + integration GREEN
  7. Arch fitness gate `test_personas_yaml_completeness.py` RED → GREEN
- **Pytest markers** — `@pytest.mark.eval` para tests que invocan LLM real. `@pytest.mark.no_eval` para unit tests no-LLM. CI default skips `--run-evals`-gated tests; full suite runs nightly.
- **Pytest fixtures** — `actor_profile_jailbreak_attempt` (Story B reused) + `run_id` (Story B). Story C adds `actor_profile_unqualified_per_archetype` parametrize fixture in `conftest.py`.

## Patterns forbidden (cero deuda)

- ❌ `datetime.utcnow()` — use `utc_now()`
- ❌ Hardcoded `'USD'` — N/A Story C (no monetary)
- ❌ Hardcoded model names — use Story B `EVAL_LLM_ROLES` registry as-is
- ❌ Modificar `simulator/__init__.py` `__all__` (frozen 7 names H9 Story B)
- ❌ Modificar `LLM_ROLE_BY_SITE` SSoT (decisión §2.1 Story B)
- ❌ Modificar `personality_profiles.system_instruction` (sales-agent-expert §3 protected)
- ❌ Modificar §3 sales-agent protected surfaces (closer_studio, SmartBuffer, OutputManager.process_response, enrollment_*, webhook adapters, follow_up_engine, PromptVersionModel, model_pricing_snapshot, tool_call_dedup) — STOP escalate
- ❌ Modificar `eval_simulator_*` DB schema o models (R5 Story B preserved)
- ❌ Modificar Story A `dialect_catalog.yaml` (consume only — strict 5-slot)
- ❌ Modificar Story B `actor_profile.py` schema_version=1 default (bump to 2 — Story C explicit edit, not "modify default")
- ❌ Editar frozen golden v1 fixture `_fixtures/golden_v1_simulation_result.yaml` (H10 Story B byte-equal)
- ❌ Editar Story B existing arch fitness gates (extend ratchet OK, edit pre-existing logic NO)
- ❌ Mirror `customer_persona_prompt.py` o `personas_loader.py` desde shared/ (basenames don't collide — verify via arch test `test_simulator_no_mirrors_shared.py`)
- ❌ `yaml.load()` sin Loader (security) — use `yaml.safe_load`
- ❌ TypedDict en LangGraph state (D4 Story B — Pydantic only)
- ❌ HTTP webhook invocation desde agent_bridge (D1 Story B — in-process only)
- ❌ Cross-module imports excepto `copilot` (Story C imports: `tests/agentic_evals/sales_agent/simulator/*` + `tests/fixtures/eval/tenants/loader.py` + `src/core/enums` — all whitelisted)
- ❌ `from __future__ import annotations` en `simulator/_internal/customer_node.py` (importado por LangGraph compose — same cement Story B T-6)
- ❌ Skip `actor_profile.dialect_code == ARCHETYPE_DIALECT_MAP[tenant_slug]` cross-check (D-AG-1 fail-fast invariant)
- ❌ Loader exposes function en `simulator/__init__.py` `__all__` (D-AG-2 — `_internal/` only, consumed via direct import path)
- ❌ Adversarial Scenario 4 modify Story B fixture in-place — use `model_copy(update={...})` (Pydantic frozen-safe)
- ❌ Inline `{tenant_name}` interpolation en customer prompt cacheable slots
- ❌ `// eslint-disable` / `# noqa` sin justification comment
- ❌ `any` TS / `Any` Python loose types — strict typing
- ❌ Default exports (excepto Next.js pages — N/A esta story FE no toca)
- ❌ `git add .` / `git add -A` — stage por nombre exacto
- ❌ `git commit --no-verify` — pre-commit hook native enforced
- ❌ `git pull` / `git fetch && merge` — parallel-safety multi-instancia

## Files in scope (builders edit ONLY these)

### Personas YAML (BE test-infra — 20 files)

- `docs/specs/personas/archetype-aware/lead-frio-impaciente-pe.yaml` (NEW happy es-PE)
- `docs/specs/personas/archetype-aware/pregunton-comparador-pe.yaml` (NEW nurture es-PE)
- `docs/specs/personas/archetype-aware/tire-kicker-pdf-only-pe.yaml` (NEW unqualified es-PE)
- `docs/specs/personas/archetype-aware/paciente-dudosa-mx.yaml` (NEW happy es-MX)
- `docs/specs/personas/archetype-aware/pregunton-side-effects-mx.yaml` (NEW nurture es-MX)
- `docs/specs/personas/archetype-aware/wrong-treatment-cirugia-mayor-mx.yaml` (NEW unqualified es-MX)
- `docs/specs/personas/archetype-aware/referido-calido-co.yaml` (NEW happy es-CO)
- `docs/specs/personas/archetype-aware/pregunton-financiamiento-co.yaml` (NEW nurture es-CO)
- `docs/specs/personas/archetype-aware/emergencia-dolor-no-target-co.yaml` (NEW unqualified es-CO)
- `docs/specs/personas/archetype-aware/ceo-b2b-escala-ar.yaml` (NEW happy es-AR voseo)
- `docs/specs/personas/archetype-aware/pregunton-comparador-3-agencias-ar.yaml` (NEW nurture es-AR voseo)
- `docs/specs/personas/archetype-aware/pre-pmf-zero-revenue-ar.yaml` (NEW unqualified es-AR voseo)
- `docs/specs/personas/archetype-aware/cto-enterprise-419.yaml` (NEW happy es-419)
- `docs/specs/personas/archetype-aware/pregunton-tech-stack-419.yaml` (NEW nurture es-419)
- `docs/specs/personas/archetype-aware/solo-founder-no-team-419.yaml` (NEW unqualified es-419)
- `docs/specs/personas/_legacy/lead-frio-impaciente.yaml` (MOVED from `docs/specs/personas/`)
- `docs/specs/personas/_legacy/lead-tibio-dudoso.yaml` (MOVED)
- `docs/specs/personas/_legacy/lead-caliente-ready.yaml` (MOVED)
- `docs/specs/personas/_legacy/tenant-experto-saturado.yaml` (MOVED)
- `docs/specs/personas/_legacy/tenant-novato-tech.yaml` (MOVED)

### Loader + helper (AGENTIC test-infra)

- `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` (NEW — `load_actor_profile_for_tenant` + `get_max_turns_for_persona_kind` + `_scan_personas_directory`)

### Schema migrations + ActorProfile + Customer Prompt V2 (AGENTIC test-infra — EDITS)

- `backend/tests/agentic_evals/sales_agent/simulator/actor_profile.py` (EDIT — `schema_version: int = 2` default + Literal `persona_kind` 4→6 values)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py` (EDIT — add 2 identity migrators + bump `CURRENT_SCHEMA_VERSIONS`)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_persona_prompt.py` (EDIT additive — V2 constant + builder fn; V1 preserved verbatim)
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/customer_node.py` (EDIT — V1/V2 dispatch on `schema_version` + extend `eval_metadata` with `persona_kind`/`schema_version`/`archetype`)

### Test files (AGENTIC test-infra — NEW)

- `backend/tests/agentic_evals/sales_agent/simulator/test_personas_loader.py` (NEW — Scenarios 1+2+3+4 contract tests + helper tests + cross-check + parse error resilience + persona_gym + bloom)
- `backend/tests/agentic_evals/sales_agent/simulator/test_customer_prompt_v2_unit.py` (NEW — V2 sub-slot rotation parametrize current_turn 1..15 + V1 backward-compat assertion)
- `backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py` (EDIT additive — append `test_qualifies_out_unqualified_lead` + `test_nurture_multi_question_realistic` + `test_eval_metadata_extended_persona_kind`)
- `backend/tests/agentic_evals/sales_agent/simulator/conftest.py` (EDIT additive — `actor_profile_unqualified_per_archetype` parametrize fixture)

### Architecture fitness gate (BE non-prod-code — NEW)

- `backend/tests/architecture/test_personas_yaml_completeness.py` (NEW — empty allowlist shrink-only)

### Rubric placeholder (BE test-infra — Story C declares path; Story E owns runtime)

- `docs/specs/rubrics/qualification-accuracy.md` (NEW — minimal placeholder; Story E implements full)

### SSoT updates (rules + capability + module narrative — post-merge by /pm)

- `.claude/rules/auditor-downstream-regression.md` (1-line update — append entry `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` → downstream tests `test_personas_loader.py` + `test_simulator_smoke.py` for Stories D/E/F/I consumers)
- `docs/product/capabilities/sales_agent/sales-conversational-engine.yaml` (5+ new fields appended per §11 03-arch.md)
- `docs/product/modules/sales-agent.md` (1-2 sentence narrative addition)

## Files NEVER touched (escalate to Chris if needed)

- `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` ← H9 surface frozen 7 names Story B
- `backend/tests/agentic_evals/sales_agent/simulator/_fixtures/golden_v1_simulation_result.yaml` ← H10 byte-equal Story B
- `backend/tests/agentic_evals/sales_agent/simulator/_internal/{runner,graph,agent_bridge,observability,llm_roles,leak_assertions,concurrency}.py` ← Story B cement; Story C only edits `customer_node.py` (V1/V2 dispatch) + `customer_persona_prompt.py` (V2 additive) + `schema_migrations.py` (2 entries) + `actor_profile.py` (Literal expand + version bump)
- `backend/tests/agentic_evals/sales_agent/simulator/state.py` ← schema_version=1 stays Story B (D-AG-3)
- `backend/tests/agentic_evals/sales_agent/simulator/result.py` ← Story B; Story C does NOT modify SimulationResult schema
- `backend/tests/agentic_evals/sales_agent/simulator/termination.py` ← Story B; Story C does NOT add new TerminationReason values
- `backend/tests/agentic_evals/sales_agent/simulator/fixtures/{actor_profiles,tenant_seeded}.py` ← Story B cement; Story C reuses fixtures
- `backend/src/modules/sales_agent/observability/eval_simulator/**` ← R5 schema-mirror cement Story B; Story C does NOT touch DB schema
- `backend/src/shared/agent_observability/**` ← shared abstractions; Story C consumes via inheritance Story B subclasses
- `backend/src/modules/sales_agent/{domain,application,api,observability/recording}/` ← runtime sales_agent
- `backend/src/modules/copilot/**` ← agentic builder territory only
- `backend/src/core/config.py` ← R31 anti-default-flip-audit
- `backend/alembic/versions/**` ← Story C does NOT add migration
- `backend/tests/fixtures/eval/tenants/{dialect_catalog.yaml,loader.py}` ← Story A cement; Story C consumes via `ARCHETYPE_DIALECT_MAP` + `_validate_dialect_code`
- `frontend/**` ← N/A esta story FE no toca
- `client_simulator/src/simulator/*.py` ← D6 preservation gate Story B (sha256 unchanged)
- `.claude/skills/`, `.claude/agents/`, `.claude/rules/` (excepto auditor-downstream-regression entry add) ← skill/rule edits manual via /pm
- §3 sales-agent protected surfaces — STOP, ASK CHRIS

## Reference docs (load before coding — orden estricto)

### Universal (load primero, todos tickets)

1. `01-spec.md` (re-read 6 scenarios + decisions D1-D17 mid-build)
2. `02-design-agentic.md` (turn-by-turn transcripts §2 + state machine extension §3 + slot architecture §5 + scope expansion §13)
3. `03-arch.md` (this story consolidated arch)
4. `04-validators.yaml` (test commands ejecutables)
5. `delta-spec.md` (Chris autonomy mandate context)

### Story B references (Story C extends, do NOT mirror)

- `docs/archive/2026/stories/eval-foundation-simulator-homologation/03-arch.md` (Story B BE+AGENTIC arch)
- `docs/archive/2026/stories/eval-foundation-simulator-homologation/05-guidelines.md` (Story B patterns required/forbidden — Story C respects)
- `docs/archive/2026/stories/eval-foundation-tenant-seed-data/03-arch.md` (Story A dialect_catalog + tenant fixtures)

### Skills (per surface)

- `sales-agent-expert` — §3 protected surfaces, anti-patterns, voice fidelity, brand voice cement
- `tessl__langgraph` — Pydantic state, reducers, conditional edges, runtime introspection caveats
- `claude-api` — Anthropic SDK + prompt caching slot architecture (V2 5min/1h TTL)
- `tessl__pytest-api-testing` — pytest-asyncio, fixtures, parametrize
- `tessl__graceful-degradation` — Rule 2 fallback YAML parse errors (loader)
- `backend-expert` — DDD patterns, arch fitness ratchet, schema-mirror exception R5 (informational — Story C no toca DB)
- `copilot-expert` — observability writes best-effort (Story B subclasses preserved)

### Rules (cement before each Edit)

- `.claude/rules/anti-duplication.md` — inventario shared SSoT (CONSULTAR antes Write nuevo file; loader genuinamente NEW per audit §2)
- `.claude/rules/auditor-downstream-regression.md` — UPDATE entry post-merge with personas_loader path + downstream tests
- `.claude/rules/architectural-fitness.md` — 1 NEW gate `test_personas_yaml_completeness.py` empty allowlist shrink-only
- `.claude/rules/backend-ddd.md` — schema-mirror exception R5 (Story C does NOT use; Story B precedent reference only)
- `.claude/rules/backend-migrations.md` — N/A Story C (no migration)
- `.claude/rules/copilot-observability.md` — best-effort writes try/except + structlog warning (loader scan errors)
- `.claude/rules/copilot-resilience.md` — observability invariants Story B preserved
- `.claude/rules/parallel-safety.md` — `git add` por nombre, no force push, no pull
- `.claude/rules/sales-agent-brand-voice.md` — excepción simulator: voz tenant respetada agent-side; voseo permitido en customer prompts es-AR
- `.claude/rules/spanish-text.md` — voseo glosario + magic comment escape `<!-- voseo-allowed -->` línea 2 YAML
- `.claude/rules/tdd-mandatory.md` — RED → GREEN → REFACTOR per layer (loader → V2 prompt → scenarios)
- `.claude/rules/tenant-isolation.md` — every query filter `tenant_id` (Story C: personas SHARED catalog, NOT tenant-scoped DB; runtime filter via Story B `eval_tenant_seeded(slug)` invariant preserved)
- `.claude/rules/git-safety.md` — Conventional Commits, branch=development, no feature branches
- `.claude/rules/anti-default-flip-audit.md` — N/A Story C (no flag in `core/config.py`)

### Templates (consult during ticket execution)

- `docs/specs/templates/T-handoff-template.md`
- `docs/specs/templates/T-impl-log-template.md`
- `docs/specs/templates/T-result-template.md`
- `docs/specs/templates/T-review-template.md`

## Native-first execution (mandatory)

Toda lint/test/type-check NATIVE WSL — NUNCA Docker:

- BE: `cd backend && .venv/bin/{ruff,pytest,mypy,jscpd}` (venv 3.12)
- Pre-commit hook native enforced — `--no-verify` PROHIBIDO.

## TDD obligatorio (RED → GREEN → REFACTOR per layer)

Orden estricto:

1. **Schema migration registry** RED → GREEN (T-1 — add 2 identity migrators + golden v1 still deserializable)
2. **ActorProfile schema bump** RED → GREEN (T-1 — Literal expand 4→6 + schema_version=2)
3. **20 Personas YAML files** + arch fitness gate RED → GREEN (T-2 — 15 archetype-aware + 5 _legacy moved + new arch test)
4. **personas_loader** RED → GREEN (T-3 — load_actor_profile_for_tenant + get_max_turns_for_persona_kind + cross-check)
5. **Customer Prompt V2** RED → GREEN (T-4 — V2 constant + builder fn + sub-slot rotation parametrize)
6. **customer_node integration** RED → GREEN (T-5 — V1/V2 dispatch + extend eval_metadata)
7. **Scenario 5 (qualify out unqualified)** integration RED → GREEN (T-6 — 5 tenants × 3 trials)
8. **Scenario 6 (nurture multi-question)** integration RED → GREEN (T-7 — 5 tenants × 1 trial × 15 turns)
9. **Scenario 4 adversarial parametrize** RED → GREEN (T-8 — Story B fixture model_copy + leak assertions)
10. **Capability YAML + module narrative** updates (T-9 post-merge by /pm only — no builder action)

Cada layer: tests primero (failing) → implementación mínima (passing) → refactor.

Default flag flips: N/A esta story (no flag en `core/config.py`).

## Anti-telephone-game (subagent return contract)

Cada builder/auditor MUST devolver UNA línea final:

```
<verdict> -> <path-to-artifact>
```

Examples:

- `done -> docs/product/stories/sales-agent-personas-instrumented-runtime/T-3-result.md`
- `blocked -> docs/product/stories/sales-agent-personas-instrumented-runtime/checkpoint.md`
- `failed -> backend/tests/agentic_evals/sales_agent/simulator/test_personas_loader.py:42 [dialect mismatch not raised]`

NUNCA inline >500 tokens de artifact body. Caller lee file on demand.

## Process metrics (R12 Layer 1 — emit on each ticket close)

Builder Step 5.5 + Auditor Step 4.5 emit metrics via `scripts/emit_process_metric.py`. Default fields: ticket_id, story_id, phase, duration_minutes, tokens_consumed, model_used, validators_pass_count, validators_fail_count.

## Decisiones de owner routing (per /architect)

| Ticket | Surface | production_code | Owner recomendado | Justificación |
|---|---|---|---|---|
| T-1 | AGENTIC test-infra (schema bump) | false | builder-agentic Opus 4.7 | Schema versioning Pydantic Literal extension + migrator chain — agentic complexity (R23 permite Sonnet pero Chris mandate cero deuda + 1000+ tenants justifica Opus) |
| T-2 | BE test-infra (20 YAML + arch test) | false | builder-backend Sonnet | YAML data + arch fitness — pure test-infra, declarative |
| T-3 | AGENTIC test-infra (loader) | false | builder-agentic Opus 4.7 | Loader recursive glob + cross-check + lru_cache + Pydantic validation — agentic critical path |
| T-4 | AGENTIC test-infra (Customer Prompt V2) | false | builder-agentic Opus 4.7 | Prompt cache slot architecture + sub-slot rotation algorithm + voice fidelity — voice-critical |
| T-5 | AGENTIC test-infra (customer_node integration) | false | builder-agentic Opus 4.7 | LangGraph node edit + V1/V2 dispatch + eval_metadata extension — agentic plumbing |
| T-6 | AGENTIC test-infra (Scenario 5) | false | builder-agentic Opus 4.7 | Production-critical qualification capability test — sales_agent runtime BANT/MEDDIC verify |
| T-7 | AGENTIC test-infra (Scenario 6) | false | builder-agentic Opus 4.7 | Realistic LATAM nurture multi-question — sub-slot rotation behavior verify |
| T-8 | AGENTIC test-infra (Scenario 4 parametrize) | false | builder-agentic Opus 4.7 | Adversarial leak defense — security-critical |
| T-9 | docs (capability YAML + module narrative) | false | /pm post-merge (NO builder) | Documentation reconciliation — `/pm` skill ownership |

> **Decisión final routing**: Per `CLAUDE.md` cost-routing matrix + R23 + Chris autonomy mandate cero deuda 1000+ tenants. Aunque R23 permite Sonnet en agentic test-infra, Chris autonomy mandate "vos decidís + sales agent también califica" + Scenarios 5+6 production-critical (qualification capability test) + Customer Prompt V2 cache prefix safety → **Opus 4.7 mandatory para 7 agentic tickets**. T-2 BE YAMLs + arch test → Sonnet OK. PM confirma final routing antes Conv 2 arranca.

## Sales_agent toolkit dependency (escalation path)

Scenarios 5+6 assume sales_agent runtime supports tools `qualify_lead` + `tag_lead_status`. If at build time these tools don't exist:

- Builder T-6/T-7 SKIP test with `pytest.skip("requires qualify_lead tool — separate sales_agent toolkit story")` + emit structured warning
- Builder logs blocker in `T-{6,7}-impl-log.md`
- /pm decides: spawn separate `sales-agent-qualification-toolkit` story OR accept Scenario 5+6 SKIP for Story C completion

This decision is OUT OF SCOPE Story C scope per delta-spec.md anti-creep guards.
