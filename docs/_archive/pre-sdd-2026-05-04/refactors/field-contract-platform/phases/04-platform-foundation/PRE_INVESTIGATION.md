# Pre-investigación obligatoria — Fase 04

> Las preguntas listadas debajo deben tener respuesta documentada con
> evidencia (grep + read) antes del primer Write/Edit de código.
> Si no se puede responder con confianza, **investigar** — no asumir.

## Sección 1 — Inventario de SSoT paralelos

**Q1.1** — ¿Cuántos registries declaran "qué fields existen y a qué
section pertenecen" en offer hoy?

**Esperado** (pre-Fase 04):
- `shared/links/ports/editable_fields::FieldSpec` registrado en
  `offer/domain/copilot_editable_fields.py`.
- `copilot/domain/offer_fields::PERSISTABLE_FIELDS`.
- `offer/domain/field_contract::FIELD_CONTRACT_REGISTRY`.
- `offer/domain/extraction_section_map::OFFER_FIELDS_BY_FE_SECTION`.
- `offer/domain/section_catalog` (secciones, no fields).

Confirmar via:
```bash
grep -rn "register_catalog\|FIELD_CONTRACT_REGISTRY\|OFFER_FIELDS_BY_FE_SECTION\|PERSISTABLE_FIELDS" \
  backend/src/modules/offer backend/src/modules/copilot backend/src/shared --include="*.py"
```

**Q1.2** — ¿Brand y buyer-persona tienen estructura paralela equivalente?

**Esperado**: sí. `brand/domain/copilot_editable_fields.py` con
`BRAND_EDITABLE_FIELDS` (~70 entries), `brand/domain/copilot_editable_fields_buyer_persona.py`
con `BUYER_PERSONA_EDITABLE_FIELDS` (~30 entries). No tocar en Fase 04.

## Sección 2 — Pydantic Offer surface

**Q2.1** — ¿Cuáles son TODOS los fields de `Offer` Pydantic?
Lista exhaustiva con tipo y default. Esto incluye:
- Top-level fields (~50)
- `specific_details` polymorphic union (Product/Service/Program/Subscription/Event)
- `platform_details: PlatformDetails | None` composable (14 sub-fields)
- Computed fields (excluir de contract)
- System fields (excluir de contract via ignore_paths)

Comando:
```bash
backend/.venv/bin/python -c "
from src.modules.offer.domain.offer import Offer
for fname, finfo in Offer.model_fields.items():
    print(f'{fname}: {finfo.annotation}')
"
```

Documentar lista completa antes de escribir `OFFER_SECTION_MAP`.

**Q2.2** — ¿Qué fields son sistema (no user-facing)?

**Esperado**: `id`, `tenant_id`, `deleted_at`, `archived_at`, `created_at`,
`updated_at`, `metadata_info`, `landing_page_config`, `status`,
`shows_as_lead_magnet` (computed).

Verificar también: `is_archived`, `is_deleted` (properties no Pydantic
fields, no aparecen en model_fields).

## Sección 3 — Mapping section por field

**Q3.1** — ¿Para cada Pydantic field user-facing, a qué section FE
pertenece?

Fuente: `OFFER_FIELDS_BY_FE_SECTION` + fields nuevos de `FIELD_CONTRACT_REGISTRY`
+ schemas FE en `frontend/src/features/offer-studio/schemas/`.

Documentar el mapping completo antes de escribir el OFFER_SECTION_MAP.

**Q3.2** — ¿Cuáles son las 21 sections FE válidas?

**Esperado**: `identity`, `strategy`, `psychology`, `promise`,
`program_details`, `service_details`, `event_details`, `product_details`,
`subscription_details`, `platform_details`, `location`, `instructors`,
`value_stack`, `pricing`, `testimonials`, `portfolio`, `faq`, `gallery`,
`resources`, `closing`, `knowledge`. Source: `extraction_section_map.FE_SECTION_SLUGS`.

