# Prompt — Builder kickoff (PR-1 drop-buyer-persona-fields)

> Cross-stack PR. Dos sesiones Claude Code paralelas: una BE, una FE. Ambas consumen mismo CONTRACT.md. Coordinan commits por nombre archivo.

---

## Variant BE — copy-paste a sesión nueva (backend)

```
Sos `nicolify-backend`. Trabajo: implementar BACKEND de PR-1-drop-buyer-persona-fields del PI-4-brand-evolutive-maintenance / S1.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/PR.md`
2. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/CONTRACT.md` (SSoT migration + schema deltas)
3. `docs/pm-nico/current-state/brand.md` + `docs/pm-nico/current-state/copilot.md`
4. `.claude/rules/backend-ddd.md`, `.claude/rules/tenant-isolation.md`, `.claude/rules/backend-migrations.md`, `.claude/rules/tdd-mandatory.md`, `.claude/rules/git-safety.md`, `.claude/rules/parallel-safety.md`
5. `CLAUDE.md` (root)

**Skills a invocar:**
- `brand-expert` — guard schema brand
- `copilot-expert` — guard cleanup persister + extraction template + field_paths_hint sin romper cache prefix slots

**Workflow TDD strict (capa por capa):**
1. **RED**: tests primero. Mínimo:
   - `tests/modules/brand/test_buyer_persona_model.py` — assertion: model NO tiene `objections` / `preferred_channels` columns
   - `tests/modules/brand/test_buyer_persona_dto.py` (o existente) — DTO request/response NO acepta/retorna fields
   - `tests/modules/copilot/persisters/test_buyer_persona_persister.py` — persister NO escribe a fields eliminados
   - `tests/architecture/test_*` — verify NO referencia post-cleanup (ratchet allowlists shrink)
   - Migration test idempotency (clone DB, re-run según `backend-migrations.md`)
2. **GREEN** capa por capa: domain → infrastructure → application → api:
   - `backend/src/modules/brand/domain/buyer_persona.py` — drop fields
   - `backend/src/modules/brand/infrastructure/models/buyer_persona_model.py` — drop columns
   - `backend/src/modules/brand/api/dto/buyer_personas.py` — drop request + response fields
   - `backend/src/modules/brand/api/buyer_personas.py` — drop from `_PROFILE_FIELDS`
   - `backend/src/modules/brand/infrastructure/repositories/buyer_persona_repository.py` — remove from update methods
   - `backend/src/modules/brand/domain/buyer_persona_field_contract.py` — drop entries `BUYER_PERSONA_SECTION_MAP` + `BUYER_PERSONA_FIELD_OVERRIDES`
   - `backend/src/modules/copilot/infrastructure/persisters/buyer_persona_persister.py` — drop from `_LIST_FIELDS`
   - `backend/src/modules/copilot/domain/field_paths_hint.py` — drop from `_LIST_PATHS["buyer_persona"]`
   - `backend/src/modules/copilot/infrastructure/prompts/templates/interview/buyer_persona_doc_extraction.j2` — drop lines 26-27 (NO alterar slot order pre/post)
   - `backend/src/modules/copilot/domain/extraction_domain_registry.py` — actualizar comentario buyer_persona JSONB
3. **Migration**:
   - `backend/alembic/versions/{rev}_drop_buyer_persona_fields.py` siguiendo CONTRACT.
   - Raw SQL idempotente: `ALTER TABLE buyer_personas DROP COLUMN IF EXISTS objections; ALTER TABLE buyer_personas DROP COLUMN IF EXISTS preferred_channels;`
   - Test antes prod con clone DB (regla `backend-migrations.md`).
   - Si CONTRACT especifica backup script → implementarlo en `scripts/backups/`.

**Quality gates NATIVE (sin docker exec):**
- `cd backend && .venv/bin/ruff check .`
- `cd backend && .venv/bin/ruff format --check .`
- `cd backend && .venv/bin/pytest tests/modules/brand/ tests/modules/copilot/persisters/ tests/architecture/ -v`
- Migration test: clone DB pattern de `.claude/rules/backend-migrations.md`

**Output:**
- Code + tests + migration + scripts (si backup) en codebase
- `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/IMPL-LOG.md` — append sección "## BE implementation"
- Commits conventional, stage por nombre (PROHIBIDO `git add .|-A|-u`):
  - `git pull origin development` antes commit (parallel-safety M5)
  - Ej: `refactor(brand): drop buyer_persona objections + preferred_channels columns`
  - Ej: `refactor(copilot): cleanup buyer_persona extraction surface (template + persister + field_paths)`
  - Ej: `feat(alembic): add migration drop_buyer_persona_fields`

**Si bloqueado por algo no anticipado** (ej: dependency oculta, test arch unexpected) → STOP, append IMPL-LOG.md, devolver control PM.

**Al terminar:**
1. IMPL-LOG.md sección BE completa con sub-deliverables, decisiones, commits.
2. Última línea respuesta:
   `<!-- @pm: BE implementation done. Próximo paso: cuando FE termine también, ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-1 BE builder done". -->`
