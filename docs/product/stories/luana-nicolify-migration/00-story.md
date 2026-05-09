# Story 10 — Migrate Nicolify to consume Luana

> **Outcome:** luana-platform-migration · **Sequence:** 10/14 · **Pivot story**

## Why

Primer brand consumer de Luana. Valida arquitectura end-to-end ANTES de bootstrappear 3 brands más.

## What

1. Rename GitHub repo `AISALESHT` → `nicolify` (preserve history)
2. Swap imports BE: todos `from src.shared.X` → `from luana_core_X` (~20k LOC affected)
3. Swap imports FE: todos `from "@/components/ui"` → `from "@luana/ui-kit"`, etc
4. Crear `apps/api/`, `apps/web/`, `vertical-saas-marketing/` (probable mínimo — Nicolify ES caso canónico)
5. `brand.config.ts` + `brand.config.py` con configuración Nicolify (theme, plan tiers, voice cloning ON, all sections enabled)
6. Wire Clerk app actual de Nicolify
7. Migrate Alembic history → snapshot v1 frozen + history clean
8. CI/CD pipeline updated for new structure
9. Deploy Nicolify v2.0.0 a cluster K8s (existing or new)
10. **Verify zero functional regression** — full /test-all + /test-frontend + Playwright smoke green

## Acceptance

- [ ] Repo renamed
- [ ] All imports swapped
- [ ] All tests pass (BE 43%+ coverage, FE 20%+ coverage)
- [ ] Playwright smoke green
- [ ] Production deploy successful
- [ ] Nicolify users see ZERO regression (production smoke test 24h)
- [ ] /pm SSoT promotes from `nicolify/docs/product/` to `luana-core/docs/product/` (post-merge)

## Risks

| Risk | Severity | Mitigation |
|---|---|---|
| Imports swap surface massive (20k+ LOC) | High | Automated codemod + tests gate |
| Alembic history collision | Medium | Snapshot frozen v1 strategy (per ADR-001 §5.7) |
| Clerk app credentials env mismatch | High | Smoke test pre-deploy + rollback plan |
| Vertical extensions Nicolify mínima | Low | Document explicitly: Nicolify = canonical case, no vertical-specific overrides |

## Effort: 16-22 tickets, ~6 días
