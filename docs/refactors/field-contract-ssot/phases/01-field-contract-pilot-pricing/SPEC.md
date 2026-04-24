# Fase 01 — FieldContract pilot (pricing)

## Objetivo

Introducir `FieldContract` BE. Migrar sección **pricing** al patrón. Cerrar Capa A pricing: los 3 fields huérfanos (`tax_included`, `installments_available`, `accepted_payment_providers`) pasan a persistir + propagarse downstream.

## Scope

**Dentro**:
- `backend/src/modules/offer/domain/field_contract.py` con dataclass + registry para pricing
- Migration idempotente para 3 columnas nuevas
- `Offer` Pydantic extendido (3 fields)
- `OfferPricingUpdate` variant DTO
- Extraction wave schema + prompt (pricing vive en closing wave o propia wave? Decidir al abrir fase con knowledge fresco — ver `offer_extraction_orchestrator.py`)
- Endpoint `GET /api/v1/offer/field-contract` versionado
- Regenerar `offer_field_paths.json` con nuevos paths (post migration)
- `pricing.schema.ts` tipa `path` contra codegen → TSC error si inventa
- Arch test allowlist shrinks (3 paths removidos)
- Sales-agent prompt template agrega bloque pricing condicional
- Landing builder consume nuevos fields si presentes
- Golden fixture ACTUALIZA baseline (nuevo baseline post-migration)
- Tests round-trip persistencia: PATCH `tax_included=true` → GET retorna true

**Fuera**:
- Otras secciones
- `OFFER_FIELDS_BY_FE_SECTION` cleanup
- Refactor `PricingStructure`

## Análisis requerido al abrir fase

Tomarse 10-15 min al arrancar:

1. Leer `backend/src/modules/offer/application/offer_extraction_orchestrator.py` — cómo estructurar prompt pricing (wave propia vs ampliar closing wave)
2. Leer `backend/src/modules/sales_agent/infrastructure/prompts/templates/agent_identity.j2` — dónde insertar bloque pricing additive
3. Leer `backend/src/modules/landing/application/landing_content_builders.py` — dónde consumir
4. Leer `backend/src/modules/offer/application/services/offer_completion_service.py` — si pricing needs actualización completion rules
5. Research breve: Pydantic introspection patterns para codegen paths — `model_fields` iteration, recursion con polymorphic (ya hecho en Fase 00 script, reutilizar)
6. Research breve: LATAM tax standards — IVA/IGV/ICMS variants, installments cultural: Brasil 12x, Argentina 3x/6x/12x sin interés, México MSI

Al terminar análisis, concretá sub-steps y actualizá este SPEC si hace falta refinamiento.

## Duración estimada

1 sprint (~3-5 días de trabajo efectivo, dividido en ~5-8 commits atómicos).

## Riesgo

Medio. Primera migration real del refactor. Tests golden + round-trip protegen.

## Definition of Done

Ver ACCEPTANCE.md (se escribe al arrancar la fase con sub-steps definidos).
