---
story_id: sales-agent-goldens-3-tenants-dataset
type: service-story
module: sales_agent
capability: sales-conversational-engine
po_version: 3
last_modified: 2026-05-08T07:00Z
ratified_by_chris: true   # spec v3 ratificada Chris 2026-05-08T07:00Z (Q1-Q8 resueltas, todas opción recomendada)
reframe_history:
  - from: v1 (extract from production sales_agent_session table)
    to: v2 (synthetic-first — generate from simulator + Chris curation)
    reason: "Sales_agent NO en producción (cero conversaciones reales). Synthetic-first es state-of-the-art mayo 2026 (Anthropic Bloom + AWS Strands + τ-Bench + PersonaGym). Story A (5 tenant seeds) + Story B (run_simulation) + Story C (15 archetype-aware personas) habilitan generación dual-LLM realistic."
    date: 2026-05-08T06:30Z
role_in_outcome: "D — goldens-generated-from-simulation (curated dataset 20-30 YAMLs)"
depends_on:
  - story_a: eval-foundation-tenant-seed-data (DONE 2026-05-07) — `load_eval_tenant(slug) → TenantContext` + `dialect_catalog.yaml`
  - story_b: eval-foundation-simulator-homologation (DONE 2026-05-08) — `run_simulation(actor_profile, ...) → SimulationResult` public API + `EvalSimulatorObservabilityContext` + `eval_simulator_llm_call`/`eval_simulator_trace_event` cost-bucket tables
  - story_c: sales-agent-personas-instrumented-runtime (REFINED 2026-05-08, awaiting build) — `load_actor_profile_for_tenant(slug, persona_kind)` + 15 archetype-aware personas YAML + `get_max_turns_for_persona_kind(kind)` helper
consumed_by:
  - story_e: sales-agent-voice-fidelity-grader-runtime — graders ejecutan vs golden transcripts curados
  - story_f: sales-agent-eval-pass-k-tracking — pass^k bucketed por (tenant_slug × persona_kind × golden_id)
  - story_g: sales-agent-voice-fidelity-ci-gate — CI gate corre runner vs goldens dataset GREEN/FAIL
  - story_h: sales-agent-eval-cost-budget-cap — budget cap measured contra full-suite cost (goldens count drives baseline)
  - story_i: sales-agent-adversarial-jailbreak-suite — extends dataset con `persona_kind=adversarial` slot (Story I scope, no aquí)
links:
  story_md: "00-story.md"
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  story_a_archive: "../../../archive/2026/stories/eval-foundation-tenant-seed-data/"
  story_b_archive: "../../../archive/2026/stories/eval-foundation-simulator-homologation/"
  story_c_spec: "../sales-agent-personas-instrumented-runtime/01-spec.md"
  story_c_design: "../sales-agent-personas-instrumented-runtime/02-design-agentic.md"
  v1_archived_commit: "f7624c9f"   # v1 spec (production-extraction paradigm) — superseded
---

## Resumen ejecutivo

> **Reframe v1→v2 (2026-05-08 post Chris ratification 2026-05-06T17:11Z):** paradigma cambia de **"extraer 12 goldens de tablas `sales_agent_session` producción"** (inviable — sales_agent no está en prod) a **"generar 20-30 goldens via dual-LLM simulator (Story B) + 15 archetype-aware personas (Story C) sobre 5 tenant seeds (Story A) + curación manual Chris"** (state-of-the-art mayo 2026: Anthropic Bloom + AWS Strands ActorProfile + τ-Bench scenario coverage + PersonaGym persona axes).

Construir el **ground-truth dataset sintético-first** del eval suite `sales_agent`. Pipeline:

1. **Generar candidatos:** script ejecuta `run_simulation()` (Story B API) sobre matrix `{5 tenants × 3 persona_kinds × N trials}` = 15 cells × N candidatos por cell.
2. **Curar manualmente:** Chris revisa transcripts (HTML preview generado por script — render simulator artifact JSON) → selecciona 1-2 winners por cell → produce 20-30 goldens finales.
3. **Persistir como YAML checked-in** bajo `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml` + README + Pydantic schema validator + pre-commit hook PII defense-in-depth.

Stories E (voice fidelity grader), F (pass^k), G (CI gate) anclan asserts a este dataset. Story I (adversarial) extiende dataset con `persona_kind=adversarial` slot (out-of-scope aquí).

