---
story_id: sales-agent-goldens-3-tenants-dataset
type: service-story
module: sales_agent
capability: sales-conversational-engine
po_version: 1
last_modified: 2026-05-06T16:00:00Z
ratified_by_chris: false
links:
  story_md: "00-story.md"
  outcome: "../../outcomes/pi-12-sales-agent-eval-foundation.md"
  capability_yaml: "../../capabilities/sales-agent/sales-conversational-engine.yaml"
  module_doc: "../../modules/sales-agent.md"
  consumers:
    - "docs/archive/2026/stories/sales-agent-eval-runner-foundation/"  # runner consumes goldens
---

## Resumen ejecutivo

Se construye el ground-truth dataset del eval suite de `sales_agent`: **12 conversaciones golden curadas** (3 tenants × 4 escenarios cada uno), extraídas de tablas live `sales_agent_session` mediante un agent-helper, anonimizadas con `sanitize_payload` (shared), y ratificadas manualmente por Chris. Se entrega como árbol de archivos YAML checked-in bajo `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/` + README + Pydantic schema validator + pre-commit hook PII scanner. Outcome: las stories 6-9 de PI-12 (personas runtime, voice fidelity grader, CI gate, adversarial suite) pueden anclar sus assertions a casos reales en lugar de mocks sintéticos.

## Acceptance Criteria (Gherkin AI-resistant)

### Scenario 1 — `goldens-curation-happy-path` (`type: happy`)

**Given:**
- Existe el script `backend/scripts/extract_golden_candidates.py` que lee `sales_agent_session` filtrando por `tenant_id` (3 tenants ratificados por Chris en open questions Q1)
- Existe el modelo Pydantic `GoldenScenarioModel` en `backend/tests/agentic_evals/sales_agent/goldens/_schema.py` con campos: `id`, `tenant_slug`, `tenant_industry`, `scenario_type ∈ {lead_frio, lead_tibio, lead_caliente, objecion_refutacion}`, `input`, `tenant_context`, `expected_behavior`, `expected_voice_attributes`, `forbidden_outputs`
- Para cada uno de los 3 tenants existen ≥ 100 sesiones en BD con transcripts completos

**When:**
- Dev ejecuta `python backend/scripts/extract_golden_candidates.py --tenant <slug> --scenario <type> --top 5` para cada combinación tenant×scenario (12 invocaciones)
- Chris elige 1 candidato por combinación (12 finales) y commitea los archivos a `backend/tests/agentic_evals/sales_agent/goldens/{tenant_slug}/{scenario_type}.yaml`

**Then:**
- Existen exactamente 12 archivos YAML válidos contra `GoldenScenarioModel` (4 por tenant)
- `pytest backend/tests/agentic_evals/sales_agent/test_goldens_schema.py -v` pasa 12 assertions (1 por golden) — cada YAML loadea, valida, y `expected_voice_attributes` es subset no vacío de campos en `personality_profile` del tenant
- Existe `backend/tests/agentic_evals/sales_agent/goldens/README.md` con secciones: "Criterios de selección", "Cómo agregar un golden nuevo" (template + checklist 6 ítems), "Política de actualización" (cuándo refrescar, quién aprueba)
- Runner de Story `sales-agent-eval-runner-foundation` (already done) puede importar los 12 goldens sin error: `pytest backend/tests/agentic_evals/sales_agent/test_runner_loads_goldens.py -v` GREEN
- Capability `sales-conversational-engine.yaml` campo `eval.goldens_dataset_path` apunta a `backend/tests/agentic_evals/sales_agent/goldens/`

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_schema.py" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_runner_loads_goldens.py" }`
- `{ type: state_check, target: filesystem, query: "find backend/tests/agentic_evals/sales_agent/goldens -name '*.yaml' | wc -l == 12" }`
- `{ type: state_check, target: filesystem, query: "test -f backend/tests/agentic_evals/sales_agent/goldens/README.md" }`

---

### Scenario 2 — `golden-yaml-schema-invalid` (`type: negative`)

**Given:**
- Existen los 12 goldens válidos del scenario 1
- Dev intenta crear un golden #13 con campo faltante (omite `expected_behavior`) o tipo incorrecto (`scenario_type: lead_random`)

**When:**
- Dev ejecuta `git add backend/tests/agentic_evals/sales_agent/goldens/{slug}/golden_invalid.yaml && git commit`

**Then:**
- Pre-commit hook ejecuta `pytest backend/tests/agentic_evals/sales_agent/test_goldens_schema.py -v` y falla con `pydantic.ValidationError` citando el campo faltante o el enum violation
- Commit es **bloqueado** (exit code ≠ 0)
- Estado del filesystem queda igual (golden inválido NO entra a HEAD)
- Mensaje de error indica path exacto del archivo + campo violador (zero ambigüedad para el dev)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_schema.py", expect_fail_on: "missing_field|invalid_enum" }`
- `{ type: state_check, target: pre_commit_hook, expect: "exit_code != 0 AND stderr contains 'ValidationError'" }`

