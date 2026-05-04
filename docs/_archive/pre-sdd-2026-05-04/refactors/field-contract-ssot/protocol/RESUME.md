# Cómo retomar este refactor

**Tiempo estimado de context rebuild**: 5-10 minutos.

Seguir en orden. No saltar pasos.

## 1. Leer contexto mínimo (5 min)

En este orden:
1. [../README.md](../README.md) — objetivo final
2. [../STATE.md](../STATE.md) — dónde estamos AHORA
3. [../INVARIANTS.md](../INVARIANTS.md) — reglas inviolables
4. [../PLAN.md](../PLAN.md) — fases frozen (solo scanear fase activa)
5. [../LEARNINGS.md](../LEARNINGS.md) — cross-cutting + fase anterior

## 2. Verificar estado git

```bash
cd /home/chris/AISALESHT
git status --short
git log --oneline -10
git branch --show-current
```

Debe coincidir con STATE.md:
- Branch: `development`
- Last commit: match `last_green_commit`
- Working tree: limpio (solo `.claude/scheduled_tasks.lock` permitido)

**Si no coincide**: [CRASH_RECOVERY.md](CRASH_RECOVERY.md).

## 3. Abrir fase activa

```bash
# Fase activa según STATE.md
cat docs/refactors/field-contract-ssot/phases/{active-phase}/SPEC.md
cat docs/refactors/field-contract-ssot/phases/{active-phase}/STATUS.md
cat docs/refactors/field-contract-ssot/phases/{active-phase}/ACCEPTANCE.md
```

## 4. Knowledge específico para la fase

Antes del primer tool call de código, tomarse **5-10 min** para:

1. Leer files que vas a modificar (Read tool — no `cat`)
2. Si hay incertidumbre arquitectónica: consulta rápida a agente Explore (1 query, bajo budget)
3. Listar en mente (o en STATUS.md sub-steps) qué archivos tocás + orden

**No empezar Write/Edit sin este paso.** Previene refactor ciego.

## 5. PRE_FLIGHT.md

Ejecutá checklist [PRE_FLIGHT.md](PRE_FLIGHT.md) antes de cambiar código.

## 6. Ejecutar sub-step siguiente

Según STATE.md `sub_step`. SPEC.md detalla cada sub-step en orden.

**Al completar sub-step**:
1. Commit atómico (conventional, por nombre de archivo)
2. Update STATE.md (`last_updated`, `last_green_commit`, `sub_step`)
3. Si hay learning → append a phases/{active}/LEARNINGS.md
4. Si hay decisión nueva → append a DECISIONS.md (ADR-NNN)
5. Repetir desde paso 5 (PRE_FLIGHT para siguiente sub-step es opt-in)

## 7. POST_FLIGHT.md al cerrar fase

Cuando todos sub-steps done:
- Ejecutá [POST_FLIGHT.md](POST_FLIGHT.md)
- Update LEARNINGS.md global con learnings de la fase
- Cerrá STATUS.md de la fase (`status: done`)
- Abrí STATUS.md de la fase siguiente (`status: ready-to-start`)
- Update STATE.md: `active_phase` a la siguiente
- Generá **prompt de continuación** para nueva sesión Claude (template abajo)

## 8. Handoff para nueva sesión

Al terminar fase o cuando contexto se queme:

1. Commit de cierre con mensaje "closes phase NN"
2. Push `development`
3. Entregá a Chris el siguiente prompt (plantilla):

```
Retomamos refactor field-contract-ssot. Contexto en docs/refactors/field-contract-ssot/.

Fase actual según STATE.md: {active-phase}
Sub-paso actual: {sub_step}
Last green commit: {hash}

Seguí protocol/RESUME.md desde paso 1. Arrancá con PRE_FLIGHT.md, ejecutá el siguiente sub-step de la fase activa. Cuando cierres fase entregame nuevo prompt para continuar.

No te desvíes del PLAN.md. Si encontrás tech debt relacionada al scope, arreglala en la misma fase.
```

Adaptá los `{...}` al estado real.

## Casos especiales

### Rama no es `development`

```bash
git checkout development
```

Si tenías WIP: `git stash push -m "pre-resume WIP"` antes. Listar stashes en STATE.md si dejás algo.

### Working tree sucio con archivos de otras sesiones

Regla parallel-safety: NO tocar. Solo trabajar con archivos de esta fase según SPEC.md.

### Test fallando

```bash
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd frontend && npx vitest run
```

Si falla algo que no debería → [CRASH_RECOVERY.md](CRASH_RECOVERY.md).

### Dudas arquitectónicas

Re-leer [DECISIONS.md](../DECISIONS.md). Si no responde, consultá [PLAN.md](../PLAN.md) out-of-scope. Si sigue ambiguo, crear ADR-NNN nueva con decisión + razón.
