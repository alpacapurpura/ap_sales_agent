import { QueryClient } from "@tanstack/react-query";
import { describe, it, expect } from "vitest";

import { createTestQueryClient, createHookWrapper, mockAuth, mockRouter } from "./helpers";

describe("createTestQueryClient", () => {
  it("returns a QueryClient instance", () => {
    const client = createTestQueryClient();
    expect(client).toBeInstanceOf(QueryClient);
  });

  it("configures queries with no retries and no cache", () => {
    const client = createTestQueryClient();
    const defaults = client.getDefaultOptions();
    expect(defaults.queries?.retry).toBe(false);
    expect(defaults.queries?.gcTime).toBe(0);
  });

  it("configures mutations with no retries", () => {
    const client = createTestQueryClient();
    const defaults = client.getDefaultOptions();
    expect(defaults.mutations?.retry).toBe(false);
  });
});

describe("createHookWrapper", () => {
  it("returns a wrapper component and a queryClient", () => {
    const { wrapper, queryClient } = createHookWrapper();
    expect(typeof wrapper).toBe("function");
    expect(queryClient).toBeInstanceOf(QueryClient);
  });

  it("creates independent queryClients on each call", () => {
    const { queryClient: client1 } = createHookWrapper();
    const { queryClient: client2 } = createHookWrapper();
    expect(client1).not.toBe(client2);
  });
});

describe("mockAuth", () => {
  it("returns default auth values when called with no overrides", async () => {
    const auth = mockAuth();
    expect(auth.isLoaded).toBe(true);
    expect(auth.isSignedIn).toBe(true);
    expect(await auth.getToken()).toBe("mock-test-token");
  });

  it("applies overrides correctly", async () => {
    const customToken = async () => "custom-token" as string | null;
    const auth = mockAuth({ isSignedIn: false, getToken: customToken });
    expect(auth.isSignedIn).toBe(false);
    expect(await auth.getToken()).toBe("custom-token");
  });

  it("allows returning null from getToken", async () => {
    const auth = mockAuth({ getToken: async () => null });
    expect(await auth.getToken()).toBeNull();
  });
});

describe("mockRouter", () => {
  it("returns default router values when called with no overrides", async () => {
    const router = mockRouter();
    expect(router.pathname).toBe("/");
    expect(typeof router.push).toBe("function");
    expect(typeof router.replace).toBe("function");
    expect(typeof router.back).toBe("function");
    await expect(router.prefetch()).resolves.toBeUndefined();
  });

  it("applies pathname override correctly", () => {
    const router = mockRouter({ pathname: "/dashboard" });
    expect(router.pathname).toBe("/dashboard");
  });

  it("applies push override correctly", () => {
    const pushSpy = () => {};
    const router = mockRouter({ push: pushSpy });
    expect(router.push).toBe(pushSpy);
  });
});
