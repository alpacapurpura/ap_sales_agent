# PR-9-e2e-and-manual-test

## Meta

| Campo | Valor |
|---|---|
| PR ID | PR-9-e2e-and-manual-test |
| Sprint padre | S3-mvp-telegram |
| PI padre | PI-1-campaigns-module |
| Estado | ready |
| Tipo | test |
| Esfuerzo | S |
| Owner PM | /pm |

## Problema (user-facing)

PR-7 + PR-8 entregan outbound conversational pipeline + inbound recognition + stats endpoint + inbox tag UI. Falta validación end-to-end automatizada (Playwright) + checklist manual para que Chris envíe campaña real a 5+ contactos Telegram (último gate antes de declarar MVP S3 visible).

## Outcome esperado

- Playwright E2E spec mockea Telegram Bot API + scheduler + worker → verifica flow: crear campaign → schedule → trigger → task SENT + audit row.
- Manual test checklist documenta proceso Chris para staging real (5+ contactos + verificación inbox tag + stats endpoint).
- S3 cierra con MVP 1 Telegram funcional end-to-end visible.

## Walking skeleton

S effort. Mínimo cohesivo:

1. NEW `frontend/e2e/specs/regression/campaign-launch-telegram.spec.ts` Playwright spec con mocks Telegram Bot API + ARQ trigger.
2. NEW `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S3-mvp-telegram/manual-test-checklist.md` para Chris.
3. IMPL-LOG.md + RESULT.md cierre.

NO nuevo código BE/FE significativo. Cero migración.

## Sub-deliverables

### Sub-A: Playwright E2E spec

Path: `frontend/e2e/specs/regression/campaign-launch-telegram.spec.ts`

Steps:
1. Auth setup: usar Clerk auth fixture existente (regression suite).
2. Mock Telegram Bot API: intercept `https://api.telegram.org/bot*/sendMessage` returning `{ok: true, result: {message_id: 12345}}`.
3. Setup tenant + lead with `telegram_id` via API.
4. Crear campaign DRAFT via API (POST `/api/v1/campaigns`).
5. Add 1 step CALL_SUBAGENT_BRIEF (POST `/api/v1/campaigns/{id}/steps`).
6. Schedule campaign now+5s (POST `/api/v1/campaigns/{id}/schedule`).
7. Wait OR trigger scheduler tick directly.
8. Verify task status: GET `/api/v1/campaigns/{id}/stats` → `sent_count >= 1`.
9. Verify audit row exists (si endpoint expone).

E2E idempotente — limpiar campaign + lead post-test.

### Sub-B: Manual test checklist

Path: `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S3-mvp-telegram/manual-test-checklist.md`

Sections: pre-flight staging, crear campaña, add segment + step, schedule, trigger, verify outbound delivery, verify inbound recognition, verify stats endpoint, cleanup.

### Sub-C: IMPL-LOG + RESULT cierre

WRITE `IMPL-LOG.md` cronograma + drift + commit hashes. WRITE `RESULT.md` cierre.

## Pre-condición

PR-7 + PR-8 SHIPPED. `git log` muestra `7bed7dea` (PR-8 BE) + `e5bd8448` (PR-8 FE) + `bda7bb2e` (PR-8 close docs).
E2E preflight script `bash scripts/e2e-preflight.sh` PASS.

## Reglas duras

- response_model: PR-9 NO introduce endpoints nuevos.
- Tenant isolation: E2E test usa staging tenant fixture.
- Native WSL: `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=regression campaign-launch-telegram.spec.ts`. NUNCA `make e2e` (Docker crashea).
- Spanish neutro LATAM en checklist.
- Cero migración.
- Mock Telegram Bot API en CI; manual test usa staging real.

## Criterio aceptación

- [ ] E2E spec PASS native WSL.
- [ ] Manual test checklist completo + reviewed por PM.
- [ ] Chris envía campaña real (opcional pre-merge — puede happen post-merge real session).
- [ ] IMPL-LOG.md + RESULT.md llenados.

## Open questions

ZERO.

## Riesgos

| Riesgo | Mitigación |
|---|---|
| E2E flaky por timing scheduler tick | Mock scheduler tick endpoint si existe; sino relax assertion |
| Telegram API mock divergence con prod | Doc: mock matches `sendMessage` 200 response shape; manual test cubre prod |
| Routes `/campañas/nuevo` o `/campañas/{id}` no existen aún | E2E navega via API directly; UI route navigation skipped/xfail |
| 5+ contactos staging requiere setup pre-existente | Documented in pre-flight checklist |