## Cambio respecto v1

| Aspecto | v1 (archivada commit `f7624c9f`) | v2 (este spec) |
|---|---|---|
| Source | `sales_agent_session` table producción | `run_simulation()` dual-LLM in-process |
| Curation | Agent-helper extrae candidatos, Chris elige | Script genera N candidatos, HTML preview, Chris selecciona |
| Tenants | 3 reales seleccionar | 5 seed sintéticos Story A (deterministic) |
| Personas | implicit (sesiones reales) | 15 archetype-aware Story C (3 kinds × 5 tenants) |
| Total goldens | 12 (3 tenants × 4 escenarios) | **20-30** (5 tenants × 3 persona_kinds × 1-2 winners) |
| PII risk | alto (transcripts reales) | bajo (synthetic-only — defense-in-depth scanner igual) |
| Reproducibility | low (transcripts cambian si refrescás extracción) | high (fixed seed + frozen ActorProfile + cached pricing snapshot) |
| Cost | zero (read-only DB) | ~$3-8 USD generation budget (Story H interface) |

## Coverage matrix (target 20-30 goldens)

| Tenant slug | Dialect | happy | nurture | unqualified | row total |
|---|---|---|---|---|---|
| `tenant_coach_lat` | es-PE | 1-2 | 1-2 | 1-2 | 3-6 |
| `tenant_medicina_estetica` | es-MX | 1-2 | 1-2 | 1-2 | 3-6 |
| `tenant_clinica_dental` | es-CO | 1-2 | 1-2 | 1-2 | 3-6 |
| `tenant_agencia_growth_video` | es-AR | 1-2 | 1-2 | 1-2 | 3-6 |
| `tenant_agencia_automatizacion_ia` | es-419 | 1-2 | 1-2 | 1-2 | 3-6 |
| **Total** | | 5-10 | 5-10 | 5-10 | **20-30** |

> Adversarial NOT included — Story I owns `persona_kind=adversarial` slot.
> Edge/negative persona_kinds skipped — loader-only (no graph invocation per Story C D15 max_turns matriz).

## Generation matrix (script input)

```yaml
runs_per_cell: 5    # Q2 ratified — 5 candidatos por (tenant × persona_kind) → 5 tenants × 3 kinds × 5 = 75 simulations
trials_per_run: 1   # 1 trial per simulation (no pass^k aquí — Story F scope)
seed_strategy: deterministic    # fixed seed per (tenant_slug, persona_kind, run_n) → reproducible
output:
  artifact_dir: "_artifacts/goldens_generation/{run_id}/"
  preview_md: "_artifacts/goldens_generation/{run_id}/preview.md"   # Q3 ratified — Markdown table inline (NO HTML, NO Streamlit)
```

> Cost baseline: 75 simulations × avg 8 turns × ~3000 tokens/turn × $0.30/1M = **~$5.40/full generation run**. Chris curation downstream zero-cost (manual). Story H budget cap interface scope.

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `goldens-generation-and-curation-happy-path` (`type: happy`)

**Given:**
- Story A delivered: `load_eval_tenant(slug) → TenantContext` + `dialect_catalog.yaml` (5 archetype slugs ratified)
- Story B delivered: `run_simulation(actor_profile, max_turns) → SimulationResult` + `EvalSimulatorCallbackHandler` + cost-bucket tables (`eval_simulator_llm_call`, `eval_simulator_trace_event`)
- Story C delivered: `load_actor_profile_for_tenant(slug, persona_kind="happy"|"nurture"|"unqualified")` + 15 archetype-aware personas YAML + `get_max_turns_for_persona_kind(kind)` helper
- Existe Pydantic schema `GoldenScenarioModel` en `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` v1 con campos cement (ver §Schema)
- Existe script `backend/scripts/generate_golden_candidates.py` que orquesta `run_simulation()` matrix + HTML preview generator

**When:**
- Dev ejecuta `python backend/scripts/generate_golden_candidates.py --runs-per-cell 5 --output-dir _artifacts/goldens_generation/{run_id}/`
- Script corre 75 simulations en paralelo (Story B `asyncio.gather + Semaphore(10)` pattern)
- Script genera Markdown table preview (`_artifacts/goldens_generation/{run_id}/preview.md`) con 75 transcripts agrupados por cell (tenant × persona_kind × run_n) — IDE-renderable, parallel-safe, zero browser dep (Q3 ratified)
- Chris abre preview en IDE, revisa transcripts, selecciona 1-2 winners por cell (target 20-30 total)
- Chris ejecuta `python backend/scripts/promote_golden.py --simulation-id <uuid> --golden-id <slug>` por cada winner → script lee artifact JSON + escribe `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml`

