# Message Blocks — Operational Guide

Practical checklist for block-type work. Authoritative spec lives in
[CONTRACT-MULTIMODAL.md §1](./CONTRACT-MULTIMODAL.md#1-message-block-schema).
This doc answers the three common "how do I..." questions.

---

## Current block registry (11 types)

| Type | Use for | Streams? | Has asset? |
|---|---|---|---|
| `text` | Markdown prose, the common case | ✅ (via `block_delta`) | — |
| `image` | PNG/JPG/WEBP/GIF/SVG | No | ✅ |
| `audio` | Voice notes + other audio. **Dual-mode mandatory** (url + transcript). | No | ✅ |
| `video` | MP4/WEBM/MOV | No | ✅ |
| `document` | PDF, DOCX, XLSX, CSV, TXT, MD | No | ✅ |
| `table` | Structured tabular data | No | — |
| `code` | Code snippets with syntax highlight | No | — |
| `citation` | RAG / knowledge-base attribution | No | — |
| `quote_reply` | Reply to a previous message in same conversation | No | — |
| `card` | Wraps existing UI action cards (proposal, alternatives, clarify, checkpoint, interview_complete, metric_summary, comparison, checklist, multi_option, navigation) | No | — |
| `tool_result` | Transparent tool-call trace | No | — |

---

## Checklist — adding a new block type

Order matters. Do not skip; arch tests will fail.

### 1. Backend — domain

File: `backend/src/modules/copilot/domain/message_blocks.py`.

- [ ] Add a new `XxxBlock(_BlockBase)` subclass with `type: Literal["xxx"]` discriminator.
- [ ] Use `model_config = ConfigDict(extra="forbid", from_attributes=True)` (inherited from `_BlockBase`; don't override).
- [ ] Add field validators for any bounded field (e.g., `snippet: str` → ≤500 chars).
- [ ] Append the class to the `MessageBlock` discriminated union.
- [ ] Append the string literal to `BLOCK_TYPES` tuple.
- [ ] Add a `# [COPILOT-CANONICAL-BLOCKS]` anchor comment near the class if not already present at the top of the file.

### 2. Backend — codec

File: `backend/src/modules/copilot/infrastructure/repositories/message_codec.py`.

- [ ] If the block contributes to plain-text `content` (e.g., text inside it that users would expect when reading on a channel without rich support), extend `_flatten_blocks()` with its rendition.

### 3. Frontend — types

File: `frontend/src/features/copilot/types/message-blocks.ts`.

- [ ] Mirror the Python class as a TypeScript `interface XxxBlock extends BlockBase` with the same field names (snake_case).
- [ ] Add it to the `MessageBlock` union type.

### 4. Frontend — renderer

Files:
- `frontend/src/features/copilot/components/messages/blocks/XxxBlockView.tsx` — new component.
- `frontend/src/features/copilot/components/chat/block-registry.ts` — add entry.

- [ ] Implement `XxxBlockView` as a pure function component: `({ block: XxxBlock }) => JSX.Element`.
- [ ] Register in `BLOCK_REGISTRY`:
  ```ts
  // [COPILOT-BLOCK-REGISTRY]
  export const BLOCK_REGISTRY: Record<MessageBlock["type"], React.FC<{ block: any }>> = {
    text: TextBlockView,
    image: ImageBlockView,
    // ...
    xxx: XxxBlockView,  // <-- new
  };
  ```
- [ ] Handle unknown/future block types with a neutral fallback (`<UnknownBlockView />`) so old FE versions don't crash on a new block type.

### 5. Channel adapters (if the block should be sendable outbound to non-web channels)

For every active outbound channel (currently only web; WA is future):
- [ ] Extend the adapter's `send_rich_message` implementation to translate `XxxBlock` to the channel's native API.
- [ ] If the channel can't represent the block, add a fallback rendition (usually text) — see [channel-adapters.md](./channel-adapters.md) for the fallback strategy.

### 6. Arch tests

File: `backend/tests/architecture/test_message_blocks.py`.

- [ ] Add a row to the `BLOCK_TYPE_METADATA` test fixture listing the new type, whether it has an asset, whether it streams.
- [ ] Ensure `test_all_block_types_in_registry` picks up the new class automatically (it iterates the `MessageBlock` union).
- [ ] If the block references an `Asset`, ensure `test_asset_block_has_asset_id_field` still passes (field is named `asset_id`, not `asset` or `url_id` etc.).

---

## Checklist — renaming / changing a block field

**Avoid.** Block schemas are an external contract once shipped. Breaking them
invalidates historical messages and forces a codec branch.

If unavoidable:
1. Deprecate the old field with a comment, keep it present.
2. Add the new field alongside.
3. Write a codec migration that populates the new field from the old.
4. Run the migration on read (never write the old field for new messages).
5. Remove the old field only after a full release cycle with metrics showing 0 reads.

---

## Validation rules

Enforced by Pydantic at write time (emit of a new message):

| Rule | Enforced in |
|---|---|
| `blocks` array ≤ 50 entries per message | `Message` root validator |
| Serialized message JSON ≤ 2 MB | Orchestrator persistence layer |
| `TableBlock`: every row length == columns length | Pydantic `model_validator` in `TableBlock` |
| `CitationBlock.snippet` ≤ 500 chars | Field validator |
| `QuoteReplyBlock.preview` ≤ 140 chars | Field validator |
| `AudioBlock.transcript` not null (empty string allowed) | Non-optional field |
| `AudioBlock.url` and `AudioBlock.asset_id` both present | Non-optional fields |
| `asset_id` exists in same tenant | Write-path check in orchestrator (cross-ref DB) — NOT in block validator |

---

## FE renderer contract

The `BLOCK_REGISTRY` is the single source of truth for which component renders
which block type. Rules:

- Registry keys are `MessageBlock["type"]` literals; exhaustive.
- Unknown types render via `UnknownBlockView` (graceful degradation for older clients on newer server).
- No component may render another block type internally except via the registry (no hardcoded branches).
- Components must be pure — no hooks that fetch data. If a block needs remote data (e.g., resolving `asset_id` to a fresh URL), the orchestrator MUST include that data in the block payload before emission.

---

## See also

- [CONTRACT-MULTIMODAL.md §1](./CONTRACT-MULTIMODAL.md#1-message-block-schema) — authoritative schema.
- [channel-adapters.md](./channel-adapters.md) — mapping blocks to channel APIs.
- [sse-protocol.md](./sse-protocol.md) — streaming semantics per block type.
- [UI-SPEC.md](./UI-SPEC.md) — visual design of each block.
