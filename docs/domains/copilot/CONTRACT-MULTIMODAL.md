# Contract: Copilot Multimodal Content

**Feature:** Rich multimodal messages (markdown, images, audios, videos, documents, tables, citations, quote-reply, cards) with a **channel-agnostic canonical block schema** that accepts WhatsApp tomorrow without refactor.

**Spec source:** user prompt — 2026-04-21.
**Related contract (already approved):** `docs/domains/copilot/CONTRACT.md` — data model v2 + agentic plugins + sidebar v2. NOT clobbered. This document is additive.
**Companion docs:** `INDEX.md`, `message-blocks.md`, `channel-adapters.md`, `sse-protocol.md`, `suggestions-engine.md`, `outbound-assets.md`.
**UI:** `UI-SPEC.md` (ux-designer owns).

**Status:** design — approved for parallel implementation after review.

This contract is the binding interface between backend and frontend sprints. Implementers do **not** redesign what already exists (assets service + storage, channel adapters, orchestrator skeleton, SSE framework, voice transcription endpoint) — they **extend** per the sections below.

**Multitenancy:** every payload carries `tenant_id` upstream (injected from `X-Tenant-ID`). Every new query filters by `tenant_id`. **No PII fields leave the backend** in any response DTO or block payload defined here.

**Non-goals** — see §14.

---

## 0. Key design decisions (summary)

| # | Decision | Rationale |
|---|---|---|
| D0.1 | Store `blocks[]` **inside each message dict** in the existing `copilot_conversations.messages` JSONB — not a new table | Backward-compat: 0 downtime, 0 backfill. Old readers see unchanged `role`+`content`; new readers prefer `blocks` when present. |
| D0.2 | Upload endpoint is a **thin proxy** that delegates to `AssetsService.upload_asset` | Zero storage duplication. Reuses R2 strategy, AI metadata pipeline, MIME detection, repository. Single SSoT for assets. |
| D0.3 | Outbound assets flow is **lookup-only** (tools `search_assets` + `get_asset`) — **assistant never generates media** | Prevents hallucinated URLs. Blocks always reference real `Asset.public_url`. Future generative media = a new tool with explicit scope. |
| D0.4 | Voice canonical flow: **new combined endpoint** `/voice/upload-and-transcribe` | Dual-mode (audio + transcript) must be atomic: split path leaves room for one-half-succeeds-one-half-fails. Old `/voice/transcribe` kept for backward-compat. |
| D0.5 | `BaseChannel` gains **`send_rich_message(msg)` with default impl** that falls back to plain `send_message` using a block-to-text flattener | Old adapters keep working untouched. New adapters override. No branching on channel type in orchestrator. |
| D0.6 | SSE v2 adds 3 block events (`block_start`, `block_delta`, `block_end`) that coexist with the legacy `text_chunk` during a migration window | Old FE keeps rendering text. New FE prefers block events. One flag flips when migration is done. |
| D0.7 | Smart chips are **stub-only** in this iteration: stable `Suggestion` interface + `useSuggestions` hook returning dummy data | Contract locks, real engine lands later with zero FE churn. |
| D0.8 | Anchor comments `[COPILOT-*]` in code → doc in `docs/domains/copilot/` | Discoverability. Ratchet arch test enforces that each anchor in code matches a §12 table row. |

---

## 1. Message Block Schema

Canonical block Union. Every block has: `type` discriminator, `id` (stable client-generated UUID), plus type-specific fields. All field names are `snake_case` in Python/JSON; TypeScript mirrors use the same names (no renaming) so FE and BE types are 1:1.

### 1.1 Python location

`backend/src/modules/copilot/domain/message_blocks.py` — **pure domain**, Pydantic v2 only. No SQLAlchemy, no FastAPI. `# [COPILOT-CANONICAL-BLOCKS] → docs/domains/copilot/message-blocks.md`.

### 1.2 TS mirror location

`frontend/src/features/copilot/types/message-blocks.ts`. Each block has a discriminated union `type` literal. Same field names as Python. Exported type: `MessageBlock`.

### 1.3 Common block envelope

```python
# domain/message_blocks.py
from __future__ import annotations
from typing import Annotated, Literal, Union
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class _BlockBase(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID                    # stable across streaming updates
    # NOTE: no `created_at` — the parent Message owns time.


# ── 1. text (markdown) ───────────────────────────────────────────────
class TextBlock(_BlockBase):
    type: Literal["text"] = "text"
    markdown: str                             # raw markdown; UTF-8
    # Streaming: emitted via block_delta events (§6)


# ── 2. image ──────────────────────────────────────────────────────────
class ImageBlock(_BlockBase):
    type: Literal["image"] = "image"
    asset_id: UUID                            # MUST exist in assets table, same tenant
    url: HttpUrl                              # snapshot of Asset.public_url at emit time
    mime: str                                 # e.g. "image/png"
    width: int | None = None
    height: int | None = None
    alt: str | None = None                    # accessibility + LLM context


# ── 3. audio ──────────────────────────────────────────────────────────
class AudioBlock(_BlockBase):
    """Voice-note / audio. Dual-mode MANDATORY: url + transcript together."""
    type: Literal["audio"] = "audio"
    asset_id: UUID
    url: HttpUrl
    mime: str                                 # "audio/webm", "audio/mpeg", ...
    duration_ms: int | None = None
    transcript: str                           # ALWAYS populated (empty string allowed if STT failed; see §9)
    transcript_language: str | None = None    # ISO 639-1 (e.g. "es")
    waveform: list[float] | None = None       # optional normalized 0..1 samples for UI


# ── 4. video ──────────────────────────────────────────────────────────
class VideoBlock(_BlockBase):
    type: Literal["video"] = "video"
    asset_id: UUID
    url: HttpUrl
    mime: str
    width: int | None = None
    height: int | None = None
    duration_ms: int | None = None
    poster_url: HttpUrl | None = None         # thumbnail


# ── 5. document ───────────────────────────────────────────────────────
class DocumentBlock(_BlockBase):
    type: Literal["document"] = "document"
    asset_id: UUID
    url: HttpUrl
    mime: str                                 # "application/pdf", "text/csv", ...
    filename: str
    size_bytes: int
    page_count: int | None = None             # PDFs
    preview_url: HttpUrl | None = None        # optional first-page thumbnail


# ── 6. table ──────────────────────────────────────────────────────────
class TableBlock(_BlockBase):
    type: Literal["table"] = "table"
    caption: str | None = None
    columns: list[str]                        # header labels
    rows: list[list[str]]                     # rows[i][j] is a string cell
    # Rule: len(row) == len(columns) for all rows (validator).


# ── 7. code ───────────────────────────────────────────────────────────
class CodeBlock(_BlockBase):
    type: Literal["code"] = "code"
    language: str                             # "python", "sql", "text", ...
    source: str
    filename: str | None = None               # optional file hint


# ── 8. citation ───────────────────────────────────────────────────────
class CitationBlock(_BlockBase):
    """RAG / knowledge-base source attribution. Emitted by search_knowledge_base."""
    type: Literal["citation"] = "citation"
    source: str                               # human-readable label e.g. "Doc: onboarding-playbook.md"
    snippet: str                              # quoted passage, ≤500 chars enforced by validator
    url: HttpUrl | None = None                # optional deep link
    score: float | None = None                # retrieval score 0..1


# ── 9. quote_reply ────────────────────────────────────────────────────
class QuoteReplyBlock(_BlockBase):
    """Reply pointing to a previous message in the same conversation."""
    type: Literal["quote_reply"] = "quote_reply"
    ref_message_id: UUID                      # target message in same conversation
    preview: str                              # ≤140 chars, truncated by composer
    ref_author_role: Literal["user", "assistant"]


# ── 10. card (wraps existing cards: proposal/alternatives/clarify/...) ─
class CardBlock(_BlockBase):
    """Thin wrapper around the existing UI action cards (see store/copilot-store.ts::UIAction)."""
    type: Literal["card"] = "card"
    card_kind: Literal[
        "proposal",
        "alternatives",
        "clarify",
        "checkpoint",
        "interview_complete",
        "metric_summary",
        "comparison",
        "checklist",
        "multi_option",
        "navigation",
    ]
    payload: dict                             # shape matches UIAction subset for card_kind
    status: Literal["pending", "resolved", "confirmed", "revising"] | None = None


# ── 11. tool_result ───────────────────────────────────────────────────
class ToolResultBlock(_BlockBase):
    """Transparent tool-call trace rendered compactly in UI."""
    type: Literal["tool_result"] = "tool_result"
    tool_name: str
    arguments: dict
    result_preview: str                       # truncated human-readable summary, ≤500 chars
    ok: bool


# ── Discriminated union ───────────────────────────────────────────────
MessageBlock = Annotated[
    Union[
        TextBlock,
        ImageBlock,
        AudioBlock,
        VideoBlock,
        DocumentBlock,
        TableBlock,
        CodeBlock,
        CitationBlock,
        QuoteReplyBlock,
        CardBlock,
        ToolResultBlock,
    ],
    Field(discriminator="type"),
]


BLOCK_TYPES: tuple[str, ...] = (
    "text", "image", "audio", "video", "document",
    "table", "code", "citation", "quote_reply", "card", "tool_result",
)
```

