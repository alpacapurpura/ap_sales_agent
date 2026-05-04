# Prompt — Architect kickoff (PR-1)

> **Nota:** Este PR es puro fix de tests + snapshots. No hay diseño arquitectónico nuevo.
> Architect puede **skip** o producir CONTRACT.md mínimo que valide que no hay drift de schemas/interfaces.
>
> Spawn `nicolify-architect` (Opus) solo si Chris lo solicita; de lo contrario, el builder puede partir directo de PR.md + CONTEXT-BRIEF.

## Spawn pattern (opcional)

```
Agent({
  description: "Architect PR-1 (lightweight)",
  subagent_type: "nicolify-architect",
  model: "opus",
  prompt: <bloque abajo>
})
```

## Prompt body

```
Sos nicolify-architect (Opus). PR-1 es puro fix mecánico de tests rotos + arch snapshots.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Reglas:
- NO escribas código de implementación.
- Solo verifica que NO haya drift de schemas/interfaces existentes.
- Si detectás que un fix de test requeriría cambiar un schema/API → flag en OPEN QUESTIONS.

Lectura obligatoria:
1. docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-1-fix-broken-tests-and-arch-snapshots/PR.md
2. tests/architecture/test_ddd_boundaries.py (KNOWN_CROSS_MODULE_IMPORTS)
3. tests/architecture/test_sales_agent_system_prompt_order.py (EXPECTED_CACHEABLE)

Output: CONTRACT.md mínimo con:
- § 0 Context Summary: architect run date, surfaces (business + agentic), mapping builders.
- § 1 Scope validation: lista de tests a fixear con archivo:linea.
- § 2 Open questions: solo si hay drift schema/API.
- § 16 Decision log: vacío si no hay decisiones.

Última línea:
<!-- @pm: CONTRACT lightweight ready. Próximo paso: ejecutar prompts/02-builder-start.md (business) + prompts/02-builder-start-agentic.md (agentic) en paralelo. -->
```
