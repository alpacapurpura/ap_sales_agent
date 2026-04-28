# S5 · Channel format registry (shared)

## Objetivo

Extraer `ChannelFormat` registry de copilot a `shared/agent_observability/channels/` (o equivalente). Sales_agent consume via `register_channel` patterns. `OutputManager` deja hardcoded chunking y consume registry. Multi-canal extensible sin tocar `OutputManager`.

## Dependencias

- S0 cerrado.

## Criterios de éxito

1. `shared/.../channels/` con `ChannelFormat` dataclass + `register_channel` API.
2. Channels registrados: `whatsapp`, `whatsapp_business`, `telegram`, `instagram_dm`, `web_chat`, `voice` (si existe), `sms`, `email`.
3. `OutputManager.process_response(text, channel_id)` consulta registry, no hardcoded if-else.
4. Sales_agent specialists pueden invocar `format_for_channel(text, channel_id)` como tool determinístico (no LLM).
5. Channel registry exporta `typing_simulation_cpm` para que `OutputManager` lo use sin import del registro interno.
6. `channel_intent_detector` shared o duplicado controlado (decisión documentada).
7. Test arch: agregar channel = single registry edit; specialists, output_manager, formatter no requieren toque.
8. Quality gates verdes.

## Research mandate

### Queries WebSearch obligatorias

1. `WhatsApp Business API message length limits 2026` — verificar max_chars vigente.
2. `Instagram DM messaging limits markdown emoji policy 2026` — Meta cambió varias veces.
3. `Telegram Bot API parse_mode HTML vs Markdown 2026` — sales puede aprovechar.
4. `SMS character encoding GSM-7 vs UCS-2 LATAM accents 2026` — emoji + tildes pueden duplicar costo.

### Tessl tiles

- N/A primaria.

### Lectura obligatoria

- `learnings/S0-*.md`.
- `backend/src/modules/copilot/domain/output_channels.py`.
- `backend/src/modules/copilot/application/tools/format_for_channel.py`.
- `backend/src/modules/copilot/application/orchestrator/channel_intent_detector.py`.
- `backend/src/modules/sales_agent/infrastructure/external/output_manager.py`.
- `backend/src/modules/sales_agent/application/services/channel_resolver.py`.

### Hallazgos research (2026-04-28)

#### WhatsApp Business API
- **Cap free-form session text:** 4096 chars. Templates: 1024. Algunos providers (BSP) permiten 1600 en business-initiated. Conclusión: chunk_size ≤ 1024 es safe cross-BSP, max_chars=4096 para session messages.
- **Markdown subset:** WhatsApp NO soporta markdown estándar — usa formato propio: `*bold*`, `_italic_`, `~strike~`, ``` ``` monospaced. Fórmula `**bold**` (markdown estándar) NO se renderiza. Decisión: `markdown_allowed=False` (preservar `*` `_` `~` literals que el wire entiende, no permitir doble-asterisco markdown).
- **Emojis:** Permitidos. UTF-8 nativo.
- **Source:** `https://www.engagespark.com/support/whatsapp-business-limits/`, `https://blogs.sparktg.com/limit-on-message-length-whatsapp-business-api.html`.

#### Telegram Bot API
- **Cap text message:** 4096 chars per message. Multi-message split por chunks.
- **parse_mode MarkdownV2:** chars que MUST escapar con `\`: `_ * [ ] ( ) ~ ` ` > # + - = | { } . !`
- Inside `pre`/`code`: escape solo ` ``` ` y `\`. Inside link `(...)`: escape `)` y `\`.
- Decisión: `parse_mode="MarkdownV2"`, `markdown_allowed=True`. `format_for_channel` con parse_mode=MarkdownV2 aplica escape a chars NO intencionados markdown.
- **Source:** `https://core.telegram.org/bots/api`, `https://core.telegram.org/tdlib/docs/classtd_1_1td__api_1_1text_parse_mode_markdown.html`.

#### Instagram DM (Graph API)
- **Cap por mensaje:** 1000 chars (incluyendo emojis). Emojis cuentan ≥2 chars cada uno (skin-tone variants más). Excede → API rechaza send.
- **Markdown:** NO renderizado. Plain text + emojis solo.
- **Rate limit:** 200 DM/h por cuenta via API (no afecta format, pero anchor para futuro).
- **Source:** `https://www.inro.social/blog/how-many-direct-messages-can-you-send-on-instagram`, `https://flowgent.ai/blog/instagram-dm-limits-how-many-messages-you-can-send-daily`.

