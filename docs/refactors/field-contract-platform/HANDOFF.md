# Handoff — siguiente sesión Claude

> Prompt listo para pegar y arrancar la próxima fase. Generado al cerrar
> Fase 04 (`fc22f528`). Sirve como anclaje para retomar el refactor sin
> reconstruir contexto desde cero.

## Cómo usar este doc

1. Pegá el prompt de **Fase 05** (abajo) en una nueva sesión Claude
   con working dir `/home/chris/AISALESHT`.
2. Claude lee `STATE.md` + protocolos + PRE_INVESTIGATION + SPEC de la
   fase activa antes de tocar código.
3. Cada commit atómico revertible. Commit final actualiza este HANDOFF
   con el prompt de la fase siguiente.

## Prompt — arrancar Fase 05 (Downstream data-driven)

```
Retomamos refactor field-contract-platform.

Workspace: docs/refactors/field-contract-platform/

Estado:
- Fase cerrada: 04-platform-foundation (commits 5ba48682 → fc22f528)
- Fase activa: 05-downstream-data-driven (ready-to-start)
- Last green commit: fc22f528
- Branch: development
- Working tree: limpio (3 ajenos: buyer-persona-ai-flow-verified.png,
  qa-extract-clean.png, docs/refactors/copilot-architecture/)
- Backend tests: 4217 pass

Protocolo de arranque obligatorio:

1. Leé en orden (5-10 min):
   - docs/refactors/field-contract-platform/STATE.md
   - docs/refactors/field-contract-platform/INVARIANTS.md
   - docs/refactors/field-contract-platform/PLAN.md §Fase 05
   - docs/refactors/field-contract-platform/DESIGN.md (escanear §2 capas
     + §2.5 proyecciones por consumer + §2.6 tests cross-cutting)
   - docs/refactors/field-contract-platform/LEARNINGS.md (cross-cutting
     + Fase 04)
   - docs/refactors/field-contract-platform/DECISIONS.md (ADR-011..017)
   - docs/refactors/field-contract-platform/phases/05-downstream-data-driven/PRE_INVESTIGATION.md
   - docs/refactors/field-contract-platform/phases/05-downstream-data-driven/SPEC.md
   - docs/refactors/field-contract-platform/protocol/RESUME.md

2. Pre-investigación obligatoria (sin saltar — lección de Fase 02 del
   workspace anterior + ADR-017):
   - Inventario completo de `{% if offer.X %}` en
     `backend/src/modules/sales_agent/.../prompts/agent_identity.j2`
     y otros templates sales-agent. Documentar field + lógica.
   - Inventario de `landing_content_builders.py` — qué fields lee,
     qué transforma, layout de output.
   - Mapping `offer_completion_service.py` legacy → `is_required_semantic`
     en FieldContract. Identificar fields hoy required-for-completion
     que no tienen el override seteado.
   - Identificar fields renderizados pero sin entry en FieldContract.
     Si encontrás → tech debt: extender FieldContract en commit dedicado
     dentro de Fase 05 (NO postpone).
   - Capturar baseline golden offer `a96403b5-c1db-4b31-97aa-cb18d08ad9f9`
     pre-Fase 05: agent_identity.j2 rendered + landing output.

3. Ejecutá protocol/PRE_FLIGHT.md (baseline tests + git status).

4. Escribir phases/05-downstream-data-driven/ACCEPTANCE.md con sub-steps
   atómicos y DoD per sub-step.

5. Scope Fase 05:
   - sales_agent/application/knowledge_builder.py consume
     get_module_contracts("offer") iterando por (section, priority).
     Filtra status=ACTIVE, skip si valor vacío. Render data-driven.
   - agent_identity.j2 template render data-driven (loop sobre contracts,
     no `{% if offer.X %}` hardcoded).
   - landing/application/services/landing_content_builders.py consume
     contract para proyectar copy.
   - offer/application/services/offer_completion_service.py calcula
     % completed con `is_required_semantic`.
   - Tests golden agent_identity rendered + landing output byte-identical
     vs baseline pre-Fase 05.

6. Out of scope:
   - Brand/buyer migration (Fase 06/07).
   - Copilot unification (Fase 08).
   - Multi-channel projection (Fase 09).
   - Schemas FE no se tocan.

7. Commits atómicos sugeridos (definitivo en SPEC + ACCEPTANCE):
   - a) baseline golden snapshot capturado.
   - b) knowledge_builder consume contract + tests.
   - c) agent_identity.j2 render data-driven + tests golden.
   - d) landing_content_builders consume contract + tests golden.
   - e) completion_service consume is_required_semantic + tests.
   - f) tech debt: fields renderizados sin entry → extend contract.
   - g) close: LEARNINGS + STATE/STATUS bump + Fase 06 ready.

8. Al cerrar fase:
   - POST_FLIGHT.md
   - STATE.md → active_phase=06, last_green_commit
   - STATUS.md Fase 05 done + Fase 06 ready
   - LEARNINGS.md append Fase 05
   - HANDOFF.md actualizado con prompt Fase 06
   - Generáme el prompt para arrancar Fase 06.

Reglas inquebrantables:
- Cada commit revertible atómico · rama development · stage por nombre · no tocar ajenos
- Tech debt del scope = arreglar en la fase; tangencial a TODO.md
- Spanish neutro LATAM · TDD · UX byte-identical
- Fase 04 cerró 5 registries paralelos en offer; mantenerlo así (no introducir nuevos)
- Brand y buyer NO se tocan en Fase 05
- Si descubrís gap arquitectónico, ADR + replanteo, no hack

Parallel sessions pueden estar corriendo — antes de commitear,
git status --short; si hay ajenos dejalos.

Empezá.
```

## Prompt — arrancar Fase 06 (Brand migration)

Generar al cerrar Fase 05. Plantilla similar al de Fase 05, ajustada a:
- Pre-investigación: inventario `BrandSettings` Pydantic + drift audit
  vs `BRAND_EDITABLE_FIELDS` (~70 entries hand-written) +
  coordinación con `project_brand_studio_refactor` activo.
- Scope: `brand/domain/field_contract.py` + section_map + overrides +
  derivación + `register_module_contracts("brand", ...)` +
  `BRAND_EDITABLE_FIELDS` proyectado.
- Tests: extender MIGRATED_MODULES + spec brand en
  `test_field_contract_platform_module_template.py`.

## Prompt — arrancar Fase 07 (Buyer-persona migration)

Análogo a Fase 06 sobre `BuyerPersona`. Decidir en pre-investigación
si se separa a su propio módulo BE o queda como aggregate dentro de
brand.

## Prompt — arrancar Fase 08 (Copilot unification)

Pre-investigación más profunda: inventario `get_catalog` + `schema_introspection`
call sites + `propose_field_updates` flow + acceptance tests existentes
copilot. Riesgo medio-alto — copilot está en producción.

## Prompt — arrancar Fase 09 (Multi-channel projection)

Pre-investigación: estado producto channels (whatsapp/telegram), trade-off
algoritmo determinístico vs LLM creativo, compat web ↔ chat. Probable
spawn de sub-fases.

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

## Contacto

Si necesitás contexto extra, todo está en
`docs/refactors/field-contract-platform/`. STATE.md siempre tiene la
verdad actual. LEARNINGS.md acumula descubrimientos. DECISIONS.md
acumula ADRs. PLAN.md es frozen — cambios requieren nueva ADR.
