# Plan — 6 fases frozen

Cambios al plan requieren entry en [DECISIONS.md](DECISIONS.md) con
razón fuerte y ADR-NNN.

## Overview

```
Fase 04  Platform foundation       FieldContract en shared/ + offer end-to-end
Fase 05  Downstream data-driven    Sales-agent + landing + completion consumen contract
Fase 06  Brand migration           Brand pasa a derivación
Fase 07  Buyer migration           Buyer-persona pasa a derivación
Fase 08  Copilot unification       Read+write surfaces unificadas en FieldContract
Fase 09  Multi-channel projection  Web + whatsapp + telegram desde mismo contract
```

Cada fase mantiene UX byte-identical por contrato.

## Fase 04 — Platform foundation

**Objetivo**: dejar `FieldContract` cross-module en `shared/domain/`
y migrar offer 100% (cierra los 5 registries paralelos en offer).

**Deliverables**:
- `shared/domain/field_contract.py` con dataclass extendido + derivación
  Pydantic + module registry + accessors + helpers (fields_by_section,
  find_contract).
- `shared/domain/field_contract_types.py` con `FieldType`, `FieldStatus`,
  `FieldContractOverride` enums/dataclass.
- `offer/domain/field_contract.py` migrado: declara `OFFER_SECTION_MAP` +
  `OFFER_FIELD_OVERRIDES` + deriva `OFFER_FIELD_CONTRACTS` de `Offer.model_fields`.
- `offer/domain/copilot_editable_fields.py` deriva.
- `copilot/domain/offer_fields.py::PERSISTABLE_FIELDS` deriva.
- `offer/domain/extraction_section_map.py::OFFER_FIELDS_BY_FE_SECTION`
  borrado. `fields_to_fe_sections()` consume `shared.fields_by_section()`.
- Arch tests cross-cutting:
  - `Pydantic ⊆ FieldContract` per migrated module.
  - `editable_fields ⊆ FieldContract`.
  - `PERSISTABLE_FIELDS ⊆ FieldContract`.
  - `FE schema paths ⊆ FieldContract`.
  - Anti-regression: `OFFER_FIELDS_BY_FE_SECTION` no puede reaparecer.
- Endpoint `/api/v1/offer/field-contract` JSON shape preservado.
- Golden snapshot offer `a96403b5...` byte-identical.

**Out of scope**:
- Brand/buyer/copilot migration (Fases 06/07/08).
- Sales-agent / landing data-driven (Fase 05).
- Multi-channel projection (Fase 09).
- Schemas FE no se tocan.

**Duración estimada**: 1 sesión larga (10 commits atómicos).

**Riesgo**: Medio. Pydantic introspección recursiva + lifecycle metadata
+ múltiples consumers a derivar.

**Mitigación**: golden snapshots por consumer, tests existentes preservados,
arch tests que fuerzan paridad.

## Fase 05 — Sales-agent + landing + completion data-driven

**Objetivo**: que los consumers downstream consuman `FieldContract`
directamente. Agregar un field nuevo al contract → aparece auto en
sales-agent prompt + landing + completion.

**Deliverables**:
- `sales_agent/application/knowledge_builder.py` consume
  `get_module_contracts("offer")` para iterar fields. Ordena por
  `(section, priority)`. Filtra `status == ACTIVE`. Skip si valor vacío.
- `agent_identity.j2` template render data-driven (no más `{% if offer.X %}`
  hardcoded por field).
- `landing/application/services/landing_content_builders.py` consume
  contract para proyectar copy.
- `offer/application/services/offer_completion_service.py` calcula %
  con `is_required_semantic` del contract.
- Tests golden: `agent_identity.j2` rendered + `landing/output` byte-identical
  vs baseline pre-fase-05 para offer `a96403b5...`.

**Pre-investigación**:
- Inventario de `{% if offer.X %}` en `agent_identity.j2`.
- Inventario de `landing_content_builders` que leen offer fields.
- Mapping legacy completion → `is_required_semantic`.
- Identificar fields hoy renderizados que no tienen entry en `FieldContract`
  (esos son tech debt: extender contract).

**Riesgo**: Medio. Tests golden protegen outputs críticos.

## Fase 06 — Brand migration

**Objetivo**: brand adopta el patrón. `BRAND_EDITABLE_FIELDS` deriva.
`BrandSettings` (Pydantic) ⊆ FieldContract registry.

**Deliverables**:
- `brand/domain/field_contract.py` con `BRAND_SECTION_MAP` + `BRAND_FIELD_OVERRIDES`.
- `BRAND_FIELD_CONTRACTS = derive_contracts_from_pydantic(...)`.
- `brand/domain/copilot_editable_fields.py` proyecta del contract.
- Arch test brand: `Pydantic ⊆ FieldContract`, `editable_fields ⊆ FieldContract`.
- Golden snapshots: `brand_settings_baseline.md` byte-identical pre/post.

**Pre-investigación**:
- Inventario completo `BrandSettings` Pydantic (identity, story, narrative,
  positioning, personality, strategy, team, communication_assets).
