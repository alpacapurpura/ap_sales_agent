import { describe, it, expect, beforeEach } from "vitest";
import { act } from "@testing-library/react";
import { useCopilotStore } from "../../store/copilot-store";

describe("Copilot Store — Interview Extensions", () => {
  beforeEach(() => {
    act(() => {
      useCopilotStore.getState().clearInterview();
    });
  });

  it("setInterviewMode activates interview", () => {
    act(() => {
      useCopilotStore.getState().setInterviewMode(true, "session-123");
    });
    const state = useCopilotStore.getState();
    expect(state.interviewMode).toBe(true);
    expect(state.interviewSessionId).toBe("session-123");
  });

  it("updateInterviewPreview merges delta", () => {
    act(() => {
      useCopilotStore.getState().setInterviewMode(true, "s1");
      useCopilotStore.getState().updateInterviewPreview({ "story.origin": "v1" });
      useCopilotStore.getState().updateInterviewPreview({ "story.mission": "v2" });
    });
    const data = useCopilotStore.getState().interviewPreviewData;
    expect(data).toEqual({ "story.origin": "v1", "story.mission": "v2" });
  });

  it("clearInterview resets all fields", () => {
    act(() => {
      useCopilotStore.getState().setInterviewMode(true, "s1");
      useCopilotStore.getState().updateInterviewPreview({ key: "val" });
      useCopilotStore.getState().clearInterview();
    });
    const state = useCopilotStore.getState();
    expect(state.interviewMode).toBe(false);
    expect(state.interviewSessionId).toBeNull();
    expect(state.interviewPreviewData).toBeNull();
  });

  it("interviewMode false by default", () => {
    const fresh = useCopilotStore.getState();
    // After clearInterview in beforeEach, it should be false
    expect(fresh.interviewMode).toBe(false);
  });

  it("setInterviewMode without sessionId sets null", () => {
    act(() => {
      useCopilotStore.getState().setInterviewMode(true);
    });
    expect(useCopilotStore.getState().interviewSessionId).toBeNull();
  });
});
