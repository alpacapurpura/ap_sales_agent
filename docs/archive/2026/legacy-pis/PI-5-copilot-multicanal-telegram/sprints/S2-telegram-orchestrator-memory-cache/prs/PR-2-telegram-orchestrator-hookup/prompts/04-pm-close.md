# Prompt — PM close loop

> Copy-paste este prompt al volver a sesión `/pm` para cerrar el PR-2.

```
/pm

PR-2-telegram-orchestrator-hookup terminó implementación + auditoría (single surface agentic). Cierro el loop.

Lee:
- `docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup/IMPL-LOG.md`
- `docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup/REVIEW-agentic.md`
- Último commits: `git log --oneline -15`
- gate-output.json (último iter agentic)

Validá:
- Verdict agentic = PASS antes de cerrar. Si verdict != PASS → escalate (no cierro PR).
- Cero cambios FE en diff (regla scope PR-2).
- Cero cambios módulos negocio en diff.
- Cero migration nueva en diff.

Hacer:
1. Escribir `RESULT.md`:
   - Outcome real vs esperado:
     · ¿Worker linked branch invoca orchestrator real (no placeholder)? Sí/No con commit ref
     · ¿`TELEGRAM_CONTEXT_WINDOW_CONFIG` aplicado runtime cuando channel='telegram'? Test ref
     · ¿`TELEGRAM_CHANNEL_CONTEXT` cacheable fragment ≥1024 tokens validado arch fitness? Threshold real medido
     · ¿Tool registry filter runtime excluye web-only groups en channel='telegram'? Test ref
     · ¿Format adapter MarkdownV2 escapa correctamente sin doble-escape? Test ref
     · ¿Latencia first-token p95 medible ahora con orchestrator real? Reportar si instrumentado
     · ¿Cache hit rate medible vía `copilot_llm_call`? Reportar si instrumentado
   - Surface entregada (paths archivos modificados + nuevos)
   - Capacidades nuevas con lineage commit hashes
   - Decisiones de implementación tomadas (especialmente EXTEND vs NEW resoluciones por subsistema: memory builder, system_prompt_layout, orchestrator entrypoint, conversation repo, format adapter, telegram worker)
   - Métricas tests pass + coverage delta + iteraciones gate-runner + iteraciones audit
   - Deuda técnica generada (S3 deferred, observabilidad enhancement futuro, etc)
2. Update `docs/pm-nico/current-state/copilot.md`:
   - Actualizar capability "Canal Telegram — DMs linkeados magic link" de "parcial (LLM placeholder)" → "live (orchestrator real)" con lineage PR-2 commit hash
   - Append bloque `### Cap: Canal Telegram — orchestrator real + memory cost-aware + prefijo cacheable Anthropic`:
     · Introducida: PR-2 (PI-5, S2, commit {hash}, 2026-04-30)
     · Estado: live
     · Operable copilot: sí (12+ tool groups telegram-allowed, orchestrator real, memory windowed, cache hit ahorro)
     · Surface code: copilot/application/memory + copilot/application/orchestrator + copilot/infrastructure/workers/telegram_worker.py
     · Memory: TELEGRAM_CONTEXT_WINDOW_CONFIG (3000/15/600/12000)
     · Cache: TELEGRAM_CHANNEL_CONTEXT fragment ≥1024 tokens umbral Anthropic
     · Tool subset runtime filter: web-only excluded (navigation, guided, landing.mutations, offer_section.mutations) → redirect template
     · Format: MarkdownV2 escape via shared/agent_observability/channels/format.py::escape_markdown_v2
3. Append decisiones implementación relevantes a `pis/active/PI-5-copilot-multicanal-telegram/decisions.md` como D-PI5-IMPL-007+ (EXTEND vs NEW resoluciones, signature changes backward compat, format adapter helper reuse, conversation lookup concurrency strategy)
4. Append learnings PR-2 a `sprints/S2-telegram-orchestrator-memory-cache/learnings.md` (qué funcionó, qué no, sorpresas — especially patterns reuse `ContextWindowBuilder` por inyección config + cache fragment threshold compute técnica + tiempo single-surface vs cross-stack PR-1)
5. Cambiar `Estado: shipped` en `PR.md`
6. PR-2 = único PR S2 → llenar `sprints/S2-telegram-orchestrator-memory-cache/handoff.md` con decisiones consolidadas para S3:
   - Surface live: orchestrator multi-channel + memory inyectada + cache fragment + tool filter runtime
   - Decisiones críticas para S3 HITL: cómo el orchestrator pasa channel info a sales_agent escalation request (interrupt LangGraph)
   - Skills/agentes recomendados S3
7. Si último PR sprint S2 → marcar sprint done. Considerar mover S3 placeholder → in-progress (Chris autoriza).

Brief < 200 palabras: qué shipped + qué cambió en producto + acción Chris siguiente.
```

## Notas

- `/pm` no inventa el RESULT — extrae info de IMPL-LOG + REVIEW-agentic + git log.
- Si REVIEW-agentic.md tiene verdict ≠ `PASS` → `/pm` NO escribe RESULT, escala a Chris para decidir.
- `current-state/copilot.md` es donde "el producto" se actualiza — capability PR-1 upgraded a "live" + capability nueva PR-2 appended. PR-folder es histórico.
- Acción Chris pendiente NO bloquea cierre RESULT (BotFather + setWebhook live test puede ocurrir post-cierre PR-2):
  - BotFather crear `@nicolify_copilot_dev_bot` + `@nicolify_copilot_bot` (si no hecho)
  - setWebhook con secret_token a dev/prod URLs
