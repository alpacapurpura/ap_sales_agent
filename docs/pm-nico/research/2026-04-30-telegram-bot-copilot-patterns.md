# Telegram Bot Copilot — Patterns Research

**Fecha:** 2026-04-30
**PI target:** PI-5 — Copilot Multicanal Telegram
**Autor:** Research agent (CTO/PM frame)
**Scope:** Decisiones de arquitectura pre-PI-5 sprint 1. Responde las 7 secciones de investigación solicitadas. Consultar este doc antes de abrir PRs.

---

## Sección 1 — Conversation Memory Pattern para Telegram Bot LLM

### Contexto Nicolify actual

El copilot web ya tiene implementado en `copilot/application/memory/`:
- `ContextWindowBuilder` — ventana deslizante `RAW_WINDOW_TOKENS=2000`, `RAW_WINDOW_MAX_MESSAGES=10`, `RAW_WINDOW_MIN_MESSAGES=4`
- `RollingSummarizer` — comprime mensajes desplazados via `ModelRole.NANO`, `SUMMARY_MAX_CHARS=400`
- `CopilotConversationModel` — columnas `messages` (JSONB), `summary` (Text), `total_tokens` (int)

Estrategia actual = **Hybrid (rolling summary + sliding window)**. Exactamente el patrón más maduro de la industria.

### Comparativa de patrones

| Patrón | Cómo funciona | Cost / Quality | Complejidad | Aplica Telegram |
|--------|---------------|----------------|-------------|-----------------|
| **Sliding window** (last N msgs) | Descarta todo antes de N | Bajo costo, pierde contexto >N | Mínima | Solo si N≥20 conversaciones cortas |
| **Rolling summary** (LangChain ConversationSummaryBufferMemory) | LLM comprime mensajes viejos en summary. Recientes en raw. | Costo moderado (1 call extra al desplazar), buena retención semántica | Media | Sí, es lo que Nicolify ya tiene |
| **Episodic memory + vector retrieval** (Qdrant) | Embeds cada turno. Retrieval semántico relevante. | Alto costo (embed + query por turno), calidad excelente para Q&A retrospectivo | Alta | No MVP — overkill para 1:1 Telegram |
| **Hybrid: recent N raw + summary old + vector retrieval** | Los 3 anteriores combinados | Costo más alto pero máxima calidad | Alta | Tier 2 post-MVP |

### Prompt caching implications (Anthropic)

Nicolify usa LiteLLM Proxy + Anthropic. Sistema prompt layout en `system_prompt_layout.py`:
- Fragmentos cacheable (`STATIC_IDENTITY`, `LIGHTHOUSE`, `MODULES_LIST`) = prefijo estable ≥1024 tokens
- Cache boundary explícito `CACHE_BOUNDARY_MARKER`
- Fragmentos volátiles (`STUDIO_SNAPSHOT`, `WORKFLOW_STATE`) = post-boundary

Para Telegram:
- **El sistema prompt del copilot Telegram será MÁS CORTO** que en web (no hay studio snapshot, no hay selected_fields, no hay form_data)
- Riesgo: prefijo cacheable puede caer BAJO 1024 tokens en Telegram context → no activa cache
- Mitigación: añadir fragmento `CHANNEL_CONTEXT` en la sección cacheable con metadata del canal, o un `TELEGRAM_BEHAVIOR_HINT` suficientemente largo para llegar al umbral

Pricing implication (Anthropic prompt caching 2025-2026):
- Cache write: ~25% extra costo de input tokens
- Cache read: ~10% del costo normal de input
- Break-even: si misma conversación tiene ≥3 turns con prefijo idéntico → ahorro neto desde el 3er turn
- Para Telegram: dueño que escribe 5+ msgs seguidos → sí conviene. Para alerts esporádicas → write+read single use → no ahorra.

### Recomendación para Telegram

**Usar el mismo patrón Hybrid existente** (`ContextWindowBuilder` + `RollingSummarizer`) pero con un perfil de config distinto:

```python
TELEGRAM_CONTEXT_WINDOW_CONFIG = ContextWindowConfig(
    RAW_WINDOW_TOKENS=3000,          # más tokens raw (Telegram es asíncrono, gaps mayores)
    RAW_WINDOW_MAX_MESSAGES=15,      # 15 msgs raw antes de comprimir
    RAW_WINDOW_MIN_MESSAGES=4,       # igual que web
    SUMMARY_MAX_CHARS=600,           # summary más largo (cubrir días de contexto)
    SUMMARY_TARGET_TOKENS=200,       # ~150% del web (contexto más disperso en el tiempo)
    NUDGE_AFTER_TOTAL_TOKENS=12000,  # más permisivo (Telegram = sesiones más cortas por turn)
    NUDGE_HARD_LIMIT_TOKENS=20000,
    NUDGE_AFTER_MESSAGE_COUNT=20,
)
```

Reutilizar `CopilotConversationModel` — añadir columna `channel_type` + `channel_chat_id` para identificar conversación Telegram (ver Sección 3). NO crear tabla separada de conversaciones Telegram — misma tabla, distinto `channel_type`.

**No implementar vector retrieval en MVP** — la conversación del copilot Telegram es lineal (el dueño no busca contexto viejo, sólo da instrucciones). Guardar como evolución futura si el dueño reporta "no me recuerda lo que le dije la semana pasada".

---

## Sección 2 — HITL (Human In The Middle Loop)

### Estado actual sales_agent

El escalation en sales_agent hoy es **fire-and-forget** — `node_escalation` emite mensaje empático al lead y va a `END`. El dueño ve la conversación en Closer Studio (web). No hay notificación activa al dueño.

Archivo clave: `sales_agent/application/agents/sales/nodes.py:337`, `tools.py:86`.

### Pattern industria

| Plataforma | Pattern handoff | Latencia aceptada |
|------------|----------------|-------------------|
| Intercom | Assign to inbox → notif push app | 0-30 min |
| Front | Bot pauses → alert email/slack → human resumes thread | 5-60 min |
| Crisp | Bot flag → operator notified → same thread continúa | 0-5 min idealmente |
| LangGraph canonical | `interrupt()` en nodo → checkpointer guarda state → resume con `Command(resume=value)` | Depende del canal notificación |

**LangGraph `interrupt()` pattern** (fuente: LangGraph docs v0.2+):
```python
# En nodo que necesita decisión humana:
value = interrupt("¿Apruebas precio override de $X?")
# Graph se pausa, state persiste en checkpointer
# Al recibir respuesta:
graph.invoke(Command(resume=owner_response), config=thread_config)
```

### Diseño state machine para Nicolify

```
sales_agent_graph
    └── node_escalation
           ├── ACTUAL: emit msg → END (pierde lead mientras)
           └── NUEVO (HITL):
                ├── emit msg al lead ("Dame un momento")
                ├── crear HITLRequest en DB (tenant_id, lead_id, pregunta, timeout, created_at)
                ├── publicar evento CopilotHITLRequestCreated
                ├── interrupt() → graph se pausa (checkpointer: AgentStateCheckpointModel ya existe)
                └── WAIT...

copilot_telegram_bot
    └── recibe CopilotHITLRequestCreated
           ├── formatea mensaje al dueño: "Tu agente necesita decidir: [pregunta]. /si / /no / texto libre"
           ├── dueño responde
           └── publica HITLResponse(request_id, respuesta)

sales_agent_resume_worker
    └── consume HITLResponse
           ├── graph.invoke(Command(resume=respuesta), config=thread_config)
           └── sales_agent continúa con instrucción inyectada
```

### Tablas DB necesarias

