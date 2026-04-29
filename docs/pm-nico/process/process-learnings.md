# Process Learnings — PM Nicolify

> Append-only. Cada sesión PM relevante puede dejar 1+ learning. Owner: `/pm`. Cuando un learning se vuelve regla → migrar a SKILL.md.

## 2026-04-29 — Sesión génesis: PI-1 campaigns + sistema de proceso

**Contexto:** primera sesión `/pm` post-bootstrap. Chris pidió migrar research legacy + crear PI iterativo + reframear con "robustez como Sprint 0".

**Aprendizajes:**

### L1 — Reframings tardíos pueden re-escribir un PI entero. OK siempre que se haga ANTES de código.
- Chris cambió direction de "MVP fast" a "robustez foundation-first" después de discovery inicial. Reescribimos PI-1 plan completo.
- **Regla derivada:** PR-0 = saneamiento research + alignment final del scope. Sirve de checkpoint antes de escribir código.

### L2 — Investigación previa a respuesta evita propuestas en el aire.
- Chris preguntó "¿extender observability o crear nuevo módulo?" → spawn `Explore` agent reveló que `shared/agent_observability/` ya existe con base infrastructure. Recomendación: extender (1 spec + 1 model). Si no investigaba primero, hubiese propuesto crear módulo nuevo.
- **Regla derivada:** Antes de recomendar arquitectura cross-module → spawn `Explore` para validar estado actual. Toma 60 seg, salva refactor.

### L3 — "Robustez como Sprint 0" tiene 8 sub-sprints potenciales pero conviene cortar a 5.
- Original: outbox, idempotency, rate limiter, circuit breaker, compliance, observability, audit, arch tests = 8.
- Cortado por Chris a 5 (S0.4/S0.7/S0.8 → S2 o regla estándar).
- **Regla derivada:** PM siempre propone scope completo + cuts sugeridos. Chris elige profundidad vs amplitud. Default: profundidad (Chris textual: "hacerlo muy bien en vez de aumentar el alcance").

### L4 — Cuotas/budget requieren razonamiento numérico en research file.
- Chris pidió "ayudame con tu razonamiento a definir cuotas". Pure docs no alcanza; necesita cost model concreto + traducción a quotas + invariantes.
- Output: `research/2026-04-29-billing-tiers-cost-model.md` con tabla cost/operación → quotas/plan → architecture.
- **Regla derivada:** Cualquier decisión cuantitativa (precio, cuota, threshold, latencia) → research file con cálculo, no solo bullet en PI.

### L5 — Sprint folders > planos.
- Estructura propuesta: `pis/PI-X/sprints/S{N}-*/sprint.md + prs/ + learnings.md + handoff.md`.
- Permite cargar contexto de un sprint sin contaminarse con otros. Handoff explícito entre sprints.
- **Regla derivada:** Sprint = unidad de trabajo PM. Sprint.md self-contained. Learning + handoff obligatorios al cerrar.

### L6 — Agent routing debe vivir como tabla, no en cabezas.
- Decidir cuándo cargar `ux-flow-architect` vs `nicolify-frontend` vs `ux-disruptivo` se repite cada PR. Sin tabla → drift.
- Output: `process/agent-routing-matrix.md`.
- **Regla derivada:** Toda regla de selección que se repita ≥3 veces → tabla. Tabla + ejemplos + anti-patterns.

### L7 — Reservación 50% por agente kind protege ventas.
- Chris: "las ventas no deben parar". Pool unificado se vacía con copilot intensivo (extraction $0.30/op).
- Solución: `BudgetGuard` con invariante reservación per agent_kind.
- **Regla derivada producto (no proceso):** todo nuevo agent_kind con costo LLM debe declarar reservación si su outcome es revenue-critical.

### L8 — PM debe sugerir handoff explícito al builder, no asumirlo.
- Chris: "dependiendo de ti como PM indiques que agentes y skills son necesarios cargar".
- PR.md debe declarar agentes/skills tabla explícita. Builder lee y carga lo que dice.
- **Regla derivada:** PR.md sin sección "Agentes / skills recomendados" = incompleto.

## Próximas sesiones — qué observar

- ¿La estructura `sprints/S{N}-*/` se mantiene útil con 5+ sprints? Si fricción → simplificar.
- ¿Agent routing matrix cubre casos reales o queda demasiado abstracto?
- ¿Process-learnings escala con append? Si crece >50 entries → consolidar las viejas en SKILL.md y resetear este archivo a las últimas 10.
- ¿Handoff entre sprints reduce contexto perdido entre conversaciones?
