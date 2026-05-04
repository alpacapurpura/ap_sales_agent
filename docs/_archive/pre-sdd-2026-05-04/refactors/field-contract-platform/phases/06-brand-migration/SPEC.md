# Fase 06 — Brand migration

## Objetivo

Brand adopta el patrón de Fase 04. `BRAND_EDITABLE_FIELDS` deriva de
`FieldContract` registry. `BrandSettings` Pydantic ⊆ FieldContract.

## Scope

**Dentro**:
- `brand/domain/field_contract.py` con `BRAND_SECTION_MAP` +
  `BRAND_FIELD_OVERRIDES`.
- `BRAND_FIELD_CONTRACTS = derive_contracts_from_pydantic(model=BrandSettings, ...)`.
- `register_module_contracts("brand", BRAND_FIELD_CONTRACTS)`.
- `brand/domain/copilot_editable_fields.py` proyecta del contract.
- Arch tests brand: `Pydantic ⊆ FieldContract`, `editable_fields ⊆ FieldContract`.
- Golden: `brand_settings_baseline.md` byte-identical.

**Fuera**:
- Buyer migration (Fase 07).
- Copilot unification (Fase 08).
- Schemas FE brand no tocan.

## Coordinación

`project_brand_studio_refactor.md` activo. Sincronizar con su sprint
para no-conflicto.

## DoD

- [ ] BRAND_FIELD_CONTRACTS deriva.
- [ ] BRAND_EDITABLE_FIELDS proyectado equivalente al actual.
- [ ] Cobertura `BrandSettings.model_fields ⊆ FieldContract` = 100%.
- [ ] Copilot conversaciones brand pre-refactor funcionan idéntico.
- [ ] Tests verde.
