# IG DM Capture Pipeline — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Instagram DM leads and conversations appear in the Growth Studio Capture stage dashboard, using ManyChat webhooks as primary data source and Meta IG messaging webhook as secondary.

**Architecture:** Two complementary data paths feed the same dashboard. ManyChat webhooks create `customer_profiles` (leads) and `official_metrics` (counts). Meta IG messaging webhook (via sales_agent) creates `journey_events` with `message_received` (conversations). Both paths merge under the `ig-dm` channel slug via existing `_merge_manychat_into_meta()` logic. A new `subscriber.new` → `message_received` bridge ensures ManyChat events also contribute to conversation counts.

**Tech Stack:** FastAPI webhooks, SQLAlchemy 2.0, ManyChat External Request API, Meta Graph API webhooks

**Current State (investigated 2026-03-30):**
- ManyChat connection for tenant `d68f4af3`: **does not exist**
- ManyChat journey_events: **0**
- Meta IG messaging webhook: **not subscribed** (0 `message_received` events)
- Conversations API (backfill): **blocked** by Standard Access timeout (code fixed but unusable until Advanced Access)
- All backend/frontend code for both paths: **already exists and is code-complete**

---

## Track A: ManyChat Webhook (Quick Win — leads + partial conversations)

### Task 1: Connect ManyChat via Settings UI

**Files:** None (user action in the app)

This task is a **manual configuration step** — no code changes.

- [ ] **Step 1: Get ManyChat API key**

In ManyChat:
1. Log in to https://manychat.com
2. Go to **Settings → API**
3. Click **Generate Token**
4. Copy the token

- [ ] **Step 2: Connect in Nicolify Settings**

In Nicolify (browser):
1. Go to **Settings** (sidebar)
2. Find the **ManyChat** section
3. Paste the API Token
4. Click **Conectar ManyChat**
5. Verify the green "Activo" badge appears with the account name

- [ ] **Step 3: Verify connection in database**

```bash
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -t -A -c \
  "SELECT channel_type, is_active, config->>'account_info' FROM channel_connections WHERE tenant_id = 'd68f4af3-3871-4f09-9cbd-a9856235025f' AND channel_type = 'manychat';"
```

Expected: `manychat|t|{"name":"...", "id":"..."}`

---

### Task 2: Configure ManyChat External Request Flows

**Files:** None (user action in ManyChat automation builder)

ManyChat must POST events to our webhook. The endpoint is:

```
POST https://<your-domain>/api/webhooks/manychat/d68f4af3-3871-4f09-9cbd-a9856235025f
```

- [ ] **Step 1: Create "New Subscriber" External Request**

In ManyChat automation builder:
1. Open the **Default Reply** flow (or your main IG DM automation)
2. Add an **External Request** block at the start
3. Configure:
   - **Method:** POST
   - **URL:** `https://<domain>/api/webhooks/manychat/d68f4af3-3871-4f09-9cbd-a9856235025f`
   - **Headers:** `Content-Type: application/json`
   - **Body (JSON):**

```json
{
  "event_type": "subscriber.new",
  "subscriber_id": "{{subscriber_id}}",
  "channel": "instagram",
  "first_name": "{{first_name}}",
  "last_name": "{{last_name}}",
  "email": "{{email}}",
  "phone": "{{phone}}",
  "ig_username": "{{ig_username}}"
}
```

- [ ] **Step 2: (Optional) Add tag-based External Requests**

For deeper funnel tracking, add External Request blocks in other flows:

**Tag Applied:**
```json
{
  "event_type": "tag.applied",
  "subscriber_id": "{{subscriber_id}}",
  "channel": "instagram",
  "tag_name": "{{last_applied_tag}}",
  "ig_username": "{{ig_username}}"
}
```

**Comment Trigger:**
```json
{
  "event_type": "comment.trigger",
  "subscriber_id": "{{subscriber_id}}",
  "channel": "instagram",
  "ig_username": "{{ig_username}}"
}
```

- [ ] **Step 3: Test webhook delivery**

Send a test DM to @visionarias.lat on Instagram. Then verify:

```bash
docker logs visionarias_brain_dev --tail 50 2>&1 | grep -i manychat
```

Expected: `manychat_webhook_processed tenant_id=d68f4af3... event=manychat_subscriber_created`

---

### Task 3: Bridge ManyChat `subscriber.new` → `message_received` journey_event

**Problem:** The capture dashboard counts conversations via `count_conversations_by_channel()` which queries `journey_events WHERE event_name='message_received'`. ManyChat webhooks create `manychat_subscriber_created` events, NOT `message_received` — so conversations show as 0 even when leads are counted.

**Fix:** When `subscriber.new` arrives for an Instagram channel, also create a `message_received` journey_event so the conversation counter picks it up.

**Files:**
- Modify: `backend/src/modules/connections/api/marketing_webhooks.py:203-211`
- Test: `backend/tests/modules/connections/test_manychat_webhook.py` (create)

- [ ] **Step 1: Write the failing test**

Create `backend/tests/modules/connections/test_manychat_webhook.py`:

```python
"""Tests for ManyChat webhook → message_received bridge."""
import uuid
from unittest.mock import patch, MagicMock

import pytest
from sqlalchemy import select, func

from src.modules.crm.infrastructure.models.customer_model import JourneyEventModel


@pytest.fixture
def tenant_id():
    return uuid.uuid4()


@pytest.fixture
def subscriber_new_payload():
    return {
        "event_type": "subscriber.new",
        "subscriber_id": "mc_12345",
        "channel": "instagram",
        "first_name": "Test",
        "last_name": "User",
        "ig_username": "testuser",
    }


def test_subscriber_new_creates_message_received_event(
    db_session, tenant_id, subscriber_new_payload
):
    """subscriber.new for instagram should also create a message_received event."""
    from src.modules.connections.api.marketing_webhooks import _handle_manychat_event
    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    # Setup: create ManyChat connection
    conn = ChannelConnectionModel(
        tenant_id=tenant_id,
        channel_type="manychat",
        is_active=True,
        credentials={"api_key": "test"},
        config={"account_info": {"name": "Test"}},
    )
    db_session.add(conn)
    db_session.commit()

    # Act: handle subscriber.new event
    import asyncio
    asyncio.get_event_loop().run_until_complete(
        _handle_manychat_event(
            db_session, tenant_id, subscriber_new_payload, "instagram"
        )
    )

    # Assert: both events exist
    events = db_session.execute(
        select(JourneyEventModel.event_name).where(
            JourneyEventModel.tenant_id == tenant_id,
        )
    ).all()
    event_names = [e[0] for e in events]

    assert "manychat_subscriber_created" in event_names
    assert "message_received" in event_names

    # Assert: message_received has correct properties
    msg_event = db_session.execute(
        select(JourneyEventModel).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "message_received",
        )
    ).scalar_one()
    assert msg_event.properties["channel_slug"] == "manychat-ig"
    assert msg_event.properties["source"] == "manychat_webhook"
    assert msg_event.properties["message_direction"] == "inbound"


def test_tag_applied_does_not_create_message_received(
    db_session, tenant_id
):
    """Non-subscriber events should NOT create message_received."""
    from src.modules.connections.api.marketing_webhooks import _handle_manychat_event
    from src.modules.connections.infrastructure.models.channel_connection_model import (
        ChannelConnectionModel,
    )

    conn = ChannelConnectionModel(
        tenant_id=tenant_id,
        channel_type="manychat",
        is_active=True,
        credentials={"api_key": "test"},
        config={},
    )
    db_session.add(conn)
    db_session.commit()

    payload = {
        "event_type": "tag.applied",
        "subscriber_id": "mc_12345",
        "channel": "instagram",
        "tag_name": "quiz_started",
        "ig_username": "testuser",
    }

    import asyncio
    asyncio.get_event_loop().run_until_complete(
        _handle_manychat_event(db_session, tenant_id, payload, "instagram")
    )

    msg_count = db_session.execute(
        select(func.count(JourneyEventModel.id)).where(
            JourneyEventModel.tenant_id == tenant_id,
            JourneyEventModel.event_name == "message_received",
        )
    ).scalar()
    assert msg_count == 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/connections/test_manychat_webhook.py -x -v --tb=short"
```

Expected: FAIL — `"message_received" not in event_names`

- [ ] **Step 3: Implement the bridge**

In `backend/src/modules/connections/api/marketing_webhooks.py`, after the existing journey_event creation block (around line 211), add:

```python
    if profile:
        journey_event = JourneyEventModel(
            profile_id=profile.id,
            tenant_id=tenant_id,
            event_name=event_name,
            event_type="track",
            properties=properties,
        )
        db.add(journey_event)

        # Bridge: subscriber.new → message_received for conversation counting.
        # The capture dashboard counts conversations via journey_events where
        # event_name='message_received', grouped by channel_slug. Without this,
        # ManyChat leads show up but conversations show as 0.
        if event_type == "subscriber.new":
            msg_event = JourneyEventModel(
                profile_id=profile.id,
                tenant_id=tenant_id,
                event_name="message_received",
                event_type="track",
                properties={
                    "channel_slug": channel_slug,
                    "channel_type": channel,
                    "message_direction": "inbound",
                    "source": "manychat_webhook",
                    "manychat_subscriber_id": subscriber_id,
                },
            )
            db.add(msg_event)

        # 3. Recalculate score
```

- [ ] **Step 4: Run test to verify it passes**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && pytest tests/modules/connections/test_manychat_webhook.py -x -v --tb=short"
```

Expected: PASS

- [ ] **Step 5: Run full backend CI**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache && pytest -x -q --tb=short"
```

Expected: All pass

- [ ] **Step 6: Commit**

```bash
git add backend/src/modules/connections/api/marketing_webhooks.py backend/tests/modules/connections/test_manychat_webhook.py
git commit -m "feat(analytics): bridge manychat subscriber.new → message_received for conversation counts"
```

---

## Track B: Meta IG Messaging Webhook (Complete — leads + real conversations)

