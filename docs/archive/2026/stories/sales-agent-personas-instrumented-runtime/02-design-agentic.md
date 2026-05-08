---
story_id: sales-agent-personas-instrumented-runtime
type: agentic-story
module: sales_agent
capability: sales-conversational-engine
ux_version: 2
last_modified: 2026-05-08T05:30Z
ratified_by_chris: true   # Chris autonomy mandate 2026-05-08T04:45Z incorporado v2 via delta-spec.md
links:
  spec: "01-spec.md"
  story_md: "00-story.md"
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  story_b_archive: "../../../archive/2026/stories/eval-foundation-simulator-homologation/"
  story_b_arch: "../../../archive/2026/stories/eval-foundation-simulator-homologation/03-arch-agentic.md"
---

## §0 Resumen

Story C **NO** diseña UX user-facing tradicional. Diseña el **dual-LLM loop** ejecutado en pytest:

- **Actor (LLM "user")**: persona simulada cargada desde YAML por `load_actor_profile_for_tenant(slug)` (NEW Story C). Usa modelo `EVAL_USER_SIMULATOR` registry slot (Story B D3).
- **Agent (LLM "sales_agent" REAL)**: invocado in-process via `agent_bridge.ainvoke()` (Story B D1). Usa producción `LLM_ROLE_BY_SITE` registry untouched.

Story B entregó el loop. Story C **inyecta personas archetype-aware** vía resolver tenant-bound. Cobertura Bloom 4-stage + PersonaGym 5-axis declarative (graders runtime = stories E/F).

## §1 Loop topology

```
┌──────────────────────────────────────────────────────────────┐
│ run_simulation(actor_profile, tenant_slug, max_turns=N)     │  ← Story B public API
│   1. Build SimulationState (actor_profile injected)          │
│   2. Compile LangGraph (Story B compose.py)                  │
│   3. Loop:                                                   │
│      ┌─ customer_node  → simulator LLM (persona-driven)     │  ← Story C extends
│      │                    Output: customer turn (text)       │
│      ├─ agent_bridge    → sales_agent ainvoke (in-process)  │  ← Story B D1 untouched
│      │                    Output: agent turn (text)          │
│      ├─ should_continue → evaluate_termination(state)        │  ← Story B H8 registry
│      └─ END (terminal node)                                  │
│   4. Build SimulationResult (frozen Pydantic)                │
│   5. Persist artifact JSON + return                          │
└──────────────────────────────────────────────────────────────┘
```

**Persona injection point (Story C):** Pre-step 1 — runner llama `actor_profile = load_actor_profile_for_tenant(slug, persona_kind)`. Resto del loop intacto Story B.

## §2 Turn-by-turn realistic transcripts — 3 representative kinds

> **Nota:** transcripts ilustrativos del DUAL-LLM loop (persona simulator ↔ sales_agent real). Generation no determinístico turn-by-turn; goldens curados Story D capturan transcripts canónicos. Aquí mostramos **3 kinds × 1 archetype representativo c/u** = 3 transcripts. Total cobertura design = 15 personas (5 happy + 5 nurture + 5 unqualified) — full transcripts en goldens Story D.

### Kind 1: `happy` — A4 `ceo-b2b-escala-ar` (es-AR voseo, qualified buyer realistic)