---

### Scenario 3 — `tenant-pool-insuficiente` (`type: edge`)

**Given:**
- Uno de los 3 tenants ratificados (ej. e-com nicho) tiene en BD < 20 sesiones con transcripts completos para `scenario_type = objecion_refutacion`
- El script `extract_golden_candidates.py` detecta el pool insuficiente

**When:**
- Dev ejecuta `python backend/scripts/extract_golden_candidates.py --tenant <slug> --scenario objecion_refutacion --top 5`

**Then:**
- Script emite `structlog` warning: `"insufficient_pool"` con campos `tenant_slug`, `scenario_type`, `pool_size`, `min_required=20` (umbral configurable en CLI)
- Script retorna exit code `2` (distinguible de éxito 0 y error 1)
- Script imprime tabla con candidatos disponibles + nota: "Decision required: (a) ratify with N candidates, (b) swap tenant, (c) supplement with synthetic — see README § Política de actualización"
- NO se crea el golden YAML automáticamente (Chris decide acción)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_extract_script.py::test_insufficient_pool_returns_exit_2" }`
- `{ type: state_check, target: stdout, query: "exit_code == 2 AND log contains 'insufficient_pool'" }`

---

### Scenario 4 — `pii-leak-blocked` (`type: adversarial`)

> AI-resistant: prevenir leak en repo público (GitHub) de email/teléfono/DNI/URL interna real no anonimizada.

**Given:**
- Atacante interno (dev distraído o malicioso) intenta commit golden YAML con PII real visible en `input` o `tenant_context.transcript_excerpt`:
  - Email: `juan.perez@empresacliente.com`
  - Teléfono: `+54 9 11 5555-1234`
  - DNI: `38.456.789`
  - URL interna: `https://admin-internal.nicolify.com/tenant/uuid-real/...`

**When:**
- Dev ejecuta `git add ... && git commit`

**Then:**
- Pre-commit hook nuevo `scripts/git-hooks/pre-commit` Section 7 (a agregar) ejecuta `python backend/scripts/scan_goldens_pii.py backend/tests/agentic_evals/sales_agent/goldens/`
- Scanner detecta los 4 patrones (regex email RFC 5322, regex teléfono LatAm + intl, regex DNI/CUIT/RUT, regex URL `*.nicolify.com` no whitelisted)
- Hook **bloquea commit** con mensaje: `"PII detected in goldens/{path}:{line}: {redacted_pattern_type}"`
- Log entry en `docs/process/learnings.md` (manual por Chris si reincide) — NO automático
- Test `backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py` provee 4 fixtures (1 por categoría PII) y verifica que cada uno es detectado por separado
- Adicional: cada golden checked-in tiene assertion en `test_goldens_schema.py::test_no_pii_in_committed_goldens` que re-corre el scanner sobre los 12 reales (defense in depth)

**Graders:**
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_pii_scanner.py", expect: "4 PII categories detected on adversarial fixtures" }`
- `{ type: contract_test, path: "backend/tests/agentic_evals/sales_agent/test_goldens_schema.py::test_no_pii_in_committed_goldens", expect: "0 matches on real 12 goldens" }`
- `{ type: state_check, target: pre_commit_hook, expect: "exit_code != 0 AND stderr matches 'PII detected'" }`
- `{ type: integration, path: "backend/tests/scripts/test_pre_commit_hook.py::test_blocks_pii_in_goldens" }`

---

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| PII | Cero patrones email/teléfono/DNI/URL-interna en `backend/tests/agentic_evals/sales_agent/goldens/` | `scan_goldens_pii.py` + arch test + pre-commit hook |
| Tenant isolation | Cada golden contiene SOLO datos de un único `tenant_slug`. Cross-tenant data en mismo YAML → schema fail | `GoldenScenarioModel` validator field |
| i18n | `input` puede contener voseo (refleja conversación real tenant AR). `expected_voice_attributes` respeta voz tenant. README en español neutro | Excepción explícita rule R2 — voseo permitido en `input` field, prohibido en README |
| Spanish neutro | README + `forbidden_outputs` (cuando aplica español neutro) sin voseo | Pre-commit hook scripts/git-hooks/pre-commit Section 5 voseo scan (con `<!-- voseo-allowed -->` magic comment en YAML transcripts si aplica voz tenant) |
| Determinismo | Mismo input + mismo tenant_context → mismo `expected_behavior` (no random) | Schema enforces — ningún campo `random_seed` |
| Reproducibilidad | Re-ejecutar `extract_golden_candidates.py` con mismo `--seed N` da mismas 5 top candidates | CLI flag `--seed` + sort estable por `session_id` |
| Versioning | Cada golden tiene `id` único + `created_at` + `extracted_from_session_uuid` (post-anonymization no expone uuid completo, hash sha256[:8]) | Schema field |

## Constraints técnicos heredados

