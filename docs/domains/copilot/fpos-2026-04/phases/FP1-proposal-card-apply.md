# FP1 — ProposalCard "Aplicar" mutation persist (B22-TP11)

**Bug origen:** TP11 J1 click "Aplicar" silent no-op.
**TP origen:** `results/TP11-2026-04-26.md §B22-TP11`.
**Tiempo estimado:** 1-2 días.
**Pre-req hard:** TP11 cerrado.
**Capa stack:** Frontend (ProposalCard + useCopilotStore activeBridge) + Backend (mutations endpoint).

---

## Misión

Cerrar el silent failure cuando user clickea "Aplicar" en ProposalCard sin form-runtime bridge connected. Garantizar que la mutation persiste **siempre** — vía bridge si está disponible, vía backend `/mutations/apply` endpoint si no — y que UI feedback es **honesto** (no muestra verde "Aplicado" si nada persistió).

---

## Research mandate

Queries:

- `"react form-runtime bridge pattern 2026 dispatcher subscriber"` — patrones para form context discovery + fallback.
- `"FastAPI mutation endpoint idempotent apply pattern 2026"` — endpoint design para apply mutation con idempotency key.
- `"optimistic UI rollback strategy 2026 mutation failure"` — handle UX cuando mutation falla post-optimistic.

Tessl tiles: `tessl__fastapi`, `tessl__zod` (si validation BE↔FE).

---

## Acceptance criteria

| AC | Descripción | Evidence pre-fix | Evidence post-fix |
|---|---|---|---|
| **AC1** | Click "Aplicar" en ProposalCard con bridge connected → field se patche en form-runtime + autosave dispara | bridge.patchField calls visible | mismo + DOM textbox value populated |
| **AC2** | Click "Aplicar" sin bridge connected → fallback call al backend `/api/v1/copilot/conversations/{id}/mutations/apply` → mutation persiste en `copilot_mutation_journal` | mutation_journal vacío post-click | row insertada con `field_path`, `new_value`, `applied_at` |
| **AC3** | Mutation falla (network error / 4xx / 5xx) → UI muestra status `failed` (no verde "Aplicado") + mensaje explícito al user | UI verde mintiendo | UI rojo "No se pudo aplicar — reintenta" |
| **AC4** | Mutation success → UI muestra `applied` (verde) + emite event `proposal_accepted` con `mutation_id` (no solo `field_count`) | event sin mutation_id | event con `mutation_id` |
| **AC5** | Idempotency: clickear "Aplicar" 2 veces no duplica row en mutation_journal | sin idempotency check | mismo `proposal_id` + `field_path` = single row |
| **AC6** | Re-load page post-apply → form fields visibles populated con valores aplicados (verifica end-to-end persistence) | textboxes vacíos | textboxes muestran "Visionarias", etc. |

---

## Procedimiento por AC

### Setup
- TP11 J1 conversation existente: `f35bc21a-78a4-495f-9a00-b9a4e6971fc2` (visionarias-v4) tiene proposal sin aplicar — usable para reproducción rápida.
- O crear nueva conversación + provocar ProposalCard via setup flow.

### AC1 — bridge happy path

1. **Test RED:** unit test FE `ProposalCard.test.tsx` con mock `useCopilotStore.activeBridge` ≠ null + mock `bridge.patchField`. Assert called with field path + new_value.
2. **Run actual code:** verificar en `ProposalCard.tsx:34-44` que el path con bridge funciona. Si ya pasa el test, este AC es regression-free baseline.
3. **Live re-run J1.click_apply** con ProposalCard + page focused en Brand Studio identity → form fields populated.

### AC2 — fallback backend mutation endpoint

1. **Investigar endpoint actual:** `grep -rn "mutations/apply\|mutation_journal" backend/src/modules/copilot/api/`. Si no existe, agregar.
2. **Backend:** crear `POST /api/v1/copilot/conversations/{id}/mutations/apply` que recibe `{updates: [{field_id, field_path, new_value}]}` + tenant_id desde header → escribe en `copilot_mutation_journal` + dispara domain event para que repos correspondientes (brand_summary, etc) actualicen.
3. **Frontend:** modificar `ProposalCard.handleApply`:
   ```js
   if (bridge && snap) {
     // existing bridge path
   } else {
     // fallback: call backend
     await fetchClient(`/api/v1/copilot/conversations/${convId}/mutations/apply`, { method: 'POST', body: { updates } });
   }
   ```
