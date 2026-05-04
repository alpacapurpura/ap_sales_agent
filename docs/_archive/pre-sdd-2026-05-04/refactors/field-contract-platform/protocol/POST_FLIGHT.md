# POST_FLIGHT — al cerrar una fase

Checklist obligatorio antes de declarar fase completa.

## 1. Tests verde end-to-end

```bash
# Native, never docker
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short
cd backend && .venv/bin/pytest -x -q --tb=short
cd frontend && npx vitest run src/__tests__/architecture/
cd frontend && npx vitest run
cd frontend && npx tsc --noEmit
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
```

Cualquier red → arreglar antes de cerrar.

## 2. Golden snapshots

Si la fase tocó algo que afecta offer/brand/buyer rendering:

- Re-ejecutar capture script si aplica.
- Diff vs baseline pre-fase.
- Byte-identical excepto fields nuevos esperados (additive only).

## 3. Verificación funcional manual

- Endpoint `/api/v1/offer/field-contract` (o equivalente fase) responde
  con shape esperado.
- Copilot `propose_field_updates` no rompe.
- Extraction worker funciona.
- Sales-agent + landing siguen renderizando.

## 4. Update docs del refactor

- `phases/{active}/STATUS.md` → `status: done`, `closed_at` fecha.
- `phases/{active}/LEARNINGS.md` (per-fase si existe) finalizado.
- `LEARNINGS.md` global → append section de la fase.
- `DECISIONS.md` → ADRs nuevas si las hubo.
- `STATE.md` → `active_phase` a la siguiente, `sub_step` reset, `last_green_commit`.
- `phases/{next}/STATUS.md` → `status: ready-to-start`.

## 5. Handoff doc

Generar/actualizar [../HANDOFF.md](../HANDOFF.md) con prompt exacto
para retomar próxima fase. El prompt:
- Cita commit verde de cierre.
- Lista los 3-5 archivos clave a leer primero.
- Apunta a `PRE_INVESTIGATION.md` de fase siguiente.
- Recuerda invariantes críticos.
- Lo entregás a Chris como output final de la sesión.

## 6. Commit cierre + push

```bash
# Stage por nombre solo lo del refactor
git add docs/refactors/field-contract-platform/...
git commit -m "chore(refactor-field-contract-platform): close fase {NN-name}"
git push  # solo si user pide
```

Mensaje conventional. Mencionar fase cerrada + fase siguiente abierta.
