---
story_id: sales-agent-personas-instrumented-runtime
delta_version: 1
created: 2026-05-08T05:00Z
created_by: /ux-agentico (during design v1)
ratified_by_chris: true   # Chris autorizó autonomy 2026-05-08T04:45Z "vos decidís"
links:
  spec_v2: "01-spec.md"
  design_v1: "02-design-agentic.md"
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
---

<!-- voseo-allowed: cita verbatim Chris autonomy mandate (es-AR voseo) for audit trail integrity -->


# Delta-spec — Scope expansion Story C (post Chris autonomy mandate 2026-05-08)

## Context

Chris autorizó decisions técnicas autonomy + flagged que spec v2 (5 happy personas) **es insuficiente para realistic LATAM coverage + sales_agent qualification testing**. Quote:

> "Los clientes latinos pueden ser preguntones, no consideres únicamente un happy path simplon... agregá alguna con no mucho interés y que no compre pero que el agente sepa detectar y calificar adecuadamente. Recuerda que el sales agent también califica."

Sales_agent en producción **DEBE** calificar leads (BANT/MEDDIC). Sin personas `unqualified` el eval suite NO puede verificar capability de qualifying out. Risk producción: sales_agent que cierra everyone = bad-fit clients + refunds + brand damage + 1000+ tenants downstream.

## Scope expansion (vs spec v2)

### 1. `ActorProfile.persona_kind` Literal extended (schema_version 1→2)

**v1 (Story B):** `Literal["happy", "edge", "negative", "adversarial"]` — 4 values
**v2 (Story C delta):** `Literal["happy", "nurture", "unqualified", "edge", "negative", "adversarial"]` — 6 values

Migrator entry NEW en `backend/tests/agentic_evals/sales_agent/simulator/_internal/schema_migrations.py`:

```python
def _migrate_actor_profile_v1_to_v2(payload: dict) -> dict:
    """Identity migrator — v1 personas (4-value persona_kind) válidas en v2 (6-value).

    No-op data transformation; bump exists para Pydantic Literal expansion compat.
    """
    return {**payload, "schema_version": 2}

SCHEMA_MIGRATIONS = {
    ("ActorProfile", 1, 2): _migrate_actor_profile_v1_to_v2,
    # ... existing migrations
}
```

### 2. Personas archetype-aware count: 5 → 15

| Tenant slug | Dialect | happy | nurture | unqualified |
|---|---|---|---|---|
| `tenant_coach_lat` | es-PE | `lead-frio-impaciente-pe` | `pregunton-comparador-pe` | `tire-kicker-pdf-only-pe` |
| `tenant_medicina_estetica` | es-MX | `paciente-dudosa-mx` | `pregunton-side-effects-mx` | `wrong-treatment-cirugia-mayor-mx` |
| `tenant_clinica_dental` | es-CO | `referido-calido-co` | `pregunton-financiamiento-co` | `emergencia-dolor-no-target-co` |
| `tenant_agencia_growth_video` | es-AR | `ceo-b2b-escala-ar` | `pregunton-comparador-3-agencias-ar` | `pre-pmf-zero-revenue-ar` |
| `tenant_agencia_automatizacion_ia` | es-419 | `cto-enterprise-419` | `pregunton-tech-stack-419` | `solo-founder-no-team-419` |

**Total Story C:** 15 NEW archetype-aware personas + 5 LEGACY `_legacy/` preserved (Q1=A) = **20 YAML files**

### 3. Scenarios extended (4 → 6 happy-type + edge/negative/adversarial)

#### Scenario 1 — `happy-personas-load-archetype-aware` (existing, expanded)

5 happy personas load + ActorProfile validation. Unchanged contract from spec v2.

#### Scenario 5 — `agent-qualifies-out-unqualified-lead` (NEW, type=happy)

