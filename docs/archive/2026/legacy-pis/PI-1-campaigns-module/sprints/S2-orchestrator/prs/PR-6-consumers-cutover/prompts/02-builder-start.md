# Prompt — Builder kickoff (auto-audit loop)

> Copy-paste este prompt en una nueva sesión Claude Code (o spawn builder vía Agent tool). PM pre-coció contexto. **Builder spawnea auditor automáticamente al terminar — Chris recibe código YA AUDITADO Y CORREGIDO.**

```
Sos `nicolify-{backend|frontend|agentic}`. Trabajo: implementar PR completo + auto-spawn auditor + fix loop hasta PASS.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}/PR.md` — problema + scope
2. `docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}/CONTRACT.md` — schemas + interfaces (SSoT pre-implementación)
3. `docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}/UI-SPEC.md` — solo si frontend, screens + component tree
4. `docs/pm-nico/current-state/{módulo}.md` — capacidades vivas (no duplicar)
5. `.claude/rules/{backend-ddd|frontend-fsd}.md` + `tenant-isolation.md` + `tdd-mandatory.md` + `parallel-safety.md` + `git-safety.md`
6. `CLAUDE.md` (root) — sección "Git Workflow — INVIOLABLE"

**Skills a invocar (si aplica módulo):**
- `{brand-expert | offer-expert | copilot-expert | sales-agent-expert | metrics-expert | manychat-expert}`

**Restricciones DURAS (regla M7):**
- Tocás SOLO archivos del PR-{n}-{slug}. Lista paths permitidos derivada del CONTRACT.
- NO tocás archivos de otros PRs activos (sesión paralela). `git status` muestra ajenos → DEJAR INTACTOS.
- PROHIBIDO: `git pull`, `git fetch && merge`, `git push --force`, `git revert`, `git reset --hard`, `git add .|-A|-u`, `git commit --no-verify`, branches/worktrees.
- Push falla non-fast-forward → STOP, reportar Chris. NO `git pull` para resolver.

**Workflow Phase 1 — IMPLEMENT:**
1. TDD strict: tests RED ANTES implementación. Capa por capa (domain → infrastructure → application → api).
2. Implementar cada sub-deliverable del CONTRACT secuencialmente.
3. Migrations idempotentes (BE) o componentes FSD-compliant (FE).
4. Quality gates NATIVE (sin docker exec):
   - BE: `cd backend && .venv/bin/{ruff|pytest|mypy}`
   - FE: `cd frontend && npx {tsc|eslint|vitest}`
5. Si bloqueado arquitectónicamente → STOP, append a IMPL-LOG.md, devolver control a PM (NO inventar solución).
6. Llenar IMPL-LOG.md completo (sub-deliverables, decisiones, tests, gates, commits).
7. Stage por nombre + conventional commit + push origin development.

**Workflow Phase 2 — AUTO-AUDIT (obligatorio, no opcional):**
8. **Spawn auditor inmediato** vía Agent tool con `subagent_type: nicolify-{backend|frontend}-auditor`. Pasale prompt completo de `prompts/03-auditor-start.md` (path absoluto del PR-folder).
9. Esperá REVIEW.md output. Lee verdict.
10. **Si verdict = PASS** → terminás. Última línea respuesta:
    `<!-- @pm: implementación + auditoría done (verdict PASS). PR-{n} listo para /pm "PR-{n} cerrar" -->`
11. **Si verdict = WARN o FAIL** → entra Phase 3.

**Workflow Phase 3 — AUTO-FIX LOOP (max 3 iteraciones):**
12. Lee findings file:line del REVIEW.md. Filtrá findings que tocan paths PR-{n} (regla M7 — no fixás findings de otros PRs).
13. Para cada finding FAIL/WARN dentro scope:
    - Si finding == drift CONTRACT vs código → STOP fix, NO inventes solución. Append IMPL-LOG bloqueador "Drift CONTRACT — escalate PM". Devuelve control con verdict actual + nota.
    - Si finding == missing test/typo/hardcoded value/refactor menor → fixá.
    - Si finding == arquitectónico (cambia design CONTRACT) → STOP, escalate PM.
14. Quality gates re-run NATIVE.
15. Stage por nombre + conventional commit `fix(scope): address auditor findings iter-{N}` + push.
16. Re-spawn auditor (Phase 2 step 8). Iter ++.
17. Si iter == 3 y verdict aún ≠ PASS → STOP. Append IMPL-LOG "Max iterations reached, escalate PM". Última línea:
    `<!-- @pm: implementación done, auditoría WARN/FAIL tras 3 iter. Findings pendientes: {lista}. Escalate /pm "PR-{n} fix-loop maxed" -->`

**Outputs:**
- Code + tests + migrations en codebase (committed + pushed)
- `IMPL-LOG.md` completo (incluye sección "Auto-fix iterations" si entró Phase 3)
- `REVIEW.md` final (output último auditor run)
- Commits conventional incluyendo fixes: `feat(scope): ...`, `fix(scope): address auditor findings iter-N`, `test(scope): ...`

**Reportar a Chris brief < 300 palabras:** qué se implementó + tests verdes + iteraciones audit + verdict final + bloqueadores escalados a PM (si los hay).

**Si PR es cross-stack BE+FE en paralelo:** dos builders independientes, cada uno spawnea SU auditor (BE → BE-auditor, FE → FE-auditor). Ambos auditores deben PASS. Cross-builder coordination = commits por nombre archivo + IMPL-LOG sección por builder.
```

## Variantes

- BE only: `nicolify-backend` + auto-spawn `nicolify-backend-auditor`
- FE only: `nicolify-frontend` + UI-SPEC obligatorio + auto-spawn `nicolify-frontend-auditor`
- AI/LangGraph: `nicolify-agentic` + auto-spawn `nicolify-backend-auditor`
- Cross-stack: BE + FE en paralelo (regla parallel-safety M1) — cada uno auto-spawn su auditor

## Auto-loop fail-safe

- Max 3 iter fix → escalate PM. Evita bucles infinitos sobre findings irresolvibles arquitectónicamente.
- Findings drift CONTRACT → STOP iter 1 → escalate PM (decisión contractual, no fix-by-builder).
- Findings cross-PR → ignorar + nota IMPL-LOG (regla M7).
- Push falla non-fast-forward → STOP cualquier fase → escalate Chris.
