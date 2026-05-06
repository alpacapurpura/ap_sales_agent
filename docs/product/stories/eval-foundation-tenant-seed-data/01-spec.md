---
story_id: eval-foundation-tenant-seed-data
type: service-story
subtype: data-seeding
module: sales_agent
capability: sales-conversational-engine
po_version: 2
last_modified: 2026-05-06T20:55Z
ratified_by_chris: true
links:
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  pre_requisite: ../maintenance-skill-sales-agent-audit/checkpoint.md
  related_new_story: ../sales-agent-dialect-configuration/        # spawned 2026-05-06 from Q7
  consumers:
    - ../eval-foundation-simulator-homologation/
    - ../sales-agent-personas-instrumented-runtime/
    - ../sales-agent-goldens-3-tenants-dataset/
    - ../sales-agent-voice-fidelity-grader-runtime/
    - ../sales-agent-eval-pass-k-tracking/
    - ../sales-agent-eval-cost-budget-cap/
    - ../sales-agent-voice-fidelity-ci-gate/
    - ../sales-agent-adversarial-jailbreak-suite/
  related_rules:
    - ../../../../.claude/rules/spanish-text.md
    - ../../../../.claude/rules/sales-agent-brand-voice.md
    - ../../../../.claude/rules/anti-duplication.md
    - ../../../../.claude/rules/tenant-isolation.md
    - ../../../../.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md
---

## Resumen ejecutivo

Crear **5 tenants seed sintéticos** checked-in (A1 Coach LatAm humano · A2 Medicina estética · A3 Clínica dental · A4 Growth Marketing video+RRSS · A5 Agencia Automatización IA + Software no-vibe-code) en `backend/tests/fixtures/eval/tenants/{archetype_slug}/`, cada uno con 6 archivos YAML + README cubriendo la data mínima que el `sales_agent` runtime necesita para correr SIN MOCKS: brand identity + personality_profile (system_instruction compiler v2 + nuevo campo `dialect_code` BCP-47) + offer_ladder + pricing + buyer_personas + communication_assets. Loader function `load_eval_tenant(archetype_slug) → TenantContext` mergea los YAMLs y produce objeto in-memory consumible por el agente. Tests aseguran (a) los 5 tenants cargan sin error, (b) schemas validan contra Pydantic models existentes (drift detection), (c) cada tenant tiene mínimo 5 campos no-null por YAML, (d) cero PII real (defense in depth), (e) `dialect_code` válido contra catálogo BCP-47.

**Outcome verificable:** ejecutando `pytest backend/tests/fixtures/eval/tenants/ -v` el suite pasa GREEN; cualquier consumer downstream (simulator, personas, goldens, graders) puede llamar `load_eval_tenant(archetype_slug)` con uno de los 5 slugs ratificados y recibir un TenantContext válido sin tocar BD real.

Esta story es **blocker absoluto** del resto de la sub-épica `eval-foundation-*`. Sin ella, las 8 stories siguientes son inalcanzables.

## Tabla de archetypes seed (ratificada Chris 2026-05-06 v2)

| Slug | Archetype | Especialidad | Currency | dialect_code BCP-47 | Voseo | Inspiración real (REF) |
|---|---|---|---|---|---|---|
| `tenant_coach_lat` | A1 Coach LatAm humano | Comunidad + transformación, multi-product offer ladder | PEN | `es-PE` | No | https://visionarias.lat |
| `tenant_medicina_estetica` | A2 Medicina estética | Clínica/profesional con personal brand IG, dermatología estética + tratamientos faciales/corporales | PEN | `es-MX` | No | dr.cardiometabolico, dra.andreacuya, dr.wagnerwilliams (refs aggregate, no copy) |
| `tenant_clinica_dental` | A3 Clínica dental | Consultorio dental personal brand, ortodoncia + estética dental + recurrencia (control anual) | PEN | `es-CO` | Parcial (bogotano tuteo) | dentalindo, refs aggregate |
| `tenant_agencia_growth_video` | A4 Growth Marketing video+RRSS | Agencia growth marketing especializada en producción de video + estrategia RRSS para escalar ventas via marketing digital | PEN | `es-AR` | Sí | toga.pe, brander.studio (refs aggregate) |
| `tenant_agencia_automatizacion_ia` | A5 Agencia Automatización IA + Software con IA | Agencia desarrollo software con IA (NO vibe-code) + automatización procesos enterprise via agentes IA | PEN | `es-419` (neutro LatAm) | No | brandtech.pe (refs aggregate, vertical tech enterprise) |