This track enables the existing sales_agent pipeline to create `message_received` journey_events from real-time Meta webhooks. It requires NO code changes — only Meta App Dashboard configuration.

### Task 4: Subscribe to Instagram Messaging Webhook

**Files:** None (Meta App Dashboard configuration)

- [ ] **Step 1: Configure webhook subscription**

In [Meta App Dashboard](https://developers.facebook.com/apps/):
1. Select the Nicolify app
2. Go to **Webhooks** → **Instagram**
3. Subscribe to the `messages` field
4. Set Callback URL: `https://<your-domain>/api/connections/meta/webhook`
5. Set Verify Token: (check your `.env` for `META_WEBHOOK_VERIFY_TOKEN`)

- [ ] **Step 2: Verify webhook is receiving events**

Send a DM to @visionarias.lat, then check:

```bash
docker logs visionarias_brain_dev --tail 50 2>&1 | grep -i "instagram\|ig_dm\|message_received\|incoming_message"
```

Expected: Logs showing message receipt → sales_agent processing → journey_event creation

- [ ] **Step 3: Verify journey_events created**

```bash
docker exec -t visionarias_postgres psql -U postgres -d visionarias_logs -t -A -c \
  "SELECT event_name, properties->>'channel_slug', COUNT(*) FROM journey_events WHERE tenant_id = 'd68f4af3-3871-4f09-9cbd-a9856235025f' AND event_name = 'message_received' GROUP BY event_name, properties->>'channel_slug';"
```

Expected: `message_received|ig-dm|N` (where N > 0)

---

## Track C: Conversations API Backfill (Blocked — needs Advanced Access)

### Task 5: Request Advanced Access for instagram_manage_messages

**Files:** None (Meta App Dashboard)

- [ ] **Step 1: Submit App Review request**

In [Meta App Dashboard](https://developers.facebook.com/apps/):
1. Go to **App Review** → **Permissions and Features**
2. Find `instagram_manage_messages`
3. Click **Request Advanced Access**
4. Fill out the required business verification and use case description
5. Submit for review (typically 1-5 business days)

- [ ] **Step 2: After approval — test Conversations API**

Once Advanced Access is granted:

```bash
docker exec -t visionarias_brain_dev bash -c 'cd /app && python -c "
import asyncio
from uuid import UUID
async def test():
    from src.core.config import settings
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    engine = create_engine(str(settings.DATABASE_URL))
    tenant_id = UUID(\"d68f4af3-3871-4f09-9cbd-a9856235025f\")
    with Session(engine) as db:
        from src.modules.connections.application.services.connection_port_impl import ConnectionPortImpl
        from src.modules.analytics.application.services.ig_dm_sync_service import InstagramDMSyncService
        cp = ConnectionPortImpl(db)
        svc = InstagramDMSyncService(db, connection_port=cp)
        result = await svc.sync(tenant_id)
        print(result)
asyncio.run(test())
"'
```

Expected: `{"synced_messages": N, "new_leads": M, "skipped": K}` where N > 0

---

## Task 6: Commit existing bug fixes from this session

**Files:**
- Modified: `backend/src/modules/analytics/application/services/ig_dm_sync_service.py`
- Modified: `backend/src/modules/analytics/application/services/etl_service.py`

These fixes were already applied in the current session:
1. `_GRAPH_API_BASE` changed to `graph.facebook.com`
2. Added `_get_page_access_token()` for System User → Page Token exchange
3. Fixed config key `tracked_page_id` (was `page_id`)
4. Used `/{page_id}/conversations` (was `/me/conversations`)
5. Integrated IG DM sync into `run_sync_all()`

- [ ] **Step 1: Verify lint + tests pass**

```bash
docker exec -t visionarias_brain_dev bash -c "cd /app && ruff check src --no-cache && pytest -x -q --tb=short"
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/modules/analytics/application/services/ig_dm_sync_service.py backend/src/modules/analytics/application/services/etl_service.py
git commit -m "fix(analytics): fix IG DM sync — correct API URL, page token exchange, integrate into sync_all

- Changed API base from graph.instagram.com to graph.facebook.com
- Added page access token exchange (system user token → page token)
- Fixed config key: tracked_page_id instead of page_id
- Used /{page_id}/conversations instead of /me/conversations
- Integrated IG DM sync into run_sync_all() so sync button triggers it"
```

---

## Execution Order

| Priority | Task | Type | Time |
|---|---|---|---|
| 1 | Task 6 | Commit existing fixes | 2 min |
| 2 | Task 3 | Code: message_received bridge | 10 min |
| 3 | Task 1 | Config: Connect ManyChat in UI | 5 min |
| 4 | Task 2 | Config: ManyChat External Requests | 15 min |
| 5 | Task 4 | Config: Meta IG webhook subscription | 10 min |
| 6 | Task 5 | Config: Advanced Access request | 15 min |

**Tasks 1-2 and 4-5 are user actions** (UI config, Meta Dashboard, ManyChat builder).
**Tasks 3 and 6 are code changes** that can be executed by an agent.
