# 05-guidelines.md — Story eval-foundation-tenant-seed-data

> Owner: `/architect`. Patterns concretos que `/dev-team` debe seguir/evitar. SIN AMBIGÜEDAD.

## Workflow del build (4 tickets — orden estricto)

T-1 → T-2 → T-3 → T-4. Cada ticket cierra GREEN antes que el siguiente arranque. Detalle deliverables en `06-tickets.yaml`.

### Pre-build (Step 0 dev-team)

```bash
# Verificar pre-requisito story `maintenance-skill-sales-agent-audit` está al menos refined
# (mejor ready). Skill audit garantiza que paths citados en personality compiler v2 son verídicos.
cat docs/product/stories/maintenance-skill-sales-agent-audit/checkpoint.md | grep state
# Si state=ready o developed → proceed
# Si state<refined → escalate Chris (eval-foundation-* depende de skill audit completo)
```

### Pre-build (Step 0.5) — read existing models

```bash
# Read Pydantic models del módulo brand para schema_alignment
grep -rn "class.*BaseModel" backend/src/modules/brand/domain/ | head -20

# Read Pydantic models del módulo offer
grep -rn "class.*BaseModel" backend/src/modules/offer/domain/ | head -20

# Read personality compiler v2 (post audit)
grep -rn "PersonalityCompiler\|compile" backend/src/modules/brand/domain/personality.py | head -20
```

Estos paths son la SSoT de schemas. Si los modelos exponen subset distinto al esperado → ajustar YAMLs (no modificar models).

## Patterns required

- **TDD strict (R8):** escribir tests pytest primero (RED), después YAMLs/loader/scanner hasta GREEN
- **Test parsing puro:** loader usa `yaml.safe_load(...)` + `pydantic.BaseModel.model_validate(...)`. Scanner usa `re.compile(...)` + `pathlib`. Sin librerías exóticas
- **Dataclass frozen para TenantContext:** `@dataclass(frozen=True)` en loader.py. Inmutable post-load.
- **Imports `from __future__ import annotations` + `from pathlib import Path` + `import re` + `import yaml` + `from dataclasses import dataclass` + `import structlog`**
- **REPO_ROOT resolution:** `Path(__file__).resolve().parents[3]` precedente test_pre_commit_hook.py
- **structlog para warnings:** `structlog.get_logger().warning("offer_ladder_missing_lead_magnet", tenant_slug=..., missing_levels=[...])`. Captured via `caplog` o `structlog.testing.capture_logs()` fixture
- **Magic comment voseo-allowed:** agregar `<!-- voseo-allowed -->` en primera línea (o primeras 20) del `personality_profile.yaml` de A4 (`tenant_agencia_growth_video`, dialect_code es-AR) que cita voseo verbatim en sample_exchanges. NO necesario en otros tenants (PE/MX/CO/419 = tuteo).
- **Dialect picks ratificados — NO inventar:**
  - `tenant_coach_lat` → `dialect_code: es-PE`
  - `tenant_medicina_estetica` → `dialect_code: es-MX`
  - `tenant_clinica_dental` → `dialect_code: es-CO`
  - `tenant_agencia_growth_video` → `dialect_code: es-AR`
  - `tenant_agencia_automatizacion_ia` → `dialect_code: es-419`
- **Currency PEN para los 5 tenants** (test isolation > realismo perfecto, ratificado Q3)
- **Buyer personas count = 3 per tenant** (2 base + 1 adversarial, total 15 personas across 5 tenants)
- **offer_ladder L0 lead magnet:**
  - A1 (Coach), A2 (Medicina estética), A3 (Clínica dental) → SÍ tienen L0 (PDF gratis / consulta primera vez gratis / consulta evaluación gratis)
  - A4 (Growth Marketing video), A5 (Automatización IA) → NO tienen L0 (entran por casos de éxito + discovery call). Trigger del edge case warning.
- **References reales en README (sin scrap):** cada README cita URL real de inspiración (e.g., visionarias.lat para A1) en sección "Inspiración"; data del seed NO es scrap del sitio real.
- **Stage commits por nombre exacto:** `git add backend/tests/fixtures/eval/tenants/{slug}/{filename}.yaml` — prohibido `git add -A`
- **Conventional commits per ticket:**
  - T-1: `feat(eval-fixtures): seed loader + dialect catalog + tests baseline (T-1)`
  - T-2: `feat(eval-fixtures): seed PII scanner + pre-commit hook section 7 (T-2)`
  - T-3: `feat(eval-fixtures): drafts 5 tenants seed YAMLs + READMEs (T-3)`
  - T-4: `feat(eval-fixtures): ratify Chris curation + capability update + GREEN (T-4)`