**Q3.3** — ¿Hay sections "técnicas" no user-facing? (e.g. classification,
onboarding como hoy emite `copilot_editable_fields.py`)?

**Esperado**: `_CLASSIFICATION` y `_ONBOARDING` viven en
`copilot_editable_fields.py` pero no están en las 21 FE slugs. Decidir:
- ¿Están en algún schema FE actual? (verificar `frontend/...schemas/`)
- ¿El copilot necesita poder editarlos? (sí — `archetype`, `value_level`)
- ¿Cómo se mapean en FieldContract? Posiblemente section virtual `classification`
  + flag `internal_only` o similar.

Decisión documentada antes de Q4.

## Sección 4 — Polymorphic + composable handling

**Q4.1** — ¿Cómo walk `specific_details: Product | Service | Program | Subscription | Event | None`?

**Esperado**:
- Para cada variant, walk fields con prefix `specific_details.X`.
- Cada field hereda `archetype_filter` automático según
  `ARCHETYPE_TO_DETAILS_MAPPING` (PRODUCTO → Product, etc.).
- Override puede pisar archetype_filter si necesario.

**Q4.2** — ¿Cómo walk `platform_details: PlatformDetails | None`?

**Esperado**:
- Walk fields con prefix `platform_details.X`. No archetype_filter (composable).

**Q4.3** — ¿`PlatformDetails` tiene nested lists (`platform_features:
list[PlatformFeature]`)? Cómo registrar contracts?

**Esperado**: el path top-level (`platform_details.platform_features`)
es suficiente. Item shape (`PlatformFeature.name`, `.description`, etc.)
NO se desglosa en contracts individuales — vive en el itemSchema del FE
y en Pydantic. FieldContract lo declara como `type=LIST, list_item_type="object"`.

## Sección 5 — `OFFER_FIELDS_BY_FE_SECTION` consumers

**Q5.1** — ¿Quiénes consumen `OFFER_FIELDS_BY_FE_SECTION` hoy?

Comando:
```bash
grep -rn "OFFER_FIELDS_BY_FE_SECTION\|fields_to_fe_sections" backend/ --include="*.py"
```

**Esperado**:
- `offer/domain/extraction_section_map.py::fields_to_fe_sections`
- `offer/workers/tasks.py::on_progress` (vía import de `fields_to_fe_sections`)
- `tests/architecture/test_extraction_section_map_paths.py`
- `tests/architecture/test_offer_extraction_section_map.py`
- `tests/modules/offer/domain/test_extraction_section_map.py`
- `tests/modules/offer/workers/test_tasks_section_grouping.py`

Cada consumer migra en su sub-step correspondiente.

## Sección 6 — `OFFER_EDITABLE_FIELDS` audit

**Q6.1** — ¿Qué entries tiene `OFFER_EDITABLE_FIELDS` hoy?

Inventario completo antes de escribir overrides. ~36 entries esperadas.
Diff vs `Offer.model_fields user-facing` revela drift.

**Q6.2** — ¿Hay drift confirmado entre `OFFER_EDITABLE_FIELDS` y
`FIELD_CONTRACT_REGISTRY`?

**Esperado** (pre-Fase 04): sí. Pricing LATAM (tax_included, installments_available,
accepted_payment_providers), authority fields, total_perceived_value_anchor,
stack_positioning_statement están en uno pero no el otro. Cerrar el drift
es **bonus** de Fase 04 (Pydantic-first elimina la posibilidad).

## Sección 7 — Endpoint `/field-contract`

**Q7.1** — ¿Cuál es el JSON shape actual del endpoint?

Comando:
```bash
grep -rn "field-contract\|FieldContractRegistrySnapshot\|FIELD_CONTRACT_VERSION" backend/src/modules/offer
```

