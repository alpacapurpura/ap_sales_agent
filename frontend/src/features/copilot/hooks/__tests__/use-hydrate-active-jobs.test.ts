import { renderHook } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── Mocks ────────────────────────────────────────────────────────────────────

const mockGetToken = vi.fn();

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: mockGetToken,
    isLoaded: true,
    isSignedIn: true,
  }),
}));

// Mock fetchActiveJobs — controlled per test
const mockFetchActiveJobs = vi.fn();
vi.mock("../../api/copilot-api", () => ({
  fetchActiveJobs: (conversationId: string, token: string) =>
    mockFetchActiveJobs(conversationId, token),
  getCopilotHeaders: (token: string) => ({ Authorization: `Bearer ${token}` }),
}));

// Store mocks
const mockRegisterJob = vi.fn();
let storeActiveJobs: Record<string, unknown> = {};

vi.mock("../../store/copilot-store", () => ({
  useCopilotStore: {
    getState: () => ({
      registerJob: mockRegisterJob,
      activeJobs: storeActiveJobs,
    }),
  },
}));

// ── Helpers ──────────────────────────────────────────────────────────────────

function makeDto(overrides: Partial<Record<string, unknown>> = {}) {
  return {
    job_id: "job-123",
    module: "brand",
    entity_id: "entity-456",
    source_kind: "url",
    source_ref: "https://example.com",
    scope: "full",
    mode: "initial",
    started_at: "2024-01-01T00:00:00Z",
    status: "running",
    progress: 42,
    stage: "Analizando...",
    filled_fields: ["brand_name"],
    filled_fields_by_section: { identity: ["brand_name"] },
    sections_touched: ["identity"],
    sections_completed: [],
    finished_at: null,
    poll_endpoint: "/api/v1/brand/tools/extract/status/job-123",
    ...overrides,
  };
}

// ── Tests ─────────────────────────────────────────────────────────────────────

describe("useHydrateActiveJobs", () => {
  beforeEach(() => {
    vi.resetAllMocks();
    storeActiveJobs = {};
    mockGetToken.mockResolvedValue("mock-token");
    mockFetchActiveJobs.mockResolvedValue(null);
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("does not fetch when conversationId is null", async () => {
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    renderHook(() => useHydrateActiveJobs(null));

    await vi.waitFor(() => {
      expect(mockFetchActiveJobs).not.toHaveBeenCalled();
    });
    expect(mockRegisterJob).not.toHaveBeenCalled();
  });

  it("does not fetch when conversationId is undefined", async () => {
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    renderHook(() => useHydrateActiveJobs(undefined));

    await vi.waitFor(() => {
      expect(mockFetchActiveJobs).not.toHaveBeenCalled();
    });
    expect(mockRegisterJob).not.toHaveBeenCalled();
  });

  it("does not call registerJob when jobs array is empty", async () => {
    mockFetchActiveJobs.mockResolvedValueOnce([]);
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    renderHook(() => useHydrateActiveJobs("conv-abc"));

    await vi.waitFor(() => {
      expect(mockFetchActiveJobs).toHaveBeenCalledWith("conv-abc", "mock-token");
    });
    expect(mockRegisterJob).not.toHaveBeenCalled();
  });

  it("calls registerJob with mapped AsyncJobState for a running job", async () => {
    const dto = makeDto({ status: "running" });
    mockFetchActiveJobs.mockResolvedValueOnce([dto]);
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    renderHook(() => useHydrateActiveJobs("conv-abc"));

    await vi.waitFor(() => {
      expect(mockRegisterJob).toHaveBeenCalledTimes(1);
    });

    const registered = mockRegisterJob.mock.calls[0][0] as Record<string, unknown>;
    expect(registered.jobId).toBe("job-123");
    expect(registered.module).toBe("brand");
    expect(registered.entityId).toBe("entity-456");
    expect(registered.sourceKind).toBe("url");
    expect(registered.sourceRef).toBe("https://example.com");
    expect(registered.status).toBe("running");
    expect(registered.progress).toBe(42);
    expect(registered.stage).toBe("Analizando...");
    expect(registered.filledFields).toEqual(["brand_name"]);
    expect(registered.filledFieldsBySection).toEqual({ identity: ["brand_name"] });
    expect(registered.sectionsTouched).toEqual(["identity"]);
    expect(registered.sectionsCompleted).toEqual([]);
    expect(registered.conversationId).toBe("conv-abc");
    expect(registered.pollEndpoint).toBe("/api/v1/brand/tools/extract/status/job-123");
    expect(typeof registered.startedAt).toBe("number");
    expect(registered.finishedAt).toBeUndefined();
  });

  it("does not call registerJob for a completed job (terminal skip)", async () => {
    const dto = makeDto({ status: "completed", finished_at: "2024-01-01T01:00:00Z" });
    mockFetchActiveJobs.mockResolvedValueOnce([dto]);
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    renderHook(() => useHydrateActiveJobs("conv-abc"));

    await vi.waitFor(() => {
      expect(mockFetchActiveJobs).toHaveBeenCalledTimes(1);
    });
    expect(mockRegisterJob).not.toHaveBeenCalled();
  });

  it("does not call registerJob for a failed job (terminal skip)", async () => {
    const dto = makeDto({ status: "failed", finished_at: "2024-01-01T01:00:00Z" });
    mockFetchActiveJobs.mockResolvedValueOnce([dto]);
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    renderHook(() => useHydrateActiveJobs("conv-abc"));

    await vi.waitFor(() => {
      expect(mockFetchActiveJobs).toHaveBeenCalledTimes(1);
    });
    expect(mockRegisterJob).not.toHaveBeenCalled();
  });

  it("skips job already tracked in store (idempotent)", async () => {
    storeActiveJobs = { "job-123": { jobId: "job-123", status: "running" } };
    const dto = makeDto({ status: "running" });
    mockFetchActiveJobs.mockResolvedValueOnce([dto]);
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    renderHook(() => useHydrateActiveJobs("conv-abc"));

    await vi.waitFor(() => {
      expect(mockFetchActiveJobs).toHaveBeenCalledTimes(1);
    });
    expect(mockRegisterJob).not.toHaveBeenCalled();
  });

  it("silently swallows fetch error without throwing or registering", async () => {
    mockFetchActiveJobs.mockResolvedValueOnce(null);
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    expect(() => {
      renderHook(() => useHydrateActiveJobs("conv-abc"));
    }).not.toThrow();

    await vi.waitFor(() => {
      expect(mockFetchActiveJobs).toHaveBeenCalledTimes(1);
    });
    expect(mockRegisterJob).not.toHaveBeenCalled();
  });

  it("silently swallows getToken error without throwing or registering", async () => {
    mockGetToken.mockRejectedValueOnce(new Error("Auth expired"));
    const { useHydrateActiveJobs } = await import("../use-hydrate-active-jobs");

    expect(() => {
      renderHook(() => useHydrateActiveJobs("conv-abc"));
    }).not.toThrow();

    // fetchActiveJobs should not be called if token unavailable
    await vi.waitFor(() => {
      expect(mockFetchActiveJobs).not.toHaveBeenCalled();
    });
    expect(mockRegisterJob).not.toHaveBeenCalled();
  });
});
