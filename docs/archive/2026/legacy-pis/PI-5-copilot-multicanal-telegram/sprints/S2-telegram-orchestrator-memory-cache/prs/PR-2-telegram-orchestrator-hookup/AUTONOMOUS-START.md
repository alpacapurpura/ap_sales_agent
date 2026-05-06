# PR-2 — Autonomous start prompt (paste en nueva conversación)

> Pegá el bloque de abajo TAL CUAL en una conversación nueva. Activa modo autónomo: Opus 4.7 toma todas las decisiones técnicas, solo te pregunta lo que de verdad necesita decisión de dueño.

---

## Prompt (paste literal)

```
/pm

Estoy retomando PI-5-copilot-multicanal-telegram en sprint S2. PR-2-telegram-orchestrator-hookup está skeleton-ready (commit 99aaad32 en development). Webhook dev ya configurado y vivo: https://dev-api.nicolify.com/api/v1/copilot/telegram/webhook → @nicolify_dev_bot. Tokens en .env (gitignored).

Quiero que ejecutes PR-2 end-to-end EN MODO AUTÓNOMO hasta dejarlo shipped + RESULT.md cerrado. Tu rol: orquestador. No me pidas decisiones técnicas — esas las tomas vos como Opus 4.7 con criterio scale-first (1000+ tenants) y early-stage (cambiar ahora es más barato que después).

──────────────────────────────────────────────────────
PRINCIPIOS NO NEGOCIABLES (mind-set permanente)
──────────────────────────────────────────────────────

1. Scale-first siempre. Cada decisión la justificás contra "¿esto escala a 1000+ tenants?". Cache hit rate, índices DB, statelessness workers, locks granularidad, queue throughput.

2. Early-stage = libertad refactor. No metas backwards-compat shims si no hay caller real que los necesite. No metas defaults "por si acaso". Si algo está mal nombrado o ubicado, renombrá. Cero deuda técnica gratuita.

3. EXTEND no NEW. Antes de crear un módulo/clase/función nueva, grep el codebase. Si existe algo con ≥80% overlap, extendelo. La regla NO-NEW-LAYER es ley (origen: PR-3 PI-2 audit failure 2026-04-30).

4. Cache prefix discipline. El BLOQUE FIJO de los prompts se mantiene byte-idéntico entre iteraciones del fix-loop. Cero timestamps/hashes/conversation_id/tenant_name interpolado mid-block.

5. Anti-hallucination. Antes de citar un path/función, verificalo con grep o read. Si dudas, leelo.

6. Defer agresivo. HITL → S3. Push notifs → S4. Multi-role filter → PI futuro. Vector retrieval → post-launch. Voice messages → PI futuro. Si algo cae fuera del scope explícito de PR-2, NO LO HAGAS.

──────────────────────────────────────────────────────
WORKFLOW AUTÓNOMO (ejecutá en orden, sin parar)
──────────────────────────────────────────────────────

Paso 1 — Bootstrap PM
- Leé docs/pm-nico/INDEX.md + roadmap.md
- Leé docs/pm-nico/pis/active/PI-5-copilot-multicanal-telegram/sprints/S2-telegram-orchestrator-memory-cache/prs/PR-2-telegram-orchestrator-hookup/PR.md (scope completo)
- Confirmá git status limpio en development. Si tree sucio con archivos ajenos → reportá pero NO pares (otra sesión paralela). Si tree sucio con archivos propios pendientes → STOP, preguntáme.

Paso 2 — Pre-flight Haiku (context-builder)
- Spawn nicolify-context-builder (Haiku 4.5) con el prompt de prompts/00-context-prep.md
- Esperá CONTEXT-BRIEF.md
- Si § 11 Faithfulness flag != "clean" → spawn de nuevo con prompt corregido (NO leas el repo entero vos)

Paso 3 — Architect (Opus 4.7)
- Spawn nicolify-architect (Opus) con el prompt de prompts/01-architect-start.md
- Esperá CONTRACT.md
- Si CONTRACT § 16 Open questions tiene preguntas marcadas como "PM owner decision" → traémelas. Si son "technical" → vos resolvelas y reescribilas vos en CONTRACT (con tu criterio scale-first/early-stage).
- Si Architect detecta que el problema requiere cambio de scope → traémelo con propuesta concreta. NO improvises scope expansion.

Paso 4 — Builder + auto-audit (Opus 4.7 agentic)
- Spawn nicolify-agentic (Opus) con el prompt de prompts/02-builder-start.md
- El builder ejecuta TDD + quality gates locales NATIVE WSL + auto-spawnea gate-runner Haiku + auto-spawnea nicolify-agentic-auditor Opus + auto-fix loop max 3 iter
- Si builder retorna PASS → Paso 5
- Si builder retorna escalado a PM tras 3 iter → leé los findings, decidí: A) update CONTRACT (drift legítimo) y re-spawn builder, B) escalar a Chris (solo si decisión owner-level), C) cambiar approach técnico vos
- Si Opus agent paused/killed mid-task → resume (SendMessage agentId) o re-spawn Opus mismo tipo. NUNCA degradar a Sonnet/Haiku para "ahorrar". NUNCA hacerte el auditor vos.

Paso 5 — Cerrar PR-2
- Leé IMPL-LOG.md + REVIEW-agentic.md + git log
- Validá ambos: verdict PASS + cero cambios FE en diff + cero cambios módulos negocio + cero migration nueva
- Escribí RESULT.md (outcome real medido vs esperado, surface, capacidades nuevas con lineage commit hash, decisiones implementación, métricas, deuda)
- Update docs/pm-nico/current-state/copilot.md: capability "Canal Telegram — DMs linkeados" upgraded de "parcial (placeholder)" → "live (orchestrator real + memory cost-aware + cache fragment ≥1024)"
- Append D-PI5-IMPL-007+ a decisions.md (EXTEND vs NEW resoluciones, signature changes, format adapter reuse, lookup concurrency)
- Append learnings PR-2 a sprints/S2-*/learnings.md
- Cambiá Estado: shipped en PR.md
- PR-2 = único PR S2 → llená sprints/S2-*/handoff.md con decisiones consolidadas para S3 (HITL escalation patterns + surface live)
- Git: stage por nombre, commit conventional `feat(copilot): PR-2 telegram orchestrator hookup + memory + cache + tool filter (PI-5 S2)`, push origin development

Paso 6 — Smoke test live
- Yo (Chris) tengo @nicolify_dev_bot ya configurado con webhook
- Pediéme que abra Telegram, escriba al bot un mensaje cualquiera SIN linkear → confirmá que recibo CTA template friendly con URL https://app.nicolify.com/.../settings/copilot/telegram (no el placeholder "recibí tu mensaje")
- Si quiero probar el flow linked: te aviso, generamos magic link desde web, /start TOKEN, mensaje, respuesta orchestrator real
- Si fallás algo en live → leé docker logs visionarias_brain_dev + copilot_trace_event en DB

Paso 7 — Reportá brief (<300 palabras)
- Qué shipped + métricas tests + iter gate-runner + iter audit + cache hit rate medido si pudiste instrumentar
- Acción Chris siguiente: ¿arrancamos S3 (HITL) o pausa para feedback live?

──────────────────────────────────────────────────────
DECISIONES QUE TOMA OPUS 4.7 SOLO (NO ME PREGUNTES)
──────────────────────────────────────────────────────

Técnicas — todas:
- Library choices (¿tiktoken vs anthropic.count_tokens? Lo que uses, justificalo en IMPL-LOG)
- Signature design (param channel default 'web' es la regla, ya está en PR.md)
- Cache fragment content composition (debe sumar ≥1024 tokens stable bytes — el contenido lo elegís vos, p.ej. "channel constraints + tool subset summary + format hint")
- Test strategy + mock patterns (pytest-asyncio + AsyncMock para bot/ARQ; rolled-back AsyncSession para DB)
- Conversation lookup concurrency (UNIQUE + ON CONFLICT vs SELECT FOR UPDATE — escalá UNIQUE+ON CONFLICT por simplicidad si tabla tiene UNIQUE constraint adecuada)
- Memory config inyección (constructor param vs lookup interno — preferí constructor param para testabilidad)
- Format adapter design (helper en application/tools/ vs reuse directo — preferí pequeño wrapper que internamente llame escape_markdown_v2)
- Naming, file locations, imports
- Refactor existentes si están mal (SIN expandir scope — solo lo del path PR-2)
- Skip features fuera de scope explícito

Métodológicas:
- Cuándo correr tests, cuántos casos por test, qué fixtures usar
- Si un finding del auditor es addressable o es escalate
- Cuándo iterar fix-loop vs cuándo escalate
- Cuándo restart container vs cuándo no

──────────────────────────────────────────────────────
DECISIONES QUE ME PREGUNTÁS (OWNER LEVEL)
──────────────────────────────────────────────────────

Solo estas — todas las demás las tomás vos:

1. SCOPE CHANGE — Si descubrís que PR-2 requiere tocar algo fuera de modules/copilot/ (cualquier otro módulo, FE, DB schema, sales_agent), pará y preguntáme. Si requiere expandir scope dentro copilot pero más allá de los 7 deliverables del walking skeleton, también pará.

2. COST TRADE-OFF >10x — Si una decisión técnica afecta costo Anthropic >10x baseline (ej: cache fragment design fuerza re-write cache cada turno) → mostrame opciones cuantificadas.

3. USER-FACING COPY — Cualquier texto que el dueño VEA en Telegram (welcome message del bot, CTA template "lo vemos en web", redirect template tools no disponibles, error messages friendly). Mostrame draft + versión alternativa, yo elijo. Lenguaje neutro LatAm tuteo (sin voseo) — eso ya está en rules/spanish-text.md, lo respetás vos.

4. BOT IDENTITY CHANGE — Si por alguna razón cambiás username, behavior, persona del bot.

5. AUDITOR ESCALATE TRAS 3 ITER — Si el auditor sigue marcando FAIL/WARN tras 3 iteraciones de fix-loop con findings que NO son drift contractual claro.

6. DECISIÓN QUE AFECTE MULTI-TENANT EN UN MISMO CHAT_ID — Hoy decidimos "1 chat_id → 1 tenant, edge case multi → necesita 2 cuentas Telegram" (D-PI5-016). Si en code path discoverás que NO podemos sostener esa decisión (ej: el lookup ambiguo crashea), traémelo.

──────────────────────────────────────────────────────
ESTADO ACTUAL VERIFICADO 2026-04-30 22:50 UTC-5
──────────────────────────────────────────────────────

- Branch: development (commit 99aaad32 PR-2 skeleton pushed)
- Bot @nicolify_dev_bot live, getMe OK (id 8641106116)
- Bot @nicolify_bot prod token cargado en .env.prod (NO setWebhook aún — post-prod-deploy)
- Webhook dev: https://dev-api.nicolify.com/api/v1/copilot/telegram/webhook configurado en Telegram con secret_token + max_connections=40 + allowed_updates=["message"]. Verificado vía getWebhookInfo
- Webhook secret token enforcement: verificado (401 con secret incorrecto, 200 con correcto, 422 con body inválido)
- Brain container visionarias_brain_dev recreated con env nuevo. Health 200. Env vars cargadas: COPILOT_TELEGRAM_BOT_USERNAME=nicolify_dev_bot, COPILOT_TELEGRAM_LINK_TOKEN_TTL_SECONDS=900
- LiteLLM container con mount issue WSL2 pre-existente (no bloquea brain — usar `docker compose up -d --no-deps api_dev` si necesitás recrear)
- PR-1 capability live: /api/v1/copilot/telegram/{webhook,link-tokens,link-status,link} + tablas copilot_channel_links + copilot_link_tokens + cols channel_type/channel_chat_id en copilot_conversations + FE /settings/copilot/telegram page + tool subset SSoT
- Worker linked branch HOY: responde placeholder fijo "recibí tu mensaje desde Telegram" — ESTO ES LO QUE PR-2 REEMPLAZA con orchestrator real

──────────────────────────────────────────────────────
ARRANCÁ
──────────────────────────────────────────────────────

Empezá Paso 1 ya. No me pidas confirmación para arrancar — la confirmación es esta misma instrucción. Reportame solo cuando llegues a Paso 7 o si chocás con algo de la lista "owner level" arriba.
```

---

## Notas de uso

- Pegá el bloque entre triple-backticks SIN los backticks (es un markdown wrapper). El contenido del prompt va desde "/pm\n\n" hasta "Empezá Paso 1 ya..."
- La conversación nueva debería ejecutar autónomamente. Tu intervención humana esperada: solo Paso 6 (smoke test) + Paso 7 (recibís brief).
- Si en una conversación nueva el sistema no carga `/pm` skill automáticamente, escribí `/pm` solo, esperá load, después pegás el resto.
- Si alguna fase tarda mucho (ej. builder >10 min sin avance), abrí monitor o terminal y mirá `docker logs visionarias_brain_dev --tail 50` o `git log --oneline -5` para ver progreso.
