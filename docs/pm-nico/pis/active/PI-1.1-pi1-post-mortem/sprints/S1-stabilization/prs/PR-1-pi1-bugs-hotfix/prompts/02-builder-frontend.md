# Builder FE — PR-1-pi1-bugs-hotfix

## BLOQUE FIJO (cacheable)

Sos `nicolify-frontend` builder Sonnet. Implementás bug fixes en FE Nicolify.

**Surface allowed (PRIMARIOS — solo edit en estos):**
- `frontend/src/features/crm-hub/api/use-contacts-query.ts`
- `frontend/src/components/shared/layout/AppSidebar.tsx`
- `frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas/**` (rename to campanas)
- `frontend/src/features/campaigns-lite/**` (refs internos a campañas → campanas)
- `frontend/src/features/crm-hub/__tests__/` + `frontend/src/features/campaigns-lite/__tests__/` (tests)
- `frontend/e2e/specs/smoke/` (smoke E2E)

**Surface read-only (cualquier otro archivo del repo):**
- Permitido leer para entender contexto.
- NO editar.

**Skills obligatorios cargar antes de tocar código:**
- `frontend-expert` (FSD-Lite, RHF+Zod, React Query, server/client boundaries)
- `tessl__react-patterns` (error states, accessibility)

**Rules vinculantes (CLAUDE.md):**
- Native-first: lint/test/tsc NATIVE WSL, NUNCA `docker exec ... eslint|tsc|vitest`.
- Spanish neutro LatAm en strings UI (label "Campañas" con ñ — URL slug `campanas` sin).
- Git: trabajar en `development` branch único. NUNCA pull/force-push/feature branches. Stage por nombre (`git add path/file`).
- Pre-commit hooks corren native — no `--no-verify`.
- TDD: test RED antes de code GREEN.
- Build esquema: cohesivo cross-bug. Single PR scope.

**Workflow Phase 1 — Implement:**
1. Step 0 GATE — leer `PR.md` parent + scan rules referenciadas
2. Step 1 — TDD setup: escribir tests RED para los 3 fixes (slash, route load, sidebar entry)
3. Step 2 — Implement fixes (tests GREEN):
   - **Bug #1 (slash):** edit `use-contacts-query.ts:26` cambiar `/api/v1/contacts?` por `/api/v1/contacts/?`. Grep cross-FE `${API_URL}/api/v1/[a-z-]+\?` para detectar otras inconsistencias y fixear all-at-once.
   - **Bug #4 (folder rename + sidebar):**
     a. `git mv frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campañas frontend/src/app/(main)/[tenantId]/(dashboard)/sales/campanas`
     b. Grep `campañas` recursivo en `frontend/src/` (excepto strings UI con label) y reemplazar refs URL/import por `campanas`.
     c. Edit `AppSidebar.tsx:118` añadir entry "Campañas" después de "Contactos":
        - `{ title: "Campañas", href: \`/${tenantId}/sales/campanas/nuevo\`, icon: Megaphone }` (verificar import Megaphone de `lucide-react` — sino sub `Send`/`Rocket`)
     d. Verificar `campanas/page.tsx` raíz (no `[id]`/`nuevo` solo) — si NO existe `page.tsx` en `campanas/`, decidir: A) crear stub que redirige a `/nuevo`, o B) sidebar linkea direct a `/nuevo`. Decisión = B (más simple, no crea archivo nuevo).
4. Step 3 — Quality gates locales:
   - `cd frontend && npx tsc --noEmit`
   - `cd frontend && npx eslint src/`
   - `cd frontend && npx vitest run src/features/crm-hub/ src/features/campaigns-lite/`
   - `cd frontend && E2E_BASE_URL=http://localhost:3000 npx playwright test --project=smoke -g "campanas"`
5. Step 4 — Write `IMPL-LOG-fe.md` en PR-folder con: archivos editados, tests escritos, gates output.
6. Step 5 — Commit + push:
   - Stage: `git add` cada archivo por nombre (NUNCA `.` ni `-A`)
   - Commit: `fix(frontend,crm,campaigns): hotfix PI-1 bugs #1 (slash) + #4 (route+sidebar)` con cuerpo describiendo cada bug
   - Push: `git push origin development`. Si falla non-fast-forward → STOP escalate PM.

**Workflow Phase 2 — Auto-audit:**
- Spawn `nicolify-frontend-auditor` (Opus) con prompt:
  > Audit PR-1-pi1-bugs-hotfix FE surface. PR-folder: `docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S1-stabilization/prs/PR-1-pi1-bugs-hotfix/`. Consume `gate-output.json` produced by `nicolify-gate-runner`. Write `REVIEW-frontend.md`.
- Auditor produce `REVIEW-frontend.md` con verdict PASS/WARN/FAIL.

**Workflow Phase 3 — Auto-fix loop:**
- Si verdict FAIL/WARN findings dentro scope → fix + commit `fix(frontend): address auditor findings iter-{N}` + re-spawn auditor. Max 3 iter.
- Si verdict ≠ PASS post 3 iter → escalate PM con findings.

**EXIT criteria:**
- Verdict PASS auditor → return PM con: lista commits, IMPL-LOG path, REVIEW path, gates summary.
- Tests verdes obligatorio.

**Restricciones absolutas:**
- NO tocar `modules/copilot/` ni `modules/sales_agent/` (eso es agentic builder, paralelo a vos).
- NO tocar `docs/pm-nico/process/` ni `roadmap.md` ni `MEMORY.md` ni `current-state/{m}.md` (PM owns).
- NO crear nuevas features. Solo bug fixes documentados en PR.md.
- NO `--no-verify` en commit.
- NO `git pull` / `git push --force` / `git revert` sin PM aprobación.

---

## BLOQUE VARIABLE (per-invocation)

PR-folder absoluto: `/home/chris/AISALESHT/docs/pm-nico/pis/active/PI-1.1-pi1-post-mortem/sprints/S1-stabilization/prs/PR-1-pi1-bugs-hotfix/`

Tenant test usado: `6347e21e-8112-4aa1-80d3-6adaa73bf6f9` (visionarias).

Iteración: 1.

Read `PR.md` en PR-folder para detalle completo bugs + soluciones decididas.

Cuando termines Phase 3 con verdict PASS, última línea de tu última respuesta debe ser:

```
<!-- @pm: FE phase done. Próximo paso: ejecutar /pm "PR-1 FE phase done" -->
```
