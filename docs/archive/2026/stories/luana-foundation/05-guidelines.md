---
story_id: luana-foundation
guidelines_version: 2                           # ★ revision applied 2026-05-10 ★
last_modified: 2026-05-10
ratified_by_chris: true                         # ★ Chris ratified scope 2026-05-10 ★
revision_notes: |
  v2 (2026-05-10): scope shifted to monorepo + GH Packages deferred.
  Removed: GitHub Packages auth pattern, .npmrc with publishConfig, subtree
  patterns, cross-repo install rules. Added: ADR-driven core changes,
  proprietary header guidance, anti-island enforcement.
  v1 (2026-05-09): superseded.
---

# 05-guidelines — Luana Foundation

> **For:** /dev-team executing Story 1 tickets
> **Status:** READY (post Chris ratification 2026-05-10)
> **Repo target:** `~/luana-platform/` (cloned from `alpacapurpura/luana-platform`)
> **AISALESHT touches:** **NONE** (Story 1 happens entirely outside AISALESHT)

## 1. Patterns REQUIRED

### 1.1 Conventional Commits mandatorios

Cada commit en `~/luana-platform/` sigue formato:
```
<type>(<scope>): <short imperative description>

<optional body explaining why, not what>

<optional footer with BREAKING CHANGE: or Closes #N>
```

Types: `feat | fix | docs | chore | refactor | test | perf | ci | build | style`
Scopes:
- Workspace member name (`core`, `nicolify`, `vitalia`, `comunify`, `lupulo`) when change is scoped to that subfolder
- `repo` para changes a configuración global (root pyproject.toml, CI, .github/)
- `docs` para changes solo en `docs/`

Ejemplos válidos:
- `feat(repo): bootstrap monorepo skeleton uv+pnpm+turborepo`
- `chore(.claude): lift .claude-shared from AISALESHT (initial sync)`
- `feat(ci): bootstrap CI workflow 4 parallel jobs`
- `docs: seed CONTRIBUTING + ARCHITECTURE + ADR README`

### 1.2 Atomic commits

Cada commit debe ser un cambio coherente:
- ✅ `feat(repo): bootstrap pyproject.toml uv workspace` — un archivo, un propósito
- ❌ Un commit gigante con 30 archivos heterogéneos

### 1.3 Branch protection respect

NUNCA `git push --force` a `main`. PR mandatory aunque seas el único developer.
Branch protection en `main`:
- `required_pull_request_reviews.required_approving_review_count: 1`
- `enforce_admins: false` (Chris puede override en emergencias)

### 1.4 ADR-driven core changes

Cualquier cambio que toque `core/**`:
- ✅ Debe haber ADR previo en `docs/architecture/ADR/NNN-<slug>.md`
- ✅ PR description debe linkear ADR
- ❌ PR sin ADR ref para cambio core/ → rechazado

ADR usa template Michael Nygard (lightweight) — ver `docs/architecture/ADR/README.md`.

Story 1 NO toca `core/` directamente (T-5 solo seedea `core/README.md` + `core/pyproject.toml` placeholder). Por lo tanto Story 1 NO requiere ADR per se. ADR-001 ya existe (back-link a outcome doc) y se cita en `docs/ARCHITECTURE.md`.

### 1.5 Conventional Commits enforcement (recommended Q1, deferred if scope tight)

Pre-commit hook que valida formato commit message. Implementar en T-7 (final) si bandwidth alcanza; sino backlog.

### 1.6 .gitignore consistency

Copiar `.gitignore` desde AISALESHT (Python venvs, node_modules, .env, dist/, build/, etc.).

### 1.7 Documentation README short

`README.md` en cada subfolder + repo root es CORTO (5-10 líneas). Detalle vive en `docs/`.

### 1.8 Proprietary license en cada source file (DEFERRED — backlog)

NO requerido en Story 1. License header per file = backlog (Story 9+). Story 1 solo ships `LICENSE` proprietary at repo root.

