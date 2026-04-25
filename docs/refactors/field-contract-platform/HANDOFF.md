# Handoff — siguiente sesión Claude

> Prompt listo para pegar y arrancar la próxima fase. Generado al cerrar
> Fase 05 (`d0d121f1`). Sirve como anclaje para retomar el refactor sin
> reconstruir contexto desde cero.

## Cómo usar este doc

1. Pegá el prompt de **Fase 06** (abajo) en una nueva sesión Claude
   con working dir `/home/chris/AISALESHT`.
2. Claude lee `STATE.md` + protocolos + PRE_INVESTIGATION + SPEC de la
   fase activa antes de tocar código.
3. Cada commit atómico revertible. Commit final actualiza este HANDOFF
   con el prompt de la fase siguiente.

## Prompt — arrancar Fase 06 (Brand migration)

```
Retomamos refactor field-contract-platform.

Workspace: docs/refactors/field-contract-platform/

Estado:
- Fase cerrada: 05-downstream-data-driven (commits 94036809 → d0d121f1)
- Fase activa: 06-brand-migration (ready-to-start)
- Last green commit: d0d121f1
- Branch: development
- Working tree: limpio (3 ajenos: buyer-persona-ai-flow-verified.png,
  qa-extract-clean.png, docs/refactors/copilot-architecture/)
- Backend tests: 4217+ pass · arch tests: 453

Protocolo de arranque obligatorio:

1. Leé en orden (5-10 min):
   - docs/refactors/field-contract-platform/STATE.md
   - docs/refactors/field-contract-platform/INVARIANTS.md
   - docs/refactors/field-contract-platform/PLAN.md §Fase 06
   - docs/refactors/field-contract-platform/DESIGN.md (escanear §2 capas
     + §2.5 proyecciones por consumer + §2.6 tests cross-cutting)
   - docs/refactors/field-contract-platform/LEARNINGS.md (cross-cutting
     + Fases 04-05)
   - docs/refactors/field-contract-platform/DECISIONS.md (ADR-011..017)
   - docs/refactors/field-contract-platform/phases/06-brand-migration/PRE_INVESTIGATION.md
   - docs/refactors/field-contract-platform/phases/06-brand-migration/SPEC.md
   - docs/refactors/field-contract-platform/protocol/RESUME.md

2. Pre-investigación obligatoria (sin saltar — ADR-017):
   - Inventario completo de `BrandSettings.model_fields` + nested sub-models
     (identity, story, narrative, positioning, personality, strategy, team,
     communication_assets, buyer_persona). Confirmar path real de cada master.
   - Lista section catalog brand (`brand/domain/section_catalog.py`).
   - Drift audit completo: diff entre `BRAND_EDITABLE_FIELDS` (~70 entries)
     y `BrandSettings.model_fields` user-facing. Esperado: drift confirmable.
   - Decisión buyer-persona scope: bloqueante para Fase 06+07. ¿Aggregate
     dentro de brand registry o módulo separado en Fase 07?
   - Coordinación con `project_brand_studio_refactor` activo: leer la
     memoria, confirmar sprint en curso, no-conflict scope.

3. Ejecutá protocol/PRE_FLIGHT.md (baseline tests + git status).

4. Escribir phases/06-brand-migration/ACCEPTANCE.md con sub-steps
   atómicos y DoD per sub-step.

5. Scope Fase 06 (per PLAN.md):
   - `brand/domain/field_contract.py` con `BRAND_SECTION_MAP` +
     `BRAND_FIELD_OVERRIDES` siguiendo el patrón offer.
   - `derive_contracts_from_pydantic(model=BrandSettings, ...)` +
     `register_module_contracts("brand", ...)`.
   - `BRAND_EDITABLE_FIELDS` proyectado del registry.
   - Extender `MIGRATED_MODULES` en arch tests:
     - `tests/architecture/test_field_contract_platform_coverage.py`
     - `tests/architecture/test_field_contract_platform_module_template.py`
   - Validar que las 5 fitness gates genéricas pasan automáticamente
     gracias a 04.I.

6. Out of scope:
   - Buyer-persona migration (Fase 07).
   - Copilot unification (Fase 08).
   - Multi-channel projection (Fase 09).
   - Schemas FE no se tocan.
   - Diferidos de Fase 05 (full data-driven loop, completion alignment,
     landing aggregate migration). NO reabrir Fase 05.

7. Commits atómicos sugeridos (definitivo en SPEC + ACCEPTANCE):
   - a) baseline golden brand snapshot.
   - b) shared platform tests pre-brand (asserts MIGRATED_MODULES extension
     trivial + walker maneja brand polymorphic-if-applies).
   - c) brand FieldContract module (section_map + overrides + derive +
     register).
   - d) BRAND_EDITABLE_FIELDS proyectado del registry.
   - e) MIGRATED_MODULES bumped + arch tests verde.
   - f) tech debt en scope (drift fields, gaps).
   - g) close: LEARNINGS + STATE/STATUS bump + Fase 07 ready.

8. Al cerrar fase:
   - POST_FLIGHT.md
   - STATE.md → active_phase=07, last_green_commit
   - STATUS.md Fase 06 done + Fase 07 ready
   - LEARNINGS.md append Fase 06
   - HANDOFF.md actualizado con prompt Fase 07
   - Generáme el prompt para arrancar Fase 07.

Reglas inquebrantables:
- Cada commit revertible atómico · rama development · stage por nombre · no tocar ajenos
- Tech debt del scope = arreglar en la fase; tangencial a TODO.md
- Spanish neutro LATAM · TDD · UX byte-identical
- Brand → derivation pattern (ADR-012). Override pattern para metadata semántica.
- Si descubrís gap arquitectónico, ADR + replanteo, no hack.
- No reabrir Fase 05 (cerrada). Diferidos de 05 documented en LEARNINGS;
  pueden tomarse en una fase 09+ dedicada.

Parallel sessions pueden estar corriendo — antes de commitear,
git status --short; si hay ajenos dejalos.

Empezá.
```

