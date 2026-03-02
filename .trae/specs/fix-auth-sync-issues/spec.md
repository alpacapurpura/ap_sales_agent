# Fix Auth Sync & Frontend Routing Spec

## Why
User `nicolify.ai@gmail.com` is experiencing a "Failed to fetch" error.
1.  **Frontend Bug**: The `fetchClient` incorrectly treats `/onboarding` as a Tenant ID, sending `X-Tenant-ID: onboarding` header which causes 400 Bad Request.
2.  **Auth Sync**: The user might be in the DB by email (invited/pre-created) but missing `clerk_id` or other details, or the webhook failed to update them. We need to ensure that login **synchronizes** the user details from Clerk **only if** the email already exists in the system.

## What Changes
-   **Frontend**:
    -   Update `src/lib/http-client.ts` to exclude `onboarding` from tenant ID extraction.
-   **Backend**:
    -   Update `src/modules/iam/api/dependencies.py` to implement **Safe User Synchronization**.
    -   **Logic**:
        1.  Extract email from Clerk Token.
        2.  Check if email exists in `users` table.
        3.  **IF EXISTS**: Update `clerk_id`, `full_name`, and `image_url` from Clerk data if they are missing or outdated. Return the user.
        4.  **IF NOT EXISTS**: Deny access (403). **DO NOT** create new users automatically.

## Impact
-   **IAM**: Ensures users pre-created by email can successfully log in and bind their Clerk identity.
-   **Frontend**: Fixed 400 errors on onboarding page.

## ADDED Requirements
### Requirement: Safe User Synchronization
The system SHALL update the local user record with Clerk data (ID, Name, Avatar) upon successful token verification, **ONLY IF** the user's email already exists in the local database.

## MODIFIED Requirements
### Requirement: Tenant Context Extraction
**Original**: `fetchClient` treats the first path segment as `tenant_id` unless in `globals`.
**Modified**: `fetchClient` MUST also exclude `onboarding` from `tenant_id` extraction.
