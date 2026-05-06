# Sprint S1 — Learnings

> Append-only durante sprint. Congela al cerrar.

## Funcionó

| Patrón | Aplicación | Beneficio |
|---|---|---|
| **Reuso `escape_markdown_v2` + `sanitize_payload` desde `shared/`** | Bot adapter + webhook handler | Cero duplicación, alineado con D-PI5-005 (no shared state vs sales_agent) |
| **EXTEND patrón existente (ARQ stack, ToolRegistry, ConversationModel, Settings)** | 5 EXTEND vs 8 NEW resoluciones (60/40 split) | NO-NEW-LAYER rule respetada. Backward compat sin breaking |
| **Idempotent migration raw SQL** (CREATE/ALTER IF NOT EXISTS) | Migration 120 | Aplicable manual cuando alembic head bloqueado por migration 114 pre-existing |
| **State machine "linked DERIVED from queries"** (no setState-in-effect) | TelegramLinkingClient | Pasa lint react-compiler estricto sin disable comments. Cleaner mental model |
| **HMAC-SHA256 con `API_SECRET_KEY` reuse** | telegram_link_service | Cero secret nuevo en Settings, reuse infraestructura existente |
| **CONTEXT-BRIEF inline cuando Haiku timeout** | PR-1 architect phase | PM main thread escribió brief en 1 turno con greps directos. Lección: si Haiku falla, PM Opus puede self-serve duplicate detection scan |

## NO funcionó (anti-patterns observados)

| Pattern | Detalle | Mitigación futura |
|---|---|---|
| **Spawn subagentes Sonnet/Opus con prompts >100k input** | Architect agent timeout @30 tool calls / 6.7 min sin escribir CONTRACT.md final | Single-author single-pass desde PM main thread es más confiable para PR L. Spawn agentes solo cuando scope encaja en sub-15-min ejecuciones |
| **Migration alembic head bloqueado** | Migration 114 (pre-existing PR-3 PI-2) tenía bug `raw_payload NOT NULL` que rompe `alembic upgrade head` | PR-1 idempotente raw SQL aplicado manual via psql. Fix migration 114 = separate ticket, NO bloquea PR-1 ship |
| **Eslint react-compiler `set-state-in-effect`** | Disable comments NO suprimen el rule en este lint config | Refactor a derived state computation (resolveLinkedView pattern) — más limpio que disable |

## Surprises

- **Telegram chat_id immutability**: research file enfatizó `from_user.id` (numeric) como identity inmutable; `username` mutable. Schema diseñado correctamente desde día 1 — auditor catch rápido si futuro PR usa username como FK
- **Cache prefix Anthropic 1024 tokens umbral**: Telegram system prompt SIN `studio_snapshot`/`form_data` cae bajo umbral → `TELEGRAM_CHANNEL_CONTEXT` fragment necesario en S2 PR-2 para mantener cache hit rate
- **ARQ pool puede ser None en test/dev sin Redis**: graceful degradation pattern (return 200 silencioso si pool None) evita 500s en tests. Discovered durante FastAPI app boot test
- **Migration auto-apply pattern**: cuando alembic stuck, scripts SQL idempotentes son rescue value. Lección: TODA migration nueva debe ser idempotente raw SQL (rule `backend-migrations.md`) — habilita rescue manual

## Process learnings (NO append `process-learnings.md` aún — esperar PI close para consolidar)

- **L-PROC-PR-AGENT-TRUNCATE-PI5-PR1**: Architect/builder spawn agents para PR L+ scope tienden a truncar sin escribir output. PM main thread takeover más confiable. Confirmado patrón pre-existente PI-2 (4 truncates documentados en retro). PI-5 PR-1 = 5° confirmation.
- **L-PROC-CONTEXT-BUILDER-FALLBACK**: Si Haiku context-builder timeout, PM main thread puede self-serve §7+§8 duplicate detection scan en ~10 greps. Tiempo elapsed similar (~5 min PM vs 5 min Haiku roundtrip), confiabilidad mayor.

## Métricas Sprint S1

| Métrica | Valor |
|---|---|
| PRs en sprint | 1 (PR-1) |
| PRs shipped | 1 (100%) |
| PRs sin auto-audit loop | 1 (single-pass single-author PM main thread) |
| Tests new | 29 (8 arch + 21 unit) |
| Tests pass | 29/29 |
| Files surface | 27 BE+FE + 4 tests = 31 cambios |
| Insertions | +2313 / -7 |
| Sprint duration | ~4 horas (research + architect + impl + close) |
| Decisiones D-PI5-* totales | 31 (research) + 6 (impl) = 37 |