```sql
CREATE TABLE IF NOT EXISTS hitl_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    sales_agent_thread_id TEXT NOT NULL,  -- LangGraph thread_id del checkpointer
    question TEXT NOT NULL,
    context JSONB,                         -- datos del lead para contexto al dueño
    status TEXT DEFAULT 'pending',         -- pending | responded | timed_out | cancelled
    response TEXT,
    responded_by UUID,                     -- copilot user_id (tenant owner)
    created_at TIMESTAMPTZ DEFAULT now(),
    responded_at TIMESTAMPTZ,
    timeout_at TIMESTAMPTZ NOT NULL        -- created_at + config timeout
);
CREATE INDEX IF NOT EXISTS idx_hitl_requests_tenant_pending 
    ON hitl_requests(tenant_id, status) WHERE status = 'pending';
```

### Latency expectations

| Escenario | Latencia aceptable | Comportamiento timeout |
|-----------|-------------------|------------------------|
| Lead en conversación activa (respondiendo activamente) | 3-10 min | Sales_agent responde con su mejor criterio |
| Lead frío (último msg hace horas) | 30-120 min | Sales_agent responde con su mejor criterio |
| Lead de alto ticket (>$1000 USD) | 15-30 min | Sales_agent pausa hasta 60 min, luego "revisamos contigo mañana" |

**Timeout default recomendado: 15 minutos.** Post-timeout el sales_agent procede con `decision_fallback` configurable por tenant (campo en `personality_profiles`).

Timeout handling:
```python
# Worker que corre cada 5 min (ARQ)
async def process_hitl_timeouts():
    expired = db.query(HITLRequest).filter(
        HITLRequest.status == "pending",
        HITLRequest.timeout_at < utc_now()
    ).all()
    for req in expired:
        req.status = "timed_out"
        # resume con fallback decision
        graph.invoke(Command(resume="TIMEOUT_FALLBACK"), config=...)
```

---

## Sección 3 — Multi-user Roles Arquitectura

### Schema `copilot_channel_links`

```sql
CREATE TABLE IF NOT EXISTS copilot_channel_links (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id),
    user_id UUID NOT NULL REFERENCES users(id),        -- Clerk user_id (copilot user)
    channel_type TEXT NOT NULL,                         -- 'telegram', 'whatsapp', futuro
    channel_user_id TEXT NOT NULL,                     -- Telegram from_user.id (numérico como string)
    channel_username TEXT,                              -- @username (MUTABLE — no usar como PK)
    role TEXT NOT NULL DEFAULT 'owner',                -- 'owner' | 'assistant' | 'finance_admin' | 'marketing_lead'
    linked_at TIMESTAMPTZ DEFAULT now(),
    last_seen_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,                             -- soft delete
    UNIQUE(tenant_id, channel_type, channel_user_id)   -- 1 chat_id = 1 rol por tenant
);
CREATE INDEX IF NOT EXISTS idx_channel_links_lookup 
    ON copilot_channel_links(channel_type, channel_user_id) 
    WHERE revoked_at IS NULL;
```

**Crítico:** `channel_user_id` = `from_user.id` (número) de Telegram — permanente. `channel_username` = `@handle` — mutable, solo display. NUNCA usar `username` como identity key.

### Permisos por rol (MVP → target)

| Rol | Tools disponibles | Herramientas bloqueadas |
|-----|-------------------|------------------------|
| `owner` | Todas (full copilot) | Ninguna |
| `assistant` | CRM, sales_agent consulta, scheduling | Mutations brand/offer, billing, connections |
| `finance_admin` | Analytics, billing, CRM read | Sales_agent mutations, brand, offer |
| `marketing_lead` | Analytics, brand read, offer read, social_media | Sales_agent, billing, CRM sensible |

Implementación: en `ToolRegistry.get_tools_for_context()` añadir `user_role` al `CopilotContext`. La resolución de herramientas filtra por `available_roles: list[str]` en metadata del tool group (ver Sección 5).

**MVP: solo `owner`.** Schema preparado para más roles desde día 1 (la tabla lo soporta).

### Pattern industria multi-user workspace