4. **Test RED:** test FE mock fetch + mock activeBridge=null. Assert fetch called with correct path + body.
5. **Test GREEN:** implement.
6. **Live re-run J1:** click "Aplicar" + SQL probe `mutation_journal WHERE conversation_id=X` → row visible.

### AC3 — error path UI honesto

1. **Test RED:** test FE mock fetch returns 500. Assert `setStatus("failed")` + error message rendered.
2. **Implement:** `try { await fetch... } catch(e) { setStatus("failed"); }`.
3. **UI:** add status `"failed"` to `type ProposalStatus` + render con border-red + texto "No se pudo aplicar — reintenta".
4. **Live verify:** mock backend 500 OR throw network → UI shows red.

### AC4 — event tracking con mutation_id

1. **Test RED:** test FE asserts `reportCopilotEvent("proposal_accepted", { ..., mutation_id })` con el ID retornado por backend.
2. **Backend response:** apply endpoint retorna `{ mutations: [{ id, field_path, ... }] }`.
3. **Frontend:** extract IDs y pasar al `reportCopilotEvent`.

### AC5 — idempotency

1. **Backend:** apply endpoint debe ser idempotent. Usar `(conversation_id, message_id, field_path)` como natural key. Si ya existe row activa (reverted_at IS NULL) → skip insert + return existing.
2. **Test BE:** call apply 2x con same payload → 1 row.
3. **Live verify:** click "Aplicar" 2 veces (UI prevent o click via console) → 1 row.

### AC6 — end-to-end persistence

1. **Live:** complete J1 setup brand → click Aplicar → reload page → verify Brand Studio identity textbox values populated.
2. **SQL probe:** verify `brand_summary` o tabla apropiada updated con valores.
3. Sub-bug discovery: si reload no muestra valores, hay problema en el read-side (repository sync). Documentar como sub-bug.

---

## Tests / archivos a crear / modificar

### Backend
- `backend/src/modules/copilot/api/mutations.py` (NEW endpoint apply)
- `backend/src/modules/copilot/application/services/mutation_apply_service.py` (NEW)
- `backend/src/modules/copilot/infrastructure/repositories/mutation_journal_repository.py` (UPDATE — add idempotent_upsert)
- `backend/tests/modules/copilot/test_mutations_apply_endpoint.py` (NEW)

### Frontend
- `frontend/src/features/copilot/components/messages/ProposalCard.tsx` (UPDATE — fallback + error path)
- `frontend/src/features/copilot/api/copilot-api.ts` (UPDATE — `applyMutations` function)
- `frontend/src/features/copilot/components/messages/ProposalCard.test.tsx` (NEW)
- `frontend/src/features/copilot/types/proposal.ts` (UPDATE — `ProposalStatus` + `failed` state)

---

## Failure playbook

- **Bridge registration logic complejo:** investigar `useCopilotStore.ts` + `bridges/form-runtime-bridge.ts`. Es posible que solo registre cuando un specific form-runtime-section está mounted + visible. Documentar en results.
- **Backend repos no apply mutation a brand_summary table:** sub-bug — apply endpoint solo escribe journal, NO ejecuta el side-effect. Necesita dispatcher por `domain` field (`identity` → brand_summary repo, `offer.X` → product repo, etc). Documentar como sub-FP1.1 si exceeds scope.
- **Idempotency conflict con migration:** si journal table no tiene unique constraint, agregar via Alembic migration idempotente.

---

## Sub-bugs descubiertos durante FP1

> Append-only. Llenar durante ejecución.

- (none yet)

---

## Output esperado

`results/FP1-{fecha}.md` con:
- Pre-research insights
- AC1-AC6 checklist con before/after evidence
- Tests added (count + paths)
- Sub-bugs si hubo
- Métricas: latency apply endpoint, FE bundle delta
- Aprendizajes para FP2
- Handoff prompt en `prompts/FP2-start.md`
