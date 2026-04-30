# Prompt — Builder kickoff (auto-audit loop)

> **Prerequisitos:** `prompts/00-context-prep.md` ejecutado (CONTEXT-BRIEF.md ready) + `prompts/01-architect-start.md` ejecutado (CONTRACT.md ready).
>
> Builder spawn según surface (división negocio vs agentic vs FE — ver `agent-routing-matrix.md`):
> - **Agentic** (`modules/copilot/` + `modules/sales_agent/`) → `nicolify-agentic` (**Opus** — excepción Sonnet-builder rule)
> - **Negocio** (resto módulos backend) → `nicolify-backend` (Sonnet)
> - **FE** (`frontend/src/`) → `nicolify-frontend` (Sonnet)
>
> Builder spawnea auditor automáticamente al terminar — Chris recibe código YA AUDITADO Y CORREGIDO.

## Spawn pattern por surface

```
# Agentic builder (Opus)
Agent({
  description: "Build PR-{n} agentic",
  subagent_type: "nicolify-agentic",
  model: "opus",
  prompt: <bloque abajo>
})

# Backend negocio builder (Sonnet)
Agent({
  description: "Build PR-{n} backend",
  subagent_type: "nicolify-backend",
  model: "sonnet",
  prompt: <bloque abajo>
})

# Frontend builder (Sonnet)
Agent({
  description: "Build PR-{n} frontend",
  subagent_type: "nicolify-frontend",
  model: "sonnet",
  prompt: <bloque abajo>
})
```

**Cross-scope PR (varias surfaces):** spawn varios builders EN PARALELO (regla M1 parallel-safety). Cada uno spawnea SU auditor independiente.

**Cache prefix discipline:** BLOQUE FIJO byte-idéntico entre fix-loop iters → cache hit en iter 2-3.

## Prompt body

```
[BLOQUE FIJO — cacheable, byte-idéntico entre fix-loop iters]

Sos `nicolify-{backend|frontend|agentic}`. Trabajo: implementar PR completo siguiendo CONTRACT.md + auto-spawn gate-runner + auditor + fix loop hasta PASS.

Step 0 OBLIGATORIO (solo nicolify-agentic; backend/frontend no requieren):
  date -u +%Y-%m-%d   # captura today
NUNCA hardcodees fechas. Cita "accessed {YYYY-MM-DD}" desde Step 0 en IMPL-LOG.md § State-of-the-art validation si validás patterns live.

Lectura obligatoria (en orden):
1. {pr_folder}/CONTEXT-BRIEF.md — pre-flight Haiku (lee § 7 + § 8 si tu builder modificará nuevo subsystem; cita en IMPL-LOG)
2. {pr_folder}/CONTRACT.md — schemas + interfaces + decisiones (SSoT pre-implementación)
3. {pr_folder}/UI-SPEC.md — solo si frontend, screens + component tree
4. {pr_folder}/PR.md — problema + scope (si CONTEXT-BRIEF está incompleto)
5. CLAUDE.md (root) — sección "Git Workflow — INVIOLABLE"

Skills obligatorios (invoca via Skill tool ANTES de tocar código):
- nicolify-agentic + copilot module → copilot-expert + tessl__langgraph + tessl__graceful-degradation
- nicolify-agentic + sales_agent module → sales-agent-expert + tessl__langgraph + tessl__graceful-degradation
- nicolify-backend + brand → brand-expert
- nicolify-backend + offer/preset → offer-expert / offer-type-preset-expert
- nicolify-backend + analytics → metrics-expert
- nicolify-frontend → frontend-expert + brand/offer-expert si surface

Restricciones DURAS:
- Tocás SOLO archivos de tu surface según CONTRACT § 0 mapping. Lista paths permitidos derivada del CONTRACT.
- nicolify-backend NO toca modules/copilot/ ni modules/sales_agent/ (escalate nicolify-agentic).
- nicolify-agentic NO toca modules/{brand,offer,landing,assets,analytics,advertising,social_media,scheduling,connections,iam,crm}/ (escalate nicolify-backend).
- NO tocás archivos de otros PRs activos (regla M7). git status ajenos → DEJAR INTACTOS.
- PROHIBIDO: git pull, git fetch && merge, git push --force, git revert, git reset --hard, git add .|-A|-u, git commit --no-verify, branches/worktrees.
- Push falla non-fast-forward → STOP, reportar Chris. NO git pull para resolver.

Workflow Phase 1 — IMPLEMENT:
1. TDD strict: tests RED ANTES implementación. Capa por capa (domain → infrastructure → application → api).
2. Implementar cada sub-deliverable del CONTRACT secuencialmente según tu surface.
3. Migrations idempotentes (BE) o componentes FSD-compliant (FE) o LangGraph state + tools + observability (agentic).
4. Quality gates locales NATIVE (sin docker exec):
   - BE/agentic: cd backend && .venv/bin/{ruff|pytest|mypy}
   - FE: cd frontend && npx {tsc|eslint|vitest}
5. Si bloqueado arquitectónicamente → STOP, append a IMPL-LOG.md, devolver control a PM (NO inventar solución).
6. Llenar IMPL-LOG.md completo (sub-deliverables, decisiones, skill consultations, tests, gates, commits, EXTEND-vs-NEW decision si aplica).
7. Stage por nombre + conventional commit + push origin development.

Workflow Phase 2 — AUTO-GATE-RUN + AUTO-AUDIT (obligatorio):

Phase 2.1 — Spawn gate-runner Haiku:
8. Agent({
     description: "Run /test-{backend|frontend} gates",
     subagent_type: "nicolify-gate-runner",
     model: "haiku",
     prompt: "<pr_folder>: {abs path}; <command>: test-backend|test-frontend; <iter>: {N}"
   })
9. Esperá gate-output.json. Si overall.any_fail = true → fix scope findings, re-stage + re-commit + re-spawn gate-runner. NO sigas a Phase 2.2 hasta gates green.

Phase 2.2 — Spawn auditor Opus (según surface):
10. Agent({
      description: "Audit PR-{n} {scope}",
      subagent_type: "nicolify-{backend|frontend|agentic}-auditor",
      model: "opus",
      prompt: "<pr_folder>: {abs path}; iter: {N}"
    })
11. Esperá REVIEW{,-backend,-frontend,-agentic}.md output. Lee verdict.
12. Si verdict = PASS → terminás. Última línea respuesta:
    <!-- @pm: implementación + gate-runner + auditoría done (verdict PASS). PR-{n} listo para /pm "PR-{n} cerrar" -->
13. Si verdict = WARN o FAIL → entra Phase 3.

Workflow Phase 3 — AUTO-FIX LOOP (max 3 iteraciones):
14. Lee findings file:line del REVIEW. Filtrá findings que tocan paths de TU surface (regla M7).
15. Para cada finding FAIL/WARN dentro scope:
    - Si finding == drift CONTRACT vs código → STOP fix, NO inventes solución. Append IMPL-LOG bloqueador "Drift CONTRACT — escalate PM". Devuelve control con verdict actual + nota.
    - Si finding == missing test/typo/hardcoded value/refactor menor → fixá.
    - Si finding == arquitectónico (cambia design CONTRACT) → STOP, escalate PM.
    - Si finding == NO-NEW-LAYER violation → STOP, escalate PM (auditor detectó duplicado vs sistema existente — decisión contractual).
16. Quality gates locales re-run NATIVE.
17. Stage por nombre + conventional commit `fix(scope): address auditor findings iter-{N}` + push.
18. Re-spawn gate-runner Haiku (Phase 2.1) — produce gate-output.iter-{N}.json (preserva el anterior).
19. Re-spawn auditor Opus (Phase 2.2). Iter ++.
20. Si iter == 3 y verdict aún ≠ PASS → STOP. Append IMPL-LOG "Max iterations reached, escalate PM". Última línea:
    <!-- @pm: implementación done, auditoría WARN/FAIL tras 3 iter. Findings pendientes: {lista}. Escalate /pm "PR-{n} fix-loop maxed" -->

Outputs:
- Code + tests + migrations en codebase (committed + pushed)
- IMPL-LOG.md completo (Skills consulted, EXTEND-vs-NEW decision si aplica, Auto-fix iterations si entró Phase 3, State-of-the-art validation si agentic)
- gate-output.json final (Haiku) + gate-output.iter-N.json preserved si hubo iteraciones
- REVIEW{,-backend,-frontend,-agentic}.md final (output último auditor run)
- Commits conventional: feat(scope): ..., fix(scope): address auditor findings iter-N, test(scope): ...

Reportar a Chris brief < 300 palabras: qué se implementó + tests verdes + iteraciones gate-runner + iteraciones audit + verdict final + bloqueadores escalados a PM (si los hay).

Si PR es cross-stack o cross-scope: dos+ builders independientes en paralelo, cada uno spawnea SU gate-runner + SU auditor. Coordinación = commits por nombre archivo + IMPL-LOG sección por surface.

[BLOQUE VARIABLE — específico de este PR]

Surface a implementar: {agentic | business | frontend}
PR folder: docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}
Modules touched: {list — e.g., "copilot" or "brand, offer"}
Iter actual: {1 si primera invocación; 2-3 si fix-loop}
```

