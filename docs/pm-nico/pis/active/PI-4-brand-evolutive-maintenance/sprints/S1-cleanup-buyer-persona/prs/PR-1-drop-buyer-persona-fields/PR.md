# PR-1-drop-buyer-persona-fields

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-1-drop-buyer-persona-fields |
| Sprint padre | S1-cleanup-buyer-persona |
| PI padre | PI-4-brand-evolutive-maintenance |
| Estado | in-progress |
| Tipo | refactor (cleanup schema + cross-stack) |
| Esfuerzo | M |
| Owner PM | /pm |
| Claimed by session | builder BE + builder FE paralelo (claim 2026-04-29 post-architect, open questions resueltas) |

## Problema (user-facing)

Buyer Persona pide al user 2 fields que NO le sirven en su flujo Nicolify:
- **Objeciones** (qué frases usa el avatar para evitar comprar)
- **Canales preferidos** (dónde consume contenido)

Feedback Chris: usuarios no usan estos campos, distraen y agregan fricción al completar buyer persona. Ningún consumidor downstream los lee (verified Explore 2026-04-29).

## Outcome esperado

- Buyer Persona form pierde 2 secciones (objections + preferred_channels)
- Form ~30% más corto en sección psychographics/journey
- `current-state/brand.md` refleja capabilities con lineage cleanup
- Sin regresión: copilot extraction sigue funcional para fields restantes, sales_agent voice intacto, offer.objections (módulo distinto) intacto

## Walking skeleton (mínimo viable cohesivo)

PR único cross-stack que limpia las 8 capas en una sola pasada cohesiva:
1. Migration DROP COLUMN objections + preferred_channels (idempotente)
2. Domain entity (`buyer_persona.py`) sin fields
3. SQLAlchemy model sin columns
4. DTOs (request + response) sin fields
5. Repository sin referencias en updates
6. `_PROFILE_FIELDS` completeness sin fields
7. FieldContract overrides + section map sin entradas
8. Copilot persister `_LIST_FIELDS` + `_LIST_PATHS["buyer_persona"]` sin fields
9. Copilot extraction template j2 sin lines 26-27
10. Frontend schema + types sin fields
11. Tests baseline + fixtures actualizados

## Soluciones consideradas

| Opción | Pros | Contras | Veredicto |
|---|---|---|---|
| **A. PR único cross-stack cohesivo** | Cohesión, single migration, single deploy, blast-radius contenida | Requiere 2 builders paralelos (BE+FE) | **ELEGIDA** |
| B. Split BE-only PR + FE-only PR | Más chico cada uno | Migration deploy intermedia rompe FE; coordinación deploy doble | descartada — increases blast radius |
| C. Soft-delete (mantener column, ocultar UI) | Reversible | Deuda permanente, no limpia copilot extraction, datos obsoletos en JSONB | descartada — no resuelve problema raíz |

## Validación técnica preliminar (Technical Sanity Check)

Spawned `Explore` 2026-04-29. Brief sintético:

- **Modules afectados**: brand (model + entity + DTOs + repo + api + field-contract), copilot (persister + field_paths + extraction template + extraction registry), tests (BE + FE)
- **NO afectados**: offer (tiene `objections` propio en `Offer` distinct), sales_agent (`objection_history` es session-state, no persona), landing/crm (referencias docs/comentarios, sin código)
- **Blockers conocidos**: Ninguno. `can_propose=False` en field-contract → copilot no proponía estos fields wholesale, baja regression risk en copilot UX.
- **Tiempo estimado**: 1 sesión architect + 2 sesiones builder paralelas + 1 sesión auditor cross-stack
- **Decisión técnica abierta**: backup datos antes DROP o aceptar pérdida — architect decide

## Decisiones diferidas (explícitas)

- ¿Otros fields buyer_persona pendientes cleanup? — Chris evaluará post-ship PR-1, abre sprint S2 si aplica
- Refactor renderAs/UX restantes secciones buyer_persona — futuro PI-4 sprint

## Out of scope

- Cleanup `offer.objections` (campo distinto, NO es buyer_persona)
- Cualquier otro field brand
- Wire copilot↔telegram (PI-2)
- Refactor sub-schema buyer_persona restante

## Copilot-first checklist

- [x] ¿Operable conversacional desde copilot? **N/A** — es cleanup schema, no nueva capacidad. Copilot dejará de extraer/proponer estos fields automáticamente al limpiar persister + extraction template.
- [x] ¿Qué tools nuevos requiere? **Ninguno**.
- [x] ¿Cards/UI nueva? **Ninguna**. Form actual pierde 2 secciones.
- [x] Si NO copilot → razón documentada: **cleanup, no feature**.

## Agentes / skills recomendados