**Nota tradeoff currency vs dialect:** los 5 tenants tienen `currency: PEN` pero dialectos de países distintos (PE/MX/CO/AR/419). Esto es **synthetic test data** — no refleja realidad económica. Decisión Chris ratificada (Q3): test isolation > realismo perfecto. Stories downstream que prueben multi-currency mix son responsabilidad propia (no esta story).

**Q7 relación con story nueva:** el campo `dialect_code` introducido en `personality_profile.yaml` es la primera materialización del concepto que la story `sales-agent-dialect-configuration` formalizará como UI tenant config + runtime prompt injection. Esta story produce el DATA; la otra produce el FEATURE UX. Path: `docs/product/stories/sales-agent-dialect-configuration/00-story.md` (state=idea, placeholder).

## Acceptance Criteria (Gherkin AI-resistant)

> 4 scenarios mínimos. Cada uno tiene grader explícito + path concreto. **Service-story:** sin UI, sin agentic conversational flow.

### Scenario 1 — `seed-tenants-checked-in-and-loadable` (`type: happy`)

**Given:**
- Path `backend/tests/fixtures/eval/tenants/` existe con 5 subfolders: `tenant_coach_lat/`, `tenant_medicina_estetica/`, `tenant_clinica_dental/`, `tenant_agencia_growth_video/`, `tenant_agencia_automatizacion_ia/`
- Cada subfolder contiene 7 archivos: `brand.yaml`, `personality_profile.yaml`, `offer_ladder.yaml`, `pricing.yaml`, `buyer_personas.yaml`, `communication_assets.yaml`, `README.md`
- Existe `backend/tests/fixtures/eval/tenants/loader.py` con función `load_eval_tenant(archetype_slug: Literal["tenant_coach_lat", "tenant_medicina_estetica", "tenant_clinica_dental", "tenant_agencia_growth_video", "tenant_agencia_automatizacion_ia"]) → TenantContext`
- Existe `backend/tests/fixtures/eval/tenants/dialect_catalog.yaml` con ≥13 entradas BCP-47 (es-419 + es-AR + es-UY + es-CL + es-MX + es-PE + es-CO + es-VE + es-EC + es-PY + es-CR + es-DO + es-CU + es-PR + es-ES). Cada entrada: `code`, `display_name`, `voseo` (`true|false|"parcial"`), `country_code`, `description`
- Pydantic models referenciados existen e importables desde `backend/src/modules/{brand,offer}/domain/`

**When:**
- Dev/CI ejecuta `cd backend && .venv/bin/pytest tests/fixtures/eval/tenants/ -v`

**Then:**
- `test_loader.py::test_loads_all_5_archetype_slugs[archetype_slug]` GREEN parametrizado por slug — loader retorna TenantContext sin raise para los 5
- Per tenant assertions:
  - `tenant.brand.identity.name` no vacío
  - `tenant.personality_profile.system_instruction` ≥ 100 chars (compiler v2 produce string sustancial)
  - `tenant.personality_profile.dialect_code` ∈ `{"es-PE", "es-MX", "es-CO", "es-AR", "es-419"}` (matchea la tabla archetypes)
  - `tenant.personality_profile.dialect_code` válido contra `dialect_catalog.yaml`
  - `len(tenant.offer_ladder.offers) >= 4` (lead magnet opcional — ver scenario 3)
  - `tenant.pricing.currency == "PEN"`
  - `len(tenant.buyer_personas) == 3` (2 base + 1 adversarial-edge per ratificación Q8)