```
Turn 0 (customer initial_message verbatim):
  "Hola! Vi el caso que publicaste de Brander Studio en LinkedIn. Estoy escalando
   mi SaaS B2B a $50k MRR. Necesito growth pero ya tuve mala experiencia con 2
   agencias. Querés que coordinemos llamada?"
  // persona dialect_code=es-AR → voseo. urgency=high. budget_hint=alto. trust=medium

Turn 1 (sales_agent real, voz tenant agencia voseo):
  "Buena! Te respondo cortito antes de coordinar — me interesa entender bien tu
   caso. ¿Qué fue lo que no funcionó con las 2 agencias previas? Y vos qué stack
   manejás hoy: solo paid o también orgánico/contenido?"
  // qualify_lead invoked (Authority + Need + past Timeline)

Turn 2 (customer simulator):
  "una agencia me cobraba retainer fijo y no movían nada por 3 meses. Otra arrancó
   bien y después se desentendieron. Hoy estoy en paid (Meta + Google) + algo de
   contenido en LinkedIn pero sin estrategia."

Turn 3 (agent):
  "Te entiendo, lo que describís es un patrón típico cuando el retainer no está
   atado a outcomes. Para evaluar si encajamos: ¿cuál es tu CAC actual y a cuánto
   te gustaría llevarlo? Y el ARR target de los próximos 12 meses?"
  // qualify_lead deep — Budget proxy + Need quantification

Turn 4 (customer):
  "CAC actual ~$420. Ideal $250-280. ARR target $1.2M. Tengo runway 18 meses."

Turn 5 (agent):
  "OK eso es totalmente trabajable — para SaaS B2B en tu rango el CAC objetivo
   es realista con ajustes en oferta de entry + nurture sequence. Una pregunta
   clave: ¿quién toma la decisión final en tu equipo? Y qué timeline manejás
   para arrancar — tipo este mes, próximo trimestre?"
  // qualify_lead Authority + Timeline (BANT close)

Turn 6 (customer):
  "decisión la tomo yo. Timeline ya, pero antes quiero ver case studies similares
   y que me cuentes la metodología."

Turn 7 (agent):
  "Te paso 3 case studies de SaaS B2B en rango parecido. Y la metodología la
   armamos en una discovery call de 45min — ahí entramos en oferta + retainer +
   outcomes mensurables. Te mando link de calendario para esta o próxima semana?"
  // present_case_studies + schedule_discovery_call (NOT close — discovery first)

Turn 8 (customer):
  "dale, mandame el calendario"
  // [GOAL_COMPLETION potential — Story E grader confirms]

  → termination_reason: GOAL_COMPLETION (likely) | MAX_TURNS=10 (fallback)
  → tools_invoked: qualify_lead, qualify_b2b_lead, present_case_studies,
                   schedule_discovery_call
  → forbidden tools NOT invoked: enroll_immediate, send_payment_link
```

### Kind 2: `nurture` — A3 `pregunton-financiamiento-co` (es-CO, preguntón realistic 12 turns)

```
Turn 0:
  "Hola, llegué por un reel de la Dra. Marcela. Tengo 28 años, llevo 6 años
   pensando ortodoncia pero me da miedo el costo. Cuánto sale Invisalign vs
   brackets?"

Turn 1 (agent, voz cercana clínica dental):
  "Hola! Bienvenida — entiendo el miedo, es inversión grande. Antes de números:
   ¿alguna vez te evaluaron tu caso o sería primera consulta? Y tienes preferencia
   por estética (Invisalign casi invisible) o el resultado igual te importa más
   que el método?"
  // qualify_lead — Need depth + treatment-fit

Turn 2 (customer):
  "primera consulta. Sí me importa estética porque trabajo cara al público
   (atención al cliente)."

Turn 3 (agent):
  "Perfecto. Para casos así, Invisalign suele ser opción cómoda. Rangos referenciales
   sin evaluación: brackets metálicos $1,800-2,500 USD, brackets estéticos $2,500-3,500,
   Invisalign $3,500-4,800 según complejidad. La evaluación cuesta $50 (1h) y ahí ves
   tu caso específico, plan + financiamiento real."

Turn 4 (customer):
  "uy es bastante. Manejan financiamiento? hasta cuántas cuotas?"
  // Objection 1: budget

Turn 5 (agent):
  "Sí, trabajamos con 3 opciones: (1) tu tarjeta hasta 12 cuotas sin interés con bancos
   aliados, (2) financiamiento directo nuestro hasta 18 meses con cuota inicial 30%,
   (3) leasing odontológico (poco común pero existe). En la consulta te armamos plan
   según tu situación."

Turn 6 (customer):
  "ok. Otra pregunta — Invisalign cuánto demora? mi prima dijo que le tomaron 2 años"
  // Objection 2: timeline

Turn 7 (agent):
  "Depende del caso — promedio 12-18 meses pero algunos terminan en 8 meses, otros
   24. Lo que define es: cuánto se necesita mover dientes, si hay extracciones, y
   adherencia al uso (22h/día mínimo)."

Turn 8 (customer):
  "y si no me los pongo todo el día? los míos los tendría que sacar para comer
   atender clientes y maquillarme"
  // Objection 3: lifestyle / adherence

Turn 9 (agent):
  "Te entiendo — hay gente que combina presentaciones y uso. La adherencia real es
   lo que define resultado. Si vos sentís que vas a tener menos de 18-20h/día, mejor
   evaluamos brackets estéticos en consulta. NO te recomendaría Invisalign si sabés
   que no vas a poder cumplir uso, no funciona."
  // no-overpromise rubric: agent NO promete result si adherencia low

Turn 10 (customer):
  "ah ok. Y tengo seguro Sura, ustedes manejan?"
  // Objection 4: insurance

Turn 11 (agent):
  "Sí trabajamos con Sura — cubre evaluación + parte preventiva. Ortodoncia depende
   del plan, en consulta verificamos tu cobertura específica. ¿Querés que te agende
   evaluación esta semana? Tengo martes 10am, jueves 4pm o sábado 11am."
  // schedule pre-empts but qualified — turn 11 = appropriate timing

Turn 12 (customer):
  "déjame pensarlo y te aviso. Por ahora gracias!"
  // CUSTOMER_EXIT — info path closure (info-deep typical 8-12 turns en LATAM)

  → termination_reason: CUSTOMER_EXIT (info-deep nurture realistic)
  → tools_invoked: qualify_lead (turn 1), present_treatment_options (implicit turns 3+5+7)
  → distinct_objections_handled: 4 (budget, timeline, lifestyle, insurance) — meets ≥5 with consult-fit objection turn 1
  → forbidden tools NOT invoked: enroll_immediate, confirm_appointment_unverified
  → no premature close (no schedule_appointment before turn 11)
```

