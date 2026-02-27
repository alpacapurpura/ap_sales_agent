## 1. Fix Infinite Redirect Loop in `RootLayout`

* Edit `frontend/src/app/layout.tsx`:

  * Remove `<SignedIn>`, `<SignedOut>`, and `<RedirectToSignIn />` components.

  * Render `{children}` directly inside `<Providers>`. This allows public pages (like `/sign-in`) to render without forcing a redirect.

## 2. Implement Correct Protection in Middleware

* Edit `frontend/src/middleware.ts`:

  * Change the logic from "protect specific routes" to "protect all routes EXCEPT public ones".

  * Define `isPublicRoute` matching `/sign-in(.*)` and `/sign-up(.*)`.

  * Enforce `auth.protect()` for any route that is NOT public.

## 3. Verification

* Verify that accessing `http://salesagent.local/` redirects to `/sign-in`.

* Verify that accessing `http://salesagent.local/sign-in` renders the sign-in form without looping.

