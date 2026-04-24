# Cómo retomar este refactor

**Tiempo estimado de context rebuild**: 5-10 minutos.

Seguir en orden. No saltar pasos.

## 1. Leer contexto mínimo (5 min)

En este orden:
1. [../README.md](../README.md) — objetivo final
2. [../STATE.md](../STATE.md) — dónde estamos AHORA
3. [../INVARIANTS.md](../INVARIANTS.md) — reglas inviolables
4. [../DESIGN.md](../DESIGN.md) — arquitectura completa (escanear secciones relevantes)
5. [../PLAN.md](../PLAN.md) — fases frozen (solo escanear fase activa)
6. [../LEARNINGS.md](../LEARNINGS.md) — cross-cutting + fase anterior
7. [../DECISIONS.md](../DECISIONS.md) — ADRs (consultar al dudar)

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
- Working tree: limpio (solo archivos de sesiones paralelas listados en STATE)

**Si no coincide**: investigar antes de continuar (probable parallel session
con WIP propio).

## 3. Abrir fase activa

```bash
PHASE=$(grep "^active_phase:" docs/refactors/field-contract-platform/STATE.md | cut -d: -f2 | tr -d ' ')
cat docs/refactors/field-contract-platform/phases/${PHASE}/PRE_INVESTIGATION.md
cat docs/refactors/field-contract-platform/phases/${PHASE}/SPEC.md
cat docs/refactors/field-contract-platform/phases/${PHASE}/STATUS.md
cat docs/refactors/field-contract-platform/phases/${PHASE}/ACCEPTANCE.md  # si existe
```

## 4. Pre-investigación obligatoria

**Antes del primer Write/Edit de código.** Cada fase tiene
`PRE_INVESTIGATION.md` con preguntas que **deben responderse** con
evidencia (grep + read), no asumirse. Si una respuesta no está clara,
investigar hasta poder.

Lección dura del refactor anterior: cerrar fase sin inventario completo
lleva a redescubrir gaps tarde.

## 5. PRE_FLIGHT.md

Ejecutá checklist [PRE_FLIGHT.md](PRE_FLIGHT.md) antes de cambiar código.

## 6. Ejecutar sub-step siguiente

Según `STATE.md sub_step`. SPEC.md detalla cada sub-step en orden.

**Al completar sub-step**:
1. Commit atómico (conventional, por nombre de archivo, scope refactor).
2. Update STATE.md (`last_updated`, `last_green_commit`, `sub_step`).
3. Si hay learning → append a `phases/{active}/LEARNINGS.md` (o cross-cutting
   en LEARNINGS.md global si aplica).
4. Si hay decisión nueva → append a DECISIONS.md (ADR-NNN).
5. Repetir desde paso 5 (PRE_FLIGHT para siguiente sub-step opcional).

## 7. POST_FLIGHT.md al cerrar fase

Cuando todos sub-steps done:
- Ejecutá [POST_FLIGHT.md](POST_FLIGHT.md).
- Update LEARNINGS.md global con learnings de la fase.
- Cerrá STATUS.md de la fase (`status: done`).
- Abrí STATUS.md de la fase siguiente (`status: ready-to-start`).
- Update STATE.md: `active_phase` a la siguiente.
- Generá [HANDOFF.md](../HANDOFF.md) con prompt exacto para nueva sesión.

## 8. Handoff para nueva sesión

Al terminar fase, entregá a Chris el prompt de [HANDOFF.md](../HANDOFF.md)
adaptado al estado real. Plantilla:

```
Retomamos refactor field-contract-platform.

Fase actual según STATE.md: {active-phase}
Sub-paso actual: {sub_step}
Last green commit: {hash}

Seguí protocol/RESUME.md desde paso 1. Pre-investigación obligatoria
antes de Write/Edit. Cuando cierres fase entregame nuevo prompt.

No te desvíes del PLAN.md. Si encontrás tech debt relacionada al scope,
arreglala en la misma fase. Si descubrís gap arquitectónico → ADR
nueva, no hack.
```

## Casos especiales

### Rama no es `development`

```bash
git checkout development
```

Si tenías WIP: `git stash push -m "pre-resume WIP"` antes.

### Working tree sucio con archivos de otras sesiones

Regla parallel-safety: NO tocar. Solo trabajar archivos de esta fase
según SPEC.md.

### Test fallando

```bash
cd backend && .venv/bin/pytest tests/architecture/ -x -q
cd frontend && npx vitest run
```

Si falla algo que no debería → investigar antes de continuar. No
hackear allowlists.

### Dudas arquitectónicas

Re-leer [DESIGN.md](../DESIGN.md) + [DECISIONS.md](../DECISIONS.md). Si
no responde, consultá [PLAN.md](../PLAN.md) out-of-scope. Si sigue
ambiguo, crear ADR-NNN nueva con decisión + razón.