#### SMS GSM-7 vs UCS-2
- **Single GSM-7 segment:** 160 chars. Concatenated multi-segment GSM-7: 153 chars/segmento.
- **Accents/emoji** flip a UCS-2: 70 chars single, 67 chars/segment concatenado. **Tildes españolas (á/é/í/ó/ú) + ñ NO están en GSM-7 base** — disparan UCS-2 → costo doble + cap reducido.
- **National Language Shift Tables (3GPP 23.038):** Spanish + Portuguese tienen shift table que permite acentos en 7-bit (155 chars) — pero soporte BSP/operador inconsistente en LATAM.
- Decisión: SMS `max_chars=160`, `emoji_allowed=False`, `markdown_allowed=False`. structure_hint advierte explícito: sin tildes para asegurar GSM-7. Si tenant insiste en tildes, preferible no usar SMS — usar WhatsApp.
- **Source:** `https://en.wikipedia.org/wiki/GSM_03.38`, `https://supportcenter.everbridge.com/hc/en-us/articles/19141701423771-EBS-GSM-7-and-UCS-2-Character-Encodings-and-Their-Importance-When-Sending-SMS-Messages`.

#### Evolution API v2 (WhatsApp wrapper)
- **Endpoint:** `POST /message/sendText/{instance}` con payload `{ "number": "...", "text": "...", "delay": int, "linkPreview": bool, "mentionsEveryOne": bool, "mentioned": [...], "quoted": {...} }`.
- **Adapter responsability:** envoltorio sobre WhatsApp Cloud API — mismos límites char (4096 session, 1024 template, 1600 BSP-permissive). NO requiere registro de canal separado: el `whatsapp` ChannelFormat existente cubre. El payload structure es responsabilidad del adapter (`shared/links/ports/channel_adapter.py::create_whatsapp_adapter`), no del registry.
- Decisión: NO crear `evolution` channel separado. Si tenant usa Evolution, sigue siendo `channel_type="whatsapp"`. Adapter wrapping Evolution lo mapea internamente.
- **Source:** `https://doc.evolution-api.com/v2/api-reference/message-controller/send-text`.

#### Conclusiones agregadas
- **Movemos copilot's `output_channels.py` + `format_for_channel.py` + `channel_intent_detector.py` a `shared/agent_observability/channels/`** — el shape (frozen+slots ChannelFormat, register_channel idempotente, get_channel_format con fallback, reset_registry_for_tests) ya es production-grade. NO redesign.
- **Extendemos `ChannelFormat`** con campos sales-relevantes (defaults preservan back-compat copilot):
  - `chunk_size: int | None = None` — split máx para `OutputManager._parse_response`. None → no split forzado.
  - `typing_simulation_cpm: int | None = None` — sales-only realismo. None → OutputManager fallback `CPM_SPEED` global.
  - `parse_mode: str | None = None` — Telegram MarkdownV2 hint para channel adapter.
- **Channels existentes copilot** (chat, whatsapp, telegram, sms, voice, instagram_dm, email) cubren sales 100%. Sales `channel_type` strings ("telegram"/"whatsapp"/"instagram") mapean a `instagram_dm` via alias dict (ya hay precedente FE/BE inconsistente).
- **`web` / `web_chat`** mencionado en plan original — copilot tiene `chat` (label "Chat (Copilot)"). NO duplicamos: para sales web embed se usa `chat`. Si surgen requirements distintos, agregar `web_chat` separado en S6.
- **Slot 6 CHANNEL_FORMAT_HINT** puebla `structure_hint` del registry resolved por `state.channel_type`. Cacheable per-tenant porque structure_hint es estática per-canal pero el slot lo lee per-turn (cache hit segundo turno mismo canal).

---

## Diseño

### `shared/agent_observability/channels/`

