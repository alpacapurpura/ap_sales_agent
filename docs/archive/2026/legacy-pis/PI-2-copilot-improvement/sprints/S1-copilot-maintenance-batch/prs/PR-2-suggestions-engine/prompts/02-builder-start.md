# Prompt — Builder kickoff

> Copy-paste este prompt en una nueva sesión Claude Code (o spawn builder vía Agent tool). PM pre-coció contexto.

```
Sos `nicolify-backend`. Trabajo: implementar PR completo BE-only siguiendo CONTRACT.md.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-2-suggestions-engine/PR.md` — problema + scope
2. `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-2-suggestions-engine/CONTRACT.md` — schemas + interfaces (SSoT pre-implementación)
3. `docs/pm-nico/current-state/copilot.md` — capacidades vivas (no duplicar)
4. `.claude/rules/backend-ddd.md` + `.claude/rules/tenant-isolation.md` + `.claude/rules/tdd-mandatory.md` + `.claude/rules/copilot-resilience.md` + `.claude/rules/copilot-observability.md`
5. `CLAUDE.md` (root)

**Skills a invocar (obligatorio):**
- `copilot-expert` — invariantes módulo copilot

**Workflow:**
1. **TDD strict**: tests RED ANTES implementación. Capa por capa (domain → infrastructure → application → api).
2. Implementar cada sub-deliverable del CONTRACT secuencialmente.
3. Migrations idempotentes (BE) o componentes FSD-compliant (FE).
4. Quality gates **NATIVE** (sin docker exec):
   - BE: `cd backend && .venv/bin/{ruff|pytest|mypy}`
   - FE: `cd frontend && npx {tsc|eslint|vitest}`
5. Si bloqueado por algo no anticipado → STOP, append a IMPL-LOG.md, devolver control a PM (NO inventar solución arquitectónica).

**Outputs:**
- Code + tests + migrations en codebase
- `docs/pm-nico/pis/active/PI-2-copilot-improvement/sprints/S1-*/prs/PR-2-suggestions-engine/IMPL-LOG.md` siguiendo template
- Commits conventional siguiendo `.claude/rules/git-safety.md`
  - PROHIBIDO `git add .|-A|-u`. Stage por nombre.
  - Conventional: `feat(scope): ...`, `test(scope): ...`, etc.

**Al terminar:**
1. IMPL-LOG.md completo con sub-deliverables, decisiones, commits.
2. `current-state/copilot.md` actualizado con capability lineage (PM puede revisar y consolidar después).
3. Última línea de tu respuesta:
   `<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-2 builder done" para review. -->`
4. Reportar a Chris brief < 250 palabras: qué se implementó + tests verdes + bloqueadores resueltos / abiertos.

**Si PR es cross-stack BE+FE en paralelo:** dos sesiones distintas, cada una builder, ambas consumen mismo CONTRACT. Ambas appendean a mismo IMPL-LOG (sección por builder). Coordinar commits por nombre archivo.
```

## Variantes

- BE only: `nicolify-backend` + auditor `nicolify-backend-auditor`
- FE only: `nicolify-frontend` + UI-SPEC obligatorio
- AI/LangGraph: `nicolify-agentic` + auditor `nicolify-backend-auditor`
- Cross-stack: BE + FE en paralelo (ver regla parallel-sessions-protocol)
