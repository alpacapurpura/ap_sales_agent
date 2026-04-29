---
globs: "**/*"
description: Git workflow + safety
---

# Git Safety

- Branches: `development` única rama trabajo. `main` = prod (push = deploy auto). NUNCA feature branches/worktrees salvo instrucción.
- Commits: Conventional `<type>(<scope>): <desc>` (feat/fix/refactor/docs/test/chore/perf/ci).
- Stage por nombre: `git add path/file`. PROHIBIDO `git add .|-A|-u` (parallel sessions tienen WIP — `parallel-safety.md`).
- `git status` antes stage. NUNCA commit `.env*`/credentials/secrets. NUNCA force push `main`. NUNCA amend published sin aprobación.
