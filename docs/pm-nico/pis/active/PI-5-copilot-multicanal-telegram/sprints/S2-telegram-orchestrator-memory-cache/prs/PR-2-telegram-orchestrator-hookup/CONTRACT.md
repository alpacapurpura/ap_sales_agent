# Contract — PR-2-telegram-orchestrator-hookup

## 0. Context Summary

| Campo | Valor |
|---|---|
| PR | `PR-2-telegram-orchestrator-hookup` |
| Sprint padre | `S2-telegram-orchestrator-memory-cache` |
| PI padre | `PI-5-copilot-multicanal-telegram` |
| Architect run on | **2026-05-01** (Step 0 `date -u +%Y-%m-%d`) |
| Architect agent | `nicolify-architect` (Opus 4.7 [1M], cutoff Jan 2026) |
| CONTEXT-BRIEF source | **§7 + §8 from `nicolify-context-builder` Haiku 4.5 (full fidelity, faithfulness flag = clean)** — verified by self-running greps Path B for memory call-site coverage (no orchestrator wiring exists yet for `RollingSummarizer` / `ContextWindowBuilder` — see § 16 Q1) |
| Modules touched | `modules/copilot/` (single surface). `shared/agent_observability/channels/` consumed READ-ONLY (`escape_markdown_v2`, `format_for_channel_impl`). |

### Surface → builder → auditor mapping

| Surface | Builder | Auditor | Skills consultadas |
|---|---|---|---|
| `modules/copilot/application/memory/`, `application/orchestrator/`, `application/tools/`, `infrastructure/workers/`, `infrastructure/repositories/`, `domain/context_window.py` | `nicolify-agentic` (Opus 4.7) | `nicolify-agentic-auditor` (Opus 4.7) | `copilot-expert` + `tessl__langgraph` + `tessl__graceful-degradation` |
| Backend negocio | — none — | — | — |
| Frontend | — none — | — | — |

PM: spawn ONE agentic builder + ONE agentic auditor. Cero `nicolify-backend` / `nicolify-frontend`.

### Skills consulted — decisions taken

- **`copilot-expert`** — confirmed (a) `system_prompt_layout.py` is the only SSoT for cacheable prefix; (b) `_build_combined_system_prompt` lives at `deep_agent.py:208`; (c) F8 cache prefix architecture must not be reordered. **Decision:** add new `TELEGRAM_CHANNEL_CONTEXT` slot to `PromptFragment` enum and `CACHEABLE_FRAGMENTS` tuple; build it conditionally on `state["client_context"]["channel"] == "telegram"` so web bytes stay byte-identical.
- **`copilot-expert`** — confirmed `stream_chat` is **streaming-only** (`AsyncGenerator[str, None]` of SSE strings). Telegram worker cannot consume SSE. **Decision:** add a new sibling method `CopilotOrchestrator.invoke_text(...)` that returns `CopilotInvokeResult` (final text + final state + tokens) — it shares `_prepare_conversation` / `_run_graph_stream` accumulator logic but does NOT yield SSE; it consumes the same async generator internally and discards SSE wire format. NO new orchestrator class. NO new graph build.
- **`tessl__langgraph`** — confirmed pattern for synchronous invocation: `compiled_graph.ainvoke(state, config={"recursion_limit": N, "configurable": {...}})`. We DO NOT need to subclass the graph; per-invocation `channel` lives in `state["client_context"]["channel"]` already supported by `_build_client_context`.
- **`tessl__graceful-degradation`** — every external call in worker (orchestrator invocation, format adapter, bot send) has explicit timeout + try/except + structlog warning + log-only-no-raise on failure. **Iron rule: every external call gets a timeout, every timeout gets a fallback.**
- **`sales-agent-expert`** — NOT consulted (sales_agent surface untouched per D-PI5-005 physical separation).

### pm-nico/current-state files affected (post-merge)

- `docs/pm-nico/current-state/copilot.md` — upgrade capability "Canal Telegram — DMs linkeados" from `parcial (LLM placeholder)` → `live (orchestrator real)` with commit hash; append micro-capability "Memory + cacheable prefix Telegram-aware".

### Architecture fitness gates that must keep passing

```
backend/tests/architecture/test_copilot_anchors.py
backend/tests/architecture/test_no_new_copilot_module_imports.py
backend/tests/architecture/test_copilot_provider_compliance.py
backend/tests/architecture/test_copilot_telegram_separation.py    ← extended w/ new test
backend/tests/architecture/test_system_prompt_order.py
backend/tests/architecture/test_brand_lighthouse_in_system_prompt.py
backend/tests/architecture/test_channel_formatter_compliance.py
backend/tests/architecture/test_workflow_compliance.py
```

Allowlist movements: only **shrinks** allowed. `test_copilot_anchors.py::ANCHOR_REGISTRY` adds 1 anchor `[COPILOT-TELEGRAM-CHANNEL-CONTEXT]` → bump cap from 36 → 37 in same commit.

---

## 1. Domain Entities

NO new entities. PR-1 already added Telegram persistence layer (`copilot_channel_links`, `copilot_link_tokens`, `copilot_conversations.{channel_type, channel_chat_id}`). PR-2 only adds **a configuration constant** to existing domain:

```python
# backend/src/modules/copilot/domain/context_window.py — EXTEND existing file

@dataclass(frozen=True, slots=True)
class ContextWindowConfig:
    # … existing fields unchanged …
    pass

DEFAULT_CONTEXT_WINDOW_CONFIG = ContextWindowConfig()  # web — UNCHANGED

# NEW — D-PI5-006 values, frozen dataclass instance
TELEGRAM_CONTEXT_WINDOW_CONFIG: ContextWindowConfig = ContextWindowConfig(
    RAW_WINDOW_TOKENS=3000,            # vs web 2000 — Telegram sessions más espaciadas
    RAW_WINDOW_MAX_MESSAGES=15,        # vs web 10
    RAW_WINDOW_MIN_MESSAGES=4,         # idem
    SUMMARY_MAX_CHARS=600,             # vs web 400 — más historia al resumir
    SUMMARY_TARGET_TOKENS=220,         # vs web 150
    NUDGE_AFTER_TOTAL_TOKENS=12_000,   # D-PI5-006
    NUDGE_HARD_LIMIT_TOKENS=20_000,    # arquitect proposal — coherencia con NUDGE_AFTER bumped
    NUDGE_AFTER_MESSAGE_COUNT=18,      # vs web 12 — coherencia ratio
    TOKEN_COUNTER="tiktoken:cl100k_base",  # idem
)

# NEW — channel → config dispatcher (pure, side-effect free)
def get_context_window_config(channel: str | None) -> ContextWindowConfig:
    """Resolve config for ``channel``. Default ``web`` for None / unknown — backward compat."""
    if channel == "telegram":
        return TELEGRAM_CONTEXT_WINDOW_CONFIG
    return DEFAULT_CONTEXT_WINDOW_CONFIG
```

**Rationale:** `ContextWindowConfig` is already `@dataclass(frozen=True, slots=True)`. Adding a sibling **instance** + a pure dispatcher fn keeps the domain immutable, tenant-isolated (no `tenant_id` needed — config is global per channel by design), backward-compatible (default ‘web’).

---

## 2. SQLAlchemy 2.0 Models

**NO model changes.** PR-1 added all required columns:

- `copilot_conversations.channel_type: VARCHAR(32) NULL` (NULL = web)
- `copilot_conversations.channel_chat_id: VARCHAR(64) NULL`
- Index on `(tenant_id, channel_type, channel_chat_id)` (already present per PR-1 RESULT.md)

