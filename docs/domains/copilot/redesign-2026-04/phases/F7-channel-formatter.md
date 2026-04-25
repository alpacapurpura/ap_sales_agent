# F7 — Channel Formatter Registry

**Pre-req:** F1. Paralelizable con F3/F6.
**Sprints estimados:** 1.
**Valor entregado:** usuario pide "para WhatsApp" / "para email" → obtiene texto formateado correctamente, listo para copiar-pegar (sin markdown roto en WA, sin caracteres truncados en SMS).

---

## §1 Objetivo

Registry declarativo `OutputChannelFormat[chat|whatsapp|email|sms|voice|instagram_dm|telegram]`. Cada channel = specs (max chars, emoji, line breaks, markdown allowed, structure hint). Synthesizer node de F5 + general chat consumen registry.

---

## §2 Pre-lectura específica

- `02-architecture-target.md §7`.
- `learnings/F1-*.md` y `learnings/F5-*.md` (synthesizer wiring).

---

## §3 Research mandate (abril 2026)

Queries WebSearch:

- `WhatsApp Business API message limits formatting 2026`
- `email formatting plain text vs HTML LLM generated 2026`
- `SMS character limit segmentation 2026 best practices`

Productos:

- Specs verificadas por canal.

---

## §4 Lo que NO se toca

- Adapters de canales del sales_agent (no tocan este flow).
- Multi-modal blocks (text block sigue intacto).

---

## §5 Deliverables

### 5.1 Domain

`backend/src/modules/copilot/domain/output_channels.py`:

```python
@dataclass(frozen=True)
class ChannelFormat:
    id: str
    label_es: str
    max_chars: int
    emoji_allowed: bool
    line_break_style: str
    markdown_allowed: bool
    structure_hint: str
```

Registry inicial: chat, whatsapp, email, sms, voice, instagram_dm, telegram.

### 5.2 Tool standalone

`backend/src/modules/copilot/application/tools/format_for_channel.py`:

- Input: content + channel_id.
- Output: formatted text + warnings (truncado, emoji removido, etc.).

### 5.3 Synthesizer integration

`copilot/application/nodes/synthesize_for_channel.py`:

- Recibe content + channel_id.
- Renderiza prompt con structure_hint + constraints.
- Output validated contra specs.

### 5.4 Provider hook

Providers pueden registrar canales nuevos: `register_channel(ChannelFormat)`.

### 5.5 UI

- Composer agrega selector "Formato salida" (chat default; opcional whatsapp/email/sms).
- Cards de respuesta muestran badge "Formato: WhatsApp" cuando aplica.

### 5.6 Tests

- Unit por channel: input idéntico, output respeta specs.
- Integration: `ask_tenant_data(..., output_channel="whatsapp")` → respuesta sin markdown, ≤1024 chars.

---

## §6 Quality gates

- `/test-backend` + `/test-frontend` verdes.
- Manual: pedir mismo contenido en chat / whatsapp / email — diferenciado correctamente.

---

## §7 Definición de hecho

- [ ] Registry con 7 canales.
- [ ] Tool format_for_channel.
- [ ] Synthesizer integration.
- [ ] Provider extension API.
- [ ] UI selector.
- [ ] Tests verdes.
- [ ] `learnings/F7-channels.md` + `prompts/F8-start.md`.