Capturar snapshot pre-refactor:
```bash
docker exec visionarias_brain_dev curl -s http://localhost:8000/api/v1/offer/field-contract \
  -H "X-Tenant-ID: 1fd1562b-2101-410a-870c-dc2f7e27b355" > /tmp/field_contract_pre.json
```

(Si el endpoint requiere auth, usar test client.)

Post-refactor: byte-identical o additive (campos nuevos en cada entry
OK; entries faltantes NO).

## Sección 8 — Tests existentes que protegen

**Q8.1** — ¿Qué tests cubren las áreas que voy a modificar?

Comando:
```bash
find backend/tests -name "test_*field_contract*" -o -name "test_*editable_fields*" \
  -o -name "test_*extraction_section*" -o -name "test_*offer_fields*" 2>/dev/null
```

**Esperado**:
- `tests/architecture/test_editable_fields_ssot.py`
- `tests/architecture/test_offer_extraction_section_map.py`
- `tests/architecture/test_extraction_section_map_paths.py`
- `tests/modules/offer/domain/test_extraction_section_map.py`
- `tests/modules/offer/workers/test_tasks_section_grouping.py`
- (posibles tests de `field_contract.py` y `offer_field_contract.py`)

Cada test debe seguir verde post-refactor. Si un test rompe → bug en
refactor, no en test.

## Sección 9 — Frontend impact zero

**Q9.1** — ¿Qué consume el FE del backend en Fase 04?

**Esperado**:
- Codegen `offer-field-paths.json` regenerado por
  `scripts/generate_offer_field_paths.py`. Output debe ser byte-identical
  o additive (nuevo path OK, perdido NO).
- Codegen `offer-field-paths.ts` idem.
- Endpoint `/field-contract` (vía hook `useFieldContract`) — shape preservado.

**Q9.2** — ¿Hay schemas FE que vamos a tocar?

**Esperado**: NO en Fase 04. Schemas son out-of-scope. Solo si
algún arch test FE rompe → investigar antes.

## Sección 10 — Coexistencia con brand/buyer/copilot

**Q10.1** — ¿El `editable_fields` port soporta múltiples módulos
con patrones distintos (brand manual + offer derivado)?

**Esperado**: sí. `register_catalog(domain, fields)` es lazy + idempotent.
Brand registra como hoy. Offer registra desde proyección. El consumer
(`get_catalog`) recibe la tuple final igual.

**Q10.2** — ¿Hay risk de circular imports al importar `shared/domain/field_contract.py`
desde `offer/domain/field_contract.py`?

**Esperado**: bajo si `shared` no importa de `modules`. Verificar.

## Sección 11 — Composable: `archetype` enum como string

**Q11.1** — `archetype_filter` en FieldContract: ¿enum `OfferArchetype`
o `tuple[str, ...]`?

Si enum → cross-module import (offer → shared/field_contract). Mal.
Si string → flexibilidad cross-module + decoupled.

**Decisión**: `tuple[str, ...]` (string values del enum). Override declara
`archetype_filter=("PROGRAMA", "MEMBRESIA")`. Walker auto-asigna desde
`ARCHETYPE_TO_DETAILS_MAPPING` con `.value` o `.name`.

Verificar consumer: ¿`fields_to_fe_sections` recibe `archetype:
OfferArchetype | None`? Sí. Convertir a string en consumer:
`archetype.value if archetype else None` antes de comparar.

## Output de la pre-investigación

Antes de empezar 04.B, debe existir:

- [ ] Lista completa Pydantic Offer fields (Q2.1, Q4.1, Q4.2).
- [ ] Lista de ignore_paths (Q2.2).
- [ ] OFFER_SECTION_MAP completo en draft (Q3.1).
- [ ] Decisión sobre _CLASSIFICATION/_ONBOARDING (Q3.3).
- [ ] Snapshot endpoint pre-refactor (Q7.1).
- [ ] Lista tests a preservar (Q8.1).
- [ ] Confirmación schemas FE no tocan (Q9).

Si alguno no está claro — investigar más, no avanzar.
