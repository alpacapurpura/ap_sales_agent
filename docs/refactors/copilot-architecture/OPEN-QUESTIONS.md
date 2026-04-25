# Preguntas pendientes — decisión humana antes de codear

Gate: sin respuesta, F0 no arranca en código. Responder via editar este archivo + commit, o Slack/conversación.

---

## Q1 — Política cuando user "escapa" del focus mode

Contexto: interview focus activa, `pending_slots > 0`. User cierra sidebar, navega a otra ruta, o refresca.

Opciones:

**A. Lock duro** — nav bloqueado con modal "tienes X slots pendientes. ¿Guardar y salir o continuar?". Cierre sidebar deshabilitado en focus.

**B. Lock suave** — nav permitido. Focus queda persisted. Al volver → retomar en mismo bloque con banner "tienes interview a medias".

**C. Híbrido** — lock duro solo para navegación dentro de la misma entity (no salgas a mitad). Cambio de entity/ruta completamente distinta = soft (persist + banner).

Pregunta: A, B, o C? Mi recomendación: **C**. Lock duro dentro de `routeFor(domain)`, soft al salir completamente del studio.

---

## Q2 — Persist-mode default para buyer_persona worker (F2)

Contexto: hoy `extract_from_doc` para buyer_persona es inline sin auto-commit (modo preview). Vamos a migrar a worker.

Opciones:

**A. Preview (default)** — worker genera delta, user aprueba. Idéntico UX al actual.

**B. Auto (default)** — worker commit directo, user ve summary card. UX tipo URL.

**C. Per-asset decisión LLM** — clarify card pregunta "¿querés que auto-guarde o previsualizar primero?".

Pregunta: A, B, o C? Mi recomendación: **A**, mantener UX actual (safety first para PII en buyer_persona).

---

## Q3 — Checkpointer scope: solo focus o todo copilot? (F3)

Contexto: `AsyncPostgresSaver` añade overhead DB write per-turn (~10-50ms). Podemos aplicarlo solo en focus mode o en todas las conversaciones.

Opciones:

**A. Global** — todas las convs checkpointed. Survive reload, multi-device. ~10-50ms/turn overhead.

**B. Solo focus** — checkpointer se activa cuando `focus.active=true`. Conversación libre sigue stateless-per-turn como hoy.

**C. Feature flag tenant** — toggle on/off por tenant (rollout gradual).

Pregunta: A, B, o C? Mi recomendación: **C**, rollout gradual. Arrancar con focus-only (B behavior) para tenants con flag off; focus+free (A) para flag on. Observar métricas.

---

## Q4 — Sanitizer retirement criteria definitivo (F6)

Contexto: `output_sanitizer.py` es parche; queremos retirarlo. Pero el criterio debe ser medible.

Propuesta:
- (a) 100% Wave A+B tools migradas a `ToolMessage.artifact` con `ToolResponse`.
- (b) ≥80% Wave C+D migradas.
- (c) Métrica "% AIMessages donde sanitizer modificó content" < 0.1% durante 2 sprints consecutivos.
- (d) Arch test `test_no_tool_returns_json_string` verde.

Pregunta: aceptás criterio propuesto? ¿Algún umbral más estricto/laxo? ¿Alternativa (e.g. mantener sanitizer como defensa-en-profundidad permanente)?

Mi recomendación: aceptar (a)(b)(c)(d). Retirement sólido, no teatro.

---

## Q5 — Paralelismo con refactor `field-contract-ssot` en curso

Contexto: otro agente paralelo trabaja en `field-contract-ssot` (rename/refactor de field paths BE↔FE). Toca schemas offer.

Opciones:

**A. Serializar** — esperar a que field-contract-ssot cierre todas sus fases antes de arrancar F0.

**B. Paralelo con sync** — F0 (docs/ADRs) arranca ya. F1 arranca cuando field-contract-ssot termine fase 01 (schemas estables).

**C. Full paralelo** — ambos refactors avanzan; mergeamos por turnos, coord rebases.

Pregunta: A, B, o C? Mi recomendación: **B**. F0 no toca código runtime, seguro. F1 necesita estabilidad de `editable_fields` que viene de field-contract-ssot.

---

## Nice-to-have (respondiendo = F7 prioridad up)

## Q6 — Anthropic memory tool opt-in por tenant?

Contexto: Anthropic memory tool reporta -84% tokens en evals públicas. Usar requiere ser Claude-first agent (no rotar models).

Pregunta: ¿estamos OK con Claude-lock para copilot core, o queremos mantener opción multi-provider (OpenAI, Gemini)? Impacta F7 design.

Mi recomendación: **Claude-first**, alineado con Anthropic SDK ya en uso (ver `anthropic` imports). Cost+quality mejor 2026.