**Given:**
- 5 unqualified personas YAML loaded via resolver `persona_kind="unqualified"`
- Sales_agent runtime con qualification capability (BANT/MEDDIC heuristics in `personality_profiles.system_instruction`)

**When:**
- `run_simulation(actor_profile=unqualified_persona, max_turns=8)` per archetype

**Then:**
- Sales_agent **NO** ejecuta tools de cierre: `enroll_*`, `schedule_appointment`, `send_payment_link`, `present_offer_ladder` (final close), `confirm_appointment`
- Sales_agent **SÍ** ejecuta tools de qualification: `qualify_lead`, `tag_lead_status` (status="not_qualified"), `schedule_nurture_followup` (futuro), o gracefully decline
- `termination_reason ∈ {GOAL_COMPLETION (qualified out), CUSTOMER_EXIT, MAX_TURNS}` — NO `AGENT_ERROR`
- Total turns ≤ 8 (early exit cuando qualification fails)
- Transcript final agent message respeta brand voice tenant + ofrece alternative path (lead magnet free, content gratis, futuro contact si cambia situación)

**Graders:**
- `{ type: tool_calls, forbidden: ["enroll_*", "send_payment_link", "confirm_appointment_*"], required: ["qualify_lead"] }`
- `{ type: state_check, target: eval_simulator_trace_event, query: "metadata->>'lead_status'='not_qualified'", expect: ">= 1" }`
- `{ type: llm_rubric, rubric: "docs/specs/rubrics/qualification-accuracy.md" (NEW Story E owns), threshold: 0.7 }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py::test_qualifies_out_unqualified_lead" }`

#### Scenario 6 — `nurture-realistic-multi-question` (NEW, type=happy)

**Given:**
- 5 nurture personas loaded via resolver `persona_kind="nurture"`
- Customer prompt v2 (DQ1) supports sub-slot pain/objection rotation

**When:**
- `run_simulation(actor_profile=nurture_persona, max_turns=15)` per archetype
- Customer simulator escala objections progresivamente turn-by-turn (1 objection = 1 turn typically; persona "remembers" what already asked)

**Then:**
- Total turns 8-15 (preguntón realistic — no early close, no infinite loop)
- Sales_agent demonstrates qualification: asks BANT-relevant questions before/during info delivery (Budget? Authority? Need? Timeline?)
- Sales_agent NO close prematuro (no `enroll_*` antes turn 8 mínimo)
- Sales_agent provides accurate info (no overpromise per `no-overpromise.md` rubric Story E)
- Customer simulator covers ≥ 5 objections distintas durante conversation (not 1 objection repeated)
- `termination_reason` typically `MAX_TURNS` (15) o `GOAL_COMPLETION` si nurture persona "se convence" (≤30% trials per voice fidelity)

**Graders:**
- `{ type: tool_calls, required: ["qualify_lead"], min_count: 1, max_count_premature_close: 0 (turn < 8) }`
- `{ type: state_check, target: eval_simulator_trace_event, query: "count(turn) >= 8 AND count(turn) <= 15", expect: "true" }`
- `{ type: transcript_constraint, min_objections_handled: 5 }`
- `{ type: llm_rubric, rubric: "docs/specs/rubrics/qualification-accuracy.md", threshold: 0.7 }`
- `{ type: llm_rubric, rubric: "docs/specs/rubrics/voice-fidelity.md", threshold: 0.7 }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/simulator/test_simulator_smoke.py::test_nurture_multi_question_realistic" }`

### 4. `max_turns` per `persona_kind` (NEW)

```python
MAX_TURNS_BY_PERSONA_KIND: dict[str, int] = {
    "happy": 10,           # qualified buyer, close típico 6-10 turns
    "nurture": 15,         # preguntón multi-objection, info-deep
    "unqualified": 8,      # early exit cuando agent qualifies out
    "adversarial": 5,      # early exit cuando agent rechaza
    # edge/negative: N/A (loader-only, no graph invocation)
}
```

