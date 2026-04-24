# Fase 00 — Guardrail

## Objetivo

Arch test que rechaza cualquier schema FE con `path` que no exista en BE domain. Allowlist temporal para deuda actual (9 paths Capa A + B). Golden fixture offer real como salvaguarda anti-regresión.

## Scope

**Dentro**:
- Script BE que genera JSON con paths válidos (`Offer` Pydantic + `{Archetype}Details`)
- Endpoint BE `GET /api/v1/offer/field-paths` (solo dev, nota: no exponer paths en prod si sensible)
- Codegen alt: script invocable en build step FE o test runtime
- Arch test FE que AST-parsea `*.schema.ts` de offer-studio + compara con JSON
- Allowlist inicial (9 paths + razón cada uno)
- Golden fixture `fixtures/offer_a96403b5_baseline.md` con snapshot offer real
- Test `backend/tests/modules/offer/test_offer_a96403b5_baseline.py` que valida DB state + rendered sales-agent prompt + landing output

**Fuera**:
- Migration
- Cambio `Offer` Pydantic domain
- Cambio schemas FE (solo agregan TS types, no fields)
- Touch sales-agent template
- Touch landing builder

## Sub-steps

### Sub-step 1/5 — Golden baseline offer real

**Pre**: PRE_FLIGHT.md.

**Pensar primero**:
- ¿Qué información captura el snapshot?
  - DB: `Offer.model_dump(exclude_none=True)` del offer
  - Rendered sales-agent prompt: ejecutar `KnowledgeBuilder` + render `agent_identity.j2` con ese offer → string final
  - Rendered landing output: ejecutar `landing_service.generate_landing_for_offer` dry-run → `LandingPageConfig.model_dump()`
- ¿Qué excluir para no tener flakiness?
  - Timestamps (created_at, updated_at)
  - UUIDs de relaciones (si cambian por re-run tests)
  - Campos que nacen null y pueden llenarse por background job

**Hacer**:
- `backend/tests/modules/offer/fixtures/offer_a96403b5_baseline.json` con el snapshot
- `backend/tests/modules/offer/test_offer_a96403b5_baseline.py` con test golden que:
  1. Obtiene offer actual DB (si existe) o usa fixture estática si no
  2. Compara `model_dump(exclude={timestamps})` vs baseline
  3. Comparar prompt render
  4. Comparar landing output
- Si test falla hoy por offer state distinto → snapshot se CREA con el estado actual. Baseline es el state actual.
- Documentar en `fixtures/offer_a96403b5_baseline.md` cómo regenerar baseline si cambio arquitectónico justificado

**Commit**: `test(offer): golden fixture for referenced offer a96403b5`

### Sub-step 2/5 — BE paths generator

**Pensar**:
- ¿Dónde vive el script? `backend/scripts/` (ya existe precedente `generate_extraction_contract_doc.py`)
- ¿Cómo enumero paths Pydantic? Iterar `Offer.model_fields` + recurse en `{Archetype}Details` por `ARCHETYPE_TO_DETAILS_MAPPING`
- Formato output: JSON plano con lista de strings. Nested: `"specific_details.program_details.weekly_time_commitment_hours"` o `"specific_details.weekly_time_commitment_hours"` (menos acoplado al archetype, porque polimórfico runtime)
- Decisión: paths flat con prefix `specific_details.{field}` asumiendo union de todas las subclases — cada archetype tiene subset visible.

**Hacer**:
- `backend/scripts/generate_offer_field_paths.py`:
  ```
  Enumera Offer.model_fields + specific_details.* union de {Archetype}Details.
  Output: backend/tests/architecture/fixtures/offer_field_paths.json
  ```
- Archivo JSON generado y committeado (para determinismo en CI sin dep Python en runner FE)
- Makefile target `make offer-field-paths` (opcional, o instrucción en script header)

**Commit**: `chore(offer): script to generate BE field paths JSON`

### Sub-step 3/5 — Arch test FE paths-resolve

**Pensar**:
- ¿Dónde vive el test? `frontend/src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts`
- ¿Cómo parseo `*.schema.ts`? Opciones:
  - Runtime import (Vitest puede importar TS) → inspecciona objeto schema exportado. ✅ simple.
  - AST (ts-morph): robusto pero heavy. ❌