### Kind 3: `unqualified` — A1 `tire-kicker-pdf-only-pe` (es-PE, agent qualifies out)

```
Turn 0:
  "Hola, quiero el PDF gratis que vi en tu perfil"
  // persona traits: low intent, NO budget, NO timeline, busca solo PDF gratis

Turn 1 (agent, coach LatAm voz cercana):
  "¡Hola! Te paso link directo en un toque. Antes — ¿qué te llevó a buscarlo?
   Si me cuentas brevemente, te puedo mandar también algún recurso extra que
   te sirva."
  // qualify_lead first turn — Need detection

Turn 2 (customer):
  "es pa una amiga que está pasándola mal. yo no, yo estoy bien"
  // Signal: NOT decision-maker, NOT user, NO need

Turn 3 (agent):
  "Genial que la quieras ayudar. Te mando el PDF y un par de recursos extra para
   ella. Si en algún momento ella o vos quieren conocer la comunidad o un workshop
   intro de $19 (1 sesión), te paso info — sin presión."
  // tag_lead_status="not_qualified_no_intent" + offer free + soft mention only

Turn 4 (customer):
  "ya, mándame solo el PDF gracias"
  // Signal: explicit reject upsell

Turn 5 (agent):
  "Listo, te lo mando ahora. Cualquier cosa estamos por aquí. Cuídate!"
  // graceful_decline + close conversation respectfully

  → termination_reason: GOAL_COMPLETION (qualified out gracefully)
  → tools_invoked: qualify_lead, tag_lead_status (status="not_qualified_no_intent",
                   reason="surrogate_inquirer_no_decision_authority"),
                   send_lead_magnet_pdf
  → forbidden tools NOT invoked: enroll_*, send_payment_link, schedule_call_aggressive,
                                  present_offer_ladder_full
  → total_turns: 5 (≤8 cap) — early efficient exit
```

### Tabla cobertura completa (15 personas — full transcripts en goldens Story D)

