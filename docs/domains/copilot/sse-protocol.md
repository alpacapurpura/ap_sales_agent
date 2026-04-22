# SSE Protocol — v1 and v2

Authoritative spec lives in
[CONTRACT-MULTIMODAL.md §6](./CONTRACT-MULTIMODAL.md#6-sse-v2-protocol).
This doc is the operational reference for producers and consumers.

---

## Event catalog

### v1 (legacy — emitted during migration window, removed after P7)

| Event | Direction | Purpose | Payload shape |
|---|---|---|---|
| `status` | BE→FE | Lifecycle markers | `{state: "thinking" \| "streaming" \| "done"}` |
| `text_chunk` | BE→FE | Streaming assistant text | `{content: str}` |
| `tool_start` | BE→FE | Tool invocation begins | `{tool: str, args: dict}` |
| `tool_result` | BE→FE | Tool invocation ends | `{tool: str, result: str (≤500c)}` |
| `ui_action` | BE→FE | Generative UI card | `UIAction` dict (see `store/copilot-store.ts`) |
| `proposal` | BE→FE | Field mutation proposal | `{updates: ProposalUpdate[], ...}` |
| `confirmation_required` | BE→FE | Gate for risky mutation | `{prompt: str, proposal_id: str}` |
| `tier_decision` | BE→FE | Which LLM tier the router chose | `{tier: str, reason: str, confidence: float}` |
| `mutation_applied` | BE→FE | Successful field mutation | `{mutation_id, domain, field_path, ...}` |
| `done` | BE→FE | Stream complete | `{conversation_id: str, message_id: str}` |
| `error` | BE→FE | Stream error | `{message: str}` (user-safe, Spanish neutro LatAm) |

### v2 (new — canonical going forward)

| Event | Direction | Purpose | Payload shape |
|---|---|---|---|
| `message_start` | BE→FE | New assistant message begins | `{message_id, role: "assistant", created_at}` |
| `block_start` | BE→FE | New block begins | `{message_id, block_id, type, index, partial: MessageBlock}` |
| `block_delta` | BE→FE | Streaming block update (text only) | `{message_id, block_id, delta: {markdown: str}}` |
| `block_end` | BE→FE | Block finalized | `{message_id, block_id, final: MessageBlock}` |
| `message_end` | BE→FE | Assistant message complete | `{message_id, status, tokens_used?, blocks: MessageBlock[]}` |

`status`, `tool_start`, `tool_result`, `tier_decision`, `mutation_applied`,
`done`, `error` remain in v2 unchanged.

`ui_action`, `proposal`, `confirmation_required` become `CardBlock` entries
inside `message_end.blocks[]` in v2; legacy events keep firing in parallel
until P8.

---

## Streaming semantics

### Text blocks (the common case)

```
block_start(type=text, partial.markdown="")
block_delta(delta.markdown="Claro, ")
block_delta(delta.markdown="aquí va ")
block_delta(delta.markdown="tu propuesta.")
block_end(final.markdown="Claro, aquí va tu propuesta.")
```

- `delta.markdown` is an **append**, not a replace.
- FE must preserve block order across concurrent blocks (the `index` field is
  stable and monotonically increasing per message).
- Partial unicode is OK — backend flushes on token boundaries.

### Non-text blocks (atomic)

```
block_start(type=image, index=1, partial=<full ImageBlock>)
block_end(final=<same ImageBlock>)
```

Image/audio/video/document/table/code/citation/quote_reply/card/tool_result
emit `block_start` and `block_end` with the same full payload. No deltas.

### Multiple blocks per message

Order is the emission order. FE shows them top-to-bottom. A message can be:
- text only → 1 block.
- text + citation → 2 blocks.
- text + image + text → 3 blocks (image embedded mid-message).
- card only → 1 block (no preceding text).

---

## Dual emission during migration

During P4–P7, the orchestrator emits BOTH legacy and v2 events for the same
assistant response:

```
# v1 path
status(streaming)
text_chunk("Claro, ")
text_chunk("aquí va")

# v2 path (same content, different events)
message_start(...)
block_start(type=text, ...)
block_delta(markdown="Claro, ")
block_delta(markdown="aquí va")
block_end(...)
message_end(...)

done(...)
```

FE behavior:
- **v1 FE**: ignore unknown v2 events, consume `text_chunk` to build display.
- **v2 FE**: ignore `text_chunk`, consume `block_*` to build display.

Feature flag: `COPILOT_EMIT_LEGACY_SSE=true` (default during migration).

Cutover: after P7 flip, orchestrator no longer emits v1 events. Old FE clients
break — acceptable because deploy cadence is coordinated.

---

## Producer implementation notes

### Where to emit from

| Event | Emitter |
|---|---|
| `status` | `CopilotOrchestrator.stream_chat` (existing) |
| `tool_start`, `tool_result` | LangGraph event bridge in `stream_chat._process_stream_event` (existing) |
| `text_chunk` | LLM streaming bridge (existing — keep during migration) |
| `message_start`, `message_end` | `CopilotOrchestrator.stream_chat` wrapping the existing loop |
| `block_start`, `block_delta`, `block_end` (text) | LLM streaming bridge, alongside `text_chunk` |
| `block_start`, `block_end` (non-text) | Orchestrator-level wrappers around tool results (citation, tool_result blocks) + composer for image/audio/video/document/card |
| `done`, `error` | `CopilotOrchestrator.stream_chat` (existing) |

### Ordering guarantees

- `message_start` MUST precede any `block_*` for the same `message_id`.
- `block_start` for index N MUST precede any `block_delta`/`block_end` for
  that block.
- `block_end` MUST precede `message_end` for the same `message_id`.
- `message_end` MUST precede `done`.

### Idempotency for reconnects

SSE does not support perfect resumption. If the client reconnects mid-stream:
- Old connection is closed; BE may emit a trailing `error` event.
- Client re-fetches the conversation via `GET /conversations/{id}` — the DB
  has persisted whatever blocks completed (via `block_end` at least).

---

## Consumer implementation notes

### FE state machine (v2)

```ts
// Pseudocode
const blocks: Map<BlockId, MessageBlock> = new Map();
const blockOrder: BlockId[] = [];

sse.on("message_start", (e) => { currentMessageId = e.message_id; });

sse.on("block_start", (e) => {
  blocks.set(e.block_id, e.partial);
  blockOrder.push(e.block_id);
});

sse.on("block_delta", (e) => {
  const b = blocks.get(e.block_id);
  if (b?.type === "text" && "markdown" in e.delta) {
    b.markdown += e.delta.markdown;
  }
});

sse.on("block_end", (e) => {
  blocks.set(e.block_id, e.final);  // authoritative
});

sse.on("message_end", (e) => {
  // Reconcile: e.blocks is ground truth, replace local map
  rebuildFromBlocks(e.blocks);
});
```

### Why `message_end.blocks` repeats everything

Belt and braces. If any `block_*` event is dropped (network hiccup, proxy
buffering), `message_end.blocks` is the canonical list. FE replaces its local
reconstruction with it.

---

## See also

- [CONTRACT-MULTIMODAL.md §6](./CONTRACT-MULTIMODAL.md#6-sse-v2-protocol).
- [message-blocks.md](./message-blocks.md) — block payloads.
- `frontend/src/features/copilot/hooks/use-copilot-chat.ts` — SSE consumer.
- `backend/src/modules/copilot/application/orchestrator/chat.py` — SSE producer.
