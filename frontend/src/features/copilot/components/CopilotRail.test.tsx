import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, fireEvent } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("token"), isLoaded: true, isSignedIn: true }),
}));

vi.mock("next/navigation", () => ({
  usePathname: () => "/t1/brand-studio",
  useParams: () => ({ tenantId: "t1" }),
}));

vi.mock("../hooks/use-conversation-list", () => ({
  useConversationList: () => ({ data: undefined }),
}));

vi.mock("../hooks/use-create-conversation", () => ({
  useCreateConversation: () => ({ mutate: vi.fn() }),
}));

function wrap(ui: ReactElement) {
  const qc = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  return render(<QueryClientProvider client={qc}>{ui}</QueryClientProvider>);
}

import { useCopilotStore } from "../store/copilot-store";

import { CopilotRail } from "./CopilotRail";

import type { ReactElement } from "react";

describe("CopilotRail", () => {
  beforeEach(() => {
    useCopilotStore.setState({ sidebarState: "collapsed", isOpen: false });
  });

  it("shows 'Abrir chat' button when collapsed", () => {
    wrap(<CopilotRail />);
    expect(screen.getByRole("button", { name: /abrir chat/i })).toBeDefined();
  });

  it("clicking 'Abrir chat' transitions to rail state", () => {
    wrap(<CopilotRail />);
    fireEvent.click(screen.getByRole("button", { name: /abrir chat/i }));
    expect(useCopilotStore.getState().sidebarState).toBe("rail");
  });

  it("shows 'Ver historial' and 'Cerrar chat' buttons when in rail state", () => {
    useCopilotStore.setState({ sidebarState: "rail", isOpen: true });
    wrap(<CopilotRail />);
    expect(screen.getByRole("button", { name: /ver historial/i })).toBeDefined();
    expect(screen.getByRole("button", { name: /cerrar chat/i })).toBeDefined();
  });

  it("clicking 'Ver historial' transitions to full state", () => {
    useCopilotStore.setState({ sidebarState: "rail", isOpen: true });
    wrap(<CopilotRail />);
    fireEvent.click(screen.getByRole("button", { name: /ver historial/i }));
    expect(useCopilotStore.getState().sidebarState).toBe("full");
  });

  it("clicking 'Cerrar chat' transitions to collapsed state", () => {
    useCopilotStore.setState({ sidebarState: "rail", isOpen: true });
    wrap(<CopilotRail />);
    fireEvent.click(screen.getByRole("button", { name: /cerrar chat/i }));
    expect(useCopilotStore.getState().sidebarState).toBe("collapsed");
  });

  it("shows conversation avatars only in collapsed state", () => {
    useCopilotStore.setState({ sidebarState: "rail", isOpen: true });
    wrap(<CopilotRail />);
    // Avatars section not rendered in rail — no "más" link
    expect(screen.queryByText("más")).toBeNull();
  });
});