**Then:**
- Existen entre 20-30 archivos YAML válidos contra `GoldenScenarioModel` distribuidos en árbol `goldens/{tenant_slug}/{persona_kind}/`
- `pytest backend/tests/agentic_evals/sales_agent/test_goldens_schema.py -v` pasa N assertions (1 por golden) — cada YAML loadea, valida, y referencia válida `actor_profile_id` (existe en `docs/specs/personas/archetype-aware/`) + `tenant_slug` (existe en Story A 5 seeds)
- Cobertura mínima cumplida: cada `(tenant_slug, persona_kind)` cell tiene ≥ 1 golden — `pytest backend/tests/agentic_evals/sales_agent/test_goldens_coverage.py::test_all_cells_covered` GREEN
- Existe `backend/tests/agentic_evals/sales_agent/goldens/README.md` con secciones: "Pipeline generación", "Cómo agregar/refrescar golden", "Política de actualización", "Schema reference"
- Capability `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` campo `eval.goldens_dataset_path: "backend/tests/agentic_evals/sales_agent/goldens/"` + `eval.goldens_count_target: { min: 20, max: 30 }` + `eval.goldens_generation_script: "backend/scripts/generate_golden_candidates.py"`
- Cost-bucket invariant preservado: filas escritas en `eval_simulator_llm_call` (Story B H7) — NO `copilot_llm_call` rows touched
- Idempotency: re-ejecutar `promote_golden` con mismo `--golden-id` overwrites YAML deterministically (no append, no duplicate)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_schema.py" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_coverage.py" }`
- `{ type: contract_test, path: "backend/tests/scripts/test_generate_golden_candidates.py" }`
- `{ type: contract_test, path: "backend/tests/scripts/test_promote_golden.py" }`
- `{ type: state_check, target: filesystem, query: "find backend/tests/agentic_evals/sales_agent/goldens -name '*.yaml' | wc -l", expect: ">= 20 AND <= 30" }`
- `{ type: state_check, target: filesystem, query: "test -f backend/tests/agentic_evals/sales_agent/goldens/README.md" }`
- `{ type: state_check, target: capability_yaml, query: "grep -q 'goldens_dataset_path' docs/product/capabilities/sales-agent/sales-conversational-engine.yaml" }`
- `{ type: state_check, target: eval_simulator_llm_call, query: "SELECT count(*) WHERE metadata->>'eval'='true' AND metadata->>'story'='D'", expect: ">= 75" }`
- `{ type: state_check, target: copilot_llm_call, query: "SELECT count(*) WHERE created_at > '<run_start>'", expect: "0 (cost-bucket invariant)" }`

---

### Scenario 2 — `golden-yaml-schema-invalid` (`type: negative`)

**Given:**
- Existen los 20-30 goldens válidos del Scenario 1
- Dev intenta crear/modificar un golden inválido: campo requerido faltante (`expected_termination_reason` omitido), enum violation (`persona_kind: lead_random`), `actor_profile_id` no existe en `docs/specs/personas/archetype-aware/`, o `tenant_slug` no ∈ 5 Story A seeds

**When:**
- Dev ejecuta `git add backend/tests/agentic_evals/sales_agent/goldens/{slug}/golden_invalid.yaml && git commit`

**Then:**
- Pre-commit hook ejecuta `pytest backend/tests/agentic_evals/sales_agent/test_goldens_schema.py -v` y falla con `pydantic.ValidationError` o `ReferentialIntegrityError` citando archivo + campo + constraint
- Commit es **bloqueado** (exit code ≠ 0)
- Estado del filesystem queda igual (golden inválido NO entra a HEAD)
- Mensaje cita: `golden_path`, `field_name`, `expected_constraint`, `actual_value` (zero ambigüedad)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_schema.py", expect_fail_on: "missing_field|invalid_enum|orphan_reference" }`
- `{ type: state_check, target: pre_commit_hook, expect: "exit_code != 0 AND stderr matches 'ValidationError|ReferentialIntegrityError'" }`
- `{ type: pytest_raises, exception: "pydantic.ValidationError|ReferentialIntegrityError" }`

