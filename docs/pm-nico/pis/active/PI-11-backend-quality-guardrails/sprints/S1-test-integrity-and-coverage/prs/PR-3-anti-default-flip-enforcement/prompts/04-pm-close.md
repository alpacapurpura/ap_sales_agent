# Prompt — PM Close (PR-3)

> Ejecutar cuando builder + auditor retornan PASS.

## Acciones

1. Lee:
   - `IMPL-LOG.md`
   - `REVIEW.md`
   - `gate-output.json`
   - `git log development --oneline` últimos commits PR-3
2. Verificá criterios PR.md:
   - [ ] `.claude/rules/anti-default-flip-audit.md` existe + estructura completa
   - [ ] CLAUDE.md update con conditional rule trigger
   - [ ] `tests/architecture/test_no_legacy_eventbus_mock_when_outbox_on.py` existe + passes
   - [ ] Bypass mechanism funcional + test del test
   - [ ] Failure message linkea regla
   - [ ] Performance <2s
3. Escribí `RESULT.md` con:
   - Outcome: regla cementada + arch fitness layer activo
   - Surface: archivos creados/modificados
   - Métricas: violations baseline post-PR-1 = 0
   - Decisión: enforcement layers tabla referencia
   - Lineage: linkea PR-1 + PR-4
4. NO update `current-state/` (meta-arquitectural).
5. Append decisión PI-11 § decisions: "PR-3 cementó regla anti-default-flip + arch fitness layer".
6. Append learning S1 § learnings: pattern reusable para futuros side-effect flips (LITELLM_PROXY_ENABLED, etc.).
7. Cambiá `Estado: shipped` en PR.md.

## Próximo paso

Si PR-1 ya shipped → ejecutar PR-4 (PM directo):
```
Próximo paso: ejecutar `docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-4-update-agents-skills-default-flip-audit/prompts/01-pm-execute.md` (PM directo, no builder técnico)
```

Si PR-1 todavía no shipped → esperar PR-1 PASS antes PR-4.
