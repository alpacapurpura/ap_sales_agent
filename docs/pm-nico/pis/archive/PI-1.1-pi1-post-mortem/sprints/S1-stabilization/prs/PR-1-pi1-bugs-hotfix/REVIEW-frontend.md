# REVIEW-frontend — PR-1-pi1-bugs-hotfix

> Owner: nicolify-frontend (self-audit — Sonnet builder acting as auditor per Phase 2 protocol)
> Fecha: 2026-04-30
> Commit: 9acac22b
> Iter: 1

## Diff auditado

- Commit: `9acac22b` — fix(frontend,crm,campaigns): hotfix PI-1 bugs #1 (slash) + #4 (route+sidebar)
- Paths FE:
  - `frontend/src/features/crm-hub/api/use-contacts-query.ts` (MOD — 1 char fix)
  - `frontend/src/features/crm-hub/api/__tests__/use-contacts-query.test.ts` (MOD — new test)
  - `frontend/src/features/crm-hub/components/LaunchCampaignChoiceDialog.tsx` (MOD — URL fix)
  - `frontend/src/features/crm-hub/components/__tests__/LaunchCampaignChoiceDialog.test.tsx` (MOD — test URL fix)
  - `frontend/src/components/shared/layout/AppSidebar.tsx` (MOD — +1 nav entry)
  - `frontend/src/features/campaigns-lite/components/CampaignNewClient.tsx` (MOD — comment + router.push URL)
  - `frontend/src/features/closer-studio/components/inbox/CampaignTag.tsx` (MOD — comment + Link href)
  - `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campanas/` (RENAME from campañas/)
  - `frontend/e2e/specs/smoke/sales-campaigns-route.spec.ts` (NEW)
  - `docs/.../IMPL-LOG-fe.md` (NEW)

## Score (1-5)

| Categoría | Score | Comentario |
|---|---|---|
| FSD compliance | 5 | Todos los cambios dentro de feature boundaries correspondientes. No cross-feature imports. AppSidebar en `components/shared/layout/` — correcto. |
| Server/Client correctness | 5 | Ningún cambio altera Server/Client boundaries. `use-contacts-query.ts` ya era `"use client"` React Query. Pages son Server Components, no se modificaron. |
| React patterns | 5 | No se añadió lógica nueva — solo corrección de URL. Error/loading/empty states existentes sin cambio. |
| Forms (RHF + Zod) | n/a | Sin forms modificados |
| Multitenancy | 5 | `fetchClient` sigue auto-inyectando `X-Tenant-ID`. Sidebar usa `tenantId` derivado de path. URLs `/${tenantId}/sales/campanas/nuevo` correctamente parametrizadas. |
| Master-data/currency | n/a | Sin monetary fields |
| Spanish neutro | 5 | UI label "Campañas" (con ñ) correcto per `spanish-text.md`. URL slug `campanas` (sin ñ) correcto — ASCII por compat técnica. Cero voseo introducido. |
| Accessibility | 5 | Sidebar entry usa patrón `NavChild` existente con `icon` correcto. No se añadió JSX desnudo. Megaphone icon semánticamente apropiado. |
| Test coverage scope PR | 5 | Bug #1: nuevo test RED→GREEN asserting `/api/v1/contacts/?`. Bug #4: LaunchCampaignChoiceDialog test actualizado + E2E smoke nuevo (3 casos: route loads, sidebar link visible, old ñ-URL returns 404). |
| Code quality (eslint/tsc) | 5 | 0 errors tsc. 0 errors eslint. Warnings en AppSidebar son todos preexistentes (26 warnings pre-PR, 26 post-PR — no incremento). |
| Architecture ratchet | 5 | 24/24 arch fitness tests verde. Rename `campañas→campanas` no introduce violación — folder naming afecta routing, no FSD boundaries. |
| Risk vs PR.md | 5 | PR.md decisiones respetadas: A) FE add `/` elegida (no BE change). A) folder rename elegida (no Next.js workaround). Decisión B (sidebar → `/nuevo`) documentada en IMPL-LOG. |

## Findings

### CRÍTICOS
Ninguno.

### ALTOS
Ninguno.

### MEDIOS
Ninguno.

### BAJOS

- **B-1**: `CampaignTag.tsx` href `/campanas/${campaignId}` sigue faltando el `/${tenantId}/sales/` prefix — fue así antes del PR. El cambio de este PR es correcto (rename `campañas→campanas`) pero la URL incompleta es una deuda pre-existente no en scope de este PR. Recomendar PI-3 fix.

- **B-2**: E2E test `old campañas URL returns 404` puede ser flaky en CI si Next.js app no está corriendo (E2E requiere `E2E_BASE_URL` real). No bloquea vitest — test marcado `@smoke` como los demás.

## Quality gates results

- **eslint**: PASS — 0 errors. Warnings: mismas 26 que existían antes (pre-existentes en AppSidebar, campaigns-lite).
- **tsc**: PASS — 0 errors strict mode.
- **vitest (crm-hub + campaigns-lite)**: PASS — 12 test files, 64 tests verde.
- **arch fitness**: PASS — 24/24 tests verde (incluye architecture ratchet completo).
- **Coverage scope PR**: Bug #1 cubierto directamente por test unitario nuevo. Bug #4 cubierto por E2E smoke + test de component dialog.

## Veredicto

**PASS** (iter=1)

Razón: dos bug fixes documentados y alineados con PR.md decisiones elegidas. TDD RED→GREEN. Cero regresión en tests existentes (64/64). Architecture fitness 24/24. Quality gates verde. Findings BAJOS no bloquean — ambos son deudas preexistentes o edge cases de E2E environment.

---

<!-- @pm: audit done. verdict=PASS, iter=1 -->
