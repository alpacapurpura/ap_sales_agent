# PRE_FLIGHT — antes de arrancar sub-step o fase

Checklist rápida. 2-3 min.

## 1. Estado git limpio

```bash
git status --short
git log --oneline -3
git branch --show-current
```

- Branch: `development`
- Working tree: limpio (solo `.claude/scheduled_tasks.lock` aceptable)
- Last commit match `STATE.md::last_green_commit`

Si algo no cuadra → [CRASH_RECOVERY.md](CRASH_RECOVERY.md).

## 2. Baseline tests

Capturar antes de tocar:

```bash
# Backend
cd backend && .venv/bin/pytest tests/architecture/ -x -q --tb=short 2>&1 | tail -3

# Frontend arch + typecheck
cd frontend && npx vitest run src/__tests__/architecture/ 2>&1 | tail -3
cd frontend && npx tsc --noEmit 2>&1 | tail -3
```

Anotar counts. Post-fase tiene que ser igual o mayor (additive only).

## 3. Re-lectura de invariantes aplicables

Mirá [../INVARIANTS.md](../INVARIANTS.md) rápido. Si tu sub-step puede tocar alguna:

- Scope del sub-step no viola regla N
- Plan de commit atómico listo
- Rollback conocido

## 4. Análisis específico de la fase

Pausa 5-10 min para pensar:

- ¿Qué archivos voy a tocar?
- ¿En qué orden?
- ¿Hay knowledge específico que necesito cargar? (docs del módulo, rules, ADRs relevantes)
- ¿Hay tests pre-existing que protegen lo que voy a modificar? Si no, ¿escribo baseline primero? (TDD obligatorio)
- ¿Paridad BE↔FE? Ambos se tocan en este sub-step o secuencial?
- ¿Cómo verifico que no rompí offer `a96403b5...`?

No escribir código sin esta pausa. SPEC.md tiene pistas para la fase.

## 5. Parallel session check

- ¿Hay otros archivos en `git status` que no son míos?
- Si sí → NO tocarlos. Solo stage por nombre lo mío.
- `.claude/scheduled_tasks.lock` nunca tocar.

## 6. Start

Empezá con Read del primer archivo a modificar. Nunca Write/Edit sin Read previo.

---

## Anti-patterns

- ❌ Saltear PRE_FLIGHT porque "es sub-step chico"
- ❌ Arrancar Write sin Read
- ❌ Baseline tests no capturado
- ❌ No leer LEARNINGS.md fase anterior
- ❌ Commit con múltiples conceptos
- ❌ `git add -A`

Cada uno cuesta más tiempo que saltarlo "ahorra".
