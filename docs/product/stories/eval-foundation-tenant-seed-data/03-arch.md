---
story_id: eval-foundation-tenant-seed-data
surface: BE
sub_architect: /architect (orchestrator, BE inline — no /architect-be sub-spawn por scope data-fixtures pure, sin DDD nuevo / sin migrations / sin services)
arch_version: 1
last_modified: 2026-05-06T21:10Z
links:
  spec: 01-spec.md
  story_md: 00-story.md
  outcome: ../../outcomes/pi-12-sales-agent-eval-foundation.md
  related_new_story: ../sales-agent-dialect-configuration/
  rules:
    - ../../../../.claude/rules/anti-duplication.md
    - ../../../../.claude/rules/spanish-text.md
    - ../../../../.claude/rules/parallel-safety.md
    - ../../../../.claude/rules/git-safety.md
    - ../../../../.claude/rules/tdd-mandatory.md
    - ../../../../.claude/rules/backend-ddd.md
    - ../../../../.tessl/tiles/maria/fastapi/rules/pii-sanitisation.md
---

## Decisión arquitectónica clave

**Story es data-engineering puro + scripts + tests** — sin código de runtime, sin migrations, sin services, sin DDD nuevo. Toda la "arquitectura" se reduce a (a) layout de archivos en `backend/tests/fixtures/eval/tenants/`, (b) Pydantic schema reuse de modelos existentes (`brand`, `offer`, sales_agent personality compiler v2), (c) loader funcional puro filesystem→TenantContext in-memory, (d) regex scanner PII + integración pre-commit hook Section 7, (e) catálogo BCP-47 dialectos como YAML referenciable.

**Decisión cardinal (AD1):** **layout multi-folder por archetype** — 5 subfolders bajo `backend/tests/fixtures/eval/tenants/`, cada uno con 6 YAMLs + README. Razón: aislamiento estrictamente per-tenant (consumers downstream cargan UN archetype a la vez via slug), facilita PR review (diff por carpeta), evita cross-pollination accidental durante curación.

**Decisión cardinal (AD2):** **schemas Pydantic re-use, no re-redactar** — los YAMLs validan contra modelos ya existentes en `backend/src/modules/brand/domain/`, `backend/src/modules/offer/domain/`, y la inferida de `personality_profiles` (la story `maintenance-skill-sales-agent-audit` que está en state=ready audita estos paths antes que esta story arranque developing). Si los modelos no exponen el subset que necesitamos, el loader hace `model_validate(yaml.safe_load(...))` sobre subsets parcialmente populados (Pydantic permite `model_validate` con campos opcionales no provistos). Drift detection vía test `test_schema_alignment.py` que falla cuando el modelo cambia sin que YAMLs se actualicen.

**Decisión cardinal (AD3):** **TenantContext es dataclass simple, no nueva entity domain** — definida en `backend/tests/fixtures/eval/tenants/loader.py` como `@dataclass(frozen=True) class TenantContext` con campos `brand`, `personality_profile`, `offer_ladder`, `pricing`, `buyer_personas`, `communication_assets`, `archetype_slug`. Razón: pertenece al test infrastructure layer, no al domain del módulo. Si futuro consumer quiere TenantContext en `src/`, eso es story aparte.

**Decisión cardinal (AD4):** **dialect_code field como first-class via personality_profile.yaml** — campo `dialect_code: str` (BCP-47 valid) en `personality_profile.yaml`. El loader valida que el code existe en `dialect_catalog.yaml`. Esto **NO modifica el modelo Pydantic de `personality_profiles`** del módulo sales_agent (que sería runtime impact prohibido per AD9 abajo); el loader extrae el campo del YAML pre-Pydantic-validation, lo asigna a TenantContext.dialect_code, y descarta del payload Pydantic (o lo agrega con `model_config = ConfigDict(extra="allow")` local al test). Cuando la story `sales-agent-dialect-configuration` se construya, ESA story formaliza el campo en el modelo runtime.

**Decisión cardinal (AD5):** **scanner PII como script standalone read-only** — `backend/scripts/scan_seed_pii.py` con CLI `python scan_seed_pii.py <path>`, exit code 0 GREEN / 1 RED / 2 missing path. Regex set: email RFC 5322 + teléfono LatAm/intl + DNI/CUIT/RUT/CURP/RFC + URL interna `*.nicolify.com`. Whitelist: `backend/tests/fixtures/eval/tenants/.eval-whitelist` (YAML con `whitelisted_urls` + `whitelisted_emails` + `whitelisted_phones`). Pre-commit hook Section 7 invoca el script.

