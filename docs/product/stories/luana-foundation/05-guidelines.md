---
story_id: luana-foundation
guidelines_version: 1
last_modified: 2026-05-09
ratified_by_chris: false
---

# 05-guidelines — Luana Foundation

> **For:** /dev-team executing Story 1 tickets
> **Status:** DRAFT — pending Chris ratification

## 1. Patterns REQUIRED

### 1.1 Conventional Commits mandatorios

Cada commit en luana-core sigue formato:
```
<type>(<scope>): <short imperative description>

<optional body explaining why, not what>

<optional footer with BREAKING CHANGE: or Closes #N>
```

Types: `feat | fix | docs | chore | refactor | test | perf | ci | build | style`
Scopes: nombre del package afectado (`core-platform`, `core-llm`, etc.) o `repo` para changes a configuración global.

### 1.2 Atomic commits

Cada commit debe ser un cambio coherente. Mejor:
- ✅ `feat(repo): bootstrap pyproject.toml uv workspace`
- ❌ Un commit gigante con 30 archivos heterogéneos.

### 1.3 Branch protection respect

NUNCA `git push --force` a `main`. PR mandatory aunque seas el único developer.

### 1.4 GitHub Packages auth via env var

Local + CI consumen `${GITHUB_TOKEN}` env. NUNCA hardcodear tokens en archivos.

### 1.5 .gitignore consistency

Cada repo (luana-core + 4 brands) tiene `.gitignore` consistente con AISALESHT actual (Python venvs, node_modules, .env, dist/, build/, etc.).

### 1.6 Documentation README short

`README.md` en cada repo es CORTO (5-10 líneas). Detalle vive en `docs/`.

## 2. Patterns FORBIDDEN

### 2.1 git submodule

❌ NO usar git submodule para `.claude-shared`. Usar git subtree exclusively (per ADR-001 OQ5).

### 2.2 Hardcoded tokens

❌ NO commitear PATs, API keys, secret keys. Pre-commit hook bloquea (a futuro).

### 2.3 Cross-repo direct imports en CI

❌ Brand CI NO puede importar archivos directamente del filesystem de luana-core. Solo via GH Packages install.

### 2.4 Brand-aware code en luana-core

❌ NO `if (brand === "vitalia") { ... }` en luana-core. Cero excepciones (ADR-001 §5 rule 1).

### 2.5 Mismas package names en npm + pip

❌ NO duplicar names. Python: `luana-core-X` (snake_case import). TS: `@luana/X` (kebab-case scoped). Distintos namespaces, distintos registries.

### 2.6 Direct push a main

❌ NUNCA. PR mandatory.

### 2.7 `git pull` (legacy parallel-safety)

❌ NO `git pull` en `nicolify` (current AISALESHT) durante Story 1 ejecución. Cualquier cambio que afecte se commitea pero no pull.

## 3. Files in scope (puede tocar /dev-team)

```
docs/architecture/luana-platform/         # update if architectural decisions emerge
docs/product/stories/luana-foundation/    # T-N-impl-log.md, T-N-result.md
```

**Files OUTSIDE Story 1 scope (NUNCA tocar en este story):**

```
backend/src/                              # Story 2-9 territory
frontend/src/                             # Story 2-9 territory
docs/product/stories/{not luana-foundation}/   # other stories
modules/                                  # any of them
```

Story 1 es **infra-only fuera de AISALESHT**. Casi todo el work happens en `~/luana-platform/` (separado de AISALESHT).

## 4. Skills + Tessl tiles a cargar

| Skill | Reason |
|---|---|
| `git-manager` | git workflow, conventional commits, branch protection |
| `commit-push` | Haiku-delegated commits |
| (none agentic, BE, FE per se — story es infra) | |

NO cargar skills agentic (`copilot-expert`, `sales-agent-expert`) — story no toca esos surfaces.

## 5. Owner routing per ticket