- **Cite decisions_applicable en commit body** sección "Decisions honored": "AD1-AD10 (arch), Q1-Q10 (spec ratified)"
- **Pre-commit hook respect:** SIEMPRE corre. NO `--no-verify`. Si scanner PII bloquea legítimamente → sanitizar con sintético equivalente. Si bloquea por whitelisted-pero-no-en-whitelist → agregar a `.eval-whitelist` con justificación inline.

## Patterns forbidden

- ❌ Crear archivos nuevos en `backend/src/` o `frontend/src/` (story es data-fixtures + scripts + tests, cero runtime impact)
- ❌ Crear migrations Alembic (loader es in-memory only — Q4 ratificado)
- ❌ Modificar Pydantic models existentes (`brand`, `offer`, personality_profile compiler v2). Si el seed YAML no encaja con model existente → ajustar YAML, NO model.
- ❌ Agregar `dialect_code` field al modelo Pydantic runtime de `personality_profiles` (esa es feature de la story `sales-agent-dialect-configuration`, fuera de scope esta story). En seed YAML, `dialect_code` se carga al `TenantContext` dataclass sin tocar el model runtime.
- ❌ Crear nuevos archivos en `references/` del skill `sales-agent-expert` (out-of-scope; ese audit ya cerró)
- ❌ Modificar `.claude/rules/` (out-of-scope; si detectas need de rule nueva, escalar Chris)
- ❌ Splittear personality_profile.yaml en archivos múltiples (estructura preservada — 6 YAMLs por tenant, fixed)
- ❌ Hardcodear paths absolutos en loader.py (usa `Path(__file__).resolve().parents[N]` o config relativa al package)
- ❌ Borrar contenido sintético adversarial sin agregarlo a `.eval-whitelist` (cero PII real en commits, pero también cero falsos positivos en scanner)
- ❌ Usar `pytest.mark.skip` o `xfail` para "pasar" CI — corregir la causa
- ❌ `// TODO`, `# TODO`, `# HACK`, `# FIXME` en código del loader/scanner (cero deuda técnica)
- ❌ Hacer HTTP requests durante tests o build (Q9 — solo schema valid, no live verification)
- ❌ Importar desde `backend/src/modules/sales_agent/` en `loader.py` o tests del seed (cross-cutting prohibido — tests/fixtures/ NO depende de `modules/sales_agent/` runtime; si necesita un schema, lo importa via modelos `brand` u `offer` que ya son cross-cutting acceptable)
- ❌ Crear loader que invoque sales_agent runtime real (loader produce TenantContext puro; consumers downstream deciden cómo usarlo)
- ❌ `dialect_code` con valor que NO está en `dialect_catalog.yaml` — viola gate `test_dialect_catalog.py::test_invalid_dialect_code_raises`
- ❌ Currency != PEN en alguno de los 5 tenants (Q3 ratified single-currency seed)
- ❌ Buyer personas count != 3 por tenant (Q8 ratified 2 base + 1 adversarial)
- ❌ Lead magnet (L0) en A4 o A5 (contradice edge case scenario 3 — esos tenants intencionalmente NO tienen L0)
- ❌ Lead magnet (L0) ausente en A1, A2 o A3 (esos tenants intencionalmente SÍ tienen L0)

## Files in scope (dev-team edita SOLO estos)

### NUEVOS — T-1 (infra)

- `backend/tests/fixtures/eval/tenants/__init__.py`
- `backend/tests/fixtures/eval/tenants/conftest.py`
- `backend/tests/fixtures/eval/tenants/loader.py`
- `backend/tests/fixtures/eval/tenants/dialect_catalog.yaml`
- `backend/tests/fixtures/eval/tenants/test_loader.py`
- `backend/tests/fixtures/eval/tenants/test_realism_smoke.py`
- `backend/tests/fixtures/eval/tenants/test_schema_alignment.py`
- `backend/tests/fixtures/eval/tenants/test_dialect_catalog.py`