**Decisión cardinal (AD6):** **edge L0 missing → warning structlog + has_lead_magnet computed property** — el loader emite `structlog.warning("offer_ladder_missing_lead_magnet", tenant_slug=..., missing_levels=[...])` y `TenantContext.offer_ladder.has_lead_magnet` es `True` solo si offer_ladder contiene una offer con `level == "L0"` (case-insensitive match). Consumers downstream pueden inspeccionar el flag.

**Decisión cardinal (AD7):** **dialect_catalog.yaml como SSoT** — archivo único bajo `backend/tests/fixtures/eval/tenants/dialect_catalog.yaml` con 15 entradas iniciales (es-419, es-AR, es-UY, es-CL, es-MX, es-PE, es-CO, es-VE, es-EC, es-PY, es-CR, es-DO, es-CU, es-PR, es-ES). Cada entry: `code`, `display_name`, `voseo` (`true|false|"parcial"`), `country_code`, `description`. Cuando la feature `sales-agent-dialect-configuration` se construya, el catálogo migra a `backend/src/modules/sales_agent/domain/dialect_catalog.py` (o YAML en `backend/src/modules/sales_agent/data/`). Hasta entonces vive en fixtures.

**Decisión cardinal (AD8):** **URLs verification solo schema** — regex `^https?://[a-zA-Z0-9.-]+(?:/[^\s]*)?$` valida formato pero NO hace HTTP requests. Decisión per Q9 ratified Chris (escalable 1000+ tenants).

**Decisión cardinal (AD9):** **cero `production_code`** — owner pool tickets `[qwen-opencode, claude-sonnet]`. Opus NOT required. Razón: aunque el contenido del seed refiere al módulo `sales_agent`, el trabajo es:
- YAMLs en `tests/fixtures/` (no es `src/`)
- Loader en `tests/fixtures/` (no es `src/`)
- Scanner en `backend/scripts/` (no es `src/`)
- Pre-commit hook en `scripts/git-hooks/` (no es `src/`)
- Tests en `tests/fixtures/`
- Capability YAML edit en `docs/product/`

Cero líneas en `backend/src/` o `frontend/src/`.

**Decisión cardinal (AD10):** **ticket split en 4** — story 5-7d excede 8h cap por ticket. Split natural: T-1 (infra schema+loader+catalog+tests baseline) → T-2 (scanner+hook) → T-3 (drafts 5 YAMLs por archetype con content) → T-4 (curación Chris + GREEN final). Detalle en `06-tickets.yaml`.

## Surface diff (BE)

### Endpoints nuevos / modificados

Ninguno.

### DTOs

Ninguno (el `TenantContext` es dataclass de test infrastructure, no DTO de API).

### Domain entities / VOs

Ninguno nuevo. Re-uso de modelos Pydantic existentes (validación read-only).

### Migrations

Ninguna.

### Servicios + Repos

Ninguno.

### Eventos emitidos / consumidos

Ninguno.

### Files nuevos (full inventory)