---

### Scenario 3 — `cell-coverage-gap` (`type: edge`)

**Given:**
- Dev (o futuro Chris refresh) elimina todos los goldens de una `(tenant_slug, persona_kind)` cell — e.g., borra carpeta `goldens/tenant_clinica_dental/nurture/`
- Coverage gate corre en CI o pre-commit

**When:**
- `pytest backend/tests/agentic_evals/sales_agent/test_goldens_coverage.py::test_all_cells_covered` ejecuta

**Then:**
- Test FAIL con mensaje específico: `"Coverage gap: cell (tenant_clinica_dental, nurture) has 0 goldens. Required minimum: 1"`
- Output cita TODAS las cells violators (no early-exit en first failure — informa scope completo)
- Test sugiere comando recovery: `python backend/scripts/generate_golden_candidates.py --tenant tenant_clinica_dental --persona-kind nurture --runs-per-cell 5`
- CI gate Story G integration: si gap detected → CI red

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_coverage.py::test_reports_all_cells_with_gaps" }`
- `{ type: state_check, target: stdout, query: "stdout contains 'Coverage gap' AND lists violator cells" }`
- `{ type: integration, path: "backend/tests/scripts/test_generate_golden_candidates.py::test_handles_single_cell_regen" }`

---

### Scenario 4 — `pii-leak-defense-in-depth` (`type: adversarial`)

> AI-resistant: aunque transcripts son sintéticos (Story C personas + Story B simulator usan `sanitize_payload` upstream), defense-in-depth previene leak de patterns que parezcan PII real, copy-paste accidental Chris durante curación, o regression si Story C modifica personas con datos accidentalmente similares a PII real.

**Given:**
- Dev (o Chris distraído durante curación) intenta commit golden YAML con PII visible en `transcript[].content` o `metadata`:
  - Email: `juan.perez@empresacliente.com`
  - Teléfono LatAm: `+54 9 11 5555-1234` (AR), `+52 55 1234 5678` (MX), `+51 9 8765 4321` (PE)
  - DNI/CUIT/RUT/RFC: `38.456.789` (AR DNI), `20-12345678-9` (AR CUIT), `12.345.678-9` (CL RUT), `MELO850101AB1` (MX RFC)
  - URL interna: `https://admin-internal.nicolify.com/tenant/uuid-real/...`

**When:**
- Dev ejecuta `git add backend/tests/agentic_evals/sales_agent/goldens/... && git commit`

**Then:**
- Pre-commit hook nuevo `scripts/git-hooks/pre-commit` Section 8 ejecuta `python backend/scripts/scan_goldens_pii.py backend/tests/agentic_evals/sales_agent/goldens/`
- Scanner detecta los 4 patrones (regex email RFC 5322, regex LatAm phone intl + national, regex DNI/CUIT/RUT/RFC LatAm, regex URL `*.nicolify.com` no whitelisted)
- Hook **bloquea commit** con mensaje: `"PII detected in goldens/{path}:{line}: {pii_category}. Remove or run sanitize_payload() upstream."`
- Test `backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py` provee fixtures (4 categorías × 3 idiomas LatAm) y verifica detección por categoría
- Defense-in-depth: cada golden checked-in tiene assertion en `test_goldens_schema.py::test_no_pii_in_committed_goldens` que re-corre scanner sobre 20-30 reales (zero matches expected — synthetic-first invariant)
- Magic comment escape rechazado: `<!-- pii-allowed -->` NO existe (PII tiene cero excusas legítimas en goldens — strict block)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py", expect: "4 PII categories × 3 LatAm dialects detected on adversarial fixtures" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_schema.py::test_no_pii_in_committed_goldens", expect: "0 matches on real 20-30 goldens" }`
- `{ type: state_check, target: pre_commit_hook, expect: "exit_code != 0 AND stderr matches 'PII detected'" }`
- `{ type: integration, path: "backend/tests/scripts/test_pre_commit_hook.py::test_blocks_pii_in_goldens" }`

---

## Schema (`GoldenScenarioModel` v1 cement)

```python
# backend/tests/agentic_evals/sales_agent/goldens/_schema.py

class GoldenScenarioModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    schema_version: Literal[1] = 1
    id: str                                              # slug-style, unique cross-dataset
    tenant_slug: Literal[5 archetype slugs from Story A]
    persona_kind: Literal["happy", "nurture", "unqualified"]   # NO adversarial here (Story I)
    actor_profile_id: str                                # references docs/specs/personas/archetype-aware/{id}.yaml
    actor_profile_schema_version: Literal[2]             # frozen at curation time (Story C v3)
    dialect_code: str                                    # BCP-47, must match dialect_catalog[tenant_slug]
    transcript: list[GoldenTurnModel]                    # full conversation captured from simulation
    expected_termination_reason: Literal[                # subset of Story B TerminationReason enum
        "GOAL_COMPLETION", "MAX_TURNS", "CUSTOMER_EXIT"
    ]
    expected_voice_attributes: list[str]                 # subset of personality_profile keys (Story E grades vs this)
    expected_tools_invoked: list[str]                    # tool calls expected (e.g., ["qualify_lead", "schedule_appointment"])
    forbidden_tools: list[str]                           # tool calls forbidden (e.g., ["enroll_*"] for unqualified personas)
    expected_min_distinct_objections_handled: int | None # nurture only — min sub-slot rotation count
    metadata: GoldenMetadataModel                        # generation provenance

class GoldenTurnModel(BaseModel):
    role: Literal["customer", "agent"]
    content: str                                         # exact verbatim from simulation_artifact.transcript
    turn_number: int
    tool_calls: list[str] | None = None                  # agent turns only
    latency_ms: int | None = None                        # observability snapshot

class GoldenMetadataModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    generated_from_simulation_id: str                    # UUID5 derived (Story B D11) — links back to artifact
    generated_at: datetime                               # UTC
    curated_by: str                                      # "chris" (oracle of truth)
    curated_at: datetime                                 # UTC
    generation_run_id: str                               # UUID — links to _artifacts/goldens_generation/{run_id}/
    seed: int                                            # deterministic re-generation
    cost_usd_at_generation: Decimal                      # observability snapshot
    notes: str                                           # Chris freeform — "why this candidate won curation"
```

## Trial policy (service-story — N/A agentic trials)

```yaml
# Goldens son data assets deterministic — no agentic trial_policy.
generation:
  runs_per_cell: 5                  # 75 sims total
  semaphore_concurrent: 10          # Story B pattern
  cost_budget_per_run_usd: 8.00     # Story H interface; abort si exceeded
  retry_on_provider_error: 1        # transient errors
  observability_tag: "eval=true,story=D,phase=generation,run_id={run_id}"
curation:
  manual_only: true                 # Chris is the oracle
  preview_format: "html"            # navegable per cell
  promotion_command: "python backend/scripts/promote_golden.py --simulation-id <uuid> --golden-id <slug>"