**Slack bot:** Cada user tiene su propio DM con el bot, mismo workspace. Permisos inferidos de Slack roles.
**Linear:** Menciones @bot en comentarios — bot identifica usuario desde mention metadata.

Para Nicolify: cada `from_user.id` hace lookup a `copilot_channel_links` para resolver `(tenant_id, user_id, role)`. Un mismo `chat_id` no puede pertenecer a dos tenants distintos (UNIQUE constraint). Si un dueño maneja 2 negocios en Nicolify → necesita 2 bots (edge case futuro).

---

## Sección 4 — Open vs Closed Bot, Magic Link Onboarding

### Decisión confirmada

Bot "open + auth in-message" — cualquiera puede escribir al bot global `@nicolify_copilot_bot`. Sin link activo el bot responde con instrucción de onboarding.

### Magic link / Deep link Telegram pattern

Telegram deep link format: `https://t.me/{botusername}?start={TOKEN}`

Cuando user hace click → Telegram abre el bot y envía automáticamente `/start TOKEN` como primer mensaje.

**Token security best practices:**

| Propiedad | Especificación |
|-----------|---------------|
| Generación | `secrets.token_urlsafe(32)` (Python) — 256 bits entropy |
| TTL | 15 minutos (suficiente para flujo in-app → open Telegram) |
| Single-use | Marcar `used_at` al validar. Segundo uso = error. |
| Signing | HMAC-SHA256 con `SECRET_KEY` del app (no solo UUID) — previene forge |
| Storage | `copilot_link_tokens(token_hash, tenant_id, user_id, expires_at, used_at)` — almacenar HASH no plaintext |

**UX flow recomendado:**

```
1. In-app (web):
   Usuario va a Settings → Copilot → Conectar Telegram
   → API genera token HMAC, guarda hash en DB, devuelve deep link URL

2. In-app modal:
   "Conecta tu Telegram para acceder al copilot desde cualquier lugar"
   [ Abrir Telegram ] → href="https://t.me/nicolify_copilot_bot?start=<TOKEN>"

3. Telegram:
   Bot recibe /start <TOKEN>
   → Bot valida token (lookup hash + TTL + unused)
   → Si válido: guarda copilot_channel_link(tenant_id, user_id, chat_id)
   → Bot responde: "Listo. Ya puedes usar el copilot desde Telegram."

4. In-app (polling):
   FE hace polling /api/v1/copilot/telegram-link-status?token_id=X cada 3s por 60s
   → Cuando DB muestra linked_at → FE muestra "Conectado" + dismiss modal
   → Alternatively: WebSocket notification
```

**No auth in-message UX (bot sin link):**
```
Usuario: "hola"
Bot: "Hola. Para usar el copilot de Nicolify, conéctate primero desde tu cuenta:
app.nicolify.com → Configuración → Copilot → Conectar Telegram
El proceso toma 30 segundos."
```

**Anti-pattern:** no pedir email/password en el bot — viola ToS Telegram + UX terrible.

---

## Sección 5 — Subset Tools "telegram-allowed" vs "web-only"

### Eje de canal en tool registry existente

El `registry.py` actual usa `ROUTE_TOOL_MAP` (route → groups) y `ALWAYS_AVAILABLE_GROUPS`. Para Telegram se necesita un segundo eje: channel.

**Diseño propuesto: metadata field `available_channels` en tool group definition:**

```python
# En ToolGroupMetadata (nuevo dataclass en domain/ports.py o nuevo archivo)
@dataclass(frozen=True, slots=True)
class ToolGroupMeta:
    name: str
    available_channels: frozenset[str] = frozenset({"web", "telegram", "whatsapp"})
    # default = todos los canales; restricción = especificar subset

# Registry map:
TOOL_GROUP_META: dict[str, ToolGroupMeta] = {
    "navigation": ToolGroupMeta("navigation", available_channels=frozenset({"web"})),  # web-only: navega SPA
    "mutation": ToolGroupMeta("mutation", available_channels=frozenset({"web", "telegram"})),
    "analytics": ToolGroupMeta("analytics", available_channels=frozenset({"web", "telegram"})),
    "crm": ToolGroupMeta("crm", available_channels=frozenset({"web", "telegram"})),
    "guided": ToolGroupMeta("guided", available_channels=frozenset({"web"})),  # web-only: wizard complejo
    "extraction": ToolGroupMeta("extraction", available_channels=frozenset({"web", "telegram"})),  # URL scraping OK
    ...
}
```

