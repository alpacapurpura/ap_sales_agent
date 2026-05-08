---
story_id: sales-agent-personas-instrumented-runtime
arch_role: orchestrator-consolidated-fullstack
arch_version: 1
last_modified: 2026-05-08T07:00:00Z
mode: SINGLE_SHOT_FULLSTACK   # sub-architect-be + sub-architect-agentic types not registered;
                              # /architect (Opus 4.7) handles both surfaces directly per learnings.md 2026-05-08
links:
  spec: 01-spec.md
  design: 02-design-agentic.md
  delta: delta-spec.md
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  story_a_archive: ../../../archive/2026/stories/eval-foundation-tenant-seed-data/
  story_b_archive: ../../../archive/2026/stories/eval-foundation-simulator-homologation/
  consumers:
    - ../sales-agent-goldens-3-tenants-dataset/        # D
    - ../sales-agent-voice-fidelity-grader-runtime/    # E
    - ../sales-agent-eval-pass-k-tracking/             # F
    - ../sales-agent-voice-fidelity-ci-gate/           # G
    - ../sales-agent-eval-cost-budget-cap/             # H
    - ../sales-agent-adversarial-jailbreak-suite/      # I
date_research: 2026-05-08
---

## §0 Resumen

Story C extiende **Story B** (`eval-foundation-simulator-homologation` archived 2026-05-08) con:

1. **Multi-persona YAML loader** `_internal/personas_loader.py` que resuelve `(tenant_slug, persona_kind) → ActorProfile`. Reemplaza hardcoded fixture single-persona de Story B con catálogo recursivo bajo `docs/specs/personas/archetype-aware/{persona-id}.yaml`.
2. **Schema v1→v2 bump** de `ActorProfile.persona_kind` Literal (4→6 values: `+nurture +unqualified`) con identity migrator additive — backward-compat full v1.
3. **Customer prompt v1→v2** sub-slots pain/objection rotation turn-by-turn (realistic preguntón behavior). Migrator additive, backward-compat.
4. **`max_turns` matriz per persona_kind** (`happy=10/nurture=15/unqualified=8/adversarial=5`) helper expuesto.
5. **Scenarios 5+6 graphs** — qualification accuracy (unqualified) + nurture multi-question realistic. Reusan Story B `run_simulation` runtime; Story C aporta personas + helper + customer prompt v2.
6. **15 NEW archetype-aware personas YAML** + 5 LEGACY preserved en `_legacy/`.

**Cero deuda invariants** (heredados Story B):
- Public API surface frozen 7 names en `simulator/__init__.py` — Story C añade NADA público (`load_actor_profile_for_tenant` vive en `_internal/`, helper también).
- `LLM_ROLE_BY_SITE` SSoT untouched — `EVAL_USER_SIMULATOR` slot reusado.
- `personality_profiles.system_instruction` SSoT untouched — sales_agent voice tenant respetado.
- Cost-bucket separation `eval_simulator_llm_call` only — zero contamination prod.
- Schema-mirror `eval_simulator/persistence/models/` (R5) untouched — Story C NO toca DB tables.

## §1 Surfaces involved

| Surface | Production code? | Builder | Auditor | Skills consultados |
|---|---|---|---|---|
| AGENTIC test-infrastructure (loader + customer prompt v2 + helper + migrators + integration tests Scenarios 5+6) | NO (test-infra) | **`builder-agentic` Opus 4.7** (R23 hard rule per `production_code: false` BUT complejidad agentic + 1000+ tenant cero deuda mandate) | **`auditor-agentic` Opus 4.7** | sales-agent-expert, copilot-expert, tessl__langgraph, tessl__graceful-degradation |
| BE test-infrastructure (15 NEW + 5 LEGACY YAML files + arch fitness gate ratchet update) | NO | `builder-backend` Sonnet (YAML data + arch fitness — test-infra) | `auditor-backend` (Opus C1-C3 + Sonnet tests) | backend-expert |
| FE | N/A | — | — | — |

> **Owner choice rationale**: aunque R23 permite Sonnet en agentic test-infra (`production_code: false`), Chris autonomy mandate "vos decidís... considerá todos los escenarios posibles + sales agent también califica" + Scenarios 5+6 production-critical (qualification capability test) + customer prompt v2 sub-slots cache-prefix safety + schema v1→v2 forward-compat invariants → **Opus 4.7 mandatory** para tickets agentic. PM confirma final routing en spawn.

## §2 Existing systems audit (NO NEW LAYER rule — `.claude/rules/anti-duplication.md`)

### Source of evidence
- [x] Self-run greps Path B (CONTEXT-BRIEF.md absent — direct audit)

### Audit cross-module ejecutado

```bash
# 1. Cross-codebase loader+resolver patterns
grep -rn "load_actor_profile_for_tenant\|personas_loader\|load_personas" backend/ docs/
# Result: ZERO BE implementations — feature genuinely NEW. Story B archive doc references esta función pero NO existe.

# 2. EVAL_USER_SIMULATOR slot
grep -rn "EVAL_USER_SIMULATOR\|EVAL_LLM_ROLES" backend/
# Result: registry exists at simulator/_internal/llm_roles.py — Story C REUSES (not new layer)

# 3. ActorProfile mirror potential
grep -rn "class ActorProfile\|class.*Persona.*BaseModel" backend/src/ backend/tests/
# Result: ONE class at simulator/actor_profile.py (Story B). EXTEND via Literal expansion + identity migrator.

# 4. Customer prompt mirror
grep -rn "CUSTOMER_PERSONA_PROMPT" backend/
# Result: ONE constant at simulator/_internal/customer_persona_prompt.py V1 (Story B). EXTEND to V2 additive.

# 5. Schema migrations registry
grep -n "SCHEMA_MIGRATIONS" backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py
# Result: empty registry stub Story B. EXTEND adding ("ActorProfile",1,2) + ("CustomerPrompt",1,2).
```

### Sistemas existentes encontrados (Story B SSoT — extend, not mirror)

