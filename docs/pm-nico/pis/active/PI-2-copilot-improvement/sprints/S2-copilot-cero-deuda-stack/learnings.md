# Learnings — S2-copilot-cero-deuda-stack

> Append durante sprint, congela al cerrar.

## PR-1 fe-swap-suggestions-api shipped 2026-04-30

### Técnicas
1. **D-9 voice adapter pattern** — URL swap simple no funciona cuando endpoints tienen shapes distintos. Adapter mantiene firma pública (`TranscriptionResponse` consumers sin cambios) + traduce shapes interno. Reusable patrón futuras endpoint migrations.
2. **Best-effort doble try/except** (engine + EventBus.publish independientes) preserva resilencia copilot rule sin acoplar dos failure modes. Bug en EventBus no rompe response engine; bug en engine no rompe emisión event downstream.
3. **React Query queryKey [route, conversationId]** = patrón correcto para hooks contextuales — cambio de route OR conversation re-fetch automático sin invalidate manual.
4. **Mutation fire-and-forget que NO invalida queries** — apropiado cuando server no re-rankea por mutation individual. Reduce re-fetches inútiles.
5. **Anchor budget preservado**: PR-1 reusó anchor `[COPILOT-SUGGESTIONS-ENGINE]` ya creado S1 — cap 36/37 sin bumpear.
6. **Architect verificación shapes en código real** evitó deuda futura — assumption "URL swap simple" rota por architect leyendo ambos endpoints; D-9 adapter shipped en mismo PR.

### De proceso
7. **L-PROC-1 confirmado en S2**: auto-loop builder→auditor sigue truncando. PR-1 BE builder PASS pero NO spawnea auditor (Phase 2 skipped). FE builder COMPLETÓ implementación (21 tests verde, 4 sub-deliverables) pero stalled antes commit + audit. PR-1 BE auditor real spawn por main thread funcionó (PASS 1 iter). PR-1 FE auditor stalled 600s — main thread completó manualmente quality gates + REVIEW-frontend.md. **Patrón consistente — FE PRs L+ requieren main thread takeover audit.**
8. **BE+FE cross-stack cohabitan en mismo commit** OK — `e53b7ef6` incluye ambas surfaces. Filesystem compartido permite single commit con paths múltiples (siempre que cada subset esté tested verde individualmente).
9. **Architect-empowered (16 decisions ZERO open questions) + path-explicit en builder prompt** evitó colisión sesión paralela PI-1 (campaigns) y misma sesión builder PR-2 architect simultáneo. M8 pattern (extend no destroy) funcionó bien.

### De producto
10. **Cero deuda S1 PR-1 D-5 + S1 PR-2 FE swap = ambas cerradas en PR-1** — voice transcription end-to-end funcional, smart-chips dinámicas live consumiendo motor BE.
11. **Métricas adopción smart-chips habilitadas día 1** vía `copilot_trace_event` query ratio. No requiere tabla nueva ni migration.

## Para process/process-learnings.md (escalable a global)

- **L-PROC-FE-AUDIT-1**: para FE PRs L+, planear main thread takeover audit por default (auto-loop FE auditor stalla token cap consistentemente).
- **L-PROC-VOICE-MIG-1**: endpoint URL migration → architect verifica shapes BE+FE en código real ANTES decidir "solo URL swap". Adapter en FE = patrón seguro vs assumption.
