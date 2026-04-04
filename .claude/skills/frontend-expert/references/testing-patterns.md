# Frontend Testing Patterns

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

- Run: `make vitest-cov` or `docker exec -t visionarias_client_dev npx vitest run --coverage`
- Thresholds: statements 5%, branches 3%, functions 3%, lines 5%
- CI will fail below these thresholds

## Execution (Docker-First)

```bash
# All tests
docker exec -t visionarias_client_dev npx vitest run

# Single feature
docker exec -t visionarias_client_dev npx vitest run src/features/copilot/

# With coverage
docker exec -t visionarias_client_dev npx vitest run --coverage
```

## Naming Convention

- Test files: `component-name.test.tsx` or `hook-name.test.ts`
- Describe blocks: feature/component name
- Test names: describe behavior, not implementation
