import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import type { LandingStatusResponse } from "../../types/landing-status";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockGetStatus = vi.fn();

vi.mock("../../api/landing-api", () => ({
  landingApi: {
    getStatus: (...args: unknown[]) => mockGetStatus(...args),
    generate: vi.fn(),
    regenerate: vi.fn(),
    publish: vi.fn(),
    unpublish: vi.fn(),
  },
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn(), error: vi.fn() },
}));

// ── Imports after mocks ──────────────────────────────────────────────────────

import { deriveLandingUiState, useLandingStatus } from "../use-landing-status";

// ── Helpers ──────────────────────────────────────────────────────────────────

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });
  function Wrapper({ children }: { children: React.ReactNode }) {
    return React.createElement(QueryClientProvider, { client: queryClient }, children);
  }
  return Wrapper;
}

const baseStatus: LandingStatusResponse = {
  offer_id: "offer-1",
  landing_page_id: null,
  is_generated: false,
  is_published: false,
  is_outdated: false,
  generated_at: null,
  offer_snapshot_version: null,
  offer_updated_at: "2026-04-10T00:00:00Z",
  job_id: null,
  job_status: "idle",
  landing_url: null,
  editor_url: null,
  completion_percentage: 50,
};

// ── deriveLandingUiState ─────────────────────────────────────────────────────

describe("deriveLandingUiState", () => {
  it("returns 'disabled' when completion < 90 and not generated", () => {
    expect(deriveLandingUiState({ ...baseStatus, completion_percentage: 50 })).toBe("disabled");
  });

  it("returns 'ready-to-generate' when completion >= 90 and not generated", () => {
    expect(deriveLandingUiState({ ...baseStatus, completion_percentage: 95 })).toBe(
      "ready-to-generate",
    );
  });

  it("returns 'in-sync' when generated and not outdated", () => {
    expect(
      deriveLandingUiState({
        ...baseStatus,
        completion_percentage: 100,
        is_generated: true,
        is_outdated: false,
      }),
    ).toBe("in-sync");
  });

  it("returns 'outdated' when generated but offer changed afterwards", () => {
    expect(
      deriveLandingUiState({
        ...baseStatus,
        completion_percentage: 100,
        is_generated: true,
        is_outdated: true,
      }),
    ).toBe("outdated");
  });

  it("treats completion_percentage exactly 90 as ready-to-generate", () => {
    expect(deriveLandingUiState({ ...baseStatus, completion_percentage: 90 })).toBe(
      "ready-to-generate",
    );
  });
});

// ── useLandingStatus ─────────────────────────────────────────────────────────

describe("useLandingStatus", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    Object.defineProperty(globalThis, "localStorage", {
      value: {
        getItem: vi.fn().mockReturnValue("test-tenant"),
        setItem: vi.fn(),
        removeItem: vi.fn(),
        clear: vi.fn(),
        length: 0,
        key: vi.fn(),
      },
      writable: true,
      configurable: true,
    });
  });

  it("exposes derived uiState once the query resolves", async () => {
    mockGetStatus.mockResolvedValue({
      ...baseStatus,
      completion_percentage: 100,
      is_generated: true,
      is_outdated: false,
    });

    const { result } = renderHook(() => useLandingStatus("offer-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.uiState).toBe("in-sync");
  });

  it("exposes uiState='disabled' when completion is below threshold", async () => {
    mockGetStatus.mockResolvedValue({
      ...baseStatus,
      completion_percentage: 45,
    });

    const { result } = renderHook(() => useLandingStatus("offer-1"), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.uiState).toBe("disabled");
  });
});
