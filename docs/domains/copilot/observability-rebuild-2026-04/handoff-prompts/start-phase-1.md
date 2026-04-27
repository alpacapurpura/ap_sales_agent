# Prompt para iniciar Fase 1 en una conversación nueva

Pegá el bloque siguiente literalmente en una nueva conversación de Claude Code:

---

```
Voy a ejecutar la Fase 1 del rediseño de observabilidad del copilot (proyecto Nicolify / AISALESHT).

Lee primero estos documentos en este orden y respetando todo lo que dicen:

1. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/README.md
2. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/ARCHITECTURE.md
3. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/PRINCIPLES.md
4. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-1-foundation/plan.md
5. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-1-foundation/research-checklist.md
6. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-1-foundation/completion-checklist.md

Reglas globales del repo aplican (ver CLAUDE.md): branch único `development`, native WSL, TDD obligatorio, migraciones idempotentes, Spanish neutro LatAm en user-facing, conventional commits, stage por nombre nunca `git add .`, sesiones paralelas activas (no tocar WIP ajeno).

Antes de tocar código:
- Ejecutá la investigación pedida en research-checklist.md (WebSearch + WebFetch).
- Validá fecha actual con `date`.
- Llená el bloque "Research findings" al inicio de phase-1-foundation/learnings.md.
- Si encontrás un cambio mayor en LangChain / LiteLLM / OTel respecto al diseño, PAUSÁ y preguntame antes de proceder.

Restricciones específicas de esta fase:
- NO tocar chat.py, deep_agent.py, graph.py, trace_recorder.py, usage_tracking.py, ni el extraction_card_flow.py. El módulo nuevo se construye aislado.
- Cualquier cambio al hot path es Fase 2, no Fase 1.
- Tests primero (TDD).
- Stage por nombre.

Ejecutá las tasks T1.1 a T1.13 del plan en orden. Cada task tiene criterio de aceptación. No avances al siguiente task si el criterio no está verificado con evidencia.

Al cerrar fase:
- Llená phase-1-foundation/learnings.md con decisiones, sorpresas, métricas.
- Llená phase-1-foundation/deferred-debt.md (puede ser "ninguno", pero explícito).
- Verificá phase-1-foundation/completion-checklist.md item por item.
- Devolveme el contenido literal de /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/handoff-prompts/start-phase-2.md para que abra Fase 2 en otra conversación.

Empezá ejecutando la investigación de research-checklist.md.
```

---

**Notas para Chris:**
- Si la conversación se queda corta de contexto: cerrar fase actual con commit + docs llenos, abrir nueva conversación con el siguiente prompt en `handoff-prompts/start-phase-2.md`.
- Si Claude propone "atajos" o "deprecation parcial": rechazar — viola PRINCIPLES.md.
- Si Claude pregunta si saltarse research: rechazar.