- `test_realism_smoke.py::test_each_yaml_has_min_5_non_null_fields[archetype_slug-yaml_filename]` GREEN para los **30 combinaciones** (5 tenants × 6 YAMLs)
- `test_schema_alignment.py::test_brand_yaml_validates_against_pydantic_model` GREEN para los 5 tenants
- `test_schema_alignment.py::test_offer_ladder_yaml_validates_against_pydantic_model` GREEN para los 5 tenants
- `test_schema_alignment.py::test_personality_profile_yaml_validates_against_pydantic_model` GREEN para los 5 tenants
- `test_dialect_catalog.py::test_catalog_contains_all_archetype_dialects` GREEN — cada `dialect_code` usado en los 5 tenants existe en el catálogo
- Capability `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` agrega campo `eval.seed_tenants_path: "backend/tests/fixtures/eval/tenants/"` + `eval.seed_archetype_slugs: [tenant_coach_lat, tenant_medicina_estetica, tenant_clinica_dental, tenant_agencia_growth_video, tenant_agencia_automatizacion_ia]`

**Graders:**
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_loader.py`
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_realism_smoke.py`
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_schema_alignment.py`
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_dialect_catalog.py`
- `state_check` — target: filesystem; query: `find backend/tests/fixtures/eval/tenants -name '*.yaml' -path '*/tenant_*' | wc -l == 30` (5 × 6 YAMLs)
- `state_check` — target: filesystem; query: `find backend/tests/fixtures/eval/tenants -name 'README.md' | wc -l == 5`
- `state_check` — target: filesystem; query: `test -f backend/tests/fixtures/eval/tenants/dialect_catalog.yaml`
- `state_check` — target: capability YAML; query: `grep -q 'seed_tenants_path' docs/product/capabilities/sales-agent/sales-conversational-engine.yaml`

---

### Scenario 2 — `yaml-required-field-missing` (`type: negative`)

**Given:**
- Tenant seed YAML existente tiene campo requerido **omitido** (e.g., `tenant_coach_lat/personality_profile.yaml` sin `system_instruction`, o sin `dialect_code`)
- O tipo incorrecto (e.g., `pricing.yaml` con `currency: "DOLLARS"`, o `personality_profile.yaml` con `dialect_code: "es-XX-INVALID"` no presente en catálogo)

**When:**
- Dev/CI ejecuta `cd backend && .venv/bin/pytest tests/fixtures/eval/tenants/test_schema_alignment.py -v` (o `test_dialect_catalog.py` para el caso dialect_code)

**Then:**
- Test falla con `pydantic.ValidationError` (para schemas Pydantic) o assertion error custom (para `dialect_code` no en catálogo) citando archivo + campo faltante
- Mensaje incluye archetype_slug + filename del YAML inválido + nombre exacto del campo faltante/inválido (ej. `tenant_coach_lat/personality_profile.yaml: field 'system_instruction' is required`, o `tenant_clinica_dental/personality_profile.yaml: dialect_code='es-XX-INVALID' not in dialect_catalog.yaml`)
- Estado del filesystem queda igual (test es read-only)
- Pre-commit hook (cuando se commitea el YAML inválido) bloquea con mismo mensaje (defense in depth — pre-commit invoca `pytest --collect-only -q` sobre los nuevos YAMLs)

**Graders:**
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_schema_alignment.py::test_loader_raises_on_missing_required_field` (positive control con fixture sintética que omite campo)
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_dialect_catalog.py::test_invalid_dialect_code_raises` (positive control con tenant fixture con dialect_code no válido)
- `state_check` — target: stdout pytest; query: "test name + file path + field name están presentes en stderr"

---

### Scenario 3 — `offer-ladder-missing-l0-lead-magnet` (`type: edge`)

**Given:**
- Tenant seed YAML `offer_ladder.yaml` carga 4 offers (L1..L4) **sin L0 lead magnet** — caso real esperado: A4 (Growth Marketing video+RRSS) y A5 (Agencia Automatización IA) probablemente NO tienen lead magnet gratuito (entran por casos de éxito + discovery call)
- Política ratificada Chris (Q6): warning structlog + load proceed; el loader emite `"offer_ladder_missing_lead_magnet"` con `tenant_slug` + `missing_levels: ["L0"]`, pero CONTINÚA load
- Campo computed `has_lead_magnet: bool` en TenantContext, derivado del offer_ladder

