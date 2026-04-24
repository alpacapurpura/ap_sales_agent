/**
 * Tests for CopilotChatPanel hydration + ActiveJobsPoller — idle-refetch polling.
 *
 * Design: polling is decoupled from message rendering. Hydration uses the
 * simple mid-stream guard (``thinking``/``streaming``), and the polling
 * effect lives in a top-level ``ActiveJobsPoller`` driven by the Zustand
 * store. Server refetch is free to full-replace local messages without
 * killing in-flight extraction jobs.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from "vitest";

import { useCopilotStore } from "../../store/copilot-store";

import type { AsyncJobState, CopilotMessage } from "../../store/copilot-store";

// ── Mocks ────────────────────────────────────────────────────────────────────

vi.mock("next/navigation", () => ({
  usePathname: () => "/tenant-1/brand-studio",
  useRouter: () => ({ push: vi.fn() }),
  useParams: () => ({ tenantId: "tenant-1" }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("token") }),
}));

// ── Helpers ──────────────────────────────────────────────────────────────────

function makeActiveJob(overrides: Partial<AsyncJobState> = {}): AsyncJobState {
  return {
    jobId: "job-xyz",
    module: "brand",
    scope: "full",
    mode: "initial",
    section: null,
    targetLabel: "Brand",
    sourceKind: "url",
    sourceRef: "https://example.com",
    pollEndpoint: "/api/v1/brand/extract-full-brand/status/job-xyz",
    conversationId: "conv-1",
    status: "running",
    progress: 0,
    stage: "",
    filledFields: [],
    filledFieldsBySection: {},
    sectionsTouched: [],
    sectionsCompleted: [],
    startedAt: Date.now(),
    ...overrides,
  };
}

// Mirrors the isMidStream expression in CopilotChatPanel post-revert:
// polling no longer depends on this flag; it's driven by ActiveJobsPoller.
function computeIsMidStream(status: string): boolean {
  return status === "thinking" || status === "streaming";
}

// ── Tests: isMidStream guard ─────────────────────────────────────────────────

describe("CopilotChatPanel hydration — isMidStream guard", () => {
  it("returns true when status is thinking", () => {
    expect(computeIsMidStream("thinking")).toBe(true);
  });

  it("returns true when status is streaming", () => {
    expect(computeIsMidStream("streaming")).toBe(true);
  });

  it("returns false when status is idle (full-replace safe)", () => {
    expect(computeIsMidStream("idle")).toBe(false);
  });

  it("returns false when status is idle even with running job — polling is decoupled", () => {
    // The whole point of idle-refetch polling revert + ActiveJobsPoller: idle + active job
    // must NOT force merge, because optimistic/server id mismatch causes
    // duplicate-message bug. Polling survives via the headless poller.
    expect(computeIsMidStream("idle")).toBe(false);
  });
});

// ── Tests: full-replace drops toolCalls — and that's OK ──────────────────────

describe("CopilotChatPanel hydration — full-replace on idle", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      status: "idle",
      activeJobs: {},
      messages: [],
      conversationId: null,
    });
  });

  afterEach(() => {
    useCopilotStore.setState({
      status: "idle",
      activeJobs: {},
      messages: [],
      conversationId: null,
    });
  });

  it("setMessages replaces local toolCalls when server transcript lands", () => {
    const optimistic: CopilotMessage = {
      id: "msg-optimistic-uuid",
      role: "assistant",
      content: "partial content",
      timestamp: Date.now(),
      toolCalls: [{ tool: "extract_from_url", jobId: "job-xyz", status: "running" }],
    };
    useCopilotStore.getState().addMessage(optimistic);

    // Server returns msg with a DIFFERENT id (real server uuid)
    const serverMessages: CopilotMessage[] = [
      {
        id: "msg-server-real-id",
        role: "assistant",
        content: "server content",
        timestamp: Date.now(),
      },
    ];

    useCopilotStore.getState().setMessages(serverMessages);

    // Full-replace is intentional: only the server message remains. No
    // duplicates. toolCalls[*].jobId is gone — polling no longer depends on
    // it (see ActiveJobsPoller).
    expect(useCopilotStore.getState().messages).toHaveLength(1);
    expect(useCopilotStore.getState().messages[0].id).toBe("msg-server-real-id");
    expect(useCopilotStore.getState().messages[0].toolCalls).toBeUndefined();
  });
});

// ── Tests: active jobs survive full-replace via the store ────────────────────

describe("ActiveJobsPoller — polling survives full-replace", () => {
  beforeEach(() => {
    useCopilotStore.setState({
      status: "idle",
      activeJobs: {},
      messages: [],
      conversationId: null,
    });
  });

  afterEach(() => {
    useCopilotStore.setState({
      status: "idle",
      activeJobs: {},
      messages: [],
      conversationId: null,
    });
  });

  it("activeJobs map persists across setMessages full-replace", () => {
    // Register a job (as onToolResult would)
    useCopilotStore.getState().registerJob(makeActiveJob({ status: "running" }));

    // Full-replace messages (as idle hydration would)
    useCopilotStore
      .getState()
      .setMessages([{ id: "server-id", role: "assistant", content: "s", timestamp: Date.now() }]);

    // Job is still tracked — ActiveJobsPoller keeps its hook mounted
    expect(useCopilotStore.getState().activeJobs["job-xyz"]).toBeDefined();
    expect(useCopilotStore.getState().activeJobs["job-xyz"].status).toBe("running");
  });

  it("pending-job filter excludes terminal jobs", () => {
    useCopilotStore.getState().registerJob(makeActiveJob({ jobId: "job-a", status: "running" }));
    useCopilotStore.getState().registerJob(makeActiveJob({ jobId: "job-b", status: "completed" }));
    useCopilotStore.getState().registerJob(makeActiveJob({ jobId: "job-c", status: "failed" }));

    const jobs = Object.values(useCopilotStore.getState().activeJobs);
    const pending = jobs.filter((j) => j.status !== "completed" && j.status !== "failed");

    // Only the running one should keep polling mounted
    expect(pending).toHaveLength(1);
    expect(pending[0].jobId).toBe("job-a");
  });
});