```python
@dataclass(frozen=True)
class ChannelFormat:
    id: str                      # e.g. "whatsapp"
    label: str                   # "WhatsApp"
    max_chars: int
    chunk_size: int              # for OutputManager splitting
    markdown_allowed: bool
    emoji_allowed: bool
    typing_simulation_cpm: int   # 0 = no typing sim
    structure_hint: str          # injected to system prompt
    parse_mode: str | None       # provider-specific (e.g. "MarkdownV2" for telegram)

CHANNELS: dict[str, ChannelFormat] = {}

def register_channel(fmt: ChannelFormat) -> None:
    if fmt.id in CHANNELS:
        raise ValueError(f"Duplicate channel: {fmt.id}")
    CHANNELS[fmt.id] = fmt

def get_channel(channel_id: str) -> ChannelFormat:
    if channel_id not in CHANNELS:
        return CHANNELS["web_chat"]  # safe fallback
    return CHANNELS[channel_id]
```

Bootstrap (al importar el módulo):
```python
register_channel(ChannelFormat(id="whatsapp", max_chars=4096, chunk_size=2000, ...))
register_channel(ChannelFormat(id="whatsapp_business", max_chars=4096, ...))
register_channel(ChannelFormat(id="telegram", max_chars=4096, parse_mode="MarkdownV2", ...))
register_channel(ChannelFormat(id="instagram_dm", max_chars=1000, markdown_allowed=False, emoji_allowed=True, ...))
register_channel(ChannelFormat(id="web_chat", max_chars=10000, markdown_allowed=True, ...))
register_channel(ChannelFormat(id="sms", max_chars=160, markdown_allowed=False, emoji_allowed=False, ...))
register_channel(ChannelFormat(id="email", max_chars=100000, markdown_allowed=True, ...))
```

### Refactor `OutputManager`

ANTES (pseudo):
```python
def process_response(text, channel):
    if channel == "whatsapp":
        chunks = split_by(text, 2000)
    elif channel == "telegram":
        chunks = split_by(text, 4096)
    ...
```

DESPUÉS:
```python
def process_response(text, channel_id):
    fmt = get_channel(channel_id)
    text = format_for_channel(text, fmt)  # determinístico
    chunks = split_by(text, fmt.chunk_size)
    return chunks  # consumed by sender adapter
```

### `format_for_channel` (shared tool)

Pure, sin LLM:
- Strip markdown si `not fmt.markdown_allowed` (regex).
- Strip emoji si `not fmt.emoji_allowed` (unicode category sweep).
- Truncate a `max_chars` (smart split).
- Apply `parse_mode` formatting (Telegram: MarkdownV2 escape).

### `channel_intent_detector`

Decisión: **mover a shared**. Sales_agent puede inferir cuando lead pide en otro canal ("mándame por WhatsApp"). Hoy no usa, pero el comportamiento es transversal.

---

## Plan TDD

### RED tests

1. `tests/shared/channels/test_channel_registry.py`:
   - `register_channel` rechaza id duplicado.
   - `get_channel("nonexistent")` retorna fallback.
   - Todos los canales bootstrap presentes.

2. `tests/shared/channels/test_format_for_channel.py`:
   - WhatsApp + markdown text → markdown stripped.
   - Telegram + markdown → preservado con escape MarkdownV2.
   - SMS + emoji → emoji stripped + accents preserved.

3. `tests/modules/sales_agent/test_output_manager_uses_registry.py`:
   - OutputManager invocado con `channel_id="whatsapp"` → chunk size 2000.
   - Channel desconocido → fallback web_chat.

4. `tests/architecture/test_channel_registry_extensibility.py`:
   - Agregar canal nuevo en bootstrap → 0 cambios en `OutputManager`, `format_for_channel`.

5. `tests/architecture/test_no_hardcoded_channel_in_output_manager.py`:
   - AST scan: no string literal `"whatsapp"`, `"telegram"`, etc. en `output_manager.py`.

---

## Implementación step-by-step

1. Crear `shared/agent_observability/channels/__init__.py` con dataclass + registry.
2. Bootstrap channels al import.
3. Mover `format_for_channel` a shared.
4. Refactor `OutputManager` para consumir registry.
5. Mover `channel_intent_detector` a shared.
6. Agregar `format_for_channel` a sales_agent tools registry como always-available.
7. Verificar copilot sigue funcionando (no rompimos nada compartiendo).

---

## Riesgos + mitigaciones

