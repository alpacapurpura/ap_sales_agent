---
phase: quick
plan: 260317-tng
type: execute
wave: 1
depends_on: []
files_modified:
  - backend/src/modules/connections/api/meta.py
  - backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py
  - frontend/src/app/connections/meta/callback/page.tsx
autonomous: true
requirements: [quick-260317-tng]

must_haves:
  truths:
    - "After Meta OAuth callback, assets are automatically synced without user clicking Sync"
    - "All Facebook Pages, Instagram Business accounts, and Ad Accounts from the Meta API appear in the assets list"
    - "When a tenant has multiple assets of the same type (e.g. 2 Facebook Pages), each is stored as a separate DB row"
    - "Toggling individual assets on/off still works correctly"
  artifacts:
    - path: "backend/src/modules/connections/api/meta.py"
      provides: "Auto-sync in oauth_callback, fixed asset creation in sync_assets"
    - path: "backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py"
      provides: "New create_asset method for multi-row asset storage"
    - path: "frontend/src/app/connections/meta/callback/page.tsx"
      provides: "Triggers sync after successful OAuth and passes result to redirect"
  key_links:
    - from: "frontend/src/app/connections/meta/callback/page.tsx"
      to: "backend POST /api/v1/connections/meta/assets/sync"
      via: "fetchClient POST call after successful OAuth callback"
      pattern: "connections/meta/assets/sync"
    - from: "backend/src/modules/connections/api/meta.py sync_assets"
      to: "channel_connection_repository.create_asset"
      via: "direct call for NEW asset rows (not upsert)"
      pattern: "repo\\.create_asset"
---

<objective>
Fix Meta Business Suite asset sync: (1) assets don't auto-sync after OAuth connection, (2) repository upsert bug silently overwrites assets when tenant has multiple assets of the same channel type (e.g. 2 Facebook Pages).

Purpose: After connecting Meta, users expect to immediately see their Pages, Instagram accounts, and Ad accounts with toggles. Currently they must manually click "Sync" and the repository bug can cause asset data loss.
Output: Working auto-sync flow after OAuth, correct multi-asset storage.
</objective>

<execution_context>
@/home/chris/AISALESHT/.claude/get-shit-done/workflows/execute-plan.md
@/home/chris/AISALESHT/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@backend/src/modules/connections/api/meta.py
@backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py
@backend/src/modules/connections/infrastructure/models/channel_connection_model.py
@backend/src/modules/connections/domain/enums.py
@frontend/src/app/connections/meta/callback/page.tsx
@frontend/src/features/connections/components/meta-view.tsx

<interfaces>
From backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py:
```python
class ChannelConnectionRepository:
    def get_by_tenant_and_type(self, tenant_id, channel_type) -> Optional[ChannelConnectionModel]
    def get_by_asset_id(self, tenant_id, channel_type, asset_id) -> Optional[ChannelConnectionModel]
    def upsert(self, tenant_id, channel_type, credentials, config) -> ChannelConnectionModel
    # upsert internally calls get_by_tenant_and_type -- returns FIRST match
    # BUG: For asset types (FACEBOOK_PAGE, INSTAGRAM_ACCOUNT, META_ADS_ACCOUNT)
    # multiple rows per tenant per type are expected, but upsert always finds
    # the first one and overwrites it instead of creating a new row.
```

From backend/src/modules/connections/domain/enums.py:
```python
class ChannelType(str, Enum):
    META = "meta"                        # master credential
    FACEBOOK_PAGE = "facebook_page"      # per-page asset
    INSTAGRAM_ACCOUNT = "instagram_account"
    META_ADS_ACCOUNT = "meta_ads_account"
```
</interfaces>
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix repository asset creation and backend auto-sync</name>
  <files>
    backend/src/modules/connections/infrastructure/repositories/channel_connection_repository.py,
    backend/src/modules/connections/api/meta.py
  </files>
  <action>
**Repository fix -- add `create_asset` method:**

In `channel_connection_repository.py`, add a new method `create_asset` that always creates a NEW row (never upserts by tenant+type). This is needed because asset channel types (FACEBOOK_PAGE, INSTAGRAM_ACCOUNT, META_ADS_ACCOUNT) can have multiple rows per tenant:

```python
def create_asset(self, tenant_id, channel_type, credentials, config):
    """Create a new asset connection row. Unlike upsert(), this always inserts."""
    connection = ChannelConnectionModel(
        tenant_id=tenant_id,
        channel_type=channel_type.value,
        credentials=credentials,
        config=config,
        is_active=True,
    )
    self.db.add(connection)
    self.db.commit()
    self.db.refresh(connection)
    return connection
```

**Fix `sync_assets` in meta.py:**