| Fase | Agente/skill | Prompt pre-coce | Entregable esperado |
|---|---|---|---|
| Pre-design | `nicolify-architect` + skill `brand-expert` + skill `copilot-expert` | `prompts/01-architect-start.md` | `CONTRACT.md` con schema delta + migration plan + persister diff plan |
| UX | N/A (no UI nueva, solo eliminación de secciones existentes) | — | — |
| Implementation BE | `nicolify-backend` + skill `brand-expert` | `prompts/02-builder-start.md` (variant BE) | code + tests + migration + `IMPL-LOG.md` (sección BE) |
| Implementation FE | `nicolify-frontend` + skill `brand-expert` | `prompts/02-builder-start.md` (variant FE) | code + tests + `IMPL-LOG.md` (sección FE) |
| Audit BE | `nicolify-backend-auditor` | `prompts/03-auditor-start.md` (variant BE) | `REVIEW-backend.md` |
| Audit FE | `nicolify-frontend-auditor` | `prompts/03-auditor-start.md` (variant FE) | `REVIEW-frontend.md` |
| Cierre | `/pm` | `prompts/04-pm-close.md` | `RESULT.md` + `current-state/brand.md` update |

## Surface impactada (del Explore brief 2026-04-29)

| Tipo | Path / nombre | Cambio |
|---|---|---|
| Migration | `backend/alembic/versions/{new}_drop_buyer_persona_fields.py` | nueva (idempotente, raw SQL) |
| Migration ref | `backend/alembic/versions/f851363921c9_add_buyer_personas.py` | NO modificar (history) |
| Modelo SA | `backend/src/modules/brand/infrastructure/models/buyer_persona_model.py:33-34` | drop columns |
| Domain entity | `backend/src/modules/brand/domain/buyer_persona.py:40-41` | drop fields |
| DTOs | `backend/src/modules/brand/api/dto/buyer_personas.py:28-29,50-51` | drop fields request + response |
| Completeness | `backend/src/modules/brand/api/buyer_personas.py:30-31` | remove from `_PROFILE_FIELDS` |
| Repository | `backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py` | remove from update methods |
| Field contract | `backend/src/modules/brand/domain/buyer_persona_field_contract.py:114-115,137-138` | remove from `BUYER_PERSONA_SECTION_MAP` + `BUYER_PERSONA_FIELD_OVERRIDES` |
| Copilot persister | `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py:29-30` | remove from `_LIST_FIELDS` |
| Copilot field paths | `backend/src/modules/copilot/domain/field_paths_hint.py:35-36` | remove from `_LIST_PATHS["buyer_persona"]` |
| Copilot extraction tmpl | `backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2:26-27` | drop field instructions |
| Copilot extraction registry | `backend/src/modules/copilot/domain/extraction_domain_registry.py` | update comment buyer_persona JSONB |
| Tests BE | `backend/tests/modules/brand/test_buyer_persona_model.py:29-30` | remove assertions |
| Tests arch baseline | `backend/tests/architecture/test_buyer_persona_editable_fields_baseline.py` | verify no break (Explore: fields NO en baseline, safe) |
| FE schema | `frontend/src/features/brand-studio/schemas/buyer-persona.schema.ts:181-249` | drop 2 array fields |
| FE types | `frontend/src/lib/api/buyer-persona.ts:17-18` | drop fields |
| FE tests | `frontend/src/features/brand-studio/pages/__tests__/PersonaDetailPage.test.tsx`, `frontend/src/features/brand-studio/components/dashboard/__tests__/BuyerPersonasDashboard.test.tsx` | remove from mock data |
| current-state | `docs/pm-nico/current-state/brand.md` | append capability lineage cleanup |

## Tests requeridos (TDD)

- BE: regression test "buyer_persona response no incluye objections / preferred_channels"
- BE: migration test idempotency (clone DB, re-run)
- BE: arch fitness existentes verdes
- FE: form-runtime test "schema buyer-persona no contiene objections / preferred_channels"
- FE: tests existentes con fixtures actualizados
- BE+FE: /test-all PASS post-cleanup

## Aceptación

- [ ] Tests verdes (BE + FE + arch)
- [ ] Lint/type check verdes (ruff + tsc + eslint)
- [ ] Migration idempotente test passed (clone DB)
- [ ] `IMPL-LOG.md` completo (secciones BE + FE)
- [ ] `REVIEW-backend.md` + `REVIEW-frontend.md` veredicto PASS
- [ ] `RESULT.md` escrito por PM
- [ ] `current-state/brand.md` actualizado con lineage
- [ ] Decisiones registradas en `decisions.md` PI

## Riesgos

| Riesgo | Mitigación |
|---|---|
| Confusión `offer.objections` vs `buyer_persona.objections` | Architect lee Explore brief; `offer.objections` NO se toca |
| Migration falla en prod por data en columns | Test con clone DB antes (regla `backend-migrations.md`) |
| Cache prefix copilot quebrado por cambio template j2 | `copilot-expert` valida slot ordering preservado |
| Frontend test fixtures con `objections: []` rotos | Builder actualiza fixtures + remueve assertions específicas |
| Tenant prod con datos llenos en columns | Architect decide: backup script o "data útil = 0 verified" |
