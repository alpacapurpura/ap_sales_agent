---
story_id: luana-iam-tenancy-content
spec_version: 1
po_version: 1                                   # ★ self-drafted by /pm per autonomous batch §7.2 pre-auth 2026-05-11 ★
last_modified: 2026-05-11
ratified_by_chris: true                         # pre-auth §7.2 — auto-ratify if stays within ADR-001 + lift mode §7.3
drafted_by: /pm (claude-opus-4-7) lift mode self-draft
authority: SESSION-RESUME-AUTONOMOUS.md §5 Phase C + outcome §7.2 + §7.3
---

# Story 3 — Luana IAM + Tenancy + Content lift

## 1. Why

6 módulos brand-agnostic constituyen el chasis multi-tenant. Lift mecánico habilita
brand bootstraps Stories 11-13 sin tocar Nicolify ni copy-paste código tenant.

## 2. Scope — lift mode (per outcome §7.3)

### 2.1 Constraint: lift mode (same Story 2)

**MUST DO:** lift verbatim, preserve DDD boundaries + names + APIs + tests, add per-package
pyproject.toml at 0.0.1-alpha, update import paths INTERNOS dentro luana-platform.

**MUST NOT DO:** scope expansion, rename, refactor, schema migration changes, publishing,
AISALESHT mutation, cross-brand decisions (brand-agnostic interfaces remain so).

### 2.2 Source → Destination mapping (per 00-story.md)

| Source AISALESHT path | Destination luana-platform path | Package name |
|---|---|---|
| `backend/src/modules/iam/` | `core/luana-core-iam/src/luana_core_iam/` | `luana-core-iam` |
| `backend/src/modules/tenant_profile/` | `core/luana-core-tenant-profile/src/luana_core_tenant_profile/` | `luana-core-tenant-profile` |
| `backend/src/modules/tenant_domains/` | `core/luana-core-tenant-domains/src/luana_core_tenant_domains/` | `luana-core-tenant-domains` |
| `backend/src/modules/commercial_calendar/` | `core/luana-core-commercial-calendar/src/luana_core_commercial_calendar/` | `luana-core-commercial-calendar` |
| `backend/src/modules/social_proof/` | `core/luana-core-social-proof/src/luana_core_social_proof/` | `luana-core-social-proof` |
| `backend/src/modules/assets/` | `core/luana-core-assets/src/luana_core_assets/` | `luana-core-assets` |

**Total: 6 Python packages** (no TS this story).

### 2.3 Tests lifting

Tests lift en mismo commit que su source code:
- `backend/tests/modules/iam/` → `core/luana-core-iam/tests/`
- `backend/tests/modules/tenant_profile/` → `core/luana-core-tenant-profile/tests/`
- etc.

### 2.4 Internal import path updates

Imports DENTRO de luana-platform:
- `from luana_core_iam.application import ...` (NOT `from src.modules.iam...`)
- Deps cross-package: `from luana_core_platform.X import ...` (Story 2 packages OK to consume)

Imports en AISALESHT NO se tocan (Story 10).

### 2.5 Multi-Clerk consideration (ADR-001 §2.5)

`luana-core-iam` MUST stay brand-agnostic. NO hardcoded Clerk app ID / publishable key.
Configuration via env vars / DI / config object pattern (per AISALESHT existing pattern).
Arch fitness test: zero `if brand == ...` o brand-specific keys en iam package.

## 3. Acceptance criteria

### 3.1 Estructura

- [ ] 6 Python packages en `~/luana-platform/core/luana-core-{iam,tenant-profile,tenant-domains,commercial-calendar,social-proof,assets}/` con pyproject.toml `0.0.1-alpha`
- [ ] Cada package registrado en root pyproject.toml `[tool.uv.workspace] members`
- [ ] `cd ~/luana-platform && uv sync --all-packages` GREEN
- [ ] Cross-package imports work (e.g., iam consume luana-core-platform OK)

### 3.2 Tests

- [ ] Cada package: `cd ~/luana-platform && uv run pytest core/luana-core-<name>/tests/` GREEN
- [ ] Mock paths updated to new module locations
- [ ] Existing test count preserved (or documented if any test deferred)

### 3.3 Brand-agnostic IAM

- [ ] No `if brand == ...` / `if tenant.brand == ...` in luana-core-iam source
- [ ] Clerk config via env / DI (preserves AISALESHT pattern)
- [ ] Smoke test: 2 fixture Clerk configs validate JWT correctly (or arch test substitute)