In the `sync_assets` endpoint, replace the three `repo.upsert(...)` calls (for pages, instagram, ads) in the "else" branches with `repo.create_asset(...)`. The `upsert` method finds the first row matching (tenant_id, channel_type) and overwrites it, which is wrong when creating the 2nd+ asset of the same type. The existing `if conn:` branches (updating existing assets found by `get_by_asset_id`) are correct and should stay.

Specifically change these three locations:
1. Line ~383-388 (pages else branch): `repo.upsert(...)` -> `repo.create_asset(...)`
2. Line ~410-415 (instagram else branch): `repo.upsert(...)` -> `repo.create_asset(...)`
3. Line ~432-437 (ads else branch): `repo.upsert(...)` -> `repo.create_asset(...)`

**Add auto-sync to `oauth_callback`:**

In the `oauth_callback` endpoint, after the successful `repo.upsert` for the master META connection, add an automatic asset sync. Call `adapter.get_business_assets()` and run the same upsert logic. To avoid code duplication, extract the asset-sync logic into a private helper function `_sync_assets_for_tenant(adapter, repo, tenant_id, master)` and call it from both `sync_assets` endpoint and `oauth_callback`. The helper should:
1. Call `adapter.get_business_assets()`
2. Load existing assets via `repo.get_all_by_tenant_and_types()`
3. For each asset: `get_by_asset_id` -> update if exists, `create_asset` if new
4. Return the raw asset dict

Wrap the auto-sync in a try/except so that if it fails (e.g. token issue), the OAuth connection itself still succeeds -- just log a warning and return `assets_synced: false` in the response. If sync succeeds, return `assets_synced: true` and the asset counts.

Update the `oauth_callback` return to:
```python
return {"status": "connected", "profile": profile, "assets_synced": assets_synced}
```
  </action>
  <verify>
    <automated>docker exec -t visionarias_brain_dev python -c "from src.modules.connections.infrastructure.repositories.channel_connection_repository import ChannelConnectionRepository; print('create_asset' in dir(ChannelConnectionRepository))"</automated>
  </verify>
  <done>
    - `create_asset` method exists in repository and always creates new rows
    - `sync_assets` endpoint uses `create_asset` for new assets (not `upsert`)
    - `oauth_callback` automatically syncs assets after connecting
    - Auto-sync failure does not break the OAuth flow
  </done>
</task>

<task type="auto">
  <name>Task 2: Frontend auto-sync after OAuth callback redirect</name>
  <files>frontend/src/app/connections/meta/callback/page.tsx</files>
  <action>
In `frontend/src/app/connections/meta/callback/page.tsx`, after the successful POST to `/connections/meta/callback`, trigger the asset sync so that by the time the user lands on the settings page, assets are already loaded.

After the `response.ok` check and before the `router.push`, add a POST call to `/api/v1/connections/meta/assets/sync`:

```typescript
// Auto-sync assets after successful OAuth
try {
  await fetchClient(`${config.api.baseUrl}/api/v1/connections/meta/assets/sync`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}` },
  });
} catch {
  // Non-blocking — backend oauth_callback may have already synced
}
```

This is a belt-and-suspenders approach: the backend `oauth_callback` now also auto-syncs, but if that failed for any reason, this frontend call provides a second chance. The call is non-blocking (catch swallows errors) so it never prevents the redirect.

Update the success toast to: `"Meta conectado - activos sincronizados"`.
  </action>
  <verify>
    <automated>docker exec -t visionarias_client_dev sh -c "cd /app && npx next lint --file src/app/connections/meta/callback/page.tsx 2>&1 | tail -5"</automated>
  </verify>
  <done>
    - Callback page triggers POST /assets/sync after successful OAuth
    - Sync failure does not block redirect to settings page
    - Toast message updated to indicate asset sync
  </done>
</task>

</tasks>

<verification>
1. Backend: `docker exec -t visionarias_brain_dev python -c "from src.modules.connections.api.meta import router; print('OK')"` -- imports without error
2. Backend: Verify `create_asset` method exists and `sync_assets` no longer calls `upsert` for new assets
3. Frontend: `docker exec -t visionarias_client_dev sh -c "cd /app && npx next build 2>&1 | tail -10"` -- builds without error
4. Manual: Connect Meta -> should auto-redirect with assets already visible (no manual sync needed)
</verification>

<success_criteria>
- After OAuth callback, user lands on settings page with assets already listed (Pages, IG accounts, Ad accounts visible with toggles)
- Multiple assets of the same type (e.g. 2 Facebook Pages) are stored as separate rows, not overwritten
- Manual "Sincronizar activos" button still works as fallback
- OAuth connection succeeds even if asset sync fails
</success_criteria>

<output>
After completion, create `.planning/quick/260317-tng-revisar-bug-en-configuraci-n-conexi-n-me/260317-tng-SUMMARY.md`
</output>
