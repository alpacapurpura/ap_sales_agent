# Handoff prompt · S00 start

> **Pega esto al iniciar conversación nueva para arrancar S00 (PRE-fase).**

---

```
Iniciamos el redesign arquitectónico de sales_agent.

📋 Plan maestro: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase: S00 — Codebase audit + cleanup deprecated + admin migration prep
📂 Doc: docs/domains/sales-agent/redesign-2026-04/phases/S00-codebase-audit-and-cleanup.md

CONTEXTO:
- Es la PRE-fase del plan de 12 fases (S00 + S0..S10).
- Objetivo: snapshot estado limpio antes de tocar arquitectura.
- Borrar feature `/sales/resumen` deprecated. Fix sales redirect + sidebar.
- Audit map entregable para que S0..S10 no rompan callers.
- Streamlit admin migration prep (sales_audit.py post-S1 migration path).
- Spanish neutro scan (loggear, no fix masivo — eso es S7).
- Branch: development limpio.

PROTOCOLO obligatorio:

1. Lee, en orden:
   - docs/domains/sales-agent/redesign-2026-04/README.md
   - docs/domains/sales-agent/redesign-2026-04/00-vision-and-objectives.md (§3 NO TOCAR)
   - docs/domains/sales-agent/redesign-2026-04/01-master-plan.md (DAG)
   - docs/domains/sales-agent/redesign-2026-04/02-architecture-target.md
   - docs/domains/sales-agent/redesign-2026-04/03-phase-protocol.md (10 pasos, incluye Paso 11 code review final)
   - docs/domains/sales-agent/redesign-2026-04/04-principles.md
   - docs/domains/sales-agent/redesign-2026-04/05-tech-debt-log.md (entradas pre-sembradas)
   - docs/domains/sales-agent/redesign-2026-04/06-glossary.md
   - docs/domains/sales-agent/redesign-2026-04/phases/S00-codebase-audit-and-cleanup.md
   - .claude/rules/admin-panel.md
   - .claude/rules/parallel-safety.md
   - .claude/rules/spanish-text.md
   - .claude/rules/frontend-fsd.md
   - .claude/rules/frontend-quality.md

2. Research mandate S00 (Web + Tessl):
   - Next.js App Router safe route deletion 2026.
   - Dependency cruiser Python imports cross-module audit 2026.
   - Streamlit admin page deprecation strategy.

3. Genera audit map:
   - docs/domains/sales-agent/redesign-2026-04/audit/sales-agent-current-state.md
   - docs/domains/sales-agent/redesign-2026-04/audit/admin-migration-plan.md
   Use Explore agent thorough para mapeo cross-module.

4. TDD primero:
   - frontend/e2e/specs/smoke/sales-routes.spec.ts (RED)
   - tests/architecture/test_no_resumen_deprecated_references.py (RED, whitelist growth-studio)

5. Cleanup:
   - Borrar app/(main)/[tenantId]/(dashboard)/sales/resumen/.
   - Update app/(main)/[tenantId]/(dashboard)/sales/page.tsx → redirect a /sales/studio/inbox.
   - Update components/shared/layout/AppSidebar.tsx → borrar entry "Resumen".
   - **NO TOCAR** features/growth-studio/**/Resumen* (Meta Ads, distinto feature).

6. Smoke FE:
   - Manual con npm run dev.
   - Skill chrome-devtools-verify.

7. Spanish neutro scan: grep voseo en sales_agent prompts + closer-studio FE. Loggear hits en 05-tech-debt-log.md severity LOW. NO fixear masivo (eso es S7).

8. Quality gates nativos:
   - cd frontend && npx tsc --noEmit && npx eslint src/ && npx vitest run
   - cd backend && .venv/bin/ruff check src/ tests/ && .venv/bin/pytest tests/admin/ tests/architecture/ -x -q
   - E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke

9. Tech debt log: agregar entradas detectadas durante audit. Ya pre-sembradas algunas (sales_audit.py legacy, sales/page.tsx redirect, sidebar).

10. Verificación funcional (§3 sigue funcionando):
    - Closer Studio inbox/pipeline/frozen renderean.
    - WS /closer-studio emite eventos.
    - Webhooks Telegram/WhatsApp/IG procesan.
    - Buffer + follow-up + frozen detection corren.

11. **PASO 11 — Code review final** (nuevo, ver 03-phase-protocol.md):
    - Verificar callers no rotos.
    - Verificar audit docs útiles (no template vacío).
    - Verificar no introdujiste nuevo coupling.
    - Verificar Spanish neutro logs accionables.

12. Cierre:
    - learnings/S00-codebase-audit-and-cleanup.md (denso, accionable).
    - prompts/S0-start.md refinado con: hash último commit, audit map paths, hooks listos.

13. Commit conventional + push:
    - chore(sales-agent-redesign-s00): cleanup deprecated /sales/resumen + audit map
    - Stage por nombre. NUNCA git add -A.

PRINCIPIOS NO NEGOCIABLES (04-principles.md):
- GoF + DRY + alta cohesión + bajo acoplamiento.
- Anti-parche: redirect interno = parche; borrar limpio.
- TDD obligatorio.
- No-broken-callers (Paso 11).
- Spanish neutro LATAM en user-facing (excepto voz de marca tenant que se aplica en S7).
- Native-first dev.
- Stage por nombre en commits.
- §3 no se toca.
- Sales studio FE vive en frontend/src/features/closer-studio/ (NO sales-studio).
- NO tocar growth-studio Meta Ads ResumenTab/Card/Hook (feature distinta).

Empieza ahora con paso 1.
```
