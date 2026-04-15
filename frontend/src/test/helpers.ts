import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import React from "react";

/**
 * Creates a QueryClient configured for testing (no retries, no cache).
 */
export function createTestQueryClient(): QueryClient {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
}

/**
 * Creates a wrapper component with QueryClientProvider for renderHook tests.
 */
export function createHookWrapper() {
  const queryClient = createTestQueryClient();
  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  }
  return { wrapper: Wrapper, queryClient };
}

/**
 * Standard mock for @clerk/nextjs useAuth.
 */
export function mockAuth(
  overrides?: Partial<{
    getToken: () => Promise<string | null>;
    isLoaded: boolean;
    isSignedIn: boolean;
  }>,
) {
  return {
    getToken: overrides?.getToken ?? (async () => "mock-test-token"),
    isLoaded: overrides?.isLoaded ?? true,
    isSignedIn: overrides?.isSignedIn ?? true,
    ...overrides,
  };
}

/**
 * Standard mock for next/navigation.
 */
export function mockRouter(
  overrides?: Partial<{
    push: (...args: unknown[]) => void;
    replace: (...args: unknown[]) => void;
    back: () => void;
    params: Record<string, string>;
    pathname: string;
  }>,
) {
  return {
    push: overrides?.push ?? (() => {}),
    replace: overrides?.replace ?? (() => {}),
    back: overrides?.back ?? (() => {}),
    prefetch: () => Promise.resolve(),
    pathname: overrides?.pathname ?? "/",
    ...overrides,
  };
}