**Concurrency invariant (cross-cutting `infrastructure/repositories/conversation_repository.py`):**
- The new lookup method MUST use the existing index but does NOT add a new UNIQUE constraint. PR-1 chose NOT to add a UNIQUE on `(tenant_id, user_id, channel_type, channel_chat_id)` — see § 16 Q5. PR-2 inherits this and uses a **per-(tenant, channel_chat_id) advisory lock** OR optimistic SELECT-then-INSERT-on-empty pattern documented in § 7.

---

## 3. Pydantic v2 DTOs

**No request/response API DTOs change.** Telegram traffic is webhook-driven (PR-1 already shipped `WebhookAck`). PR-2 introduces ONE internal application-layer DTO:

```python
# backend/src/modules/copilot/application/orchestrator/invoke_result.py — NEW

from pydantic import BaseModel, ConfigDict

class CopilotInvokeResult(BaseModel):
    """Result of CopilotOrchestrator.invoke_text() — non-streaming text invocation.

    Internal application-layer DTO; never serialized to HTTP. Telegram worker
    consumes it and routes the text through ``format_for_channel_impl`` →
    ``CopilotTelegramBot.send_message``.
    """

    model_config = ConfigDict(from_attributes=True, frozen=True)

    conversation_id: str
    response_text: str          # Final assistant text (post-orchestrator, pre-channel-format)
    total_tokens: int           # Sum across all LLM calls in the turn
    cache_read_tokens: int      # cache_read_input_tokens accumulated
    cache_creation_tokens: int  # cache_creation_input_tokens accumulated
    error_kind: str | None      # None = ok | "timeout" | "tool_loop" | "llm_error" | "unknown"
```

NO new request DTOs. NO new HTTP endpoints. NO `response_model=` to declare (PR-2 is application-layer only).

---

## 4. API Routes

**No new routes. No route signature change.** Existing routes:
- `POST /api/v1/copilot/telegram/webhook` (PR-1, NON-BLOCKING, secret_token auth) — handler enqueues ARQ job, returns 200 in <200ms. UNCHANGED.
- All `/link-tokens`, `/link-status`, `/link` UNCHANGED.

`FastAPI(redirect_slashes=False)` invariant preserved — no router-level change.

---

## 5. TypeScript Types (Frontend)

NOT APPLICABLE. PR-2 has zero FE surface (verified vs PR.md "Out of scope" + RESULT.md PR-1 "FE flow completo: linking + polling").

---

## 6. Repository Interfaces

```python
# backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py
# EXTEND existing class — ONE new method

class ConversationRepository:
    # … existing methods unchanged (49+ methods preserved) …

    def get_or_create_by_channel(
        self,
        *,
        tenant_id: UUID,
        user_id: UUID,
        channel_type: str,
        channel_chat_id: str,
    ) -> CopilotConversationModel:
        """Return the live conversation for ``(tenant, user, channel, chat_id)`` or create one.

        PI-5 D-PI5-007: 1 conversation per ``(tenant_id, user_id, channel_type,
        channel_chat_id)`` quadruple — single source of truth.

        Concurrency strategy: optimistic SELECT-then-INSERT pattern.
            1. SELECT … WHERE all four keys + deleted_at IS NULL LIMIT 1
            2. If hit → return.
            3. Else → INSERT new row with auto-uuid; flush.
            4. On IntegrityError (rare race; UNIQUE on the index would catch
               it once D-PI5-DEFER-UNIQUE is decided — see open question Q5) →
               retry SELECT once and return that row.

        Tenant-scoped. Excludes ``deleted_at`` rows. Per-channel: ``channel_type
        == 'web'`` IS ACCEPTED (caller's responsibility) but the canonical web
        path uses ``create()`` + ``get_by_id()`` already.

        # [COPILOT-TELEGRAM-CONV-LOOKUP-PR2] -> docs/pm-nico/pis/active/PI-5/.../PR-2/CONTRACT.md
        """
```

**All other existing methods unchanged.** Tenant isolation: every query already filters `tenant_id` (verified in §7 reading); the new method follows the same pattern.

**Test surface:** `tests/modules/copilot/infrastructure/repositories/test_conversation_repository_telegram_lookup.py` (NEW):
- Hits existing row when `(t, u, 'telegram', 'chat-1')` present → returns same `id`
- Creates when no row matches
- Honors `deleted_at IS NOT NULL` (treats deleted as missing → creates new)
- Cross-tenant isolation: same `(u, channel_type, chat_id)` for tenant A returns row A, never tenant B's

---

## 7. Application Services

### 7.1 `CopilotOrchestrator.invoke_text` — NEW non-streaming text invocation

```python
# backend/src/modules/copilot/application/orchestrator/chat.py — EXTEND

class CopilotOrchestrator:
    # … existing __init__, _prepare_conversation, _run_graph_stream, stream_chat unchanged …

    async def invoke_text(
        self,
        *,
        user_id: UUID,
        tenant_id: UUID,
        message: str,
        conversation_id: str | None = None,
        channel: str = "web",
        context: ClientContextDTO | None = None,
    ) -> CopilotInvokeResult:
        """Run one full turn and return the final assistant text (no SSE).

        PR-2 PI-5: entry point used by Telegram worker (and any other future
        non-streaming consumer like email). Internally drives the same graph
        stream as ``stream_chat`` but accumulates the final ``acc.full_response``
        instead of yielding SSE events.

        Steps mirror ``stream_chat`` exactly:
          1. ``_prepare_conversation`` — gets/creates conv, hydrates state.
          2. ``state["client_context"]["channel"] = channel`` (per-invocation context).
          3. Open observability turn (best-effort).
          4. Iterate ``_run_graph_stream`` to drain SSE generator and accumulate.
          5. ``_persist_messages`` (existing path).
          6. Return ``CopilotInvokeResult``.

        Errors are caught and reported via ``error_kind`` (timeout / tool_loop /
        llm_error / unknown). The method NEVER raises to the worker — graceful
        degradation per ``tessl__graceful-degradation`` (worker writes a friendly
        fallback to user, logs structured error).

        Default ``channel='web'`` preserves backward compat for other future
        non-streaming callers.
        """
```

**Key invariant:** `invoke_text` shares `_prepare_conversation` and `_run_graph_stream` with `stream_chat`. NO duplicate orchestrator. NO new graph build. NO new persistence path.

**`_prepare_conversation` extension** (single line addition):

```python
# inside _prepare_conversation, after client_ctx is built but before state composition:
client_ctx["channel"] = (context.channel if context and getattr(context, "channel", None) else "web")  # PR-2 PI-5
```

**`ClientContextDTO` extension** (`backend/src/modules/copilot/api/dto.py`):

```python
class ClientContextDTO(BaseModel):
    # … existing fields …
    channel: str | None = None     # PR-2 PI-5: 'web' | 'telegram' | future. None = web (backward compat).
```

**Idempotency:** Telegram worker already handles re-delivery (`update_id`) at webhook layer (PR-1). `invoke_text` is NOT idempotent across calls — same `(message, conversation_id)` produces a new turn each call. Worker MUST de-dup at update_id level (already done).

### 7.2 Memory builder channel-awareness

```python
# backend/src/modules/copilot/application/memory/context_window_builder.py — EXTEND

class ContextWindowBuilder:
    """… existing docstring unchanged …"""

    def __init__(self, config: ContextWindowConfig) -> None:
        """Store the config for build-time lookups."""
        self._cfg = config

    # NEW — convenience constructor
    @classmethod
    def for_channel(cls, channel: str | None) -> "ContextWindowBuilder":
        """Build a builder for the given ``channel`` (default web)."""
        from src.modules.copilot.domain.context_window import get_context_window_config
        return cls(get_context_window_config(channel))

    # … existing build() method unchanged — config drives behavior ✓
```

