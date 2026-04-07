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
- Never `git add .` without reviewing what will be staged
- Never commit `.env`, `.env.prod`, credentials, or secrets
- Never force push to `main`
- Never amend published commits without explicit approval
- Never create branches or worktrees without explicit user instruction
