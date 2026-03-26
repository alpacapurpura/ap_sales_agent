---
name: manychat-expert
description: "ManyChat API integration, connections module, chatbot automation, messaging flows, subscriber sync, webhook setup. Pushy trigger: 'manychat', 'many chat', 'chatbot automation', 'subscriber sync', 'messaging flow', 'send content API', 'manychat webhook', 'manychat tag', 'manychat custom field', 'trigger flow'."
---

# ManyChat Expert

You are an expert in ManyChat's API, messaging automation, and its integration with Nicolify's connections module. ManyChat updates their API frequently — **always fetch fresh docs before coding**.

---

## Step 0 — Always Fetch Fresh Documentation (NON-NEGOTIABLE)

Before writing ANY ManyChat-related code, you MUST:

1. **Resolve the ManyChat library on context7:**
   ```
   mcp__plugin_context7_context7__resolve-library-id("ManyChat API")
   ```
   Then query the resolved library for the specific topic you need:
   ```
   mcp__plugin_context7_context7__query-docs(library_id, topic="<your topic>")
   ```
   Example topics: "subscribers", "tags", "custom fields", "flows", "send content", "webhooks", "whatsapp templates", "rate limits"

2. **Web search for recent changes:**
   ```
   WebSearch("ManyChat API changelog 2026")
   WebSearch("ManyChat API updates <topic>")
   ```

3. **Cross-reference** context7 results with what you find via web search. If there's a conflict, the web search result is likely more recent.

Do NOT skip this step. Do NOT rely on cached knowledge. ManyChat deprecates and changes endpoints without long notice periods.

---

## API Capabilities Quick Reference

Use this as a starting point — always verify against fresh docs (Step 0).

| Area | Key Endpoints | Rate Limit |
|---|---|---|
| **Subscribers** | GET/POST find by ID/email/custom field, create, update | 10 rps |
| **Tags** | List, create, add/remove from subscriber | 10 rps |
| **Custom Fields** | Set individual, batch (up to 20), create new | 10 rps |
| **Flows** | List all flows | 10 rps |
| **Flows (trigger)** | Trigger a flow for a subscriber | 20 rps, 100/sub/hour |
| **Send Content** | Send messages (text, image, card, etc.) | 25 rps |
| **WhatsApp Templates** | List templates, send template message | Requires Meta review |
| **Page/Bot Info** | getInfo, getWidgets, getGrowthTools, bot fields | 10 rps |

### Authentication
- All requests use `Authorization: Bearer <API_TOKEN>`
- Token generated in ManyChat Settings > API
- HTTPS only, 10-second request timeout

### Known API Gaps (Critical for Planning)

These features are **NOT available** via the ManyChat API — do not attempt to build them:

- No broadcast creation/scheduling API (must use ManyChat UI)
- No flow creation/editing API (must use ManyChat Flow Builder UI)
- No metrics/analytics API (no way to pull open rates, click rates, etc.)
- No bulk operations on subscribers (loop one-by-one)
- No automation/rule creation API
- No keyword/trigger setup API

**Implication for Nicolify:** Pre-build flows and automations in ManyChat UI. Use the API for data sync (subscribers, tags, custom fields) and triggering pre-built flows.

---

## Existing Nicolify Integration

Read `references/nicolify-integration.md` for the full file map. Summary:

| Layer | File | What It Does |
|---|---|---|
| Connector | `infrastructure/marketing_connectors/manychat.py` | `ManyChatConnector.verify_connection()` — validates API key via `/fb/page/getInfo` |
| API | `api/manychat.py` | 4 endpoints: `/status`, `/connect`, `/disconnect`, `/test` |
| Enum | `domain/enums.py` | `ChannelType.MANYCHAT` |
| Router | `main.py:199` | Mounted at `/api/v1/connections/manychat` with tenant context |
| Frontend | `features/connections/components/manychat-view.tsx` | Connect/disconnect/test UI |
| API Client | `lib/api/connections.ts` | `connectionsApi.{getManyChatStatus,connectManyChat,testManyChat,disconnectManyChat}` |

### What's Missing (Extension Opportunities)

- `sync_contacts` — ManyChatConnector inherits from BaseConnector but doesn't implement `sync_contacts()` or `sync_events()`
- Subscriber search/creation via API
- Tag management (assign tags from Sales Agent qualification)
- Custom field sync (push deal stage, qualification score, etc.)
- Flow triggering (trigger pre-built flows based on CRM events)
- Webhook receiver (ManyChat → Nicolify for real-time subscriber events)

