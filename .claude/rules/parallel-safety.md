# Parallel Safety (OBLIGATORIO)

Chris multi-instancia Claude Code WSL. BLOQUEANTE.

## Branches
`development` única trabajo. `main` solo prod. NUNCA feature branches/worktrees salvo instrucción.

## Worktrees PROHIBIDOS
Worktrees git = pierde trabajo (Chris perdió 1 semana previa). Sesiones paralelas SIEMPRE mismo workdir mismo branch.

## Inicio conversación
Antes de actuar: `git status --short && git branch --show-current && git stash list && git log --oneline -3`.
- development limpio → proceder.
- main limpio → `git checkout development`.
- Otra rama → switch a development.
- Tree sucio → PARAR: reportar archivos, ofrecer A) commit B) stash C) descartar (solo si Chris pide). No empezar hasta limpio.
- **Sesión paralela detectada (otra instancia Claude Code activa):** `git pull origin development` PRIMERO antes de cualquier write.

## Sync
`main` adelantado → `git checkout development && git merge main`. Reverse solo en pase prod.
**Ante cada commit nuevo:** `git pull origin development` antes para evitar merge sorpresa.

## Scope commits (paralelo)
Commit **solo archivos esta sesión modificó**. Stage por nombre. PROHIBIDO `git add .|-A|-u`. Status muestra ajenos → dejar intactos + reportar. Excepción: Chris "commitea todo".

## Sesiones paralelas — reglas M1-M6 (KISS sin worktrees)

| # | Regla |
|---|---|
| **M1** | Sesiones paralelas TOCAN PRs DE MÓDULOS DISTINTOS — obligatorio. Evita race en `current-state/{m}.md` y `docs/{m}/` |
| **M2** | `docs/pm-nico/process/process-learnings.md` + `docs/pm-nico/roadmap.md` + `MEMORY.md` SOLO los edita `/pm`. Builders nunca |
| **M3** | Tests/CI/Docker SECUENCIAL siempre. Solo una sesión corre `/test-all`/`/dev-up`/`make ci-parity` a la vez. Container/port collision invisible hasta crash |
| **M4** | Claim by commit: `/pm` cambia `Estado: in-progress` en `PR.md` y commitea/pushea **inmediato** antes de cualquier otro trabajo |
| **M5** | `git pull origin development` al inicio Y antes de cada commit. NUNCA pull con diff sin commit |
| **M6** | Bootstrap PM pregunta `¿en qué PI vas a trabajar?` antes de proceder. Chris elige consciente, no la sesión |

Detalle completo + casos conflicto + workflow paso-a-paso → `docs/pm-nico/process/parallel-sessions-protocol.md`.

## Cierre
"eso es todo"/"gracias"/"cierra":
1. `git status --short`
2. Cambios propios → stage nombre + conventional commit + reportar hash
3. Archivos ajenos → reportar intactos
4. Stashes creados → reportar
5. WIP roto → `git stash push -m "WIP: ..."`

## Prohibido
- Feature branches/worktrees sin instrucción
- Worktrees git (sin excepción salvo decisión consciente con Chris)
- Checkout fuera development/main
- Tree sucio ajeno
- Cerrar sin commit/reporte
- Push origin main sin aprobación (= deploy prod)
- Builders editando `docs/pm-nico/process/process-learnings.md` / `roadmap.md` / `MEMORY.md` (solo PM)
- Tests/Docker dos sesiones a la vez