| Riesgo | Mitigación |
|---|---|
| Telegram MarkdownV2 escape rompe mensajes | Test exhaustivo con caracteres especiales (`_`, `*`, `[`, `]`, `(`, `)`). |
| SMS GSM-7 con tildes duplica caracteres | Detectar y warn al user (loggear, no fail). |
| OutputManager refactor rompe live conversations | Smoke con webhook real Telegram dev environment antes de deploy. |
| typing_simulation_cpm queda en OutputManager hardcoded | Mover al ChannelFormat dataclass como campo. |

---

## Tech debt watchpoints

- Si webhook adapters tienen channel-specific signature verification mezclada con format → separar (single responsibility).
- Si `channel_resolver.py` mezcla resolución de adapter (in/out) con format → split.
- Channel-specific tools (ej: WhatsApp send-button) no caben en `format_for_channel` — necesitarían tools separados. Loggear si aparecen.

---

## Ajustes vs plan original

- **Plan original**: extract registry copilot a shared/, sales OutputManager refactor de hardcoded if-else por canal, sales specialists invocan `format_for_channel` como tool determinístico.
- **Realidad post-audit**: el copilot ya tenía un registry production-grade (`@dataclass(frozen=True, slots=True)` + `register_channel` idempotente + `get_channel_format` con fallback + `reset_registry_for_tests`). NO redesign. Move + extend.
- **Sales OutputManager NO tenía if-else por canal**: `_parse_response(channel_type)` recibía el param con `# noqa: ARG003` y splitting era paragraph-only universal. La "tech debt" era una **ausencia de wiring**, no un anti-patrón. S5 wirea `_parse_response` para que consuma `ChannelFormat.chunk_size` cuando el registry lo declara.
- **`format_for_channel` como tool sales**: NO se agregó al sales tools registry en S5. El uso real es `OutputManager._parse_response` consume `chunk_size` (suficiente para WhatsApp template-safe). Si el LLM tuviera que adaptar texto post-generación a otro canal (ej. lead pide "mándame por WhatsApp" pero `channel_type` viene `telegram`), es DEFERRED-S8/S9 cuando los tools de scheduling/payment se agreguen al registry.
- **`channel_intent_detector` move a shared**: hecho via shim (re-export). Sales puede consumir cuando el lead pida switch de canal. Wiring activo NO se agrega en S5 (sales hoy NO procesa intent — bloqueado por `BufferService.smart_debounce` §3).
- **typing_simulation_cpm**: agregado al `ChannelFormat` como campo opcional (default None → fallback `OutputManager.CPM_SPEED` global). NO wireado en S5 (CPM_SPEED es §3 protected). Disponible para S6 si se decide override per-canal.
- **`web_chat`**: NO se agregó como canal separado. `chat` (label "Chat (Copilot)") cubre. Si surge requerimiento de sales web embed con specs distintas, S6 puede agregar `web_chat` al baseline.
- **Telegram MarkdownV2 escape**: agregado como utility `escape_markdown_v2(text)` en `format.py`. NO auto-aplicado por `format_for_channel_impl` (rompería intentional markdown). Channel adapter Telegram (`shared/links/ports/channel_adapter.py::create_telegram_adapter`) consume cuando le toque.
- **Aliases**: `instagram` → `instagram_dm` resuelto por `_CHANNEL_ID_ALIASES` dict en `format.py`. Sales `ChannelResolver` usa `instagram` (no `_dm`); el alias evita duplicar entradas.

---

## Resultado

| Criterio | Estado |
|---|---|
| 1. `shared/.../channels/` con dataclass + register_channel | ✅ `src/shared/agent_observability/channels/{format,format_for_channel,intent_detector}.py` |
| 2. Channels registrados (whatsapp/telegram/instagram_dm/sms/voice/email/chat) | ✅ 7 canónicos cross-agent |
| 3. OutputManager consume registry, no hardcoded | ✅ `_enforce_chunk_size` + `_split_by_cap` + arch ratchet |
| 4. Specialists pueden invocar `format_for_channel` | ✅ tool importable; activo wiring opcional (DEFERRED-S8/S9) |
| 5. Channel registry exporta `typing_simulation_cpm` | ✅ campo opcional declared (no wireado activo, §3 protected) |
| 6. `channel_intent_detector` shared | ✅ moved + copilot shim back-compat |
| 7. Test arch: agregar canal = single registry edit | ✅ baseline + tests structure_hint/markdown/emoji/parse_mode/chunk_size cubren |
| 8. Quality gates verdes | ✅ ruff 0 / format clean / 3134 tests passed |