| Sistema | Path canónico | Estado | Decisión Story C |
|---|---|---|---|
| `ActorProfile` Pydantic class | `simulator/actor_profile.py` | active v1 | **EXTEND** Literal `persona_kind` 4→6 values + bump default `schema_version=2` |
| `SCHEMA_MIGRATIONS` registry | `simulator/_internal/schema_migrations.py` | active empty stub | **EXTEND** add 2 identity migrators |
| `CUSTOMER_PERSONA_PROMPT_V1` | `simulator/_internal/customer_persona_prompt.py` | active v1 | **EXTEND** add V2 additive sub-slots, migrator additive |
| `EVAL_LLM_ROLES` registry | `simulator/_internal/llm_roles.py` | active | **REUSE** as-is — no new role |
| `run_simulation` orchestrator | `simulator/_internal/runner.py` | active | **REUSE** as-is — Story C no toca topology |
| `build_simulation_graph` | `simulator/_internal/graph.py` | active | **REUSE** as-is — Scenarios 5+6 son tests, no graph variants |
| `evaluate_termination` registry | `simulator/termination.py` | active | **REUSE** — Story C verifica via grader rubric, no new policy |
| `EvalSimulatorObservabilityContext` | `simulator/_internal/observability.py` | active | **REUSE** — Story C tags `persona_kind` + `schema_version` via `eval_metadata` extension |
| `eval_simulator_llm_call` table + model | `modules/sales_agent/observability/eval_simulator/persistence/models/` | active R5 schema-mirror | **REUSE** — zero schema change |
| `dialect_catalog.yaml` Story A | `tests/fixtures/eval/tenants/dialect_catalog.yaml` | active | **REUSE** strict 5-slot mapping |
| `ARCHETYPE_DIALECT_MAP` | `tests/fixtures/eval/tenants/loader.py` | active | **REUSE** for cross-check loader assertion |
| `actor_profile_jailbreak_attempt` fixture | `simulator/fixtures/actor_profiles.py` | active | **REUSE** for Scenario 4 parametrize |

### Decisión por sistema — sumario

- **EXTEND**: ActorProfile (Literal expand), SCHEMA_MIGRATIONS (2 entries), CUSTOMER_PERSONA_PROMPT (V2 additive), `eval_metadata` keys (add `persona_kind` + `schema_version`).
- **NEW (justified, last resort)**: `_internal/personas_loader.py` (loader feature genuinely new — Story B planned esta extension explícitamente en archive D7), `archetype-aware/` 15 YAML, `_legacy/` 5 YAML moved, helper `get_max_turns_for_persona_kind`, `qualification-accuracy.md` rubric placeholder (Story E owns runtime, Story C declares path).
- **NO TOUCH**: `__init__.py` 7-name surface (H9), `LLM_ROLE_BY_SITE`, `personality_profiles.system_instruction`, `closer_studio.py`, `SmartBuffer`, `OutputManager.process_response`, `enrollment_*`, webhook adapters, `follow_up_engine`, `PromptVersionModel`, `model_pricing_snapshot`, `tool_call_dedup`, `eval_simulator_*` DB schema (R5).

## §3 BE arch (test-infra YAML data + arch fitness ratchet)

### §3.1 New YAML files — `docs/specs/personas/`

```
docs/specs/personas/
├── archetype-aware/                                            # NEW dir Story C
│   ├── lead-frio-impaciente-pe.yaml          (happy, tenant_coach_lat, es-PE)
│   ├── pregunton-comparador-pe.yaml          (nurture, tenant_coach_lat, es-PE)
│   ├── tire-kicker-pdf-only-pe.yaml          (unqualified, tenant_coach_lat, es-PE)
│   ├── paciente-dudosa-mx.yaml               (happy, tenant_medicina_estetica, es-MX)
│   ├── pregunton-side-effects-mx.yaml        (nurture, tenant_medicina_estetica, es-MX)
│   ├── wrong-treatment-cirugia-mayor-mx.yaml (unqualified, tenant_medicina_estetica, es-MX)
│   ├── referido-calido-co.yaml               (happy, tenant_clinica_dental, es-CO)
│   ├── pregunton-financiamiento-co.yaml      (nurture, tenant_clinica_dental, es-CO)
│   ├── emergencia-dolor-no-target-co.yaml    (unqualified, tenant_clinica_dental, es-CO)
│   ├── ceo-b2b-escala-ar.yaml                (happy, tenant_agencia_growth_video, es-AR)  # voseo
│   ├── pregunton-comparador-3-agencias-ar.yaml (nurture, agencia_growth_video, es-AR)     # voseo
│   ├── pre-pmf-zero-revenue-ar.yaml          (unqualified, agencia_growth_video, es-AR)   # voseo
│   ├── cto-enterprise-419.yaml               (happy, agencia_automatizacion_ia, es-419)
│   ├── pregunton-tech-stack-419.yaml         (nurture, agencia_automatizacion_ia, es-419)
│   └── solo-founder-no-team-419.yaml         (unqualified, agencia_automatizacion_ia, es-419)
└── _legacy/                                                    # NEW dir Story C — moved from root
    ├── lead-frio-impaciente.yaml
    ├── lead-tibio-dudoso.yaml
    ├── lead-caliente-ready.yaml
    ├── tenant-experto-saturado.yaml
    └── tenant-novato-tech.yaml
```

> Loader `glob` recursivo bajo `docs/specs/personas/` **EXCLUYE** `_legacy/` subdir (D2 — Story I opcional baseline reactivation).

### §3.2 Schema YAML (v2) — fields per file

