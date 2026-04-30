# S2 Learnings — Orchestrator + Cutover

> Lecciones para futuros sprints PI-1 + meta-process pm-nico.

## Cierre

- Cierre real: 2026-04-30
- PRs shipped: PR-5 (PASS post Sub-G) + PR-6 (PASS post Sub-G)
- Builders: 9 sub-spawns nicolify-backend (PR-5) + 6 sub-spawns nicolify-backend (PR-6)
- Auditores: 2 (PR-5 iter-1+2) + 2 (PR-6 iter-1+2)
- Architect: 2 (PR-5 + PR-6)

## Wins

### W-1 — Wrapper pattern (D27 ext) cero deuda escalable
- 3 wiring points (1 per módulo) en lugar de parchar 18 callsites individuales
- Callsite nuevo se gates auto al pasar por el factory
- Match patrón sales_agent (ConversationPipeline DI) + copilot (build_deep_agent_graph DI)
- Backwards-compat: budget_guard param optional (None default)

### W-2 — Single-TX launch refinada (D22 architect refinement)
- Original PR.md: insertar todas las tasks DAG en 1 TX
- Architect refinement post-audit schema vivo: solo root tasks (step_index==0); descendientes diferidos S3+ post-success handler
- Razón: lock long en Campaign row, batch INSERT más grande, fail rollback peor
- Resultado: launch < 2s p95 segment 100 leads

### W-3 — F-7 política integration tests sin mocks de service
- Continuada de PR-4 — atrapa drift real entre mocks y impl
- 29 nuevos tests F-7 en PR-6 detectaron mock/prod divergencias 0
- BudgetGuardingChatModel bucket isolation tests (SA pool exhausted no bloquea Others)

### W-4 — Architecture ratchet shrink-only allowlists
- KNOWN_UNGUARDED 5 entries (brand 3 + workers 2) shrink-only documenta deuda
- KNOWN_DIRECT_LEGACY_EMITTERS empty (seeded clean post-cutover)
- Forces explicit justification + follow-up issue para cada nueva entry

### W-5 — Architect autonomy ZERO open questions
- PR-5: 1 cosmetic Q (table singular) → architect decide default
- PR-6: 3 Qs scope/producto → PM main session resuelve sin pause
- Resultado: builder no se bloquea, sub-spawns ágiles

## Fails / Pain Points

### P-1 — Builder usage limit interrumpe mid-task
- Sub-A/B (PR-5) requirieron 2-3 spawns cada uno
- Sub-D (PR-5) requirió 5 spawns por re-spawns post-pause
- Mitigación: prompt focused per sub-deliverable + commit-or-die directive
- Sub-G fix-loop (PR-6) hecho por PM main directly sin spawn

### P-2 — Stash pop drama (Sub-C PR-6)
- Builder hizo `git stash pop` que aplicó WIP de PI-2 sesión paralela como propio
- Resultado: mis cambios deep_agent.py + chat.py se PERDIERON
- Mitigación: PM verificó git status pre-commit, identificó files M ajenos, redo wiring fresh en deep_agent.py only
- Lesson: `git stash` PROHIBIDO en sesiones paralelas — usa filesystem natural

### P-3 — Drift CONTRACT vs realidad (Sub-C PR-6)
- CONTRACT decía `provider_factory.build_chat_model()` que no existe
- Realidad: `LLMFactory.get_service().get_client(ModelRole.AGENT)` en deep_agent.py:243
- PM main resolvió drift inline pasando spec correcta a builder
- Lesson: architect debe leer schema vivo MÁS profundo antes CONTRACT (esto se hizo PR-5 well, PR-6 falló parcialmente)

### P-4 — Audit findings críticos PR-5 iter-1 (4 critical/high)
- F-1 LeadQueryServiceImpl import path inexistente (4 sitios)
- F-2 Cross-module allowlist no agregada
- F-3 Migration fork (multiple heads)
- F-4 Test legacy STUB notice no actualizado
- Mitigación: Sub-G fix-loop builder shipped en 1 spawn — todos resueltos
- Lesson: builder spawn debe correr `pytest tests/architecture/` antes commit (no solo module tests)

### P-5 — Mypy strict scope confunde
- Application layer NO checked por mypy (solo domain) → builders pueden dejar issues sin notar
- Lesson: explicar scope en builder prompt + reference pyproject.toml mypy.overrides
- Future: ratchet expand mypy a application layers gradual

## Decisiones que vale revisar

| Decisión | Resultado | Cambio futuro? |
|---|---|---|
| D26 cutover secuencial vs paralelo | OK rollback simple | mantener |
| D27 ext wrapper pattern (3 puntos vs 18 callsites) | OK escalable | mantener — patrón generalizado |
| D29 brand BudgetGuard DEFERRED DR-7 | OK con allowlist documented | Sub-D-2 / S3 sí ejecutar — no más deferral |
| Sub-deliverables sub-A through sub-F estructura | OK ágil | mantener — facilita re-spawn focused |
| Mypy strict scope domain only | mediocre — application errors invisibles | considerar expand application gradualmente |

## Recomendaciones próximos sprints

### R-1 — Spawn builder en sub-deliverables atomic
- Cada sub-spawn = 1 commit + 1 push obligatorio
- Pre-commit hooks corren native — fix root cause si fallan
- NO permitir builder pause sin commit (commit-or-die directive)

### R-2 — Architect schema live audit OBLIGATORIO antes CONTRACT
- Lectura schema vivo SQLA + repos + services PRE-CONTRACT
- Drift catched early evita re-work builder mid-task
- PR-5 lo hizo bien, PR-6 falló parcial — formalizar checklist architect

### R-3 — Ratchet allowlist documenta cada DR
- Cada DR-N flagged en IMPL-LOG → entry en KNOWN_* allowlist correspondiente
- Comment en allowlist: "DR-N TODO sprint destino"
- Auditor verifica DR ≤ N en allowlist

### R-4 — F-7 política mantener
- 1 integration test sin mocks de service por feature crítica
- Mock solo en boundary (HTTP, DB, redis client)
- Detecta mock/prod divergence

### R-5 — Stash PROHIBIDO en sesiones paralelas
- Filesystem natural ya da sync
- Stash + pop = riesgo perder WIP otra sesión
- Si necesitás backup → commit + revert/cherry-pick controlado

## Skills usados S2

- `nicolify-architect` — CONTRACTs PR-5 + PR-6 (1387 + 750 LOC)
- `nicolify-backend` — implementation (15+ sub-spawns)
- `nicolify-backend-auditor` — REVIEWs (4 iter)
- `tessl__graceful-degradation` — CB iron rules + timeout/fallback
- `tessl__pytest-api-testing` — ARQ ctx fixture + httpx mock
- `backend-expert` — DDD + Pydantic v2 + arch-fitness ratchet
- `sales-agent-expert` — invariante pool + voz brand
- `copilot-expert` — LLM call sites + cost cycle

## Próximo sprint

S3-mvp-telegram. Foco: OutboundOrchestrator + AgentState campaign_id + supervisor routing + bridge campaigns→sales_agent + inbound reply recognition + Inbox UI tag + campaign analytics + E2E real Telegram messages.

S3 cierra cuando MVP 1 Telegram funcional end-to-end visible (Chris envía 5+ contactos reales). Posterior: PI-1 cierra completo.