**When:**
- Dev/CI ejecuta loader sobre los 5 tenants

**Then:**
- Loader retorna TenantContext válido para los 5 (NO raise)
- Para los tenants sin L0 (esperado: A4 y A5), structlog emite warning con level `warning`, payload `{tenant_slug, offer_count, missing_levels: ["L0"], has_lead_magnet: false}`
- Test `test_loader.py::test_offer_ladder_no_lead_magnet_emits_warning_proceeds_load` GREEN — captura warning via `caplog` o structlog testing fixture, asserta level=warning + tenant_slug presente + has_lead_magnet=false
- Para los tenants CON L0 (esperado: A1 + A2 + A3), `has_lead_magnet=true` y NO se emite warning
- Consumers downstream (simulator, personas) pueden inspeccionar `tenant.offer_ladder.has_lead_magnet` para skipear preguntas tipo "¿Empezarías con el PDF gratis?"

**Graders:**
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_loader.py::test_offer_ladder_no_lead_magnet_emits_warning_proceeds_load`
- `state_check` — target: structlog capture; query: "warning event 'offer_ladder_missing_lead_magnet' emitted with tenant_slug + missing_levels=['L0'] for A4 and A5"

---

### Scenario 4 — `pii-real-detected-in-seed-yaml` (`type: adversarial`)

> AI-resistant: defense in depth bloquea PII real (email/teléfono/DNI/URL interna no whitelisted) que pudiera llegar accidentalmente al YAML por copy-paste descuidado durante curación.

**Given:**
- Atacante interno (dev distraído, builder LLM con copy-paste agresivo, curación Chris con paste de transcript real) intenta commit YAML con PII real visible:
  - Email real: `juan.perez@gmail.com`
  - Teléfono real: `+51 999 555 1234` (PE), `+52 55 1234 5678` (MX), `+57 320 555 1234` (CO), `+54 9 11 5555 1234` (AR)
  - DNI/CUIT/RUT/CURP/RFC: `38.456.789` (AR), `12345678-9` (CL), `12345678` (PE), `RFXX771013JE2` (MX), `1234567890` (CO)
  - URL interna: `https://admin.nicolify.com/tenant/uuid-real/...` no presente en `.eval-whitelist`

**When:**
- Dev ejecuta `git add backend/tests/fixtures/eval/tenants/...yaml && git commit`

**Then:**
- Pre-commit hook nuevo `scripts/git-hooks/pre-commit` Section 7 (a agregar) ejecuta `python backend/scripts/scan_seed_pii.py backend/tests/fixtures/eval/tenants/`
- Scanner detecta los 4 patrones (regex email RFC 5322, regex teléfono LatAm + intl, regex DNI/CUIT/RUT/CURP/RFC, regex URL `*.nicolify.com` no whitelisted)
- Hook **bloquea commit** con mensaje: `"PII detected in seed/{path}:{line}: {redacted_pattern_type} — sanitiza con sintético equivalente o agrega a backend/tests/fixtures/eval/tenants/.eval-whitelist con justificación"`
- Test `test_seed_pii_scanner.py::test_4_categories_detected_on_adversarial_fixtures` GREEN — provee 4 fixtures (1 por categoría PII) y verifica detección por separado
- Test `test_seed_pii_scanner.py::test_no_pii_in_committed_seeds` GREEN — re-corre scanner sobre los 30 YAMLs reales committed (defense in depth post-commit)
- `personality_profile.yaml::sample_exchanges` PUEDE contener teléfonos/emails sintéticos con prefix `+99 0 ...` o domain `@example.com` — el scanner los whitelistea explicit (no falsos positivos)