- `.claude/rules/backend-ddd.md` — script bajo `backend/scripts/`, tests bajo `backend/tests/`. NO tocar `modules/sales_agent/{domain,application,api}/` (data asset puro)
- `.claude/rules/tenant-isolation.md` — query DB filtra `tenant_id` siempre, incluso para extracción de candidatos
- `.claude/rules/anti-duplication.md` — usar `shared/agent_observability/recording/sanitization.py::sanitize_payload`. NO crear sanitizer local
- `.claude/rules/spanish-text.md` § excepción sales_agent — voseo permitido en `input` field si tenant es AR; el resto del texto user-facing (README, mensajes CLI, error strings) es español neutro
- `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` — patrones PII canónicos (email/phone/SSN/address/DOB/IP/financial). El scanner extiende con DNI/CUIT/RUT LatAm + URLs internas
- `.claude/rules/parallel-safety.md` — extracción es read-only sobre `sales_agent_session`, parallel-safe entre sesiones distintas

## Cross-module impact

- **Lee de:** `sales_agent_session` (DB table — read-only, infra `modules/sales_agent/persistence/`)
- **Lee de:** `personality_profiles` (para `expected_voice_attributes`)
- **Es leído por:** `backend/tests/agentic_evals/sales_agent/runner.py` (story `sales-agent-eval-runner-foundation` already done)
- **Es leído por:** Stories futuras PI-12 (`personas-instrumented-runtime`, `voice-fidelity-grader-runtime`, `voice-fidelity-ci-gate`, `eval-pass-k-tracking`, `adversarial-jailbreak-suite`)
- **Eventos emitidos:** ninguno (data asset, no runtime)
- **Eventos consumidos:** ninguno

## Open questions (para resolver con Chris ANTES de pasar a /architect)

- [ ] **Q1 — Selección 3 tenants representativos:** ¿qué 3 tenant_slugs concretos? Sugerencia mínima diversificada: 1 coach (probable AR voseo), 1 consultor B2B (probable LatAm neutro), 1 e-com nicho. Confirmar slugs reales de prod.
- [ ] **Q2 — Tabla origen:** ¿es `sales_agent_session` o tiene otro nombre en BD actual? ¿Schema actual incluye campo `transcript: jsonb` o transcripts viven en tabla separada (`sales_agent_message`)?
- [ ] **Q3 — Pool mínimo aceptable:** umbral default propuesto `min_required = 20` sesiones por tenant×scenario. ¿OK o querés `100` (alineado con asunción de 00-story.md)?
- [ ] **Q4 — Sanitization scope extra:** además de los 7 patrones PII canónicos del Tessl rule, ¿agregamos DNI argentino (`XX.XXX.XXX`), CUIT (`XX-XXXXXXXX-X`), RUT chileno, RFC mexicano, URLs internas `*.nicolify.com` no whitelisted? Propongo sí.
- [ ] **Q5 — Pre-commit hook scope:** ¿el scanner PII solo corre sobre `backend/tests/agentic_evals/sales_agent/goldens/` o sobre todo `backend/tests/agentic_evals/`? Propongo solo sales_agent/goldens (scope quirúrgico, evita falsos positivos en docs/fixtures de otros agents).
- [ ] **Q6 — Schema YAML format:** ¿Pydantic v2 model SSoT (cargado por Python para validación) y opcionalmente exporta JSON Schema para IDE autocomplete? Propongo Pydantic SSoT, JSON Schema autogenerado en CI.
- [ ] **Q7 — README "agregar golden nuevo":** ¿template auto-generable (`make new-golden TENANT=x SCENARIO=y` que crea YAML stub validado) o doc manual con ejemplo? Propongo make target (escribible en backlog si scope crece).
- [ ] **Q8 — Política de actualización dataset:** ¿cuándo se refresca? Propuesta: trigger cuando (a) voice fidelity grader saturate >0.95 average (señal de overfitting), (b) cambio mayor en `personality_profiles` schema, (c) cada 6 meses revisión calendarizada.
- [ ] **Q9 — Anonymization de tenant identity en goldens:** ¿`tenant_slug` en YAML es el slug real (ej. `coachjuan-mx`) o un alias estable (`tenant_a`, `tenant_b`, `tenant_c`)? Trade-off: real → debugging más fácil, alias → cero leak si repo se vuelve público. Propongo **alias estable** + tabla privada en `.env.eval` con mapping (no checked-in).
- [ ] **Q10 — Estimate split (5d total):** ¿confirmás división aproximada (a) 1d schema + script + tests, (b) 1d sanitization + PII scanner + pre-commit hook, (c) 2d extracción agent-helper + curación Chris, (d) 1d README + integración runner + capability update? Si Chris dispone <2h curación → bumpear a 6d o partir story.

## Próximo paso

`type=service-story` → ratificación Chris de las 10 open questions (especialmente Q1, Q2, Q9 que bloquean el architect) → bump `po_version: 2` con respuestas inline → transition `state=refining → refined` → `/architect` produce ready package (03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml).

## Changelog

- v1 2026-05-06 — `/po` draft inicial. 4 scenarios (happy/negative/edge/adversarial) + 10 open questions críticas para ratificación.