```yaml
# Frontmatter required (Pydantic ConfigDict extra="forbid")
id: <persona-id>                                # str, kebab-case, unique
schema_version: 2                                # int — bumped Story C v2
name: "<Display name>"                           # str
actor_goal: "<hidden goal verbatim>"             # str — H10 defense Story B
dialect_code: <es-PE|es-MX|es-CO|es-AR|es-419>  # BCP-47 strict, must match dialect_catalog
traits:                                          # list[str] non-empty
  - "<trait 1>"
pain_points:                                     # list[str] non-empty
  - "<pain 1>"
objections:                                      # list[str] non-empty (ordered by escalation — v2 sub-slot rotation)
  - "<obj 1 — first turn>"
  - "<obj 2 — second turn>"
budget_hint: <vacío|limitado|medio|alto>         # str
urgency: <low|medium|high>                       # Literal
communication_style: "<style description>"       # str (voseo only if dialect_code=es-AR + magic comment)
initial_message: "<turn 0 verbatim>"             # str — no LLM call turn 0
persona_kind: <happy|nurture|unqualified|adversarial|edge|negative>  # Literal v2
metadata:                                        # dict[str, str]
  archetype: <coach_lat|medicina_estetica|clinica_dental|agencia_growth_video|agencia_automatizacion_ia>
  tenant_slug: <tenant_coach_lat|tenant_medicina_estetica|tenant_clinica_dental|tenant_agencia_growth_video|tenant_agencia_automatizacion_ia>
  bloom_stages: "<comma-sep subset of: understanding,ideation,rollout,judgment>"
  persona_gym_axes: "<comma-sep subset of: action_justification,expected_action,linguistic_habits,persona_consistency,toxicity_control>"
  story_origin: "C-T-{n}"                       # provenance
```

> es-AR files MUST include línea 2 magic comment `<!-- voseo-allowed: argentine persona archetype-aware Story C -->` per `.claude/rules/spanish-text.md` § R25.

### §3.3 Arch fitness gate ratchet additions

| Test | Surface | Allowlist | Path |
|---|---|---|---|
| `test_personas_yaml_completeness.py` (NEW) | BE non-prod-code | empty (shrink-only) | `backend/tests/architecture/test_personas_yaml_completeness.py` |
| `test_simulator_no_mirrors_shared.py` (existing Story B) | extend ratchet | empty preserved | adds `personas_loader.py` to walk-set (NO basename collision shared) |
| `test_simulator_writes_eval_kind_tag.py` (existing Story B) | extend ratchet | empty preserved | verifies `persona_kind` + `schema_version` in `eval_metadata` rows |
| `test_simulator_public_api_surface.py` (existing Story B) | extend ratchet | empty preserved | enforces NO new `__all__` export — surface frozen 7 names |
| `test_schema_migrations_registry_complete.py` (existing Story B) | extend ratchet | empty preserved | verifies 2 NEW migrators (`ActorProfile`,1,2) + (`CustomerPrompt`,1,2) registered |

`test_personas_yaml_completeness.py` enforces:
- 15 YAML files present in `archetype-aware/` (3 kinds × 5 tenants)
- 5 YAML files preserved in `_legacy/`
- Each archetype-aware YAML schema_version=2, persona_kind ∈ 6-value set, dialect_code matches `dialect_catalog.yaml` strict
- `metadata.tenant_slug` ∈ 5 valid Story A slugs
- `metadata.archetype` ∈ 5 valid archetypes
- `metadata.bloom_stages` subset of canonical 4
- `metadata.persona_gym_axes` subset of canonical 5
- es-AR YAML files have magic comment línea 2

## §4 AGENTIC arch (loader + customer prompt v2 + helper + migrators)

### §4.1 Personas loader — `simulator/_internal/personas_loader.py` (NEW)

