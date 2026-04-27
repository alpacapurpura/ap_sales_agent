# Prompt para iniciar Fase 3 en una conversación nueva

Pegá el bloque siguiente literalmente en una nueva conversación de Claude Code:

---

```
Voy a ejecutar la Fase 3 (final) del rediseño de observabilidad del copilot (proyecto Nicolify / AISALESHT).

Esta fase entrega el OBJETIVO DE NEGOCIO: dashboard Streamlit de costo LLM por tenant con ciclo billing 25-25, y cierra la deuda técnica restante (PII, retention, alertas). Sin tocar el hot path del copilot.

Lee primero estos documentos en este orden:

1. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/README.md
2. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/ARCHITECTURE.md
3. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/PRINCIPLES.md
4. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-1-foundation/learnings.md (referencia)
5. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-2-atomic-switch/learnings.md (referencia)
6. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-2-atomic-switch/deferred-debt.md
7. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-2-atomic-switch/completion-checklist.md (verificá ✓)
8. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-3-reporting-hardening/plan.md
9. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-3-reporting-hardening/research-checklist.md
10. /home/chris/AISALESHT/docs/domains/copilot/observability-rebuild-2026-04/phase-3-reporting-hardening/completion-checklist.md

Reglas globales del repo (ver CLAUDE.md) aplican. ESPECIAL ATENCIÓN: regla 11 (Spanish neutro LatAm SIN voseo) — el dashboard y todos los textos user-facing deben usar tuteo (`tú/tienes/puedes/cambia`), nunca `vos/tenés/podés/mirá`.

Antes de empezar:
- Ejecutá research-checklist.md.
- Llená "Research findings" en phase-3-reporting-hardening/learnings.md.
- Verificá Fase 2 cerrada (soak completado, diff cost <5%, feature flag borrado).
- `git status --short` — verificá no hay WIP en backend/src/admin/ ajeno.

Restricciones específicas:
- NO tocar hot path del copilot (chat.py, deep_agent.py, graph.py). Esta fase es admin + workers + reporting.
- Spanish neutro: verificar dashboard con `grep -nE "vos|sos|tenés|querés|podés|sabés|hacés|venís|decís|mirá|dejá|poné|usá|hacé|elegí" backend/src/admin/modules/costo_copilot.py` → cero matches.
- Streamlit page nueva sigue patrón registry de `.claude/rules/admin-panel.md`: 1 PageSpec + 1 pages/{slug}.py wrapper + 1 modules/{name}.py::render_*.
- PII redaction NO debe ser síncrono > 100ms en hot path — si Presidio es lento, queda regex sincrónico + Presidio en worker async (anotar como deferred).
- Performance dashboard: `tenants_summary` < 200ms para 50 tenants × 30 días.
- Tests primero, sin excepciones.

Al cerrar fase (= cierre del rebuild completo):
- Llená phase-3-reporting-hardening/learnings.md con métricas finales del rebuild (3 fases combinadas).
- Llená phase-3-reporting-hardening/deferred-debt.md.
- Items relevantes que queden → mover a /home/chris/AISALESHT/docs/mejoras-proceso/to-do.md (regla 12 CLAUDE.md).
- Update /home/chris/AISALESHT/docs/domains/copilot/INDEX.md con entrada al rebuild + dashboard.
- Update /home/chris/AISALESHT/.claude/rules/copilot-resilience.md con queries a copilot_llm_call.
- Crear /home/chris/AISALESHT/.claude/rules/copilot-observability.md (regla nueva — content en plan.md T3.12).
- Mensaje final con resumen del rebuild completo: archivos eliminados, líneas, commits, link al dashboard, items en deferred-debt que necesitan seguimiento.

Empezá leyendo los docs en orden y luego ejecutando la investigación.
```

---

**Notas para Chris:**
- Al cerrar Fase 3, el rebuild está completo. No hay "Fase 4". Items pendientes van a `docs/mejoras-proceso/to-do.md` o se cierran como decisión consciente de "no hacer".
- Validá manualmente el dashboard con tu data real antes de declararlo cerrado: abrí admin, navegá a "Costo Copilot", verificá que muestra tenants reales con costos coherentes.
- Si el dashboard muestra costos inesperadamente altos o bajos vs lo que esperabas: posible bug en PricingResolver o FXResolver. Investigar antes de cerrar.