3. Brief < 250 palabras: qué se implementó + tests verdes + migration tested.
```

---

## Variant FE — copy-paste a sesión nueva (frontend)

```
Sos `nicolify-frontend`. Trabajo: implementar FRONTEND de PR-1-drop-buyer-persona-fields del PI-4-brand-evolutive-maintenance / S1.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/PR.md`
2. `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/CONTRACT.md` (SSoT schema deltas FE)
3. `docs/pm-nico/current-state/brand.md`
4. `.claude/rules/frontend-fsd.md`, `.claude/rules/frontend-quality.md`, `.claude/rules/form-runtime-array.md`, `.claude/rules/tdd-mandatory.md`, `.claude/rules/git-safety.md`, `.claude/rules/parallel-safety.md`
5. `CLAUDE.md` (root)

**Skills a invocar:**
- `brand-expert` — guard schema brand FE
- `tessl__react-patterns` — patrones obligatorios componentes

**Workflow TDD strict:**
1. **RED**: tests primero:
   - Vitest schema test — `frontend/src/features/brand-studio/schemas/__tests__/buyer-persona.schema.test.ts` (o existente): assertion schema fields list NO contiene `objections` ni `preferred_channels`
   - Component fixtures — verify mocks sin fields
2. **GREEN**:
   - `frontend/src/features/brand-studio/schemas/buyer-persona.schema.ts` — drop array fields lines 181-249 (objections + preferred_channels)
   - `frontend/src/lib/api/buyer-persona.ts` — drop fields lines 17-18
   - `frontend/src/features/brand-studio/pages/__tests__/PersonaDetailPage.test.tsx` — actualizar mock data
   - `frontend/src/features/brand-studio/components/dashboard/__tests__/BuyerPersonasDashboard.test.tsx` — actualizar mock data
   - Verificar: ningún componente referencia los fields directamente (search `objections|preferred_channels` bajo `frontend/src/features/brand-studio/` y `frontend/src/lib/api/`)

**Quality gates NATIVE:**
- `cd frontend && npx tsc --noEmit`
- `cd frontend && npx eslint src/features/brand-studio/ src/lib/api/buyer-persona.ts`
- `cd frontend && npx vitest run src/features/brand-studio/`
- `cd frontend && npx vitest run src/__tests__/architecture/` — verify arch tests verdes

**Output:**
- Code + tests actualizados en codebase
- `docs/pm-nico/pis/active/PI-4-brand-evolutive-maintenance/sprints/S1-cleanup-buyer-persona/prs/PR-1-drop-buyer-persona-fields/IMPL-LOG.md` — append sección "## FE implementation"
- Commits conventional, stage por nombre:
  - `git pull origin development` antes commit (parallel-safety M5)
  - Ej: `refactor(brand-studio): remove objections + preferred_channels from buyer-persona schema`
  - Ej: `test(brand-studio): update buyer-persona fixtures sans dropped fields`

**Coordinación con BE:** No tocar archivos backend. Si arch test FE detecta drift con BE types, esperar que BE termine y resync.

**Si bloqueado:** STOP, append IMPL-LOG.md, devolver control PM.

**Al terminar:**
1. IMPL-LOG.md sección FE completa.
2. Última línea respuesta:
   `<!-- @pm: FE implementation done. Próximo paso: cuando BE termine también, ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-1 FE builder done". -->`
3. Brief < 250 palabras: qué se implementó + tests verdes + arch tests verdes.
```

## Notas operativas

- **Cross-stack paralelo**: BE y FE pueden correr simultáneo. Ambas appendean IMPL-LOG.md (sección por builder). Conflict en archivos = improbable porque no se solapan.
- **PR cross-stack** = ambos auditores corren después → REVIEW-backend.md + REVIEW-frontend.md.
- **Parallel safety M3**: tests/CI secuencial. Si BE corre `/test-backend` y FE corre `/test-frontend` simultáneo = OK (no comparten DB). Pero `make ci-parity` o `/test-all` = una sesión sola.