## Prompt — arrancar Fase 07 (Buyer-persona migration)

Generar al cerrar Fase 06. Análogo a Fase 06 sobre `BuyerPersona`.
La decisión clave de Fase 06 (aggregate vs módulo separado) define el
scope de Fase 07.

## Prompt — arrancar Fase 08 (Copilot unification)

Pre-investigación más profunda: inventario `get_catalog` + `schema_introspection`
call sites + `propose_field_updates` flow + acceptance tests existentes
copilot. Riesgo medio-alto — copilot está en producción.

## Prompt — arrancar Fase 09 (Multi-channel projection)

Pre-investigación: estado producto channels (whatsapp/telegram), trade-off
algoritmo determinístico vs LLM creativo, compat web ↔ chat. Probable
spawn de sub-fases. Aquí también podría caber el work diferido de
Fase 05 (full data-driven loop en agent_identity, completion alignment,
landing aggregate migration).

## Notas para futuras sesiones

- **Cada fase tiene `PRE_INVESTIGATION.md` obligatorio** (ADR-017). No
  saltar — la lección de Fase 02 del workspace anterior está en el
  ADN del refactor.
- **Cada commit atómico revertible**. INVARIANT 3.
- **UX byte-identical durante migración**. INVARIANT 4. Si rompe golden
  snapshot, no es Fase 04+, es un bug.
- **No introducir nuevos registries paralelos**. INVARIANT 1. Cualquier
  consumer nuevo proyecta del FieldContract registry.
- **Brand y buyer NO se tocan** hasta su fase respectiva. INVARIANT 10.
- **Tech debt en scope se arregla en la misma fase**. INVARIANT 16.
- **Lifecycle versionado** (status/deprecated_in/replaced_by) para
  evitar breaking changes durante deprecaciones. ADR-013.
- **Diferidos de Fase 05** (loop data-driven full, completion alignment,
  landing aggregate) viven en LEARNINGS Fase 05 — NO reabrir Fase 05;
  cuando proceda, tomar en Fase 09 o phase dedicada.

## Contacto

Si necesitás contexto extra, todo está en
`docs/refactors/field-contract-platform/`. STATE.md siempre tiene la
verdad actual. LEARNINGS.md acumula descubrimientos. DECISIONS.md
acumula ADRs. PLAN.md es frozen — cambios requieren nueva ADR.