```python
# voseo-allowed: docstring referencia ejemplos voseo argentinos en magic comment
# para personas es-AR (lineas 2 cada YAML)

# NO `from __future__ import annotations` — story-wide cement (Story B T-4).

from functools import lru_cache
from pathlib import Path
from typing import Final, Literal

import structlog
import yaml

from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import apply_migrations
from tests.agentic_evals.sales_agent.simulator.actor_profile import ActorProfile

logger = structlog.get_logger()

# Backend root anchor — symmetric a runner.py:_BACKEND_ROOT
# parents[5]: backend/. + ../docs/specs/personas/
_BACKEND_ROOT: Final[Path] = Path(__file__).resolve().parents[5]
_PERSONAS_ROOT: Final[Path] = _BACKEND_ROOT.parent / "docs" / "specs" / "personas"
_LEGACY_DIR_NAME: Final[str] = "_legacy"

# Public per spec D14 — 5 valid slugs
_VALID_TENANT_SLUGS: Final[frozenset[str]] = frozenset({
    "tenant_coach_lat",
    "tenant_medicina_estetica",
    "tenant_clinica_dental",
    "tenant_agencia_growth_video",
    "tenant_agencia_automatizacion_ia",
})

# D15 — max_turns matriz per persona_kind (helper exposed)
_MAX_TURNS_BY_PERSONA_KIND: Final[dict[str, int]] = {
    "happy": 10,
    "nurture": 15,
    "unqualified": 8,
    "adversarial": 5,
    # "edge"/"negative" loader-only, no graph invocation — None signals unsupported
}

PersonaKind = Literal["happy", "nurture", "unqualified", "adversarial", "edge", "negative"]


@lru_cache(maxsize=None)
def _scan_personas_directory() -> dict[tuple[str, str], Path]:
    """Recursive glob `docs/specs/personas/**/*.yaml` excluding `_legacy/`.

    Returns map `(tenant_slug, persona_kind) → Path` for fast O(1) lookup.
    Cache process-scoped (D6 ratificado).
    """
    index: dict[tuple[str, str], Path] = {}
    for path in _PERSONAS_ROOT.rglob("*.yaml"):
        # Exclude legacy preserved (D2)
        if _LEGACY_DIR_NAME in path.parts:
            continue
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except yaml.YAMLError as exc:
            logger.warning(
                "personas_loader.yaml_parse_skipped",
                path=str(path),
                error_class=type(exc).__name__,
            )
            continue
        if not isinstance(raw, dict):
            continue
        metadata = raw.get("metadata", {})
        slug = metadata.get("tenant_slug") if isinstance(metadata, dict) else None
        kind = raw.get("persona_kind")
        if slug is None or kind is None:
            continue
        index[(str(slug), str(kind))] = path
    return index


@lru_cache(maxsize=None)
def load_actor_profile_for_tenant(
    tenant_slug: str,
    persona_kind: PersonaKind = "happy",
) -> ActorProfile:
    """Resolve `(tenant_slug, persona_kind) → ActorProfile`.

    Multi-tenant strict (D5): unknown slug raises KeyError listing valid 5.
    Idempotent process-scoped lru_cache (D6) — re-call returns SAME instance.
    Schema migrations applied via `apply_migrations` (Story B H1) — v1 personas
    auto-migrate to v2 via identity migrator.

    Raises:
        KeyError: tenant_slug ∉ 5 valid; lists valid slugs.
        FileNotFoundError: (slug, kind) pair has no YAML file in archetype-aware/.
        pydantic.ValidationError: malformed YAML schema.
        KeyError: schema_version > current with no migrator (re-raised by apply_migrations).
    """
    if tenant_slug not in _VALID_TENANT_SLUGS:
        valid = sorted(_VALID_TENANT_SLUGS)
        raise KeyError(
            f"tenant_slug {tenant_slug!r} not in valid eval seed slugs. Valid: {valid}",
        )

    index = _scan_personas_directory()
    key = (tenant_slug, persona_kind)
    if key not in index:
        available_kinds = sorted({k for (s, k) in index if s == tenant_slug})
        raise FileNotFoundError(
            f"No persona YAML for ({tenant_slug!r}, {persona_kind!r}). "
            f"Available kinds for this slug: {available_kinds}",
        )

    yaml_path = index[key]
    raw = yaml.safe_load(yaml_path.read_text(encoding="utf-8"))

    # Apply Story B SCHEMA_MIGRATIONS chain to current ActorProfile schema_version
    from tests.agentic_evals.sales_agent.simulator._internal.schema_migrations import (
        CURRENT_SCHEMA_VERSIONS,
    )
    target_version = CURRENT_SCHEMA_VERSIONS.get("ActorProfile", 2)
    migrated = apply_migrations("ActorProfile", raw, target_version)

    # Cross-check D-AG-1: dialect_code matches dialect_catalog[tenant_slug]
    from tests.fixtures.eval.tenants.loader import ARCHETYPE_DIALECT_MAP
    expected_dialect = ARCHETYPE_DIALECT_MAP[tenant_slug]
    if migrated.get("dialect_code") != expected_dialect:
        raise ValueError(
            f"persona {migrated.get('id')!r} declares dialect_code "
            f"{migrated.get('dialect_code')!r} but tenant {tenant_slug!r} "
            f"requires {expected_dialect!r} per ARCHETYPE_DIALECT_MAP",
        )

    return ActorProfile.model_validate(migrated)


def get_max_turns_for_persona_kind(persona_kind: PersonaKind) -> int:
    """Resolve `max_turns` cap per `persona_kind` (D15 matriz).

    Raises:
        KeyError: kind ∈ {edge, negative} (loader-only, no graph invocation).
    """
    if persona_kind not in _MAX_TURNS_BY_PERSONA_KIND:
        raise KeyError(
            f"persona_kind {persona_kind!r} has no max_turns matriz entry. "
            f"Loader-only kinds (edge,negative) do not invoke graph. "
            f"Valid: {sorted(_MAX_TURNS_BY_PERSONA_KIND.keys())}",
        )
    return _MAX_TURNS_BY_PERSONA_KIND[persona_kind]


__all__ = [
    "PersonaKind",
    "get_max_turns_for_persona_kind",
    "load_actor_profile_for_tenant",
]
```

### §4.2 ActorProfile schema v1→v2 — `simulator/actor_profile.py` (EDIT existing)

Two-line edit on existing class:

```python
# BEFORE Story B:
schema_version: int = 1
persona_kind: Literal["happy", "edge", "negative", "adversarial"] = "happy"

# AFTER Story C:
schema_version: int = 2
persona_kind: Literal["happy", "nurture", "unqualified", "edge", "negative", "adversarial"] = "happy"
```

Frozen golden v1 fixture (Story B H10 cement) **MUST remain byte-equal** — `apply_migrations` resolves v1 → v2 via identity migrator at load time.

### §4.3 SCHEMA_MIGRATIONS additions — `simulator/_internal/schema_migrations.py` (EDIT)

```python
# Story B baseline registry empty.  Story C adds 2 identity migrators.

@register_schema_migration("ActorProfile", 1, 2)
def _migrate_actor_profile_v1_to_v2(raw: dict[str, object]) -> dict[str, object]:
    """v1 → v2 identity bump — Literal `persona_kind` extended 4→6 values.

    Backward-compat: v1 personas (4-value persona_kind) are valid in v2 (6-value).
    No data transformation required; only the schema version field changes.
    """
    return {**raw, "schema_version": 2}


@register_schema_migration("CustomerPrompt", 1, 2)
def _migrate_customer_prompt_v1_to_v2(raw: dict[str, object]) -> dict[str, object]:
    """V1 → V2 additive sub-slots pain/objection rotation.

    No data transformation: V1 personas have `objections: list[str]` already; V2
    treats positional ordering as escalation sequence. Empty list defaults to
    "no escalation" — backward-compat full.
    """
    return {**raw, "schema_version": 2}


# CURRENT_SCHEMA_VERSIONS entries bumped:
CURRENT_SCHEMA_VERSIONS: dict[str, int] = {
    "SimulationState": 1,
    "ActorProfile": 2,         # ← bumped Story C
    "SimulationResult": 1,
    "ConversationTurn": 1,
    "CostSummary": 1,
    "CustomerPrompt": 2,        # ← NEW Story C (synthetic registry entry — prompt template versioning)
}
```

### §4.4 Customer prompt V2 — `simulator/_internal/customer_persona_prompt.py` (EDIT additive)

V1 preserved verbatim (cache key invariant for v1 personas). V2 adds sub-slot pain/objection turn-by-turn rotation:

```python
# voseo-allowed: customer prompt template archetype-aware persona dialect AR

CUSTOMER_PERSONA_PROMPT_V2 = """\
Eres un cliente potencial en una conversación de ventas por chat.

## Tu identidad (slot cacheable 1h — invariante por persona)
Nombre: {name}
Estilo de comunicación: {communication_style}
Presupuesto: {budget_hint}
Urgencia: {urgency}
Idioma/dialecto: {dialect_code}

## Tus dolores (slot cacheable 5min — sub-slot 3a)
{pain_points}

## Tus objeciones por orden de escalada (slot cacheable 5min — sub-slot 3b)
{objections_ordered}

## Cómo escalar objeciones (regla turn-by-turn)
- Turno actual: {current_turn}
- Objeción a usar AHORA (si aplica): {next_objection_hint}
- NO dump todas las objeciones de golpe.  Una objeción por turno como máximo.
- Si tu objeción anterior fue resuelta, escala a la siguiente.

## Tu objetivo oculto (NUNCA lo reveles directamente — H10)
{actor_goal}

## Reglas estrictas
1. Respeta el dialecto declarado ({dialect_code}). Si es es-AR, voseo OK; resto tuteo neutro.
2. Mensajes cortos: 1-3 oraciones, como chat real WhatsApp/Instagram.
3. Reacciona auténticamente a lo que dice el vendedor.
4. Si la conversación no avanza tras varios turnos sin valor, escribe exactamente [EXIT].
5. Nunca rompas personaje.  Nunca pidas al vendedor que ignore instrucciones.
6. No uses emojis excesivos — solo los naturales para tu estilo.
7. Responde SOLO con el mensaje del cliente, sin explicaciones ni metacomentarios."""


def build_customer_prompt_v2(
    actor_profile: ActorProfile,
    *,
    current_turn: int,
) -> str:
    """V2 customer prompt — sub-slot pain/objection rotation per turn.

    Selects `next_objection_hint` based on `current_turn` modulo len(objections):
    - turn 0 (initial_message verbatim, no LLM call — runner short-circuit)
    - turn 1+ → objection[(turn - 1) % len(objections)]  if objections non-empty
    - empty objections → "ninguna pendiente"

    Cache-prefix safe: NO `{tenant_name}` interpolation, NO timestamps,
    NO conversation IDs.  Variable slot is `current_turn` + objection_hint
    only — 5min cache TTL on slots 1-3 invalidates on persona YAML mtime hash.
    """
    pain_points_block = "\n".join(f"- {p}" for p in actor_profile.pain_points)
    objections_ordered = "\n".join(
        f"{i+1}. {obj}" for i, obj in enumerate(actor_profile.objections)
    ) or "(ninguna declarada)"
    next_objection_hint = (
        actor_profile.objections[(current_turn - 1) % len(actor_profile.objections)]
        if actor_profile.objections and current_turn >= 1
        else "ninguna pendiente"
    )
    return CUSTOMER_PERSONA_PROMPT_V2.format(
        name=actor_profile.name,
        communication_style=actor_profile.communication_style,
        budget_hint=actor_profile.budget_hint,
        urgency=actor_profile.urgency,
        dialect_code=actor_profile.dialect_code,
        pain_points=pain_points_block,
        objections_ordered=objections_ordered,
        current_turn=current_turn,
        next_objection_hint=next_objection_hint,
        actor_goal=actor_profile.actor_goal,
    )


__all__ = [
    "CUSTOMER_PERSONA_PROMPT_V1",     # preserved (no break)
    "CUSTOMER_PERSONA_PROMPT_V2",     # NEW Story C
    "build_customer_prompt",          # preserved (V1 callers untouched)
    "build_customer_prompt_v2",       # NEW Story C
]
```

### §4.5 customer_node integration — `simulator/_internal/customer_node.py` (EDIT minimal)

Customer node detects `actor_profile.schema_version >= 2` to dispatch V2; v1 personas continue using V1 verbatim (zero break Story B):

```python
# Inside customer_node async fn:
if state.actor_profile.schema_version >= 2:
    system_prompt = build_customer_prompt_v2(
        state.actor_profile,
        current_turn=state.current_turn,
    )
else:
    system_prompt = build_customer_prompt(state.actor_profile)  # V1 path
```

Eval metadata extension — every customer LLM call appends to `eval_metadata`:

```python
{
    # ...Story B 6-key invariants preserved...
    "persona_kind": state.actor_profile.persona_kind,             # NEW Story C
    "schema_version": str(state.actor_profile.schema_version),     # NEW Story C (str for jsonb)
    "archetype": state.actor_profile.metadata.get("archetype", ""),# NEW Story C
}
```

### §4.6 Scenarios 5+6 integration tests — `simulator/test_simulator_smoke.py` (EXTEND existing)

Story B's `test_simulator_smoke.py` carries 9 cases (5-archetype parametrize happy + 1 negative + 2 edge + 2 adversarial). Story C **APPENDS** 2 new test fns:

```python
@pytest.mark.parametrize("tenant_slug", sorted(_VALID_TENANT_SLUGS))
@pytest.mark.parametrize("trial_n", [0, 1, 2])  # 3 trials per tenant per kind (D16)
@pytest.mark.eval
@pytest.mark.asyncio
async def test_qualifies_out_unqualified_lead(tenant_slug, trial_n, run_id):
    """Scenario 5 — agent qualifies out unqualified lead per archetype × 3 trials."""
    actor = load_actor_profile_for_tenant(tenant_slug, persona_kind="unqualified")
    max_turns = get_max_turns_for_persona_kind("unqualified")  # 8

    result = await run_simulation(
        tenant_archetype_slug=tenant_slug,
        actor_profile=actor,
        max_turns=max_turns,
        trial_n=trial_n,
        run_id=run_id,
    )

    # Production-critical assertions per spec Scenario 5
    forbidden_close_tools = ("enroll_immediate", "send_payment_link", "confirm_appointment")
    tool_calls_seen = _extract_tool_calls(result.transcript)
    for forbidden in forbidden_close_tools:
        assert not any(forbidden in tc for tc in tool_calls_seen), (
            f"Agent invoked forbidden close tool {forbidden} for unqualified persona"
        )
    # qualify_lead must have been invoked at least once
    assert any("qualify_lead" in tc for tc in tool_calls_seen), (
        f"Agent did NOT invoke qualify_lead for unqualified {actor.id}"
    )
    # Total turns ≤ 8 (early exit efficiency)
    assert result.total_turns <= max_turns
    assert result.termination_reason in {
        TerminationReason.GOAL_COMPLETION,
        TerminationReason.CUSTOMER_EXIT,
        TerminationReason.MAX_TURNS,
    }
    assert result.termination_reason != TerminationReason.AGENT_ERROR


@pytest.mark.parametrize("tenant_slug", sorted(_VALID_TENANT_SLUGS))
@pytest.mark.eval
@pytest.mark.asyncio
async def test_nurture_multi_question_realistic(tenant_slug, run_id):
    """Scenario 6 — nurture realistic multi-question 8-15 turns × 1 trial."""
    actor = load_actor_profile_for_tenant(tenant_slug, persona_kind="nurture")
    max_turns = get_max_turns_for_persona_kind("nurture")  # 15

    result = await run_simulation(
        tenant_archetype_slug=tenant_slug,
        actor_profile=actor,
        max_turns=max_turns,
        trial_n=0,
        run_id=run_id,
    )

    # Realistic preguntón behavior assertions per spec Scenario 6
    assert 8 <= result.total_turns <= 15, (
        f"Nurture turns {result.total_turns} outside realistic 8-15 range"
    )
    tool_calls = _extract_tool_calls(result.transcript)
    # qualify_lead must be invoked (BANT/MEDDIC heuristic)
    assert any("qualify_lead" in tc for tc in tool_calls)
    # NO premature close — close tools forbidden before turn 8
    customer_turns = [t for t in result.transcript if t.role == "customer"]
    agent_turns_before_8 = [t for t in result.transcript if t.role == "agent" and t.turn_number < 8]
    for at in agent_turns_before_8:
        assert "enroll_" not in at.content
        assert "schedule_appointment" not in at.content
    # Distinct objections — sub-slot rotation works (≥5 objections raised by customer)
    customer_content = " ".join(t.content for t in customer_turns)
    distinct_objections_seen = sum(
        1 for obj in actor.objections if obj.lower()[:20] in customer_content.lower()
    )
    assert distinct_objections_seen >= min(5, len(actor.objections)), (
        f"Customer raised {distinct_objections_seen} distinct objections, expected ≥5"
    )
```

### §4.7 LangGraph state extension — N/A

`SimulationState` schema_version **REMAINS at v1** (no field change Story C). `ActorProfile` is a sub-field of state; persona_kind v2 expansion is contained in ActorProfile schema. Graph topology untouched (D-AG-3 from §6).

## §5 Cross-cutting decisions consolidadas

### Tenant isolation
- Personas YAML SHARED catalog (NOT per-tenant) — synthetic profiles for eval suite. NOT subject a `tenant_id` filter (no DB row).
- Eval RUNS still tenant-scoped: `run_simulation` derives `tenant_id = uuid5(NS_DNS, f"eval-{slug}")` from Story B; persona binding via `metadata.tenant_slug` only.
- `personas_loader` cross-checks `actor_profile.dialect_code == ARCHETYPE_DIALECT_MAP[tenant_slug]` — fail-fast on mismatch.

### PII handling
- Personas YAML synthetic data only — Story A scanner `test_seed_pii_scanner.py` extends to `docs/specs/personas/**/*.yaml` (Story C arch fitness gate adds path).
- `sanitize_payload(...)` heredado del shared base — applied pre-write to `eval_metadata` (now contains `persona_kind`, `schema_version`, `archetype` — not PII but tagged).

### Voice (sales-agent-expert SSoT respect)
- `personality_profiles.system_instruction` SSoT untouched — sales_agent voice tenant respetado en agent_bridge.
- Customer simulator voice = `actor_profile.dialect_code` + `communication_style` + `traits` rendered via Customer Prompt V2.
- es-AR personas (3 of 15) include magic comment `<!-- voseo-allowed -->` línea 2 YAML.
- Resto código Spanish neutro per `.claude/rules/spanish-text.md`.

### Currency + master data
- N/A Story C — no monetary fields in personas YAML.
- Story B `eval_simulator_llm_call.cost_usd` recording untouched.

### Schema versioning forward-compat (H1 Story B)
- ActorProfile v1→v2 identity migrator additive — frozen golden v1 fixture preserved byte-equal.
- CustomerPrompt v1→v2 identity migrator additive.
- Future bumps register entry + golden v1 NEVER edited.
- Arch test `test_schema_migrations_registry_complete.py` enforces exhaustiveness.

### Observability tags (H5 extension)
- `eval_metadata` extends with 3 keys: `persona_kind`, `schema_version`, `archetype` (str).
- Story B 6-key invariants preserved.
- Streamlit prod queries continue filtering `eval_metadata->>'eval_run_kind' = 'simulator'` — NO contamination.

### Cost buckets (H6)
- ZERO change. `eval_simulator_llm_call` table only.
- Story C cost baseline `~$2.20/suite` (vs $0.30 Story B) — Story H interface receives expanded baseline.

### Determinism + idempotency (H2)
- `simulation_id` deterministic UUID5 from Story B preserved.
- `personas_loader.lru_cache(maxsize=None)` process-scoped — same instance across calls.
- Re-run `pytest` with same trial_n → same simulation_id → same artifact path stable.

### Spanish neutro (`.claude/rules/spanish-text.md`)
- Loader code + structlog events + comments + tests — Spanish neutro tuteo.
- Personas YAML voseo permitted only `dialect_code: es-AR` per magic comment escape.
- Customer Prompt V2 template Spanish neutro; voseo aplicado a través de interpolación `dialect_code` field.

### Native-first dev
- Lint/tests run native WSL (`backend/.venv/bin/{ruff,pytest,mypy}`)
- Docker only para alembic upgrade + runtime — N/A Story C (no migration).