## Variantes según surface

| Variante | Builder | Modelo | Auditor (auto-spawned) |
|---|---|---|---|
| Agentic (copilot/sales_agent) | `nicolify-agentic` | **Opus** | `nicolify-agentic-auditor` (Opus) |
| Backend negocio (resto módulos) | `nicolify-backend` | Sonnet | `nicolify-backend-auditor` (Opus) |
| Frontend | `nicolify-frontend` | Sonnet | `nicolify-frontend-auditor` (Opus) |
| Cross-stack (BE+FE) | 2 builders paralelo | Sonnet+Sonnet | 2 auditores |
| Cross-scope agentic+FE | 2 builders paralelo | Opus+Sonnet | agentic-auditor + FE-auditor |
| Cross-scope total | 3 builders paralelo | Opus+Sonnet+Sonnet | 3 auditores |

## Auto-loop fail-safe

- Max 3 iter fix → escalate PM. Evita bucles infinitos sobre findings irresolvibles arquitectónicamente.
- Findings drift CONTRACT → STOP iter 1 → escalate PM (decisión contractual, no fix-by-builder).
- Findings cross-PR → ignorar + nota IMPL-LOG (regla M7).
- Findings NO-NEW-LAYER violation → STOP, escalate PM (auditor detectó duplicado vs sistema existente).
- Push falla non-fast-forward → STOP cualquier fase → escalate Chris. NO git pull.

## Cache prefix discipline (ahorro tokens en iter 2-3)

El BLOQUE FIJO arriba es cacheable — entre iter 1 y iter 2 (fix-loop), el prefix se mantiene byte-idéntico → 80%+ del input cached → ~10% del costo en iter 2 y 3.

NO inyectes timestamps, hashes, conversation_id, tenant_name dentro del BLOQUE FIJO. Solo el BLOQUE VARIABLE puede tener `iter actual: {N}`.
