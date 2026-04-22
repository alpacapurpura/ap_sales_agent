import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, act } from "@testing-library/react";
import { describe, it, expect, vi, beforeEach } from "vitest";

import type { ReactNode } from "react";

vi.mock("@clerk/nextjs", () => ({
  useAuth: () => ({ getToken: () => Promise.resolve("test-token") }),
}));

vi.mock("../../api/media-api", async () => {
  const actual = await vi.importActual<typeof import("../../api/media-api")>("../../api/media-api");
  return {
    ...actual,
    uploadCopilotMedia: vi.fn().mockResolvedValue({
      asset_id: "asset-1",
      public_url: "https://cdn.example.com/file.pdf",
      mime: "application/pdf",
      size_bytes: 1024,
      kind: "document",
    }),
  };
});

import { useMediaUpload } from "../use-media-upload";

function wrapper({ children }: { children: ReactNode }) {
  const qc = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={qc}>{children}</QueryClientProvider>;
}

describe("useMediaUpload", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("starts with empty uploads", () => {
    const { result } = renderHook(() => useMediaUpload(), { wrapper });
    expect(result.current.uploads).toHaveLength(0);
  });

  it("validates invalid MIME type", () => {
    const { result } = renderHook(() => useMediaUpload(), { wrapper });
    const fakeFile = new File(["data"], "test.exe", { type: "application/x-msdownload" });
    const error = result.current.validateFile(fakeFile);
    expect(error).toContain("no soportado");
  });

  it("accepts valid PDF MIME type", () => {
    const { result } = renderHook(() => useMediaUpload(), { wrapper });
    const fakeFile = new File(["data"], "doc.pdf", { type: "application/pdf" });
    const error = result.current.validateFile(fakeFile);
    expect(error).toBeNull();
  });

  it("adds upload item when uploadMedia is called", async () => {
    const { result } = renderHook(() => useMediaUpload(), { wrapper });
    const fakeFile = new File(["data"], "doc.pdf", { type: "application/pdf" });

    await act(async () => {
      await result.current.uploadMedia(fakeFile);
    });

    expect(result.current.uploads.length).toBe(1);
    expect(result.current.uploads[0].status).toBe("success");
    expect(result.current.uploads[0].file).toBe(fakeFile);
  });

  it("removeUpload removes the item from the list", async () => {
    const { result } = renderHook(() => useMediaUpload(), { wrapper });
    const fakeFile = new File(["data"], "doc.pdf", { type: "application/pdf" });

    await act(async () => {
      await result.current.uploadMedia(fakeFile);
    });

    const { id } = result.current.uploads[0];

    act(() => {
      result.current.removeUpload(id);
    });

    expect(result.current.uploads).toHaveLength(0);
  });
});
