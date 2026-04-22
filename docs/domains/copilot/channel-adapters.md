# Channel Adapters — Operational Guide

How to add a new outbound channel (email, Telegram-rich, WhatsApp activated,
iMessage, etc.) that speaks the canonical `MessageBlock` protocol. Spec anchor:
[CONTRACT-MULTIMODAL.md §5](./CONTRACT-MULTIMODAL.md#5-channel-adapter-extension).

---

## The contract in one paragraph

The orchestrator always produces an `OutgoingMessage` with `blocks: list[dict]`
and a flattened `text`. It calls `adapter.send_rich_message(msg)` on whatever
adapter the channel resolver returns. The default `BaseChannel.send_rich_message`
falls back to `send_message` using `msg.text` (plain text). Rich channels
override to consume `msg.blocks`. No branching in the orchestrator.

---

## Checklist — adding a new channel

### 1. Skeleton

File: `backend/src/modules/connections/infrastructure/channels/{channel}/` (or
the shared location already chosen for your channel family).

- [ ] Implement `normalize_payload(payload)` → `IncomingMessage | None`.
- [ ] Implement `send_message(OutgoingMessage)` — plain text send.
- [ ] Implement `set_typing_status(user_id)` or no-op.
- [ ] **Override** `send_rich_message(OutgoingMessage)` (see below).

### 2. Override `send_rich_message`

```python
async def send_rich_message(self, message: OutgoingMessage) -> dict[str, Any]:
    """Translate blocks to native API calls. See docs/domains/copilot/channel-adapters.md."""
    if not message.blocks:
        return await self.send_message(message)

    results = []
    for block in message.blocks:
        handler = self._BLOCK_DISPATCH.get(block["type"], self._fallback_to_text)
        result = await handler(message.user_id, block)
        results.append(result)
    return {"results": results}

_BLOCK_DISPATCH = {
    "text":     _send_text,
    "image":    _send_image,
    "audio":    _send_audio,
    # ...
}

async def _fallback_to_text(self, user_id: str, block: dict) -> dict:
    """Fallback for unsupported blocks: send the block's plain-text equivalent."""
    text = _flatten_block_to_text(block)
    if not text:
        return {"skipped": block["type"]}
    return await self._send_text(user_id, text)
```

The fallback strategy MUST never raise when a block type is unsupported. It
either sends a text rendition (if meaningful) or silently skips (with a log).

### 3. Per-block mapping

Fill the mapping table for your channel. The canonical schema is in
[CONTRACT-MULTIMODAL.md §1.5](./CONTRACT-MULTIMODAL.md#15-per-block-whatsapp-translatability)
— WhatsApp is provided as a worked example.

For a new channel, produce a similar table **before** writing code.

### 4. Channel resolver registration

If the new channel is dispatched automatically per lead, register it in
`src.modules.sales_agent.application.services.channel_resolver.ChannelResolver._CHANNEL_MAP`
with a `(ChannelType, id_field)` tuple.

If the channel is copilot-only (web SSE, for example), it doesn't go through
the resolver — the orchestrator emits SSE directly.

### 5. Arch tests

- [ ] `test_new_rich_channels_override_send_rich_message` — any `BaseChannel`
      subclass declared as "rich-capable" (via registration list) MUST override
      `send_rich_message`. Fails if the default fallback would be used for a
      rich channel.
- [ ] `test_channel_block_dispatch_complete` — every `MessageBlock["type"]` has
      an entry in `_BLOCK_DISPATCH` for each rich channel (or is explicitly
      listed in `UNSUPPORTED_BLOCKS` with a log-only fallback).

---

## Fallback strategy — mandatory

When a channel cannot represent a block type natively, fall back in this order:

1. **Text rendition** via `_flatten_block_to_text(block)` — the same function
   the backend uses to populate `OutgoingMessage.text`.
2. **Silent skip with log** if the block has no meaningful text (e.g.,
   `tool_result` on a user-facing channel).
3. **Error** only if the block is malformed (missing required fields). Never
   error because "this channel doesn't support type X" — that's a fallback, not
   an error.

Rationale: users don't care about our internal schema. A WhatsApp user should
receive *something* when we emit a complex card; a text summary is better than
silence.

---

## WhatsApp reference implementation (when activated)

Skeleton (non-goal of this iteration — documented for implementers tomorrow):

```python
class WhatsAppCloudAdapter(BaseEvolutionApi):
    async def send_rich_message(self, message: OutgoingMessage) -> dict[str, Any]:
        """Map blocks to WhatsApp Cloud API Media / Interactive messages."""
        if not message.blocks:
            return await self.send_message(message)

        quote_ctx: str | None = None
        results = []
        for block in message.blocks:
            bt = block["type"]

            if bt == "quote_reply":
                quote_ctx = block["ref_message_id"]
                continue  # attach to next block

            if bt == "text":
                r = await self._send_text(message.user_id, block["markdown"], quote=quote_ctx)
            elif bt == "image":
                r = await self._send_media(message.user_id, "image", block["url"],
                                           caption=block.get("alt"), quote=quote_ctx)
            elif bt == "audio":
                r = await self._send_media(message.user_id, "audio", block["url"], quote=quote_ctx)
                # transcript goes as follow-up text for accessibility
                if block.get("transcript"):
                    await self._send_text(message.user_id, f"🎙️ {block['transcript']}")
            elif bt == "video":
                r = await self._send_media(message.user_id, "video", block["url"],
                                           caption=block.get("alt"), quote=quote_ctx)
            elif bt == "document":
                r = await self._send_media(message.user_id, "document", block["url"],
                                           filename=block["filename"], quote=quote_ctx)
            elif bt == "card" and block["card_kind"] in {"proposal", "alternatives", "multi_option"}:
                r = await self._send_interactive(message.user_id, block["payload"], quote=quote_ctx)
            elif bt == "citation":
                r = await self._send_text(message.user_id,
                                          f"> {block['snippet']}\n— {block['source']}")
            elif bt == "table" or bt == "code":
                r = await self._send_text(message.user_id, _flatten_block_to_text(block))
            elif bt == "tool_result":
                r = {"skipped": "tool_result"}  # never show internal traces
            else:
                r = await self._fallback_to_text(message.user_id, block)

            results.append(r)
            quote_ctx = None
        return {"results": results}
```

---

## Telegram rich

Telegram's Bot API natively supports most blocks (`sendPhoto`, `sendAudio`,
`sendVideo`, `sendDocument`, quote via `reply_to_message_id`, `parseMode=MarkdownV2`
for text, inline keyboards for `card`). Implementation mirrors WA.

---

## Email (SMTP / transactional)

Email has different semantics — the entire `blocks` list becomes one HTML body:

- `text` → HTML paragraph (markdown → HTML via `markdown-it`).
- `image/video/document` → `<img>`, `<video>`, `<a href>` links. Attach inline
  if size permits.
- `card` → HTML button blocks (CTA links).
- `table` → `<table>` HTML.

One adapter call = one email. `send_rich_message` composes, `send_message`
sends the plain-text fallback for text-only email clients.

---

## Debugging

- Log every block dispatched, with `block_type`, `asset_id` (if present),
  channel API response status.
- Never log the full block payload at INFO level (can leak PII in captions/alt).
- At DEBUG, log flattened text only.

---

## See also

- [CONTRACT-MULTIMODAL.md §1.5](./CONTRACT-MULTIMODAL.md#15-per-block-whatsapp-translatability) — authoritative WA mapping.
- [CONTRACT-MULTIMODAL.md §5](./CONTRACT-MULTIMODAL.md#5-channel-adapter-extension) — `BaseChannel.send_rich_message` contract.
- [message-blocks.md](./message-blocks.md) — block type registry.
- `.claude/rules/copilot-resilience.md` — no hardcoded channel branches in copilot tools.