### 3.4 Lint + format

- [ ] `uv run ruff check core/luana-core-*` GREEN

### 3.5 No tocar AISALESHT

- [ ] `git diff <base SHA> HEAD --name-only` in AISALESHT shows ZERO mutations of `backend/src/modules/{iam,tenant_profile,tenant_domains,commercial_calendar,social_proof,assets}/`

### 3.6 No publishing

- [ ] No `publishConfig` / `.releaserc.json` / `release.yml`
- [ ] No semantic-release dep

## 4. Halt criteria (auto-stop + escalate Chris)

1. Cross-module coupling between Story 3 modules + Story 4/5+ modules (e.g., iam imports from crm) — escalate
2. iam runtime requires brand-specific config (would break brand-agnostic invariant) — escalate
3. Auditor REJECTED + 3 auto-fix iter fail
4. Scope expansion needed
5. Cumulative cost > $1500 — soft check-in
6. Test mock paths beyond mechanical translation (require logic refactor)

## 5. Out of scope

- crm/, analytics/, advertising/, social_media/, landing/, connections/ (Story 4)
- brand/, offer/ (Story 5)
- copilot/ (Story 6)
- sales_agent/ (Story 7)
- campaigns/, scheduling/, extension SDK (Story 8)
- GH Packages publishing (Story 9)
- AISALESHT import swap (Story 10)

## 6. Risks

| # | Risk | Severity | Mitigation |
|---|---|---|---|
| 1 | iam coupling with other modules (e.g., crm User model) | Medium | Architect dependency analysis; lift platform port if cross-cuts |
| 2 | tenant_domains Cloudflare integration coupled to Nicolify env | Low | Lift verbatim; env config externalized |
| 3 | Tests with `monkeypatch.setattr('src.modules.X')` requiring path migration | Medium | Lift tests + update mock paths in same commit |
| 4 | commercial_calendar / social_proof / assets dependencies on brand/offer (Story 5) | Low | Cross-check architect; if coupled → defer to Story 5 |
| 5 | Schema migrations remain in AISALESHT alembic (DB single source) | Low (accepted) | Story 9 publishing handles versioning later |

## 7. Scenario coverage

```gherkin
Scenario A — Python package lift per module
  Given backend/src/modules/iam/ exists in AISALESHT
  When /dev-team lifts to core/luana-core-iam/src/luana_core_iam/
  And pyproject.toml created with version 0.0.1-alpha
  And tests lifted to core/luana-core-iam/tests/
  Then cd ~/luana-platform && uv sync --all-packages exits 0
  And cd ~/luana-platform && uv run pytest core/luana-core-iam/tests/ exits 0

Scenario B — Cross-package import works
  Given luana-core-iam needs luana-core-platform (Story 2)
  When pyproject.toml declares dependency on luana-core-platform
  Then uv sync resolves
  And `from luana_core_platform.X import Y` works in luana-core-iam source

Scenario C — Brand-agnostic IAM
  Given luana-core-iam lifted
  When grep -r "brand" core/luana-core-iam/src/
  Then matches are limited to variable names / docstrings (NOT control flow)
  And no hardcoded Clerk publishable key or app ID found in source

Scenario D — No AISALESHT mutation
  Given /dev-team finishes all tickets
  When git diff in AISALESHT
  Then ZERO files under backend/src/modules/{iam,tenant_profile,tenant_domains,commercial_calendar,social_proof,assets}/ modified

Scenario E — Arch fitness ratchet preserved
  Given lifted modules with their existing arch fitness tests
  When running pytest core/tests/architecture/ (or per-package)
  Then 0 new violations
```

## 8. Notes for /architect

- Order: emit dependency graph between 6 modules + Story 2 packages (likely iam → tenant_profile → tenant_domains → rest)
- Granularity: 1 module per ticket OR group of independent modules per ticket
- If commercial_calendar / social_proof / assets are tightly coupled to brand/offer (Story 5), document AND defer those modules to Story 5
- Validator pattern: per-package "uv sync + uv run pytest"; cross-package import smoke
- 05-guidelines.md: explicit READ-ONLY AISALESHT paths + CREATE luana-platform paths
- Multi-Clerk: arch fitness test "no brand-aware code in iam"
