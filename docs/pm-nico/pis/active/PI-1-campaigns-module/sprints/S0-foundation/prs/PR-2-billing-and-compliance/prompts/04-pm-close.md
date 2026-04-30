# Prompt — PM close loop (PR-2 billing-and-compliance)

> Copy-paste al volver `/pm` para cerrar PR-2.

```
/pm

PR-2-billing-and-compliance terminó implementación + auditoría. Cierro loop.

Lee:
- `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/IMPL-LOG.md`
- `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-2-billing-and-compliance/REVIEW.md`
- Últimos commits: `git log --oneline -15`

Hacer:
1. Verificar verdict REVIEW = PASS. WARN/FAIL → escalar Chris.
2. Escribir `RESULT.md` (template `process/pr-folder-template/RESULT.md`):
   - Outcome real vs esperado (4 servicios + Streamlit admin + invariant test verde + 5 planes seeded)
   - Surface concreta (tablas, env vars, migration 110, paths, Streamlit page URL)
   - Capacidades nuevas con lineage PR-2
   - Decisiones implementación (basadas en CONTRACT)
   - Métricas: tests verdes, invariant property-based con N runs, migration clone DB OK, Streamlit smoke OK
   - Deuda técnica: wiring consumers (copilot/sales_agent/ChannelRouter) → S2. tenant_billing_config legacy migration data → S2 worker
3. Update `current-state/iam.md` (cap "Plan tiers + tenant_subscription" lineage PR-2)
4. Update `current-state/copilot.md` (cap "BudgetGuard API exposed (wiring S2)")
5. Update `current-state/sales_agent.md` (cap "BudgetGuard reservation 50% invariant exposed (wiring S2)")
6. Update `current-state/campaigns.md` (cap "ComplianceService + RateLimiter API exposed (wiring S2)")
7. Append `pis/active/PI-1-campaigns-module/decisions.md`:
   - D15: 5 planes editable plan_config + tenant_subscription
   - D16: Reservación 50% sales_agent invariant enforced
   - D17: ComplianceService policy chain (WABA24h + OptIn + Blacklist + CountryBlock)
   - D18: Streamlit `/planes-billing` admin para Chris
   - (otras según architect/builder)
8. Append `sprints/S0-foundation/learnings.md`:
   - Property-based testing Hypothesis para invariants
   - Compat layer pattern (legacy + new + fallback)
   - Streamlit smoke test pattern
9. Cambiar `Estado: shipped` en `PR.md`.
10. **Si último PR S0** (PR-1 + PR-2 ambos shipped):
    - Llenar `sprints/S0-foundation/handoff.md` para S1 (decisiones + surface + agentes recomendados)
    - Considerar mover S1-domain-campaigns sprint a in-progress (next bootstrap PI)

Quiero brief < 200 palabras: shipped + cambios producto + S0 cierre status.
```

## Notas

- Si PR-1 + PR-2 shipped → S0 cierre obligatorio: handoff.md + retro temprana opcional.
- Wiring consumers explicit S2.
- Invariant test (property-based) es el delivery más importante PR-2 — Chris debe ver verde en RESULT.
