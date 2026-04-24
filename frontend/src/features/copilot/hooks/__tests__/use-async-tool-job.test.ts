import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

// ── Mocks ───────────────────────────────────────────────────────────────────

// Mock @clerk/nextjs
vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("mock-token"),
    isLoaded: true,
    isSignedIn: true,
  }),
}));

// Mock the invalidation map
vi.mock("../../lib/job-invalidation-map", () => ({
  JOB_INVALIDATION_MAP: {
    brand: [["brand-settings"], ["brand-sections"]],
    offer: [["offer"]],
    asset: [["assets"]],
    persona: [["personas"]],
  },
}));

// Mock the tab notification hook
vi.mock("../use-tab-notification-permission", () => ({
  useTabNotificationPermission: () => ({
    requestIfNeeded: vi.fn().mockResolvedValue(undefined),
    isGranted: vi.fn().mockReturnValue(false),
  }),
}));

// Mock sonner
const mockToastSuccess = vi.fn();
vi.mock("sonner", () => ({
  toast: { success: (msg: string, opts?: unknown) => mockToastSuccess(msg, opts) },
}));

// Mock pollJobStatus — will be overridden in each test
const mockPollJobStatus = vi.fn();
vi.mock("@/lib/api/ai-actions", () => ({
  pollJobStatus: (endpoint: string, token: string) => mockPollJobStatus(endpoint, token),
  // keep the deprecated alias
  pollExtractionStatus: (jobId: string, token: string) =>
    mockPollJobStatus(`/api/v1/brand/tools/extract-full-brand/status/${jobId}`, token),
}));

// Mock React Query
const mockInvalidateQueries = vi.fn();
const mockRefetchQueries = vi.fn();
vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({
    invalidateQueries: mockInvalidateQueries,
    refetchQueries: mockRefetchQueries,
  }),
}));

// Mock the store — track calls to store actions
const mockRegisterJob = vi.fn();
const mockUpdateJob = vi.fn();
const mockCompleteJob = vi.fn();
const mockClearJob = vi.fn();

let storeState: Record<string, unknown> = {};

vi.mock("../../store/copilot-store", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../store/copilot-store")>();
  const useCopilotStore = ((selector?: (s: unknown) => unknown) => {
    if (typeof selector === "function") return selector(storeState);
    return storeState;
  }) as unknown as {
    (selector?: (s: unknown) => unknown): unknown;
    getState: () => typeof storeState;
  };
  useCopilotStore.getState = () => storeState;
  return {
    ...actual,
    useCopilotStore,
  };
});

// ── Helpers ─────────────────────────────────────────────────────────────────

function makeJobState(
  overrides: Partial<{
    jobId: string;
    module: string;
    status: string;
    progress: number;
    filledFields: string[];
    pollEndpoint: string;
    conversationId: string | null;
  }> = {},
) {
  return {
    jobId: "job-abc",
    module: "brand" as const,
    scope: "full" as const,
    mode: "initial" as const,
    section: null,
    targetLabel: "Brand Studio",
    sourceKind: "url" as const,
    sourceRef: "https://example.com",
    status: "queued" as const,
    progress: 0,
    stage: "",
    filledFields: [],
    filledFieldsBySection: {},
    sectionsTouched: [],
    sectionsCompleted: [],
    startedAt: Date.now(),
    pollEndpoint: "/api/v1/brand/tools/extract-full-brand/status/job-abc",
    conversationId: "conv-1",
    ...overrides,
  };
}

// ── Tests ────────────────────────────────────────────────────────────────────

