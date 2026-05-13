---
ticket: T-9
title: "Deploy infrastructure verify + architectural plan re-scope (formerly Vercel reconfig)"
date: 2026-05-16
session: 10
owner: /pm Opus inline (re-scoped after Chris Q2 Sesion 10)
verdict: done
state_transition: draft → done
re_scoped_from: "Vercel reconfig + CF tunnel verify"
re_scope_reason: "Architect wrong assumption — Nicolify does NOT use Vercel. Chris ratified Sesion 10 Q2: 'cada marca tendrá su propio deploy ya que cada una manejará su propio dominio, su propio servidor (VPS), su propio docker compose, docker file, etc.'"
---

# T-9 — Deploy infrastructure verify + per-brand architectural plan

> **Sesion 10 Q2 ratificación:** original T-9 spec ("Vercel reconfig") obsolete — Nicolify uses self-hosted Docker + GHCR + GitHub Actions + Cloudflare Tunnel. Per Chris architectural framework "cada marca su propio deploy", T-9 closes as documentation + verify; production workflow migration deferred to future per-brand extraction stories.

## Pre-execution diagnosis

**Real Nicolify deploy stack (verified inline):**

| Component | Reality |
|---|---|
| **Production build/deploy** | GitHub Actions `.github/workflows/deploy-prod.yml` → push to `AISALESHT main` triggers Docker build + GHCR push (`ghcr.io/alpacapurpura/visionarias-{backend,frontend}`) + self-hosted server deploy |
| **dev-app.nicolify.com** | Cloudflare Tunnel via `cloudflare-tunnel` container in AISALESHT docker-compose.yml line 454, routing to `visionarias_client_dev:3000` (Next.js dev server, mounts `AISALESHT/frontend:/app`) |
| **app.nicolify.com** | Production server (self-hosted VPS) |
| **Vercel** | ❌ NOT used (architect wrong assumption) |

## Acceptance verify (Sesion 10 inline)