`get_tools_for_route()` acepta `channel: str = "web"` → filtra tools por `available_channels`.

### Clasificación tools web vs telegram

| Group / Tool | Telegram | Razón |
|--------------|----------|-------|
| `navigation` | NO | Navega SPA Next.js — irrelevante en bot |
| `awareness` | Sí | Lee módulos del tenant — útil para consultas |
| `mutation` | Parcial | Solo mutations simples (toggle, approve) — no forms complejos |
| `analytics` | Sí | Consultar métricas → texto plano o tabla |
| `crm` | Sí | Consultar leads, estado funnel |
| `sales_agent` | Sí | Ajustar parámetros, ver pipeline |
| `guided` (wizard) | NO | Wizard multi-paso requiere UI web |
| `extraction` | Sí | URL scraping funciona en Telegram |
| `knowledge_search` | Sí | Q&A sobre KB de marketing |
| `data_query` | Sí | ask_tenant_data sub-grafo funciona bien |
| `document` (upload) | Sí | Telegram soporta file upload nativo (20MB bots) |
| `landing` mutations | NO | Editor complejo de landing → web-only |
| `offer_section` mutations | NO | Form complejo → web-only |
| `offer_ladder` | Parcial | Consulta sí, mutations NO |
| `channel_format` | Sí | Para formatear output Telegram |
| `pin_to_memory` | Sí | Útil para guardar notas desde Telegram |

### UX para "no disponible aquí"

**Pattern correcto:**
```
Dueño: "Actualiza el color de mi landing a rojo"
Bot: "Ese ajuste requiere el editor web.
Puedo abrirte el link directo: app.nicolify.com/[tenant]/landing
¿Quieres que te lo mande?"
```

**Anti-pattern:** `"Error: tool 'landing_mutation' no disponible"` — confunde, no ayuda.

Implementación: tool wrapper `TelegramUnavailableTool` que responde con redirect amigable. El LLM recibe en su system prompt instrucción: "Si el usuario pide algo que requiere la web, usa esta respuesta template y ofrece el link directo."

### Telegram message limits (fuente: Telegram Bot API docs)

| Límite | Valor |
|--------|-------|
| Texto por mensaje | 4096 chars |
| Caption (foto/video) | 1024 chars |
| Inline keyboard buttons | Máx 8 botones por fila, 100 botones total |
| Callback data per button | 64 bytes |
| File upload (bot → user) | 50 MB |
| File upload (user → bot, recibido) | 20 MB (bots) |
| Mensajes editables | Solo si tiene `message_id` y < 48h |
| MarkdownV2 chars especiales | `_*[]()~\`>#+-=|{}.!` deben escaparse con `\` |

`escape_markdown_v2()` ya está implementado en `shared/agent_observability/channels/format.py` — reutilizar.

---

## Sección 6 — Escalabilidad 1000 Tenants

### Telegram Bot API rate limits

| Límite | Valor |
|--------|-------|
| Mensajes enviados (global, 1 bot) | 30 msg/segundo |
| Mensajes al mismo chat | 1 msg/segundo |
| Notificaciones en grupos | 20 msg/minuto por grupo |
| Webhook updates recibidos | No límite oficial en bot side |
| setWebhook max connections | 1-100 (default 40) |

Con 1000 tenants y 1 bot global copilot:
- Si cada tenant envía 1 msg/segundo al mismo tiempo → 1000 msgs/seg entrante **al webhook** (el bot recibe todo)
- El envío de respuestas: 30 msg/seg máximo → si hay pico simultáneo, necesitamos queue
- Con `max_connections=100` en setWebhook → Telegram tiene 100 conexiones paralelas al webhook server

### Arquitectura webhook escalable

```
Telegram → POST /api/v1/copilot/telegram/webhook (1 endpoint global)
              ↓
         FastAPI handler (async, NON-BLOCKING)
              ↓
         Deserializa update → identifica chat_id → lookup tenant
              ↓
         Publica en cola ARQ/Redis: TelegramCopilotTurnJob(chat_id, tenant_id, text)
              ↓
         Return 200 OK a Telegram INMEDIATAMENTE (< 200ms)
              ↓
         ARQ workers procesan cola asíncronamente
              ↓
         Worker llama copilot orchestrator → genera respuesta
              ↓
         Llama Bot API sendMessage (con rate limit awareness)
