# POST_FLIGHT — al cerrar fase

Checklist completa. ~10-15 min.

## 1. Acceptance checklist de la fase

Abrir `phases/{active}/ACCEPTANCE.md`. Marcar cada item. **Todos** green antes de avanzar.

Si alguno RED → fixear en nuevo sub-step + commit antes de cerrar.

## 2. Verification layers

### 2a. Tests locales native

```bash
# Backend full
cd backend && .venv/bin/pytest -x -q --tb=short

# Backend arch específico
cd backend && .venv/bin/pytest tests/architecture/ -x -q

# Frontend full
cd frontend && npx vitest run

# Frontend arch
cd frontend && npx vitest run src/__tests__/architecture/

# TSC
cd frontend && npx tsc --noEmit

# Lint
cd backend && .venv/bin/ruff check src/ tests/ --no-cache
cd frontend && npx eslint src/
```

Todos green. Counts ≥ baseline pre-fase.

### 2b. Diff vs baseline

Comparar outputs capturados en PRE_FLIGHT:
- Tests passed count: post ≥ baseline
- Tests failed count: post = 0 (siempre)
- New tests added: match expectativa fase

### 2c. Golden fixture verificación

```bash
# Re-run golden test
cd backend && .venv/bin/pytest tests/modules/offer/test_offer_a96403b5_baseline.py -x -v
```

Debe pasar. Si falla → investigar diff. Additive (nuevo campo agregado) = OK si justificado. Subtractive (campo perdido) = PR mal, rollback.

### 2d. Live manual smoke (offer real)

1. Abrir dev-app.nicolify.com
2. Navegar offer `a96403b5-c1db-4b31-97aa-cb18d08ad9f9`
3. Verificar sección afectada por la fase:
   - Editor renderiza
   - Campos editables funcionan
   - Autosave funciona (tipear → network 200 → refresh → persistido)
4. Sales-agent prompt render: diff snapshot pre/post

5 min. Si algo roto → rollback inmediato.

## 3. Update docs workspace

### STATE.md
- `last_updated`: ahora
- `last_green_commit`: último hash
- `active_phase`: siguiente fase
- `sub_step`: 0/N fase siguiente
- `status`: `ready-to-start` (fase siguiente)
- Historial sesiones: append entry

### LEARNINGS.md
- Sección fase actual: replace `_pendiente_` con learnings reales
- Cross-cutting: append si hay learning aplicable a todo Nicolify
- Deuda técnica: listar

### DECISIONS.md
- Si hubo decisión arquitectónica nueva → nueva ADR-NNN

### TODO.md
- Marcar fase como done
- Pending siguiente fase: review + ajustar si aprendizajes lo requieren
- Blockers update

### phases/{current}/STATUS.md
- `status: done`
- `closed_at`: timestamp
- `commits`: listar hashes

### phases/{current}/LEARNINGS.md
- Complete con descubrimientos + decisiones + deuda

### phases/{next}/STATUS.md
- `status: ready-to-start`
- `opened_at`: timestamp

## 4. Commits check

```bash
git log --oneline --since="{fase start}" | head -20
```

- Cada commit conventional: `<type>(<scope>): <desc>`
- Cada commit atómico (un concepto)
- Cada commit revertible individual
- Staged por nombre explícito

## 5. Update `docs/mejoras-proceso/to-do.md`

Si hubo learning/deuda que aplica fuera del refactor → append entry.

## 6. Prompt de handoff para nueva sesión

Generá el prompt que Chris usa en sesión nueva. Template:

```
Retomamos refactor field-contract-ssot.

📁 Workspace: docs/refactors/field-contract-ssot/

Estado:
- Fase cerrada: {NN - nombre}
- Próxima fase: {NN+1 - nombre}
- Last green commit: {hash}
- Branch: development

Arrancá siguiendo protocol/RESUME.md desde paso 1.
Objetivo fase siguiente: {pegar línea del PLAN.md}
Duración estimada: {del PLAN.md}

Recordá:
- No te desvíes del PLAN.md
- Tech debt en scope = arreglar en la fase
- Cada fase cierra con POST_FLIGHT.md + prompt handoff para la siguiente

Si working tree no coincide con STATE.md → CRASH_RECOVERY.md.
```

Entregar a Chris al final del turn.

## 7. Commit de cierre

Último commit de la fase con mensaje explícito:

```
chore(refactor-field-contract): close phase {NN}

Phase completed. All acceptance checks green.
Golden fixture verified. Live smoke OK.

Learnings captured in docs/refactors/field-contract-ssot/LEARNINGS.md.
Next phase: {NN+1} scheduled.

Co-Authored-By: Claude Opus 4.7 (1M context) <noreply@anthropic.com>
```

## Anti-patterns

- ❌ Cerrar fase con algún ACCEPTANCE item RED
- ❌ Skip golden fixture verification
- ❌ No actualizar STATE.md
- ❌ Prompt de handoff ausente o ambiguo
- ❌ Learnings vacíos ("sin aprendizajes" raramente es cierto)
