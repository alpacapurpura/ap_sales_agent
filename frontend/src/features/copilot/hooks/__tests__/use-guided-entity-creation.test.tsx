import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

const { mockSendMessage, mockOpenPanel, mockPush, mockReportEvent, mockGetToken } = vi.hoisted(
  () => ({
    mockSendMessage: vi.fn(),
    mockOpenPanel: vi.fn(),
    mockPush: vi.fn(),
    mockReportEvent: vi.fn(),
    mockGetToken: vi.fn().mockResolvedValue("tok-test"),
  }),
);

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: mockGetToken }),
}));

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: mockPush }),
}));

vi.mock("@/components/shared/navigation", () => ({
  useNavigation: () => ({
    runWithOverlay: async <T,>(fn: () => Promise<T>) => fn(),
  }),
}));

vi.mock("@/features/copilot/hooks/use-copilot-chat", () => ({
  useCopilotChat: () => ({
    sendMessage: mockSendMessage,
    sendCardAction: vi.fn(),
    stopStreaming: vi.fn(),
  }),
}));

vi.mock("@/features/copilot/store/copilot-store", () => {
  const state = { openPanel: mockOpenPanel };
  const useCopilotStore = (selector?: (s: typeof state) => unknown) =>
    selector ? selector(state) : state;
  useCopilotStore.getState = () => state;
  return { useCopilotStore };
});

vi.mock("@/features/copilot/api/copilot-api", () => ({
  reportCopilotEvent: (...args: unknown[]) => mockReportEvent(...args),
}));

import { useGuidedEntityCreation } from "../use-guided-entity-creation";

interface FakeEntity {
  id: string;
  name: string;
}

function makeEntity(overrides: Partial<FakeEntity> = {}): FakeEntity {
  return { id: "ent-1", name: "Nueva entidad", ...overrides };
}

