import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen, fireEvent } from "@testing-library/react";

vi.mock("@/features/copilot/store/copilot-store", () => ({
  useCopilotStore: vi.fn(() => ({
    openPanel: mockOpenPanel,
    addSelectedField: mockAddSelectedField,
  })),
}));

const mockOpenPanel = vi.fn();
const mockAddSelectedField = vi.fn();

import { SectionChatTrigger } from "../section-chat-trigger";

describe("SectionChatTrigger", () => {
  beforeEach(() => {
    mockOpenPanel.mockClear();
    mockAddSelectedField.mockClear();
  });

  it("renders an icon button with accessible label", () => {
    render(
      <SectionChatTrigger sectionId="identity" sectionLabel="Identidad" />
    );
    expect(
      screen.getByRole("button", { name: /consultar.*identidad/i })
    ).toBeInTheDocument();
  });

  it("renders the message circle icon", () => {
    render(
      <SectionChatTrigger sectionId="identity" sectionLabel="Identidad" />
    );
    const button = screen.getByRole("button");
    const svg = button.querySelector("svg");
    expect(svg).toBeTruthy();
  });

  it("opens copilot panel and sets context on click", () => {
    render(
      <SectionChatTrigger sectionId="tone" sectionLabel="Tono y Voz" />
    );
    fireEvent.click(screen.getByRole("button"));
    expect(mockOpenPanel).toHaveBeenCalled();
    expect(mockAddSelectedField).toHaveBeenCalledWith({
      fieldId: "tone",
      fieldLabel: "Tono y Voz",
      fieldValue: "",
    });
  });

  it("applies additional className", () => {
    render(
      <SectionChatTrigger
        sectionId="identity"
        sectionLabel="Identidad"
        className="my-class"
      />
    );
    const button = screen.getByRole("button");
    expect(button.className).toContain("my-class");
  });
});