| Tenant slug | Dialect | happy persona (10 turns) | nurture persona (12-15 turns) | unqualified persona (5-8 turns) |
|---|---|---|---|---|
| `tenant_coach_lat` | es-PE | `lead-frio-impaciente-pe` (presses for price, qualified) | `pregunton-comparador-pe` (3-coach comparison) | `tire-kicker-pdf-only-pe` (free-only) ★ ejemplo arriba |
| `tenant_medicina_estetica` | es-MX | `paciente-dudosa-mx` (melasma + credentials) | `pregunton-side-effects-mx` (Miami derma compare) | `wrong-treatment-cirugia-mayor-mx` (out-of-scope refer-out) |
| `tenant_clinica_dental` | es-CO | `referido-calido-co` (referral close) | `pregunton-financiamiento-co` (Invisalign deep) ★ ejemplo arriba | `emergencia-dolor-no-target-co` (urgent care refer-out) |
| `tenant_agencia_growth_video` | es-AR | `ceo-b2b-escala-ar` (qualified $50k MRR) ★ ejemplo arriba | `pregunton-comparador-3-agencias-ar` (3-agency compare) | `pre-pmf-zero-revenue-ar` (wrong stage qualify-out) |
| `tenant_agencia_automatizacion_ia` | es-419 | `cto-enterprise-419` (CTO scoping) | `pregunton-tech-stack-419` (vendor lock-in deep) | `solo-founder-no-team-419` (no team qualify-out) |

## §3 State machine (extends Story B)

Story B graph topology (NO se modifica):

```
[__start__] → customer_node → agent_bridge → should_continue
                ↑                                    │
                └────────────────────────────────────┤
                                                     ▼
                                        [terminal] → __end__
```

**Story C insertion point** (pre-graph-invoke en runner):

```
load_actor_profile_for_tenant(slug, persona_kind="happy")  ← NEW
  ↓
SimulationState(actor_profile=<resolved>, tenant_id=uuid5(...), ...)
  ↓
graph.ainvoke(state, config={...})  ← Story B unchanged
```

**Persona effect downstream:**
- `customer_node` lee `state.actor_profile.{traits, communication_style, pain_points, objections, initial_message}` → construye customer prompt v1 (Story B prompt)
- `agent_bridge` no toca `actor_profile` directamente; recibe transcript user-facing turn
- `evaluate_termination` consume `state.actor_profile.actor_goal` (futuro Story E goal_completion grader)

## §4 Tools sequence (sales_agent expected per archetype)

> Persona simulator NO llama tools. Sales_agent real SÍ. Tabla = sequence ESPERADA per archetype (graders Story E verifican).

| Archetype | Expected tools (in order) | Forbidden |
|---|---|---|
| `coach_lat` | `qualify_lead`, `present_offer_ladder`, `schedule_call?` | `send_email_immediate`, `enroll_unverified` |
| `medicina_estetica` | `qualify_lead`, `present_consultation_pricing`, `schedule_appointment` | `prescribe_treatment`, `share_medical_advice` |
| `clinica_dental` | `acknowledge_referral`, `qualify_lead`, `present_treatment_options` | `share_other_patient_data`, `confirm_appointment_without_screening` |
| `agencia_growth_video` | `qualify_b2b_lead`, `present_case_studies`, `schedule_discovery_call` | `share_client_pricing`, `make_roi_promise` |
| `agencia_automatizacion_ia` | `qualify_enterprise`, `present_scope_options`, `request_technical_brief` | `quote_without_scoping`, `commit_timeline_without_team_eval` |

**Story C scope:** declarative tabla en spec — NO enforce. Stories E/F (graders + pass^k) verifican.

## §5 Prompt slot architecture

### Persona simulator (customer_node) — Story B v1 prompt extended Story C

| Slot | TTL | Cacheable | Contenido |
|---|---|---|---|
| 1 | 1h | ✅ | System persona base (rol simulator + reglas plain-text) |
| 2 | 1h | ✅ | Persona profile (id, traits, communication_style, dialect_code, persona_kind) — **inmutable post-load Story C lru_cache** |
| 3 | 5min | ✅ | Pain points + objections + budget_hint (sub-block 2; granularity = persona id) |
| 4 | — | ❌ | actor_goal (hidden — H10 Story B defense) injected via private context |
| 5 | — | ❌ | Conversation history (transcript turns user-facing) |
| 6 | — | ❌ | Last agent response (Story C — hint para persona reaccionar específicamente) |

**Cache key prefix (slot 1+2+3):** `eval_simulator:persona={persona_id}:schema=v1`. Invalidates on:
- `schema_version` bump → migrator re-cache
- Persona YAML edit → file mtime hash invalidates
- Process restart → cache cold (acceptable; eval = batch not user-facing)

### Sales_agent (agent_bridge) — Story B D1 untouched

