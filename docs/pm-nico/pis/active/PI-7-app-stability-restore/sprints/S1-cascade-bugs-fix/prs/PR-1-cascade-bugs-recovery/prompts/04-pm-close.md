# Prompt — PM close loop PR-1-cascade-bugs-recovery

> Copy-paste este prompt al volver a sesión `/pm` para cerrar el PR.

```
/pm

PR-1-cascade-bugs-recovery terminó implementación + auditoría. Cierro el loop.

Lee:
- docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery/IMPL-LOG.md
- docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery/REVIEW.md
- docs/pm-nico/pis/active/PI-7-app-stability-restore/sprints/S1-cascade-bugs-fix/prs/PR-1-cascade-bugs-recovery/gate-output.json
- Últimos commits: git log --oneline -10

Hacer:
1. Verificar smoke real Telegram Chris-mediated:
   - Bot respond correct voice-tenant Visionarias (no error fallback)
   - sales_agent_trace_event turn_end status='ok'
   - sales_agent_llm_call cost_usd > 0
   - visionarias_litellm container Up healthy
2. Escribir RESULT.md siguiendo template (process/pr-folder-template/RESULT.md):
   - Outcome real vs esperado (matriz pre-fix vs post-fix)
   - Surface entregada (paths + commits)
   - Bug #7 fix detalle + evidence test + RCA
   - Bug #9 fix detalle + container status verify
   - Decisiones tomadas durante implementación
   - Métricas: turn count post-fix, cost_usd, latency turn_end
   - Deuda técnica generada (si la hay)
3. Update current-state/sales-agent.md:
   - Tabla "Estado calidad funcional" → row "LLM call" → status: live (was: down due to litellm)
   - Append PR-1-cascade-bugs-recovery a "PIs históricos"
   - Lineage capacidad "Sales agent end-to-end" → última modificación PR-1 PI-7 + commit + fecha
4. Update current-state/brand.md:
   - Append note Bug #7 fix lineage en sección "Estado calidad funcional"
   - Capacidad "brand_data_adapter ORM→DTO conversion" lineage PR-1 PI-7
5. Append decisiones relevantes a pis/active/PI-7-app-stability-restore/decisions.md:
   - D-1: Single PR cross-surface vs split (referencia CONTRACT § 0 razones)
   - D-2: Bug #7 fix approach elegido (A | B | C de PR.md options)
   - D-3: Bug #9 fix approach elegido + impacto otros services
6. Append learnings a sprints/S1-cascade-bugs-fix/learnings.md:
   - Cascade discovery pattern: bug observability emerge bug LLM stack down
   - Smoke real Chris-mediated value vs synthetic test
   - Cualquier process improvement detectado
7. Cambiar Estado: shipped en PR.md.
8. Última PR del sprint S1 → llenar sprints/S1-cascade-bugs-fix/handoff.md:
   - Decisiones congeladas
   - Surface entregada
   - Próximo sprint (S2 si más bugs cascade) o cierre PI-7
9. Si métrica única éxito PI-7 cumplida → escribir pis/active/PI-7-app-stability-restore/retro.md + mover folder a pis/archive/PI-7-app-stability-restore/.
10. Update roadmap.md:
    - PI-7 active → Done
    - Si nuevos bugs cascade post-smoke → abrir PI-8 cascade-recovery-N+1
11. Decirme próximo paso: ¿abrir nuevo PI? ¿continuar PI-3/4/5? ¿cierre limpio?

Quiero brief al final < 200 palabras con qué shipped + qué cambió en producto + métrica única éxito PI-7 status.
```

## Notas

- /pm no inventa el RESULT — extrae info de IMPL-LOG + REVIEW + git log + smoke verify.
- Si REVIEW.md tiene veredicto != PASS → /pm NO escribe RESULT, escala a Chris para decidir.
- current-state/{módulo}.md es donde "el producto" se actualiza. PR-folder es histórico.
- Si smoke Chris-mediated falla post-PASS audit → bug N+1 cascade descubierto. PM abre handoff a S2 o PI-8.
