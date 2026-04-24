# Crash Recovery

Qué hacer cuando algo rompió entre sesiones o mid-fase.

## Scenarios

### A. Working tree no coincide con STATE.md

**Síntoma**: `git status --short` muestra cambios que no deberían estar, o falta un commit que STATE.md dice fue hecho.

**Diagnóstico**:
```bash
git status --short
git log --oneline -10
git stash list
```

Comparar contra STATE.md `last_green_commit` y session history.

**Respuesta**:

1. **Si falta commit**: otro dev o sesión hizo revert. Leer `git log`, identificar revert commit. Nueva entry LEARNINGS.md. Decidir: re-aplicar (si era correcto) o respetar (si había razón).

2. **Si sobran cambios no commiteados que no son míos**: regla parallel-safety — NO tocar. Son de otra sesión. Coordinar con Chris.

3. **Si sobran cambios míos que olvidé commitear**: revisar si compilan + tests pasan. Si sí → commit retroactivo con mensaje honesto. Si no → stash con nombre descriptivo, STATE.md refleja el stash.

4. **Si stash pendiente mío**: aplicar si calza con fase activa; sino dejar listado y reportar.

### B. Test pre-existing falla post-commit de refactor

**Síntoma**: baseline pre-fase pasó 120 tests, post-sub-step pasa 119.

**Respuesta**:

1. Identificar test failing: `cd backend && .venv/bin/pytest --lf -v`
2. Leer stack trace. ¿Es por cambio mío o por infra?
3. Si cambio mío:
   - **Fix inmediato** si es regresión accidental no deseada
   - **Update test** si cambio era intencional y test desactualizado (documentar en LEARNINGS.md por qué)
4. Si infra (DB, Redis down, flaky):
   - Retry limpio. Si persiste, reportar a Chris. Fase pausa.
5. Nunca skip con `pytest.mark.skip` o `@pytest.mark.xfail` para "pasar CI".

### C. Golden fixture falla

**Síntoma**: `test_offer_a96403b5_baseline.py` red.

**Respuesta**:

1. Ver diff exact entre snapshot + actual
2. Categorizar:
   - **Additive** (nuevo field con valor, viejo intacto): actualizar snapshot con entry en DECISIONS.md explicando por qué se agregó field a baseline
   - **Subtractive** (field perdido): BUG. Revert commit. Investigar por qué desapareció. Fix.
   - **Mutational** (valor viejo cambió): casi siempre BUG. Investigar.
3. Jamás "regenerar snapshot" sin entender por qué cambió.

### D. Migration falla al aplicar

**Síntoma**: `alembic upgrade head` error.

**Respuesta**:

1. Leer error: ¿column ya existe? ¿FK rota? ¿type incompatible?
2. Si idempotencia falló: fix migration (raw SQL `IF NOT EXISTS`). Re-commit.
3. Si data inválida: investigar tenant data, no drop blindly.
4. Test en clone DB antes de re-intentar prod:
   ```bash
   docker exec -t visionarias_postgres psql -U postgres -c "CREATE DATABASE migration_test;"
   docker exec visionarias_postgres bash -c 'pg_dump -U postgres -s visionarias_logs | psql -U postgres -d migration_test'
   docker exec -t visionarias_brain_dev bash -c 'POSTGRES_DB=migration_test alembic upgrade head'
   ```

### E. Arch test nuevo RED sin razón clara

**Síntoma**: Fase 0 arch test red para path que esperaba en allowlist.

**Respuesta**:

1. Verificar que schemas FE realmente contienen el path
2. Verificar codegen JSON tiene paths actualizados del BE
3. Si discrepancia: regenerar `offer-field-paths.json` (script BE)
4. Allowlist actualizar solo si path es justificado deuda temporal. Cada entrada en allowlist = razón escrita.

### F. Sesión Claude muere mid-fase sin commit

**Síntoma**: STATE.md dice sub-step 3/5, pero git log solo muestra hasta sub-step 2. Cambios uncommitted en disk (o perdidos).

**Respuesta**:

1. `git status --short` — ver si están los cambios
2. `git diff` — review
3. Si están:
   - Decidir si completos/testados. Si sí: commit + update STATE.md.
   - Si incompletos: completá el sub-step limpio, entonces commit.
4. Si perdidos: volver a sub-step 3/5 según SPEC.md + rehacer.
5. Nunca "avanzar" sobre un sub-step incompleto.

### G. Paralelo Claude session pisó archivo

**Síntoma**: archivo que estabas editando tiene cambios que no hiciste.

**Respuesta**:

1. `git log --oneline <file>` ver si hay commits nuevos
2. Si sí: leer commits + decidir:
   - Son compatibles → merge mental, ajustá tu edit al nuevo estado
   - Conflictan → pausá, reportá a Chris para coordinar
3. Regla parallel-safety: **no revert al trabajo del otro**. Siempre incorporar o coordinar.

### H. Tests de `FieldContract` verifican shape equivocado

**Síntoma**: decidiste extender `FieldContract` con campo X, tests de contract agreement fallan.

**Respuesta**:

1. Si extensión legítima: update test + DECISIONS.md ADR-NNN
2. Si no necesario: revert extensión
3. Nunca agregar campo a `FieldContract` sin consumer real (ver INVARIANTS #20 no desviar)

## Plan general si todo está confuso

1. **Stop**: no más Write/Edit hasta entender
2. **Read**:
   - STATE.md
   - phases/{active}/STATUS.md
   - Last 10 git log
   - LEARNINGS.md últimas entries
3. **Report** a Chris: "estado confuso, necesito guía sobre X"
4. **Nunca** force-push, reset --hard, stash drop, sin confirmación Chris

## Prompt de recovery para sesión nueva

Si crash total, Chris puede arrancar sesión con:

```
Crash recovery refactor field-contract-ssot.

Workspace: docs/refactors/field-contract-ssot/

1. Leé protocol/CRASH_RECOVERY.md
2. Diagnosticá: git status, git log -10, STATE.md
3. Identificá scenario (A-H)
4. Reportáme tu diagnóstico antes de tocar nada
5. Esperá mi OK para recovery path
```