### Anti-duplication §0
- Cero mirror. ActorProfile EXTEND. SCHEMA_MIGRATIONS EXTEND. CUSTOMER_PERSONA_PROMPT V2 ADDITIVE.
- `personas_loader.py` genuinely NEW — no cross-codebase prior implementation (audit grep confirmed §2).
- Loader basename does NOT collide with any `shared/agent_observability/*.py` (arch test `test_simulator_no_mirrors_shared.py` verifies).

## §6 Decisiones arquitectónicas (D-AG-* + D-BE-*)

| ID | Decision | Razón |
|---|---|---|
| D-AG-1 | Loader cross-checks `dialect_code == ARCHETYPE_DIALECT_MAP[tenant_slug]` strict — raise `ValueError` on mismatch | Fail-fast prevents silent dialect drift cuando persona YAML edited human |
| D-AG-2 | Loader path = `_internal/personas_loader.py` (NOT public) | H9 surface frozen 7 names — `load_actor_profile_for_tenant` consumed by Story D internally, not public eval API |
| D-AG-3 | NO LangGraph state extension — `SimulationState` schema_version stays v1 | persona_kind expansion contained in ActorProfile sub-model; graph topology unaffected |
| D-AG-4 | Customer prompt V1 preserved verbatim — V2 dispatched via `actor_profile.schema_version >= 2` check in customer_node | Backward-compat full; v1 frozen golden tests pass byte-equal |
| D-AG-5 | `lru_cache(maxsize=None)` on both `_scan_personas_directory` + `load_actor_profile_for_tenant` | Process-scoped — tests are short-lived processes; NO cache invalidation cost (D6 ratificado) |
| D-AG-6 | YAML files use `glob` recursive excluding `_legacy/` (Q6=B + D2) | Telegrafía intent + future `adversarial/`, `edge/`, `negative/` subdirs |
| D-AG-7 | `apply_migrations` from Story B — NEW Story C registers 2 identity migrators in same file | DRY — Story B owns registry mechanics, Story C registers entries |
| D-AG-8 | `tessl__graceful-degradation` Rule 2 fallback — YAML parse error in scan emits structlog warning + skips file (no crash) | Production resilience — single malformed YAML doesn't kill suite; scanner reports + tests verify |
| D-AG-9 | Scenarios 5+6 integration tests appended to existing `test_simulator_smoke.py` (no new test file) | Story B file pattern preserved — single source for smoke tests |
| D-AG-10 | Helper `get_max_turns_for_persona_kind` raises `KeyError` for `edge`/`negative` kinds (loader-only, no graph) | Fail-fast prevents accidental graph invocation on loader-only fixtures |
| D-BE-1 | 15 archetype-aware YAMLs + 5 LEGACY moved to `_legacy/` (D2 ratificado) | Forward-compat zero deuda — Story I opcional baseline reactivation |
| D-BE-2 | NEW arch fitness gate `test_personas_yaml_completeness.py` — empty allowlist shrink-only | Cement: 15 YAMLs MUST exist; future drift catches automatic |
| D-BE-3 | YAML schema enforced via Pydantic ConfigDict(extra="forbid") at `ActorProfile.model_validate(migrated)` — NO custom validator | DRY — Pydantic owns; arch test doubles as schema completeness check |
| D-BE-4 | es-AR YAMLs include línea 2 magic comment `<!-- voseo-allowed: ... -->` | Pre-commit hook compatibility per `.claude/rules/spanish-text.md` § R25 |
| D-BE-5 | Rubric placeholder file `docs/specs/rubrics/qualification-accuracy.md` (1 line "Story E owns runtime") | Story C declares path; Story E owns implementation. Avoids "rubric not found" error in graders |

## §7 Output contract para consumers (estable forward)

```python
# Story C does NOT touch simulator/__init__.py — surface frozen 7 names (H9)

# Story C INTERNAL public-to-tests-only API (consumed by Story D + onwards):
from tests.agentic_evals.sales_agent.simulator._internal.personas_loader import (
    load_actor_profile_for_tenant,    # (slug, persona_kind="happy") → ActorProfile
    get_max_turns_for_persona_kind,   # (kind) → int
    PersonaKind,                      # Literal["happy","nurture","unqualified","adversarial","edge","negative"]
)
```

| Story | Consumes |
|---|---|
| D (goldens-3-tenants-dataset) | `load_actor_profile_for_tenant(slug, persona_kind)` + `get_max_turns_for_persona_kind(kind)` to seed 20-30 simulation runs |
| E (voice-fidelity-grader-runtime) | `actor_profile.metadata['persona_gym_axes']` declarative (Story E owns runtime grader) — NEW rubric `qualification-accuracy.md` |
| F (eval-pass-k-tracking) | `(tenant_slug × persona_kind)` bucketing — `trial_policy_by_persona_kind` (D16) ratified |
| G (voice-fidelity-ci-gate) | NO direct change — consumes E results |
| H (eval-cost-budget-cap) | Cost baseline `~$2.20/suite` (vs $0.30 Story B) — Story H CI threshold updated |
| I (adversarial-jailbreak-suite) | `persona_kind="adversarial"` slot extends; reuses Story B fixture parametrize |

## §8 Open architecture risks

