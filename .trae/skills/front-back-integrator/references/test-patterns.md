# Integration Test Patterns

Use these patterns to verify Frontend-Backend integration and multi-tenant isolation.

## 1. Backend Integration Test (Pytest + HTTPX)

This pattern verifies that the backend endpoint correctly handles tenant context and returns the expected data structure.

```python
import pytest
from httpx import AsyncClient
from backend.src.main import app  # Adjust import path
from backend.src.core.security import create_access_token

@pytest.mark.asyncio
async def test_endpoint_tenant_isolation(client: AsyncClient, db_session):
    # Setup: Create two tenants and users
    tenant_a_id = "tenant_a"
    tenant_b_id = "tenant_b"
    user_a = create_test_user(db_session, tenant_id=tenant_a_id)
    token_a = create_access_token(user_a.id)

    # 1. Happy Path: Access own data
    response = await client.get(
        "/api/v1/resource",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": tenant_a_id
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert all(item["tenant_id"] == tenant_a_id for item in data)

    # 2. Cross-Tenant Attempt: Access other tenant's context
    response = await client.get(
        "/api/v1/resource",
        headers={
            "Authorization": f"Bearer {token_a}",
            "X-Tenant-ID": tenant_b_id  # Mismatch!
        }
    )
    assert response.status_code == 403  # Should be forbidden

    # 3. Missing Context
    response = await client.get(
        "/api/v1/resource",
        headers={"Authorization": f"Bearer {token_a}"}
    )
    assert response.status_code == 400  # Or 403, depending on implementation
```

## 2. Frontend API Client Test (Jest/Vitest)

This pattern verifies that the frontend client correctly constructs requests with headers.

```typescript
import { fetchClient } from '@/lib/http-client';
import { renderHook, waitFor } from '@testing-library/react';
import { useResource } from './useResource';

// Mock fetch
global.fetch = jest.fn();

describe('useResource Integration', () => {
  it('sends X-Tenant-ID header', async () => {
    (fetch as jest.Mock).mockResolvedValueOnce({
      ok: true,
      json: async () => ({ data: [] }),
    });

    const { result } = renderHook(() => useResource('tenant_123'));

    await waitFor(() => result.current.isSuccess);

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining('/api/v1/resource'),
      expect.objectContaining({
        headers: expect.objectContaining({
          'X-Tenant-ID': 'tenant_123',
          'Authorization': expect.stringContaining('Bearer'),
        }),
      })
    );
  });
});
```

## 3. Manual Verification Checklist

When automated tests are not available, verify manually:

1.  **Open Browser DevTools (Network Tab)**.
2.  Perform the action in UI.
3.  **Inspect Request**:
    -   Method: GET/POST/PUT/DELETE
    -   URL: Correct API version? (`/api/v1/...`)
    -   Headers: `X-Tenant-ID` present? `Authorization` present?
4.  **Inspect Response**:
    -   Status: 200 OK?
    -   Payload: Matches UI expectations?
    -   Preview: No "Internal Server Error" or HTML stack trace?
5.  **Check Backend Logs**:
    -   Does the log show `tenant_id=...` in the context?
    -   Are there any SQL errors related to missing columns?
