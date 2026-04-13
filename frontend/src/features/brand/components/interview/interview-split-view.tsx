"use client";

/**
 * Brand Interview Split View — backward-compatible wrapper.
 *
 * Delegates to the generic InterviewSplitView from copilot,
 * with domain="brand". Ensures the brand preview is registered
 * before rendering.
 */

// Side-effect import: registers brand preview in the PreviewRegistry
import "./register-brand-preview";

import { InterviewSplitView as GenericInterviewSplitView } from "@/features/copilot/components/interview/interview-split-view";

interface InterviewSplitViewProps {
  sessionId?: string;
}

export function InterviewSplitView({ sessionId }: InterviewSplitViewProps) {
  return (
    <GenericInterviewSplitView
      domain="brand"
      sessionId={sessionId}
      routeBase="brand-studio/interview"
    />
  );
}