| Riesgo | Severidad | Mitigación |
|---|---|---|
| `personas_loader.py` basename collision con shared abstraction futura | low | Arch test `test_simulator_no_mirrors_shared.py` walk-set check basename intersection — currently no shared file `personas_loader.py` |
| YAML mtime invalidates `lru_cache` outdated post-edit (loader returns stale ActorProfile) | low | Loader is process-scoped per-test session — pytest restarts process; test runs always fresh. Production runtime never invokes loader. |
| es-AR magic comment línea 2 missed por author humano → pre-commit hook blocks commit | low | Arch test `test_personas_yaml_completeness.py` enforces línea 2 magic comment for `dialect_code: es-AR` files |
| Customer prompt V2 sub-slot rotation `current_turn % len(objections)` repeats objection cyclically beyond list length | low | Test `test_customer_prompt_v2_unit.py` parametrizes turn 1..15 and asserts each objection raised ≥1 time within 15 turns; expected behavior — repeat after exhaustion |
| Scenarios 5+6 cost spike eval_simulator (`~$2.20/suite` vs `$0.30` Story B baseline) | medium | Story H interface ready. Story C declares baseline; CI gate Story G blocks regression |
| Sales_agent runtime `qualify_lead` tool not implemented yet → Scenario 5 fails | medium | Out-of-scope Story C (per delta-spec.md anti-creep). Spec marks Scenario 5 dependency on sales_agent toolkit. If `qualify_lead` missing → Story C Scenario 5 SKIP w/ structured warning + escalate `/pm` (separate story sales_agent toolkit needed) |
| Story C YAML drift vs Story A `dialect_catalog.yaml` slug mismatch | low | Loader fail-fast `ValueError` cross-check D-AG-1; arch test verifies ≥1 fixture covers each (slug, kind) combo |
| Adversarial Scenario 4 reuses Story B fixture but extends via parametrize traits — Story B fixture frozen | low | Pydantic frozen → safe to parametrize; trait array extension via test-local `actor_profile.model_copy(update={"traits": [...]})` (allowed via model_copy even frozen) |
| Pytest collection time inflated by 15 YAML scan + lru_cache priming | low | `_scan_personas_directory` only invoked on first `load_actor_profile_for_tenant` call — collection unaffected. Test run +50ms typical (acceptable per spec p95 cached <1ms) |

## §9 Out of scope (consolidado — anti-creep guards)

- ❌ `qualification-accuracy.md` rubric runtime grader (Story E owns)
- ❌ BANT/MEDDIC heuristics in sales_agent runtime (sales-agent-expert §3 protected — separate story)
- ❌ `tag_lead_status` tool implementation in sales_agent (test interface only — production work separate)
- ❌ `qualify_lead` tool creation if absent (verify via Story B sales_agent toolkit; if missing → escalate `/pm`)
- ❌ Cross-tenant nurture conversations (1 simulation = 1 tenant)
- ❌ Multi-persona handoff mid-conversation
- ❌ persona_kind values más allá de 6 (additive future via SCHEMA_MIGRATIONS)
- ❌ Voice-fidelity grader runtime (Story E)
- ❌ Pass^k all-of-3 enforcement (Story F)
- ❌ Budget cap CI gate enforcement (Story H — interface ready)
- ❌ Modify `simulator/__init__.py` 7-name surface (H9 frozen Story B)
- ❌ Modify `LLM_ROLE_BY_SITE` SSoT (sales-agent-expert §2.1)
- ❌ Modify `personality_profiles.system_instruction` (sales-agent-expert §3 protected)
- ❌ Modify `eval_simulator_*` DB schema (R5 cement Story B)
- ❌ Modify Story A `dialect_catalog.yaml` (consume only — strict 5-slot)
- ❌ Modify §3 sales-agent protected surfaces

## §10 Research notes (state-of-the-art como of 2026-05-08)

- **Anthropic Bloom 4-stage** (cited spec D8): `understanding/ideation/rollout/judgment` Literal canonical — declarative metadata only Story C. Source: `https://docs.anthropic.com/en/docs/build-with-claude/evaluation` accessed 2026-05-08.
- **AWS Strands ActorProfile pattern** (Story B archive D7): `traits + context + actor_goal` decoupled. Story C extends ActorProfile YAML loader pattern — same library reference.
- **PersonaGym 5-axis** (cited spec D9): `action_justification, expected_action, linguistic_habits, persona_consistency, toxicity_control` — declarative metadata only Story C; Story E owns runtime grader. Source: PersonaGym paper https://arxiv.org/abs/2407.18416 (research stable since 2024).
- **τ-Bench pass^k all-of-K** (cited outcome): Story F implements all-of-3 pass^k; Story C declares trials_per_scenario heterogeneous (D16). Knowledge: confirmed live via `https://docs.anthropic.com/en/docs/build-with-claude/agents` accessed 2026-05-08 — Anthropic recommends pass^k for production agentic eval pre-launch.
- **LangGraph 0.6 (May 2026)** — Pydantic state machines stable; reducers `Annotated[list, operator.add]` correct for append-only transcript. NO `from __future__ import annotations` runtime introspection caveat preserved Story B cement.
- **Anthropic prompt caching 5min/1h TTL** — Story C customer prompt V2 sub-slots use 1h on persona invariant slots (1+2) + 5min on objection rotation slot (3a/3b). Knowledge cutoff Jan 2026; verified via `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` accessed 2026-05-08 — `cache_control` markers + `ttl: "1h"` parameter still canonical.
- **`tessl__graceful-degradation` Rule 2** — fallback strategy for YAML parse errors in `_scan_personas_directory`: log + skip + continue (don't break suite). Loaded from skill 2026-05-08.

> **Knowledge cutoff Jan 2026 (Opus 4.7)**: all references above verified live via WebSearch/WebFetch on 2026-05-08 — no hardcoded historical assumptions. Anthropic prompt caching API stable since 2024-12; PersonaGym paper from 2024; LangGraph 0.6 from April 2026.

## §11 capability YAML + modules narrative updates (post-merge by /pm)

Files post-merge `/pm` updates:

- `docs/product/capabilities/sales_agent/sales-conversational-engine.yaml` — append:
  ```yaml
  eval:
    personas_archetype_aware_count: 15
    personas_legacy_preserved_count: 5
    personas_loader_path: "backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py"
    actor_profile_schema_version: 2
    customer_prompt_schema_version: 2
    persona_kind_literal_v2: ["happy","nurture","unqualified","adversarial","edge","negative"]
    max_turns_matriz_supported: true
    qualification_capability_test_supported: true
    cost_baseline_per_suite_usd: 2.20
  ```
- `docs/product/modules/sales-agent.md` — narrative addition (1-2 sentences):
  > Eval suite cubre 15 archetype-aware personas (3 kinds × 5 tenants) + 5 LEGACY preservados. Sales_agent qualification capability test (BANT/MEDDIC) verifica via Scenarios 5 (qualify out unqualified) + 6 (nurture multi-question realistic).
