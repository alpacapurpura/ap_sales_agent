# Frontend Testing Patterns

## TDD Protocol (OBLIGATORIO)

**REGLA NO NEGOCIABLE:** Tests PRIMERO, implementación DESPUÉS.

1. **Hooks:** `hook-name.test.ts` con comportamiento esperado (RED) → implementar hook (GREEN)
2. **Components:** `component-name.test.tsx` con renders esperados (RED) → implementar (GREEN)
3. **Stores:** `store-name.test.ts` con estado esperado (RED) → implementar (GREEN)

Feature existente sin tests → cubrir comportamiento actual (baseline) → luego test del cambio (RED) → implementar (GREEN).

---

## Stack

- **Vitest** (happy-dom environment)
- **@testing-library/react** (render, screen, renderHook)
- **@testing-library/jest-dom** (matchers)
- Config: `frontend/vitest.config.mts`
- Setup: `frontend/src/test/setup.ts`

## Shared Test Helpers

```typescript
import { createTestQueryClient, createHookWrapper, mockAuth, mockRouter } from '@/test/helpers';
```

- `createTestQueryClient()` — QueryClient with `retry: false, gcTime: 0`
- `createHookWrapper()` — Returns `{ wrapper: QueryClientProvider, queryClient }`
- `mockAuth(overrides?)` — Standard mock for `@clerk/nextjs` useAuth
- `mockRouter(overrides?)` — Standard mock for `next/navigation`

## Test File Structure

```
features/{domain}/__tests__/
  component-name.test.tsx    # Component tests
  hook-name.test.ts          # Hook tests
  util-name.test.ts          # Utility tests
```

## Hook Testing Pattern

```typescript
import React from 'react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { createHookWrapper } from '@/test/helpers';

// Mock API adapter
const mockFetch = vi.fn();
vi.mock('@/features/domain/api', () => ({
  fetchData: (...args: unknown[]) => mockFetch(...args),
}));

// Mock auth
vi.mock('@clerk/nextjs', () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue('mock-test-token'),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

describe('useCustomHook', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('returns loading state initially', () => {
    mockFetch.mockReturnValue(new Promise(() => {}));
    const { wrapper } = createHookWrapper();
    const { result } = renderHook(() => useCustomHook(), { wrapper });
    expect(result.current.isLoading).toBe(true);
  });

  it('returns data on success', async () => {
    mockFetch.mockResolvedValue(mockData);
    const { wrapper } = createHookWrapper();
    const { result } = renderHook(() => useCustomHook(), { wrapper });
    await waitFor(() => expect(result.current.isSuccess).toBe(true));
    expect(result.current.data).toEqual(mockData);
  });
});
```

## Component Testing Pattern

```typescript
import React from 'react';
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ComponentName } from '../ComponentName';

describe('ComponentName', () => {
  it('renders with expected content', () => {
    render(<ComponentName value={42} />);
    expect(screen.getByText('42')).toBeInTheDocument();
  });

  it('applies correct styles for variant', () => {
    const { container } = render(<ComponentName variant="success" />);
    expect(container.firstChild).toHaveClass('bg-green-500');
  });
});
```

## Zustand Store Testing

No React rendering needed — test directly via getState/setState:

```typescript
import { describe, it, expect, beforeEach } from 'vitest';
import { useMyStore } from '../my-store';

describe('myStore', () => {
  beforeEach(() => {
    useMyStore.setState(useMyStore.getInitialState());
  });

  it('toggles panel', () => {
    useMyStore.getState().togglePanel();
    expect(useMyStore.getState().isOpen).toBe(true);
  });
});
```

## Mocking Patterns

### Mock fetch (global)
```typescript
const originalFetch = globalThis.fetch;
beforeEach(() => { globalThis.fetch = vi.fn(); });
afterEach(() => { globalThis.fetch = originalFetch; });
```

### Mock window.open
```typescript
vi.stubGlobal('open', vi.fn());
```

### Mock localStorage
```typescript
Object.defineProperty(globalThis, 'localStorage', {
  value: { getItem: vi.fn().mockReturnValue('tenant-id'), setItem: vi.fn() },
  writable: true, configurable: true,
});
```

## Coverage

- Run: `cd frontend && npx vitest run --coverage`
- Thresholds: **all 20%** (statements, branches, functions, lines)
- CI will fail below these thresholds
- The skill `/test-frontend` already includes coverage automatically

## Execution (Native — NEVER use docker exec)

```bash
# All tests
cd frontend && npx vitest run

# Single feature
cd frontend && npx vitest run src/features/copilot/

# With coverage
cd frontend && npx vitest run --coverage
```

## E2E Testing con Playwright

Para detalles completos, ver `.claude/rules/e2e-testing.md`.

### Cuándo escribir E2E
- Feature nueva con UI (page, form, widget)
- Bug fix que afecta interacción de usuario
- Cambios en navegación o flujo de auth

### Estructura
- Smoke tests: `frontend/e2e/specs/smoke/` — rutas críticas, taggeados `@smoke`
- Regression tests: `frontend/e2e/specs/regression/{domain}/` — flujos completos por dominio

### Ejecución (nativo en WSL, NUNCA Docker)
```bash
# Smoke (~2 min)
cd frontend && npx playwright test --project=smoke

# Regression (más lento)
cd frontend && npx playwright test --project=regression

# Test específico
cd frontend && npx playwright test --project=smoke --grep "test-name"
```

### Page Object Model
- Un POM por página en `frontend/e2e/pages/`
- Locators: `getByRole`, `getByText`, `getByLabel` — NUNCA selectores CSS
- Usar `.first()` en locators que puedan matchear >1 elemento (strict mode)

## Naming Convention

- Test files: `component-name.test.tsx` or `hook-name.test.ts`
- Describe blocks: feature/component name
- Test names: describe behavior, not implementation
