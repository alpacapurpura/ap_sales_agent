# Prompt — PM Close (PR-1)

> Ejecutar cuando ambos auditores (business + agentic) retornan PASS.

## Acciones

1. Leer IMPL-LOG.md (business) + IMPL-LOG.md (agentic) + REVIEW-backend.md + REVIEW-agentic.md.
2. Verificar que `pytest` colecta 0 failed (sin `--deselect` de estos tests).
3. Escribir RESULT.md con:
   - Outcome: lista de tests fixeados + arch fitness estado.
   - Surface: archivos modificados por surface.
   - Métricas: tests antes (10 failed) vs después (0 failed).
   - Decisiones: default outbox, imports DDD, endpoint legacy 410.
4. No hay update de current-state/ (no capacidades user-facing nuevas).
5. Append decisiones a `PI-11/decisions.md`.
6. Cambiar Estado PR-1 → `shipped`.
7. Informar a Chris: "PR-1 shipped. CI verde. Listo para PR-2."

Próximo paso: ejecutar `docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-2-coverage-p0-modules/prompts/02-builder-start.md`