| Check | Result |
|---|---|
| `visionarias_client_dev` container running | ✅ UP 7 hours (healthy) — port 3000 internal |
| `cloudflare-tunnel` container running | ⚠ DOWN — Exited (0) 5 days ago (2026-05-08, pre-Sesion 9, NOT caused by Story 10) |
| `dev-app.nicolify.com` reachable | ⚠ HTTP 530 — tunnel container down causing Cloudflare-side failure (pre-existing) |
| FE volume mount intact | ✅ AISALESHT/frontend/:/app preserved (dual-state with luana-platform/nicolify/frontend/ also rsync'd) |
| `deploy-prod.yml` workflow accessible | ✅ Present in AISALESHT/.github/workflows/ — unmodified by Sesion 9/10 |

**Regression risk:** Zero. Tunnel down is pre-existing operational state. Story 10 did NOT modify Cloudflare config, AISALESHT docker-compose, or `deploy-prod.yml`.

## Architectural plan — "each brand own deploy" (Chris framework Sesion 10 Q2)

**Long-term vision (post-Story 10):**

```
luana-platform/                         (shared monorepo — NO deploy)
├── core/@luana/*                        (shared packages: format, hooks, ui-kit, schemas, design-tokens, api-client)
├── core/luana-core-*                    (shared engines: campaigns, extension-sdk, etc.)
└── nicolify/                            (transient — Story 10 dual-state)
    ├── frontend/                        ← will extract to nicolify-brand-repo
    └── backend/                         ← will extract to nicolify-brand-repo

nicolify-brand-repo/                    (FUTURE — per-brand independent deploy)
├── frontend/                            (consumes @luana/* via pnpm workspace OR git submodule)
├── backend/                             (consumes luana_core_* via pip git+ OR submodule)
├── docker-compose.yml                   (brand-specific compose)
├── Dockerfile.{frontend,backend}        (brand-specific Dockerfiles)
├── .github/workflows/deploy-prod.yml    (brand-specific deploy → own VPS, own GHCR namespace)
├── cloudflared/config.yml               (brand-specific tunnel routing dev-app.<brand>.com)
└── docs/                                (brand-specific SSoT functional)

vitalia-brand-repo/                     (FUTURE — own deploy stack)
comunify-brand-repo/                    (FUTURE)
lupulo-brand-repo/                      (FUTURE)
```

**Per-brand ownership scope:**
- Own domain DNS (`app.<brand>.com` + `dev-app.<brand>.com`)
- Own VPS/cloud server (separate billing, separate scaling)
- Own `docker-compose.yml` (brand-specific service composition)
- Own `Dockerfile.*` (brand-specific build args, base images, optimization)
- Own `deploy-prod.yml` GH Actions workflow (push to brand-repo `main` triggers brand-specific deploy)
- Own Cloudflare Tunnel routing (`dev-app.<brand>.com` → brand-specific local dev container)
- Own GHCR namespace (`ghcr.io/alpacapurpura/<brand>-{backend,frontend}`)

**Shared (`luana-platform` consumes):**
- TypeScript packages (`@luana/*`) via `pnpm` workspace (or future npm registry publish)
- Python packages (`luana_core_*`) via `pip install git+https://...@luana-platform` (or future PyPI publish)

## What T-9 does NOT do (per Sesion 10 Q2 ratification)

1. ❌ **NO Vercel project migration** — never used.
2. ❌ **NO `deploy-prod.yml` migration** — workflow stays in AISALESHT until per-brand extraction story creates `nicolify-brand-repo`. Post-T-14 archive will retire `deploy-prod.yml` AISALESHT-side; new brand repo will spawn its own.
3. ❌ **NO GHCR image rename** — `visionarias-{backend,frontend}` keeps name until brand repo creation.
4. ❌ **NO Cloudflare Tunnel reconfig** — config stays in AISALESHT docker-compose.yml until brand extraction. Tunnel down state is operational (Chris can `docker compose up tunnel` when needed).
5. ❌ **NO CF DNS reconfig** — `dev-app.nicolify.com` remains pointed to current tunnel ID.

## Outstanding items deferred to future per-brand extraction story

| Item | Owner | Notes |
|---|---|---|
| Create `nicolify-brand-repo` | `/pm` + Chris (new outcome story) | Extract from `luana-platform/nicolify/` post-Story 10 stabilization |
| Migrate `deploy-prod.yml` to brand repo | brand extraction story | Update paths from AISALESHT-relative to brand-repo-relative |
| Brand-specific Cloudflare Tunnel config | brand extraction story | Move tunnel container + config from AISALESHT to brand repo |
| Brand-specific Dockerfiles + compose | brand extraction story | Lift from AISALESHT/{backend,frontend}/Dockerfile + docker-compose.yml |
| `make ci-parity` brand-specific config | Story 10 T-12 + brand extraction | Root-level moves to luana-platform per Decisión 8 (cross-brand pattern); per-brand overrides in brand repo |
| dev-app.<brand>.com tunnel reconfig | brand extraction story | Each brand owns its tunnel ID + DNS |

## Files modified

### AISALESHT
- `docs/product/stories/luana-nicolify-migration/T-9-impl-log.md` — NEW (this file)
- `docs/product/stories/luana-nicolify-migration/06-tickets.yaml` — T-9 state update (in commit)
- `docs/product/outcomes/luana-platform-migration.md` — architectural plan addendum (in commit)

### luana-platform
- No changes (T-9 is documentation + verification only).

## Cost estimate

| Operation | Tokens (est) | Cost USD (est) |
|---|---|---|
| /pm Opus inline diagnosis + verify + doc | ~8k | ~$0.50 |
| **T-9 total** | ~8k | **~$0.50** |

Way under $300-500 original estimate (re-scope from Vercel work eliminated bulk).

## Verdict

`done` — T-9 closed as documentation + verify. Real production workflow migration deferred to future per-brand extraction stories per Chris architectural framework "cada marca su propio deploy".

**T-11 (Playwright smoke E2E) + T-12 (ci-parity root migration) unblocked.**

## Cross-reference

- Spec original: `06-tickets.yaml` § T9 (obsolete content, status re-scoped)
- Chris ratification: Sesion 10 Q2 free-form text
- Stack reality grep evidence: `.github/workflows/deploy-prod.yml`, `docker-compose.yml:454`
- Outcome doc addendum: `docs/product/outcomes/luana-platform-migration.md` (architectural plan section)

Last line: `done -> docs/product/stories/luana-nicolify-migration/T-9-impl-log.md`
