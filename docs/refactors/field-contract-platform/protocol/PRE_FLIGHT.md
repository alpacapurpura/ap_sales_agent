# PRE_FLIGHT — antes de arrancar sub-step o fase

Checklist 2-3 min.

## 1. Estado git limpio

```bash
git status --short
git log --oneline -3
git branch --show-current
```

- Branch: `development`
- Working tree: limpio (parallel session files listed en STATE.md ignorables)
- Last commit match `STATE.md::last_green_commit`

## 2. Baseline tests

Capturar antes de tocar:

```bash
# Backend
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short 2>&1 | tail -3

# Frontend arch + typecheck
cd frontend && npx vitest run src/__tests__/architecture/ 2>&1 | tail -3
cd frontend && npx tsc --noEmit 2>&1 | tail -3
```

Anotar counts. Post-fase tiene que ser igual o mayor.

## 3. Pre-investigación de la fase completa

**Bloqueante.** Si tu fase tiene `PRE_INVESTIGATION.md`, todas las
preguntas deben tener respuesta documentada antes del primer Write/Edit.

Si una respuesta no está clara → grep + read hasta tenerla. Nunca
asumir.

Lección refactor anterior: cerrar fase sin inventario completo lleva a
redescubrir gaps semanas después.

## 4. Re-lectura de invariantes aplicables

Mirá [../INVARIANTS.md](../INVARIANTS.md). Si tu sub-step puede tocar:

- Scope del sub-step no viola regla N
- Plan de commit atómico listo
- Rollback conocido

## 5. Análisis específico de la fase

Pausa 5-10 min para pensar:

- ¿Qué archivos voy a tocar? (lista explícita)
- ¿En qué orden?
- ¿Hay knowledge específico que necesito cargar?
- ¿Hay tests pre-existing que protegen lo que voy a modificar? Si no,
  ¿escribo baseline primero? (TDD obligatorio)
- ¿Paridad BE↔FE? Ambos se tocan en este sub-step o secuencial?
- ¿Cómo verifico que UX no regresa? (golden snapshots existentes,
  o crearlos antes)

No escribir código sin esta pausa.

## 6. Parallel session check

- ¿Hay otros archivos en `git status` que no son míos?
- Si sí → NO tocarlos. Solo stage por nombre lo mío.
- `.claude/scheduled_tasks.lock` nunca tocar.

## 7. Start

Empezá con Read del primer archivo a modificar. Nunca Write/Edit sin
Read previo.

---

## Anti-patterns

- ❌ Saltear pre-investigación porque "creo que sé".
- ❌ Saltear PRE_FLIGHT porque "es sub-step chico".
- ❌ Arrancar Write sin Read.
- ❌ Baseline tests no capturado.
- ❌ No leer LEARNINGS.md fase anterior.
- ❌ Commit con múltiples conceptos.
- ❌ `git add -A`.

Cada uno cuesta más tiempo que saltarlo "ahorra".
