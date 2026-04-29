# Parallel Sessions Protocol

> Cómo correr 2+ sesiones Claude Code simultáneas en mismo workdir + mismo branch sin pisar trabajo.

## Decisión histórica

**Worktrees PROHIBIDOS** — Chris perdió 1 semana de trabajo previa por divergencia de branches en worktrees. Modelo adoptado: **mismo workdir, mismo branch (`development`), partición manual por PR/módulo**.

## Reglas duras (M1-M6)

| # | Regla | Por qué |
|---|---|---|
| **M1** | Sesiones paralelas TOCAN PRs DE MÓDULOS DISTINTOS — obligatorio | Evita race en `current-state/{m}.md` y `docs/{m}/` |
| **M2** | `docs/pm-nico/process/process-learnings.md` y `roadmap.md` y `MEMORY.md` SOLO los edita `/pm` (nunca builders) | Evita race en archivos centralizados |
| **M3** | Tests/CI/Docker SECUENCIAL siempre. Solo una sesión corre `/test-all`/`/dev-up`/`make ci-parity` a la vez | Container/port collision invisible hasta que un job mata al otro |
| **M4** | Claim by commit: PM cambia `Estado: in-progress` en `PR.md` y commitea/pushea **inmediato** antes de cualquier otro trabajo | Otra sesión que arranca hace `git pull` → ve claim |
| **M5** | `git pull origin development` al **inicio** de cada sesión Y antes de **cada commit nuevo**. NUNCA pull con diff sin commit | Evita merge sorpresa |
| **M6** | Bootstrap PM pregunta `¿en qué PI vas a trabajar?` antes de proceder. PM lista PRs disponibles del PI elegido + estado in-progress de otros | Chris elige consciente, no sesiones eligen sin saber |

## Workflow Chris dos sesiones

```
[Inicio]
Sesión A:                          Sesión B:
  /pm                                /pm
  → "PI-1 campaigns"                 → "PI-2 copilot"
  → PM lista PRs PI-1                → PM lista PRs PI-2
  → Chris pickea PR-1                → Chris pickea PR-X (módulo distinto: copilot)
  → PM marca Estado:in-progress
  → PM commitea + push
                                     → Chris hace git pull → ve PR-1 claimed
                                     → PM marca Estado:in-progress PR-X (distinct)
                                     → PM commitea + push

[Durante]
Ambas sesiones desarrollan EN PARALELO archivos de módulos distintos.
Ninguna toca: docs/pm-nico/process/, MEMORY.md, roadmap.md, current-state/{otro-m}.md.

[Tests]
Si A va a correr tests Docker → A avisa B → B espera.
Tests NUNCA en paralelo (port/container collision).

[Cierre]
Ambas commitean por nombre archivo (parallel-safety.md regla).
Push secuencial: A push → B git pull rebase → B push.
```

## Casos de conflicto y mitigaciones

| Caso | Mitigación |
|---|---|
| A y B tocan mismo módulo (caso accidental) | M1 lo prohíbe. Si pasa: secuencial — B espera A merge a development antes seguir |
| A escribe `current-state/{m}.md`, B también (módulos distintos) | OK — archivos distintos |
| A escribe `roadmap.md`, B también | M2 lo prohíbe a builders. Si dos /pm sessions tocan roadmap → secuencial |
| Tests Docker concurrent | M3 lo prohíbe — sesión avisa por chat o commit "wip: corriendo tests" |
| Sesión B no ve claim de A (race) | M4 + M5: A commitea/pushea ANTES empezar; B pull al iniciar |

## Lo que NO hacer

- ❌ Worktrees git (`git worktree add`)
- ❌ Feature branches (`feat/xyz`)
- ❌ Stage `git add .` o `-A` o `-u`
- ❌ Commit/push sin haber hecho `git pull` previo
- ❌ Tests Docker dos sesiones a la vez
- ❌ Una sesión edita archivo central (`roadmap.md`, `MEMORY.md`, `process-learnings.md`) sin saber que otra sesión `/pm` está activa
- ❌ Sesión B agarra PR sin verificar `Estado:` actual (puede estar in-progress por A)

## Anchor

- Esta regla aplica a TODA sesión Claude Code en este workdir, no solo `/pm`.
- Reflejada en `.claude/rules/parallel-safety.md` (universal) y `.claude/skills/pm/SKILL.md` (bootstrap PM).
- Si encontrás conflicto que la regla no cubre → append a `process-learnings.md`.