```

**Crítico:** Telegram espera respuesta 200 en < 5 segundos o reintenta el webhook. El handler NUNCA procesa el LLM inline — solo encola.

**Long polling vs webhook:**
- Long polling: 1 proceso hace GET getUpdates en loop. Sólo funciona con 1 replica. Inviable para producción.
- Webhook: Telegram pushea updates. Funciona con múltiples réplicas + load balancer. **Ganador claro para producción.**

El proyecto ya tiene webhooks Telegram implementados en `connections/api/telegram.py` para sales_agent — el copilot bot reutiliza el mismo patrón.

### Rate limit handling en envío de respuestas

```python
# Worker wrapper para respetar 30 msg/sec global y 1 msg/sec per chat
class TelegramRateLimitedSender:
    _global_semaphore: asyncio.Semaphore = asyncio.Semaphore(30)   # 30/sec global
    _chat_locks: dict[str, asyncio.Lock] = {}                      # 1/sec per chat
    
    async def send(self, chat_id: str, text: str) -> None:
        chat_lock = self._chat_locks.setdefault(chat_id, asyncio.Lock())
        async with self._global_semaphore:
            async with chat_lock:
                await self._bot_api.send_message(chat_id=chat_id, text=text)
                await asyncio.sleep(1.0 / 30)  # sustain global rate