describe("useAsyncToolJob", () => {
  beforeEach(() => {
    vi.useFakeTimers();
    mockPollJobStatus.mockReset();
    mockInvalidateQueries.mockReset();
    mockRefetchQueries.mockReset();
    mockToastSuccess.mockReset();
    mockRegisterJob.mockReset();
    mockUpdateJob.mockReset();
    mockCompleteJob.mockReset();
    mockClearJob.mockReset();

    storeState = {
      activeJobs: {},
      registerJob: mockRegisterJob,
      updateJob: mockUpdateJob,
      completeJob: mockCompleteJob,
      clearJob: mockClearJob,
    };

    // Default Notification mock
    Object.defineProperty(global, "Notification", {
      value: class {
        static permission = "default";
        static requestPermission = vi.fn().mockResolvedValue("default");
        constructor() {}
      },
      writable: true,
      configurable: true,
    });

    // Default document.hidden = false
    Object.defineProperty(document, "hidden", { value: false, writable: true, configurable: true });
  });

  afterEach(() => {
    vi.useRealTimers();
    vi.restoreAllMocks();
  });

  it("polls every 2 seconds while running", async () => {
    const job = makeJobState({ status: "running", progress: 10 });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    mockPollJobStatus.mockResolvedValue({
      status: "running",
      progress: 20,
      stage: "Analizando...",
      filled_fields: [],
      filled_fields_by_section: {},
      sections_touched: [],
      sections_completed: [],
      newly_completed_section: null,
      error: null,
    });

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    renderHook(() => useAsyncToolJob("job-abc"));

    // Advance 2 seconds — first poll fires
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(mockPollJobStatus).toHaveBeenCalledTimes(1);

    // Advance another 2 seconds — second poll
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(mockPollJobStatus).toHaveBeenCalledTimes(2);
  });

  it("backs off to 5s after 60s elapsed", async () => {
    const job = makeJobState({ status: "running", progress: 50 });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    mockPollJobStatus.mockResolvedValue({
      status: "running",
      progress: 50,
      stage: "Sigue...",
      filled_fields: [],
      filled_fields_by_section: {},
      sections_touched: [],
      sections_completed: [],
      newly_completed_section: null,
      error: null,
    });

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    renderHook(() => useAsyncToolJob("job-abc"));

    // Advance 60 seconds (30 polls @ 2s)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(60000);
    });
    const countBefore = mockPollJobStatus.mock.calls.length;

    // Advance 2 more seconds — should NOT fire (backoff is 5s)
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    expect(mockPollJobStatus.mock.calls.length).toBe(countBefore);

    // Advance 3 more seconds — now 5s has passed since last poll → fires
    await act(async () => {
      await vi.advanceTimersByTimeAsync(3000);
    });
    expect(mockPollJobStatus.mock.calls.length).toBeGreaterThan(countBefore);
  });

  it("calls invalidateQueries with brand keys on completion for module=brand", async () => {
    const job = makeJobState({ status: "running", progress: 80 });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    mockPollJobStatus.mockResolvedValueOnce({
      status: "completed",
      progress: 100,
      stage: "Listo",
      filled_fields: ["brand_name"],
      filled_fields_by_section: { identity: ["brand_name"] },
      sections_touched: ["identity"],
      sections_completed: ["identity"],
      newly_completed_section: "identity",
      finished_at: new Date().toISOString(),
      error: null,
    });

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    renderHook(() => useAsyncToolJob("job-abc"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ["brand-settings"] });
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ["brand-sections"] });
  });

  it("dispatches copilot:field-update for each newly arrived field", async () => {
    const job = makeJobState({ status: "running", filledFields: [] });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    const dispatchedEvents: string[] = [];
    window.addEventListener("copilot:field-update", (e) => {
      const { detail } = e as CustomEvent<{ fieldId: string }>;
      dispatchedEvents.push(detail.fieldId);
    });

    mockPollJobStatus.mockResolvedValueOnce({
      status: "running",
      progress: 50,
      stage: "Analizando...",
      filled_fields: ["brand_name", "tagline"],
      filled_fields_by_section: { identity: ["brand_name", "tagline"] },
      sections_touched: ["identity"],
      sections_completed: [],
      newly_completed_section: null,
      error: null,
    });

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    renderHook(() => useAsyncToolJob("job-abc"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(dispatchedEvents).toContain("brand_name");
    expect(dispatchedEvents).toContain("tagline");
  });

  it("fires toast on terminal status + document.hidden", async () => {
    // Set document.hidden = true
    Object.defineProperty(document, "hidden", { value: true, writable: true, configurable: true });

    const job = makeJobState({ status: "running", progress: 90 });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    mockPollJobStatus.mockResolvedValueOnce({
      status: "completed",
      progress: 100,
      stage: "Listo",
      filled_fields: [],
      filled_fields_by_section: {},
      sections_touched: [],
      sections_completed: [],
      newly_completed_section: null,
      finished_at: new Date().toISOString(),
      error: null,
    });

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    renderHook(() => useAsyncToolJob("job-abc"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    expect(mockToastSuccess).toHaveBeenCalledWith(
      expect.stringContaining("Extracción"),
      expect.objectContaining({ duration: Infinity }),
    );
  });

  it("stops polling after unmount", async () => {
    const job = makeJobState({ status: "running" });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    mockPollJobStatus.mockResolvedValue({
      status: "running",
      progress: 30,
      stage: "...",
      filled_fields: [],
      filled_fields_by_section: {},
      sections_touched: [],
      sections_completed: [],
      newly_completed_section: null,
      error: null,
    });

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    const { unmount } = renderHook(() => useAsyncToolJob("job-abc"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });
    const countAtUnmount = mockPollJobStatus.mock.calls.length;
    unmount();

    await act(async () => {
      await vi.advanceTimersByTimeAsync(10000);
    });

    // No more calls after unmount
    expect(mockPollJobStatus.mock.calls.length).toBe(countAtUnmount);
  });

  it("does not poll on terminal initial status", async () => {
    const job = makeJobState({ status: "completed" });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    renderHook(() => useAsyncToolJob("job-abc"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(10000);
    });

    expect(mockPollJobStatus).not.toHaveBeenCalled();
  });

  // ── Per-wave module cache invalidation ───────────────────────────────────

  it("invalidates module queries per-wave when new section completes", async () => {
    const job = makeJobState({
      status: "running",
      progress: 30,
      conversationId: "conv-1",
    });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    mockPollJobStatus.mockResolvedValueOnce({
      status: "running",
      progress: 60,
      stage: "Analizando identidad...",
      filled_fields: ["brand_name"],
      filled_fields_by_section: { identity: ["brand_name"] },
      sections_touched: ["identity"],
      sections_completed: ["identity"], // ← new section completed mid-poll
      newly_completed_section: "identity",
      error: null,
    });

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    renderHook(() => useAsyncToolJob("job-abc"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    // Should invalidate the conversation detail (existing behavior)
    expect(mockInvalidateQueries).toHaveBeenCalledWith(
      expect.objectContaining({
        queryKey: ["copilot", "conversation", "conv-1"],
      }),
    );

    // ALSO invalidate module queries per-wave so the studio form refreshes
    // (brand-settings, brand-sections) without waiting for job terminal.
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ["brand-settings"] });
    expect(mockInvalidateQueries).toHaveBeenCalledWith({ queryKey: ["brand-sections"] });
  });

  it("does NOT invalidate module queries when no new section completes", async () => {
    const job = makeJobState({
      status: "running",
      progress: 30,
      conversationId: "conv-1",
    });
    storeState = { ...storeState, activeJobs: { "job-abc": job } };

    mockPollJobStatus.mockResolvedValueOnce({
      status: "running",
      progress: 40,
      stage: "Analizando...",
      filled_fields: ["brand_name"],
      filled_fields_by_section: { identity: ["brand_name"] },
      sections_touched: ["identity"],
      sections_completed: [], // ← no section completed yet
      newly_completed_section: null,
      error: null,
    });

    const { useAsyncToolJob } = await import("../use-async-tool-job");
    renderHook(() => useAsyncToolJob("job-abc"));

    await act(async () => {
      await vi.advanceTimersByTimeAsync(2000);
    });

    // No new section → should NOT have called invalidateQueries with brand-settings
    const brandSettingsCalls = mockInvalidateQueries.mock.calls.filter(
      (call) => JSON.stringify(call[0]?.queryKey) === JSON.stringify(["brand-settings"]),
    );
    expect(brandSettingsCalls).toHaveLength(0);
  });
});