---

## Extension Patterns

When adding new ManyChat features, follow the established connections module architecture:

### Backend (DDD Inside-Out)

1. **Connector method** — Add to `ManyChatConnector` in `infrastructure/marketing_connectors/manychat.py`:
   - Use `httpx.AsyncClient` for all HTTP calls
   - Always pass `Authorization: Bearer {api_key}` header
   - Return `Tuple[bool, Dict]` for consistency with `verify_connection()`
   - Respect rate limits (see table above)

2. **DTOs** — Create in `api/dto/manychat_dto.py` (Pydantic v2 BaseModel)

3. **API route** — Add to `api/manychat.py`:
   - Always inject `user: User = Depends(get_current_user)` and `repo: ChannelConnectionRepository = Depends(_get_repo)`
   - Filter by `user.tenant_id` — never skip tenant isolation
   - Retrieve stored API key via `connection.credentials.get("api_key")`

4. **Router registration** — Already mounted in `main.py:199`, new routes on the existing router are auto-included

5. **Migration** — If new DB fields needed, use idempotent raw SQL (see CLAUDE.md)

### Frontend

- Extend `ManyChatView` in `features/connections/components/manychat-view.tsx`
- Add API functions to `lib/api/connections.ts` following the existing `connectionsApi.{method}` pattern
- Use `fetchClient` with `Authorization: Bearer ${token}` header

### Example: Adding Subscriber Sync

```
# Backend
1. ManyChatConnector.get_subscribers(api_key, params) -> calls GET /fb/subscriber/getSubscribers
2. ManyChatConnector.find_subscriber_by_email(api_key, email) -> calls GET /fb/subscriber/findByCustomField
3. ManyChatSyncService.sync_subscribers(tenant_id) -> orchestrates fetch + upsert to CRM
4. POST /api/v1/connections/manychat/sync-subscribers endpoint

# Frontend
5. connectionsApi.syncManyChatSubscribers(token) in connections.ts
6. "Sync Subscribers" button in ManyChatView connected state
```

---

## Recommended Integration Strategy

ManyChat works best as a **messaging execution layer** driven by Nicolify's intelligence:

1. **Pre-build flows in ManyChat UI** — The API cannot create flows. Design conversation trees in ManyChat's visual builder.

2. **Tags as routing signals** — Sales Agent assigns tags (e.g., `qualified`, `hot-lead`, `booked`) → ManyChat automation triggers the appropriate flow based on tag.

3. **Custom fields as data bridge** — Push structured data from Nicolify to ManyChat:
   - Qualification score, deal stage, product interest
   - ManyChat flows personalize messages using these fields

4. **Flow triggering for one-off actions** — Use `/fb/sending/sendFlow` to push a subscriber into a specific flow (e.g., post-purchase onboarding, abandoned cart recovery).

5. **Webhooks for bidirectional sync** — Configure ManyChat to POST to Nicolify on subscriber events (new subscriber, tag added, custom field changed) for real-time CRM updates.

6. **Rate limit awareness** — All implementations must:
   - Respect per-endpoint rate limits (see table)
   - Use exponential backoff on 429 responses
   - Never exceed 100 flow triggers per subscriber per hour

---

## MCP Server Reference

- **Biznomad/manychat-mcp** — Community MCP server with ~14 tools (subscriber CRUD, tags, custom fields, flows, send content)
- TypeScript-based, useful for prototyping and testing
- For production Nicolify features, prefer direct API integration via `ManyChatConnector` to maintain control over error handling, rate limiting, and tenant isolation

---

## Checklist Before Submitting ManyChat Code

- [ ] Fetched fresh docs from context7 + web search (Step 0)
- [ ] Tenant isolation: all queries/operations filtered by `user.tenant_id`
- [ ] Rate limits respected (check endpoint-specific limits)
- [ ] API key retrieved from encrypted `connection.credentials`, never hardcoded
- [ ] Error handling: graceful 429 (rate limit), 401 (expired token), timeout handling
- [ ] Follows existing connector pattern (`ManyChatConnector` + `api/manychat.py`)
- [ ] DTOs use Pydantic v2 BaseModel
- [ ] Migration (if any) is idempotent raw SQL
