# Prompt — Architect kickoff PR-6

> Spawn `nicolify-architect` vía Agent tool.

```
Sos `nicolify-architect`. Trabajo: producir CONTRACT.md para PR-6-consumers-cutover.

**Framing CRÍTICO:** "1000 clientes, robusto + escalable, cero deuda técnica." ZERO open questions ideal.

**Lectura obligatoria (en orden):**
1. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S2-orchestrator/prs/PR-6-consumers-cutover/PR.md` — scope + decisiones D26-D28
2. `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S2-orchestrator/prs/PR-5-orchestrator-and-workers/{PR.md,CONTRACT.md,RESULT.md}` — D21 cutover order rationale + S0 primitives consumed
3. `docs/pm-nico/pis/active/PI-1-campaigns-module/PI.md` — visión PI
4. `docs/pm-nico/current-state/{sales_agent,copilot,brand}.md` — capabilities pre-cutover
5. **Schema vivo (leer ANTES escribir CONTRACT):**
   - `backend/src/core/config.py:209-212` — flags state actual
   - `backend/src/shared/domain_events/outbox/application/event_bus_adapter.py` — adapter logic
   - `backend/src/shared/billing/` — BudgetGuard signature + Reservation type
   - `backend/src/shared/billing/infrastructure/repositories/` — model_pricing_snapshot access
   - `backend/src/modules/sales_agent/application/` — LLM call sites + emisores legacy
   - `backend/src/modules/copilot/application/` — LLM call sites + emisores legacy
   - `backend/src/modules/brand/application/` — emisores legacy (no LLM directo)
6. Reglas: backend-ddd + tenant-isolation + architectural-fitness + sales-agent-brand-voice (invariante reservación 50%) + parallel-safety (M8 extend, no destroy)

**Skills a invocar (ANTES diseñar):**
- `sales-agent-expert` (BudgetGuard wiring sales_agent — reservación 50% invariante; voz tenant no romper)
- `copilot-expert` (BudgetGuard wiring copilot LLM call sites; cost cycle observability)
- `tessl__graceful-degradation` (BudgetGuard fallback si dependency down)

**Tu output: CONTRACT.md completo en**
`docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S2-orchestrator/prs/PR-6-consumers-cutover/CONTRACT.md`

**Secciones obligatorias CONTRACT.md:**

1. **Module surface (cutover scope)** — paths exactos modified, sub-deliverables Order (sales_agent → copilot → brand).
2. **LLM call sites enumerados** — list exhaustivo con file:line de cada `LiteLLM.acompletion` / `provider.invoke` / `client.chat.completions` en sales_agent + copilot. Wrapping pattern propuesto.
3. **Emisores legacy enumerados** — list exhaustivo con file:line de cada `event_bus.publish_in_memory` en sales_agent + copilot + brand. Indicar si callsite sync vs async + bridge strategy.
4. **BudgetGuard wiring spec** — signature, estimation strategy, error handling 402, audit row schema.
5. **Cost estimation algorithm** — fórmula `cost = pricing[model] * (input_tokens + max_output_tokens)`. Source pricing snapshot.
6. **Cutover order matrix** — sales_agent (commit 1) → smoke verify → copilot (commit 2) → smoke → brand (commit 3) → smoke → BudgetGuard wiring (commit 4) → retire legacy (commit 5).
7. **Decisiones D26-D28 confirmadas** — con cualquier ajuste tras audit schema vivo.
8. **Test strategy detallado** — fixtures integration F-7 sin mocks, BudgetGuard tests con plan exhausted simulado.
9. **Architectural fitness gates** — exact AST scan logic.
10. **Open questions for PM** — IDEAL VACÍA.

**Reglas duras:**
- NO escribas código de implementación. Solo schemas + interfaces + decisiones.
- SQLA 2.0 async + Pydantic v2 + structlog SIEMPRE.
- response_model obligatorio cualquier endpoint MOD.
- Cero deuda técnica. Cada decisión documenta razón "1000 clientes" + alternativa.
- Sesiones paralelas: PR-6 toca `core/config.py` (3 lines flag defaults) + LLM callsites copilot/sales_agent. Si PI-2 paralela toca mismo callsite → regla M8 extend, no destroy.

**Al terminar:**
1. Escribir CONTRACT.md completo (single file).
2. Última línea EXACTA:
   `<!-- @pm: CONTRACT.md ready. Próximo paso: ejecutar prompts/02-builder-start.md o ejecutar /pm "PR-6 architect done" para review. -->`
3. Reportar Chris brief < 200 palabras: decisiones tomadas + open questions (IDEAL: cero) + drift detectado en schema vivo vs PR.md.

**Working dir:** `/home/chris/AISALESHT`. NO push, NO commit (PM commitea CONTRACT después de validar).
```