```

### File upload limits

- Bots pueden recibir archivos de hasta **20 MB** (vía `getFile` API)
- Para document tool en Telegram: el bot descarga el archivo con `file_path` → pasa a `document_processor` → mismo flujo que web
- Archivos > 20 MB: bot responde "El archivo es muy grande para procesar aquí. Sübelo desde la web."

---

## Sección 7 — Riesgos / Anti-patterns

### Lista definitiva

| # | Anti-pattern | Riesgo | Mitigación |
|---|--------------|--------|------------|
| **A1** | Per-tenant bot tokens para copilot | Cada tenant necesita su propio bot → UX pesada, gestión tokens O(N) | **1 bot global** `@nicolify_copilot_bot` con `TELEGRAM_COPILOT_BOT_TOKEN` env var. Distinto de `TELEGRAM_BOT_TOKEN` que es para sales_agent. |
| **A2** | Mezclar copilot bot con sales_agent bot | Copilot = dueño. Sales_agent = leads. Si se mezclan: dueño ve conversaciones de leads, leads ven config privada | 2 bots separados. Config distinta. CERO shared state. Namespace en Redis separado. |
| **A3** | Persistir mensajes Telegram completos sin sanitizar PII | from_user contiene `first_name`, `last_name`, `username`, `phone` (si compartido) → viola GDPR/LGPD | Sanitizar payload antes de persistir. Solo guardar `chat_id` (numérico), `text`, `message_id`. No guardar `username` en logs — solo en `copilot_channel_links`. Usar `sanitize_payload()` que ya existe en `copilot/infrastructure/prompts/sanitizer.py`. |
| **A4** | Asumir Telegram `username` == identidad permanente | Users pueden cambiar @handle. Usar como FK → datos huérfanos | Identity key = `from_user.id` (entero, inmutable). `username` = display only, guardar en campo nullable mutable. |
| **A5** | Usar `asyncio.sleep()` para rate limiting en el handler webhook | Handler bloquea → Telegram retries → cascada | Rate limiting en worker, no en handler. Handler siempre responde 200 en < 200ms. |
| **A6** | LangGraph HITL sin checkpointer persistente | Sales_agent graph se reinicia → `interrupt()` pierde state | `AgentStateCheckpointModel` ya existe en sales_agent — usarlo. O PostgreSQL checkpointer de LangGraph. |
| **A7** | Inline keyboard buttons para flows complejos | Telegram max 100 buttons, 64 bytes callback data — forms complejos no caben | Keyboards solo para yes/no, opciones ≤5. Todo lo demás → text input o redirect web. |
| **A8** | Enviar respuestas LLM inline (en el webhook handler) | Timeout Telegram 5s → si LLM tarda > 5s Telegram reintenta → mensajes duplicados | Siempre: enqueue → 200 OK → worker procesa → sendMessage async. |
| **A9** | 1 conversation por tenant (global) en Telegram | Si dueño escribe desde 2 dispositivos o retoma una semana después → contexto mezclado | 1 conversation por `chat_id`. `chat_id` en Telegram DMs = `from_user.id` — mismo usuario siempre tiene el mismo chat_id con el bot. |
| **A10** | No validar que el update viene de Telegram | Webhook endpoint público — cualquiera puede hacer POST | Validar secret_token (Telegram permite `setWebhook` con `secret_token` header — validar `X-Telegram-Bot-Api-Secret-Token`). |
| **A11** | Procesar mensajes de grupos/canales | Bot global recibirá añadidos a grupos → procesarlos con copilot logic expone copilot a terceros | Handler ignora todo update que no sea `message.chat.type == "private"`. |

---

## Decisiones Recomendadas (Consolidado)

### MEMORIA
- **D1:** Reutilizar `ContextWindowBuilder` + `RollingSummarizer` existentes con config `TELEGRAM_CONTEXT_WINDOW_CONFIG` distinto (más tokens raw, summary más largo). No implementar vector retrieval en MVP.
- **D2:** Reutilizar `CopilotConversationModel` — añadir columnas `channel_type` + `channel_chat_id`. Una conversación Telegram = 1 row con `channel_type='telegram'` + `channel_chat_id=str(from_user.id)`.
- **D3:** Monitorear si el prefijo cacheable del sistema prompt en Telegram baja de 1024 tokens — añadir fragmento `TELEGRAM_CHANNEL_CONTEXT` a `CACHEABLE_FRAGMENTS` para asegurar umbral Anthropic.

### HITL
- **D4:** Crear tabla `hitl_requests` (schema en Sección 2). Sales_agent genera `HITLRequest` → evento → copilot Telegram notifica al dueño → respuesta resume graph via LangGraph `Command(resume=...)`.
- **D5:** Timeout default: 15 minutos. Post-timeout: sales_agent procede con `decision_fallback` configurable. Worker ARQ cada 5 min resuelve expirados.
- **D6:** Sales_agent graph necesita checkpointer persistente para que `interrupt()` sobreviva process restart. Usar `AgentStateCheckpointModel` existente o migrar a `PostgresCheckpointer` de LangGraph.

### MULTI-USER
- **D7:** Crear tabla `copilot_channel_links` (schema en Sección 3) desde MVP aunque solo se use con rol `owner`. Identity key = `from_user.id`, no `username`.
- **D8:** MVP: solo owner puede linkear. Schema permite múltiples roles para futuro sin migraciones.

### ONBOARDING
- **D9:** Magic link via `t.me/nicolify_copilot_bot?start=TOKEN`. Token = HMAC-SHA256, TTL 15 min, single-use. Guardar hash en DB (no plaintext). FE polling cada 3s por 60s para confirmar link.
- **D10:** Bot sin link responde con instrucción clara de onboarding + URL directa. Sin intentar auth in-chat.

### TOOLS
- **D11:** Añadir `available_channels: frozenset[str]` a metadata de tool groups. Default = todos los canales. Groups web-only: `navigation`, `guided` (wizard), `landing` mutations, `offer_section` mutations.
- **D12:** Tool unavailable en Telegram → respuesta template friendly + link web directo. NUNCA mensaje de error técnico.

### ESCALABILIDAD
- **D13:** Webhook handler es NON-BLOCKING — solo encola en ARQ/Redis y devuelve 200 en < 200ms.
- **D14:** 1 bot global copilot (`TELEGRAM_COPILOT_BOT_TOKEN` env var). Distinto e independiente de `TELEGRAM_BOT_TOKEN` (sales_agent).
- **D15:** Rate limiting en ARQ worker (30 msg/sec global, 1 msg/sec per chat_id). No en handler.
- **D16:** Validar `X-Telegram-Bot-Api-Secret-Token` header en webhook endpoint para prevenir fake updates.
- **D17:** Filtrar `chat.type == "private"` — ignorar grupos, canales, supergrupos.

### SEGURIDAD / PII
- **D18:** `sanitize_payload()` (ya existe) se llama antes de persistir cualquier mensaje Telegram.
- **D19:** Guardar solo `from_user.id` (numérico) como identity. `username` en `channel_links` nullable, mutable, no usado como FK.
- **D20:** Archivos Telegram > 20 MB → rechazar con mensaje friendly + redirect web. ≤ 20 MB → descargar con `getFile` → mismo pipeline que document tool web.

---

## Referencias Técnicas

- Telegram Bot API rate limits: https://core.telegram.org/bots/faq#broadcasting-to-users
- Telegram Bot API sendMessage: https://core.telegram.org/bots/api#sendmessage
- Telegram setWebhook + secret_token: https://core.telegram.org/bots/api#setwebhook
- Telegram deep links: https://core.telegram.org/bots/features#deep-linking
- LangGraph interrupt pattern: https://langchain-ai.github.io/langgraph/how-tos/human_in_the_loop/
- LangGraph Command(resume=): https://langchain-ai.github.io/langgraph/concepts/human_in_the_loop/
- LangChain ConversationSummaryBufferMemory: https://python.langchain.com/docs/modules/memory/types/summary_buffer/
- Anthropic prompt caching docs: https://docs.anthropic.com/en/docs/build-with-claude/prompt-caching

## Código Nicolify de referencia para PI-5

| Qué | Path |
|-----|------|
| Context window builder | `backend/src/modules/copilot/application/memory/context_window_builder.py` |
| Rolling summarizer | `backend/src/modules/copilot/application/memory/rolling_summarizer.py` |
| Context window config | `backend/src/modules/copilot/domain/context_window.py` |
| Tool registry con channel_format | `backend/src/modules/copilot/application/tools/registry.py` |
| Telegram channel format spec | `backend/src/shared/agent_observability/channels/format.py` |
| Telegram adapter existente (sales_agent) | `backend/src/modules/connections/infrastructure/channels/telegram.py` |
| Telegram service (connect/webhook) | `backend/src/modules/connections/infrastructure/channels/telegram_service.py` |
| Telegram webhook API (sales_agent) | `backend/src/modules/connections/api/telegram.py` |
| Sales_agent graph (escalation node) | `backend/src/modules/sales_agent/application/agents/sales/graph.py` |
| Sales_agent tool escalate_to_human | `backend/src/modules/sales_agent/application/agents/sales/tools.py` |
| Conversation model | `backend/src/modules/copilot/infrastructure/models/conversation_model.py` |
| System prompt layout (cache boundary) | `backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py` |
| ConversationalChannelPort (seam existente) | `backend/src/shared/links/ports/conversational_channel.py` |
| Test flujo Telegram existente | `backend/src/tests/test_telegram_flow.py` |
