import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("../config/interview-preview-registry", () => ({
  getPreviewEntry: (domain: string) => {
    if (domain === "offer") {
      return {
        summaryComponent: () =>
          Promise.resolve({
            default: ({ data }: { data: Record<string, unknown> }) => (
              <div data-testid="offer-preview-summary">
                {String(data?.public_name ?? "Sin nombre")}
              </div>
            ),
          }),
        sectionsComponent: () =>
          Promise.resolve({
            default: () => <div data-testid="offer-preview-sections">Sections</div>,
          }),
        emptyStateMessage: "Describe tu oferta...",
      };
    }
    return null;
  },
}));

import { CopilotPreviewPane } from "../components/CopilotPreviewPane";
import { useCopilotStore } from "../store/copilot-store";

describe("CopilotPreviewPane", () => {
  beforeEach(() => {
    useCopilotStore.setState({ previewData: null, focusEntity: null, focusSnapshot: null });
  });

  it("shows empty state when no preview data", async () => {
    useCopilotStore.setState({
      focusEntity: { domain: "offer", entityId: "123", label: "Test" },
    });
    render(<CopilotPreviewPane />);
    await waitFor(() => {
      expect(screen.getByText("Describe tu oferta...")).toBeDefined();
    });
  });

  it("renders preview summary with data", async () => {
    useCopilotStore.setState({
      focusEntity: { domain: "offer", entityId: "123", label: "Test" },
      previewData: { public_name: "Oferta Premium" },
    });
    render(<CopilotPreviewPane />);
    await waitFor(() => {
      expect(screen.getByText("Oferta Premium")).toBeDefined();
    });
  });

  it("renders nothing when no focusEntity", () => {
    const { container } = render(<CopilotPreviewPane />);
    expect(container.innerHTML).toBe("");
  });
});