describe("useGuidedEntityCreation", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockGetToken.mockResolvedValue("tok-test");
  });

  it("creates entity, opens copilot panel, sends guided prompt, then navigates", async () => {
    mockSendMessage.mockResolvedValue(undefined);
    const createEntity = vi.fn().mockResolvedValue(makeEntity({ id: "p-9" }));

    const { result } = renderHook(() =>
      useGuidedEntityCreation<FakeEntity>({
        domain: "buyer_persona",
        tenantId: "t-1",
        createEntity,
      }),
    );

    expect(result.current.creating).toBe(false);
    expect(result.current.error).toBeNull();

    await act(async () => {
      await result.current.create();
    });

    expect(createEntity).toHaveBeenCalledTimes(1);
    expect(mockOpenPanel).toHaveBeenCalledTimes(1);
    expect(mockSendMessage).toHaveBeenCalledTimes(1);
    // Prompt is natural-language so it doesn't read as machine instruction
    // to the user, but still embeds the entity_id so the LLM can extract it
    // when it calls start_guided_setup.
    expect(mockSendMessage).toHaveBeenCalledWith(expect.stringContaining("Guíame paso a paso"));
    expect(mockSendMessage).toHaveBeenCalledWith(expect.stringContaining("p-9"));
    expect(mockPush).toHaveBeenCalledWith("/t-1/brand-studio/publico/persona/p-9");
  });

  it("uses custom getNavigateUrl when provided", async () => {
    mockSendMessage.mockResolvedValue(undefined);
    const createEntity = vi.fn().mockResolvedValue(makeEntity({ id: "of-3" }));
    const getNavigateUrl = vi.fn((e: FakeEntity) => `/custom/${e.id}`);

    const { result } = renderHook(() =>
      useGuidedEntityCreation<FakeEntity>({
        domain: "offer",
        tenantId: "t-1",
        createEntity,
        getNavigateUrl,
      }),
    );

    await act(async () => {
      await result.current.create();
    });

    expect(getNavigateUrl).toHaveBeenCalledWith(expect.objectContaining({ id: "of-3" }));
    expect(mockPush).toHaveBeenCalledWith("/custom/of-3");
  });

  it("still navigates if sendMessage throws (best-effort guided trigger)", async () => {
    mockSendMessage.mockRejectedValue(new Error("chat down"));
    const createEntity = vi.fn().mockResolvedValue(makeEntity({ id: "p-x" }));

    const { result } = renderHook(() =>
      useGuidedEntityCreation<FakeEntity>({
        domain: "buyer_persona",
        tenantId: "t-1",
        createEntity,
      }),
    );

    await act(async () => {
      await result.current.create();
    });

    expect(mockPush).toHaveBeenCalledWith("/t-1/brand-studio/publico/persona/p-x");
    expect(result.current.error).toBeNull();
  });

  it("does NOT open panel or navigate if createEntity throws; surfaces error", async () => {
    const createEntity = vi.fn().mockRejectedValue(new Error("backend 500"));

    const { result } = renderHook(() =>
      useGuidedEntityCreation<FakeEntity>({
        domain: "buyer_persona",
        tenantId: "t-1",
        createEntity,
      }),
    );

    await act(async () => {
      await result.current.create();
    });

    expect(mockOpenPanel).not.toHaveBeenCalled();
    expect(mockSendMessage).not.toHaveBeenCalled();
    expect(mockPush).not.toHaveBeenCalled();
    expect(result.current.error).toBe("backend 500");
    expect(result.current.creating).toBe(false);
  });

  it("ignores concurrent create() calls while one is in flight", async () => {
    let resolveCreate: (v: FakeEntity) => void = () => undefined;
    const createEntity = vi.fn(
      () =>
        new Promise<FakeEntity>((resolve) => {
          resolveCreate = resolve;
        }),
    );
    mockSendMessage.mockResolvedValue(undefined);

    const { result } = renderHook(() =>
      useGuidedEntityCreation<FakeEntity>({
        domain: "buyer_persona",
        tenantId: "t-1",
        createEntity,
      }),
    );

    let firstCall: Promise<void> = Promise.resolve();
    act(() => {
      firstCall = result.current.create();
    });

    // Second call while first still pending — should no-op.
    await act(async () => {
      await result.current.create();
    });

    expect(createEntity).toHaveBeenCalledTimes(1);

    await act(async () => {
      resolveCreate(makeEntity({ id: "ent-1" }));
      await firstCall;
    });

    expect(createEntity).toHaveBeenCalledTimes(1);
  });

  it("uses onNavigate override instead of router.push when provided", async () => {
    mockSendMessage.mockResolvedValue(undefined);
    const createEntity = vi.fn().mockResolvedValue(makeEntity({ id: "p-nav" }));
    const onNavigate = vi.fn();

    const { result } = renderHook(() =>
      useGuidedEntityCreation<FakeEntity>({
        domain: "buyer_persona",
        tenantId: "t-1",
        createEntity,
        onNavigate,
      }),
    );

    await act(async () => {
      await result.current.create();
    });

    expect(onNavigate).toHaveBeenCalledWith("/t-1/brand-studio/publico/persona/p-nav");
    expect(mockPush).not.toHaveBeenCalled();
  });

  it("reports telemetry event after triggering guided", async () => {
    mockSendMessage.mockResolvedValue(undefined);
    const createEntity = vi.fn().mockResolvedValue(makeEntity({ id: "p-tele" }));

    const { result } = renderHook(() =>
      useGuidedEntityCreation<FakeEntity>({
        domain: "buyer_persona",
        tenantId: "t-1",
        createEntity,
      }),
    );

    await act(async () => {
      await result.current.create();
    });

    expect(mockReportEvent).toHaveBeenCalledWith(
      "guided_setup_requested",
      expect.objectContaining({ domain: "buyer_persona", entity_id: "p-tele" }),
      "tok-test",
    );
  });
});