| Ticket type | Modelo recomendado |
|---|---|
| `gh CLI` invocations (org create, repo create, branch protection) | Sonnet (mechanical) |
| Skeleton file writes (pyproject.toml, package.json, turbo.json, .releaserc.json) | Sonnet |
| `.claude-shared/` lift desde AISALESHT | Sonnet (cp + git ops) |
| CI workflow YAML drafting | Sonnet |
| Stub package smoke test (F-1, F-2 validators) | Sonnet |
| GitHub Project v2 setup (`gh project create` + custom fields) | Sonnet |
| Documentation drafting (CONTRIBUTING, RELEASES, ARCHITECTURE) | Sonnet |

**Cero tickets requieren Opus.** R23 N/A (story is infra, not agentic production code).

## 6. Local environment requirements

Para ejecutar Story 1 tickets, machine debe tener:

- `gh CLI` 2.x+ authenticated (`gh auth status` clean)
- `git` 2.34+ (subtree subcommand)
- `uv` (Astral) latest
- `pnpm` 9.x+
- `node` 22.x+
- `python` 3.12.x
- `${GITHUB_TOKEN}` env var with `read:packages` + `write:packages` scopes (PAT)

Verify: `~/luana-platform/luana-core/scripts/check-env.sh` (T-2 ticket creates this).

## 7. Pre-commit hook (future, recommended Q4)

A futuro (Story 1 final ticket si Chris ratifica):

```bash
luana-core/.git/hooks/pre-commit:
  - Validate Conventional Commits format on staged commit message
  - Run ruff check on staged Python files
  - Run eslint on staged TS files
  - Block if any check fails
```

## 8. Tests required (Story 1 specific)

Architectural fitness en `luana-core/tests/architecture/`:

```python
# Tests created in T-9 ticket (validation suite):
test_workspace_integrity.py:
  - test_pyproject_workspace_members_resolve()
  - test_package_json_workspaces_resolve()
test_claude_shared_present.py:
  - test_rules_dir_non_empty()
  - test_skills_dir_non_empty()
  - test_agents_dir_non_empty()
test_ci_workflow_complete.py:
  - test_ci_yml_has_4_jobs()
  - test_release_yml_present()
test_branch_protection_enforced.py:
  - test_5_repos_main_protected()  (gh API call, async)
```

## 9. Cross-cutting (ALL tickets must respect)

- ✅ Tenant isolation: N/A (no DB code)
- ✅ Spanish neutro: docs/CONTRIBUTING.md user-facing → Spanish neutro applied
- ✅ PII sanitisation: N/A (no API endpoints)
- ✅ Secrets: ZERO hardcoded en cualquier file. Env vars exclusively.
- ✅ TDD: tests in T-9 BEFORE merge. Smoke validators NF-1..F-9 acted as TDD signals throughout.

## 10. Definition of Done (per ticket)

Cada ticket Story 1 cierra cuando:
1. Files committed con Conventional Commits format
2. PR opened against `main`, CI green
3. Manual smoke validation if applicable (e.g., F-1 publish smoke)
4. T-N-impl-log.md updated con timestamp + commit SHA
5. T-N-result.md describes outcome + artifacts produced

## 11. Dependencies entre tickets

Tickets DAG en `06-tickets.yaml`. Critical paths:
- T-1 (org creation) blocks all
- T-2 (luana-core skeleton) blocks T-3 (CI), T-4 (claude-shared lift), T-5 (release config)
- T-6 (GH Packages smoke) blocks T-7 (brand subtree), T-8 (project v2)
- T-9 (validation suite) runs last

## 12. Open guidelines questions (Chris ratify)

1. ¿Pre-commit hook obligatorio Story 1 final ticket o backlog Sem 4+? (Recomiendo Story 1)
2. ¿README.md de cada brand repo qué contenido inicial? (Stub con link a luana-core ARCHITECTURE.md OK)
3. ¿GitHub Discussions habilitar org-wide para Q&A async cross-repo? (Recomiendo SÍ — gratis y útil)