```
backend/tests/fixtures/eval/tenants/
├── __init__.py                                    # NEW — empty package marker
├── conftest.py                                    # NEW — fixtures shareables (TenantContext factory, parametrize archetype_slug)
├── loader.py                                      # NEW — load_eval_tenant() + TenantContext dataclass
├── dialect_catalog.yaml                           # NEW — 15 entries BCP-47
├── .eval-whitelist                                # NEW — whitelist URLs/emails/phones públicos
├── tenant_coach_lat/                              # NEW — A1
│   ├── brand.yaml
│   ├── personality_profile.yaml                   # incluye dialect_code: es-PE
│   ├── offer_ladder.yaml                          # 5 offers L0..L4 (con lead magnet)
│   ├── pricing.yaml                               # currency: PEN
│   ├── buyer_personas.yaml                        # 3 personas (2 base + 1 adversarial)
│   ├── communication_assets.yaml
│   └── README.md                                  # rationale + reference real (visionarias.lat)
├── tenant_medicina_estetica/                      # NEW — A2
│   └── ... (6 YAMLs + README, dialect_code: es-MX, currency: PEN)
├── tenant_clinica_dental/                         # NEW — A3
│   └── ... (dialect_code: es-CO, currency: PEN)
├── tenant_agencia_growth_video/                   # NEW — A4
│   └── ... (dialect_code: es-AR, currency: PEN, sin L0 lead magnet — edge case)
├── tenant_agencia_automatizacion_ia/              # NEW — A5
│   └── ... (dialect_code: es-419, currency: PEN, sin L0 lead magnet — edge case)
├── test_loader.py                                 # NEW — tests del loader (5 tenants × assertions)
├── test_realism_smoke.py                          # NEW — ≥5 campos no-null por YAML
├── test_schema_alignment.py                       # NEW — Pydantic validation drift detection
├── test_dialect_catalog.py                        # NEW — catálogo completo + dialect_code de cada tenant válido
└── test_seed_pii_scanner.py                       # NEW — 4 fixtures adversariales + post-commit defense in depth

backend/scripts/
└── scan_seed_pii.py                               # NEW — CLI scanner regex PII

scripts/git-hooks/
└── pre-commit                                     # MODIFY — agregar Section 7 (PII scan en eval/tenants/)

backend/tests/scripts/
└── test_pre_commit_hook.py                        # MODIFY — agregar test_blocks_pii_in_seed_tenants scenario

docs/product/capabilities/sales-agent/
└── sales-conversational-engine.yaml               # MODIFY — agregar eval.seed_tenants_path + eval.seed_archetype_slugs
```

**Totales:** 30 YAMLs (5 × 6) + 5 READMEs + 1 catalog YAML + 1 .eval-whitelist + 1 loader.py + 5 test files + 1 scanner script + 1 conftest.py + 1 __init__.py = **45 archivos nuevos** + 3 archivos modificados.

### Tests requeridos (5 archivos test, ≥20 funciones)

`test_loader.py`:
- `test_loads_all_5_archetype_slugs[archetype_slug]` parametrizado (5 funcs efectivas via parametrize)
- `test_dialect_code_per_archetype_matches_table` — A1=es-PE, A2=es-MX, A3=es-CO, A4=es-AR, A5=es-419
- `test_offer_ladder_no_lead_magnet_emits_warning_proceeds_load` — A4+A5 disparan warning, A1+A2+A3 no
- `test_buyer_personas_count_3_per_tenant`
- `test_pricing_currency_pen_for_all`
- `test_loader_raises_on_missing_archetype_slug` — slug inexistente → KeyError o custom

`test_realism_smoke.py`:
- `test_each_yaml_has_min_5_non_null_fields[archetype_slug-yaml_filename]` parametrizado (30 funcs efectivas)

`test_schema_alignment.py`:
- `test_brand_yaml_validates_against_pydantic_model[archetype_slug]`
- `test_offer_ladder_yaml_validates_against_pydantic_model[archetype_slug]`
- `test_personality_profile_yaml_validates_against_pydantic_model[archetype_slug]`
- `test_loader_raises_on_missing_required_field` — fixture sintética con campo omitido

`test_dialect_catalog.py`:
- `test_catalog_has_min_13_entries`
- `test_catalog_contains_all_archetype_dialects` — set seed dialects ⊆ set catalog codes
- `test_each_entry_has_required_fields` — code, display_name, voseo, country_code, description
- `test_invalid_dialect_code_raises` — fixture con dialect_code "es-XX-INVALID" → assertion error

`test_seed_pii_scanner.py`:
- `test_4_categories_detected_on_adversarial_fixtures[email|phone|dni|url]` parametrizado
- `test_no_pii_in_committed_seeds` — re-corre scanner sobre los 30 YAMLs reales
- `test_whitelist_skips_known_public_urls` — visionarias.lat permitido
- `test_whitelist_skips_synthetic_fixtures_in_sample_exchanges` — `+99 0 ...`, `@example.com` permitidos

**Coverage minimum:** N/A — tests viven en `tests/fixtures/`, no participan del threshold del módulo (43%).

**Determinismo:** todos los tests son puros — leen filesystem, no DB, no network, no LLM. `pytest --count=3` debe pasar idéntico.

## Surface diff (FE)

N/A — story no toca FE.

## Surface diff (Agentic)

