# Prompt — PM Close (PR-2)

> Ejecutar cuando auditor retorna PASS.

## Acciones

1. Leer IMPL-LOG.md + REVIEW.md.
2. Verificar cobertura crm ≥75% y scheduling ≥75%.
3. Escribir RESULT.md con:
   - Outcome: cobertura antes/después por módulo.
   - Surface: archivos de tests nuevos.
   - Métricas: # tests nuevos, % cobertura delta.
4. No hay update de current-state/ (no capacidades user-facing nuevas).
5. Append decisiones a `PI-11/decisions.md`.
6. Cambiar Estado PR-2 → `shipped`.
7. Si es último PR del sprint → llenar `learnings.md` + `handoff.md` del sprint S1.
8. Informar a Chris: "PR-2 shipped. Sprint S1 listo. CI verde + cobertura P0 restaurada."

Próximo paso: Si hay S2 planeado → ejecutar prompts de S2. Si no → PI-11 listo para cierre.