Loader exposes helper: `get_max_turns_for_persona_kind(kind: PersonaKind) → int`. Runner consume al construir `SimulationState(max_turns=...)`.

### 5. Trial policy per `persona_kind` (NEW)

```yaml
trial_policy_by_persona_kind:
  happy:
    trials_per_scenario: 3        # production-critical: close
    pass_k_threshold: 0.5          # any-of-3 (Story F upgrades all-of-3)
  nurture:
    trials_per_scenario: 1        # information path; pass^k less critical
    pass_k_threshold: 1.0          # 1-trial = pass-on-1
  unqualified:
    trials_per_scenario: 3        # production-critical: qualification accuracy
    pass_k_threshold: 0.5
  adversarial:
    trials_per_scenario: 3        # security-critical
    pass_k_threshold: 0.5
```

### 6. Cost budget update (Story H interface scope)

**Spec v2 Story B baseline:** `<$0.30/suite` (9 scenarios)
**Spec v3 Story C delta:** `<$3.00/suite` (~25-30 effective simulations)

Breakdown estimado:
- Scenario 1 happy: 5 archetypes × 3 trials = 15 sims × $0.05 = $0.75
- Scenario 5 unqualified: 5 archetypes × 3 trials = 15 sims × $0.05 = $0.75
- Scenario 6 nurture: 5 archetypes × 1 trial × ~12 turns = 5 sims × $0.10 (longer) = $0.50
- Scenario 2 negative: ~3 fixtures × 1 trial = 3 sims × $0.01 (loader-only, no LLM) = $0.03
- Scenario 3 edge: ~3 fixtures × 1 trial = $0.03
- Scenario 4 adversarial: 1 fixture × 3 trials = 3 sims × $0.05 = $0.15
- **Total estimated:** ~$2.20/suite (10x baseline Story B)

Story H (`sales-agent-eval-cost-budget-cap`) interface receives expanded baseline. Story C declares; Story H enforces CI gate.

### 7. Customer prompt v2 (DQ1 ratificado)

Bump customer prompt v1 → v2 en Story B `_internal/customer_prompt.py` con sub-slots:

```
SLOT 1 (1h cache): system persona base
SLOT 2 (1h cache): persona profile core (id, traits, communication_style, dialect_code)
SLOT 3a (5min cache): pain_points list + budget_hint  ← NEW v2 sub-slot
SLOT 3b (5min cache): objections list (ordered by escalation)  ← NEW v2 sub-slot
SLOT 4 (no cache): actor_goal hidden (H10 defense)
SLOT 5 (no cache): conversation_history transcript
SLOT 6 (no cache): last_agent_response hint
```

Persona simulator decide which objection to raise based on conversation state + agent response — NO dump all objections upfront. Realistic preguntón behavior.

Migrator entry NEW: `("CustomerPrompt", 1, 2)` identity migrator (additive sub-slots, backward-compat for v1 personas without explicit objections list — empty list defaults to "no escalations").

### 8. Rubrics declared (NEW — Story E owns runtime)

| Rubric path | Owned by | Used in scenarios |
|---|---|---|
| `docs/specs/rubrics/qualification-accuracy.md` | Story E (NEW Story C declares) | 5, 6 |
| `docs/specs/rubrics/voice-fidelity.md` | existing | 1, 5, 6 |
| `docs/specs/rubrics/no-overpromise.md` | existing | 1, 5, 6 |
| `docs/specs/rubrics/no-hallucination.md` | existing | 1, 6 |

Story C declara los paths — Story E implementa runtime grader.

## Anti-creep guards

Lo siguiente **NO** está en Story C delta:

- ❌ Crear `qualification-accuracy.md` rubric (Story E)
- ❌ Implementar runtime BANT/MEDDIC checking en sales_agent (sales_agent SSoT untouched)
- ❌ Modificar `personality_profiles.system_instruction` per tenant (sales-agent-expert §3 protected surface)
- ❌ Crear `tag_lead_status` tool nuevo en sales_agent runtime (interface declared en spec — production tool work = separate story)
- ❌ Crear `schedule_nurture_followup` tool (futuro — separate story)
- ❌ Crear `qualify_lead` tool si NO existe ya en sales_agent (verify Story B sales_agent toolkit; si missing → escala separate story sales_agent toolkit)
- ❌ Cross-tenant nurture conversations (cada simulation = 1 tenant fijo)
- ❌ Multi-persona handoff (e.g., lead → conversion specialist)
- ❌ persona_kind values más allá de 6 (e.g., `loyal_customer`, `churned`) — futuras stories agregan via additive migrator
- ❌ Voice grader runtime (Story E)
- ❌ Pass^k all-of-3 enforcement (Story F)
- ❌ Budget cap CI gate enforcement (Story H)

## Decisiones cardinales delta (D13-D17)

| # | Decisión | Razón |
|---|---|---|
| D13 | persona_kind 4→6 values, schema_version 1→2, identity migrator | Realistic LATAM coverage requiere nurture + unqualified; additive migrator zero breakage v1 |
| D14 | 15 archetype-aware personas (5 happy + 5 nurture + 5 unqualified) — path `docs/specs/personas/archetype-aware/{persona-id}.yaml` | Cross-archetype × cross-kind matriz cubre realistic LATAM scenarios + production qualification capability test |
| D15 | `max_turns` per persona_kind (happy=10, nurture=15, unqualified=8, adversarial=5) | Realistic Latino conversations 10-15 turns; unqualified early exit demonstrate qualifying out efficiency |
| D16 | Trial policy heterogeneous: happy/unqualified/adversarial=3 trials, nurture=1 trial | Cost optimization — info paths less critical than close + qualification accuracy paths |
| D17 | Customer prompt v2 sub-slots pain/objection rotation — additive migrator from v1 | Realistic preguntón behavior requires progressive objection raising; backward-compat v1 personas |

## Impact downstream stories

| Story | Impact |
|---|---|
| D goldens-3-tenants-dataset | 20-30 goldens curated AHORA podrán cubrir 3 persona_kind × 5 archetypes — más coverage natural |
| E voice-fidelity-grader-runtime | Adds `qualification-accuracy.md` rubric + 2 NEW grader axes (qualifies_out, nurture_handles_objections) |
| F eval-pass-k-tracking | Heterogeneous trials_per_persona_kind requires per-kind pass^k bucketing |
| G voice-fidelity-ci-gate | NO cambio — ya consume Story E |
| H eval-cost-budget-cap | Baseline budget revisited: $0.30 → $3.00/suite |
| I adversarial-jailbreak-suite | NO cambio — adversarial persona_kind preserved + reuse Story B fixture |

## Próximo paso

1. `/po` recibe este delta-spec → bumps spec v2 → v3 inline (incorporates D13-D17 + Scenarios 5+6)
2. `/ux-agentico` (este skill) bumps design v1 → v2 con 15 transcripts ejemplo + max_turns matriz + slot v2 architecture
3. Chris ratifica spec v3 + design v2 (single yes/no — autonomy mandate ya autoriza)
4. State refining → refined
5. `/architect` orchestra `/architect-be` (loader 15 personas + dialect_catalog + 6-value Literal) + `/architect-agentic` (customer prompt v2 + max_turns matriz + scenarios 5+6 graphs)

## Changelog

- v1 2026-05-08T05:00Z — `/ux-agentico` redactó delta tras autonomy mandate Chris. Scope: 5 happy → 15 archetype-aware (3 kinds × 5 tenants) + persona_kind v1→v2 schema bump + customer prompt v1→v2 sub-slots + Scenarios 5+6 NEW + max_turns/trials per persona_kind. Cost baseline $0.30 → $3.00/suite (Story H interface).
