# Outbound Assets — Assistant Delivers Media

How the assistant includes images, audio, video, and documents in its
responses. **It never generates media** — it references existing `Asset` rows
via two tools.

Authoritative spec: [CONTRACT-MULTIMODAL.md §8](./CONTRACT-MULTIMODAL.md#8-outbound-assets-tools).
Anchor: `[COPILOT-OUTBOUND-ASSETS]`.

---

## Flow

```
User: "Muéstrame mi flyer del lanzamiento"
  ↓
LLM: invokes search_assets(query="flyer lanzamiento", kind="image", limit=3)
  ↓
Backend: repo query filtered by tenant_id → returns 3 AssetRef JSON
  ↓
LLM: picks the most relevant, emits response with:
  - TextBlock("Aquí está tu flyer principal:")
  - ImageBlock(asset_id=..., url=..., alt=...)
  ↓
Orchestrator: wraps in SSE v2 events (block_start + block_end for the image),
persists to conversation.
  ↓
FE: renders the image inline in chat.
```

---

## Tools

### `search_assets`

Free-text search over tenant assets.

| Arg | Type | Notes |
|---|---|---|
| `query` | `str` | Searched against `Asset.user_description`, `ai_description`, `filename`, `ai_metadata.tags`. Required. |
| `kind` | `"image" \| "audio" \| "video" \| "document" \| null` | Optional filter. |
| `offer_id` | `UUID \| null` | Optional scope. |
| `limit` | `int` | 1..20, default 5. |

Returns JSON array:
```json
[
  {
    "asset_id": "9f1e...",
    "public_url": "https://cdn.r2.../flyer.png",
    "mime": "image/png",
    "kind": "image",
    "filename": "flyer-lanzamiento.png",
    "description": "Flyer principal para el lanzamiento Q3"
  }
]
```

### `get_asset`

Fetches one asset by id.

| Arg | Type |
|---|---|
| `asset_id` | `UUID` |

Returns one `AssetRef` or `{"error": "not_found"}` (used for both true 404
and cross-tenant attempts, to avoid leaking existence).

---

## What the tools never return

- `storage_path` (internal R2 key) — never exposed outside the backend.
- Assets from a different tenant — repo filter + explicit `tenant_id` param.
- Soft-deleted assets (`deleted_at IS NOT NULL`).
- `ai_metadata` fields that are internal debug data (e.g., processing cost).

Returned payload is the minimum the LLM needs to build a block.

---

## Guardrails

### Prompt-level

System prompt snippet (added to skills that include `"assets"` in their
allowed_tools):

> Cuando el usuario te pida una imagen, audio, video o documento que ya subió,
> llama primero a `search_assets` con una consulta descriptiva. NUNCA inventes
> URLs o IDs de assets. Usa solo los valores de `asset_id` y `public_url` que
> devuelve la tool. Responde con el bloque canónico correspondiente
> (`image`, `audio`, `video`, `document`).

### Tool-level

- Tenant-scoped queries: both tools accept `tenant_id` from the injected
  user principal (never from LLM arguments).
- Rate-limit same as other expensive tools (`copilot-tools` scope).
- `limit ≤ 20` prevents token bloat.

### Orchestrator-level

Before emitting a block that references an `asset_id`, the orchestrator:
1. Validates the asset exists in the tenant (1 quick SELECT).
2. Confirms `Asset.status = "completed"` or at least has a valid `public_url`.
3. If validation fails, the block is dropped and a `TextBlock` explaining "el
   archivo no está disponible" replaces it. The LLM's hallucinated URL never
   reaches the user.

Arch test: `test_outbound_asset_block_validated_before_emit`.

---

## Per-block assembly from `AssetRef`

| Kind | Block | Mapping |
|---|---|---|
| `image` | `ImageBlock` | `asset_id`, `url = public_url`, `mime`, `alt = description` |
| `audio` | `AudioBlock` | `asset_id`, `url = public_url`, `mime`, `transcript` left empty (not a voice note; no STT). For user-uploaded voice notes, transcript is filled at upload time (§9). |
| `video` | `VideoBlock` | `asset_id`, `url`, `mime`, `poster_url` from `Asset.ai_metadata.poster_url` if exists |
| `document` | `DocumentBlock` | `asset_id`, `url`, `mime`, `filename`, `size_bytes`, `preview_url` from `ai_metadata` if exists |

For `audio` blocks referenced via `search_assets` (i.e., not a voice note),
`transcript` is an empty string. UI handles that case by not showing a
transcript panel, just the audio controls.

---

## Non-goals

- **Generation.** Assistant does not create images, audio, etc. A future
  generative tool (e.g., `generate_image_from_prompt`) would be a separate
  arch-reviewed PR with explicit guardrails (cost, moderation, prompt
  sanitization).
- **Cross-tenant asset discovery.** No "find similar assets across tenants"
  tool. Multi-tenant isolation is absolute.
- **Asset editing.** Tools are read-only. Creating/updating/deleting assets
  happens through the assets module's own endpoints, not copilot.

---

## See also

- [CONTRACT-MULTIMODAL.md §8](./CONTRACT-MULTIMODAL.md#8-outbound-assets-tools).
- `backend/src/modules/assets/` — the module that owns assets.
- `backend/src/modules/copilot/application/tools/assets_tools.py` — tool impls (to be created).
- [message-blocks.md](./message-blocks.md) — block schemas.
- `.claude/rules/tenant-isolation.md` — why every query filters tenant_id.
