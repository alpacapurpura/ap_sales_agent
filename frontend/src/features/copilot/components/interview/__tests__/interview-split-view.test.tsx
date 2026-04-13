import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, act } from "@testing-library/react";

// ── Mocks (must be before imports) ──────────────────────────────────────────

vi.mock("next/navigation", () => ({
  useRouter: () => ({
    replace: vi.fn(),
    push: vi.fn(),
  }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({
    getToken: vi.fn().mockResolvedValue("test-token"),
  }),
}));

vi.mock("@tanstack/react-query", () => ({
  useQuery: vi.fn().mockReturnValue({
    data: null,
    isLoading: false,
  }),
  useQueryClient: () => ({
    invalidateQueries: vi.fn(),
  }),
}));

vi.mock("@/features/copilot/store/copilot-store", () => ({
  useCopilotStore: vi.fn().mockReturnValue({
    interviewPreviewData: null,
    setInterviewMode: vi.fn(),
    updateInterviewPreview: vi.fn(),
  }),
}));

vi.mock("@/features/copilot/hooks/useInterviewChat", () => ({
  useInterviewChat: vi.fn().mockReturnValue({
    messages: [],
    status: "idle",
    sendMessage: vi.fn(),
    sendCardAction: vi.fn(),
    addInitialMessage: vi.fn(),
  }),
}));

vi.mock("@/features/copilot/components/interview/interview-chat-panel", () => ({
  InterviewChatPanel: () => <div data-testid="chat-panel">Chat</div>,
}));

vi.mock("@/features/copilot/api/interview-api", () => ({
  getActiveInterview: vi.fn().mockResolvedValue(null),
  getInterviewState: vi.fn().mockResolvedValue({
    session_id: "test-session",
    mapa_global: {},
    bloque_actual: "identidad",
    bloques_completados: [],
    config: { total_bloques: 5 },
    messages_count: 0,
  }),
  startInterview: vi.fn().mockResolvedValue({
    session_id: "new-session",
    conversation_id: "new-conv",
    config: {},
    initial_message: "Hola",
  }),
  abandonInterview: vi.fn().mockResolvedValue(undefined),
}));

// Mock the preview registry to return test components
vi.mock("@/features/copilot/config/interview-preview-registry", () => ({
  getPreview: vi.fn().mockReturnValue({
    summaryComponent: () => (
      <div data-testid="preview-summary">Summary</div>
    ),
    sectionsComponent: ({
      currentBlock,
    }: {
      currentBlock: string;
      data: Record<string, unknown>;
      blocksCompleted: string[];
    }) => (
      <div data-testid="preview-sections">
        Sections: block={currentBlock}
      </div>
    ),
    emptyStateMessage: "No hay datos",
  }),
}));

vi.mock("@/features/copilot/components/interview/interview-header", () => ({
  InterviewHeader: ({
    currentBlockLabel,
  }: {
    currentBlockLabel: string;
    blocksCompleted: number;
    totalBlocks: number;
  }) => (
    <div data-testid="interview-header">Header: {currentBlockLabel}</div>
  ),
}));

vi.mock(
  "@/features/copilot/components/interview/session-restore-modal",
  () => ({
    SessionRestoreModal: () => null,
  }),
);

// ── Import after mocks ─────────────────────────────────────────────────────

import { InterviewSplitView } from "../interview-split-view";
import { getPreview } from "@/features/copilot/config/interview-preview-registry";

// ── Tests ───────────────────────────────────────────────────────────────────

describe("InterviewSplitView (generic)", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders chat panel when sessionId is provided", async () => {
    await act(async () => {
      render(<InterviewSplitView domain="brand" sessionId="test-session" />);
    });
    expect(screen.getByTestId("chat-panel")).toBeInTheDocument();
  });

  it("renders preview components from registry", async () => {
    await act(async () => {
      render(<InterviewSplitView domain="brand" sessionId="test-session" />);
    });

    expect(screen.getByTestId("preview-summary")).toBeInTheDocument();
    expect(screen.getByTestId("preview-sections")).toBeInTheDocument();
  });

  it("renders interview header", async () => {
    await act(async () => {
      render(<InterviewSplitView domain="brand" sessionId="test-session" />);
    });
    expect(screen.getByTestId("interview-header")).toBeInTheDocument();
  });

  it("calls getPreview with the domain prop", async () => {
    await act(async () => {
      render(
        <InterviewSplitView domain="buyer_persona" sessionId="test-session" />,
      );
    });
    expect(getPreview).toHaveBeenCalledWith("buyer_persona");
  });

  it("renders correctly with entityId prop", async () => {
    await act(async () => {
      render(
        <InterviewSplitView
          domain="offer"
          sessionId="test-session"
          entityId="offer-123"
        />,
      );
    });
    expect(screen.getByTestId("chat-panel")).toBeInTheDocument();
    expect(screen.getByTestId("preview-summary")).toBeInTheDocument();
  });
});
