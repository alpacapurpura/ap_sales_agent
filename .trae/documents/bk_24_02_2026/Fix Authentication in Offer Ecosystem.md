I have confirmed that the error is caused by the missing authentication token in the API call to list offers. The backend rejects the request with "Not authenticated" (401/403) because the frontend is not sending the Clerk JWT.

### Plan to Fix "Ecosistema de Ofertas" Authentication

1.  **Update API Service (`frontend/src/lib/api/offer.ts`)**:
    *   Modify `listOffers` to accept a `token: string` argument.
    *   Add the `Authorization: Bearer ${token}` header to the `fetch` request.
    *   This aligns with the project's standard pattern seen in `admin.ts` and `avatar.ts`.

2.  **Update Component (`frontend/src/components/offer-studio/offer-dashboard.tsx`)**:
    *   Inject the `useAuth` hook from `@clerk/nextjs`.
    *   Retrieve the token using `await getToken()` before calling the API.
    *   Pass the token to `offerApi.listOffers(token)`.

This will ensure the backend receives the user's credentials and tenant context, resolving the "Not authenticated" and "Forbidden" errors.