N/A — story es data-fixtures + tests + scripts. Cero runtime agentic. Cuando la story `sales-agent-dialect-configuration` se construya, ESA story toca runtime agentic (compiler personality_profile recibe nuevo input dialect_code). Esta NO.

## Cross-cutting concerns

- **Tenant isolation:** N/A en runtime (no DB queries). En filesystem: cada subfolder contiene SOLO data de un único archetype; cross-tenant data en mismo YAML → schema fail.
- **Idempotency:** loader idempotente (pure filesystem reads).
- **Rate limiting:** N/A.
- **Caching:** N/A.
- **Backwards compatibility:** consumers downstream que no existen aún → contrato a definir cuando se construyan. La signature `load_eval_tenant(archetype_slug) → TenantContext` es estable.
- **PII:** scanner PII bloquea commits con PII real; whitelist explicita gestiona excepciones públicas.
- **Spanish neutro:** README + scanner CLI messages en español neutro siempre. `personality_profile.yaml::sample_exchanges` respeta dialect_code (voseo si AR, parcial si CL/CR/CO-paisa, tuteo si PE/MX/CO-bogotano/VE/EC/419). Magic comment `<!-- voseo-allowed -->` agregado en personality_profile.yaml de A4 (es-AR).
- **Schema drift:** `test_schema_alignment.py` falla rápido si Pydantic models cambian post-merge.

## Riesgos y mitigaciones

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Pydantic models de `brand`/`offer` cambian post-T-1 invalidando seed YAMLs | high | `test_schema_alignment.py` corre en CI; falla rápido. Si hay drift, se reabre la story para update. |
| Currency mismatch dialect (PEN para tenant es-AR/es-MX) confunde consumers downstream | medium | Documentado en README per archetype + en spec NFR. Consumers reciben `currency` y `dialect_code` separados; no hay assumption de coupling. |
| Scanner PII tiene false positives en data sintética legítima | medium | `.eval-whitelist` con URLs públicas + emails sintéticos `@example.com` + teléfonos `+99 0 ...` documentados. |
| Curación Chris excede 1-3d propuesto → story se vuelve 9-10d | medium | T-3 (drafts iniciales por builder) reduce carga Chris a ratificar/ajustar; estimate 1-3d realista si Chris dispone 2-3h por día. Si excede, escalar checkpoint blocked. |
| Builder LLM (sonnet/qwen) inventa data implausible que rompe realismo | low | Builder cita references reales en README + Chris ratifica T-4 antes merge. Smoke test `test_realism_smoke.py` cubre min 5 campos no-null. |
| Pre-commit hook Section 7 colisiona con Sections 1-6 existentes | low | Test extendido `test_pre_commit_hook.py::test_blocks_pii_in_seed_tenants` cubre composability. |
| `dialect_code: es-419` en A5 confunde si el grader voice fidelity (story E) espera dialecto concreto | low | `es-419` es legítimo en catálogo; grader debe tratarlo como "any LatAm neutro acceptable". Documentar en spec story E cuando se refine. |

## Decisiones registradas

- **2026-05-06 21:10Z** — Skip /architect-be sub-spawn (BE inline). Razón: data-fixtures + scripts + tests, sin DDD/services/migrations. Architect-be especializa en surfaces que aquí no existen.
- **2026-05-06 21:10Z** — `production_code: false` para los 4 tickets. Owner pool [qwen-opencode, claude-sonnet]. Opus NOT required.
- **2026-05-06 21:10Z** — Ticket split en 4 (T-1 infra + T-2 scanner+hook + T-3 drafts content + T-4 curación). Total ~5-7d. Cada ticket ≤ 2d nominal.
- **2026-05-06 21:10Z** — `dialect_code` field NO modifica modelo Pydantic runtime de personality_profiles — solo dataclass test infrastructure. Story `sales-agent-dialect-configuration` formaliza runtime.
- **2026-05-06 21:10Z** — Catálogo BCP-47 vive en `backend/tests/fixtures/eval/tenants/dialect_catalog.yaml` hasta que la story dialect-configuration migre a `backend/src/modules/sales_agent/`.

## Próximo paso

Ready package consolidado tras producir 04-validators.yaml + 05-guidelines.md + 06-tickets.yaml + checkpoint transition refined→ready. Conv 2 (autonomous build) puede arrancar — `/dev-team` toma T-1 primero, después T-2, T-3, T-4 secuencial respetando depends_on.
