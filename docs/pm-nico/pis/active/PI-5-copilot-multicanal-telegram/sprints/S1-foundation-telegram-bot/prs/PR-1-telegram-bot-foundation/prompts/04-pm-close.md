# Prompt — PM close loop

> Copy-paste este prompt al volver a sesión `/pm` para cerrar el PR.

```
/pm

PR-1-telegram-bot-foundation terminó implementación + auditoría (cross-scope agentic + frontend). Cierro el loop.

Lee:
- `docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S1-foundation-telegram-bot/prs/PR-1-telegram-bot-foundation/IMPL-LOG.md`
- `docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S1-foundation-telegram-bot/prs/PR-1-telegram-bot-foundation/REVIEW-agentic.md`
- `docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S1-foundation-telegram-bot/prs/PR-1-telegram-bot-foundation/REVIEW-frontend.md`
- Último commits: `git log --oneline -15`
- gate-output.json (último iter agentic + frontend)

Validá:
- AMBOS verdicts (agentic + frontend) = PASS antes de cerrar. Si uno != PASS → escalate.

Hacer:
1. Escribir `RESULT.md`:
   - Outcome real vs esperado (link end-to-end < 60s? webhook < 200ms? rate limiter activo?)
   - Surface entregada (rutas API, tablas, componentes FE)
   - Capacidades nuevas con lineage commit hashes
   - Decisiones de implementación tomadas (especialmente EXTEND vs NEW resoluciones)
   - Métricas tests pass + coverage + iteraciones gate-runner + iteraciones audit
   - Deuda técnica generada (S2 deferred items, FE polling hardening, etc)
2. Update `docs/pm-nico/current-state/copilot.md`:
   - Sección "Capacidades actuales" → añadir capability "Canal Telegram — DMs linkeados magic link, webhook non-blocking + ARQ async, tool subset Telegram-allowed (12+ groups), redirect template tools web-only"
   - Bloque `### Cap: Telegram channel foundation` con introducida/lineage/operable copilot
   - Sección "Conexiones cross-módulo" → confirma cero acoplamiento copilot↔sales_agent (separación física)
3. Append decisiones implementación relevantes (EXTEND vs NEW resoluciones del architect, conflictos resueltos durante builder) a `pis/active/PI-5-copilot-multicanal-telegram/decisions.md` como D-PI5-032+
4. Append learnings PR-1 a `sprints/S1-foundation-telegram-bot/learnings.md` (qué funcionó, qué no, sorpresas — especially patterns reuse `escape_markdown_v2`/`sanitize_payload`/ARQ stack, tiempo paralelización 2 builders)
5. Cambiar `Estado: shipped` en `PR.md`
6. PR-1 = único PR S1 → llenar `sprints/S1-foundation-telegram-bot/handoff.md` con decisiones para S2 (memory + cache prefix + tool registry deepen + non-link UX)
7. ¿Próximo paso? PR-2 S2 (memory + cache + tool subset deepen) o cerrar sprint S1 + dejar S2 placeholder hasta Chris autorice arrancar

Brief < 200 palabras: qué shipped + qué cambió en producto + acción Chris siguiente.
```

## Notas

- `/pm` no inventa el RESULT — extrae info de IMPL-LOG + REVIEW + git log.
- Si REVIEW.md tiene veredicto != `approve` → `/pm` NO escribe RESULT, escala a Chris para decidir.
- `current-state/{módulo}.md` es donde "el producto" se actualiza. PR-folder es histórico.
