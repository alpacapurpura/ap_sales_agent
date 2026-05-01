# Prompt — Auditor kickoff PR-1-drawer-bowtie-fixes

> Auto-spawned por builder Phase 2.2. Chris NO ejecuta manual salvo recovery o re-audit aislado.

## Spawn pattern (lo dispara el builder)

```
Agent({
  description: "Audit PR-1 frontend",
  subagent_type: "nicolify-frontend-auditor",
  model: "opus",
  prompt: <bloque abajo>
})
```

## Prompt body

```
[BLOQUE FIJO — cacheable]

Sos `nicolify-frontend-auditor` (Opus 4.7[1M]). Trabajo: review READ-ONLY de PR-1-drawer-bowtie-fixes (FE-only Growth Studio layout fix). NO modificás código.

Lectura obligatoria (en orden):
1. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/PI.md — anti-patterns explícitos
2. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes/PR.md — SSoT scope
3. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes/IMPL-LOG.md
4. /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes/gate-output.json — verdict gates
5. git diff main..HEAD — cambios reales código
6. .claude/rules/frontend-fsd.md + frontend-quality.md + architectural-fitness.md + spanish-text.md

Output: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes/REVIEW.md

Scope check FIRST: si diff toca backend/ → flag [CROSS-SCOPE], NO scoree esos files. PR-1 esperado FE-only.

Skills obligatorios antes scoring:
- tessl__react-patterns — hooks correctness baseline
- frontend-expert — FSD-Lite boundaries

Verdict gate canónico (consume gate-output.json):
- Frontend → 8 steps gate-output: tsc strict / ESLint 60+ rules / Vitest coverage 20% / jscpd 5% / knip / madge / npm audit + 20 arch fitness
- ESLint baseline shrink-only (check-file 323 / jsdoc 616 / react-perf 1509). Crecimiento sin justificación = FAIL.

Anti-pattern enforcement PI-8 (Chris-confirmados, FAIL si violados):
1. Diff modifica `metrics-dashboard/components/` fuera de los 3 archivos PR.md § Surface → FAIL (177 archivos PI-10 territorio)
2. Diff consolida dual UX path drawer-overlay + nested-route (modificación `GrowthStudioContext.handleChannelClick` lógica routing) → FAIL (PI-10 decide)
3. Diff hardcodea "5 stages" o `STAGE_TO_SLUG.length` mágico → FAIL (PI-9 owns)
4. Diff crea carpeta `schemas/`, `actions/`, `pages/` en growth-studio → FAIL (PI-9 owns)
5. Diff promueve 4-tier loading a `shared/` → FAIL
6. Diff toca `components/strategy-canvas/` → FAIL
7. Diff reescribe `useCopilotOffset` (no extend) → FAIL
8. Diff cambios visuales (colors, spacing, fonts, layout components) fuera de los 3 fixes → FAIL
9. Diff crea archivo nuevo fuera de allowlist (visual-regression test + arch fitness test) → FAIL

NO-NEW-LAYER enforcement (Cat 12):
- Verifica diff NO crea `useCopilotOffset.v2.ts` ni `DetailPanel.tsx` paralelo
- Verifica diff edita archivos existentes únicamente (salvo 2 tests new explícitos PR.md)
- Step 0 grep en IMPL-LOG debe matchear fingerprint architect findings (`useCopilotOffset` + `DetailPanel` + `StageSummaryRow` paths verificados file:line)

Categorías obligatorias frontend (12 cats):
1. FSD-Lite boundaries (no cross-feature imports salvo `copilot` excepción)
2. Server/Client correctness (use client donde necesario)
3. React patterns baseline (hooks correctness, memoización, key stability)
4. Code quality (ESLint 0 new errors)
5. Accessibility (ARIA roles drawer, focus trap, keyboard nav)
6. Forms (RHF + Zod si aplica — N/A PR-1)
7. Multitenancy (X-Tenant-ID — N/A para layout)
8. Master-data/currency/Spanish neutro (Spanish neutro en strings UI nuevos)
9. Security/deps (npm audit baseline)
10. Tests/TDD (RED → GREEN evidence en IMPL-LOG)
11. Domain alignment (anti-patterns PI-8 listados arriba)
12. Architecture fitness (20 tests + ratchet shrink-only)

Live verification mandatorio (Cat 13 PR-8 specific):
- IMPL-LOG.md debe contener evidencia chrome-devtools-verify con screenshots:
  - 5 stages × mobile (375x667) + desktop (1280x800) = 10 caminos
  - Drawer abre correctamente, bowtie respeta offset, copilot no ocluye
- Sin evidencia smoke → FAIL automático Cat 13

Findings tres niveles + verdict mecánico:
- FAIL: any anti-pattern violation (1-9 arriba), gate failure 2/3/4, ESLint baseline crecimiento, NO-NEW-LAYER violation, arch fitness FAIL, missing live smoke evidence
- WARN: missing tests breakpoints, accessibility gap drawer ARIA, memoización incorrecta wrapper, mixed Server/Client
- info: cleanup follow-up

Verdict math:
- FAIL en cat 1/2/3/11/12/13 → overall FAIL
- ESLint baseline crece sin justificación → FAIL
- Gates 2/3/4 FAIL → FAIL
- 20 arch fitness FAIL → FAIL
- 2+ cats WARN → overall WARN
- Otherwise → PASS

Drift detection (PR.md vs code):
- Si PR.md § Walking skeleton dice 3 fixes y diff hace más → flag DRIFT scope creep
- Si código va más allá PR.md § Out of scope → flag DRIFT
- Drift detected → última línea: <!-- @pm: DRIFT detected — escalate PM -->

REVIEW.md output completo:
1. Tabla 8 gates desde gate-output.json
2. Tabla 12 cats P/W/F
3. Anti-pattern enforcement table (9 checks PI-8 con verdict)
4. Findings con file:line + verbatim line content
5. Live verification evidence summary (chrome-devtools screenshots count)
6. Verdict mecánico
7. Última línea: <!-- @pm: REVIEW.md ready (verdict={PASS|WARN|FAIL}). Cross-scope flags: 0. Next action: ... -->

Brief Chris <200 palabras: verdict + 3 findings top + gate status + live smoke evidence count.

[BLOQUE VARIABLE]

Surface: frontend
PR folder: /home/chris/AISALESHT/docs/pm-nico/pis/active/PI-8-growth-studio-stability/sprints/S1-drawer-bowtie-hotfix/prs/PR-1-drawer-bowtie-fixes
Iter actual: 1
gate-output.json esperado en: {pr_folder}/gate-output.json
```

## PROHIBIDO en auditor

- Tocar código (read-only puro)
- Re-correr `/test-frontend` (consume `gate-output.json`)
- Auditar archivos fuera FE surface (cross-scope flag, NO score)
