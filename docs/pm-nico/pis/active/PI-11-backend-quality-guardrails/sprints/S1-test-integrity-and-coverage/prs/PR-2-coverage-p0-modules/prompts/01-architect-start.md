# Prompt — Architect kickoff (PR-2)

> **Nota:** PR-2 es puro aumento de cobertura en módulos existentes. No hay diseño arquitectónico nuevo.
> Architect puede **skip** o producir CONTRACT.md mínimo.

## Spawn pattern (opcional)

```
Agent({
  description: "Architect PR-2 (lightweight)",
  subagent_type: "nicolify-architect",
  model: "opus",
  prompt: <bloque abajo>
})
```

## Prompt body

```
Sos nicolify-architect (Opus). PR-2 es puro aumento de cobertura de tests en crm y scheduling.

Step 0 OBLIGATORIO:
  date -u +%Y-%m-%d

Reglas:
- NO escribas código de implementación.
- Verifica que NO haya drift de schemas/interfaces existentes.
- Si detectás que un nuevo test requeriría cambiar un schema/API → flag en OPEN QUESTIONS.

Lectura obligatoria:
1. docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules/PR.md
2. src/modules/crm/application/services/ (listar servicios sin cobertura)
3. src/modules/scheduling/application/services/ (listar servicios sin cobertura)

Output: CONTRACT.md mínimo con:
- § 0 Context Summary: architect run date, surface (business), builder mapping.
- § 1 Scope validation: lista de servicios/repos a cubrir con tests.
- § 2 Open questions: solo si hay drift schema/API.

Última línea:
<!-- @pm: CONTRACT lightweight ready. Próximo paso: ejecutar prompts/02-builder-start.md -->
```
