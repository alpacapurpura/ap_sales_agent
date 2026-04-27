# Handoff prompt · S{N} start

> Pega esto al iniciar conversación nueva.

---

```
Continuamos el redesign arquitectónico de sales_agent → madurez copilot + capacidades nuevas (brand voice + scheduler + payment + eval).

📋 Plan maestro: docs/domains/sales-agent/redesign-2026-04/README.md
🎯 Fase actual: S{N} — {Título}
📂 Doc de la fase: docs/domains/sales-agent/redesign-2026-04/phases/S{N}-{slug}.md
📝 Aprendizajes previos: docs/domains/sales-agent/redesign-2026-04/learnings/S{N-1}-*.md

PROTOCOLO (obligatorio):

1. Lee README.md + 00-vision-and-objectives.md (presta atención a §3 lo que NO se toca) + 01-master-plan.md + 02-architecture-target.md + 03-phase-protocol.md + 04-principles.md.
2. Lee phases/S{N}-{slug}.md — sección Research mandate.
3. Lee learnings/S{N-1}-*.md (si existe).
4. Lee 05-tech-debt-log.md — ¿alguna deuda relevante?
5. Ejecuta research fresco (WebSearch + Tessl tiles + WebFetch). Mínimo 3 queries del mandate.
6. Confirma o ajusta enfoque. Si research sugiere cambio → documenta en phases/S{N}-*.md sección "Ajustes vs plan original" antes de codear.
7. TaskCreate granular (≤4h por task).
8. TDD: RED test antes de cualquier código. RED → GREEN → REFACTOR.
9. Quality gates nativos (NUNCA docker exec): ruff + pytest + arch tests.
10. Verificación funcional. §3 sigue funcionando (closer studio + buffer + webhooks + follow-up + frozen detection).
11. Si detectas tech debt: validá real → mide impacto → fix root cause SI cabe en scope, DEFERRED si no. Loggea en 05-tech-debt-log.md.
12. learnings/S{N}-*.md (denso, accionable, sin filler).
13. prompts/S{N+1}-start.md (refina con contexto fresco).
14. Commit conventional + push (solo archivos sesión, NUNCA git add -A).

PRINCIPIOS NO NEGOCIABLES (04-principles.md):
- GoF + DRY + alta cohesión + bajo acoplamiento.
- Anti-parche. Bug ajeno → validá → fix root cause SI cabe en scope.
- TDD obligatorio. Test reproductor antes del fix.
- Tenant isolation siempre. PII sanitization en TODOS los writes a tracing.
- Best-effort observability (try/except + structlog warning + db.rollback).
- Spanish neutro LATAM (sin voseo).
- Native-first dev (NUNCA docker exec lint/tests).
- response_model= en todos los endpoints.
- Stage por nombre en commits (NUNCA git add -A).

CONTEXTO ESPERADO:
- Branch: development limpio
- Último commit: {COMPLETAR CON HASH AL FINAL DE S{N-1}}
- Hooks de fases previas: {COMPLETAR}
- Tech debt en radar: {COMPLETAR}

Empieza ahora con paso 1.
```