## 2. Patterns FORBIDDEN

### 2.1 GH Packages publishing setup en Story 1

❌ NO crear `.npmrc` con `publishConfig`. ❌ NO crear `.releaserc.json`. ❌ NO crear `.github/workflows/release.yml`. ❌ NO instalar `semantic-release`. ❌ NO `uv publish` ni `npm publish`.
Todo eso = Story 9 (`luana-v0-1-0-publish`).

### 2.2 Hardcoded tokens

❌ NO commitear PATs, API keys, secret keys. Pre-commit hook bloquea (a futuro).

### 2.3 Cross-subfolder direct imports skipping workspace dep declaration

❌ Brand subfolder NO puede importar archivos de `core/` mediante path relativo (`../core/...`). Debe declarar dep en su `pyproject.toml` via `tool.uv.sources` (workspace ref) o `package.json` via `workspace:*`.

### 2.4 Brand-aware code en core/

❌ NO `if (brand === "vitalia") { ... }` en `core/`. Cero excepciones (ADR-001 §5 rule 1).

### 2.5 Mismas package names en npm + pip

❌ NO duplicar names. Python: `luana-core-X` (snake_case import). TS: `@luana/X` (kebab-case scoped). Distintos namespaces.

### 2.6 Direct push a main

❌ NUNCA. PR mandatory.

### 2.7 `git pull` (legacy parallel-safety)

❌ NO `git pull` en `~/luana-platform/` durante Story 1 ejecución. Single Claude sub Story 1 → no parallel-sessions issue, pero hábito mantiene per `.claude/rules/parallel-safety.md`.

### 2.8 git submodule

❌ NO usar git submodule. Single monorepo elimina necesidad. Si futuro multi-repo refactor → subtree (no submodule) per ADR-001 OQ5.

### 2.9 Touching AISALESHT files

❌ Story 1 NO toca `~/AISALESHT/**` excepto:
- ✅ Read-only `cp -r .claude/` para lift inicial
- ❌ Cualquier `Edit` a archivos AISALESHT

## 3. Files in scope (puede tocar /dev-team)

```
~/luana-platform/                              # ★ todo el work happens AQUÍ ★
├── (ALL files OK to create/edit per ticket)

/home/chris/AISALESHT/docs/product/stories/luana-foundation/
├── T-N-impl-log.md                            # impl log per ticket
├── T-N-result.md                              # result per ticket
└── checkpoint.md                              # state updates only via /pm
```

**Files OUTSIDE Story 1 scope (NUNCA tocar en este story):**

```
~/AISALESHT/backend/src/                       # other stories
~/AISALESHT/frontend/src/                      # other stories
~/AISALESHT/docs/product/stories/{not luana-foundation}/   # other stories
~/AISALESHT/.claude/                           # read-only para lift, no edit
~/AISALESHT/modules/                           # any of them
```

Story 1 es **infra-only fuera de AISALESHT** (excepto los 3 archivos del story propio). Casi todo el work happens en `~/luana-platform/`.

## 4. Skills + Tessl tiles a cargar

| Skill | Reason |
|---|---|
| `git-manager` | git workflow, conventional commits, branch protection |
| `commit-push` | Haiku-delegated commits |

NO cargar skills agentic (`copilot-expert`, `sales-agent-expert`, `brand-expert`, `offer-expert`, etc.) — story no toca esos surfaces. Cargarlos = waste de context tokens.

## 5. Owner routing per ticket

| Ticket type | Modelo recomendado |
|---|---|
| `gh CLI` invocations (branch protection, CODEOWNERS verify) | Sonnet (mechanical) |
| Skeleton file writes (pyproject.toml, package.json, turbo.json, pnpm-workspace.yaml) | Sonnet |
| `.claude-shared/` lift desde AISALESHT (cp + git ops) | Sonnet |
| CI workflow YAML drafting | Sonnet |
| CODEOWNERS + PR template + ADR README drafting | Sonnet |
| Architectural fitness tests bootstrap (pytest skeletons) | Sonnet |
| Documentation drafting (CONTRIBUTING, ARCHITECTURE, RELEASES placeholder) | Sonnet |