```

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Synthetic-only | Zero PII real en cualquier golden YAML — defense-in-depth scanner enforces | `scan_goldens_pii.py` + arch test + pre-commit hook |
| Tenant isolation | Cada golden contiene SOLO datos de un único `tenant_slug`. Cross-tenant data → schema fail | `GoldenScenarioModel` + arch test |
| Reproducibility | Re-generación deterministic con `--seed N` produce mismas N candidatas (cache by simulation_id) | CLI flag + LRU cache + frozen ActorProfile |
| Schema versioning | `schema_version: 1` cement. Future bumps via SCHEMA_MIGRATIONS registry (Story B H1 pattern reused) | Pydantic Literal + migrator registry |
| Referential integrity | `actor_profile_id` exists in Story C YAMLs + `tenant_slug` ∈ 5 Story A seeds + `dialect_code == dialect_catalog[tenant_slug]` strict | `test_goldens_schema.py` cross-reference checks |
| Cost-bucket | Generation writes to `eval_simulator_llm_call` ONLY (Story B H7 cement) | DB query post-generation verifies row presence + zero `copilot_llm_call` |
| i18n / voseo | `transcript[].content` may contain voseo if `dialect_code = es-AR` (sales_agent voice exception). README + tooling messages neutro | Pre-commit hook honra magic comment per-YAML when `dialect_code = es-AR` |
| Determinism (load) | `pytest -k goldens` parallel-safe: each YAML loads independent (no shared mutable state) | conftest fixture scope=function |
| CI cost | Goldens load + schema validation < 5s for 30 YAMLs | pytest perf budget |
| Generation idempotency | `promote_golden --golden-id X --simulation-id Y` overwrites YAML deterministically | unit test |

## Constraints técnicos heredados

- `.claude/rules/anti-duplication.md` — script CONSUMES Story A `load_eval_tenant`, Story B `run_simulation`, Story C `load_actor_profile_for_tenant`. Schema validator CONSUMES `sanitize_payload` (shared). NO mirror.
- `.claude/rules/auditor-downstream-regression.md` — tabla SSoT MUST add row when `goldens/` path created (R3 row addition required, downstream consumers = Stories E/F/G/H/I)
- `.claude/rules/spanish-text.md` — voseo permitido en `transcript[].content` cuando `dialect_code = es-AR` (sales_agent voice exception). README + CLI messages + scanner messages = español neutro
- `.claude/rules/tdd-mandatory.md` — RED tests primero (schema → coverage → script → PII scanner → integration runner)
- `.claude/rules/backend-ddd.md` — script bajo `backend/scripts/`, tests bajo `backend/tests/`. NO tocar `modules/sales_agent/{domain,application,api}/` (data asset puro)
- `.claude/rules/tenant-isolation.md` — N/A directly (synthetic data, no DB tenant queries) — referential integrity check enforces 1 tenant per golden YAML
- `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` — PII canonical patterns extended con LatAm DNI/CUIT/RUT/RFC + nicolify internal URLs
- `.claude/rules/parallel-safety.md` — Story D parallel-safe (data asset, no DB writes outside cost-bucket eval tables)
- `sales-agent-expert` skill §3 protected surfaces — N/A (NO touching production runtime — pure test infrastructure)
- Story B H9 cement — script imports ONLY de `simulator/__init__.py` public API (7 names). NO touching `_internal/`.
- Story C cement — `load_actor_profile_for_tenant` signature stable; goldens reference `actor_profile_id` + `actor_profile_schema_version` (snapshot at curation time, immune to v3+ future bumps via SCHEMA_MIGRATIONS pattern)

## Cross-module impact

- **Lee de:**
  - `backend/tests/fixtures/eval/tenants/loader.py` (Story A) — `load_eval_tenant(slug)`
  - `backend/tests/fixtures/eval/tenants/dialect_catalog.yaml` (Story A) — BCP-47 catalog
  - `backend/tests/agentic_evals/sales_agent/simulator/__init__.py` (Story B) — `run_simulation`, `SimulationResult`, `ActorProfile`, `TerminationReason`
  - `backend/tests/agentic_evals/sales_agent/simulator/_internal/personas_loader.py` (Story C) — `load_actor_profile_for_tenant`, `get_max_turns_for_persona_kind`
  - `docs/specs/personas/archetype-aware/*.yaml` (Story C) — 15 personas YAML
- **Escribe a:**
  - `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml` (NEW — 20-30 files)
  - `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` (NEW — Pydantic schema)
  - `backend/tests/agentic_evals/sales_agent/goldens/README.md` (NEW)
  - `backend/scripts/generate_golden_candidates.py` (NEW)
  - `backend/scripts/promote_golden.py` (NEW)
  - `backend/scripts/scan_goldens_pii.py` (NEW)
  - `scripts/git-hooks/pre-commit` Section 8 (extend — PII scanner gate)
  - `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (extend — `eval.goldens_*` fields)
  - `eval_simulator_llm_call` + `eval_simulator_trace_event` tables (Story B contract — observability rows during generation)
- **Es leído por:**
  - Story E `voice-fidelity-grader-runtime` — graders consume goldens dataset path
  - Story F `eval-pass-k-tracking` — pass^k bucket por (tenant × persona_kind × golden_id)
  - Story G `voice-fidelity-ci-gate` — CI runs vs goldens count target
  - Story H `eval-cost-budget-cap` — budget cap measured contra goldens-suite full-run cost
  - Story I `adversarial-jailbreak-suite` — extends dataset con `persona_kind=adversarial` (additive, no migration)
- **Eventos emitidos:** ninguno (data asset)
- **Eventos consumidos:** ninguno

## Out of scope (anti-creep)

- ❌ Adversarial goldens (`persona_kind=adversarial`) — Story I scope, dataset extends additively
- ❌ Edge/negative `persona_kind` goldens — loader-only test (Story C D15 max_turns matriz N/A)
- ❌ Production-extracted goldens (paradigma v1 superseded — sales_agent no en prod)
- ❌ Versioning tooling beyond git history — git diff goldens/ basta para PI-12
- ❌ Auto-curation 100% (sin Chris en loop) — drift risk sin oracle
- ❌ Cross-language goldens (en/pt/etc.) — scope LatAm Spanish only
- ❌ Refresh policy automation (cron/CI) — manual trigger Chris cuando aplique
- ❌ Goldens >30 — saturation point eval suite (Story F pass^k diminishing returns >30 trials)
- ❌ Golden mutation post-promotion (immutable post-commit excepto Chris explicit refresh)
- ❌ Tocar `simulator/__init__.py` public API surface (Story B H9 frozen)
- ❌ Tocar `docs/specs/personas/archetype-aware/*.yaml` (Story C consume only)
- ❌ Tocar `backend/tests/fixtures/eval/tenants/` (Story A consume only)
- ❌ Modificar `core/config.py` defaults (no flag flips this story)
- ❌ Re-run generation en CI per-PR (cost prohibitive — generation manual trigger only)

## Decisiones cardinales (cement)

| # | Decisión | Razón |
|---|---|---|
| D1 | Synthetic-first paradigm — generation via Story B `run_simulation()` + Story C 15 personas + Story A 5 tenants | v1 (extract from prod) inviable — sales_agent no en prod. State-of-the-art mayo 2026 |
| D2 | Coverage matrix 5 tenants × 3 persona_kinds × 1-2 winners = **20-30 goldens** target | Cubre Bloom 4-stage + production-critical happy/unqualified + realistic LATAM nurture |
| D3 | Persona kinds in scope: `happy`, `nurture`, `unqualified`. Adversarial = Story I (additive) | Defense-in-depth — security suite isolated, easier to extend without dataset re-curation |
| D4 | Pipeline 2 fases: (1) script genera N candidatos paralelos via `run_simulation()`, (2) Chris cura manual via HTML preview + `promote_golden` CLI | Hybrid automation — máquina hace grunt work, oracle de producto decide winners |
| D5 | Goldens path: `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/{persona_kind}/{golden_id}.yaml` | Tree facilita coverage gate per-cell + IDE navigation |
| D6 | Schema `GoldenScenarioModel` v1 cement con `schema_version: Literal[1]`. Future bumps via SCHEMA_MIGRATIONS registry (Story B H1 pattern reused) | Forward-compat 5+ years sin re-curation |
| D7 | `actor_profile_schema_version: Literal[2]` snapshot at curation time | Goldens immune a Story C v3+ future schema bumps (frozen artifact contract) |
| D8 | Generation deterministic via `--seed N` flag + frozen ActorProfile + cached pricing snapshot | Reproducibility — dev re-runs misma generación, mismos candidatos |
| D9 | Cost-bucket invariant: generation writes `eval_simulator_llm_call` ONLY (Story B H7 cement) | Zero contamination prod observability |
| D10 | PII defense-in-depth: scanner pre-commit hook Section 8 + `test_no_pii_in_committed_goldens` arch test. NO magic comment escape (strict block) | Synthetic-first regression risk Chris copy-paste real PII durante curación |
| D11 | Coverage gate per-cell: each `(tenant × persona_kind)` ≥ 1 golden — `test_all_cells_covered` enforces | CI red si gap; prevents drift over time |
| D12 | Curation tooling: **Markdown table preview** (`preview.md` inline, IDE-renderable) + `promote_golden` CLI. NO HTML, NO Streamlit/web UI (Q3 ratified) | Zero browser dep, parallel-safe, IDE-friendly, terminal-renderable. Lighter than HTML, easier diff via git |
| D13 | `metadata.generated_from_simulation_id` UUID5 stable hash de `(tenant_slug, persona_id, run_n, seed)` Story B D11 contract | Idempotent re-generation; goldens trace back to source simulation |
| D14 | `expected_*` fields populated by `promote_golden`: termination_reason + tools_invoked + forbidden_tools auto-derived from simulation result; **`expected_voice_attributes` auto-extracted subset de tenant `personality_profile.system_instruction` keys** (Q5 ratified) per `dialect_code`. Chris override en `notes` freeform string (Q7 ratified) | Hybrid: máquina hace grunt work, Chris añade judgment freeform. Story E grader consume `expected_voice_attributes` directo |
| D15 | README documents pipeline + refresh policy. Refresh trigger: (a) Story C personas evolve schema_version 2→N, (b) voice fidelity grader saturate >0.95 (overfitting signal), (c) every 6 months calendar review | Manual trigger only — automated refresh = drift risk |
| D16 | Goldens immutable post-commit excepto refresh explícito (delete + regenerate). NO partial mutation | Audit trail clean — git history es la versioning |
| D17 | `forbidden_tools` per persona_kind enforced declarative: `unqualified` → `forbidden: [enroll_*, send_payment_link]` (sales_agent must qualify out, not close); `happy/nurture` → `forbidden: []` (close OK) | Aligns con Story C Scenario 5 production-critical qualification capability test |

## Open questions — RESUELTAS (Chris ratificó 2026-05-08T07:00Z)

- [x] **Q1 → A**: Goldens count target = **20-30 range** (5 tenants × 3 kinds × 1-2 winners). Diminishing returns >30 per τ-Bench. Flexible — Chris elige según calidad.
- [x] **Q2 → A**: `runs_per_cell = 5` candidates × 15 cells = 75 simulations × ~$0.07/sim = **~$5.40 generation budget**. Sweet spot variance vs cost.
- [x] **Q3 → B**: Curation tooling = **Markdown table inline** (`preview.md` IDE-renderable). NO HTML, NO Streamlit. Zero browser dep, parallel-safe, terminal-friendly.
- [x] **Q4 → A**: Coverage gate = **≥ 1 golden per cell** (15 minimum). Compatible 20 goldens total minimum. Maintenance liviano.
- [x] **Q5 → A**: `expected_voice_attributes` = **auto-extract subset** de `personality_profile.system_instruction` keys (Story A) per `dialect_code` + Chris override en `notes` freeform. Hybrid: máquina hace grunt work, Chris añade judgment.
- [x] **Q6 → A**: Refresh policy = **manual trigger only** (Chris decides). README documenta triggers (Story C schema bump, grader saturate >0.95, 6-month review). Zero auto-drift.
- [x] **Q7 → A**: `metadata.notes` = **freeform string** Chris writes ("why this won curation"). Audit trail rico, no constraint inicial.
- [x] **Q8 → A**: Generation = **NO CI generation** (cost prohibitive — manual trigger only). CI valida schema + coverage + PII solamente. Zero CI cost balance.

## Próximo paso

Service-story → `/po` ratifica con Chris (loop iterativo) → spec ratificada → transition `state: refining → refined` → `/architect` orchestrator spawna `/architect-be` (script + schema + scanner + pre-commit hook + capability extension) → produce ready package (03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml) → `/dev-team` autonomous build (depends_on Story C build complete primero — bloqueador hard).

> **Build order ack:** Story C build MUST complete antes Story D build (Story D consume `load_actor_profile_for_tenant` runtime). Story C state=refined awaiting `/architect` package. Story D refinement ahora paralela; Story D build espera Story C build done.

## Changelog

- v1 2026-05-06 — `/po` draft (production-extraction paradigm). Archivado en commit `f7624c9f`. Superseded.
- v2 2026-05-08T06:30Z — `/po` reframe synthetic-first. Consume Story A (5 tenant seeds + dialect_catalog) + Story B (`run_simulation` API + cost-bucket tables) + Story C (15 archetype-aware personas + persona_kind v2 6-val). Coverage matrix 20-30 goldens (5 tenants × 3 kinds × 1-2 winners). Pipeline 2 fases: script generation + Chris preview curation + `promote_golden` CLI. Schema `GoldenScenarioModel` v1 cement con SCHEMA_MIGRATIONS forward-compat. PII defense-in-depth scanner. 17 decisiones cardinales D1-D17. 8 open questions Q1-Q8 awaiting Chris ratification.
- v3 2026-05-08T07:00Z — Chris ratificó Q1-Q8 (todas opción A — recomendada except Q3=B Markdown). Ajustes inline: D12 cement `preview.md` Markdown inline (NO HTML/Streamlit) + D14 `expected_voice_attributes` auto-extract de `personality_profile` + Chris `notes` override. Scenario 1 actualizado preview format. `ratified_by_chris: true`. Próximo: transition `state: refining → refined` → `/architect` orchestrator → ready package.
