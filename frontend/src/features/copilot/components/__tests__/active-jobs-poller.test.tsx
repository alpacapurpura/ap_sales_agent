/**
 * @vitest-environment happy-dom
 */
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { useCopilotStore, type AsyncJobState } from "../../store/copilot-store";
import { ActiveJobsPoller } from "../ActiveJobsPoller";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: async () => "test-token" }),
}));

vi.mock("../../hooks/use-tab-notification-permission", () => ({
  useTabNotificationPermission: () => ({
    requestIfNeeded: vi.fn(),
    isGranted: () => false,
  }),
}));

vi.mock("@/lib/api/ai-actions", () => ({
  pollJobStatus: vi.fn(async () => ({ status: "running", progress: 0 })),
}));

const jobFixture = (overrides: Partial<AsyncJobState> = {}): AsyncJobState => ({
  jobId: "job-1",
  module: "brand",
  scope: "full",
  mode: "initial",
  section: null,
  targetLabel: "Brand",
  sourceKind: "url",
  sourceRef: "https://example.com",
  pollEndpoint: "/api/v1/brand/extraction-jobs/job-1",
  conversationId: "conv-1",
  status: "running",
  progress: 50,
  stage: "extracting",
  filledFields: [],
  filledFieldsBySection: {},
  sectionsTouched: [],
  sectionsCompleted: [],
  startedAt: Date.now(),
  ...overrides,
});

const wrap = (ui: React.ReactNode): React.ReactElement => {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return <QueryClientProvider client={qc}>{ui}</QueryClientProvider>;
};

describe("ActiveJobsPoller", () => {
  beforeEach(() => {
    useCopilotStore.setState({ activeJobs: {} });
  });

  afterEach(() => {
    cleanup();
    useCopilotStore.setState({ activeJobs: {} });
  });

  it("renders nothing when no jobs are active", () => {
    const { container } = render(wrap(<ActiveJobsPoller />));
    expect(container.firstChild).toBeNull();
  });

  it("renders a visible chip for each pending job", () => {
    useCopilotStore.setState({ activeJobs: { "job-1": jobFixture() } });
    render(wrap(<ActiveJobsPoller />));
    expect(screen.getByTestId("active-jobs-banner")).toBeTruthy();
  });

  it("hides when all jobs are terminal", () => {
    useCopilotStore.setState({
      activeJobs: { "job-1": jobFixture({ status: "completed" }) },
    });
    const { container } = render(wrap(<ActiveJobsPoller />));
    expect(container.firstChild).toBeNull();
  });
});
