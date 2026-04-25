# Handoff — siguiente sesión Claude

> Prompt listo para pegar y arrancar la próxima fase. Generado al cerrar
> Fase 06 (`ed8a3a4f`). Sirve como anclaje para retomar el refactor sin
> reconstruir contexto desde cero.

## Cómo usar este doc

1. Pegá el prompt de **Fase 07** (abajo) en una nueva sesión Claude
   con working dir `/home/chris/AISALESHT`.
2. Claude lee `STATE.md` + protocolos + PRE_INVESTIGATION + SPEC de la
   fase activa antes de tocar código.
3. Cada commit atómico revertible. Commit final actualiza este HANDOFF
   con el prompt de la fase siguiente.

## Prompt — arrancar Fase 07 (Buyer-persona migration)

```
Retomamos refactor field-contract-platform.

Workspace: docs/refactors/field-contract-platform/

Estado:
- Fase cerrada: 06-brand-migration (commits 61606fcf → ed8a3a4f)
- Fase activa: 07-buyer-migration (ready-to-start)
- Last green commit: ed8a3a4f
- Branch: development
- Working tree: limpio (3 ajenos: buyer-persona-ai-flow-verified.png,
  qa-extract-clean.png, docs/refactors/copilot-architecture/)
- Backend tests: 4261 pass · arch tests: 471

Protocolo de arranque obligatorio:

1. Leé en orden (5-10 min):
   - docs/refactors/field-contract-platform/STATE.md
   - docs/refactors/field-contract-platform/INVARIANTS.md
   - docs/refactors/field-contract-platform/PLAN.md §Fase 07
   - docs/refactors/field-contract-platform/DESIGN.md (escanear §2 capas
     + §2.5 proyecciones por consumer + §2.6 tests cross-cutting)
   - docs/refactors/field-contract-platform/LEARNINGS.md (cross-cutting
     + Fases 04-06, especialmente §Fase 06 →Para Fase 07 + dict subkeys)
   - docs/refactors/field-contract-platform/DECISIONS.md (ADR-011..017)
   - docs/refactors/field-contract-platform/phases/07-buyer-migration/PRE_INVESTIGATION.md
   - docs/refactors/field-contract-platform/phases/07-buyer-migration/SPEC.md
   - docs/refactors/field-contract-platform/protocol/RESUME.md

2. Pre-investigación obligatoria (sin saltar — ADR-017):
   - Inventario `BuyerPersona.model_fields` (top-level: name, tagline,
     scope, offer_id, is_primary, demographics, psychographics, pain_points,
     desires, objections, preferred_channels, buyer_journey,
     purchase_triggers, anti_patterns, completeness_score, is_active +
     audit fields).
   - Inventario `BUYER_PERSONA_EDITABLE_FIELDS` (~12 entries en
     `brand/domain/copilot_editable_fields_buyer_persona.py`).
   - Inventario `_build_buyer_persona_paths` en
     `copilot/domain/schema_introspection.py` — set de paths válidos
     (top-level + dot-notation sub-keys conocidos como
     `demographics.age_range`, `psychographics.values`, etc.).
   - Decisión walker handling de dict sub-keys (BuyerPersona usa dict
     en demographics, psychographics, buyer_journey, pain_points, ...).
     LEARNINGS Fase 06 propone Patrón B: extender walker con
     `dict_subkeys: dict[str, tuple[str, ...]]`. Validar si vale la
     pena vs Patrón A (hand-author paths).
   - ¿Module file separado `buyer_persona/` o queda en `brand/`?
     PLAN.md sugiere virtual module bajo brand/. Decidir.
   - Drift audit BUYER_PERSONA_EDITABLE_FIELDS vs
     `_build_buyer_persona_paths` vs `BuyerPersonaPersister` accepted
     paths.
   - Coordinación con `project_brand_studio_refactor`: confirmar
     buyer-persona FE schema activo (sprint 2 ya deja buyer-persona
     schema en brand-studio).

3. Ejecutá protocol/PRE_FLIGHT.md (baseline tests + git status).

4. Escribir phases/07-buyer-migration/ACCEPTANCE.md con sub-steps
   atómicos y DoD per sub-step.

5. Scope Fase 07 (per PLAN.md):
   - `brand/domain/buyer_persona_field_contract.py` (o equivalente)
     con `BUYER_PERSONA_SECTION_MAP` + `BUYER_PERSONA_FIELD_OVERRIDES`.
   - Walker invocation. Si elegimos Patrón B: PR shared/ que extiende
     `derive_contracts_from_pydantic` con `dict_subkeys` arg ANTES de
     06.C buyer.
   - `register_module_contracts("buyer_persona", ...)`.
   - `_LAZY_REGISTRARS["buyer_persona"] = ...` en
     `shared/domain/field_contract.py`.
   - `BUYER_PERSONA_EDITABLE_FIELDS` proyectado del registry.
   - Extender `MIGRATED_MODULES = ("offer", "brand", "buyer_persona")`.
   - Agregar `_buyer_persona_spec()` en
     `test_field_contract_platform_module_template.py`.
   - Tests específicos buyer-persona (Pydantic ⊆ contract, ratchet
     anti-regression similar al de brand).

6. Out of scope:
   - Brand re-migration (Fase 06 done, no reabrir).
   - Copilot unification (Fase 08).
   - Multi-channel projection (Fase 09).
   - Schemas FE no se tocan.
   - Diferidos de Fase 05 (full data-driven loop, completion alignment,
     landing aggregate migration).

7. Commits atómicos sugeridos (definitivo en SPEC + ACCEPTANCE):
   - a) baseline golden buyer-persona snapshot + ACCEPTANCE.
   - b) (opcional) walker shared extension `dict_subkeys` arg + tests
     unit + arch tests previos siguen verde.
   - c) buyer-persona FieldContract module (section_map + overrides +
     derive + register).
   - d) BUYER_PERSONA_EDITABLE_FIELDS proyectado del registry.
   - e) MIGRATED_MODULES bumped + buyer-persona pydantic coverage.
   - f) tech debt en scope (anti-regression buyer ratchet test).
   - g) close: LEARNINGS + STATE/STATUS bump + Fase 08 ready.

8. Al cerrar fase:
   - POST_FLIGHT.md
   - STATE.md → active_phase=08, last_green_commit
   - STATUS.md Fase 07 done + Fase 08 ready
   - LEARNINGS.md append Fase 07
   - HANDOFF.md actualizado con prompt Fase 08
   - Generáme el prompt para arrancar Fase 08.

Reglas inquebrantables:
- Cada commit revertible atómico · rama development · stage por nombre · no tocar ajenos
- Tech debt del scope = arreglar en la fase; tangencial a TODO.md
- Spanish neutro LATAM · TDD · UX byte-identical
- Buyer-persona → derivation pattern (ADR-012). Override pattern para
  metadata semántica.
- Si descubrís gap arquitectónico, ADR + replanteo, no hack.
- No reabrir Fases 04-06 (cerradas). Diferidos documented en LEARNINGS;
  pueden tomarse en una fase 09+ dedicada.

Parallel sessions pueden estar corriendo — antes de commitear,
git status --short; si hay ajenos dejalos.

Empezá.
```

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
