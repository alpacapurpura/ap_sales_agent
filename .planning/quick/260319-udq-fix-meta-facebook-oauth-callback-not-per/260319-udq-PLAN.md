---
phase: quick
plan: 260319-udq
type: execute
wave: 1
depends_on: []
files_modified:
  - frontend/src/app/connections/meta/callback/page.tsx
  - backend/src/modules/connections/api/meta.py
autonomous: true
requirements: [fix-meta-oauth-callback]

must_haves:
  truths:
    - "After granting Facebook permissions, user is redirected back and sees 'Meta Business Suite Conectado' status"
    - "Connection persists across page refresh (is_active=true, credentials stored)"
    - "Assets are synced and visible after successful OAuth"
  artifacts:
    - path: "frontend/src/app/connections/meta/callback/page.tsx"
      provides: "Robust Meta OAuth callback handler with retry logic"
    - path: "backend/src/modules/connections/api/meta.py"
      provides: "Meta OAuth callback with diagnostic logging"
  key_links:
    - from: "frontend callback page"
      to: "backend /meta/callback"
      via: "POST with code + redirect_uri"
      pattern: "fetchClient.*meta/callback"
    - from: "backend /meta/callback"
      to: "repo.upsert"
      via: "stores credentials with is_active=True"
      pattern: "repo\\.upsert"
---

<objective>
Fix Meta/Facebook OAuth callback not persisting connection state after permission grant.

Purpose: After granting Facebook permissions, users are redirected back to the connection page but see "Connect with Facebook" as if nothing happened. The OAuth flow completes on Meta's side but the connection is not reflected in the app.

Output: Working Meta OAuth flow where connection status is correctly persisted and displayed after redirect.
</objective>

<context>
@backend/src/modules/connections/api/meta.py
@backend/src/modules/connections/infrastructure/channels/meta.py
@frontend/src/app/connections/meta/callback/page.tsx
@frontend/src/features/connections/components/meta-view.tsx
@frontend/src/lib/http-client.ts
@frontend/src/lib/api/connections.ts
@backend/src/modules/iam/api/dependencies.py
</context>

<tasks>

<task type="auto">
  <name>Task 1: Fix Meta OAuth callback — auth race condition and silent failure handling</name>
  <files>frontend/src/app/connections/meta/callback/page.tsx</files>
  <action>
The root cause is a combination of issues in the frontend callback page:

1. **Clerk auth race condition after full-page redirect**: After Facebook redirects back to `/connections/meta/callback`, the Clerk auth provider may not have restored the session yet when `getToken()` is called. The current code calls `getToken()` once — if it returns null, it immediately redirects to `/sign-in`, losing the OAuth code entirely.

2. **fetchClient 401 interceptor**: Even if `getToken()` returns a value, if it's stale/expired, the backend returns 401 which `fetchClient` intercepts and redirects to `/sign-in` — the callback error handler never fires.

3. **Missing X-Tenant-ID on callback page**: The callback URL path `/connections/meta/callback` starts with `connections` which is in the `fetchClient` globals list, so tenant ID comes from `localStorage` only. If localStorage doesn't have it, the backend falls back to default tenant — which works but is fragile.

Fix the callback page with these changes:

a) **Add retry loop for getToken()** — Wait up to 5 seconds for Clerk to restore the session after the full-page redirect. Use a polling loop with 500ms intervals (max 10 attempts). This handles the race condition where Clerk needs time to hydrate after the browser redirect from Facebook.

b) **Bypass fetchClient for the callback POST** — Use native `fetch` directly instead of `fetchClient` to avoid the 401/403 interceptors silently redirecting away. The callback page needs full control over error handling. Still include the X-Tenant-ID header manually from sessionStorage (`meta_oauth_tenant_id`) or localStorage.

c) **Add error state UI** — Instead of silently redirecting on failure, show an error message on the callback page itself with a "Retry" button that re-triggers `handleCallback()`, and a "Go back" link. This prevents silent failures.

d) **Persist OAuth code in sessionStorage** — Before attempting the API call, save the `code` to sessionStorage so if the page refreshes during auth retry, the code is not lost (URL params are preserved anyway but this is defense-in-depth).

