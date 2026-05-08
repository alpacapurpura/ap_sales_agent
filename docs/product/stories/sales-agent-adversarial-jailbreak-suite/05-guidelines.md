<!-- voseo-allowed: cita es-AR voseo en persona YAML coercion-100x-roi-ar.yaml ejemplo (sales-agent voice exception per .claude/rules/sales-agent-brand-voice.md) -->

# 05-guidelines.md — Story sales-agent-adversarial-jailbreak-suite

> /architect orchestrator delivered (2026-05-08). Patterns required + forbidden + files in/out scope. Cero ambigüedad. Builders consultan ESTO antes de cada Edit.

## Patterns required (cero deuda — escala 1000+ tenants × N updates)

### Backend (Python 3.12 + Pydantic v2 + SQLAlchemy 2.0) — declarative changes

- **Pydantic v2 ConfigDict** — `model_config = ConfigDict(extra="forbid", frozen=True)` cuando crees nuevos modelos. Story I NO crea nuevos modelos; extiende Literals existentes (Story D `GoldenPersonaKind`, Story E `MajEvalScore.rubric_id` + `RubricGradeRequest.rubrics`).
- **Pydantic v2 Literal expansion forward-compat** — agregar variant a Literal es **superset operation**. Old data válido. NO `schema_version` bump. NO migrator. (docs.pydantic.dev/latest/concepts/types/#literal-type accessed 2026-05-08).
- **`structlog`** logging — NUNCA `print` / `logging.{info,warn,error}`. Structured fields obligatorios en Story I scenarios: `tenant_slug`, `simulation_id`, `turn_n`, `persona_id`, `attack_category`, `system_leak_detected`, `compliance_violation`.
- **`utc_now()` from `shared/domain/datetime_utils.py`** — NUNCA `datetime.utcnow()`. N/A Story I (no DDL — schema mirror reused Story E).
- **YAML safe_load** — `yaml.safe_load(...)` para personas YAML (Story C T-2 pattern reused). NUNCA `yaml.load(...)` (RCE risk).
- **Anti-duplication §0** — antes Write nuevo file: grep cross-codebase + `cat .claude/rules/anti-duplication.md` inventario shared. Match → STOP escalate. Story I REUSE Stories C/D/E/F/G/H infra. NO mirror state machine. NO mirror grader. NO mirror EvalPassKSummary. NO mirror BudgetGuard.
- **`from __future__ import annotations` PERMITIDO en `tests/agentic_evals/sales_agent/adversarial/*.py`, `tests/architecture/test_adversarial_*.py`** — NOT in LangGraph compose path (Story I no toca LangGraph).
- **Migrations idempotent raw SQL** — N/A Story I (no DDL).
- **Schema-mirror exception R5** — N/A Story I (Story E DDL columns `persona_kind VARCHAR(32)` y `rubric_id VARCHAR(64)` already accommodate Literal extension via String storage).

### Pydantic v2 schema versioning forward-compat (Story I additive Literal extensions)

- Story D `GoldenScenarioModel.schema_version: Literal[1] = 1` cement preserved post Story I. NO bump v1→v2 — Literal expansion `GoldenPersonaKind +adversarial` superset.
- Story E `MajEvalScore.schema_version: Literal[1] = 1` cement preserved. NO bump — Literal expansion `rubric_id +toxicity-control` superset.
- Story F `EvalPassKSummary.schema_version: Literal[1] = 1` cement preserved. Story F D9 cement YA incluye `persona_kind=adversarial` Literal slot (Story I provides data only).

### Adversarial persona YAML (Story C v2 schema cement)

- **schema_version=2** mandatory (Story C T-2 cement post v2).
- **persona_kind=adversarial** mandatory (Story C v2 6-val Literal slot already exists per `_VALID_PERSONA_KINDS`).
- **dialect_code** matches `ARCHETYPE_DIALECT_MAP[tenant_slug]` strict (es-PE / es-MX / es-CO / es-AR / es-419 per tenant — Story C T-2 enforcement).
- **metadata.archetype** ∈ 5 valid archetypes (coach_lat / medicina_estetica / clinica_dental / agencia_growth_video / agencia_automatizacion_ia).
- **metadata.tenant_slug** ∈ 5 valid Story A slugs.
- **metadata.bloom_stages** subset of 4 canonical stages (`understanding,ideation,rollout,judgment`). Adversarial typically `judgment` or `judgment,rollout`.
- **metadata.persona_gym_axes** MUST contain `"toxicity_control"` (5th axis — Story I D12 cement per arch fitness gate `test_adversarial_persona_metadata_axis.py`).
- **metadata.attack_categories** MUST be comma-separated string of 1-3 categories from: `jailbreak,prompt-injection,hostile-persona,overpromise-coercion,compliance-probes`.
- **metadata.forbidden_tools** comma-separated string per spec §3 table.
- **metadata.story_origin** = `"I-T-2"` (Story I ticket origin trace).
- **es-AR YAMLs**: `<!-- voseo-allowed -->` o `# voseo-allowed` magic comment línea 2 mandatory (Story C T-2 enforcement via existing arch fitness gate).

### Rubric MD (Story I OWNS toxicity-control.md v1)

- **Frontmatter YAML** (top of MD inside ```yaml fence): `id`, `version: 1`, `applies_to: [agentic-story]`, `modules: [sales_agent]`, `threshold_default: 0.85`, `ssot: [...]`, `last_modified: 2026-05-08`, `owner_story: sales-agent-adversarial-jailbreak-suite`.
- **Sections**: Propósito · Inputs al juez · Assertions A1-A5 (mapped to 5 attack categories) · Scoring methodology · Out of scope · Calibration · Cache invalidation · Story chain.
- **Spanish neutro tuteo** (per `.claude/rules/spanish-text.md` glosario): NO voseo (no `tenés/podés/querés/mirá/dejá/...`). Use `tienes/puedes/quieres/mira/deja/...`. Pre-commit hook + `be_spanish_neutro_rubric_md` validator catch.
- **Pattern parity** con `voice-fidelity.md` + `qualification-accuracy.md` (Story E v1) — same structure, same length range (~150-250 lines).

### Test scenarios (5 NEW under `adversarial/`)

- **`pytest.mark.eval`** marker on every test function (consume `eval` group — costs counted Story H bucket).
- **`pytest.mark.asyncio`** for async test functions (`grade_transcript_maj_eval` is async).
- **Fixture `eval_session`** (existing Story B `conftest.py`) — async session for DB writes/reads.
- **`@pytest.mark.parametrize`** for 5 personas × 5 categories matrix (per `test_defense_happy.py::test_5_categories_resistance`).
- **API consume only** (anti-duplication §0):
  - `from tests.agentic_evals.sales_agent.simulator import run_simulation, grade_transcript_maj_eval` (Story B+E H9 surface 8 names).
  - `from tests.agentic_evals.sales_agent.simulator._internal.personas_loader import load_actor_profile_for_tenant` (Story C internal pin D-AG-2).
  - `from tests.agentic_evals.sales_agent.grader.result import RubricGradeRequest, MajEvalScore` (Story E result.py).
  - **NUNCA** import from `modules/sales_agent/` runtime (test-infra ↔ runtime separation).
  - **NUNCA** mirror Story B+E logic in adversarial scenarios — consume API.

### Sandbox markers cement (Story E DQ2 reused)

3-layer defense-in-depth (Story E owns; Story I REUSE — NO new defense layer per spec D9):

1. **Slot 1 system directive** — verbatim `CRITICAL SECURITY DIRECTIVE` block en Story E `judge_prompts.py::SLOT_1_TEMPLATE`. Cacheable TTL=1h.
2. **Slot 5 builder** — literal `<<TRANSCRIPT_BEGIN>>` + `<<TRANSCRIPT_END>>` strings wrap transcript content. Adversarial transcripts wrapped same.
3. **Arch fitness gate** Story E `test_grader_sandbox_markers_enforced.py` — AST scan asserts marker literals present.

Story I scenarios CONFIRM existing defense via Scenario 4 multi-vector attack test — verify markers actually prevent injection execution. NUNCA accept transcript content unwrapped.

### Anthropic prompt caching (Story E DQ1 reused)

- **Slots 1+2+3 cacheable TTL=1h** — Story E reused. Slot 2 = rubric MD verbatim (5 rubrics for adversarial). Cache invalidates per `rubric_version` bump (toxicity-control v1 → v2 future).
- **Slots 4+5+6 NOT cached** — per-call variable (transcript + tenant voice + judge instructions).
- **NUNCA `{tenant_name}` interpolation** mid-block cacheable slot — sales-agent-expert §3 anti-pattern.

### Voice + Spanish neutro (Story I scope)

- **Code (`adversarial/*.py`, `test_adversarial_*.py`, `core/config.py` extension)** + **structlog events** + **comments** + **tests** — Spanish neutro tuteo per `.claude/rules/spanish-text.md` glosario.
- **Rubric MD `toxicity-control.md` v1** = Spanish neutro tuteo. Threshold/scoring methodology Spanish prose; rubric/category IDs literal English (`jailbreak`, `prompt-injection`, etc.).
- **Persona YAMLs**:
  - `coercion-100x-roi-ar.yaml` (es-AR) → voseo permitted **with magic comment línea 2** (sales_agent voice exception per `.claude/rules/sales-agent-brand-voice.md`).
  - `troll-jailbreak-pe.yaml` (es-PE), `compliance-probe-medical-mx.yaml` (es-MX), `prompt-injection-name-co.yaml` (es-CO), `pii-fishing-419.yaml` (es-419) → tuteo neutro NO voseo.
- **`personality_profile.system_instruction` Slot 3** = verbatim from tenant SSoT (sales-agent-expert §3 protected — voseo permitted only if tenant es-AR; judges READ-ONLY). Story I NO touch.
- **NUNCA crear `brand_voice_summary` table mirror** (creep guard cement sales-agent-brand-voice).
- **NUNCA fine-tune judges per tenant** — generic judges + voice via Slot 3 = single variable (Story E D19 cement).

### `core/config.py` Settings extension (3 NEW thresholds)

- **`SALES_AGENT_RUBRIC_TOXICITY_CONTROL_THRESHOLD: float = Field(default=0.85)`** — D6 spec.
- **`SALES_AGENT_RUBRIC_VOICE_FIDELITY_ADVERSARIAL_THRESHOLD: float = Field(default=0.80)`** — adversarial-only override; Story E baseline 0.7 preserved for happy/nurture/unqualified.
- **`SALES_AGENT_RUBRIC_NO_HALLUCINATION_ADVERSARIAL_THRESHOLD: float = Field(default=0.85)`** — adversarial-only override; Story E baseline 0.7 preserved.
- **`description=...`** field cite Story I cement + R29 anti-default-flip protection.
- **Anti-default-flip R29 enforcement** (per `.claude/rules/anti-default-flip-audit.md`): defaults frozen. Flip via env var override only. NEW arch fitness gate `test_adversarial_thresholds_defaults_protected.py` declarative check defaults match spec D6.

### Arch fitness gate authoring (`test_adversarial_persona_metadata_axis.py` + `test_adversarial_thresholds_defaults_protected.py`)

- **Pattern parity** con Story C `test_personas_yaml_completeness.py` (existing 350-line gate).
- **`pytest.mark.no_eval`** marker (NOT eval — gate runs in arch fitness suite).
- **`yaml.safe_load`** for YAML reads.
- **Allowlist empty** (shrink-only ratchet — every NEW adversarial YAML must comply).
- **Helpful error messages** with file paths + line numbers + remediation hints (cite spec D-number).

## Patterns forbidden (cero deuda violations)

- ❌ **NO mirror Story D goldens infra** — extend via `--persona-kinds adversarial` CLI flag + `forbidden_tools` map adversarial branch (additive). NUNCA crear `backend/scripts/generate_adversarial_goldens.py` paralelo.
- ❌ **NO mirror Story E grader** — extend Literals + dispatch map (`_DEFAULT_RUBRICS_BY_PERSONA_KIND`). NUNCA crear `backend/tests/agentic_evals/sales_agent/adversarial_grader/` paralelo.
- ❌ **NO mirror Story F EvalPassKSummary** — Literal `persona_kind +adversarial` slot ya cement Story F D9. Story I provides data only.
- ❌ **NO touch `personality_profile.system_instruction`** SSoT — D10 cement + sales-agent-expert §3 protected.
- ❌ **NO touch Story B `simulator/__init__.py` H9 surface** (8 names post Story E expand). NO new public API.
- ❌ **NO new state machine** — DQ1 cement REUSE Story B `run_simulation` + Story C personas + Story E grader.
- ❌ **NO new defense layer** — DQ2 cement REUSE Story E sandbox markers (Slot 5).
- ❌ **NO `from __future__ import annotations` en LangGraph compose path** (sales-agent-expert anti-pattern). N/A Story I scope.
- ❌ **NO `print` / `logging.{info,warn,error}`** — structlog only.
- ❌ **NO `Any` / dicts magicos** en Pydantic types — siempre Literal + Field constraints.
- ❌ **NO `monkeypatch.setattr(USE_*=False)` band-aid** en tests — migrate to canonical path (anti-default-flip R29).
- ❌ **NO Bucket Literal expansion en Story H** — adversarial uses EXISTING `grader` bucket (per spec D7).
- ❌ **NO Alembic migration** Story I (Pydantic v2 Literal expansion is forward-compat superset; DDL columns already accommodate string storage).
- ❌ **NO modificar voice cement compiler v2** (`personality_profiles.system_instruction` SSoT). Creep guard cement.
- ❌ **NO touch `modules/sales_agent/{domain,application,api,observability/recording}/`** — test-infra only.
- ❌ **NO `git add .` o `-A`** — stage por nombre (parallel-safety.md).
- ❌ **NO commit con tests rotos**, NO `skip`/`xfail` para pasar CI, NO reducir coverage sin tests.
- ❌ **NO crear nuevo `[COPILOT-*]` anchor** — Story I no toca copilot/.
- ❌ **NO `pkgutil`** discovery (filesystem scan instead — namespace packages issue Story B precedent).
- ❌ **NO docker exec lint/tests** — native WSL only.

## Files in scope (NEW + MODIFIED por ticket)

| File | Action | Ticket | Surface |
|---|---|---|---|
| `docs/specs/rubrics/toxicity-control.md` | NEW | T-1 | BE rubric authoring |
| `docs/specs/personas/archetype-aware/troll-jailbreak-pe.yaml` | NEW | T-2 | persona YAML |
| `docs/specs/personas/archetype-aware/compliance-probe-medical-mx.yaml` | NEW | T-2 | persona YAML |
| `docs/specs/personas/archetype-aware/prompt-injection-name-co.yaml` | NEW | T-2 | persona YAML |
| `docs/specs/personas/archetype-aware/coercion-100x-roi-ar.yaml` | NEW | T-2 | persona YAML (voseo magic comment) |
| `docs/specs/personas/archetype-aware/pii-fishing-419.yaml` | NEW | T-2 | persona YAML |
| `backend/tests/architecture/test_adversarial_persona_metadata_axis.py` | NEW | T-2 | arch fitness gate |
| `backend/tests/architecture/test_adversarial_thresholds_defaults_protected.py` | NEW | T-3 | arch fitness gate |
| `backend/src/core/config.py` | MODIFIED | T-3 | 3 NEW Settings thresholds |
| `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` | MODIFIED | T-2 | GoldenPersonaKind Literal +adversarial |
| `backend/tests/agentic_evals/sales_agent/grader/result.py` | MODIFIED | T-3 | rubric_id Literal + RubricGradeRequest.rubrics +toxicity-control (post Story E build) |
| `backend/scripts/generate_golden_candidates.py` | MODIFIED | T-4 | --persona-kinds adversarial flag |
| `backend/scripts/promote_golden.py` | MODIFIED | T-4 | _resolve_forbidden_tools adversarial branch |
| `backend/tests/agentic_evals/sales_agent/grader/_internal/maj_eval.py` | MODIFIED | T-5 | _DEFAULT_RUBRICS_BY_PERSONA_KIND adversarial slot (5 rubrics) |
| `backend/tests/agentic_evals/sales_agent/adversarial/__init__.py` | NEW | T-6 | empty package marker |
| `backend/tests/agentic_evals/sales_agent/adversarial/test_defense_happy.py` | NEW | T-6 | Scenario 1 |
| `backend/tests/agentic_evals/sales_agent/adversarial/test_no_system_leak.py` | NEW | T-6 | leak_assertion grader |
| `backend/tests/agentic_evals/sales_agent/adversarial/test_multi_vector_attack.py` | NEW | T-6 | Scenario 4 |
| `backend/tests/agentic_evals/sales_agent/adversarial/test_pass_k_strict_cero_tolerance.py` | NEW | T-6 | Scenario 3 |
| `backend/tests/agentic_evals/sales_agent/adversarial/test_chris_semestral_review_signal.py` | NEW | T-6 | Scenario 2 supporting |
| `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/adversarial/{golden_id}.yaml` | NEW (5-10 files) | T-7 | Chris curation post-build |
| `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` | MODIFIED (eval block) | T-8 | post-merge by /pm |

## Files OUT of scope (NO touch)

- ❌ `modules/sales_agent/{domain,application,api,observability/recording}/` (test-infra only)
- ❌ `modules/copilot/` (PI-13 extends Story I patterns — out of scope this PI)
- ❌ `frontend/` (N/A — adversarial test-infra backend only)
- ❌ `backend/tests/agentic_evals/sales_agent/simulator/{__init__.py,_internal/*.py}` (Story B owns; Story I consume only)
- ❌ `backend/tests/agentic_evals/sales_agent/goldens/_schema_migrations.py` (Story D registry empty; Story I no migrator needed)
- ❌ `backend/tests/agentic_evals/sales_agent/grader/_internal/{cache.py,judge_prompts.py,judge_registry.py}` (Story E owns; Story I REUSE — NO touch)
- ❌ `backend/tests/agentic_evals/sales_agent/pass_k/*` (Story F owns; Story I consume only)
- ❌ `backend/tests/agentic_evals/sales_agent/ci_gate/*` (Story G owns; Story I integration test mockable)
- ❌ `backend/tests/agentic_evals/sales_agent/budget/*` (Story H owns; Story I consume only)
- ❌ `backend/alembic/versions/*` (no DDL migration Story I)
- ❌ `personality_profiles.system_instruction` (Story A SSoT — sales-agent-expert §3 protected)
- ❌ `docs/specs/personas/_legacy/*` (Story C T-2 preserved 5 legacy YAMLs; Story I no touch)
- ❌ Existing 15 archetype-aware YAMLs (Story C — happy/nurture/unqualified preserved)
- ❌ Existing 7 rubric MD files (`code-quality.md, completeness.md, empathy-tone.md, no-hallucination.md, no-overpromise.md, qualification-accuracy.md, tool-trajectory.md, voice-fidelity.md`)
- ❌ `core/enums/*` (no enum changes Story I)
- ❌ `shared/agent_observability/*` (anti-duplication shared cement — Story I REUSE)
- ❌ `shared/billing/*` (Story H consumer reuses BudgetGuard.check primitive)

## Reference docs (orden estricto build phase)

Builders consultan en orden:

1. **`05-guidelines.md`** (este archivo) — single entry point patterns + files in/out scope.
2. **`01-spec.md`** — Gherkin AI-resistant scenarios + 15 D-decisions cement + open questions resolved.
3. **`02-design-agentic.md`** — turn-by-turn transcripts mockup + tools sequence + voice constraints + error recovery + cost budget + observability.
4. **`03-arch.md`** — technical design completo (rubric MD content, Pydantic Literal extensions, scripts edits, arch fitness gates, file structure).
5. **`04-validators.yaml`** — 4 categories validators ejecutables (non_functional + functional + agentic_eval + scenario_coverage).
6. **`06-tickets.yaml`** — atomic DAG con dependencies + owner_eligibility per ticket + acceptance criteria.
7. **Cross-story refs** (consume API only, NO mirror):
   - Story C `_internal/personas_loader.py` (`load_actor_profile_for_tenant`)
   - Story D `goldens/_schema.py` (`GoldenScenarioModel` + Literal expansion target)
   - Story D `scripts/{generate_golden_candidates,promote_golden,scan_goldens_pii}.py` (extension targets)
   - Story E `grader/result.py` (`MajEvalScore`, `JudgeOpinion`, `RubricGradeRequest` Literal expansion targets) + `grader/_internal/maj_eval.py` (dispatch extension target)
   - Story F `pass_k/aggregator.py` (`compute_pass_k_for_run` consumer for adversarial rows)
   - Story G `01-spec.md` (monthly cadence integration mockable)
   - Story H `BudgetGuard.check` (primitive consumer; no expansion needed)
8. **Rules cargados (read on demand)**:
   - `.claude/rules/anti-duplication.md` (cardinal — extend not mirror)
   - `.claude/rules/sales-agent-brand-voice.md` (voice cement creep guard + voseo exception)
   - `.claude/rules/spanish-text.md` (neutro default + voseo magic comment escape)
   - `.claude/rules/anti-default-flip-audit.md` (R29 thresholds)
   - `.claude/rules/tdd-mandatory.md` (RED tests primero)
   - `.claude/rules/auditor-downstream-regression.md` (Story I terminal — no downstream consumers, NA section)
   - `.claude/rules/architectural-fitness.md` (allowlists shrink-only)

## Skills loaded (orden estricto)

| Skill | Cuándo | Para qué |
|---|---|---|
| `sales-agent-expert` | T-1 (rubric MD), T-2 (personas YAML), T-3+T-5+T-6 (Pydantic + grader + scenarios) | §0 anti-duplication cardinal + §3 protected surfaces + voice cement creep guard + glossary |
| `backend-expert` | T-1 (rubric MD authoring), T-2 (arch fitness gate), T-3 (Settings + Literal extension), T-4 (scripts) | Pydantic v2 + SQLAlchemy 2.0 + arch fitness gate patterns + Settings declarative |
| `tessl__langgraph` | T-6 (scenarios consume Story B+E LangGraph machinery indirectly) | Reference patterns Story B+E reuse |
| `tessl__fastapi` | T-3 (Pydantic v2 ConfigDict patterns) | Pydantic v2 best practices |
| `tessl__pytest-api-testing` | T-6 (5 scenarios) | pytest async + parametrize + fixture patterns |
| `tessl__graceful-degradation` | T-6 (scenarios + structlog warn paths) | Best-effort observability + fallback per Rule 2 |
| `brand-expert` | T-1 (rubric MD authoring tone) | Rubric MD pattern parity Story E precedent |
| `copilot-expert` | T-6 (validate cross-pollination patterns reusable for PI-13 future) | Reference — copilot adversarial extension future |

## TDD-mandatory layered approach

Per `.claude/rules/tdd-mandatory.md` — RED tests primero por capa:

1. **T-1 RED**: `test_toxicity_control_rubric_present.py` (NEW T-1 acceptance) — assert MD file exists + frontmatter parsed → fails before T-1 build → GREEN post.
2. **T-2 RED**: `test_personas_yaml_completeness.py::test_adversarial_personas_count_matches_expected` (Story C extends with new assertion) + `test_adversarial_persona_metadata_axis.py` → fails before T-2 personas YAML created → GREEN post.
3. **T-3 RED**: `test_settings_has_adversarial_thresholds` + `test_adversarial_thresholds_defaults_protected.py` + `test_persona_kind_literal_includes_adversarial` (Story D extends) + `test_rubric_id_literal_includes_toxicity_control` (Story E extends) → fails before T-3 Settings + Literal edits → GREEN post.
4. **T-4 RED**: `test_resolve_forbidden_tools_adversarial_branch_per_persona` + `test_persona_kinds_flag_supports_adversarial` → fails before T-4 scripts edits → GREEN post.
5. **T-5 RED**: `test_dispatch_5_rubrics_for_adversarial_persona_kind` + `test_dispatch_4_rubrics_for_happy_unchanged` → fails before T-5 maj_eval.py dispatch extension → GREEN post.
6. **T-6 RED**: 5 scenarios (`test_defense_happy`, `test_no_system_leak`, `test_multi_vector_attack`, `test_pass_k_strict_cero_tolerance`, `test_chris_semestral_review_signal`) — fail because adversarial goldens absent (T-7 Chris curation post-build) → adversarial scenarios use mock goldens or skip with markers `pytest.mark.requires_goldens` until T-7 lands → GREEN post T-7.
7. **T-7**: Chris manual curation step (post-build) — generate via Story D pipeline + promote 5-10 candidates.
8. **T-8**: `/pm` post-merge capability YAML append.

## Native-first build commands

**ALL commands native WSL. NUNCA Docker exec ruff/pytest/tsc/vitest.**

```bash
# Lint + format
cd backend && .venv/bin/ruff check tests/agentic_evals/sales_agent/adversarial/ tests/architecture/test_adversarial_*.py scripts/{generate_golden_candidates,promote_golden}.py src/core/config.py
cd backend && .venv/bin/ruff format --check tests/agentic_evals/sales_agent/adversarial/ tests/architecture/test_adversarial_*.py scripts/{generate_golden_candidates,promote_golden}.py src/core/config.py

# Mypy strict
cd backend && .venv/bin/mypy --strict tests/agentic_evals/sales_agent/adversarial/ scripts/{generate_golden_candidates,promote_golden}.py --ignore-missing-imports

# Arch fitness — full suite (verify Story B/C/D/E/F gates STILL GREEN + 2 NEW gates pass)
cd backend && .venv/bin/pytest tests/architecture/ -x -q --override-ini="addopts="

# Story I scenarios (eval marker — costs counted Story H bucket)
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/adversarial/ -x -q -m eval

# Single scenario debugging
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/adversarial/test_defense_happy.py::test_5_categories_resistance -xvs

# Coverage (story-scoped)
cd backend && .venv/bin/pytest tests/agentic_evals/sales_agent/adversarial/ tests/architecture/test_adversarial_*.py --cov=tests/agentic_evals/sales_agent/adversarial --cov-report=term-missing --cov-fail-under=85

# Capability YAML extension verification (post T-8 by /pm)
grep -E "adversarial_personas_count|toxicity_control_rubric_path|adversarial_pass_k_threshold" docs/product/capabilities/sales-agent/sales-conversational-engine.yaml
```

## Owner routing per ticket (R23 cost-routing matrix)

Per `learnings.md` 2026-05-05 R23: agentic tickets `production_code: false` → Sonnet OK; agentic tickets `production_code: true` (modules/copilot, modules/sales_agent runtime) → Opus 4.7 mandatory.

Story I = MIXED test-infra `production_code: false` (NO toca runtime sales_agent). Sin embargo, design adversarial defense semantic correctness + multi-vector attack realism + sandbox bypass detection requieren agentic judgment. Routing per ticket:

| Ticket | Production code? | Builder eligible | Rationale |
|---|---|---|---|
| T-1 (rubric MD authoring) | NO | **Sonnet** OK declarative | Rubric MD content + frontmatter — declarative pattern parity Story E |
| T-2 (5 personas YAML + arch fitness gate) | NO | **Sonnet** OK declarative | YAML schemas + AST gate — declarative pattern parity Story C T-2 |
| T-3 (Pydantic Literal extensions + Settings + arch fitness threshold gate) | NO | **Sonnet** OK declarative | Pure Literal expansion + Settings property addition + simple AST gate |
| T-4 (scripts extensions adversarial branch + CLI flag) | NO | **Sonnet** OK declarative | argparse extension + dict map + branch — declarative scripts edit Story D pattern |
| T-5 (Story E grader dispatch extension) | NO | **Sonnet** OK declarative | _DEFAULT_RUBRICS_BY_PERSONA_KIND dict map adversarial slot — declarative |
| T-6 (5 scenarios test files) | NO (test-infra) | **Opus 4.7 mandatory** | Adversarial defense semantic + multi-vector attack realism + sandbox bypass detection require agentic judgment per Chris cero deuda mandate. Sonnet podría escribir tests que parecen correctos pero NO capturan ataque real. Reputational damage asymmetry justifica Opus. |
| T-7 (Chris curation goldens) | N/A | **Chris manual** | Oracle of truth per Story D D4 cement. NOT builder ticket — manual curation step post-build. |
| T-8 (capability YAML eval block append) | N/A | **/pm post-merge** | Per pm-redesign Punto 4 paradigm — capability promotion al merge. |

PM confirma final routing en spawn (validar `production_code` flag + complexity assessment per ticket en 06-tickets.yaml `owner_eligibility` matrix).

## Build order (HARD blockers + soft blockers)

```
T-1 (rubric MD)            ─┐
T-2 (5 personas YAML +     ─┼─ parallel-safe — independent of Stories C/D/E build state
       arch fitness gate)   │
T-3 (Pydantic Literal +    ─┘
     Settings + threshold gate)
                                ↓
T-4 (scripts extensions)   ─── HARD blocked by Story D done (✓ developed)
                                ↓
T-5 (grader dispatch)      ─── HARD blocked by Story E build done
                                ↓
T-6 (5 scenarios)          ─── HARD blocked by Stories C+D+E build done
                              SOFT blocked by Stories F (mockable) + G (mockable) + H (mockable)
                                ↓
T-7 (Chris curation        ─── Manual step post T-6 build close
     goldens 5-10)
                                ↓
T-8 (capability YAML       ─── /pm post-merge
     append)
```

Story I = LAST en sub-épica eval-foundation PI-12. Build phase HARD blocked until Stories C+D+E build done.

## Audit checklist (auditor APPROVED criteria)

- [x] Spec v2 + design v2 + arch v1 ratificados Chris
- [ ] All 4 categories validators GREEN
- [ ] 5 personas YAML schema_version=2 + persona_kind=adversarial + metadata.persona_gym_axes contains toxicity_control
- [ ] Rubric MD `toxicity-control.md` v1 frontmatter parses cleanly + Spanish neutro
- [ ] Arch fitness gate `test_adversarial_persona_metadata_axis.py` GREEN
- [ ] Arch fitness gate `test_adversarial_thresholds_defaults_protected.py` GREEN
- [ ] Story B/C/D/E/F arch fitness gates STILL GREEN
- [ ] Pydantic Literal extensions verified (Story D + Story E)
- [ ] Settings 3 NEW thresholds added with descriptions citing Story I + R29
- [ ] Story D scripts extensions: --persona-kinds adversarial flag + _resolve_forbidden_tools branch
- [ ] Story E grader dispatch extension: _DEFAULT_RUBRICS_BY_PERSONA_KIND adversarial slot 5 rubrics
- [ ] 5 test scenarios under `adversarial/` parametrized by 5 personas × 5 categories
- [ ] Cost-bucket invariant Story B H7 preserved (eval_simulator_grade only)
- [ ] Sandbox markers Slot 5 reused (NO new defense layer per spec D9)
- [ ] Voice cement compiler v2 untouched (creep guard cement)
- [ ] Anti-duplication §0 verified (no mirror state machine, no mirror grader, no mirror EvalPassKSummary)
- [ ] Spanish neutro tuteo verified rubric MD (no voseo) + persona YAMLs voseo only AR with magic comment
- [ ] Native-first commands (no docker exec lint/tests)
- [ ] R29 anti-default-flip protection enforced (3 thresholds defaults frozen)
- [ ] Build order honored (T-1+T-2+T-3 parallel-safe; T-4 needs Story D; T-5 needs Story E; T-6 needs C+D+E)
- [ ] T-7 Chris curation 5-10 adversarial goldens post-build
- [ ] T-8 capability YAML extension post-merge by /pm

## Changelog

- v1 2026-05-08T17:30Z — `/architect` orchestrator delivered. Patterns required + forbidden + files in/out scope + reference docs orden estricto + skills loaded + TDD layered + native-first commands + owner routing per ticket (R23 matrix) + build order HARD/soft blockers + audit checklist.
