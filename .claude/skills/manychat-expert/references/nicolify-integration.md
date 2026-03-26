# Nicolify ManyChat Integration Map

## Existing Files

### Backend

| File | Purpose |
|---|---|
| `backend/src/modules/connections/infrastructure/marketing_connectors/manychat.py` | `ManyChatConnector` — inherits `BaseConnector`, implements `verify_connection(api_key)` via `/fb/page/getInfo`. Does NOT yet implement `sync_contacts()` or `sync_events()`. |
| `backend/src/modules/connections/infrastructure/marketing_connectors/base.py` | `BaseConnector` ABC — defines `sync_contacts(tenant_id)` and `sync_events(tenant_id)` interface. |
| `backend/src/modules/connections/api/manychat.py` | FastAPI router with 4 endpoints: `GET /status`, `POST /connect`, `POST /disconnect`, `POST /test`. Inline DTOs (`ManyChatConnectRequest`, `ManyChatStatusResponse`, `ConnectionResponse`). |
| `backend/src/modules/connections/domain/enums.py` | `ChannelType.MANYCHAT = "manychat"` enum value. |
| `backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py` | `ChannelConnectionRepository` — shared repo for all channel connections. Key methods: `get_active(tenant_id, channel_type)`, `upsert(tenant_id, channel_type, credentials, config)`, `get_by_tenant_and_type()`, `deactivate()`, `update_config()`. |
| `backend/src/main.py:199` | Router registration: `app.include_router(conn_manychat.router, prefix="/api/v1/connections/manychat", tags=["Connections - ManyChat"], dependencies=[Depends(get_tenant_context)])` |

### Frontend

| File | Purpose |
|---|---|
| `frontend/src/features/connections/components/manychat-view.tsx` | `ManyChatView` component — two states: disconnected (API key input form) and connected (account info, test connection, disconnect). Uses Clerk auth, Shadcn UI, sonner toasts. |
| `frontend/src/lib/api/connections.ts` | API client functions: `connectionsApi.getManyChatStatus()`, `.connectManyChat()`, `.testManyChat()`, `.disconnectManyChat()`. Uses `fetchClient` with bearer token. |

### Types / DTOs

| Type | Location | Fields |
|---|---|---|
| `ManyChatConnectRequest` | `api/manychat.py` (inline) | `api_key: str` |
| `ManyChatStatusResponse` | `api/manychat.py` (inline) | `is_connected: bool`, `account_info: Optional[Dict]` |
| `ConnectionResponse` | `api/manychat.py` (inline) | `status: str`, `message: str`, `details: Optional[Dict]` |
| `ManyChatConnectRequest` | `lib/api/connections.ts` | `{ api_key: string }` |
| `ManyChatStatusResponse` | `lib/api/connections.ts` | extends `ChannelStatusResponse` + `account_info?: Record<string, any>` |

---

## Code Patterns to Follow

### Connector Pattern

```python
# infrastructure/marketing_connectors/manychat.py
class ManyChatConnector(BaseConnector):
    BASE_URL = "https://api.manychat.com"

    @staticmethod
    async def verify_connection(api_key: str) -> Tuple[bool, Dict[str, Any]]:
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{BASE_URL}/fb/page/getInfo", headers=headers)
            # ... parse response
```

New connector methods should:
- Be `@staticmethod async` methods
- Accept `api_key` as first parameter
- Return `Tuple[bool, Dict[str, Any]]` (success flag + data/error)
- Use `httpx.AsyncClient` for HTTP calls
- Set all three headers: Authorization, Content-Type, Accept

### API Route Pattern

```python
# api/manychat.py
@router.post("/new-endpoint", response_model=SomeResponse)
async def new_endpoint(
    request: SomeRequest,                                    # Pydantic DTO
    user: User = Depends(get_current_user),                  # Auth
    repo: ChannelConnectionRepository = Depends(_get_repo),  # DB access
):
    connection = repo.get_active(user.tenant_id, ChannelType.MANYCHAT)
    if not connection:
        raise HTTPException(status_code=404, detail="No active ManyChat connection found")

    api_key = connection.credentials.get("api_key")
    # ... call ManyChatConnector method with api_key
```

### Frontend API Client Pattern

```typescript
// lib/api/connections.ts
newManyChatMethod: async (data: NewRequest, token: string): Promise<NewResponse> => {
    const res = await fetchClient(`${API_URL}/api/v1/connections/manychat/new-endpoint`, {
        method: "POST",
        headers: {
            Authorization: `Bearer ${token}`,
            "Content-Type": "application/json",
        },
        body: JSON.stringify(data),
    });
    if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || "Error en operacion ManyChat");
    }
    return res.json();
},
```

---

## What's Implemented vs Pending

| Feature | Status | Notes |
|---|---|---|
| API key connection | DONE | Stores encrypted in `channel_connections.credentials` |
| Connection status check | DONE | Reads from DB, returns account_info |
| Connection test | DONE | Re-validates API key against `/fb/page/getInfo` |
| Disconnect | DONE | Soft-deactivates via `repo.deactivate()` |
| Subscriber sync | PENDING | `BaseConnector.sync_contacts()` not implemented |
| Event sync | PENDING | `BaseConnector.sync_events()` not implemented |
| Tag management | PENDING | No endpoints for listing/assigning tags |
| Custom field sync | PENDING | No endpoints for reading/writing custom fields |
| Flow triggering | PENDING | No endpoint for `/fb/sending/sendFlow` |
| Webhook receiver | PENDING | No inbound webhook endpoint for ManyChat events |
| Send content | PENDING | No endpoint for sending messages via API |
| WhatsApp templates | PENDING | No endpoints for WhatsApp template management |

---

## How to Extend: Step-by-Step

### Adding a New ManyChat Feature

1. **Add connector method(s)** to `ManyChatConnector`:
   ```
   backend/src/modules/connections/infrastructure/marketing_connectors/manychat.py
   ```

2. **Create DTOs** (if needed) in a new file:
   ```
   backend/src/modules/connections/api/dto/manychat_dto.py
   ```
   Or add inline in `api/manychat.py` for simple cases (following existing pattern).

3. **Add API route(s)** to existing router in:
   ```
   backend/src/modules/connections/api/manychat.py
   ```
   No need to update `main.py` — routes on the existing `router` object are auto-included.

4. **Add frontend API function** to:
   ```
   frontend/src/lib/api/connections.ts
   ```

5. **Update UI** in:
   ```
   frontend/src/features/connections/components/manychat-view.tsx
   ```
   Or create a new component if the feature warrants its own view.

6. **Migration** (if new DB columns needed):
   ```
   backend/alembic/versions/<rev>_<description>.py
   ```
   Use idempotent raw SQL per CLAUDE.md conventions.

### Adding Webhook Support

Webhooks require a public-facing endpoint. Pattern:

1. Create `api/manychat_webhooks.py` with a new router
2. Register in `main.py` at `/api/v1/webhooks/manychat` (no tenant context middleware — webhook identifies tenant via payload)
3. Validate webhook signature/source
4. Map ManyChat subscriber events to CRM contact updates
