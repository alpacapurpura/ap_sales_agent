# Prompt — Builder kickoff PR-1-drawer-bowtie-fixes

> Spawn `nicolify-frontend` (Sonnet). Builder spawnea gate-runner Haiku + auditor Opus automáticamente al terminar implement.

## Spawn pattern

```
Agent({
  description: "Build PR-1 drawer-bowtie-fixes",
  subagent_type: "nicolify-frontend",
  model: "sonnet",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable, byte-idéntico entre fix-loop iters]

Sos `nicolify-frontend` (Sonnet). Trabajo: implementar PR-1-drawer-bowtie-fixes (FE-only, layout bug fix Growth Studio) + auto-spawn gate-runner + auditor + fix loop hasta PASS.

Lectura obligatoria (en orden):
1. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/PI.md — outcome + anti-patterns explícitos
2. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/sprint.md
3. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes/PR.md — SSoT scope + walking skeleton + tests requeridos + decisiones diferidas
4. CLAUDE.md (root) — sección "Git Workflow — INVIOLABLE"
5. .claude/rules/frontend-fsd.md + frontend-quality.md + spanish-text.md

Skills obligatorios (invoca via Skill tool ANTES de tocar código):
- frontend-expert — FSD-Lite + Server/Client correctness
- tessl__react-patterns — hooks correctness + a11y baseline
- chrome-devtools-verify — live smoke browser-based mandatorio post-fix

Restricciones DURAS PI-8 (anti-patterns Chris-confirmados):
- Tocás SOLO los archivos listados en PR.md § Surface impactada. Ningún otro archivo.
- NO reescribas `metrics-dashboard/components/` (177 archivos = masa PI-10).
- NO consolidás dual UX path drawer-overlay vs nested-route (decisión PI-10).
- NO hardcodeás "5 stages" en code path (PI-9 owns registry).
- NO creás carpeta `schemas/` ni `actions/` ni `pages/` en growth-studio (PI-9 owns).
- NO promovés 4-tier loading a `shared/` (sin segundo consumer).
- NO tocás `components/strategy-canvas/`.
- NO asumís que `ChannelDetailSidebar` desaparece (PI-10 decide).
- NO new files salvo: `__tests__/visual-regression-drawer-bowtie.test.tsx` + `__tests__/architecture/test-growth-studio-copilot-offset.test.ts`.
- NO reescribir `useCopilotOffset` — solo extend consumers.
- NO cambios visuales (colores, espaciados, tipografía, layout components) — PI-10 territorio.
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify, branches/worktrees.
- Push falla non-fast-forward → STOP, reportar Chris. NO git pull.

Step 0 GATE — Anti-duplication grep (PR.md § Existing systems audit):

Ejecutar literal y pegar SALIDA REAL en IMPL-LOG.md sección "Step 0 grep findings":

```bash
find /home/chris/AISALESHT/frontend/src -name "use-copilot-offset*" 2>/dev/null
grep -rn "useCopilotOffset\|copilotWidth" /home/chris/AISALESHT/frontend/src 2>/dev/null
grep -rn "DetailPanel\|detail-panel" /home/chris/AISALESHT/frontend/src/features/ /home/chris/AISALESHT/frontend/src/components/ 2>/dev/null
grep -rn "z-\[4[0-9]\]\|z-\[5[0-9]\]\|z-\[6[0-9]\]\|z-50\|z-40" /home/chris/AISALESHT/frontend/src/features/copilot/ /home/chris/AISALESHT/frontend/src/components/ui/ 2>/dev/null
grep -rn "StageSummaryRow" /home/chris/AISALESHT/frontend/src/features/growth-studio/ 2>/dev/null
```

Si grep encuentra archivo `useCopilotOffset.v2.ts` o `DetailPanel.tsx` paralelo → STOP. Algo está mal. Escalate PM.

Workflow Phase 1 — IMPLEMENT (TDD strict):

1. RED: escribir tests primero
   - `frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx`:
     - Mobile (viewport 375x667) → ChannelRow click abre drawer → panel z-index numeric > copilot mobile z-index numeric
     - Desktop (1280x800) → bowtie wrapper computed style `padding-right` matches `copilotWidth` cuando copilot expanded
     - Transition mobile↔desktop sin layout shift (CLS metric)
     - Cero regresión: 4-tier loading hooks return data (mock provider)
   - `frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts`:
     - Scan `frontend/src/features/growth-studio/**/*.tsx` por `createPortal\|className="[^"]*\bfixed\b`
     - Para cada match → exigir import de `useCopilotOffset` O uso de `<DetailPanel`
     - Allowlist initial vacía → ratchet shrink-only
   - npx vitest run → tests RED ✓

2. GREEN: implementar 3 fixes
   - Fix 1 — z-index ladder: decidir `z-[60]` panel mobile vs `z-[40]` copilot mobile vía análisis consumers (grep z-50 cross-codebase). Documentar elección IMPL-LOG con justificación.
   - Fix 2 — Bowtie offset: wrap `<StageSummaryRow>` parent en su renderer con `useCopilotOffset()` + `style={{ paddingRight: copilotWidth }}`. Verificar clip-path NO se rompe.
   - Fix 3 — Viewport edges: agregar transitions `useCopilotOffset` a TODOS fixed/portal elements growth-studio (lo que arch fitness ratchet exige).
   - npx vitest run → tests GREEN ✓
   - npx tsc --noEmit → 0 errors
   - npx eslint . → 0 new errors (baseline preservado)

3. CHROME DEVTOOLS VERIFY (mandatorio antes commit):
   - Invocar skill `chrome-devtools-verify`
   - Smoke: navegar dev-app.nicolify.com/{tenantId}/growth-studio
   - Para cada stage (5 stages) × 2 viewports (375x667 mobile + 1280x800 desktop) = 10 caminos
   - Click ChannelRow → verificar drawer abre + bowtie respeta offset + copilot NO ocluye
   - Capturar screenshots evidencia en IMPL-LOG

4. Quality gates locales NATIVE:
   - cd /home/chris/AISALESHT/frontend && npx tsc --noEmit
   - cd /home/chris/AISALESHT/frontend && npx eslint . --max-warnings=$(eslint baseline)
   - cd /home/chris/AISALESHT/frontend && npx vitest run --coverage

5. IMPL-LOG.md completo:
   - Step 0 grep findings (output literal)
   - Decisión z-index final (panel up vs copilot down) + razón
   - 3 fixes implementados con paths + diff resumen
   - Tests verdes (counts)
   - chrome-devtools smoke screenshots evidencia
   - Skills consultados (frontend-expert + react-patterns + chrome-devtools-verify)

6. Stage por nombre + conventional commit:
   - git add frontend/src/components/ui/detail-panel.tsx
   - git add frontend/src/features/copilot/components/CopilotSidebar.tsx (si tocaste)
   - git add frontend/src/features/growth-studio/components/metrics-dashboard/stage-widgets/StageSummaryRow.tsx
   - git add frontend/src/features/growth-studio/__tests__/visual-regression-drawer-bowtie.test.tsx
   - git add frontend/src/__tests__/architecture/test-growth-studio-copilot-offset.test.ts
   - git add docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes/IMPL-LOG.md
   - git commit -m "fix(growth-studio): drawer + bowtie + copilot z-index/offset hotfix (PI-8 PR-1)"
   - git push origin development

Workflow Phase 2 — AUTO-GATE-RUN + AUTO-AUDIT:

Phase 2.1 — Spawn gate-runner Haiku:
   Agent({
     description: "Run /test-frontend gates iter-1",
     subagent_type: "nicolify-gate-runner",
     model: "haiku",
     prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes; <command>: test-frontend; <iter>: 1"
   })
Esperar gate-output.json. Si overall.any_fail=true → fix scope findings, re-stage + re-commit + re-spawn gate-runner.

Phase 2.2 — Spawn auditor Opus:
   Agent({
     description: "Audit PR-1 frontend",
     subagent_type: "nicolify-frontend-auditor",
     model: "opus",
     prompt: "<pr_folder>: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes; iter: 1"
   })
Esperar REVIEW.md output. Lee verdict.

Si verdict = PASS → terminás. Última línea respuesta:
   <!-- @pm: implementación + gate-runner + auditoría done (verdict PASS). PR-1-drawer-bowtie-fixes listo para /pm "PR-1 cerrar" -->

Si verdict = WARN o FAIL → entra Phase 3.

Workflow Phase 3 — AUTO-FIX LOOP (max 3 iteraciones):
- Lee findings file:line del REVIEW. Filtrá findings que tocan paths permitidos PR.md.
- Findings drift PR.md vs código → STOP, escalate PM.
- Findings arquitectónicos (cambian PR scope) → STOP, escalate PM.
- Findings WARN/FAIL dentro scope → fixá, re-run quality gates, conventional commit `fix(growth-studio): address auditor findings iter-{N}`, push.
- Re-spawn gate-runner Haiku + auditor Opus. Iter ++.
- Si iter == 3 y verdict aún ≠ PASS → STOP. Última línea:
   <!-- @pm: implementación done, auditoría WARN/FAIL tras 3 iter. Findings pendientes: {lista}. Escalate /pm "PR-1 fix-loop maxed" -->

Outputs:
- Code + tests committed + pushed origin development
- IMPL-LOG.md completo (Step 0 grep findings + 3 fixes diff + tests verdes + chrome-devtools smoke + Skills + Auto-fix iters si aplica)
- gate-output.json final (Haiku) + iter-N preserved si hubo iteraciones
- REVIEW.md Opus auditor (verdict final)
- Commits conventional: fix(growth-studio): drawer + bowtie + copilot z-index/offset hotfix (PI-8 PR-1)

Reportar a Chris brief <300 palabras: 3 fixes implementados + tests verdes + chrome-devtools smoke evidencia + iter audit + verdict final + bloqueadores escalados PM (si los hay).

[BLOQUE VARIABLE — específico iter-1]

Surface: frontend (FE-only)
PR folder: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes
Modules touched: frontend/src/features/growth-studio + frontend/src/components/ui + frontend/src/features/copilot
Iter actual: 1
```

## Notas

- Auditor + gate-runner los spawnea ESTE builder al terminar implement (Phase 2). Chris NO ejecuta separately.
- Chris recibe respuesta UNA vez con verdict final tras auto-loop.
- Si verdict=PASS → ejecutar `04-pm-close.md` con `/pm`. Si ≠ PASS tras 3 iter → escalate PM.