### NUEVOS — T-2 (scanner + hook)

- `backend/scripts/scan_seed_pii.py`
- `backend/tests/fixtures/eval/tenants/.eval-whitelist`
- `backend/tests/fixtures/eval/tenants/test_seed_pii_scanner.py`
- `scripts/git-hooks/pre-commit` (MODIFY — agregar Section 7)
- `backend/tests/scripts/test_pre_commit_hook.py` (MODIFY — agregar `test_blocks_pii_in_seed_tenants`)

### NUEVOS — T-3 (drafts content)

- `backend/tests/fixtures/eval/tenants/tenant_coach_lat/{brand,personality_profile,offer_ladder,pricing,buyer_personas,communication_assets}.yaml`
- `backend/tests/fixtures/eval/tenants/tenant_coach_lat/README.md`
- `backend/tests/fixtures/eval/tenants/tenant_medicina_estetica/{...}` idem 6 YAMLs + README
- `backend/tests/fixtures/eval/tenants/tenant_clinica_dental/{...}` idem
- `backend/tests/fixtures/eval/tenants/tenant_agencia_growth_video/{...}` idem (sin L0)
- `backend/tests/fixtures/eval/tenants/tenant_agencia_automatizacion_ia/{...}` idem (sin L0)

### MODIFY — T-4 (curación + capability)

- 30 YAMLs anteriores (ajustes per ratificación Chris)
- 5 README.md anteriores (ajustes)
- `docs/product/capabilities/sales-agent/sales-conversational-engine.yaml` (agregar `eval.seed_tenants_path` + `eval.seed_archetype_slugs`)

### MODIFY — todos los tickets

- `docs/product/stories/eval-foundation-tenant-seed-data/T-{n}-impl-log.md` (NEW per ticket)
- `docs/product/stories/eval-foundation-tenant-seed-data/checkpoint.md` (state transitions per ticket)

## Files dev-team NEVER touches (escalate to Chris)

- `backend/src/modules/sales_agent/**` (cero runtime impact)
- `backend/src/modules/brand/**` y `backend/src/modules/offer/**` (read-only — solo importar models para validation)
- `backend/src/shared/**` (cross-cutting; el sanitizer existe, NO duplicar)
- `backend/alembic/versions/**` (no migrations)
- `frontend/src/**` (no FE)
- `frontend/e2e/**` (no E2E)
- `.claude/skills/sales-agent-expert/**` (audit de esa story es separate, ya cerró)
- `.claude/rules/**`
- `.claude/agents/**`
- `docs/process/learnings.md` (solo `/pm`)
- `docs/product/BACKLOG.md` (auto-gen — solo pre-commit hook R33)
- `MEMORY.md` (solo `/pm`)
- Outcomes en `docs/product/outcomes/` (solo `/pm`)
- Otras stories en `docs/product/stories/` que no sean `eval-foundation-tenant-seed-data`
- `docs/product/stories/sales-agent-dialect-configuration/` (placeholder — Chris dispara refinement futuro, NO modificar ahora)

## Reference docs (load before coding)

- `01-spec.md` (re-leer scenarios + decisions Q1-Q10 mid-build cuando dude)
- `03-arch.md` (re-leer AD1-AD10 cuando surja ambigüedad técnica)
- `04-validators.yaml` (los validators son la verdad operacional)
- skill `sales-agent-expert` (post-audit; cita `personality_profiles.system_instruction` SSoT)
- skill `brand-expert` (schema brand.yaml)
- skill `offer-expert` (schema offer_ladder.yaml + offer levels L0..L4)
- `.claude/rules/spanish-text.md` § sales_agent excepción + magic comment voseo-allowed
- `.claude/rules/anti-duplication.md` (sanitization SSoT shared — no re-redactar)
- `.claude/rules/parallel-safety.md` (M1-M8 — esp. M8 archivos ajenos)
- `.claude/rules/git-safety.md` (stage por nombre)
- `.claude/rules/tdd-mandatory.md` (RED → GREEN)
- `.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md` (patrones PII canónicos)
- `backend/tests/scripts/test_pre_commit_hook.py` (precedente — test pattern sobre hook)
- `backend/tests/scripts/conftest.py` (fixtures comunes)

## Catálogo BCP-47 — contenido inicial mínimo

