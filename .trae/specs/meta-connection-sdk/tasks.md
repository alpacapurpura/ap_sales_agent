# Tasks

- [x] Task 1: Setup Environment and Dependencies
  - [x] Add `facebook-business` to `backend/requirements.txt`.
  - [x] Add `META_APP_ID` and `META_APP_SECRET` to `backend/.env` (and `.env.example`).
  - [x] Install dependencies (`pip install -r backend/requirements.txt`).

- [x] Task 2: Refactor Meta Adapter to use SDK
  - [x] Modify `backend/src/modules/connections/infrastructure/channels/meta.py`:
    - [x] Import `facebook_business`.
    - [x] Implement `init_api` method using `FacebookAdsApi.init`.
    - [x] Update `get_authorization_url` to use global config.
    - [x] Update `exchange_code` to use SDK (if supported) or `httpx` with global config.
    - [x] Update `get_user_profile`, `get_ad_accounts`, `get_pages` to use SDK objects (`User`, `AdAccount`, `Page`).

- [x] Task 3: Update API Endpoints
  - [x] Modify `backend/src/modules/connections/api/meta.py`:
    - [x] Update `get_auth_url` to use `MetaAdapter` with global config.
    - [x] Update `oauth_callback` to handle token exchange and storage.
    - [x] Update `test_connection` to verify SDK initialization.
    - [x] (Optional) Mark `update_config` as deprecated or admin-only.

- [x] Task 4: Frontend Integration
  - [x] Create `MetaConnectButton.tsx` in `frontend/src/features/marketing-studio/components/connections/`.
  - [x] Update `ConnectionsView.tsx` to use `MetaConnectButton`.
  - [x] Implement `useMetaAuth` hook (or similar) to handle the OAuth redirect and callback logic.
  - [x] Add "Test Connection" button to `ConnectionsView` (visible only when connected).
  - [x] Implement `handleTestConnection` function to call `/test` endpoint and show toast notification.

- [x] Task 5: Verification
  - [x] Verify OAuth flow manually (Click -> Redirect -> Success).
  - [x] Verify `get_ad_accounts` returns data via `test` endpoint.
