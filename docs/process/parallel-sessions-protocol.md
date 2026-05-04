# Parallel Sessions Protocol (M1-M8)

> Migra de `.claude/rules/parallel-safety.md`. Owner: `/pm`.
> Chris corre múltiples Claude Code WSL con mismo workdir + branch `development`.
> Cada sesión commitea SU trabajo.

## Contexto

- Branch única `development`. `main` = prod (push = deploy auto).
- NUNCA worktrees / feature branches / release / hotfix.
- Filesystem compartido entre sesiones.

## Reglas M1-M8

### M1 — Default: PRs de módulos distintos

Sesiones paralelas tocan PRs DE MÓDULOS DISTINTOS por default. Cross-módulo OK con M8 escalation.

### M2 — Owner único de SSoT

Solo `/pm` modifica:
- `docs/process/learnings.md`
- `docs/product/roadmap.md`
- `docs/product/INDEX.md`
- `~/.claude/projects/.../memory/MEMORY.md`

Builders / dev-team / auditor: NUNCA tocan estos.

### M3 — Tests/CI/Docker SECUENCIAL

Una sesión a la vez:
- `/test-all`
- `/test-backend`
- `/test-frontend`
- `/dev-up`
- `make ci-parity`
- `make dev`

Razón: container/port collision invisible hasta crash.

### M4 — Claim by commit

`/pm` cambia `Estado: in-progress` en `PI.md` / `checkpoint.md` + commit/push **inmediato**. Pre-claim. Otra sesión que pull/lee verá el claim.

### M5 — NO pull / NO force / NO revert

- `git pull` PROHIBIDO sin excepción
- `git push --force` / `--force-with-lease` PROHIBIDO
- `git revert` PROHIBIDO sin aprobación Chris
- Push falla non-fast-forward → STOP, reportar

### M6 — PM bootstrap pregunta

`/pm` al activar pregunta `¿en qué PI/sprint/story?` antes proceder. NO asume default.

### M7 — Subagentes paths PRIMARIOS

Subagentes (`/architect-{be,fe,agentic}`, `/dev-team`, `/auditor`):
- Reciben paths PRIMARIOS del story (handoff explícito)
- Read-all permitido (lectura cross-story OK)
- "Extend, no destroy" en archivos ajenos (M8)

### M8 — Tocar archivos otra sesión

OK si:
- (a) entendés leyendo
- (b) extend/append no replace
- (c) si rompe → STOP escalate Chris

Filosofía Chris (2026-04-29).

## Inicio sesión

```bash
git status --short
git branch --show-current
git log --oneline -3
```

- `development` limpio → proceder
- `main` limpio → checkout `development`
- Otra rama → switch `development`
- Tree sucio archivos propios → reportar, ofrecer commit/stash
- Tree sucio archivos AJENOS → proceder NO TOCAR esos. Reportar lista.

## Cierre sesión

`"eso es todo"` / `"gracias"` / `"cierra"` / `/cierra-limpio`:

1. `git status --short`
2. Cambios propios → stage por nombre + conventional commit + reportar hash
3. Archivos ajenos → reportar intactos
4. Stashes → reportar
5. WIP roto → `git stash push -m "WIP: ..."`

## Prohibido

- `git pull` (cualquier forma)
- `git fetch && merge`
- `git push --force` / `--force-with-lease`
- `git revert` sin aprobación
- `git reset --hard` sin aprobación
- `git add .` / `-A` / `-u`
- `git commit --no-verify`
- Feature branches / worktrees
- Checkout fuera `development` / `main`
- Tree sucio ajeno tocado
- Cierre sin commit / reporte
- `git push origin main` sin aprobación
- Builders editando `learnings.md` / `roadmap.md` / `MEMORY.md`
- `/test-all` / Docker dos sesiones simul

## Conflict resolution

Si encontrás archivo modificado por otra sesión:
1. **NO sobreescribir.** Leer primero.
2. Si conflict de scope → escalate Chris.
3. Si append-friendly (logs, IMPL-LOG, history) → append OK.
4. Si replacement obvio (typo, refactor) → STOP + reportar antes proceder.
