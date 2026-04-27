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

### Hallazgos research

> COMPLETAR.

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

> COMPLETAR.