```python
# backend/src/modules/copilot/application/memory/rolling_summarizer.py — EXTEND

class RollingSummarizer:
    """… existing docstring unchanged …"""

    def __init__(self, llm: BaseChatModel | None = None, max_chars: int = 400) -> None:
        # UNCHANGED signature.
        self._llm = llm
        self._max_chars = max_chars

    # NEW — convenience constructor
    @classmethod
    def for_channel(cls, channel: str | None, llm: BaseChatModel | None = None) -> "RollingSummarizer":
        """Build a summarizer with channel-appropriate ``max_chars``."""
        from src.modules.copilot.domain.context_window import get_context_window_config
        cfg = get_context_window_config(channel)
        return cls(llm=llm, max_chars=cfg.SUMMARY_MAX_CHARS)
```

**Backward compat invariant:** existing call sites that construct `ContextWindowBuilder(DEFAULT_CONTEXT_WINDOW_CONFIG)` or `RollingSummarizer(max_chars=400)` keep working byte-identically. NO call site of these classes was found in `application/orchestrator/` or `api/` (verified via grep — see § 16 Q1). PR-2 adds the **first** wiring inside `invoke_text` flow.

### 7.3 Telegram worker — orchestrator hookup

```python
# backend/src/modules/copilot/infrastructure/workers/telegram_worker.py
# REPLACE the placeholder branch (lines 133-154) with real orchestrator invocation

# … unchanged lines 1-132 (token-resolution, /start, unlinked CTA branches) …

# ── Linked DM → invoke orchestrator (PR-2 hookup) ──
await touch_last_seen(db, link_id=link.id)

# 1) Conversation lookup-or-create per (tenant, user, channel='telegram', chat_id)
conv_repo = ConversationRepository(db)
conv = conv_repo.get_or_create_by_channel(
    tenant_id=link.tenant_id,
    user_id=link.user_id,
    channel_type="telegram",
    channel_chat_id=chat_id,
)
db.commit()  # release the lookup-or-create transaction before orchestrator

# 2) Orchestrator invocation with channel='telegram' + 30s hard timeout (graceful-degradation)
orchestrator = CopilotOrchestrator(db)
ctx = ClientContextDTO(channel="telegram", locale="es")

try:
    result: CopilotInvokeResult = await asyncio.wait_for(
        orchestrator.invoke_text(
            user_id=link.user_id,
            tenant_id=link.tenant_id,
            message=text,
            conversation_id=str(conv.id),
            channel="telegram",
            context=ctx,
        ),
        timeout=30.0,  # tessl__graceful-degradation — orchestrator + LLM hard cap
    )
except TimeoutError:
    _LOGGER.warning("copilot_telegram_orchestrator_timeout",
                    tenant_id=str(link.tenant_id),
                    chat_id_prefix=_mask_chat_id(chat_id))
    await bot.send_message(
        chat_id=chat_id,
        text="Estoy tardando más de lo normal. Intentá de nuevo en un momento.",
        parse_mode="MarkdownV2",
    )
    return

# 3) Format adapter post-orchestrator (channel='telegram')
formatted = format_for_channel_impl(content=result.response_text, channel_id="telegram")
text_to_send: str = str(formatted["content"])

# 4) Bot send — escape_markdown_v2 happens inside CopilotTelegramBot.send_message (PR-1)
await bot.send_message(
    chat_id=chat_id,
    text=text_to_send,
    parse_mode="MarkdownV2",
)

# 5) Observability log (best-effort, no raise)
_LOGGER.info(
    "copilot_telegram_turn_completed",
    tenant_id=str(link.tenant_id),
    conversation_id=str(conv.id),
    chat_id_prefix=_mask_chat_id(chat_id),
    response_length=len(text_to_send),
    cache_read_tokens=result.cache_read_tokens,
    cache_creation_tokens=result.cache_creation_tokens,
    total_tokens=result.total_tokens,
)
```

**Per-dependency error isolation** (`tessl__graceful-degradation` § Rule 5):
- Conversation lookup failure → log + send fallback "no pude recuperar tu conversación, intentá de nuevo"; never raises.
- Orchestrator timeout → log + friendly fallback above.
- Format adapter is pure → cannot fail (only string transforms).
- `bot.send_message` already handles its own retries + degrades silently (PR-1).

**The wrapping `try/except Exception` at the bottom of the worker (lines 156-162) stays as the safety net — never raise to ARQ.**

### 7.4 Tool registry runtime filter — verification only

`get_tools_for_context(context, channel='telegram')` already supports the `channel` param (PR-1, registry.py:402). Builder MUST verify the orchestrator call site at `chat.py:808, 875, 887, 988` passes `channel=state["client_context"]["channel"]` (currently passes hardcoded or default — auditor catches). Documented as builder responsibility, not new code.

---

## 8. Agentic Surfaces

### 8.1 LangGraph state changes

**No state schema change.** `CopilotState` (existing TypedDict) already carries `client_context: dict`; we add the literal key `"channel"` to the dict. Reducer unchanged (`add_messages` for messages; client_context overwrites — no reducer needed for static per-turn keys).

### 8.2 Topology

UNCHANGED. The existing `build_deep_agent_graph` (single deep agent + tool node + ReAct loop, no supervisor) handles Telegram traffic. No subagent additions. No new `Send` parallel routing.

### 8.3 Nodes + edges

UNCHANGED. The graph is the same one `stream_chat` uses. `invoke_text` consumes the same compiled graph; only the SSE wire is dropped.

### 8.4 Tools — runtime channel filter (verify, no code change to registry)

Tools live behind `get_tools_for_context(context, channel='telegram')`. PR-1 cemented the `ToolGroupMeta.available_channels` SSoT (D-PI5-023). PR-2's job: ensure orchestrator passes `channel='telegram'` when present in `state["client_context"]["channel"]`.

```python
# backend/src/modules/copilot/application/orchestrator/deep_agent.py — small EXTEND at call site

# Existing pattern (line ~275):
# tools = get_tools_for_context(context, channel='web')   ← typically default
# CHANGE TO:
channel = state.get("client_context", {}).get("channel") or "web"
tools = get_tools_for_context(context, channel=channel)
```

(Builder confirms exact line; CONTEXT-BRIEF §7 pinpointed registry @402, deep_agent imports @27,36,56,231,275.)

### 8.5 Prompt cache slot — `TELEGRAM_CHANNEL_CONTEXT` cacheable fragment

```python
# backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py — EXTEND

class PromptFragment(StrEnum):
    # … existing slots …
    STATIC_IDENTITY = "static_identity"
    STATIC_TOOLS_HINT = "static_tools_hint"
    MARKETING_KB_HINT = "marketing_kb_hint"
    TELEGRAM_CHANNEL_CONTEXT = "telegram_channel_context"   # NEW — D-PI5-009
    LIGHTHOUSE = "lighthouse"
    EDITABLE_CATALOG = "editable_catalog"
    MODULES_LIST = "modules_list"
    # … volatile tail …

CACHEABLE_FRAGMENTS: tuple[PromptFragment, ...] = (
    PromptFragment.STATIC_IDENTITY,
    PromptFragment.STATIC_TOOLS_HINT,
    PromptFragment.MARKETING_KB_HINT,
    PromptFragment.TELEGRAM_CHANNEL_CONTEXT,    # NEW — between MARKETING_KB_HINT and LIGHTHOUSE
    PromptFragment.LIGHTHOUSE,
    PromptFragment.EDITABLE_CATALOG,
    PromptFragment.MODULES_LIST,
)
```

**Slot ordering rationale:**
- Goes BEFORE `LIGHTHOUSE` so it stays in the cross-tenant cacheable head (LIGHTHOUSE is per-tenant).
- Goes AFTER `MARKETING_KB_HINT` so the F10 anchor [COPILOT-MARKETING-KB-F10] is preserved exactly.
- Empty value when `state["client_context"]["channel"] != "telegram"` → `_take()` skips it → web prefix bytes IDENTICAL.

