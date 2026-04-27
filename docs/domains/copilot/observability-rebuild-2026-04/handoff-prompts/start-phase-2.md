# Prompt para iniciar Fase 2 en una conversación nueva

Pegá el bloque siguiente literalmente en una nueva conversación de Claude Code:

---

```
Voy a ejecutar la Fase 2 del rediseño de observabilidad del copilot (proyecto Nicolify / AISALESHT).

Esta fase es el SWITCH ATÓMICO: en un solo commit cambiamos el hot path de chat.py + extraction_card_flow.py y BORRAMOS trace_recorder.py + usage_tracking.py + node_trace.py. Es el commit de mayor riesgo del rebuild — manejalo con cuidado.

Lee primero estos documentos en este orden:

1. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/README.md
2. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/ARCHITECTURE.md
3. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/PRINCIPLES.md
4. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-1-foundation/learnings.md
5. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-1-foundation/deferred-debt.md
6. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-1-foundation/completion-checklist.md (verificá que TODO esté ✓ — si no, pausá y avisame)
7. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-2-atomic-switch/plan.md
8. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-2-atomic-switch/research-checklist.md
9. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-2-atomic-switch/completion-checklist.md

Reglas globales del repo (ver CLAUDE.md) aplican.

Antes de empezar:
- Ejecutá research-checklist.md.
- Llená "Research findings" en phase-2-atomic-switch/learnings.md.
- `git status --short` y `git log --oneline -10` — si hay WIP en chat.py o extraction_card_flow.py de otra sesión, POSTERGAR fase y avisame.
- Verificá Fase 1 cerrada por completo (completion-checklist todos ✓). Si no, NO empieces Fase 2.
- Si hubo deferred-debt en Fase 1, decidí qué items entran al alcance de Fase 2 vs quedan para Fase 3.

Restricciones específicas:
- El switch (T2.5) DEBE ser un solo commit. Cambios + deletions juntos. Si requerís commits previos para preparar (event bus, domain events, register), hacelos antes (T2.2-T2.4).
- Conservar best-effort writes (excepción en obs no rompe turn).
- Conservar shape de turn_end.data JSONB para compat con UI vieja durante Fase 2 (Streamlit migra recién en Fase 3).
- Feature flag rollback temporal SÍ permitido durante 24-48h, borrar en commit posterior dentro de Fase 2.
- Tests primero, sin excepciones.
- Stage por nombre. Conventional commits: `feat(copilot-obs): atomic switch — wire callback handler, delete legacy paths`.

Después del switch:
- 24-48h de soak en dev environment monitoreando logs y diff de cost agregado (debe ser <5%).
- Solo entonces borrar feature flag.
- Solo entonces dar fase por cerrada.

Plan de rollback (si rompe):
1. Activar feature flag `COPILOT_OBS_REBUILD_DISABLED=true`.
2. Si flag no alcanza: `git revert <hash del commit atómico>` — NUNCA `git reset --hard` sobre development.
3. Investigar root cause con trazas existentes.

Al cerrar fase:
- Llená phase-2-atomic-switch/learnings.md.
- Llená phase-2-atomic-switch/deferred-debt.md.
- Verificá phase-2-atomic-switch/completion-checklist.md.
- Devolveme el contenido literal de /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/handoff-prompts/start-phase-3.md para abrir Fase 3.

Empezá leyendo los docs en orden y luego ejecutando la investigación.
```

---

**Notas para Chris:**
- Esta fase requiere ventana sin interrupciones para el switch atómico (4-6h).
- Después del switch, hay 24-48h de soak antes de cerrar fase. NO arrancar Fase 3 antes del soak.
- Si Claude propone hacer el switch en múltiples commits "para reducir riesgo": rechazar — viola PRINCIPLES.md (un commit atómico es justamente lo que reduce riesgo de quedar en estado inconsistente).
