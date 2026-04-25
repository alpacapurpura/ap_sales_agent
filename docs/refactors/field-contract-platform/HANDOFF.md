# Handoff — siguiente sesión Claude

> Prompt listo para pegar y arrancar la próxima fase. Generado al cerrar
> Fase 07 (`e4714606`). Sirve como anclaje para retomar el refactor sin
> reconstruir contexto desde cero.

## Cómo usar este doc

1. Pegá el prompt de **Fase 08** (abajo) en una nueva sesión Claude
   con working dir `/home/chris/AISALESHT`.
2. Claude lee `STATE.md` + protocolos + PRE_INVESTIGATION + SPEC de la
   fase activa antes de tocar código.
3. Cada commit atómico revertible. Commit final actualiza este HANDOFF
   con el prompt de la fase siguiente.

## Prompt — arrancar Fase 08 (Copilot unification)

```
Retomamos refactor field-contract-platform.

Workspace: docs/refactors/field-contract-platform/

Estado:
- Fase cerrada: 07-buyer-migration (commits 8394ecee → e4714606)
- Fase activa: 08-copilot-unification (ready-to-start)
- Last green commit: e4714606
- Branch: development
- Working tree: limpio (3 ajenos: buyer-persona-ai-flow-verified.png,
  qa-extract-clean.png, docs/refactors/copilot-architecture/)
- Backend tests: 4286+ pass · arch tests: 491 · shared platform: 23
- 3 módulos migrados al FieldContract platform: offer + brand + buyer_persona

Protocolo de arranque obligatorio:

1. Leé en orden (5-10 min):
   - docs/refactors/field-contract-platform/STATE.md
   - docs/refactors/field-contract-platform/INVARIANTS.md
   - docs/refactors/field-contract-platform/PLAN.md §Fase 08
   - docs/refactors/field-contract-platform/DESIGN.md (escanear §2.5
     proyecciones por consumer + §2.6 tests cross-cutting)
   - docs/refactors/field-contract-platform/LEARNINGS.md (cross-cutting
     + Fases 04-07, especialmente §Fase 07 →Para Fase 08 + diferidos
     scope Fase 08)
   - docs/refactors/field-contract-platform/DECISIONS.md (ADR-011..017)
   - docs/refactors/field-contract-platform/phases/08-copilot-unification/STATUS.md
   - docs/refactors/field-contract-platform/protocol/RESUME.md

2. Pre-investigación obligatoria (sin saltar — ADR-017):
   Crear phases/08-copilot-unification/PRE_INVESTIGATION.md
   inventariando:
   - Call sites de `get_catalog`, `validate_field_path`,
     `is_editable_path`, `get_model_sections`,
     `format_editable_field_catalog_markdown` (grep en src/ +
     tests/).
   - Flujo de `propose_field_updates` (copilot → validator → persister).
     Verificar paths: editable_fields port → schema_introspection →
     persister.
   - Tests acceptance copilot existentes que cubren el área (chat
     tests, propose_field_updates tests, interview persister tests).
   - Estado actual de `_DOMAIN_FIELD_CACHE`, `_DOMAIN_DICT_PARENTS`,
     `_DOMAIN_BUILDERS` en schema_introspection.
   - Estado de `copilot/domain/offer_fields.py::PERSISTABLE_FIELDS` —
     ya derivada en Fase 04, evaluar drop del archivo.
   - Coordinación: ningún consumer downstream depende del shape
     interno del cache.

3. Ejecutá protocol/PRE_FLIGHT.md (baseline tests + git status).

4. Crear phases/08-copilot-unification/SPEC.md con plan de migración
   editable_fields port + schema_introspection a derivación de
   `get_module_contracts(domain)` + lista de archivos a tocar.

5. Escribir phases/08-copilot-unification/ACCEPTANCE.md con sub-steps
   atómicos y DoD per sub-step.

6. Scope Fase 08 (per PLAN.md):
   - `shared/links/ports/editable_fields.py`: `get_catalog(domain)`
     proyecta de `get_module_contracts(domain)` con filtro
     `can_propose=True` + `status=ACTIVE` (cuando módulo migrado);
     fallback al hand-written catalog para módulos no migrados.
   - `copilot/domain/schema_introspection.py`:
     - `_build_offer_paths` consume `{c.path for c in
       get_module_contracts("offer")}`.
     - `_build_brand_paths` idem para brand.
     - `_build_buyer_persona_paths` idem para buyer_persona.
       Combinar con dict_subkeys parents derivados.
     - `_DOMAIN_DICT_PARENTS["buyer_persona"]` deriva de
       `BUYER_PERSONA_DICT_SUBKEYS.keys()` (o eliminar si validator
       pasa a strict).
     - `validate_field_path`: comportamiento idéntico via projection.
   - Evaluar drop de `copilot/domain/offer_fields.py` (consumers
     promueven a `get_module_contracts("offer")` directo).
   - Tests acceptance copilot existentes pasan idéntico.
   - Arch tests cross-cutting: cualquier shape derivado del
     FieldContract registry queda explícito.

7. Out of scope:
   - Fases 04-07 cerradas (no reabrir).
   - Multi-channel projection (Fase 09).
   - Reescritura masiva del prompt copilot (UX intacta).
   - Cambios en FE schemas (INVARIANT 9).
   - Diferidos de Fase 05 (full data-driven loop, completion alignment,
     landing aggregate migration) — siguen para Fase 09+ dedicada.

8. Commits atómicos sugeridos (definitivo en SPEC + ACCEPTANCE):
   - a) PRE_INVESTIGATION + SPEC + ACCEPTANCE + baseline acceptance
     copilot tests (golden snapshot si necesario).
   - b) `editable_fields` port `get_catalog` deriva de
     `get_module_contracts` cuando módulo migrado.
   - c) `schema_introspection` `_build_*_paths` consumen el registry.
   - d) (opcional) drop `copilot/domain/offer_fields.py` o
     simplificar.
   - e) Tests cross-cutting que enforzan derivation.
   - f) close: LEARNINGS + STATE/STATUS bump + Fase 09 ready.

9. Al cerrar fase:
   - POST_FLIGHT.md
   - STATE.md → active_phase=09, last_green_commit
   - STATUS.md Fase 08 done + Fase 09 ready
   - LEARNINGS.md append Fase 08
   - HANDOFF.md actualizado con prompt Fase 09
   - Generáme el prompt para arrancar Fase 09.

Reglas inquebrantables:
- Cada commit revertible atómico · rama development · stage por nombre · no tocar ajenos
- Tech debt del scope = arreglar en la fase; tangencial a TODO.md
- Spanish neutro LATAM · TDD · UX byte-identical
- Copilot está en producción — tests acceptance exhaustivos antes
  de tocar nada. Riesgo medio-alto.
- Si descubrís gap arquitectónico, ADR + replanteo, no hack.
- No reabrir Fases 04-07 (cerradas). Diferidos documented en LEARNINGS;
  pueden tomarse en una fase 09+ dedicada.

Parallel sessions pueden estar corriendo — antes de commitear,
git status --short; si hay ajenos dejalos.

Empezá.
```

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
- **Tech debt en scope se arregla en la misma fase**. INVARIANT 16.
- **Lifecycle versionado** (status/deprecated_in/replaced_by) para
  evitar breaking changes durante deprecaciones. ADR-013.
- **Diferidos de Fase 05** (loop data-driven full, completion alignment,
  landing aggregate) viven en LEARNINGS Fase 05 — NO reabrir Fase 05;
  cuando proceda, tomar en Fase 09 o phase dedicada.
- **Walker `dict_subkeys` arg** (Fase 07) habilita cualquier módulo
  futuro con JSONB sub-keys sin tocar shared. Pattern Patrón B
  validado.

## Contacto

Si necesitás contexto extra, todo está en
`docs/refactors/field-contract-platform/`. STATE.md siempre tiene la
verdad actual. LEARNINGS.md acumula descubrimientos. DECISIONS.md
acumula ADRs. PLAN.md es frozen — cambios requieren nueva ADR.