```python
# backend/src/modules/copilot/application/orchestrator/graph.py — EXTEND _build_..._fragment family

_TELEGRAM_CHANNEL_CONTEXT_ES: Final[str] = """\
## Canal Telegram — convenciones operables

Este turno se envía desde el bot @nicolify_copilot_bot. Aplican TODAS las
reglas siguientes hasta que el canal cambie:

### Tools no disponibles desde Telegram
Las siguientes acciones requieren el editor web. Si el usuario las pide,
NUNCA inventes éxito — responde con plantilla "Esto se ajusta mejor desde
la web. Te paso el link: app.nicolify.com/{slug}/[ruta]" y termina el turno:
- Edición visual de landings (`landing.*` mutations)
- Wizard de creación de oferta paso a paso (`guided.*`)
- Mutaciones masivas de secciones de oferta (`offer_section.*`)
- Navegación/redireccionamiento (`navigation.*`)

### Tools disponibles desde Telegram
- `awareness`, `analytics`, `crm`, `sales_agent`, `extraction`,
  `knowledge_search`, `data_query`, `document`, `channel_format`,
  `pin_to_memory`, `mutation` (parcial; sólo campos individuales),
  `offer_ladder` (consulta).

### Formato de salida
- Markdown V2 de Telegram. Negritas, cursivas, código inline y bloques de
  código permitidos. Tablas NO renderizan — usa bullets.
- Máximo 4096 caracteres por mensaje. Si la respuesta excede, divide en
  bloques temáticos coherentes con doble newline.
- Sin emojis dentro de bloques de código.
- Para links usa `[texto](https://...)` — nunca pegues URLs sueltas si el
  texto del link es más legible.

### Tono y voz
- Usa la voz del tenant (lighthouse). Tuteo neutro LATAM por defecto. NO
  voseo salvo que la voz del tenant lo establezca explícitamente.
- Responses concisas. Telegram prioriza intercambios cortos: 2-3 párrafos
  máx por turno salvo que el usuario pida un brief.

### Sesiones espaciadas
- El usuario puede no escribir durante horas. NUNCA asumas continuación
  inmediata: si el usuario retoma una intención de hace varias horas,
  re-confirma el contexto en una línea antes de actuar.

### Cuando el usuario quiere algo "del web"
Plantilla obligatoria, byte por byte:
"Esto se ajusta mejor desde el editor web. Te paso el link directo:
app.nicolify.com/{tenant_slug}/{ruta}"

[COPILOT-TELEGRAM-CHANNEL-CONTEXT]
"""

def _build_telegram_channel_context_fragment(state: CopilotState) -> str:
    """Compose the TELEGRAM_CHANNEL_CONTEXT slot (PR-2 PI-5).

    Returns the literal block when ``state["client_context"]["channel"] ==
    "telegram"``; empty string otherwise. The block is byte-identical
    cross-tenant cross-turn — NO interpolation of timestamps, conv ids,
    tenant ids, message counts, or anything that varies between requests.
    The single ``{tenant_slug}`` and ``{ruta}`` placeholders are LITERAL
    strings the LLM substitutes at output time — they are NEVER
    interpolated by Python.
    """
    channel = state.get("client_context", {}).get("channel")
    if channel != "telegram":
        return ""
    return _TELEGRAM_CHANNEL_CONTEXT_ES
```

```python
# backend/src/modules/copilot/application/orchestrator/graph.py::build_system_prompt
# EXTEND fragments dict — add ONE entry

fragments = {
    # ── Cacheable prefix ──
    PromptFragment.STATIC_IDENTITY: _build_static_identity_fragment(),
    PromptFragment.STATIC_TOOLS_HINT: _build_static_tools_hint_fragment(active_tools),
    PromptFragment.MARKETING_KB_HINT: _build_marketing_kb_hint_fragment(),
    PromptFragment.TELEGRAM_CHANNEL_CONTEXT: _build_telegram_channel_context_fragment(state),  # NEW
    PromptFragment.LIGHTHOUSE: lighthouse,
    # … rest unchanged …
}
```

**TTL choice:** 5min default `cache_control: {"type": "ephemeral"}` (no `ttl: "1h"` override).
- Justification: Telegram conversations span hours but cache benefit per single-turn already amortized. Choosing 5min over 1h saves 60% on cache-write cost (5m write = 1.25× base, 1h write = 2× base — Anthropic 2026-05).
- Break-even: 5m cache amortizes after 2 reads within 5min. Telegram multi-turn within 5min is common (user testing app interactively).
- 1h would cost 2× per write; only worthwhile if reads come >5min apart consistently. Defer that optimization to post-launch metric review.

**Forbidden in cache prefix (per Anthropic docs accessed 2026-05-01):**
- `tenant_id`, `tenant_slug`, `tenant_name` interpolated as Python f-string in the cacheable block — those go in `LIGHTHOUSE` (per-tenant cacheable, separate slot).
- `conversation_id`, `chat_id`, `update_id` — never enter the prefix.
- Timestamps, turn counters, random ids — forbidden.
- `{tenant_slug}` in the literal block above is a **literal** string the LLM emits in output (not Python-interpolated).

**Validation invariant (auditor enforced):**
Every LLM call inside `invoke_text` MUST log `cache_creation_input_tokens` + `cache_read_input_tokens` from the response. By turn 3 of a Telegram conversation, `cache_read_tokens > 0`; if `cache_read_tokens == 0` across iter ≥2 → silent invalidator in prefix → arch test FAIL.

**Threshold targeting (DATE-AWARE — Anthropic docs accessed 2026-05-01):**
- **Anthropic Opus 4.7 minimum cacheable prefix = 4096 tokens** (NOT 1024).
- **Anthropic Sonnet 4.6 minimum cacheable prefix = 2048 tokens.**
- OpenAI prompt cache threshold = 1024 tokens (different vendor).
- **PR.md target ≥1024 tokens is INCORRECT for Anthropic.** See § 16 Q3 — flagged to PM.
- Architect proposal: target **≥2048 tokens contiguous** (Sonnet floor) and recommend Sonnet for Telegram if cache ROI is the priority. If Opus is the active provider (`AI_PROVIDER_AGENT=openai/anthropic` resolves to Opus), threshold rises to ≥4096 tokens — the `_TELEGRAM_CHANNEL_CONTEXT_ES` block above is ~600 tokens by itself + `STATIC_IDENTITY` (~800) + `STATIC_TOOLS_HINT` (~200) + `MARKETING_KB_HINT` (~300) + `LIGHTHOUSE` (~tenant ~500) ≈ ~2400 tokens for Sonnet (PASS) but borderline for Opus (FAIL). Recommendation: builder adds **filler prose** to `TELEGRAM_CHANNEL_CONTEXT_ES` to bring per-block to ~1500 tokens so total cacheable ≥4096 even on Opus.

### 8.6 Checkpointer

UNCHANGED. Copilot graph doesn't use a checkpointer (state is reconstructed per turn from `copilot_conversations.messages`). Telegram inherits this. Recovery from mid-turn crash: ARQ retry replays the worker job with the same payload; conversation lookup-or-create is idempotent → next turn resumes cleanly.

### 8.7 Stream modes

NOT APPLICABLE for Telegram. `invoke_text` does NOT expose any stream mode externally. Internally `_run_graph_stream` uses `astream` (existing) — auditor verifies no behavior drift.

### 8.8 Observability writes (mandatory)

UNCHANGED architecture. The existing `obs.observe_turn(...)` context manager wraps `invoke_text`'s graph drive (see § 7.1 step 3) — `copilot_trace_event` + `copilot_llm_call` rows persist exactly as in `stream_chat`. Builder adds:

- One new event type `copilot_telegram_turn_completed` to structured log (already shown § 7.3 step 5) — NOT a new DB row.
- Cache-hit metric capture: `result.cache_read_tokens` + `result.cache_creation_tokens` flow from `obs` aggregator already populated by F8 prompt-cache integration. No new instrumentation.

**PII sanitization invariant:** `sanitize_payload(...)` already runs at recorder layer (rule `copilot-observability.md`). PR-2 must NOT bypass it; the worker logs `chat_id_prefix=_mask_chat_id(chat_id)` (PR-1 helper) for the structured log only.

**Cost target:** ≥60% `cache_read_input_tokens` hit rate by turn 3 of any Telegram conversation. Below that → arch fitness test FAIL (see § 14 telegram-cache-prefix test).

### 8.9 Eval goldens

NOT APPLICABLE — sales_agent only. Copilot quality goldens (`tests/quality/golden/`) are NOT modified; the new prompt slot is byte-identical when `channel=='web'` so existing goldens pass byte-for-byte.

### 8.10 RAG / Qdrant

UNCHANGED. `KnowledgeService` calls go via `knowledge_search` tool (already in `ALWAYS_AVAILABLE_GROUPS`). No telegram-specific Qdrant collection. D-PI5-008 explicitly defers vector retrieval until post-launch.

### 8.11 Skill decisions referenced

| Skill | Decision adopted |
|---|---|
| `copilot-expert` | (1) Re-use `system_prompt_layout.py` SSoT; new slot `TELEGRAM_CHANNEL_CONTEXT` placed between `MARKETING_KB_HINT` and `LIGHTHOUSE`. (2) `stream_chat` is streaming-only — sibling `invoke_text` method is the right pattern (NO new orchestrator class). (3) Anchor `[COPILOT-TELEGRAM-CHANNEL-CONTEXT]` registered (cap 36→37). (4) Trace recorder honest — `set_turn_error` propagates from `invoke_text` to `obs` exactly as in `stream_chat`. |
| `tessl__langgraph` | (1) `compiled_graph.ainvoke()` is preferred sync entry but copilot graph is `astream`-based — `invoke_text` consumes `_run_graph_stream` to keep parity. (2) Per-invocation context flows via `state["client_context"]["channel"]` — NO graph subclassing. (3) `recursion_limit` env-driven (`COPILOT_RECURSION_LIMIT`) already present — unchanged. |
| `tessl__graceful-degradation` | (1) Worker has 30s hard timeout on `invoke_text`. (2) Per-dependency error isolation in worker (lookup / orchestrator / format / bot send each have try/except + structlog warning + fallback message). (3) NEVER raises to ARQ (existing safety net preserved at line 156). (4) Idempotency at update_id (PR-1) covers retry semantics. |

---

## 9. Migration Notes

**NONE.** All schema work happened in PR-1. `alembic upgrade head` produces no PR-2 migration. Migration 114 pre-existing block (per RESULT.md) does not affect PR-2.

Smoke command (zero-rev verification): `cd backend && .venv/bin/alembic current` should print the same head before and after PR-2 merge.

---

## 10. File Structure

| Layer | Path | Action | LOC delta |
|---|---|---|---|
| domain | `backend/src/modules/copilot/domain/context_window.py` | EXTEND | +25 |
| domain | `backend/src/modules/copilot/api/dto.py` | EXTEND (`channel` field on `ClientContextDTO`) | +1 |
| application | `backend/src/modules/copilot/application/orchestrator/invoke_result.py` | NEW (`CopilotInvokeResult` DTO) | +25 |
| application | `backend/src/modules/copilot/application/orchestrator/chat.py` | EXTEND (`invoke_text` method + `_prepare_conversation` channel pass) | +90 |
| application | `backend/src/modules/copilot/application/orchestrator/system_prompt_layout.py` | EXTEND (`TELEGRAM_CHANNEL_CONTEXT` enum + tuple) | +3 |
| application | `backend/src/modules/copilot/application/orchestrator/graph.py` | EXTEND (`_build_telegram_channel_context_fragment` + dict entry) | +60 |
| application | `backend/src/modules/copilot/application/orchestrator/deep_agent.py` | EXTEND (`get_tools_for_context(context, channel=channel)` from state) | +3 |
| application | `backend/src/modules/copilot/application/memory/context_window_builder.py` | EXTEND (`for_channel` classmethod) | +10 |
| application | `backend/src/modules/copilot/application/memory/rolling_summarizer.py` | EXTEND (`for_channel` classmethod) | +10 |
| infrastructure | `backend/src/modules/copilot/infrastructure/repositories/conversation_repository.py` | EXTEND (`get_or_create_by_channel`) | +35 |
| infrastructure | `backend/src/modules/copilot/infrastructure/workers/telegram_worker.py` | REPLACE placeholder branch | -22 / +60 |
| tests | `backend/tests/modules/copilot/application/memory/test_context_window_telegram_config.py` | NEW | +60 |
| tests | `backend/tests/modules/copilot/application/orchestrator/test_invoke_text.py` | NEW | +90 |
| tests | `backend/tests/modules/copilot/application/orchestrator/test_telegram_channel_context_fragment.py` | NEW | +50 |
| tests | `backend/tests/modules/copilot/application/tools/test_registry_telegram_runtime_filter.py` | NEW (CONTEXT-BRIEF §7 confirms registry already supports channel param) | +60 |
| tests | `backend/tests/modules/copilot/infrastructure/repositories/test_conversation_repository_telegram_lookup.py` | NEW | +80 |
| tests | `backend/tests/modules/copilot/integration/test_telegram_end_to_end.py` | NEW (3 cases: linked happy / unlinked CTA / `/start TOKEN`) | +180 |
| arch | `backend/tests/architecture/test_copilot_telegram_separation.py` | EXTEND (+ `test_telegram_cache_prefix_meets_anthropic_threshold`) | +50 |
| arch | `backend/tests/architecture/test_copilot_anchors.py` | EXTEND (cap 36→37 + new anchor) | +2 |
| docs | `docs/pm-nico/current-state/copilot.md` | EXTEND (capability upgrade) | +15 (PM owns post-merge) |

**No frontend files. No DB migration files. No `requirements.txt` change.**

---

## 11. Cross-Cutting Concerns

| Concern | How PR-2 honors it |
|---|---|
| **Tenant isolation** | `get_or_create_by_channel` filters `tenant_id`. `invoke_text` propagates `tenant_id` through `state` and `obs`. Lookup never crosses tenants. |
| **Currency** | NOT APPLICABLE — no monetary fields. |
| **Master data (UTC, locale)** | `client_context.locale="es"` default. `created_at`/`updated_at` on conversations use `DateTime(timezone=True)` (PR-1 model). UTC store, FE NEVER displays Telegram dates yet. |
| **Spanish neutro LatAm** | All user-facing strings (worker fallback messages, `_TELEGRAM_CHANNEL_CONTEXT_ES`) use tuteo + tildes + ñ. **Output of orchestrator respects tenant voice (lighthouse)** per copilot voice rules — `_TELEGRAM_CHANNEL_CONTEXT_ES` does NOT prescribe voseo/tuteo to the LLM (line 30 says "respeta la voz del tenant"). |
| **PII** | `chat_id_prefix=_mask_chat_id(chat_id)` in worker logs (PR-1 helper). `sanitize_payload` runs in recorder layer for trace events. Worker NEVER logs `text` body — only `len(text)` aggregate. `response_model=` invariant: NOT APPLICABLE — no new HTTP route. |
| **Native-first dev** | Tests run `cd backend && .venv/bin/pytest tests/modules/copilot/...`. Builder NEVER `docker exec ... pytest`. |
| **Idempotency** | Worker handles re-delivery via `update_id` dedup (PR-1). `get_or_create_by_channel` is idempotent on the quadruple key. `invoke_text` is NOT idempotent across calls (each call is a new turn) — by design, mirroring `stream_chat`. |

---

## 12. Architecture Fitness Impact

Gates that **must remain green**:

```
backend/tests/architecture/test_copilot_anchors.py                          ← bump cap 36→37 in same commit, add anchor
backend/tests/architecture/test_no_new_copilot_module_imports.py            ← ratchet 22 frozen
backend/tests/architecture/test_copilot_provider_compliance.py
backend/tests/architecture/test_copilot_telegram_separation.py              ← +1 test (cache prefix threshold)
backend/tests/architecture/test_system_prompt_order.py                      ← updated for new slot in CACHEABLE_FRAGMENTS
backend/tests/architecture/test_brand_lighthouse_in_system_prompt.py        ← unchanged (LIGHTHOUSE position preserved)
backend/tests/architecture/test_channel_formatter_compliance.py             ← unchanged (channel registry unchanged)
backend/tests/architecture/test_workflow_compliance.py                      ← unchanged
backend/tests/architecture/test_extraction_orchestrator_inheritance.py      ← unchanged (no extraction work)
```

**Allowlists shrinking:** none. We add one new anchor — registry cap bumps but allowlist of `cross-module imports from copilot` does NOT grow (PR-2 is internal to copilot module + reads from shared/agent_observability already on the existing allowlist).

`test_system_prompt_order.py` MUST be updated in same commit because `CACHEABLE_FRAGMENTS` tuple grew by 1 — that test enforces the canonical order. Builder updates the expected-tuple in the test as part of "intentional change".

---

## 13. pm-nico/current-state Updates Required

Builder writes; `/pm` owns at close:

```diff
# docs/pm-nico/current-state/copilot.md

- ### Cap: Canal Telegram — DMs linkeados magic link
- - Estado: foundation live (LLM orchestrator hookup pendiente S2 PR-2)
- - Operable copilot: parcial (linking + tool subset registry; LLM responses = placeholder MVP)

+ ### Cap: Canal Telegram — DMs linkeados + copilot orchestrator real
+ - Estado: live (orchestrator real + memory cost-aware + cacheable prefix)
+ - Operable copilot: TOTAL (KB + tools + voz idénticos al copilot web; tools web-only redirigen via plantilla "editor web")
+ - Memoria: TELEGRAM_CONTEXT_WINDOW_CONFIG (3000 raw tokens, 15 msgs, summary 600 chars)
+ - Cache: TELEGRAM_CHANNEL_CONTEXT fragment cacheable Anthropic, target ≥60% cache_read en turno ≥3
+ - Latencia first-token p95 < 5s (medición S2)
+ - Lineage commit: <PR-2 hash> (PI-5, S2, 2026-05-XX)
```

---

## 14. Test Surfaces (TDD-mandatory)

RED order — builder writes RED first per layer, then GREEN.

### Domain (5 tests)
- `test_context_window_telegram_config.py`
  - `TELEGRAM_CONTEXT_WINDOW_CONFIG` is a `ContextWindowConfig` instance with the D-PI5-006 values byte-exact.
  - `get_context_window_config("telegram")` returns `TELEGRAM_CONTEXT_WINDOW_CONFIG`.
  - `get_context_window_config("web")` returns `DEFAULT_CONTEXT_WINDOW_CONFIG`.
  - `get_context_window_config(None)` returns `DEFAULT_CONTEXT_WINDOW_CONFIG`.
  - `get_context_window_config("unknown")` returns `DEFAULT_CONTEXT_WINDOW_CONFIG` (graceful default).

### Infrastructure (4 tests)
- `test_conversation_repository_telegram_lookup.py`
  - Hit existing row by quadruple key.
  - Create new row when absent; tenant_id, user_id, channel_type, channel_chat_id all persist.
  - `deleted_at IS NOT NULL` excludes from hit (creates new).
  - Cross-tenant isolation: tenant A lookup never returns tenant B row.

### Application (12 tests)
- `test_telegram_channel_context_fragment.py`
  - Returns `_TELEGRAM_CHANNEL_CONTEXT_ES` when `channel=="telegram"`.
  - Returns `""` when `channel=="web"`.
  - Returns `""` when `channel` key missing.
  - Returns `""` when `client_context` missing entirely.
  - Block contains `[COPILOT-TELEGRAM-CHANNEL-CONTEXT]` anchor.
  - Block contains NO timestamp, NO conv_id, NO tenant_id, NO Python f-string interpolation (regex assert: `\{tenant_slug\}` literal present, no other `\{...\}`).

- `test_invoke_text.py` (orchestrator non-streaming entry)
  - `invoke_text(channel="web", message="hi")` returns `CopilotInvokeResult` with non-empty `response_text`.
  - `invoke_text(channel="telegram", ...)` populates `state["client_context"]["channel"]="telegram"` (assert via mocked recorder capture).
  - `invoke_text` raises NEVER on orchestrator inner `Exception` — returns `error_kind != None` instead.
  - `invoke_text` populates `cache_read_tokens` + `cache_creation_tokens` from accumulated obs metrics.

- `test_registry_telegram_runtime_filter.py`
  - `get_tools_for_context(context, channel='telegram')` excludes navigation/guided/landing/offer_section tool names.
  - Includes 12+ telegram-allowed groups verbatim per D-PI5-024 list.
  - `channel='web'` (default) returns superset (no filter).
  - Unknown channel falls back to default (no telegram-specific filter applied).

### Architecture (1 NEW test)
- `test_copilot_telegram_separation.py::test_telegram_cache_prefix_meets_anthropic_threshold`
  - Build a minimal `CopilotState` with `client_context["channel"]="telegram"` + tenant minimal fixture (no studio_snapshot, no form_data, no inspirations) + lighthouse stub of fixed length (300 tokens).
  - Call `build_system_prompt(state)` and split on `CACHE_BOUNDARY_MARKER`.
  - Count tokens of cacheable head via `count_tokens()` (cl100k_base).
  - Assert `tokens_count >= 2048` (Sonnet 4.6 floor — see § 16 Q3 PM resolution required for Opus 4.7 ≥4096).
  - **If asserts FAIL:** builder adds filler prose to `_TELEGRAM_CHANNEL_CONTEXT_ES` until target met.

### Integration (3 cases)
- `test_telegram_end_to_end.py`
  - **Case 1 happy linked:** mocked Telegram update from linked chat_id → ARQ call → worker → mock conv lookup → mock `invoke_text` returning text "Hola, ¿en qué te ayudo?" → mock `format_for_channel_impl` returning same → mock `bot.send_message` called once with escaped MarkdownV2.
  - **Case 2 unlinked CTA:** mocked update from unknown chat_id → worker sends `_UNLINKED_CTA_TEMPLATE` (PR-1 path, untouched) → no orchestrator invoked, no conv_repo call.
  - **Case 3 `/start TOKEN`:** mocked update text `"/start <valid_token>"` → linking service consumes → confirmation sent → no orchestrator invoked.
  - All cases run against in-memory SQLite (`db_engine` fixture from `tests/conftest.py`) — register `CopilotConversationModel` + `CopilotChannelLinkModel` in `db_engine` per copilot-expert pattern.

**Mock pattern documented:**
- `httpx.AsyncClient` is patched at `infrastructure.channels.telegram_bot.httpx.AsyncClient` — Telegram Bot API never hit in tests.
- `LLMFactory.get_service()` is patched at `application.orchestrator.deep_agent` (existing copilot test pattern).
- ARQ enqueue is bypassed: tests call `process_copilot_telegram_turn(ctx, payload)` directly with synthetic ctx.

---

## 15. Research Notes

| Source | Accessed | Version / state | Key takeaway | Why this pattern |
|---|---|---|---|---|
| `https://platform.claude.com/docs/en/build-with-claude/prompt-caching` | **2026-05-01** (Step 0 captured date) | Anthropic public docs, 2026-04 baseline | Opus 4.7 minimum cacheable prefix = **4096 tokens**, Sonnet 4.6 = **2048 tokens**. Cache marker on last static block. Forbidden in prefix: timestamps, request ids, dynamic interpolation. 5min TTL = 1.25× write / 0.1× read; 1h TTL = 2× write / 0.1× read. Validate via `cache_read_input_tokens > 0` from response usage. | The PR.md target ≥1024 tokens is **OpenAI's threshold**, not Anthropic's. PR-2 must target ≥2048 (Sonnet floor) or ≥4096 (Opus floor) depending on `AI_PROVIDER_AGENT`. Builder verifies live provider and adds filler if needed. |
| `https://docs.langchain.com/oss/python/langgraph/workflows-agents` | **2026-05-01** | LangGraph oss public docs | Recommended sync invocation = `compiled_graph.ainvoke(state, config)`. Per-invocation context lives in initial state dict, NOT subclass. | We do NOT use `ainvoke` directly because copilot graph builds with `astream` for SSE — `invoke_text` consumes the same `_run_graph_stream` to keep parity. Per-invocation `channel` lives in `state["client_context"]["channel"]`. |
| `https://core.telegram.org/bots/api#markdownv2-style` | 2026-04-30 (PR-1, re-verified by reading shared/.../format.py) | Telegram Bot API current | MarkdownV2 must escape: `_*[]()~>#+-=\|{}.!`. PR-1 implemented `escape_markdown_v2` correctly. `parse_mode="MarkdownV2"` mandatory for safety. | PR-2 reuses PR-1's `escape_markdown_v2` + `format_for_channel_impl(channel_id="telegram")` — NO inline escaping. |
| `tessl__graceful-degradation` skill | 2026-05-01 | Tessl tile current | Iron rule: every external call needs a timeout + a fallback. Per-dependency isolation. Never retry payments / orchestrator-class non-idempotent ops with backoff. | 30s hard timeout on `invoke_text`. Friendly fallback message. Worker NEVER raises to ARQ. Per-dependency isolation in worker (lookup / orchestrator / format / send each have try/except). |
| `copilot-expert` skill (in-process) | 2026-05-01 | F8 cache-prefix architecture, post-redesign 2026-04 | `system_prompt_layout.py` is SSoT; `compose_system_prompt(fragments)` enforces canonical order; `CACHEABLE_FRAGMENTS` tuple is the audit log; new fragment = enum value + tuple insert + builder fn. | Followed verbatim. New `TELEGRAM_CHANNEL_CONTEXT` slot inserted between `MARKETING_KB_HINT` and `LIGHTHOUSE`. |

**Knowledge cutoff disclosure:** Opus 4.7 cutoff is January 2026; Anthropic prompt-caching minimum-token thresholds for Opus 4.7 / Sonnet 4.6 / Haiku 4.5 reflect the **live Anthropic docs as of 2026-05-01**. WebFetch on 2026-05-01 confirmed the 4096/2048/4096 floors — the architect did NOT rely on remembered (pre-cutoff) values.

---

## 16. Open Questions for PM

| # | Topic | Question | Architect recommendation |
|---|---|---|---|
| **Q1** | Memory builders not wired | Greps confirm `RollingSummarizer` and `ContextWindowBuilder` classes exist in `application/memory/` but **no orchestrator/api/worker call site invokes them today** (only the `synthesizer.py:12` reference is a docstring quote, not a call). They appear to be infrastructure provisioned but not yet hooked into `stream_chat`/`graph.py`. Is this intentional dead code awaiting a future wiring PR, or is the PR.md assumption "memory builders already drive the conversation window" incorrect? | **Builder MUST verify with `copilot-expert` invocation in builder phase.** If wiring is absent, PR-2 scope GROWS to wire `ContextWindowBuilder.for_channel(channel).build(...)` inside `_prepare_conversation` BEFORE the graph stream — that's the right place. Worker passes `channel="telegram"` → memory window respects D-PI5-006 config. **If wiring already exists in a path I missed,** PR-2 scope stays as drafted. PM: please confirm with Chris whether PR-2 owns first-time wiring or assumes preexisting wiring. Default architect assumption: **PR-2 owns first-time wiring** → scope holds because the LOC delta is small (~15 LOC inside `_prepare_conversation`). |
| **Q2** | `format_for_channel(channel='telegram')` already exists | Verified: `format_for_channel_impl(content, channel_id)` exists at `shared/agent_observability/channels/format_for_channel.py:83` and the `telegram` channel is registered with `parse_mode="MarkdownV2"`. PR.md asked the architect to flag if not. | **No new function needed.** Worker calls `format_for_channel_impl(content=result.response_text, channel_id="telegram")` directly. Resolved. |
| **Q3** | Cacheable prefix Anthropic threshold ≥1024 vs ≥4096 | PR.md targets ≥1024 tokens (OpenAI threshold). Anthropic Opus 4.7 = **4096**, Sonnet 4.6 = **2048**. Active provider depends on `AI_PROVIDER_AGENT` env var. | **PM decision needed before builder writes filler:** which provider drives `ModelRole.AGENT` in prod? If Anthropic Opus → builder targets 4096 (filler ~3500 extra tokens needed). If Sonnet → 2048 (filler ~500). If OpenAI → 1024 (no filler). Architect default: **target 2048 (Sonnet floor) so the contract is provider-agnostic above the OpenAI bar.** Builder pads `_TELEGRAM_CHANNEL_CONTEXT_ES` to ~1500 tokens of stable prose. Arch fitness test asserts ≥2048 tokens contiguous cacheable — Chris/PM upgrades to ≥4096 in a follow-up if Opus is selected. |
| **Q4** | Orchestrator entrypoint signature change (`channel` param) | `stream_chat` accepts `context: ClientContextDTO`. PR-2 adds `channel: str = "web"` as a sibling param to `invoke_text` AND adds `channel: str | None = None` to `ClientContextDTO`. The two are redundant — caller can pass via DTO or via direct kwarg. | **Architect chose redundancy on purpose for ergonomics:** worker passes `channel="telegram"` directly (less noise than constructing a DTO). Future callers may use the DTO field. `_prepare_conversation` resolves to ONE source: `context.channel or kwarg or "web"`. PM: OK to keep both paths? If PM prefers DTO-only, builder drops the kwarg from `invoke_text` and makes worker construct `ClientContextDTO(channel="telegram")`. Default: keep both. |
| **Q5** | UNIQUE constraint on `(tenant, user, channel_type, channel_chat_id)` | PR-1 added an index on these but NOT a UNIQUE constraint. PR-2's `get_or_create_by_channel` uses an optimistic SELECT-then-INSERT; rare race could create duplicates. Adding UNIQUE = new migration, which PR-2 explicitly excludes. | **Architect recommends deferring UNIQUE to a follow-up migration PR (S5 PR-5 candidate).** Race window is microseconds — production traffic at MVP volume (≤dozens of Telegram-active tenants) makes the race statistically improbable. PR-2 documents the gap in `RESULT.md` deuda técnica. PM: OK to defer? |
| **Q6** | `RollingSummarizer.SUMMARY_MAX_CHARS` configurable from `ContextWindowConfig` | Currently `RollingSummarizer.__init__(max_chars=400)` — NOT reading from `ContextWindowConfig.SUMMARY_MAX_CHARS`. The `for_channel` classmethod I propose reads the config, but the existing constructor signature stays. | **Architect proposal:** classmethod `for_channel` is the canonical builder. Direct `__init__(max_chars=N)` remains for tests. NO breaking change. PM: confirm. |

### Resoluciones PM (Opus 4.7, 2026-04-30, mind-set scale-first 1000+ + early-stage)

| # | Resolución | Justificación |
|---|---|---|
| **Q1** | **ACEPTAR architect default — PR-2 owns first-time wiring de `ContextWindowBuilder` + `RollingSummarizer` dentro `_prepare_conversation`** | Greps confirmaron ZERO call sites. ~15 LOC delta interno, NO scope creep. Memory deliverable de PR.md ya cubre wiring (deliverable 3). Builder cabletea ambos via `for_channel(channel)` classmethod. |
| **Q2** | RESOLVED por architect — reuso `format_for_channel_impl` shared, NO new function. | — |
| **Q3** | **Target ≥2048 tokens stable bytes (Sonnet floor + Kimi K2.6 ≥1024 baseline cubierto)**. Arch fitness `test_telegram_cache_prefix_meets_anthropic_threshold` asserts ≥2048. | Provider AGENT actual = Kimi K2.6 via LiteLLM (`AI_PROVIDER_AGENT=kimi`, `AI_MODEL_AGENT=kimi-k2.6` per `.env.example`). Kimi caching baseline ≥1024 tokens — 2048 cubre con margin. Si swap a Anthropic Opus 4.x en futuro PR (threshold 4096) → follow-up extiende fragment a 4096. Hoy 2048 = sweet spot scale-first (Kimi prod + Sonnet ready). |
| **Q4** | **ACEPTAR — keep both paths (DTO field + kwarg)**. `_prepare_conversation` dispatch: `channel = context.channel or kwarg or "web"`. | Ergonomía worker (kwarg directo) + futuro callers (DTO). Cero deuda — single source of truth en dispatch. |
| **Q5** | **ACEPTAR defer UNIQUE constraint a S5 PR-5 candidate**. PR-2 documenta gap en `RESULT.md` deuda. | Race window microsegundos, MVP volume (≤docenas tenants telegram-active). UNIQUE = nueva migration excluida de scope PR-2. Index ya cubre lookup performance. |
| **Q6** | **ACEPTAR — classmethod `for_channel` canonical, `__init__` legacy preservado para tests**. | Backward compat. NO breaking change. Tests existentes pass. |

**Verdict:** TODAS las open questions resueltas — builder puede arrancar SIN escalate adicional. Cero scope expansion, cero migration nueva, cero touch FE/módulos negocio.

---

## Existing systems audit (NO NEW LAYER rule)

### Source of evidence
- [x] CONTEXT-BRIEF.md § 7 + § 8 (Haiku context-builder pre-cocked, faithfulness flag = clean)
- [x] Self-run greps (Path B partial — to verify call-site coverage of `RollingSummarizer` / `ContextWindowBuilder` in orchestrator/api/workers; result: ZERO call sites — see Q1)
- [ ] Re-validation of CONTEXT-BRIEF flagged scan-incomplete (N/A — no flag)

### Audit cross-module ejecutado

CONTEXT-BRIEF §13 verbatim grep commands re-executed by architect (output identical to brief). Additional self-run commands:

```bash
# Verify memory primitives have NO active call sites in orchestrator/api/workers
grep -rn "RollingSummarizer\b\|ContextWindowBuilder\b" backend/src/modules/copilot/ \
  | grep -v "__pycache__\|memory/rolling_summarizer.py\|memory/context_window_builder.py"
# Result: ZERO call sites — primitives provisioned but not yet wired (Q1).

# Verify format_for_channel_impl exists in shared (PR.md doubt resolved)
grep -rn "format_for_channel_impl\|escape_markdown_v2" backend/src/shared/agent_observability/
# Result: format_for_channel_impl @ format_for_channel.py:83, escape_markdown_v2 @ format.py:260,
#         both exported via __init__.py:25,30-31 — Q2 RESOLVED, no new function needed.

# Verify channel registry has telegram entry with parse_mode="MarkdownV2"
grep -A 3 "_TELEGRAM = ChannelFormat" backend/src/shared/agent_observability/channels/format.py
# Result: id="telegram", max_chars=4096, markdown_allowed=True, parse_mode="MarkdownV2" — confirmed.

# Verify ToolGroupMeta.available_channels SSoT exists for telegram filtering
grep -n "ToolGroupMeta\|available_channels" backend/src/modules/copilot/application/tools/registry.py
# Result: ToolGroupMeta @353, TOOL_GROUP_META @366 with web-only entries (navigation/guided/landing/offer_section).
```

### Sistemas existentes encontrados — DECISIÓN

| Sistema | Path:LOC | Estado | Decisión PR-2 | Justificación |
|---|---|---|---|---|
| `ContextWindowConfig` + `DEFAULT_CONTEXT_WINDOW_CONFIG` | `domain/context_window.py:9-26` | active | **EXTEND** — add sibling `TELEGRAM_CONTEXT_WINDOW_CONFIG` instance + `get_context_window_config(channel)` dispatcher | Frozen dataclass already supports per-channel instances. NO new abstraction. |
| `ContextWindowBuilder` | `application/memory/context_window_builder.py:17-78` | active class, ZERO call sites | **EXTEND** — `for_channel(channel)` classmethod | Backward compat preserved; no signature change to `__init__` or `build()`. |
| `RollingSummarizer` | `application/memory/rolling_summarizer.py:43-93` | active class, ZERO call sites | **EXTEND** — `for_channel(channel, llm)` classmethod | Same as above. Tests still construct via `__init__(max_chars=N)`. |
| `system_prompt_layout.py` (`PromptFragment`, `CACHEABLE_FRAGMENTS`, `compose_system_prompt`) | `application/orchestrator/system_prompt_layout.py:49-108` | active SSoT | **EXTEND** — add `TELEGRAM_CHANNEL_CONTEXT` enum value + tuple position | Slot ordering invariant preserved; web bytes byte-identical. |
| `_build_*_fragment` family | `application/orchestrator/graph.py:625-760` | active builder layer | **EXTEND** — add `_build_telegram_channel_context_fragment(state)` matching the family signature | Conditional empty-string keeps web behavior. |
| `get_tools_for_context(context, channel)` + `ToolGroupMeta` | `application/tools/registry.py:353-402` | active SSoT (PR-1) | **EXTEND CALL SITE ONLY** — orchestrator passes `channel` from state | Registry signature unchanged; PR-1 already cemented `available_channels` SSoT. |
| `format_for_channel_impl` + `escape_markdown_v2` | `shared/agent_observability/channels/format_for_channel.py:83` + `format.py:260` | active shared utility | **REUSE READ-ONLY** | Worker imports + calls. NO new format adapter. |
| `CopilotOrchestrator` | `application/orchestrator/chat.py:586` | active class (streaming-only) | **EXTEND** — add sibling `invoke_text` method | NO new orchestrator class; shares `_prepare_conversation` + `_run_graph_stream` exactly. |
| `ConversationRepository` | `infrastructure/repositories/conversation_repository.py:27` | active (49+ methods) | **EXTEND** — add `get_or_create_by_channel` method | Tenant-scoped, follows existing kwargs-only pattern. |
| `process_copilot_telegram_turn` (worker) | `infrastructure/workers/telegram_worker.py:46` | active (PR-1 placeholder) | **REPLACE** placeholder branch (lines 133-154) with real orchestrator invocation | Same function, swap inner block. |
| `CopilotTelegramBot` | `infrastructure/channels/telegram_bot.py:38` | active (PR-1) | **REUSE READ-ONLY** | Bot adapter unchanged. |
| `ClientContextDTO` | `api/dto.py:10` | active | **EXTEND** — add `channel: str \| None = None` field | Backward compat (None default → web). |

**Verdict:** All 11 surfaces are EXTEND or REUSE. **Zero NEW abstractions, zero parallel layers, zero duplicate registries.** The single NEW file (`invoke_result.py`) is a Pydantic application-layer DTO of <30 LOC — auditor confirms it's a value object not a layer.

CONTEXT-BRIEF §8 mechanical recommendation = match. Faithfulness preserved.
