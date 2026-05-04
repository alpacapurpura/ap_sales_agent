# Parallel Safety (OBLIGATORIO)

Chris multi-instancia Claude Code WSL. Mismo workdir+branch (`development`)+filesystem. Cada sesión commitea SU trabajo.

## Branches
`development` única. `main` solo prod. NUNCA feature branches/worktrees/release/hotfix.

## Worktrees PROHIBIDOS
Chris perdió 1 semana previa. Sesiones paralelas = mismo workdir mismo branch.

## NO PULL
**`git pull` PROHIBIDO sin excepción.** No inicio, no antes commit, no cierre.

Razón: dos sesiones paralelas pull → desincronizan vs in-memory; conflicts sobreescriben WIP otra. Filesystem compartido ya da sync.

Push falla non-fast-forward → STOP, reportar Chris.

## NO FORCE PUSH
`git push --force`/`--force-with-lease` PROHIBIDO. Reescribe historia.

## NO REVERT sin aprobación
`git revert` puede sobreescribir trabajo paralelo. Solo aprobación explícita Chris.

## Inicio conversación
`git status --short && git branch --show-current && git log --oneline -3`.
- `development` limpio → proceder.
- `main` limpio → checkout `development`.
- Otra rama → switch `development`.
- Tree sucio archivos propios → PARAR: reportar, ofrecer commit/stash/descartar.
- Tree sucio archivos AJENOS → proceder NO TOCAR esos. Reportar lista.

## Scope commits
Stage por nombre solo archivos esta sesión. PROHIBIDO `git add .|-A|-u`. Status muestra ajenos → intactos+reportar. Pre-commit hooks native — `--no-verify` PROHIBIDO.

## Reglas M1-M8

| # | Regla |
|---|---|
| M1 | Sesiones paralelas tocan PRs DE MÓDULOS DISTINTOS por default. Cross-módulo OK con M8 |
| M2 | `docs/pm-nico/process/process-learnings.md` + `roadmap.md` + `MEMORY.md` SOLO `/pm`. Builders nunca |
| M3 | Tests/CI/Docker SECUENCIAL. Una sesión a la vez `/test-all`/`/dev-up`/`make ci-parity`. Container/port collision invisible hasta crash |
| M4 | Claim by commit: `/pm` cambia `Estado: in-progress` PR.md + commit/push inmediato |
| M5 | NO pull. NO force push. NO revert sin aprobación. Push falla → STOP |
| M6 | Bootstrap PM pregunta `¿en qué PI?` antes proceder |
| M7 | Subagentes paths PRIMARIOS PR + read all + "extend, no destroy" ajenos. PM prefija PI completo prompts |
| M8 | Tocar archivos otra sesión OK si: (a) entendés leyendo, (b) extend/append no replace, (c) rompe → STOP escalate Chris. Filosofía Chris (2026-04-29) |

Detalle: `docs/pm-nico/process/parallel-sessions-protocol.md`.

## Cierre

"eso es todo"/"gracias"/"cierra":
1. `git status --short`
2. Cambios propios → stage nombre + conventional commit + reportar hash
3. Archivos ajenos → reportar intactos
4. Stashes → reportar
5. WIP roto → `git stash push -m "WIP: ..."`

## Prohibido

`git pull` (cualquier forma) · `fetch && merge` · `push --force`/`--force-with-lease` · `revert` sin aprobación · `reset --hard` sin aprobación · `add .`/`-A`/`-u` · `commit --no-verify` · feature branches/worktrees · checkout fuera `development`/`main` · tree sucio ajeno tocado · cierre sin commit/reporte · push `origin main` sin aprobación · builders editando `process-learnings.md`/`roadmap.md`/`MEMORY.md` · tests/Docker dos sesiones simul.