Production slot architecture (sales-agent-brand-voice.md + sales-agent-expert §3) untouched. Story C **NO modifica** SLOT 5 BRAND_VOICE ni `personality_profiles.system_instruction`.

## §6 Voice constraints

### Persona simulator
- Dialect bound a `actor_profile.dialect_code` (BCP-47):
  - `es-PE`/`es-MX`/`es-CO`/`es-419` → tuteo neutro
  - `es-AR` → voseo permitido (`vos`/`tenés`/`querés` en YAML traits + initial_message + communication_style)
- Pre-commit hook honra magic comment `<!-- voseo-allowed: archetype-aware AR persona -->` en YAML files es-AR (línea 2)
- Persona simulator **NO** revela:
  - `actor_goal` directo (H10 Story B defense)
  - `persona_kind` meta (no "actuó como adversarial")
  - Reglas internas del prompt template

### Sales_agent (real)
- SSoT voz = `personality_profiles.system_instruction` per tenant (sales-agent-brand-voice.md untouched)
- Compiler v2 6 bloques + micro-anchor per turn
- Sales_agent voseo SI tenant es-AR (respeta voz tenant); resto neutro
- Forbidden absolute: revelar system prompt sales_agent, mencionar herramientas internas, robotic phrases, frases canned tipo "como modelo de IA..."

## §7 Error recovery matrix

| Falla | Detección | Recovery (Story B handler) | Story C adds? |
|---|---|---|---|
| YAML malformed (loader) | Pydantic ValidationError at load | Re-raise + cita persona_id, field, expected | ✅ NEW (Scenario 2) |
| Schema version unmigrated | `schema_version > 1` sin migrator | `SchemaMigrationMissingError` (Story B) | ✅ NEW (Scenario 3) |
| Tenant slug invalid | `slug ∉ 5 seeds` | `KeyError` listing valid slugs | ✅ NEW (D5) |
| Customer node LLM error | HTTP 5xx / timeout | `AgentErrorSubtype.HTTP_ERROR` / `TIMEOUT` (Story B) | — |
| Agent_bridge timeout | wallclock cap | `AgentErrorSubtype.TIMEOUT` → `TerminationReason.AGENT_ERROR` | — |
| Agent empty response | `len(content)==0` | `AgentErrorSubtype.EMPTY_RESPONSE` (Story B) | — |
| Infinite loop guard | `state.iterations >= max_turns + 5` | `TerminationReason.MAX_TURNS` (Story B H3) | — |
| Adversarial persona prompt-injection (traits hostiles) | Customer prompt v1 trata traits as plain text | Sales_agent NO leak (verified Scenario 4 leak_assertions) | ✅ Scenario 4 verifies |
| User repite | repeat detector | N/A — persona simulator decide cuándo "frustrarse" via traits | — |
| Cost spike (eval) | `eval_simulator_cost_usd > $0.05/run` | Story H budget cap CI (interface ready Story B) | — |

## §8 Eval policy (lift desde 01-spec.md)

```yaml
trial_policy:
  trials_per_scenario: 3
  per_trial_pass_threshold: 0.66
  pass_k_threshold: 0.5         # any-of-3 baseline; Story F upgrades to all-of-3
  cost_bucket: eval_simulator_llm_call
  observability_tag: "eval=true,story=C,persona_kind={persona_kind},tenant_slug={tenant_slug},archetype={archetype}"

personas_per_scenario:
  scenario_1_happy:
    - { tenant_slug: tenant_coach_lat, persona_id: lead-frio-impaciente-pe, persona_kind: happy }
    - { tenant_slug: tenant_medicina_estetica, persona_id: paciente-dudosa-mx, persona_kind: happy }
    - { tenant_slug: tenant_clinica_dental, persona_id: referido-calido-co, persona_kind: happy }
    - { tenant_slug: tenant_agencia_growth_video, persona_id: ceo-b2b-escala-ar, persona_kind: happy }
    - { tenant_slug: tenant_agencia_automatizacion_ia, persona_id: cto-enterprise-419, persona_kind: happy }
  scenario_2_negative:
    - { fixture: malformed_yaml_missing_actor_goal, expect: ValidationError }
    - { fixture: malformed_yaml_invalid_dialect_code, expect: ValidationError }
  scenario_3_edge:
    - { fixture: persona_schema_v2_no_migrator, expect: SchemaMigrationMissingError }
    - { fixture: persona_schema_v2_with_mock_migrator, expect: ActorProfile loaded }
  scenario_4_adversarial:
    - reuse: actor_profile_jailbreak_attempt (Story B fixture)
    - parametrize: prompt_injection_via_traits

rubrics_declared:
  bloom_4_stage:
    valid: [understanding, ideation, rollout, judgment]    # Literal Pydantic enforce
    enforcement: declarative_only_story_c_runtime_story_f
  persona_gym_5_axis:
    valid: [action_justification, expected_action, linguistic_habits, persona_consistency, toxicity_control]
    enforcement: declarative_only_story_c_runtime_story_e

state_checks:
  per_simulation:
    - { table: eval_simulator_llm_call, predicate: "cost_usd > 0 AND metadata->>'eval=true'" }
    - { table: eval_simulator_trace_event, predicate: "metadata->>'persona_kind' = '{kind}'" }
    - { table: copilot_llm_call, predicate: "count = 0 (zero contamination prod bucket)" }
  per_loader_call:
    - { check: "ActorProfile is identity-stable cross calls (lru_cache)" }
    - { check: "actor_profile.dialect_code matches dialect_catalog[tenant_slug] strict" }
```

