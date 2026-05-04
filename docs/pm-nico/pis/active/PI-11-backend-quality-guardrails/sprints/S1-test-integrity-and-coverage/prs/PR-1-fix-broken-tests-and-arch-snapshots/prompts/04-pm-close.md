# Prompt — PM Close (PR-1)

> Ejecutar cuando ambos auditores (business + agentic) retornan PASS y polluter está fixed at source SIN band-aid.

## Acciones

1. Lee:
   - `IMPL-LOG.md` business + agentic
   - `REVIEW-backend.md` + `REVIEW-agentic.md`
   - `gate-output.json` final
   - `git log development --oneline` últimos commits PR-1
2. Verificá criterios de aceptación de PR.md:
   - [ ] Stash{0} aplicado, revisado, commiteado
   - [ ] `pytest` 0 failed, 0 deselected, 0 `flaky` permanentes
   - [ ] `vitest run` 0 failed
   - [ ] Polluter `test_chat_flow_telegram_new_lead_snapshot` fixed at source (no marker)
   - [ ] Singleton fixture exhaustivo + lista validada IMPL-LOG
   - [ ] EventBus mocks migration audit completo IMPL-LOG (business + agentic)
   - [ ] Snapshot helpers outbox-aware
   - [ ] LegacyEventBus.publish runtime warning emit
   - [ ] litellm.py kimi clamp activo + test regression
   - [ ] Arch fitness 78/78 PASS
3. Escribí `RESULT.md` con:
   - **Outcome**: lista de tests fixeados + polluter root cause + EventBus migration count + singleton inventory + bug fix litellm + LegacyEventBus deprecation
   - **Surface**: archivos modificados por surface (business vs agentic vs FE)
   - **Métricas**: tests antes (25 BE failed + 2 FE failed + 1 flaky polluter) vs después (0 failed, 0 flaky permanente)
   - **Decisiones cementadas**: D1-D7 (referenciar PI.md)
   - **Polluter root cause**: detalle de qué fue + fix aplicado
   - **Singleton inventory**: lista exhaustiva con grep evidence
   - **EventBus migration**: lista paths migrados business + agentic
4. NO update `current-state/` (sin capacidades user-facing nuevas — PR es hardening calidad).
5. Append decisiones a `PI-11/decisions.md` (crear si no existe).
6. Append learnings a `S1-test-integrity-and-coverage/learnings.md` (crear si no existe):
   - Patrón "default flag flip = side-effect call path change → audit tests obligatorio" (cementado en PR-3 + PR-4)
   - Polluter hunt methodology que funcionó (qué bisección + sospechosos primarios + JSON diff workflow)
   - Singleton fixture exhaustive pattern (referencia para futuros agentes)
   - Costo PI-11 vs costo replicado per-deploy si no hubiera PI
7. Cambiá `Estado: shipped` en PR.md.
8. Verificá `MEMORY.md` no necesita update (solo si salió learning durable que merece memory entry — Chris confirma).
9. Informá a Chris:
   ```
   PR-1 shipped. CI verde permanente. Polluter fixed at source. Próximo paso: ejecutar PR-3/prompts/02-builder-start.md (si no shipped paralelo) o PR-4 PM directo.
   ```

## Próximo paso

- Si PR-3 ya shipped paralelo (ideal flow):
  ```
  Próximo paso: ejecutar `docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-4-update-agents-skills-default-flip-audit/prompts/01-pm-execute.md` (PM directo, no builder técnico)
  ```
- Si PR-3 todavía no shipped:
  ```
  Próximo paso: ejecutar `docs/pm-nico/pis/active/PI-11-backend-quality-guardrails/sprints/S1-test-integrity-and-coverage/prs/PR-3-anti-default-flip-enforcement/prompts/02-builder-start.md`
  ```