`backend/tests/fixtures/eval/tenants/dialect_catalog.yaml`:

```yaml
# Catálogo dialectos BCP-47 — SSoT temporal hasta que story sales-agent-dialect-configuration
# migre a backend/src/modules/sales_agent/.
# Mantener ordenado por code para diff legible.

dialects:
  - code: es-419
    display_name: "Español neutro (LatAm)"
    voseo: false
    country_code: null
    description: "Convención mediática pan-LatAm. Default seguro."
  - code: es-AR
    display_name: "Rioplatense (Argentina)"
    voseo: true
    country_code: AR
    description: "Voseo + sh para ll/y + lunfardo."
  - code: es-CL
    display_name: "Chileno"
    voseo: parcial
    country_code: CL
    description: "Voseo verbal informal + chilenismos."
  - code: es-CO
    display_name: "Colombiano"
    voseo: parcial
    country_code: CO
    description: "Tuteo bogotano / voseo paisa."
  - code: es-CR
    display_name: "Costarricense"
    voseo: parcial
    country_code: CR
    description: "Voseo + tuteo mixed."
  - code: es-CU
    display_name: "Cubano"
    voseo: false
    country_code: CU
    description: "Caribeño con aspiración s."
  - code: es-DO
    display_name: "Dominicano"
    voseo: false
    country_code: DO
    description: "Caribeño con aspiración s + uso de tú."
  - code: es-EC
    display_name: "Ecuatoriano"
    voseo: false
    country_code: EC
    description: "Andino similar a PE."
  - code: es-ES
    display_name: "Castellano (España)"
    voseo: false
    country_code: ES
    description: "Peninsular. Vosotros (informal plural). Distinción c/z vs s."
  - code: es-MX
    display_name: "Mexicano"
    voseo: false
    country_code: MX
    description: "Tuteo neutral + lexicón mexicano."
  - code: es-PE
    display_name: "Peruano (limeño/andino)"
    voseo: false
    country_code: PE
    description: "Andino claro + tuteo."
  - code: es-PR
    display_name: "Puertorriqueño"
    voseo: false
    country_code: PR
    description: "Caribeño con aspiración s + influencia inglés."
  - code: es-PY
    display_name: "Paraguayo"
    voseo: true
    country_code: PY
    description: "Bilingüe español-guaraní + voseo."
  - code: es-UY
    display_name: "Rioplatense (Uruguay)"
    voseo: true
    country_code: UY
    description: "Similar AR con sutilezas léxicas."
  - code: es-VE
    display_name: "Venezolano"
    voseo: false
    country_code: VE
    description: "Caribeño + andino mix."
```

## .eval-whitelist — contenido inicial mínimo

`backend/tests/fixtures/eval/tenants/.eval-whitelist`:

```yaml
# Whitelist URLs/emails/phones públicos legítimamente referenciados en seed YAMLs.
# El scanner PII skipea estos patrones (no falsos positivos).
# Cada entry MUST tener `justification` inline.

whitelisted_urls:
  - url: "https://visionarias.lat"
    justification: "Reference real público A1 Coach LatAm humano (visited 2026-05-06, public site)"
  - url: "https://www.youtube.com/@visionarias.oficial"
    justification: "Podcast YouTube público A1, citado en communication_assets.yaml"

whitelisted_email_domains:
  - domain: "@example.com"
    justification: "Synthetic emails per RFC 2606 — used in sample_exchanges of personality_profile.yaml"

whitelisted_phone_prefixes:
  - prefix: "+99 0"
    justification: "Synthetic phones reserved (ITU-T E.164 not assigned) — used in sample_exchanges"
  - prefix: "+99 9"
    justification: "Synthetic phones reserved — alternative pattern"
```

## Scanner PII — patrones regex mínimos

`backend/scripts/scan_seed_pii.py`:

```python
# Regex set canónico (extender si Chris ratifica nuevos patterns)
PATTERNS = {
    "email": r"(?<![a-zA-Z0-9._%+-])([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})(?![a-zA-Z0-9.])",
    "phone_intl": r"(?<![\d])(\+\d{1,3}[\s\-]?\(?\d{1,4}\)?[\s\-]?\d{1,4}[\s\-]?\d{1,4}[\s\-]?\d{0,4})(?![\d])",
    "dni_ar": r"(?<![\d.])(\d{1,2}\.\d{3}\.\d{3})(?![\d.])",
    "cuit_ar": r"(?<![\d-])(\d{2}-\d{8}-\d)(?![\d])",
    "rut_cl": r"(?<![\d.])(\d{1,2}\.?\d{3}\.?\d{3}-[\dkK])(?![\d.])",
    "dni_pe": r"(?<![\d])(\d{8})(?![\d])",  # cuidado false positives — refina con context guard
    "curp_mx": r"(?<![A-Z])([A-Z]{4}\d{6}[HM][A-Z]{5}[A-Z\d]\d)(?![A-Z\d])",
    "rfc_mx": r"(?<![A-Z])([A-ZÑ&]{3,4}\d{6}[A-Z\d]{3})(?![A-Z\d])",
    "url_internal_nicolify": r"https?://(?:[a-zA-Z0-9-]+\.)*nicolify\.com(?:/[^\s]*)?",
}
```

**Whitelist match:** ANTES de aplicar regex, comparar contra `.eval-whitelist`. Si match → skip.

## Anti-patterns prohibidos resumen

1. ❌ Inventar dialect picks distinto a tabla ratificada (PE/MX/CO/AR/419)
2. ❌ Currency mixed (siempre PEN para los 5)
3. ❌ Buyer personas != 3 per tenant
4. ❌ L0 lead magnet en A4 o A5 (rompe edge case)
5. ❌ Saltarse Step 0/0.5 (verificar pre-requisito skill audit + read existing models)
6. ❌ Crear archivos en `backend/src/`
7. ❌ Modificar Pydantic models para forzar YAML inválido a validar
8. ❌ Reportar GREEN sin `T-{n}-impl-log.md` con secciones obligatorias
9. ❌ `pytest.mark.skip`/`xfail` para esquivar tests rojos
10. ❌ `--no-verify` en commits (pre-commit hook obligatorio)
11. ❌ Tocar archivos ajenos (M8 parallel-safety)
12. ❌ HTTP requests durante tests/build

## Validation antes de cerrar cada ticket

Antes de marcar un ticket como `developed`:

- [ ] Validators de `04-validators.yaml::scenario_coverage` que apliquen al ticket → todos GREEN
- [ ] `T-{n}-impl-log.md` poblado con secciones obligatorias (ver template T-impl-log-template.md)
- [ ] `git diff --name-only HEAD~N..HEAD -- backend/src/ frontend/src/ | wc -l` = 0
- [ ] `git diff --name-only HEAD~N..HEAD -- backend/alembic/versions/ | wc -l` = 0
- [ ] Pre-commit hook pasa con archivos staged
- [ ] `make ci-parity` corrió GREEN si dev-team modificó algo no-trivial (T-1 + T-2 incluyen scripts, recommend ci-parity)

## Validation antes de cerrar story (todos los 4 tickets developed)

- [ ] T-1, T-2, T-3, T-4 todos `developed`
- [ ] 30 YAMLs + 5 READMEs + 1 dialect_catalog.yaml + 1 .eval-whitelist presentes
- [ ] Capability YAML actualizada
- [ ] `pytest backend/tests/fixtures/eval/tenants/ -v` GREEN end-to-end
- [ ] `bash scripts/git-hooks/pre-commit` GREEN con todos los archivos staged
- [ ] Determinismo: `pytest --count=3` o equivalente (validator `determinism_check`)
- [ ] `make ci-parity` GREEN

## Handoff downstream

Story state=`developed` → Chris triggers `/auditor` (Conv 3) manualmente para gestionar gasto Opus auditor:
- `/auditor` lee `01-spec.md` + `03-arch.md` + `T-1..T-4-impl-log.md` + diff
- Verifica los 4 scenarios cubiertos, decisions Q1-Q10 honored, AD1-AD10 honored
- APPROVED → `/pm` aplica merge → capability `sales-conversational-engine` bumpea con `eval.seed_tenants_path` + `eval.seed_archetype_slugs` → archive a `docs/archive/2026/stories/eval-foundation-tenant-seed-data/`
- Stories downstream que esperaban este seed (`eval-foundation-simulator-homologation`, `sales-agent-personas-instrumented-runtime`, `sales-agent-goldens-3-tenants-dataset`, etc.) ahora pueden arrancar refining → refined → ready con confianza en data ground truth concreta
