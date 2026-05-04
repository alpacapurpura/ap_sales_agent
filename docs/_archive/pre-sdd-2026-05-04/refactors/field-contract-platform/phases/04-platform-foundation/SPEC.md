# Fase 04 — Platform foundation

## Objetivo

Promover `FieldContract` a `shared/domain/`. Migrar offer 100%
(elimina drift entre los 5 registries paralelos). Brand/buyer/copilot
intactos. UX byte-identical.

## Scope

**Dentro**:
- `shared/domain/field_contract.py` con dataclass extendido (estructura
  + filtros + lifecycle + copilot meta).
- `shared/domain/field_contract_types.py` con `FieldType`, `FieldStatus`,
  `FieldContractOverride`.
- Walker `derive_contracts_from_pydantic(model, section_map, overrides, ignore)`.
- Module registry shared con accessors públicos.
- `offer/domain/field_contract.py` migrado: `OFFER_SECTION_MAP` + `OFFER_FIELD_OVERRIDES`
  + derivación. `OFFER_FIELD_CONTRACTS` deriva de `Offer.model_fields`.
- `offer/domain/copilot_editable_fields.py` proyecta del registry.
- `copilot/domain/offer_fields.py::PERSISTABLE_FIELDS` proyecta.
- `offer/domain/extraction_section_map.py::OFFER_FIELDS_BY_FE_SECTION`
  borrado. `fields_to_fe_sections()` consume `shared.fields_by_section()`.
- Endpoint `/api/v1/offer/field-contract` shape preservado.
- Arch tests cross-cutting que fuerzan paridad.

**Fuera**:
- Brand/buyer/copilot migration.
- Sales-agent + landing data-driven (Fase 05).
- Multi-channel projection (Fase 09).
- Schemas FE no se tocan.

## Sub-steps (10 commits atómicos)

| ID | Commit | Output |
|---|---|---|
| 04.A | docs workspace + ADRs | `docs/refactors/field-contract-platform/` completo (este, README, DESIGN, INVARIANTS, PLAN, DECISIONS, STATE, LEARNINGS, protocol/, phases/) |
| 04.B | feat(shared) FieldContract platform core | `shared/domain/field_contract.py` + `field_contract_types.py` + unit tests |
| 04.C | refactor(offer) migrate to shared | `offer/domain/field_contract.py` declara mapping + overrides + deriva. Endpoint shape preservado |
| 04.D | refactor(offer) fields_by_section derives | `extraction_section_map.fields_to_fe_sections` consume util shared. Tests pass |
| 04.E | refactor(offer) copilot_editable_fields derives | `offer/domain/copilot_editable_fields.py` proyecta. Catalog equivalente |
| 04.F | refactor(copilot) PERSISTABLE_FIELDS derives | `copilot/domain/offer_fields.py` deriva |
| 04.G | chore(offer) drop OFFER_FIELDS_BY_FE_SECTION | Borrado. Arch test anti-regression |
| 04.H | test(arch) cross-cutting field contract guards | Cobertura tests |
| 04.I | test(arch) generic guards future modules | Tests preparados (no-ops para módulos no migrados) |
| 04.J | chore close phase + handoff | LEARNINGS, STATE, STATUS done, HANDOFF.md |

## DoD

- [ ] Pydantic Offer ⊆ FieldContract = 100% paths user-facing (excepto ignore_paths).
- [ ] `OFFER_EDITABLE_FIELDS` registrado idéntico (o superior, cierra drift) al actual.
- [ ] `PERSISTABLE_FIELDS` set idéntico al actual.
- [ ] `fields_to_fe_sections` output idéntico al pre-refactor para casos
      tested en `test_offer_extraction_section_map.py`.
- [ ] Endpoint `/api/v1/offer/field-contract` JSON snapshot match.
- [ ] Backend test suite verde (`pytest`).
- [ ] Frontend arch tests verde.
- [ ] Golden offer `a96403b5...` snapshot byte-identical (si aplica).
- [ ] `OFFER_FIELDS_BY_FE_SECTION` ya no existe en el codebase.
- [ ] Brand `BRAND_EDITABLE_FIELDS` no fue tocado.
- [ ] Buyer `BUYER_PERSONA_EDITABLE_FIELDS` no fue tocado.
- [ ] HANDOFF.md generado con prompt Fase 05.
- [ ] LEARNINGS.md actualizado.

## Riesgos identificados

| Riesgo | Mitigación |
|---|---|
| Pydantic introspección frágil con `Optional[X]`, `list[X]`, custom types | Reuso `copilot.schema_introspection.unwrap_optional`. Tests cubren edge cases |
| Composables (`PlatformDetails`, `specific_details.*`) shape al derivar | Walker recursivo + override explícito. Existing codegen `generate_offer_field_paths.py` ya maneja esto correcto — patrón reutilizable |
| `FieldSpec` registrado cambia shape sutilmente | Snapshot test del catalog antes/después. Solo agregar fields no-presentes (cierra drift) |
| Endpoint `/field-contract` rompe contrato FE | Test snapshot del JSON. Si shape cambia → adapter en endpoint que preserve forma vieja |
| Tests existentes que importan `OFFER_FIELDS_BY_FE_SECTION` fallan | Migran en mismo commit que borra (04.G) |
| Test extraction grouping output cambia | Tests existentes en `test_offer_extraction_section_map.py` mantienen comportamiento (firma del consumer no cambia) |
| Pydantic `discriminator` o `Annotated` no soportados por walker | Edge cases documentados; fallback explícito |