e) **Add diagnostic console.error logs** at each failure point so the user can provide browser console output for debugging.

Keep the existing logic: save tenantId to sessionStorage before redirect, read it back after callback, redirect to `/${tenantId}/settings?tab=meta` on success.
  </action>
  <verify>
Run TypeScript compilation check: `docker exec -it visionarias_client_dev npx tsc --noEmit --pretty 2>&1 | grep -E "(error|callback)" | head -20` — should show no errors in the callback file.
  </verify>
  <done>
Meta OAuth callback page retries getToken() with backoff, uses native fetch to avoid silent 401 redirects, shows error UI on failure instead of silently redirecting, and includes diagnostic logging.
  </done>
</task>

<task type="auto">
  <name>Task 2: Add backend diagnostic logging and response validation to Meta OAuth callback</name>
  <files>backend/src/modules/connections/api/meta.py</files>
  <action>
Add comprehensive logging to the backend `/callback` endpoint to diagnose exactly where failures occur in the OAuth flow:

1. **Log incoming request details** at the start of `oauth_callback`: log the tenant_id resolved from user, whether redirect_uri matches expected patterns, and the code length (not the code itself for security).

2. **Log after upsert**: After `repo.upsert()`, log the connection's `id`, `is_active`, and `channel_type` to confirm the DB write succeeded. Also verify by re-reading: call `repo.get_by_tenant_and_type(user.tenant_id, ChannelType.META)` immediately after upsert and log whether it returns a connection with `is_active=True` and a valid `access_token` in credentials. This catches cases where the DB commit silently fails or the upsert has a logic issue.

3. **Ensure the response includes `is_connected: True` explicitly** in the returned dict (it already does via `"is_connected": True` but verify it's always set).

4. **Add a `GET /debug-status` temporary endpoint** (or better, add a query param `?debug=true` to the existing `/status` endpoint) that returns additional diagnostic info: whether a connection row exists at all, its `is_active` value, whether credentials has `access_token`, and `updated_at` timestamp. This helps diagnose whether the issue is "connection not saved" vs "status endpoint reading wrong data". Guard behind `settings.DEBUG` or always enable it (it's behind auth anyway).

Do NOT change the core OAuth logic (exchange_code, upsert) — the backend flow is correct, we just need visibility into what's happening.
  </action>
  <verify>
Run linting: `docker exec -it visionarias_brain_dev ruff check src/modules/connections/api/meta.py --fix` — should pass with no errors.
  </verify>
  <done>
Backend Meta OAuth callback has diagnostic logging at each step (code exchange, profile fetch, upsert, verification read-back). Status endpoint can return debug info for troubleshooting.
  </done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>Fixed Meta OAuth callback flow with auth retry logic, error UI, and backend diagnostic logging</what-built>
  <how-to-verify>
    1. Navigate to /{tenantId}/settings and click the Meta tab
    2. Click "Conectar con Facebook" button
    3. Complete the Facebook permissions dialog (grant all permissions)
    4. After redirect back, you should see "Conectando con Meta..." briefly
    5. Then you should be redirected to /{tenantId}/settings?tab=meta showing "Meta Business Suite Conectado"
    6. If it fails, check browser console for diagnostic logs starting with "[Meta OAuth]"
    7. Also check backend logs: `docker logs visionarias_brain_dev 2>&1 | grep meta_oauth | tail -20`
    8. Refresh the page — connection should persist
    9. Click "Sincronizar activos" — should show your Pages, IG accounts, etc.
  </how-to-verify>
  <resume-signal>Type "approved" or describe what happened (error messages, console output, etc.)</resume-signal>
</task>

</tasks>

<verification>
- Frontend callback page compiles without TypeScript errors
- Backend meta.py passes ruff linting
- Full OAuth flow: click connect -> Facebook dialog -> redirect back -> connection persists
- Connection visible in status endpoint with is_connected=true
</verification>

<success_criteria>
After completing Meta OAuth permissions dialog, user is redirected back to settings page and sees "Meta Business Suite Conectado" with synced assets. Connection persists across page refresh.
</success_criteria>

<output>
After completion, create `.planning/quick/260319-udq-fix-meta-facebook-oauth-callback-not-per/260319-udq-SUMMARY.md`
</output>