**Cero tickets requieren Opus.** R23 N/A (story is infra, not agentic production code per `.claude/rules/tdd-mandatory.md` + R23 rule).

`owner_eligibility: [sonnet, opus]` en todos los tickets.

## 6. Local environment requirements

Para ejecutar Story 1 tickets, machine debe tener:

- `gh CLI` 2.x+ authenticated (`gh auth status` clean) — verify alpacapurpura account
- `git` 2.34+
- `uv` (Astral) latest
- `pnpm` 9.x+
- `node` 22.x+
- `python` 3.12.x
- `${GITHUB_TOKEN}` env var with `repo` scope (PAT for branch protection API calls)

## 7. Pre-commit hook (T-7 si scope alcanza)

A futuro Story 1 final ticket si Chris ratifica:

```bash
~/luana-platform/.git/hooks/pre-commit:
  - Validate Conventional Commits format on staged commit message
  - Run uv run ruff check on staged Python files
  - Run pnpm lint on staged TS files (if any)
  - Block if any check fails
```

Si bandwidth no alcanza → backlog Sem 4+.

## 8. Tests required (Story 1 specific)

Architectural fitness en `nicolify/tests/architecture/`:

```python
# Tests created in T-7 ticket (validation suite):
test_workspace_integrity.py:
  - test_pyproject_workspace_members_resolve()
  - test_pnpm_workspace_members_resolve()

test_codeowners_present.py:
  - test_codeowners_file_exists()
  - test_codeowners_protects_core_paths()

test_adr_folder_present.py:
  - test_adr_readme_exists()

test_pr_template_present.py:
  - test_pr_template_has_required_sections()

test_claude_shared_present.py:
  - test_rules_dir_non_empty()
  - test_skills_dir_non_empty()
  - test_agents_dir_non_empty()
```

## 9. Cross-cutting (ALL tickets must respect)

- ✅ Tenant isolation: N/A (no DB code)
- ✅ Spanish neutro: docs/CONTRIBUTING.md user-facing → Spanish neutro applied per `.claude/rules/spanish-text.md`
- ✅ PII sanitisation: N/A (no API endpoints)
- ✅ Secrets: ZERO hardcoded. Env vars exclusively (only `${GITHUB_TOKEN}` for gh API verifications)
- ✅ TDD: tests in T-7 antes de merge. Validators NF-1..F-6 acted as TDD signals throughout
- ✅ R23 N/A: no agentic production code

## 10. Definition of Done (per ticket)

Cada ticket Story 1 cierra cuando:
1. Files committed con Conventional Commits format
2. PR opened against `main`, CI green
3. Manual smoke validation if applicable
4. T-N-impl-log.md updated con timestamp + commit SHA
5. T-N-result.md describes outcome + artifacts produced

## 11. Dependencies entre tickets

Tickets DAG en `06-tickets.yaml`. Critical path:
- T-1 (clone + branch protection + governance scaffolding) blocks all
- T-2 (skeleton) blocks T-3 (CI), T-4 (claude-shared), T-5 (subfolders), T-6 (docs)
- T-7 (validation suite + arch fitness tests) runs last

## 12. Open guidelines questions

1. ¿Pre-commit hook obligatorio T-7 o backlog Sem 4+? Recomendación: best-effort en T-7, backlog si scope tight.
2. ¿README.md de cada subfolder qué contenido inicial? Stub 5-10 líneas con purpose + scope + link a `docs/ARCHITECTURE.md`.
3. ¿Status check names en branch protection — 4 jobs o `lint`/`test` aggregator? /dev-team decide en T-3 según UI GitHub.
