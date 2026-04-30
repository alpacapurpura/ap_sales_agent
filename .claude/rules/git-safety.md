---
globs: "**/*"
description: Git workflow + safety
---

# Git Safety

- Branches: `development` única rama trabajo. `main` = prod (push = deploy auto). NUNCA feature branches/worktrees/release/hotfix salvo instrucción.
- Commits: Conventional `<type>(<scope>): <desc>` (feat/fix/refactor/docs/test/chore/perf/ci).
- Stage por nombre: `git add path/file`. PROHIBIDO `git add .|-A|-u` (parallel sessions tienen WIP — `parallel-safety.md`).
- `git status` antes stage. NUNCA commit `.env*`/credentials/secrets.
- **PROHIBIDO sin excepción:** `git pull`, `git fetch && merge`, `git push --force`/`--force-with-lease`, `git revert` sin aprobación Chris, `git reset --hard` sin aprobación, `git commit --no-verify`, amend de commits pusheados.
- Push falla non-fast-forward → STOP, reportar Chris. NO `git pull` para resolver.
