---
globs: "**/*"
description: Git workflow and safety rules
---

# Git Safety Rules

## Branch Model
- **`development`** = única rama de trabajo. Todo el código va aquí.
- **`main`** = producción. Solo merges de `development` durante pase a producción.
- **NUNCA crear feature branches, worktrees, ni ramas adicionales** salvo instrucción explícita del usuario.

## Commit Format
Conventional Commits: `<type>(<scope>): <description>`

Types: `feat`, `fix`, `refactor`, `docs`, `test`, `chore`, `perf`, `ci`

## Safety
- Always review `git status` before staging
- **Stagear por nombre siempre** (`git add path/to/file`). Nunca `git add .`, `git add -A` ni `git add -u` — otras sesiones paralelas pueden tener WIP en el working tree. Ver `parallel-safety.md` → "Scope de commits".
- Never commit `.env`, `.env.prod`, credentials, or secrets
- Never force push to `main`
- Never amend published commits without explicit approval
- Never create branches or worktrees without explicit user instruction
