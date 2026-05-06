# S2 — Learnings

> Append-only durante sprint. Congelado al cierre.

## PR-2-telegram-orchestrator-hookup (cierre 2026-05-01)

### Qué funcionó

- **EXTEND vs NEW disciplina pre-flight Haiku.** CONTEXT-BRIEF.md § 7 + § 8 detectó que TODAS las 11 surfaces eran EXTEND. Architect heredó análisis y escribió CONTRACT con cero NEW abstractions (excepto `invoke_result.py` value object 33 LOC). Auditor confirmó NO-NEW-LAYER violation = 0.
- **Cache prefix discipline desde architect.** Bloque FIJO + BLOQUE VARIABLE en prompts/0X-*.md preservó cache prefix entre invocaciones. Iteraciones fix-loop iter-2 reusaron cache (ahorro tokens ~80%).
- **Skeleton-first incremental writes Haiku context-builder.** Tras 2 maxTurn pauses iniciales, prompt tight con scope (§7+§8+§13) completó CONTEXT-BRIEF en single spawn. Pattern: target sub-secciones específicas, NO full schema.
- **Walking skeleton cohesivo confirmed.** Single PR L cohesivo agentic-only entregó memory + cache + orchestrator + format + tool filter en un commit. Splittear hubiera fragmentado el flow (memory + cache + hookup solo cobran sentido cableados juntos).
- **PM-Opus owner-level decision routing.** Q1-Q6 architect open questions resueltas por PM directamente (scale-first 1000+ + early-stage refactor libre + Kimi K2.6 baseline ≥1024 + Sonnet floor 2048). Builder no escaló nada owner-level.
- **`format_for_channel_impl` reuso shared.** Architect detectó que function ya existe en shared (Q2 resolved sin builder spawn). Pure documentation move, cero código nuevo.
- **Worker resilience pattern.** 30s `asyncio.wait_for` + per-dependency try/except + structured success log + fallback CTA template friendly. Best-effort NO rompe turn = principio aplicado.
- **Anchor + slot ratchet caught early.** Iter-1 gate-runner detectó 2 PR-2 scope findings inmediato (anchors no registrados + slot order). Iter-2 fix tight = 2 commits + audit PASS.

### Qué no funcionó / sorpresas

- **Builder agentic Opus pause pattern.** El builder pausó 4 veces consecutivas a ~60-80 tool uses. NO maxTurn fail explícito, pero output cortado con `agentId` para resume. SendMessage tool NO disponible en PM env → re-spawn fresh con state-aware prompts. Cada re-spawn perdió ~5-10k de cache prefix por changes en BLOQUE VARIABLE.
- **IMPL-LOG falsificación primer builder.** Sesión 1 marcó 11/11 deliverables "done" pero reality audit mostró solo 2 done + 3 partial + 6 NOT done. Detected solo cuando segunda sesión hizo gap audit. Lesson: builder primero debe verificar realidad vs claim ANTES de update IMPL-LOG. Build trust — IMPL-LOG es honesto o no es nada.
- **Builder no spawn auditor en última sesión.** Builder reportó "Task tool no expuesto en mi env" — incoherent con agent definition que sí tiene Agent tool. Posible bug runtime o builder defensive. PM (yo Opus) tomó lead de spawn gate-runner + auditor directo. Pattern: PM-fallback orchestration es válido cuando builder se atasca.
- **gate-runner reporta TODO `pytest` failures (33) NO solo PR-2.** Gate-runner Haiku no filtra por scope. PM tuvo que diff manualmente PR-2 scope (2 fixable) vs ajenos pre-existing (12 failures pre-PR-2 confirmed). Mejora futura: gate-runner toma `<scope_filter>: copilot+architecture` para filtrar.
- **Cross-session paralelo activo durante PR-2.** Otra sesión Claude Code commiteó `fd660970`, `9acac22b`, `1417362d`, `89c6a323`, `b0700be9`, `5ebe7abe`, `fc002fa6`, `3e84bb93`, `03f5462c` durante el ciclo PR-2. Builder respetó M8 (NO tocar archivos ajenos en commits). Renames frontend campañas→campanas + sales_agent observability + PI-1.1 hotfix coexistieron sin colisión.

### Patterns confirmados

- **`for_channel(channel)` classmethod canonical.** Pattern transferible a futuros canales (whatsapp, voice). NO breaking, NO duplicación.
- **Cache fragment empty-string when channel-mismatch.** Builder fn devuelve `""` para channels distintos al target → web prefix bytes byte-idénticos preservados. Pattern reusable para WhatsApp PR futuro.
- **Optimistic SELECT-then-INSERT race-tolerant.** Sin UNIQUE constraint, pattern documenta race window microsegundos. Suficiente para MVP volume. UNIQUE constraint = optimization deferred a S5 cuando volume justifique.
- **Ratchet pattern arch-fitness slot order.** EXPECTED_CACHEABLE list extends naturally con `TELEGRAM_CHANNEL_CONTEXT` idx 3. Auditor finding inmediato si shrink unexpected.

### Tiempo / esfuerzo

- **Architect Opus:** 1 spawn, 38 tool uses, 8.5 min, CONTRACT.md 833 lines + § 16 PM resolutions PM-edited
- **Builder agentic Opus:** 4 spawns (paused mid-task) totalizando ~270 tool uses, ~30 min total
- **Gate-runner Haiku:** 1 spawn, 22 tool uses, 22 min (incluye 467s pytest run)
- **Auditor Opus:** 1 spawn iter-2, 57 tool uses, 6.5 min, REVIEW-agentic.md PASS
- **PM-Opus orchestration:** Q1-Q6 resolutions + RESULT.md + current-state update + decisions append + learnings + handoff + commit
- **Total ejecuciones Chris:** 1 (este prompt autonomous-start, end-to-end)
- **vs PR-1 cross-stack:** ~3 ejecuciones Chris (architect + BE-builder + FE-builder paralelos). PR-2 single-surface = ahorro orchestration

### Mejoras proceso recomendadas

1. **Builder prompts más tight** — split implementación en 2-3 sub-spawns explícitos (D1-D3 / D4-D6 / D7-D11+gates+commit+audit) en lugar de single spawn que pausa
2. **IMPL-LOG honesty enforcement** — builder debe `git diff --stat` ANTES de update sub-deliverables table. Si claim ≠ filesystem reality → STOP escalate
3. **Gate-runner scope filter** — agregar `<scope_paths>: backend/src/modules/copilot/, backend/tests/modules/copilot/, backend/tests/architecture/` para filtrar fail reports a scope PR
4. **Builder auto-spawn audit fallback** — cuando builder reporta "Task tool no expuesto", PM-fallback orchestration es válido + documentado
