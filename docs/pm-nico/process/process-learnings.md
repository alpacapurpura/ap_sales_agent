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

## 2026-04-29 (noche) — Sesión refactor: paradigma producto-vs-proyecto + PR-folder + paralelismo + Opus 1M

**Contexto:** segunda sesión `/pm` post-bootstrap. Chris cuestionó cómo asegurar consistencia entre sesiones (PM olvida convo entre runs), cómo evitar flakiness, cómo orquestar sin que PM sea god-mode pero siendo dueño del proceso, cómo sesiones paralelas, cómo aprovechar Opus 4.7[1M] context.

**Aprendizajes consolidados:**

### L9 — PR es CARPETA auto-contenida, no archivo único.
- Antes: `prs/PR-N-{slug}.md` (un archivo PM).
- Después: `prs/PR-N-{slug}/{PR,CONTRACT,UI-SPEC,IMPL-LOG,REVIEW,RESULT}.md + prompts/{01-04}-*.md`.
- Beneficio: cada agente (PM/architect/UX/builder/auditor) escribe en archivo asignado. PM al retomar lee carpeta y reconstruye estado sin ambigüedad.
- **Regla derivada:** template canónico en `process/pr-folder-template/`. Copia entera para cada PR nuevo.
- Pattern inspirado en `docs/domains/copilot/{feature}/` que Chris ya usaba intuitivamente.

### L10 — Paradigma Producto vs Proyecto (Capability Registry).
- `current-state/{m}.md` = producto vivo SSoT. Cada capacidad linkea al PR que la introdujo/modificó.
- `pis/active/{PI}/` = proyectos en curso. Al cerrar → mueven a `pis/archive/{PI}/`.
- `ideas/` = raw input, `opportunities/` = discovery validado.
- **Regla derivada:** sin lineage en current-state = orfandad funcional. PR shipped sin update current-state = no se considera shipped.
- Es estándar industria: SAFe "Feature Delivery Traceability", Lenny "Product Operating System".

### L11 — Opus 4.7[1M] cambia matemática sprint sizing.
- Antes: sprint = 5+ PRs chicos por miedo al contexto.
- Ahora: sprint = 1-3 PRs amplios cohesivos. Cada PR ≈ 3 ejecuciones (architect + builder + auditor).
- **Regla derivada:** NO splittear PR por contexto. Splittear solo cuando scope deja de ser cohesivo (multi-dominio, multi-blast-radius).
- Ejemplo S0 reescrito: PR-1 foundation-primitives (outbox + idempotency + observability) + PR-2 billing-and-compliance.

### L12 — Sesiones paralelas: mismo workdir, mismo branch, partición por módulo.
- Worktrees PROHIBIDOS — Chris perdió 1 semana previa por divergencia.
- Reglas M1-M6 en `process/parallel-sessions-protocol.md`:
  - M1 PRs de módulos distintos
  - M2 archivos centrales (roadmap, MEMORY, process-learnings) solo PM
  - M3 tests/Docker secuencial
  - M4 claim by commit inmediato
  - M5 git pull al inicio + antes de cada commit
  - M6 PM bootstrap pregunta PI
- **Regla derivada:** no hay locks ni worktrees. La disciplina es git pull + claim by commit + módulos distintos.

### L13 — PM como orchestrator + handoff prompts pre-cocidos.
- Auto-invocación entre agentes NO realista hoy (Anthropic Agent Teams experimental).
- Patrón realista: PM produce `prompts/{NN}-{phase}-start.md` con todo el contexto pre-cocido. Chris copia/pega en sesión nueva o spawn agent. Agente termina con `<!-- @pm: ... -->` comment indicando próximo paso.
- **Regla derivada:** PR-folder SIEMPRE incluye `prompts/01-architect-start.md` + `02-builder-start.md` + `03-auditor-start.md` + `04-pm-close.md` listos para usar. PM al cerrar turno (Track B) muestra ruta exacta del prompt siguiente.

### L14 — Dual-Track explícito en SKILL.
- PM vive en dos tracks paralelos: A (refinement = discovery + definición + entrega de PR-folder ready) y B (orchestration = handoffs + RESULT.md + current-state update).
- Chris puede pedir refinar PR-3 (Track A) mientras PR-1 está en review (Track B). PM maneja ambos sin perder contexto.
- **Regla derivada:** workflow conversacional documenta ambos tracks. Salida turn-a-turn distingue: Track A → pregunta a Chris; Track B → ruta exacta de prompt.

### L15 — Bootstrap PM extendido: pregunta PI explícito.
- Antes: bootstrap leía INDEX + roadmap + saludaba general.
- Ahora: bootstrap pregunta "¿en qué PI vas a trabajar?" antes de cargar contexto del PI elegido.
- **Regla derivada:** sin saber PI elegido, PM no puede priorizar contexto correcto. Pregunta SIEMPRE.

### L16 — Technical Sanity Check liviano en discovery.
- PM puede spawn `Explore` o `nicolify-architect` (read-only) durante discovery para validar viabilidad técnica ANTES de escribir solución elegida.
- **Regla derivada:** scope ≥ M o cross-module → Sanity Check obligatorio. Brief vuelve, PM transcribe a sección "Validación técnica preliminar" en PR.md. NO contamina rol — architect no escribe código, solo asesora.

## Próximas sesiones — qué observar

- ¿PR-folder structure se siente natural en práctica? Si fricción al copy template → revisar.
- ¿`prompts/{NN}-*.md` realmente se usan o son letra muerta? Medir cuántos PRs usan vs improvisan handoff.
- ¿`@pm` comment al final de agentes se respeta? Si builders/auditors no lo ponen → escalate.
- ¿Bootstrap pregunta PI funciona o Chris la encuentra molesta? Si molesta → ajustar.
- ¿Sesiones paralelas con M1-M6 evitan colisiones? Tracking: cuántas veces hay merge conflicts en docs/pm-nico/.
- ¿Agent routing matrix cubre casos reales o queda demasiado abstracto?
- ¿Process-learnings escala con append? Si crece >50 entries → consolidar las viejas en SKILL.md y resetear este archivo a las últimas 10.