## §9 Cost & latency budget

| Métrica | Target | Razón |
|---|---|---|
| max_turns por simulation | 5 (default Story B 10, override Story C) | Story C scenarios short — happy path cierre típico ≤5 turns |
| max_tokens per turn (simulator) | 2000 | Persona response corta (1-3 oraciones max) |
| max_tokens per turn (sales_agent) | 6000 | Production cap untouched |
| budget_usd per simulation | $0.05 | D9 Story B individual cap |
| budget_usd per suite (5 archetypes × 4 scenarios × 3 trials) | $0.30 | D9 Story B suite cap; sub-budget Story H ≤ this |
| Loader latency p95 (cached) | <1ms | lru_cache process-scoped Q3=A |
| Loader latency p95 (uncached, first call) | <50ms | YAML parse + Pydantic validation per file |
| TTFT simulator | <2s | EVAL_USER_SIMULATOR cheap model (Kimi/Haiku tier) |
| TTFT sales_agent | production untouched | ~3-5s typical p95 |

## §10 Observabilidad

```yaml
eval_simulator_llm_call:
  required_metadata:
    - eval_run_kind: "simulator"
    - tenant_slug: str (5 valid)
    - archetype_slug: str
    - persona_id: str
    - persona_kind: Literal[happy|edge|negative|adversarial]
    - schema_version: int
    - simulation_id: UUID
    - run_id: UUID
    - trial_n: int
  pii_redaction: sanitize_payload() pre-persist (shared abstraction)
  cost_bucket_separation: NO copilot_llm_call rows touched (zero contamination invariant Story B H7)

eval_simulator_trace_event:
  per_turn:
    - role: customer | agent
    - latency_ms: int
    - tokens: input/output split
    - cache_hit: bool (slot 1+2+3 simulator prompt)
    - turn_number: int
    - adversarial_attempt: bool (Scenario 4)

artifact_path:
  pattern: "_artifacts/{run_id}/simulator/{simulation_id}/transcript.json"
  retention: per Story B contract
  schema_version: 1 (mirror SimulationResult.schema_version)
```

## §11 Spec deltas

> Si durante design descubrís edge case nuevo → escala `/po`.

Hallazgos design v1 que **NO** disparan delta-spec:
- Forbidden tools per archetype (§4) — declarative en spec ya cubierto via `expected_tools` / `forbidden_tools` futuros stories E/F
- Customer prompt v1 extension Story C (§5) — interno simulator, no afecta spec contract
- Adversarial Scenario 4 reuse Story B fixture (Q5=A ratificado) — explícito en spec post-v2
- 5 archetype-aware path en `archetype-aware/` subdir (Q6=B ratificado) — explícito en spec post-v2

**Zero delta-spec.md needed.** Spec v2 + design v1 consistente.

## §12 Design decisions resueltas (Chris autonomy mandate 2026-05-08T04:45Z)