- Diff `BRAND_EDITABLE_FIELDS` (manual ~70 entries) vs `BrandSettings.model_fields`
  → identificar drift.
- Verificar que copilot conversaciones existentes siguen funcionando:
  test acceptance que ejercita `propose_field_updates` para brand.

**Coordinar con**: `project_brand_studio_refactor.md` activo. Asegurar
no-conflicto.

**Riesgo**: Bajo (patrón validado en Fase 04). Cuidar que la lista
de FieldSpec emitida sea equivalente para no romper system prompt.

## Fase 07 — Buyer-persona migration

**Objetivo**: idem brand para buyer-persona.

**Deliverables**:
- `buyer_persona/domain/field_contract.py` con SECTION_MAP + OVERRIDES.
  (Nota: hoy `buyer_persona` vive como aggregate dentro de `brand/domain/`.
  Confirmar en pre-investigación si conviene crear módulo BE separado o
  mantener.)
- Derivación.
- Arch tests.

**Pre-investigación**:
- Confirmar dónde vive el modelo Pydantic actual de `BuyerPersona`.
- Verificar interaction con brand-studio refactor.

**Riesgo**: Bajo.

## Fase 08 — Copilot read+write unification

**Objetivo**: eliminar duplicación interna del copilot. `editable_fields`
port + `schema_introspection` consumen `FieldContract` cross-module.
Reduce 2 SSoT a 1.

**Deliverables**:
- `shared/links/ports/editable_fields.py` rewriteado: `get_catalog(domain)`
  proyecta de `get_module_contracts(domain)` con filtro `can_propose=True`.
  Mantiene shape `FieldSpec` por backward-compat o se promueve consumers
  a leer `FieldContract` directo.
- `copilot/domain/schema_introspection.py` simplificado: `get_model_sections`,
  `validate_field_path` consumen `FieldContract` registry. La introspección
  Pydantic se reduce o se mueve a un helper dedicado.
- Tests acceptance copilot: chat tests existentes pasan idéntico.
- `copilot/domain/offer_fields.py::PERSISTABLE_FIELDS` ya derivada en Fase 04.
  En Fase 08 evaluar si seguir necesitando el archivo o promover consumer
  a leer `FieldContract` directamente.

**Pre-investigación**:
- Mapeo de TODOS los call sites de `get_catalog` y `schema_introspection`
  para entender qué shape esperan.
- Identificar dónde `propose_field_updates` valida paths — ese flujo
  debe seguir igual.

**Riesgo**: Medio-alto. Copilot está en producción. Tests acceptance
exhaustivos requeridos.

## Fase 09 — Multi-channel projection

**Objetivo**: el copilot conversacional whatsapp/telegram consume
`FieldContract` para preguntar naturalmente. La web sigue funcionando.

**Deliverables**:
- `copilot/application/orchestrator/conversational_questioning.py`:
  algoritmo `next_question(module, state)` que selecciona siguiente
  field por (priority, gate, missing).
- Integración con whatsapp/telegram channel adapters (donde estén o
  donde vivan en ese momento).
- Tests E2E channel-agnostic: mismo flow funciona en web + chat.
- Documentación copilot conversacional pattern.

**Pre-investigación**:
- Estado del copilot conversacional en ese momento (whatsapp ya integrado?
  telegram?). Esta fase asume que la infraestructura de channels está
  funcionando — solo agrega el algoritmo de questioning data-driven.
- Trade-offs: ¿el algoritmo decide preguntas o el LLM? Híbrido natural:
  algoritmo selecciona candidate fields (filtra por gate/missing), LLM
  decide el orden y formula la pregunta natural.

**Riesgo**: Alto. Producto y arquitectura interactúan. Probable spawn
de sub-fases.

## Reglas inquebrantables

Ver [INVARIANTS.md](INVARIANTS.md).

## Tech debt discovery

Si durante cualquier fase encontrás deuda técnica **relacionada al scope**,
la arreglás en la misma fase. Si es tangencial → entry en
`docs/mejoras-proceso/to-do.md`. **Nunca** posponer al final.

## Out of scope global

- Validación runtime de constraints (longitudes, regex, ranges) →
  vive en Pydantic + Zod FE.
- Internacionalización beyond español neutro LATAM → producto.
- Form-runtime UI patterns → FE-only.
- Tenant-specific overrides de fields → evaluar cuando aparezca demanda.
- Eliminar `editable_fields` port ⇒ evaluado en Fase 08.

## Métricas de éxito por fase

| Fase | Métrica |
|---|---|
| 04 | Cobertura `Pydantic Offer ⊆ FieldContract` = 100%. 0 registries paralelos en offer. Golden snapshot byte-identical. |
| 05 | Sales-agent + landing render data-driven. Golden snapshot byte-identical. |
| 06 | Cobertura `Pydantic Brand ⊆ FieldContract` = 100%. UX brand intacta. |
| 07 | Cobertura `Pydantic BuyerPersona ⊆ FieldContract` = 100%. |
| 08 | Copilot read+write surfaces consolidadas. Tests acceptance copilot verde. |
| 09 | Mismo flujo de captura funciona web + chat. |
