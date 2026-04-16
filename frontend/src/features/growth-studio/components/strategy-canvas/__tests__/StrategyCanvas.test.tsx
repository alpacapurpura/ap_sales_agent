import { render, screen, waitFor } from "@testing-library/react";
import { describe, it, expect, vi } from "vitest";

import { MOCK_CONFIG } from "../config/mock-data";
import { StrategyCanvas } from "../StrategyCanvas";

// Mock ParentSize to provide valid dimensions immediately
vi.mock("@visx/responsive", async () => {
  const actual = await vi.importActual("@visx/responsive");
  return {
    ...actual,
    ParentSize: ({
      children,
    }: {
      children: (args: { width: number; height: number }) => React.ReactNode;
    }) => <div>{children({ width: 1200, height: 800 })}</div>,
  };
});

describe("StrategyCanvas", () => {
  it("renders complex mock data without crashing", async () => {
    render(<StrategyCanvas config={MOCK_CONFIG} />);

    await waitFor(() => {
      expect(screen.queryByText(/Error:/i)).not.toBeInTheDocument();
      // Check for first and last nodes
      expect(screen.getByText("Universo")).toBeInTheDocument();
      expect(screen.getByText("Evangelización")).toBeInTheDocument();
    });
  });

  it("renders node labels correctly", async () => {
    render(<StrategyCanvas config={MOCK_CONFIG} />);
    expect(await screen.findByText("Universo")).toBeInTheDocument();
    expect(await screen.findByText("Conversión")).toBeInTheDocument();
  });

  it("renders links", async () => {
    const { container } = render(<StrategyCanvas config={MOCK_CONFIG} />);
    await waitFor(() => {
      // Check for path elements. Visx renders links as paths.
      const paths = container.querySelectorAll("path");
      expect(paths.length).toBeGreaterThan(0);
    });
  });
});