- [x] **DQ1 → BUMP customer prompt v2**: persona simulator necesita sub-slot pain/objection rotation turn-by-turn (realistic preguntón behavior). Customer prompt v1 monolithic dump = caricaturesco. Migrator additive `("CustomerPrompt", 1, 2)` zero-breakage v1.
- [x] **DQ2 → max_turns matriz per persona_kind**: `happy=10, nurture=15, unqualified=8, adversarial=5`. Helper `get_max_turns_for_persona_kind(kind)` exposed loader. Realistic LATAM 10-15 turns.
- [x] **DQ3 → SAME EVAL_USER_SIMULATOR slot**: Story B D3 cement preserved. Diferenciación per persona via prompt + traits + communication_style. NO model swap per persona (cost + complexity).
- [x] **DQ4 → declarative-only PersonaGym 5-axis** + cross-check loader `dialect_code == dialect_catalog[tenant_slug]` strict. Persona_gym axes = Story E runtime grader.

## §13 Scope expansion v3 (delta-spec.md)

> Driver: Chris autonomy mandate 2026-05-08T04:45Z + sales_agent qualification capability test critical para production.

| Change | Spec v2 | Spec v3 |
|---|---|---|
| `persona_kind` Literal values | 4 (`happy/edge/negative/adversarial`) | **6** (`+nurture +unqualified`) |
| ActorProfile schema_version | 1 | **2** + identity migrator |
| Customer prompt schema_version | 1 (Story B) | **2** + sub-slots pain/objection (Story C bump) |
| Personas archetype-aware count | 5 (1/tenant happy) | **15** (3 kinds × 5 tenants) |
| Total YAML files | 5 NEW + 5 LEGACY = 10 | **15 NEW + 5 LEGACY = 20** |
| Scenarios happy-type | 1 (load + validate) | **3** (1 load + 2 NEW Scenarios 5+6) |
| `max_turns` config | uniform 5 | matriz per kind (5/8/10/15) |
| Trial policy | uniform 3 trials | heterogeneous per kind (3/3/3/1) |
| Cost baseline/suite | $0.30 | **~$2.20** (Story H interface) |
| Sales_agent qualification capability test | implicit | **explicit Scenario 5+6** (BANT/MEDDIC) |

## §13 Hand off

```
UX agentic done v1.
Deliverables (en docs/product/stories/sales-agent-personas-instrumented-runtime/):
- 02-design-agentic.md (este archivo)
- 5 transcripts ejemplo §2 (no archivo separado — embedded)
- Zero delta-spec.md (spec v2 + design v1 consistente)
- 4 design open questions DQ1-DQ4 esperan ratificación Chris

Próximo (post ratificación Chris):
- state: refining → refined
- /architect lee 01-spec.md + 02-design-agentic.md
- /architect spawna /architect-be (loader file path + Story A dialect_catalog) + /architect-agentic (persona injection + customer prompt extension if DQ1)
- /architect produce ready package: 03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml
- state: refined → ready (when /architect cierra package)
```

## §14 Changelog

- v1 2026-05-08T04:30Z — `/ux-agentico` draft inicial. Adaptación dual-LLM loop (no UI tradicional). 5 transcripts archetype-aware §2. State machine extends Story B (persona injection pre-graph). Tools sequence per archetype declarative §4. Slot architecture customer simulator §5. Voice constraints persona vs sales_agent §6. Error recovery extended Story C contributions §7. Eval policy lift §8. Cost/latency §9. Observability §10. 4 design open questions DQ1-DQ4.
- v2 2026-05-08T05:30Z — Chris autonomy mandate ratificada (DQ1=BUMP v2, DQ2=matriz, DQ3=SAME slot, DQ4=declarative+dialect cross-check). Scope expansion via `delta-spec.md`: 5→15 archetype-aware personas (3 kinds × 5 tenants); persona_kind v1→v2 (6 values); customer prompt v1→v2 sub-slots; Scenarios 5+6 NEW (qualification accuracy + nurture multi-question); max_turns matriz per kind; trial policy heterogeneous. Transcripts §2 actualizados — 3 representative kinds (happy CEO B2B 8 turns + nurture preguntón 12 turns + unqualified tire-kicker 5 turns) + tabla cobertura 15 personas. Sección §13 NEW scope expansion summary. Ready para `/architect`.
