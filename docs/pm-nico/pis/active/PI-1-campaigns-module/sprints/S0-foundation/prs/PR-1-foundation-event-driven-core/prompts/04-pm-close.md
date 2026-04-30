# Prompt — PM close loop (PR-1 foundation-event-driven-core)

> Copy-paste este prompt al volver a sesión `/pm` para cerrar PR-1.

```
/pm

PR-1-foundation-event-driven-core terminó implementación + auditoría. Cierro el loop.

Lee:
- `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-1-foundation-event-driven-core/IMPL-LOG.md`
- `docs/pm-nico/pis/active/PI-1-campaigns-module/sprints/S0-foundation/prs/PR-1-foundation-event-driven-core/REVIEW.md`
- Últimos commits: `git log --oneline -15`

Hacer:
1. **Verificar verdict REVIEW.md = PASS**. Si WARN/FAIL → escalar a Chris ANTES de escribir RESULT, decidir si fix o aceptar.
2. Escribir `RESULT.md` siguiendo template (`process/pr-folder-template/RESULT.md`):
   - Outcome real vs esperado (3 primitivas + 3 emisores migrados con flags OFF + observability spec campaign)
   - Surface entregada concreta (paths, tablas, env vars, migration 109)
   - Capacidades nuevas con lineage (PR-1 + commit hashes + fecha)
   - Decisiones tomadas durante implementación (basadas en CONTRACT + bloqueadores resueltos)
   - Métricas: tests verdes, coverage delta, migration idempotente clone DB OK
   - Deuda técnica generada: 20 emisores legacy todavía en in-memory path (S2). Flag rollout pendiente PR siguiente
3. Update `current-state/campaigns.md`:
   - Append capability "Observability spec registered (`agent_kind=campaign`)" con lineage PR-1
4. Update `current-state/sales_agent.md`, `current-state/copilot.md`, `current-state/brand.md`:
   - Append capability "Outbox migration ready (behind flag USE_OUTBOX_PATTERN_*)" con lineage PR-1
5. Append decisiones a `pis/active/PI-1-campaigns-module/decisions.md`:
   - D12: Adapter pattern + feature flag por emisor (no big-bang)
   - D13: Soft-fail Redis IdempotencyService (better double-process que pérdida)
   - D14: ARQ worker dispatcher cron 10s (vs in-process scheduler)
   - (otras según architect/builder decidió)
6. Append learnings a `sprints/S0-foundation/learnings.md`:
   - Que funcionó (TDD por sub-deliverable, Explore audit pre-architect, etc)
   - Que cambiaría
   - Patterns reutilizables S1+
7. Cambiar `Estado: shipped` en `PR.md`.
8. Si PR-2 ya está refinado → próximo paso "ejecutar prompts/01-architect-start.md de PR-2".
9. Si último PR del sprint S0 → llenar `handoff.md` (decisiones + surface + agentes recomendados S1).

Quiero brief < 200 palabras con qué shipped + qué cambió en producto + flag rollout pendiente.
```

## Notas

- `/pm` no inventa el RESULT — extrae de IMPL-LOG + REVIEW + git log.
- Si REVIEW.md veredicto != PASS → `/pm` escala a Chris antes RESULT.
- `current-state/{m}.md` updates son responsabilidad PM (M2 parallel-safety).
- Flag rollout (cutover por módulo) NO es parte PR-1 — es PR siguiente.
