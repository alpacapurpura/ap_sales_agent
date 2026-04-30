# Parallel Safety (OBLIGATORIO)

Chris multi-instancia Claude Code WSL. BLOQUEANTE. Mismo workdir, mismo branch (`development`), mismo filesystem. Cada sesión commitea SU trabajo.

## Branches
`development` única rama trabajo. `main` solo prod. NUNCA feature branches/worktrees/release/hotfix.

## Worktrees PROHIBIDOS
Worktrees git = pierde trabajo (Chris perdió 1 semana previa). Sesiones paralelas SIEMPRE mismo workdir mismo branch.

## NO PULL
**`git pull` PROHIBIDO sin excepción.** No pull al inicio, no pull antes commit, no pull al cierre.

Razón: dos sesiones paralelas que pull se desincronizan vs su contexto in-memory; conflictos al pull sobreescriben WIP de la otra. Filesystem compartido ya da el "sync" — cada sesión ve cambios de la otra al hacer `git status` o leer archivos.

Si push falla por non-fast-forward → STOP, reportar a Chris. Chris coordina manualmente.

## NO FORCE PUSH
`git push --force` / `--force-with-lease` PROHIBIDO. Reescribe historia commiteada por otras sesiones.

## NO REVERT sin aprobación
`git revert <commit>` puede sobreescribir trabajo paralelo (filesystem compartido). Solo con aprobación explícita Chris.

## Inicio conversación
Antes de actuar: `git status --short && git branch --show-current && git log --oneline -3`.
- `development` limpio → proceder.
- `main` limpio → `git checkout development`.
- Otra rama → switch a `development`.
- Tree sucio con archivos propios pendientes → PARAR: reportar, ofrecer A) commit B) stash C) descartar (solo si Chris pide). No empezar hasta limpio.
- Tree sucio con archivos AJENOS (otra sesión activa) → proceder pero NO TOCAR esos archivos. Reportar lista.

## Scope commits (paralelo)
Commit **solo archivos esta sesión modificó**. Stage por nombre. PROHIBIDO `git add .|-A|-u`. Status muestra ajenos → dejar intactos + reportar. Excepción: Chris "commitea todo".

Pre-commit hooks (ruff/format) corren native — ningún `--no-verify`.

## Sesiones paralelas — reglas M1-M8

| # | Regla |
|---|---|
| **M1** | Sesiones paralelas TOCAN PRs DE MÓDULOS DISTINTOS por default. Reduce probabilidad colisión real (misma función misma línea). NO bloqueante — colisiones cross-módulo OK con regla M8 |
| **M2** | `docs/pm-nico/process/process-learnings.md` + `docs/pm-nico/roadmap.md` + `MEMORY.md` SOLO los edita `/pm`. Builders nunca |
| **M3** | Tests/CI/Docker SECUENCIAL siempre. Solo una sesión corre `/test-all`/`/dev-up`/`make ci-parity` a la vez. Container/port collision invisible hasta crash |
| **M4** | Claim by commit: `/pm` cambia `Estado: in-progress` en `PR.md` y commitea/pushea **inmediato** antes de cualquier otro trabajo |
| **M5** | NO pull. NO force push. NO revert sin aprobación. Push falla → STOP, reportar Chris |
| **M6** | Bootstrap PM pregunta `¿en qué PI vas a trabajar?` antes de proceder. Chris elige consciente, no la sesión |
| **M7** | Subagentes reciben paths PRIMARIOS de su PR + permiso lectura todo el repo + regla "extend, no destroy" sobre ajenos. PM prefija PI completo en prompts (doble PR-{n} en PIs distintos confunde paths) |
| **M8** | Tocar archivos de otra sesión paralela PERMITIDO si: (a) entendés lo que el otro hizo leyendo el archivo, (b) tu cambio extend/append (no replace ni borra), (c) si rompe trabajo del otro → STOP escalate Chris. Filosofía Chris (2026-04-29): probabilidad colisión real = baja, mismo código compartido OK |

Detalle completo + casos conflicto + workflow paso-a-paso → `docs/pm-nico/process/parallel-sessions-protocol.md`.

## Cierre
"eso es todo"/"gracias"/"cierra":
1. `git status --short`
2. Cambios propios → stage nombre + conventional commit + reportar hash
3. Archivos ajenos → reportar intactos (no commit, no descartar)
4. Stashes creados → reportar
5. WIP roto → `git stash push -m "WIP: ..."`

## Prohibido
- `git pull` (cualquier forma)
- `git fetch && merge`
- `git push --force` / `--force-with-lease`
- `git revert` sin aprobación Chris
- `git reset --hard` sin aprobación Chris
- `git add .` / `-A` / `-u`
- `git commit --no-verify`
- Feature branches / worktrees / release branches
- Checkout fuera `development`/`main`
- Tree sucio ajeno tocado
- Cerrar sin commit/reporte
- Push `origin main` sin aprobación (= deploy prod)
- Builders editando `docs/pm-nico/process/process-learnings.md` / `roadmap.md` / `MEMORY.md` (solo PM)
- Tests/Docker dos sesiones a la vez
