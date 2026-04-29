# Prompt — Builder kickoff

> Copy-paste este prompt en una nueva sesión Claude Code (o spawn builder vía Agent tool). PM pre-coció contexto.

```
Sos `nicolify-{backend|frontend|agentic}`. Trabajo: implementar PR completo siguiendo CONTRACT + UI-SPEC.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}/PR.md` — problema + scope
2. `docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}/CONTRACT.md` — schemas + interfaces (SSoT pre-implementación)
3. `docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}/UI-SPEC.md` — solo si frontend, screens + component tree
4. `docs/pm-nico/current-state/{módulo}.md` — capacidades vivas (no duplicar)
5. `.claude/rules/{backend-ddd|frontend-fsd}.md` + `tenant-isolation.md` + `tdd-mandatory.md`
6. `CLAUDE.md` (root)

**Skills a invocar (si aplica módulo):**
- `{brand-expert | offer-expert | copilot-expert | sales-agent-expert | metrics-expert | manychat-expert}`

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
- `docs/pm-nico/pis/active/PI-{X}-{theme}/sprints/S{N}-*/prs/PR-{n}-{slug}/IMPL-LOG.md` siguiendo template
- Commits conventional siguiendo `.claude/rules/git-safety.md`
  - PROHIBIDO `git add .|-A|-u`. Stage por nombre.
  - Conventional: `feat(scope): ...`, `test(scope): ...`, etc.

**Al terminar:**
1. IMPL-LOG.md completo con sub-deliverables, decisiones, commits.
2. `current-state/{módulo}.md` actualizado con capability lineage (PM puede revisar y consolidar después).
3. Última línea de tu respuesta:
   `<!-- @pm: implementación done. Próximo paso: ejecutar prompts/03-auditor-start.md o ejecutar /pm "PR-{n} builder done" para review. -->`
4. Reportar a Chris brief < 250 palabras: qué se implementó + tests verdes + bloqueadores resueltos / abiertos.

**Si PR es cross-stack BE+FE en paralelo:** dos sesiones distintas, cada una builder, ambas consumen mismo CONTRACT. Ambas appendean a mismo IMPL-LOG (sección por builder). Coordinar commits por nombre archivo.
```

## Variantes

- BE only: `nicolify-backend` + auditor `nicolify-backend-auditor`
- FE only: `nicolify-frontend` + UI-SPEC obligatorio
- AI/LangGraph: `nicolify-agentic` + auditor `nicolify-backend-auditor`
- Cross-stack: BE + FE en paralelo (ver regla parallel-sessions-protocol)