### 1.4 TypeScript mirror (skeleton — frontend implements verbatim)

```typescript
// frontend/src/features/copilot/types/message-blocks.ts
// [COPILOT-CANONICAL-BLOCKS] → docs/domains/copilot/message-blocks.md

export interface BlockBase {
  id: string; // UUID
}

export interface TextBlock extends BlockBase {
  type: "text";
  markdown: string;
}

export interface ImageBlock extends BlockBase {
  type: "image";
  asset_id: string;
  url: string;
  mime: string;
  width?: number;
  height?: number;
  alt?: string;
}

export interface AudioBlock extends BlockBase {
  type: "audio";
  asset_id: string;
  url: string;
  mime: string;
  duration_ms?: number;
  transcript: string;
  transcript_language?: string;
  waveform?: number[];
}

export interface VideoBlock extends BlockBase {
  type: "video";
  asset_id: string;
  url: string;
  mime: string;
  width?: number;
  height?: number;
  duration_ms?: number;
  poster_url?: string;
}

export interface DocumentBlock extends BlockBase {
  type: "document";
  asset_id: string;
  url: string;
  mime: string;
  filename: string;
  size_bytes: number;
  page_count?: number;
  preview_url?: string;
}

export interface TableBlock extends BlockBase {
  type: "table";
  caption?: string;
  columns: string[];
  rows: string[][];
}

export interface CodeBlock extends BlockBase {
  type: "code";
  language: string;
  source: string;
  filename?: string;
}

export interface CitationBlock extends BlockBase {
  type: "citation";
  source: string;
  snippet: string;
  url?: string;
  score?: number;
}

export interface QuoteReplyBlock extends BlockBase {
  type: "quote_reply";
  ref_message_id: string;
  preview: string;
  ref_author_role: "user" | "assistant";
}

export type CardKind =
  | "proposal" | "alternatives" | "clarify" | "checkpoint"
  | "interview_complete" | "metric_summary" | "comparison"
  | "checklist" | "multi_option" | "navigation";

export interface CardBlock extends BlockBase {
  type: "card";
  card_kind: CardKind;
  payload: Record<string, unknown>;
  status?: "pending" | "resolved" | "confirmed" | "revising";
}

export interface ToolResultBlock extends BlockBase {
  type: "tool_result";
  tool_name: string;
  arguments: Record<string, unknown>;
  result_preview: string;
  ok: boolean;
}

export type MessageBlock =
  | TextBlock | ImageBlock | AudioBlock | VideoBlock | DocumentBlock
  | TableBlock | CodeBlock | CitationBlock | QuoteReplyBlock
  | CardBlock | ToolResultBlock;
```

### 1.5 Per-block WhatsApp translatability

Every block MUST have a pre-planned translation to WhatsApp Media API. When WA channel activates (non-goal here), no schema change is needed. Table:

| Block | WA Media API mapping |
|---|---|
| `text` | `messages` (type=text) — markdown sanitized to WA subset (bold `*x*`, italic `_x_`). |
| `image` | `messages` (type=image) with `link=url` + `caption=alt` if present. |
| `audio` | `messages` (type=audio) with `link=url`. Transcript sent as separate text message when user prefers text (optional). |
| `video` | `messages` (type=video) with `link=url`. |
| `document` | `messages` (type=document) with `link=url`+`filename`. |
| `table` | Rendered as monospace text block (WA has no native table). Composer joins with `\|` separators. |
| `code` | Rendered as preformatted text (\`\`\`). |
| `citation` | Appended as footnote text after parent text block. |
| `quote_reply` | Native WA reply via `context.message_id` header. `preview` dropped. |
| `card` | Interactive `button`/`list` messages when `card_kind` supports (proposal → button; alternatives/multi_option → list). Otherwise rendered as text fallback. |
| `tool_result` | **Dropped** (internal trace, never shown outside web). |

Frontend renderer is WA-agnostic; the translator lives in the WA adapter (§5).

---

## 2. Message Entity

Messages remain **embedded in `copilot_conversations.messages` JSONB**, per existing schema (§3). A Message is a JSON object:

```python
# Shape of each entry in copilot_conversations.messages[]
{
    "id": "uuid-str",                       # NEW: stable message id (was implicit before)
    "role": "user" | "assistant" | "tool",  # existing
    "content": str,                         # existing: plain-text fallback (always filled — §3)
    "blocks": list[MessageBlock] | None,    # NEW: canonical rich content
    "status": "sending" | "streaming" | "sent" | "error",  # NEW
    "created_at": "ISO-8601 UTC",           # NEW: explicit per-message timestamp
    "tool_calls": [...],                    # existing (LangChain persistence)
    "tool_call_id": str | None,             # existing (tool role)
    "name": str | None,                     # existing (tool name)
    "tokens_used": int | None,              # NEW: optional assistant-only
    "metadata": dict | None                 # NEW: open bag (latency_ms, model, tier, etc.)
}
```

### 2.1 Status lifecycle (assistant messages)

```
sending  → streaming  → sent
             └── error ─┘
```

- `sending`: user hit send, BE not yet started streaming.
- `streaming`: SSE `status:streaming` received; blocks are being appended/updated.
- `sent`: SSE `status:done`. Persisted to DB.
- `error`: SSE `error`. `content` contains the human-readable error message in Spanish neutro LatAm. `blocks` kept as-is (partial).

### 2.2 Invariants

1. `content` is NEVER null. When only `blocks` exist, `content` = flattened plain text (concat of `TextBlock.markdown` + `AudioBlock.transcript` + table/citation text renditions, trimmed). This guarantees **legacy readers keep working** (display `content`) and WA/Telegram/email fallback has text always.
2. `id` is server-generated for assistant messages, client-generated for user messages. Always UUIDv4.
3. `blocks` on a user message represents uploads the user sent. On an assistant message represents what the assistant emitted.
4. `status` is only meaningful for assistant messages. Persisted as `"sent"` for user messages.

### 2.3 Pydantic domain entity

`backend/src/modules/copilot/domain/message.py` — new file.

```python
from __future__ import annotations
from datetime import datetime
from typing import Literal
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field

from src.modules.copilot.domain.message_blocks import MessageBlock

MessageRole = Literal["user", "assistant", "tool"]
MessageStatus = Literal["sending", "streaming", "sent", "error"]


class Message(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)

    id: UUID
    conversation_id: UUID
    role: MessageRole
    content: str                           # flattened plaintext; never null
    blocks: list[MessageBlock] | None = None
    status: MessageStatus = "sent"
    created_at: datetime                   # UTC
    tokens_used: int | None = None
    metadata: dict | None = None

    # Tool-role fields (existing legacy)
    tool_calls: list[dict] | None = None
    tool_call_id: str | None = None
    name: str | None = None
```

---

## 3. DB Migration

**Table target:** existing `copilot_conversations.messages` (JSONB array). There is **no** `copilot_messages` table in this codebase (the prompt wording was imprecise; verified via `grep -r "copilot_messages"` = 0 hits). Rich content lives inside each element of this array.

### 3.1 Schema change

**None at the SQL level.** `messages` is JSONB; we change its element shape. That's what JSONB is for. A forward-compat read adapter (§3.2) handles both shapes.

### 3.2 Idempotent migration (still ship an Alembic revision for telemetry / rollback anchor)

```python
# alembic/versions/20260422_1200_copilot_multimodal.py
"""copilot multimodal: blocks-capable message shape (no schema change).

Revision ID: 20260422_1200
Revises: <parent>
Create Date: 2026-04-22
"""

def upgrade() -> None:
    # No-op at SQL level. Marker revision so ops can correlate deploys.
    op.execute("""
        COMMENT ON COLUMN copilot_conversations.messages IS
        'JSONB array of Message objects. Shape v2 (2026-04-22):
         { id, role, content, blocks?, status, created_at, tool_calls?,
           tool_call_id?, name?, tokens_used?, metadata? }.
         Legacy v1 readers treat missing fields as null.';
    """)

    # Helpful partial index for counting dirty conversations during migration.
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_copilot_conv_has_blocks
          ON copilot_conversations ((messages::jsonb @? '$[*].blocks'))
          WHERE deleted_at IS NULL
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_copilot_conv_has_blocks")
```

### 3.3 Read adapter (backward-compat, MANDATORY)

`backend/src/modules/copilot/infrastructure/repositories/message_codec.py` — new file.

```python
from __future__ import annotations
from datetime import datetime
from uuid import UUID, uuid4

from src.modules.copilot.domain.message import Message
from src.modules.copilot.domain.message_blocks import TextBlock
from src.shared.domain.datetime_utils import utc_now


def decode_message(raw: dict, *, conversation_id: UUID) -> Message:
    """Read-side adapter. Accepts both v1 (legacy) and v2 shapes.

    v1 shape: {role, content, tool_calls?, tool_call_id?, name?}
    v2 shape: {id, role, content, blocks?, status, created_at, ...}

    When blocks missing, synthesize a single TextBlock from content.
    When content missing but blocks present, flatten blocks to content.
    """
    mid = UUID(raw["id"]) if "id" in raw else uuid4()
    role = raw.get("role", "assistant")
    content = raw.get("content") or ""
    blocks_raw = raw.get("blocks")
    status = raw.get("status", "sent")
    created = raw.get("created_at")
    created_dt = (
        datetime.fromisoformat(created) if isinstance(created, str) else utc_now()
    )

    blocks = None
    if blocks_raw is None and content:
        # Synthesize from legacy content so downstream code always sees blocks
        # if the caller opts into v2 rendering.
        blocks = [TextBlock(id=uuid4(), markdown=content)]
    elif blocks_raw is not None:
        blocks = blocks_raw  # Pydantic will validate via Message model

    return Message.model_validate(
        {
            "id": mid,
            "conversation_id": conversation_id,
            "role": role,
            "content": content or _flatten_blocks(blocks_raw) if blocks_raw else "",
            "blocks": blocks,
            "status": status,
            "created_at": created_dt,
            "tool_calls": raw.get("tool_calls"),
            "tool_call_id": raw.get("tool_call_id"),
            "name": raw.get("name"),
            "tokens_used": raw.get("tokens_used"),
            "metadata": raw.get("metadata"),
        },
    )


def encode_message(msg: Message) -> dict:
    """Write-side adapter. Always emits v2 shape.

    New messages ALWAYS carry blocks[]. Legacy code paths that persisted via
    `role+content` dicts must be migrated to this encoder before cleanup.
    """
    return msg.model_dump(mode="json", exclude_none=True, by_alias=False)


def _flatten_blocks(blocks: list[dict] | None) -> str:
    if not blocks:
        return ""
    parts: list[str] = []
    for b in blocks:
        t = b.get("type")
        if t == "text":
            parts.append(b.get("markdown", ""))
        elif t == "audio":
            parts.append(b.get("transcript", ""))
        elif t == "citation":
            parts.append(f'"{b.get("snippet", "")}" — {b.get("source", "")}')
        elif t == "table":
            cols = " | ".join(b.get("columns", []))
            rows = "\n".join(" | ".join(r) for r in b.get("rows", []))
            parts.append(f"{cols}\n{rows}")
        elif t == "code":
            parts.append(f"```{b.get('language','')}\n{b.get('source','')}\n```")
        elif t == "quote_reply":
            parts.append(f"> {b.get('preview','')}")
        # image/video/document/card/tool_result contribute no plain-text body.
    return "\n\n".join(p for p in parts if p)
```

### 3.4 Write path

All new code paths persisting messages MUST call `encode_message()`. The existing `CopilotOrchestrator._serialize_messages` / `_deserialize_messages` become callers of this codec instead of duplicating serialization. `# [COPILOT-MESSAGE-CODEC] → docs/domains/copilot/message-blocks.md`.

### 3.5 Backfill

**Not part of this iteration.** Old messages keep working via read adapter. Future backfill (optional) would iterate conversations, synthesize blocks per message, rewrite `messages` JSONB. Deferred — see §14.

---

## 4. `OutgoingMessage` Extension

Location: `backend/src/shared/domain/messages.py`.

**Extension strategy:** add an optional `blocks` list. Backward-compat preserved — old callers ignore the new field.

```python
# shared/domain/messages.py  (diff)
from typing import Any
from src.shared.domain.base_entity import BaseEntity


class IncomingMessage(BaseEntity):
    user_id: str
    text: str
    channel_type: str
    metadata: dict[str, Any] = {}


class OutgoingMessage(BaseEntity):
    user_id: str
    text: str                                 # existing: required, becomes "flattened fallback"
    channel_type: str | None = None
    metadata: dict[str, Any] = {}
    # NEW — list of MessageBlock payloads (raw dicts; validated at adapter layer).
    # None for legacy senders; non-null for copilot/WA/rich senders.
    blocks: list[dict] | None = None          # [COPILOT-OUTGOING-BLOCKS]
```

**Validator:** when `blocks` is set, `text` MUST equal the flattened output of those blocks (invariant 2.2.1). Enforced by a Pydantic `model_validator` in a follow-up (non-blocking).

---

## 5. Channel Adapter Extension

Location: `backend/src/shared/infrastructure/channels/base.py`.

**Decision (D0.5):** Add a new method `send_rich_message(msg)` to the `BaseChannel` ABC with a **default implementation** that flattens blocks to text and delegates to `send_message`. This is the **chosen** option.

### 5.1 Chosen approach — new method with default fallback

```python
# shared/infrastructure/channels/base.py  (diff)
from abc import ABC, abstractmethod
from typing import Any

from src.shared.domain.messages import IncomingMessage, OutgoingMessage


class BaseChannel(ABC):

    @abstractmethod
    def normalize_payload(self, payload: dict[str, Any]) -> IncomingMessage | None: ...

    @abstractmethod
    async def send_message(self, message: OutgoingMessage) -> dict[str, Any]: ...

    @abstractmethod
    async def set_typing_status(self, user_id: str) -> None: ...

    # NEW — orchestrator calls this. Default falls back to text-only send_message.
    # Rich channels override with block-aware senders.
    async def send_rich_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Send a rich multimodal message. Override for native block support.

        Default implementation sends `message.text` via send_message, dropping
        blocks (which is safe because OutgoingMessage invariant 4.0 guarantees
        `text` is the flattened plain-text equivalent).

        [COPILOT-CHANNEL-RENDERER] → docs/domains/copilot/channel-adapters.md
        """
        return await self.send_message(message)
```

### 5.2 Alternatives considered

| Alternative | Pros | Cons | Verdict |
|---|---|---|---|
| **A. Extend `send_message` with optional `blocks`** | 1 method. | Breaks LSP for existing adapters that only handle text. No type-safe signal to dispatcher about "this channel supports rich". Harder to arch-test. | Rejected. |
| **B. New method `send_rich_message` with default fallback (chosen)** | LSP preserved. Adapters opt-in. Dispatcher always calls `send_rich_message`; text-only channels degrade via default. Easy arch test: "every new rich sender overrides this method". | Adds one method to ABC. | **Chosen.** |
| **C. New port `RichChannel` separate from `BaseChannel`** | Clear separation. | Channel resolver has to choose between two ports — duplicates branching. Orchestrator needs two adapters for same channel during migration. | Rejected (over-engineered). |

### 5.3 Implications for WhatsApp tomorrow

When WA channel activates:

1. `WhatsAppProvider` (in `connections/infrastructure/channels/whatsapp/`) overrides `send_rich_message`.
2. It iterates `message.blocks` and issues one WA Media API call per block per the mapping in §1.5.
3. `quote_reply` is combined with the next non-quote block via `context.message_id`.
4. Default `send_message` still routes plain text for non-copilot callers (sales_agent legacy).

No refactor to orchestrator, no change to `OutgoingMessage`, no change to channel resolver.

---

## 6. SSE v2 Protocol

Location: `backend/src/modules/copilot/api/dto.py` (extend `SSEEventType`), `frontend/src/features/copilot/api/copilot-api.ts` (mirror).
`# [COPILOT-SSE-V2] → docs/domains/copilot/sse-protocol.md`.

### 6.1 Event inventory (v1 + v2, full)

| Event | Generation | Payload | Lifecycle | Compat |
|---|---|---|---|---|
| **Legacy (v1, keep emitting during migration)** | | | | |
| `status` | orchestrator | `{state: "thinking" \| "streaming" \| "done"}` | any | v1+v2 |
| `text_chunk` | LLM stream | `{content: str}` | before `block_*`, same content | v1 only after migration flag |
| `tool_start` | LangGraph | `{tool: str, args: dict}` | any | v1+v2 |
| `tool_result` | LangGraph | `{tool: str, result: str}` | after `tool_start` | v1+v2 |
| `ui_action` | tool output | legacy UIAction dict | any | v1+v2 (becomes CardBlock in v2) |
| `proposal` | mutation tool | `{updates: ProposalUpdate[], ...}` | any | v1+v2 (becomes CardBlock in v2) |
| `confirmation_required` | mutation tool | `{...}` | any | v1+v2 |
| `tier_decision` | router | `{tier, reason, confidence}` | once, first | v1+v2 |
| `mutation_applied` | mutation tool | `{mutation_id, ...}` | any | v1+v2 |
| `done` | orchestrator | `{conversation_id, message_id}` | last | v1+v2 |
| `error` | orchestrator | `{message: str}` | any | v1+v2 |
| **New (v2)** | | | | |
| `message_start` | orchestrator | `{message_id, role: "assistant", created_at}` | first after `status:streaming` | v2 |
| `block_start` | LLM stream / tool | `{message_id, block_id, type: BLOCK_TYPE, index: int, partial: MessageBlock}` | any after `message_start` | v2 |
| `block_delta` | LLM stream | `{message_id, block_id, delta: {markdown: str}}` (currently only for `text` blocks) | between `block_start` and `block_end` for same `block_id` | v2 |
| `block_end` | LLM stream / tool | `{message_id, block_id, final: MessageBlock}` | finalizes a block | v2 |
| `message_end` | orchestrator | `{message_id, status, tokens_used?, blocks: MessageBlock[]}` | once, before `done` | v2 |

### 6.2 Streaming semantics

- **Text blocks** stream via `block_start` (empty markdown) → N × `block_delta` (append to markdown) → `block_end` (final markdown).
- **Non-text blocks** (image/audio/video/document/table/citation/card/tool_result/quote_reply) emit **one `block_start` with the full payload, no deltas, then `block_end` with same payload**. These are atomic.
- `block_end` always carries the final `MessageBlock` (full, validated) so FE can cache/persist without reconstructing.
- `message_end.blocks` is the **ordered** final list. FE uses it to reconcile any dropped `block_*` events (network hiccup).

### 6.3 Backward compatibility window

Orchestrator emits **both** `text_chunk` AND `block_start/delta/end` for text content during migration window. Feature flag `COPILOT_EMIT_LEGACY_SSE=true` (default) toggles legacy.

FE with v2 renderer: prefers `block_*` events, ignores `text_chunk` (they duplicate).
FE with v1 renderer: ignores unknown `block_*` events, consumes `text_chunk`.

Cleanup step (§13): flip flag to `false`, then remove `text_chunk` emission.

### 6.4 Payload examples

```json
event: message_start
data: {"message_id":"9f1...","role":"assistant","created_at":"2026-04-21T15:30:01.234Z"}

event: block_start
data: {"message_id":"9f1...","block_id":"aa1...","type":"text","index":0,
       "partial":{"id":"aa1...","type":"text","markdown":""}}

event: block_delta
data: {"message_id":"9f1...","block_id":"aa1...","delta":{"markdown":"Claro, "}}

event: block_delta
data: {"message_id":"9f1...","block_id":"aa1...","delta":{"markdown":"aquí va tu propuesta..."}}

event: block_end
data: {"message_id":"9f1...","block_id":"aa1...",
       "final":{"id":"aa1...","type":"text","markdown":"Claro, aquí va tu propuesta..."}}

event: block_start
data: {"message_id":"9f1...","block_id":"bb2...","type":"citation","index":1,
       "partial":{"id":"bb2...","type":"citation","source":"Doc: brand-book.md",
                  "snippet":"La voz de la marca es cálida y cercana.","score":0.84}}

event: block_end
data: {"message_id":"9f1...","block_id":"bb2...","final":{...same as above...}}

event: message_end
data: {"message_id":"9f1...","status":"sent","tokens_used":142,
       "blocks":[{...},{...}]}

event: done
data: {"conversation_id":"c0a...","message_id":"9f1..."}
```

---

## 7. Upload Endpoint

### 7.1 Route

```
POST /api/v1/copilot/media/upload
```

Location: `backend/src/modules/copilot/api/media.py` — **new file**.
`# [COPILOT-MEDIA-UPLOAD] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §7`.

### 7.2 Auth

Clerk Bearer + `X-Tenant-ID`. Reuses `get_current_user` + `get_tenant_context` deps. Rate-limited via existing `check_rate_limit` with scope `"copilot-media"`.

### 7.3 Request

`multipart/form-data`:

| Field | Type | Required | Validation |
|---|---|---|---|
| `file` | `UploadFile` | yes | ≤25 MB (configurable `COPILOT_MEDIA_MAX_BYTES`). MIME sniffed server-side. |
| `kind` | `str` | no | One of `"image"`, `"audio"`, `"video"`, `"document"`. If omitted, inferred from MIME. |
| `description` | `str` | no | Passed through to `AssetsService.upload_asset` (≤240 chars). |

### 7.4 Allowed MIME types

| kind | MIME whitelist |
|---|---|
| image | `image/png`, `image/jpeg`, `image/webp`, `image/gif`, `image/svg+xml` |
| audio | `audio/webm`, `audio/mpeg`, `audio/mp4`, `audio/ogg`, `audio/wav` |
| video | `video/mp4`, `video/webm`, `video/quicktime` |
| document | `application/pdf`, `text/plain`, `text/csv`, `text/markdown`, `application/vnd.openxmlformats-officedocument.wordprocessingml.document`, `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`, `application/msword`, `application/vnd.ms-excel` |

Anything else → `415 Unsupported Media Type`.

### 7.5 Delegation (the key rule — DO NOT DUPLICATE STORAGE)

```python
# api/media.py  (pseudocode — NOT implementation)
service = AssetsService(db)              # existing service; same instance the assets module uses
asset = service.upload_asset(
    tenant_id=current_user.tenant_id,
    file_obj=file.file,
    filename=file.filename,
    mime_type=file.content_type,
    description=description,
    offer_id=None,                       # copilot uploads are not offer-scoped
    background_tasks=background_tasks,   # AI metadata pipeline continues in background
)
```

**Reused automatically:**
- R2 / local storage strategy (`settings.STORAGE_PROVIDER`).
- MIME auto-detection fallback.
- `Asset` row persisted with `tenant_id`, `public_url`, `storage_path`, `status=PROCESSING`.
- Background AI metadata extraction (colors, description for images).
- Existing arch tests for assets module.

### 7.6 Response DTO

```python
# api/media_dto.py — new file
from uuid import UUID
from pydantic import BaseModel, ConfigDict, HttpUrl

class MediaUploadResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    asset_id: UUID
    public_url: HttpUrl
    mime: str
    size_bytes: int
    kind: Literal["image", "audio", "video", "document"]
    # No PII. No filename echoed back (only the UUID is canonical).
```

| HTTP | When |
|---|---|
| `200 OK` | Uploaded, Asset row created (status=`processing`). |
| `400 Bad Request` | Missing file, empty file, invalid `kind`. |
| `413 Payload Too Large` | Exceeds `COPILOT_MEDIA_MAX_BYTES`. |
| `415 Unsupported Media Type` | MIME not in whitelist for inferred/declared `kind`. |
| `401 / 403` | Auth / tenant errors (handled by deps). |
| `429 Too Many Requests` | Rate limit. |

### 7.7 Tenant isolation

`tenant_id` = `current_user.tenant_id`. `AssetsService` already filters by `tenant_id` in all reads. Uploaded asset is visible only inside the tenant.

### 7.8 Client flow (frontend)

```ts
// features/copilot/api/media-api.ts  (new)
// [COPILOT-MEDIA-UPLOAD]
export async function uploadCopilotMedia(
  file: File,
  kind?: "image" | "audio" | "video" | "document",
  description?: string,
): Promise<MediaUploadResponse> {
  const fd = new FormData();
  fd.append("file", file);
  if (kind) fd.append("kind", kind);
  if (description) fd.append("description", description);
  return fetchClient.post("/copilot/media/upload", fd);
}
```

On success, the chat composer builds a block (`ImageBlock` / `AudioBlock` / `VideoBlock` / `DocumentBlock`) referencing `asset_id` + `url` and appends it to the outbound user `Message.blocks[]`.

---

## 8. Outbound Assets Tools

Assistant-side tools that LET the LLM REFERENCE existing assets. **The assistant never generates media.**
`# [COPILOT-OUTBOUND-ASSETS] → docs/domains/copilot/outbound-assets.md`.

### 8.1 `search_assets`

Location: `backend/src/modules/copilot/application/tools/assets_tools.py` — new file, registered in `TOOL_GROUPS["assets"]`.

**LangChain tool signature (for the LLM):**

| Field | Type | Description |
|---|---|---|
| `query` | `str` | Free-text search over `Asset.user_description`, `ai_description`, `filename`, `ai_metadata.tags`. |
| `kind` | `"image" \| "audio" \| "video" \| "document" \| null` | Optional filter. |
| `offer_id` | `UUID \| null` | Optional scope to a specific offer. |
| `limit` | `int` | 1..20, default 5. |

**Returns (to LLM):** JSON array of `AssetRef`:

```json
{
  "asset_id": "uuid",
  "public_url": "https://...",
  "mime": "image/png",
  "kind": "image",
  "filename": "hero.png",
  "description": "Flyer hero image"
}
```

The tool **never returns** `storage_path` (internal), nor any cross-tenant data (tenant filter enforced in repo).

### 8.2 `get_asset`

| Field | Type | Description |
|---|---|---|
| `asset_id` | `UUID` | Required. |

Returns one `AssetRef` or `{"error": "not_found"}`. Tenant-scoped.

### 8.3 LLM prompt guidance (system-prompt skill snippet)

```
When the user asks for an image/audio/video/document you have previously
uploaded, call search_assets first with a descriptive query. Do NOT invent
URLs. Use only asset_id + public_url returned by the tool. Emit an
ImageBlock / AudioBlock / VideoBlock / DocumentBlock referencing those.
```

### 8.4 Tool → Block emission

Tool output is `AssetRef`. The agent composes the appropriate block type (`ImageBlock` etc.), wraps it in `block_start` + `block_end` SSE events, and includes it in `message_end.blocks`. No streaming deltas for non-text blocks (§6.2).

### 8.5 Route binding

`ROUTE_TOOL_MAP` gets a new group `"assets"` added to routes where the assistant should have access:

```python
# application/tools/registry.py  (diff)
TOOL_GROUPS["assets"] = ASSETS_TOOLS

# Add "assets" to routes that may reference tenant media:
ROUTE_TOOL_MAP = {
    "brand-studio": [..., "assets"],
    "offer-studio": [..., "assets"],
    "landing-studio": [..., "assets"],
    "assets": [..., "assets"],
    "*": [..., "assets"],  # globally available
}
```

### 8.6 Guardrails

- Tools filter by `tenant_id` from `get_current_user().tenant_id`. Arch test: `test_assets_tools_tenant_scoped`.
- `get_asset` returns 404-shaped error if asset belongs to a different tenant (never "not authorized", to avoid leaking existence).
- Tool results capped at `limit=20` to avoid token bloat.
- `Asset.deleted_at`-filtered reads only.

---

## 9. Voice Dual-Mode

`# [COPILOT-VOICE-DUAL-MODE] → docs/domains/copilot/CONTRACT-MULTIMODAL.md §9`.

### 9.1 Decision (D0.4): new combined endpoint

```
POST /api/v1/copilot/voice/upload-and-transcribe
```

Location: `backend/src/modules/copilot/api/voice.py` (extend). Existing `/voice/transcribe` stays for backward-compat (old clients that only need STT).

### 9.2 Rationale — why not split

| Split flow (two calls) | Combined flow (one call) |
|---|---|
| FE: POST `/voice/transcribe` + POST `/media/upload`, then compose block. | FE: POST `/voice/upload-and-transcribe`, receive full `AudioBlock`. |
| 2 requests, 2 round trips, 2 failure modes. If STT succeeds but upload fails → user sees transcript but no audio; block can't be built. Partial success is messy. | 1 request, atomic. BE runs STT + storage in the same handler. On any failure, neither is persisted. |
| Two log lines per voice message, correlation is manual. | Single log line with both `asset_id` and `transcript_length`. |
| STT and storage might run concurrently but FE can't. | BE runs them concurrently via `asyncio.gather`, FE sees lower latency. |

**Chosen: combined.** Keep split endpoints as escape hatches (existing `/voice/transcribe` remains for other callers, new `/media/upload` remains for non-audio).

### 9.3 Request

Same as `/voice/transcribe`: `multipart/form-data` with `file: UploadFile`.

### 9.4 Response DTO

```python
# api/voice_dto.py  (extend)
class VoiceUploadAndTranscribeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    block: AudioBlock          # complete block ready to include in message.blocks
```

### 9.5 Handler pseudo-flow

```python
@router.post("/voice/upload-and-transcribe", response_model=VoiceUploadAndTranscribeResponse)
async def voice_upload_and_transcribe(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> VoiceUploadAndTranscribeResponse:
    audio_bytes = await file.read()
    mime = file.content_type or "audio/webm"

    # Fan out in parallel — neither depends on the other
    transcriber = WhisperTranscriber()
    assets = AssetsService(db)

    # We need the raw bytes for STT and a file-like for storage → seek to 0 after read
    file.file.seek(0)

    transcribe_task = asyncio.create_task(transcriber.transcribe(audio_bytes, mime))
    asset = assets.upload_asset(
        tenant_id=user.tenant_id,
        file_obj=file.file,
        filename=file.filename or f"voice-{uuid.uuid4()}.webm",
        mime_type=mime,
        background_tasks=background_tasks,
    )
    transcription = await transcribe_task

    block = AudioBlock(
        id=uuid.uuid4(),
        asset_id=asset.id,
        url=asset.public_url,
        mime=mime,
        duration_ms=int(transcription.duration_seconds * 1000) if transcription.duration_seconds else None,
        transcript=transcription.text,
        transcript_language=transcription.language,
    )
    return VoiceUploadAndTranscribeResponse(block=block)
```

### 9.6 Failure modes

| Case | Response |
|---|---|
| STT fails but upload succeeds | 200 with `block.transcript = ""`, `transcript_language = null`. UI shows "Transcripción no disponible" next to the audio control. User can still play it. |
| Upload fails | 502 (storage error). FE surfaces error. No partial state committed to chat. |
| Both fail | 502 same as above. |
| Audio too long (>2 min default, configurable) | 413. |

The invariant **"audio block always has both url and transcript fields present"** holds — `transcript` may be empty string, never missing.

---

## 10. Citations + Quote-Reply

### 10.1 Citations

`# [COPILOT-CITATION-BLOCK] → docs/domains/copilot/message-blocks.md`.

**Emitted by:** `search_knowledge_base` tool (existing, lives in `application/tools/knowledge_tools.py`).

**Flow:**
1. LLM calls `search_knowledge_base(query)`.
2. Tool returns list of RAG hits (existing `SearchResultItem`: content, score, metadata).
3. Orchestrator interceptor (new, in `orchestrator/chat.py`) detects `search_knowledge_base` tool results, wraps each hit in a `CitationBlock`, and streams them as `block_start`/`block_end` events **after** the current text block finishes.
4. Persisted in `message.blocks`.

**Mapping — `SearchResultItem` → `CitationBlock`:**

| RAG field | Citation field |
|---|---|
| `metadata.title` or `metadata.source` | `source` |
| `content` (truncated to 500 chars) | `snippet` |
| `metadata.url` | `url` |
| `score` | `score` |

### 10.2 Quote-reply

`# [COPILOT-QUOTE-REPLY] → docs/domains/copilot/message-blocks.md`.

**Produced by:** user action in chat UI ("Reply" button on a message).

**Flow:**
1. User clicks "Reply to this" on message `m_ref`.
2. FE builds a `QuoteReplyBlock` with `ref_message_id=m_ref.id`, `preview = flatten(m_ref).slice(0,140)`, `ref_author_role = m_ref.role`.
3. Block is prepended to the outbound user message's `blocks[]`.
4. Assistant receives blocks via normal chat payload and can resolve `ref_message_id` against the same conversation's history for context.

**Transport-neutral:** web UI renders as indented quote box. WA adapter maps to native reply (see §1.5). Telegram adapter (future) same — Telegram has `reply_to_message_id`.

**Server validation:** `ref_message_id` MUST exist in the same `conversation_id` — arch-tested via integration test, not enforced at block-validation time (blocks are dumb payloads; orchestrator validates on receipt).

---

## 11. Smart Chips Contract (stub)

`# [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md`.

**Scope this iteration:** contract + UI stub. No real engine.

### 11.1 TypeScript interface (stable)

```typescript
// frontend/src/features/copilot/types/suggestions.ts
export interface Suggestion {
  id: string;                           // stable, UUID or "stub-*"
  label: string;                        // user-visible chip text (Spanish neutro LatAm)
  prompt: string;                       // filled into the input on click
  confidence?: number;                  // 0..1, future ranking; currently undefined
  category?: "followup" | "action" | "clarify" | "nav";
}

export interface SuggestionsPayload {
  conversation_id: string;
  suggestions: Suggestion[];            // ordered; max 5 chips shown
  generated_at: string;                 // ISO UTC
}
```

### 11.2 Hook

```typescript
// frontend/src/features/copilot/hooks/use-suggestions.ts
// [COPILOT-SUGGESTIONS-ENGINE] → docs/domains/copilot/suggestions-engine.md
//
// Stub: returns hardcoded dummy chips based on current_route.
// Real engine lands in a follow-up; FE surface is frozen here.
export function useSuggestions(conversationId: string | null): {
  suggestions: Suggestion[];
  isLoading: boolean;
  refresh: () => void;
}
```

**Stub behavior:** returns 3 hardcoded chips derived from `currentRoute` (e.g., on `brand-studio`: "Audita mi identidad", "Mejora mi tagline", "Revisa mi tono de voz"). Simulates 200ms latency.

### 11.3 Backend contract (future, not built now)

When real engine lands, it will expose:

```
GET /api/v1/copilot/conversations/{conversation_id}/suggestions
Response: SuggestionsPayload
```

Implementation options (picked later, see `suggestions-engine.md`):
- Heuristic BE (rule-based on last messages + route + procedure_state).
- Tool-driven (LLM emits `Suggestion[]` as part of `message_end.metadata`).
- New SSE event `suggestions_ready` pushed after `done`.

All three fit the above hook with no FE change.

---

## 12. Anchor Comment Convention

**Rule:** every extension point in the codebase MUST carry a `# [COPILOT-*]` comment that maps to a doc (or doc section). Arch test `test_copilot_anchors_have_docs` enforces: for each anchor name in source, there is a matching row in the table below.

### 12.1 Canonical anchor table

| Anchor | File (primary) | Doc target |
|---|---|---|
| `[COPILOT-CANONICAL-BLOCKS]` | `backend/src/modules/copilot/domain/message_blocks.py` `frontend/src/features/copilot/types/message-blocks.ts` | `docs/domains/copilot/message-blocks.md` |
| `[COPILOT-MESSAGE-CODEC]` | `backend/src/modules/copilot/infrastructure/repositories/message_codec.py` | `docs/domains/copilot/message-blocks.md` §3 |
| `[COPILOT-OUTGOING-BLOCKS]` | `backend/src/shared/domain/messages.py` | `docs/domains/copilot/CONTRACT-MULTIMODAL.md §4` |
| `[COPILOT-CHANNEL-RENDERER]` | `backend/src/shared/infrastructure/channels/base.py` | `docs/domains/copilot/channel-adapters.md` |
| `[COPILOT-SSE-V2]` | `backend/src/modules/copilot/api/dto.py` `frontend/src/features/copilot/api/copilot-api.ts` | `docs/domains/copilot/sse-protocol.md` |
| `[COPILOT-MEDIA-UPLOAD]` | `backend/src/modules/copilot/api/media.py` `frontend/src/features/copilot/api/media-api.ts` | `docs/domains/copilot/CONTRACT-MULTIMODAL.md §7` |
| `[COPILOT-OUTBOUND-ASSETS]` | `backend/src/modules/copilot/application/tools/assets_tools.py` | `docs/domains/copilot/outbound-assets.md` |
| `[COPILOT-CITATION-BLOCK]` | `backend/src/modules/copilot/application/tools/knowledge_tools.py` `backend/src/modules/copilot/application/orchestrator/chat.py` | `docs/domains/copilot/message-blocks.md` §citation |
| `[COPILOT-QUOTE-REPLY]` | `frontend/src/features/copilot/components/messages/MessageBubble.tsx` | `docs/domains/copilot/message-blocks.md` §quote_reply |
| `[COPILOT-VOICE-DUAL-MODE]` | `backend/src/modules/copilot/api/voice.py` `frontend/src/features/copilot/hooks/use-voice-recorder.ts` | `docs/domains/copilot/CONTRACT-MULTIMODAL.md §9` |
| `[COPILOT-SUGGESTIONS-ENGINE]` | `frontend/src/features/copilot/hooks/use-suggestions.ts` | `docs/domains/copilot/suggestions-engine.md` |
| `[COPILOT-BLOCK-REGISTRY]` | `frontend/src/features/copilot/components/chat/block-registry.ts` | `docs/domains/copilot/message-blocks.md` §FE renderer |

### 12.2 Rule enforcement

Arch test file: `backend/tests/architecture/test_copilot_anchors.py`.

```python
# Pseudocode
def test_copilot_anchors_have_docs():
    anchors_in_code = set(grep_for(r"\[COPILOT-([A-Z0-9-]+)\]"))
    anchors_in_table = set(ANCHOR_REGISTRY.keys())
    assert anchors_in_code <= anchors_in_table, \
        f"New anchors missing from table §12.1: {anchors_in_code - anchors_in_table}"
```

Adding a new anchor = update this table in the same PR. No exceptions.

---

## 13. Migration Strategy

### 13.1 Phased deploy order

| Phase | Step | Reversible? | Gate |
|---|---|---|---|
| **P1** | Ship Alembic marker revision §3.2 + read adapter §3.3 | ✅ pure metadata | arch tests green |
| **P2** | Ship `MessageBlock` domain + `Message` entity §1, §2, `OutgoingMessage.blocks` §4 | ✅ additive | unit tests green |
| **P3** | Ship `/copilot/media/upload` §7 + `search_assets`/`get_asset` tools §8 + `/voice/upload-and-transcribe` §9 | ✅ additive endpoints | integration tests green |
| **P4** | Ship SSE v2 events §6, **dual emission** (legacy `text_chunk` + new `block_*`) | ✅ v1 FE still works | FE v1 parity |
| **P5** | FE v2 renderer (block registry, composer, voice dual UI, citations, quote-reply, media upload UI) | ✅ via feature flag `COPILOT_V2_UI` | E2E smoke on v2 |
| **P6** | Flip `COPILOT_V2_UI` to default on | ✅ toggle back | 2-week burn-in |
| **P7** | Flip `COPILOT_EMIT_LEGACY_SSE` to false; remove `text_chunk` emission from orchestrator | ⚠️ requires P6 | grep confirms no FE reads `text_chunk` |
| **P8** | Remove legacy `text_chunk` from `SSEEventType` literal union | ⚠️ type break; acceptable after P7 | arch tests pass |

### 13.2 Reversibility

- P1–P5 reversible via feature flag or revert.
- P6 reversible via flag flip.
- P7 reversible via revert within the same release window.
- P8 requires re-add if rolled back (not destructive to data).

### 13.3 Backfill (deferred)

Existing conversations with legacy v1 messages keep working via read adapter (§3.3). If a future need arises (e.g., cross-conv search over blocks), a one-shot job rewrites each conversation's `messages` JSONB. Script location reserved: `backend/scripts/copilot/backfill_message_blocks.py`. Not in this iteration.

---

## 14. Non-goals

Explicitly **out of scope** of this contract:

1. **AI generation of media** (images/audio/video by LLM). Assistant only references existing `Asset`s. Future generative tools = separate contract.
2. **Real smart-chips engine.** Contract + stub only (§11).
3. **WhatsApp channel activation.** Schema is WA-ready (§1.5, §5.3), but no WA send path is built here. Existing `WhatsAppProvider` is untouched.
4. **Video live-streaming / WebRTC.** Only pre-uploaded video assets are supported. `VideoBlock.url` = R2 / local file URL, not a manifest.
5. **Backfill of legacy messages** to block shape (§13.3).
6. **Threading / nested conversations.** `quote_reply` is a single-hop reference, not a new conversation.
7. **Per-block reactions / edits.** Blocks are immutable once `block_end` is emitted.
8. **Mention / at-user blocks** (@mentions). Not needed for single-user copilot UX.
9. **Dynamic block types from skills.** The 11 block types are the full set for this iteration; extensions require a new arch-reviewed PR.
10. **E2E encryption of attachments.** R2 storage is tenant-scoped but not E2EE. Out of scope.

---

## 15. Open Questions & Decisions Log

### 15.1 Decisions locked

| # | Question | Decision | Rationale |
|---|---|---|---|
| Q1 | Where do rich blocks live — new table or embed in existing JSONB? | Embed in existing `copilot_conversations.messages[].blocks`. | Zero migration. Legacy readers still work. JSONB designed for this. |
| Q2 | Add rich support via new method or extend existing? | New `send_rich_message` with default fallback. | LSP preserved, adapters opt-in, arch-testable. |
| Q3 | Voice dual-mode: split or combined endpoint? | Combined `/voice/upload-and-transcribe` + keep split for backward-compat. | Atomicity + lower FE latency + simpler client code. |
| Q4 | Assistant generates media or references existing? | References only (`search_assets` / `get_asset`). | No hallucinated URLs. Generative case is a future tool with explicit guardrails. |
| Q5 | Emit legacy SSE in parallel or cut over? | Dual emit during migration, then cut. | Any FE version keeps working mid-rollout. |
| Q6 | Naming — `Block` vs `MessageBlock` vs `blocks[]`? | Class name `MessageBlock`, field name `blocks`, event prefix `block_*`. | Unambiguous across languages and event namespace. |
| Q7 | Where do citations come from? | Orchestrator wraps `search_knowledge_base` tool results into `CitationBlock` automatically. | Authors of future knowledge tools don't need to learn the block API. |
| Q8 | Where do smart chips come from (future)? | Deferred — contract locked to allow 3 implementations. | YAGNI: pick when first real use case surfaces. |
| Q9 | Max payload size per message? | `blocks` array ≤ 50 items, total serialized JSONB ≤ 2 MB. | Prevents runaway memory and Postgres TOAST pressure. Enforced at write time. |
| Q10 | Should `content` be deprecated? | No — kept forever as flattened-text mirror. | WA/email/non-block consumers rely on it. Invariant 2.2.1. |

### 15.2 Open (parked)

| # | Question | Trigger to resolve |
|---|---|---|
| O1 | Should `CardBlock.payload` be typed per `card_kind`? | When we have >15 card kinds and dict drift becomes a bug source. |
| O2 | Markdown dialect — GFM or custom? | When FE adds first markdown extension beyond basic (tables already a separate block). |
| O3 | Should `waveform` be computed server-side? | When voice UI needs it pre-rendered (not now). |
| O4 | Audio max duration — 2 min, 5 min, 10 min? | First real-user voice message >2 min. |

---

## Appendix A — File Structure Summary (backend + frontend changes)

### Backend (new / modified)

```
backend/src/modules/copilot/
├── domain/
│   ├── message_blocks.py          # NEW §1  [COPILOT-CANONICAL-BLOCKS]
│   └── message.py                 # NEW §2
├── infrastructure/
│   └── repositories/
│       └── message_codec.py       # NEW §3.3  [COPILOT-MESSAGE-CODEC]
├── application/
│   ├── tools/
│   │   └── assets_tools.py        # NEW §8  [COPILOT-OUTBOUND-ASSETS]
│   └── orchestrator/
│       └── chat.py                # EDIT §6 (SSE v2), §10 (citation wrap)
└── api/
    ├── media.py                   # NEW §7  [COPILOT-MEDIA-UPLOAD]
    ├── media_dto.py               # NEW §7.6
    ├── voice.py                   # EDIT §9 (combined endpoint) [COPILOT-VOICE-DUAL-MODE]
    ├── voice_dto.py               # EDIT §9.4
    └── dto.py                     # EDIT §6 (SSE event literal)  [COPILOT-SSE-V2]

backend/src/shared/
├── domain/messages.py             # EDIT §4  [COPILOT-OUTGOING-BLOCKS]
└── infrastructure/channels/base.py  # EDIT §5  [COPILOT-CHANNEL-RENDERER]

backend/alembic/versions/
└── 20260422_1200_copilot_multimodal.py  # NEW §3.2 (marker revision)

backend/tests/architecture/
└── test_copilot_anchors.py        # NEW §12.2

backend/tests/modules/copilot/
├── test_message_blocks.py         # NEW (Pydantic validation)
├── test_message_codec.py          # NEW (v1↔v2 round-trip)
├── test_media_upload.py           # NEW (endpoint, delegation)
├── test_voice_combined.py         # NEW (dual-mode)
└── test_assets_tools.py           # NEW (tenant isolation)
```

### Frontend (new / modified)

```
frontend/src/features/copilot/
├── types/
│   ├── message-blocks.ts          # NEW §1.4  [COPILOT-CANONICAL-BLOCKS]
│   └── suggestions.ts             # NEW §11.1
├── api/
│   ├── copilot-api.ts             # EDIT §6 (SSE v2 types)  [COPILOT-SSE-V2]
│   └── media-api.ts               # NEW §7.8  [COPILOT-MEDIA-UPLOAD]
├── components/
│   ├── chat/
│   │   └── block-registry.ts      # NEW §1.4 FE  [COPILOT-BLOCK-REGISTRY]
│   └── messages/
│       ├── MessageBubble.tsx      # EDIT (render blocks via registry)  [COPILOT-QUOTE-REPLY]
│       ├── blocks/
│       │   ├── TextBlockView.tsx           # NEW
│       │   ├── ImageBlockView.tsx          # NEW
│       │   ├── AudioBlockView.tsx          # NEW (dual-mode player + transcript)
│       │   ├── VideoBlockView.tsx          # NEW
│       │   ├── DocumentBlockView.tsx       # NEW
│       │   ├── TableBlockView.tsx          # NEW
│       │   ├── CodeBlockView.tsx           # NEW
│       │   ├── CitationBlockView.tsx       # NEW
│       │   ├── QuoteReplyBlockView.tsx     # NEW
│       │   ├── CardBlockView.tsx           # NEW (dispatches to existing card components)
│       │   └── ToolResultBlockView.tsx     # NEW
├── hooks/
│   ├── use-copilot-chat.ts        # EDIT (SSE v2 consumer)  [COPILOT-SSE-V2]
│   ├── use-voice-recorder.ts      # EDIT §9  [COPILOT-VOICE-DUAL-MODE]
│   ├── use-media-upload.ts        # NEW §7.8
│   └── use-suggestions.ts         # NEW §11.2  [COPILOT-SUGGESTIONS-ENGINE]
└── __tests__/
    ├── block-registry.test.tsx    # NEW
    ├── message-bubble.test.tsx    # EDIT (block rendering)
    └── use-voice-recorder.test.ts # EDIT
```

---

## Appendix B — Acceptance Checklist

This contract is complete and mergeable when:

- [x] All 11 block types defined with Pydantic v2 + TS mirror.
- [x] `Message` entity defined with v2 shape + legacy compat invariants.
- [x] DB migration is a metadata-only idempotent revision (§3.2).
- [x] `OutgoingMessage` extension is additive (`blocks: list[dict] | None`).
- [x] `BaseChannel.send_rich_message` added with default fallback, LSP-safe.
- [x] SSE v2 events listed with payload examples and dual-emission strategy.
- [x] Upload endpoint delegates to `AssetsService.upload_asset` (no storage dup).
- [x] Outbound tools `search_assets` + `get_asset` defined, tenant-scoped.
- [x] Voice dual-mode endpoint `/voice/upload-and-transcribe` defined with atomicity.
- [x] Citations & quote-reply specified end-to-end (transport-neutral).
- [x] Smart chips stub interface + hook locked.
- [x] 11 anchor comments mapped to docs (§12.1).
- [x] Migration phased plan with reversibility per step.
- [x] Non-goals enumerated.
- [x] Decisions + open questions logged with rationale.

Ready for parallel implementation: **YES** (pending architect review).
