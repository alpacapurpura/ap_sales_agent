import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// ── Mocks ───────────────────────────────────────────────────────────────────

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: vi.fn().mockResolvedValue("token") }),
}));

vi.mock("@tanstack/react-query", () => ({
  useQueryClient: () => ({ invalidateQueries: vi.fn() }),
}));

vi.mock("sonner", () => ({
  toast: { success: vi.fn() },
}));

vi.mock("@/lib/api/ai-actions", () => ({
  pollJobStatus: vi.fn().mockResolvedValue({ status: "running", progress: 50, stage: "", filled_fields: [], filled_fields_by_section: {}, sections_touched: [], sections_completed: [], newly_completed_section: null, error: null }),
  pollExtractionStatus: vi.fn(),
}));

vi.mock("../../lib/job-invalidation-map", () => ({
  JOB_INVALIDATION_MAP: {
    brand: [["brand-settings"], ["brand-sections"]],
    offer: [["offer"]],
    asset: [["assets"]],
    persona: [["personas"]],
  },
}));

vi.mock("../../../hooks/use-tab-notification-permission", () => ({
  useTabNotificationPermission: () => ({
    requestIfNeeded: vi.fn(),
    isGranted: vi.fn().mockReturnValue(false),
  }),
}));

// Provide the store with job data for rendering chip
const mockStoreActiveJobs: Record<string, unknown> = {};

vi.mock("../../../store/copilot-store", async (importOriginal) => {
  const actual = await importOriginal<typeof import("../../../store/copilot-store")>();
  const buildState = () => ({
    activeJobs: mockStoreActiveJobs,
    registerJob: vi.fn(),
    updateJob: vi.fn(),
    completeJob: vi.fn(),
    clearJob: vi.fn(),
  });
  const useCopilotStore = ((selector?: (s: unknown) => unknown) => {
    const state = buildState();
    if (typeof selector === "function") return selector(state);
    return state;
  }) as unknown as {
    (selector?: (s: unknown) => unknown): unknown;
    getState: () => ReturnType<typeof buildState>;
  };
  useCopilotStore.getState = buildState;
  return {
    ...actual,
    useCopilotStore,
  };
});

// ── Import after mocks ────────────────────────────────────────────────────────

import { ToolCallChip } from "../ToolCallChip";

describe("ToolCallChip", () => {
  beforeEach(() => {
    // clear job state
    for (const key of Object.keys(mockStoreActiveJobs)) {
      // eslint-disable-next-line @typescript-eslint/no-dynamic-delete
      delete mockStoreActiveJobs[key];
    }
  });

  describe("legacy layout (no jobId)", () => {
    it("renders tool label", () => {
      render(<ToolCallChip tool="extract_from_url" status="running" />);
      expect(screen.getByText("Analizando página web")).toBeInTheDocument();
    });

    it("shows spinner when running", () => {
      render(<ToolCallChip tool="extract_from_url" status="running" />);
      expect(screen.getByRole("status")).toBeInTheDocument();
    });

    it("shows check when done", () => {
      render(<ToolCallChip tool="extract_from_url" status="done" />);
      const chip = screen.getByRole("status");
      expect(chip).toBeInTheDocument();
      // aria-label indicates completed
      expect(chip.getAttribute("aria-label")).toContain("completada");
    });

    it("does not render progress bar without jobId", () => {
      const { container } = render(<ToolCallChip tool="extract_from_url" status="running" />);
      expect(container.querySelector("[data-testid='job-progress-bar']")).toBeNull();
    });
  });

  describe("extended layout (with jobId, running)", () => {
    beforeEach(() => {
      mockStoreActiveJobs["job-xyz"] = {
        jobId: "job-xyz",
        module: "brand",
        status: "running",
        progress: 42,
        stage: "Analizando sección 'Nosotros'",
        filledFields: ["brand_name", "tagline", "mission", "vision", "values", "tone_of_voice", "tagline2", "positioning", "uvp", "target_audience", "pain_points", "desires"],
        sectionsCompleted: ["identity", "strategy", "audience"],
        pollEndpoint: "/api/v1/brand/tools/extract-full-brand/status/job-xyz",
      };
    });

    it("renders progress bar when jobId and running", () => {
      const { container } = render(
        <ToolCallChip tool="extract_from_url" status="running" jobId="job-xyz" />,
      );
      expect(container.querySelector("[data-testid='job-progress-bar']")).not.toBeNull();
    });

    it("renders stage text", () => {
      render(<ToolCallChip tool="extract_from_url" status="running" jobId="job-xyz" />);
      expect(screen.getByText(/Analizando sección/i)).toBeInTheDocument();
    });

    it("renders field counter", () => {
      render(<ToolCallChip tool="extract_from_url" status="running" jobId="job-xyz" />);
      expect(screen.getByText(/12 campos/i)).toBeInTheDocument();
    });

    it("renders section counter", () => {
      render(<ToolCallChip tool="extract_from_url" status="running" jobId="job-xyz" />);
      expect(screen.getByText(/3 secciones/i)).toBeInTheDocument();
    });
  });

  describe("extended layout (with jobId, completed)", () => {
    beforeEach(() => {
      mockStoreActiveJobs["job-done"] = {
        jobId: "job-done",
        module: "brand",
        status: "completed",
        progress: 100,
        stage: "Listo",
        filledFields: Array.from({ length: 27 }, (_, i) => `field_${i}`),
        sectionsCompleted: ["identity", "strategy", "audience", "positioning", "audience2", "visuals"],
        pollEndpoint: "/api/v1/brand/tools/extract-full-brand/status/job-done",
      };
    });

    it("renders success tint (no progress bar)", () => {
      const { container } = render(
        <ToolCallChip tool="extract_from_url" status="done" jobId="job-done" />,
      );
      expect(container.querySelector("[data-testid='job-progress-bar']")).toBeNull();
    });

    it("renders final field/section counters", () => {
      render(<ToolCallChip tool="extract_from_url" status="done" jobId="job-done" />);
      expect(screen.getByText(/27 campos/i)).toBeInTheDocument();
      expect(screen.getByText(/6 secciones/i)).toBeInTheDocument();
    });
  });
});
