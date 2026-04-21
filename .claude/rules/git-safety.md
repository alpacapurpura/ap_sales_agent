---
globs: "**/*"
description: Git workflow and safety rules
---

# Git Safety

## Branch Model
- **`development`** = única rama trabajo. Todo aquí.
- **`main`** = prod. Solo merges desde development en pase.
- **NUNCA feature branches/worktrees/ramas extra** salvo instrucción explícita.

## Commit Format
Conventional: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

## Safety
- Always review `git status` before staging
- **Stage por nombre siempre** (`git add path/to/file`). Nunca `git add .`/`-A`/`-u` — otras sesiones paralelas pueden tener WIP. Ver `parallel-safety.md` → "Scope commits".
- Never commit `.env`, `.env.prod`, credentials, secrets
- Never force push `main`
- Never amend published commits sin aprobación
- Never create branches/worktrees sin instrucción explícita