- Decisión: runtime import. El schema FE ya es objeto exportado.
- Allowlist inicial: Set<string> con 9 paths + comentario razón cada uno.

**Hacer**:
- Test itera todos los schemas en `frontend/src/features/offer-studio/schemas/*.schema.ts`
- Para cada `path` en cada `field` (incluyendo `itemSchema.fields[].path`) — valida:
  - Existe en `offer_field_paths.json`, O
  - Está en `KNOWN_UNRESOLVED_PATHS` allowlist
- Test falla con mensaje claro: "Path `X` in {schema} not resolved. Add to Offer domain or allowlist with reason."
- Allowlist inicial comentada:
  ```ts
  const KNOWN_UNRESOLVED_PATHS = new Set<string>([
    "tax_included",                             // Fase 01 — Pricing LATAM
    "installments_available",                   // Fase 01 — Pricing LATAM
    "accepted_payment_providers",               // Fase 01 — Pricing LATAM
    "authority_positioning_for_sales",          // Fase 02 — Authority block
    "authority_notes",                          // Fase 02 — Authority block
    "total_perceived_value_anchor",             // Fase 02 — Value-stack anchor
    "stack_positioning_statement",              // Fase 02 — Value-stack anchor
    "specific_details.weekly_time_commitment_hours",  // Fase 02 — Program narratives
    "specific_details.prerequisites_text",      // Fase 02 — Program narratives
  ]);
  ```

**Commit**: `test(offer-studio): arch test FE schema paths resolve to BE domain`

### Sub-step 4/5 — Smoke test: allowlist shrink-only

**Pensar**: la allowlist puede crecer accidentalmente. Test arch que verifica que allowlist tiene máximo 9 elementos (shrink-only ratchet).

**Hacer**:
- En mismo test file: assertion `expect(KNOWN_UNRESOLVED_PATHS.size).toBeLessThanOrEqual(9)`
- Comentario: "Shrink-only ratchet. Reduce as phases close. Never grow."

**Commit**: incluido en sub-step 3/5.

### Sub-step 5/5 — Docs + handoff

**Hacer**:
- Actualizar `docs/mejoras-proceso/to-do.md` con entry: `[ ] Reducir KNOWN_UNRESOLVED_PATHS en frontend/src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts a medida que fases 01-02 cierran`
- Update `fixtures/offer_a96403b5_baseline.md` con docs de cómo regenerar
- Update workspace: STATE.md + LEARNINGS.md + STATUS.md fase 00 + abrir fase 01 STATUS.md
- POST_FLIGHT.md full

**Commit**: `chore(refactor-field-contract): close phase 00`

## Archivos a tocar

```
backend/
  scripts/generate_offer_field_paths.py                         (new)
  tests/architecture/fixtures/offer_field_paths.json            (new, generated)
  tests/modules/offer/fixtures/offer_a96403b5_baseline.json     (new)
  tests/modules/offer/test_offer_a96403b5_baseline.py           (new)

frontend/
  src/__tests__/architecture/test-fe-schema-paths-resolve.test.ts  (new)

docs/
  refactors/field-contract-ssot/fixtures/offer_a96403b5_baseline.md  (new)
  mejoras-proceso/to-do.md                                          (append entry)
  refactors/field-contract-ssot/STATE.md                            (update per commit)
  refactors/field-contract-ssot/LEARNINGS.md                        (update al cierre)
  refactors/field-contract-ssot/phases/00-guardrail/STATUS.md       (update per commit)
  refactors/field-contract-ssot/phases/00-guardrail/COMMITS.md      (append per commit)
  refactors/field-contract-ssot/phases/00-guardrail/LEARNINGS.md    (complete al cierre)
  refactors/field-contract-ssot/phases/01-*/STATUS.md               (abrir al cierre)
```

## Duración estimada

2-3h (incluye pausas de análisis + golden fixture capture).

## Riesgo

Bajo. Zero runtime impact.

## Definition of Done

Ver [ACCEPTANCE.md](ACCEPTANCE.md).
