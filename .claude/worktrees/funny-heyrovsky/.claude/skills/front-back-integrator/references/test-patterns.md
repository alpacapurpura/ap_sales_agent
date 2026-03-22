# Integration Test Patterns

Patrones para verificar la integracion Frontend-Backend y el aislamiento multi-tenant.

## 1. Backend Integration Test (Pytest + HTTPX)

Verifica que el endpoint del backend maneja correctamente el contexto de tenant y retorna la estructura de datos esperada.

```python
import pytest
from httpx import AsyncClient
from backend.src.main import app
from backend.src.core.security import create_access_token

@pytest.mark.asyncio
async def test_endpoint_tenant_isolation(client: AsyncClient, db_session):
    # Setup: Crear dos tenants y usuarios
    tenant_a_id = "tenant_a"
    tenant_b_id = "tenant_b"
    user_a = create_test_user(db_session, tenant_id=tenant_a_id)
    token_a = create_access_token(user_a.id)

    # 1. Happy Path: Acceder a datos propios
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

    # 2. Cross-Tenant Attempt: Acceder al contexto de otro tenant
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

Verifica que el cliente frontend construye correctamente los requests con headers.

```typescript
import { fetchClient } from '@/lib/http-client';
import { renderHook, waitFor } from '@testing-library/react';
import { useResource } from './useResource';

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

## 3. Checklist de Verificacion Manual

Cuando no hay tests automatizados disponibles:

1. **Abrir Browser DevTools (Network Tab)**.
2. Realizar la accion en la UI.
3. **Inspeccionar Request**:
   - Method: GET/POST/PUT/DELETE
   - URL: Version de API correcta? (`/api/v1/...`)
   - Headers: `X-Tenant-ID` presente? `Authorization` presente?
4. **Inspeccionar Response**:
   - Status: 200 OK?
   - Payload: Coincide con las expectativas de la UI?
   - Preview: No hay "Internal Server Error" o HTML stack trace?
5. **Verificar Backend Logs**:
   - El log muestra `tenant_id=...` en el contexto?
   - Hay errores SQL relacionados con columnas faltantes?
