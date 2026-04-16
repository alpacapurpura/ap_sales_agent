import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const pushMock = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: pushMock }),
  useParams: () => ({ tenantId: "test-tenant" }),
}));

import { InterviewModeButton } from "../InterviewModeButton";

describe("InterviewModeButton", () => {
  beforeEach(() => {
    pushMock.mockClear();
  });

  it("renders with default label", () => {
    render(<InterviewModeButton domain="brand" />);
    expect(screen.getByRole("button", { name: /modo entrevista/i })).toBeInTheDocument();
  });

  it("renders with custom label", () => {
    render(<InterviewModeButton domain="brand" label="Iniciar entrevista" />);
    expect(screen.getByRole("button", { name: /iniciar entrevista/i })).toBeInTheDocument();
  });

  it("navigates to brand interview route on click", () => {
    render(<InterviewModeButton domain="brand" />);
    fireEvent.click(screen.getByRole("button"));
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/brand-studio/interview");
  });

  it("navigates to buyer_persona interview route with personaId", () => {
    render(<InterviewModeButton domain="buyer_persona" entityId="persona-123" />);
    fireEvent.click(screen.getByRole("button"));
    expect(pushMock).toHaveBeenCalledWith(
      "/test-tenant/brand-studio/interview/buyer-persona?personaId=persona-123",
    );
  });

  it("navigates to buyer_persona interview route without entityId", () => {
    render(<InterviewModeButton domain="buyer_persona" />);
    fireEvent.click(screen.getByRole("button"));
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/brand-studio/interview/buyer-persona");
  });

  it("navigates to offer interview route with offerId", () => {
    render(<InterviewModeButton domain="offer" entityId="offer-456" />);
    fireEvent.click(screen.getByRole("button"));
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/offer-studio/interview?offerId=offer-456");
  });

  it("navigates to offer interview route without entityId", () => {
    render(<InterviewModeButton domain="offer" />);
    fireEvent.click(screen.getByRole("button"));
    expect(pushMock).toHaveBeenCalledWith("/test-tenant/offer-studio/interview");
  });

  it("renders the sparkles icon", () => {
    render(<InterviewModeButton domain="brand" />);
    const button = screen.getByRole("button");
    // The button should contain an SVG icon (Sparkles from lucide-react)
    const svg = button.querySelector("svg");
    expect(svg).toBeTruthy();
  });

  it("applies additional className", () => {
    render(<InterviewModeButton domain="brand" className="extra-class" />);
    const button = screen.getByRole("button");
    expect(button.className).toContain("extra-class");
  });
});
