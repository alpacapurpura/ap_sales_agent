# Process Learnings (append-only)

> Owner: `/pm`. NUNCA editar entries históricas. Solo append.
> Cada incident / decisión cardinal / surprise / case study agrega entry.

---

## 2026-05-04 — Migración a SDD Level 3 / Spec-Driven Harness

**Contexto:** Estructura `docs/pm-nico/` se quedó corta. 6 PIs activos. Múltiples sesiones Claude. Necesidad de specs ejecutables + evals AI-resistant + resume protocol robusto.

**Decisiones:**
1. Estructura `docs/{product,projects,specs,process}/` paralela a `pm-nico/`. Migración gradual.
2. Story = unidad atómica. 1 archivo YAML. NO capability monolítico.
3. 3 tipos story: ui / agentic / service. Eval policy distinta.
4. Scenarios AI-resistant obligatorios: happy + negative + edge + adversarial.
5. Personas + Rubrics first-class versionados.
6. 9 skills nuevos: /pm rewrite, /po, /ux-ui, /ux-agentico, /architect (+ 3 sub), /dev-team, /auditor.
7. 11 nicolify-* agents renombrados al nuevo paradigma.
8. Tickets agentic = Opus 4.7 obligatorio (qwen ban).
9. Tickets BE/FE no-agentic = qwen-opencode preferido.
10. Self-fix auditor cap 2 iter, después escala.
11. /pm habla solo nuevo. Legacy `pm-nico/` lee on-demand manual.

**Fuentes consultadas:**
- Anthropic effective-harnesses-for-long-running-agents
- Anthropic harness-design-long-running-apps
- Anthropic multi-agent-research-system
- Anthropic managed-agents
- Anthropic AI-resistant-technical-evaluations
- Anthropic demystifying-evals-for-ai-agents
- Vercel "We removed 80% of our agents tools"
- τ-Bench / τ2-Bench (multi-turn evals)
- ejemplo-harness-subagentes (betta-tech)

**Riesgos identificados:**
- Migration parcial: durante 4-6 semanas, /pm habla solo nuevo pero PIs viejos siguen en pm-nico/. Chris debe pedir manual cuando query algo legacy.
- Aprendizaje curva: 9 skills nuevos. Primer story exemplar piloto crítico.
- Cost: multi-agent multiplica tokens (Anthropic 15x). Mitigación: solo orchestrator + sub-architects en Opus, devs en qwen/sonnet cuando posible.

---