**Graders:**
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_4_categories_detected_on_adversarial_fixtures`
- `contract_test` — path: `backend/tests/fixtures/eval/tenants/test_seed_pii_scanner.py::test_no_pii_in_committed_seeds`
- `state_check` — target: pre_commit_hook; query: "exit_code != 0 AND stderr contains 'PII detected in seed/'"
- `integration` — path: `backend/tests/scripts/test_pre_commit_hook.py::test_blocks_pii_in_seed_tenants` (extender el test existente del hook)

---

## Non-functional requirements

| Categoría | Requisito | Verificador |
|---|---|---|
| Tiempo build | Story completable en ≤7d (1d schema+loader+tests baseline · 2d drafts iniciales 5 YAMLs por archetype + scanner PII + pre-commit hook · 1d catálogo dialectos como YAML referenciable · 1-3d curación Chris + ratificación + ajustes finales) | story estimate vs git log |
| Determinismo carga | `load_eval_tenant(slug)` retorna idéntico TenantContext en N llamadas | `pytest --count=3` |
| Sin runtime impact | 0 cambios en `backend/src/modules/sales_agent/{domain,application,api}/` ni `frontend/src/` | `git diff --stat` muestra 0 bytes en src/sales_agent runtime + frontend |
| Sin BD seed | Loader produce TenantContext in-memory únicamente (Q4 ratificado) | grep no `INSERT INTO`, no `session.add` en loader.py |
| Tenant isolation | Cada subfolder contiene SOLO data de un único archetype. Cross-archetype data en mismo YAML → schema fail | schema validator + arch test |
| PII | Cero patrones PII real en `backend/tests/fixtures/eval/tenants/` | `scan_seed_pii.py` + arch test + pre-commit hook |
| Spanish neutro | README per-tenant + mensajes scanner CLI en español neutro. `personality_profile.yaml::sample_exchanges` respeta dialecto del tenant (voseo si AR, tuteo si PE/MX/CO/CL/EC, parcial si CL) | pre-commit hook voseo scan + magic comment `<!-- voseo-allowed -->` cuando aplica (tenants AR + CO paisa + CL parcial) |
| Realismo mínimo | Cada YAML tiene ≥5 campos no-null (excluye `id`, `created_at`, `updated_at`) | `test_realism_smoke.py` |
| Schema drift detection | Tests en CI fallan rápido si Pydantic models cambian post-merge invalidando seed YAMLs | `test_schema_alignment.py` |
| References reales documentadas | README per-tenant cita URL real (e.g., visionarias.lat) en sección "Inspiración" — pero data NO es scrap real | grep README contiene "Inspiración" + URL |
| Verificación URLs | Solo regex schema valid (no HTTP 200 check) — escalable 1000+ tenants per Q9 | regex validator en `communication_assets.yaml` schema |
| Dialect catalog completeness | Catálogo BCP-47 contiene ≥13 entradas; los 5 tenants seed usan dialectos distintos (es-PE, es-MX, es-CO, es-AR, es-419) para diversidad de testing voice fidelity downstream | `test_dialect_catalog.py` |

## Constraints técnicos heredados

- `.claude/rules/anti-duplication.md` — usar `shared/agent_observability/recording/sanitization.py::sanitize_payload` si necesitamos sanitizer en runtime; el `scan_seed_pii.py` es read-only check, NO duplica sanitization
- `.claude/rules/spanish-text.md` § excepción sales_agent — voseo permitido en `personality_profile.yaml::sample_exchanges` cuando `dialect_code in ["es-AR", "es-UY", "es-PY"]` (voseo full) o `dialect_code in ["es-CL", "es-CR"]` (voseo parcial). Voseo PROHIBIDO cuando `dialect_code in ["es-PE", "es-MX", "es-CO" (bogotano), "es-VE", "es-EC", "es-419"]`. README de seed en español neutro siempre.
- `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` — patrones PII canónicos (email/phone/SSN/address/DOB/IP/financial). Scanner extiende con DNI/CUIT/RUT LatAm + CURP/RFC mexicanos + URLs internas
- `.claude/rules/parallel-safety.md` — story corre en `development`, archivos del seed son de esta sesión
- `.claude/rules/tdd-mandatory.md` — RED → GREEN: tests escritos primero (fixtures sintéticas con campos faltantes/PII), después YAMLs reales hasta GREEN
- `.claude/rules/backend-ddd.md` — fixtures bajo `backend/tests/fixtures/`, NO bajo `backend/src/`. Loader puro funcional, sin DI ni servicios
- Native-first WSL: tests corren `cd backend && .venv/bin/pytest tests/fixtures/eval/tenants/ -v` (no Docker)

## Cross-module impact

- **Lee de:** Pydantic models existentes (`backend/src/modules/brand/domain/`, `backend/src/modules/offer/domain/`, sales_agent personality compiler v2 existente)
- **Es leído por:** los 8 stories restantes de la sub-épica `eval-foundation-*` (ver tabla links.consumers)
- **Eventos emitidos:** ninguno (data asset, no runtime)
- **Eventos consumidos:** ninguno
- **Spawned-from-this-story:** `sales-agent-dialect-configuration` (placeholder, state=idea, refinement post Q7) — esta story introduce el campo `dialect_code` como data; la otra formaliza la feature UX tenant config + runtime
- **Arch tests potencialmente afectados:** `tests/architecture/` no se modifica; story es additive en `tests/fixtures/`

## Decisions ratified (Chris 2026-05-06 v2)

- [x] **Q1 — A2/A3 separación a 2 tenants médicos:** A2 = Medicina estética, A3 = Clínica dental
- [x] **Q2 — A4/A5 separación a 2 tenants agencia:** A4 = Growth Marketing video+RRSS, A5 = Agencia Automatización IA + Software con IA (NO vibe-code)
- [x] **Q3 — Currency PEN para los 5** (test isolation > realismo perfecto; tradeoff dialect-mixed-currency aceptado)
- [x] **Q4 — Loader: solo in-memory** (BD seed = story futura `eval-foundation-tenant-seed-db-bridge` si requerida)
- [x] **Q5 — Scanner PII: solo `backend/tests/fixtures/eval/tenants/`** (scope quirúrgico)
- [x] **Q6 — Edge L0 sin lead magnet: warning + proceed** + campo computed `has_lead_magnet: bool`. Aplicará a A4 + A5 esperadamente.
- [x] **Q7 — Dialect catalog BCP-47 + dialect_code field**:
  - Story aparte `sales-agent-dialect-configuration` creada como placeholder (state=idea) para feature UX tenant config + runtime — refinement futuro
  - Esta story produce DATA (campo + catálogo); la otra produce FEATURE
  - Migration default cuando feature exista: todos tenants existentes → `dialect_code = 'es-419'`
  - Dialect picks per archetype: A1=es-PE, A2=es-MX, A3=es-CO, A4=es-AR, A5=es-419
- [x] **Q8 — Buyer personas: 2 base + 1 adversarial = 3 per tenant × 5 tenants = 15 personas total**
- [x] **Q9 — URL verification: solo schema valid** (escalable 1000+ tenants; HTTP 200 check NO en CI)
- [x] **Q10 — Estimate: lo necesario** → propuesta 5-7d total (justificada por scope expansion 3→5 tenants)

## Próximo paso

`type=service-story` → ratificada (`ratified_by_chris: true`) → transition `state=refining → refined` → `/architect` produce ready package (03-arch.md + 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml).

## Changelog

- v1 2026-05-06 — `/po` draft inicial. 4 scenarios + 10 open questions críticas para ratificación.
- v2 2026-05-06 20:55Z — **Chris ratified all 10 questions.** Cambios: scope 3→5 tenants (A1 Coach + A2 Medicina estética + A3 Clínica dental + A4 Growth Marketing video+RRSS + A5 Agencia Automatización IA), dialect catalog BCP-47 ratificado, dialect picks per archetype (PE/MX/CO/AR/419), spawned new placeholder story `sales-agent-dialect-configuration` (Q7 feature UX), buyer personas 3 per tenant (2 base + 1 adversarial), estimate 5-7d. State transition refining → refined.
