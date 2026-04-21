"use client";

import { useAuth } from "@clerk/nextjs";
import { useMutation } from "@tanstack/react-query";
import { useCallback, useState } from "react";

import { invokeOfferSectionTool, type OfferCopilotResult } from "../api/section-tools-api";

// ---------------------------------------------------------------------------
// Re-export type so consumers can import from the hook file (convenience)
// ---------------------------------------------------------------------------

export type { OfferCopilotResult } from "../api/section-tools-api";

// ---------------------------------------------------------------------------
// Hook interface
// ---------------------------------------------------------------------------

export interface UseOfferCopilotResult {
  /**
   * Invoke a named backend tool. Returns the parsed OfferCopilotResult.
   * Never writes to the backend — draft_fields are pending-patch only.
   */
  invokeTool: (toolKey: string, toolArgs?: Record<string, string>) => Promise<OfferCopilotResult>;
  /** True while the mutation is in-flight. */
  isInvoking: boolean;
  /** Last successful tool result. Cleared when offerId or sectionSlug change. */
  lastResult: OfferCopilotResult | null;
  /** Last invocation error. Cleared when offerId or sectionSlug change. */
  lastError: Error | null;
}

interface InvokePayload {
  toolKey: string;
  toolArgs?: Record<string, string>;
}

/**
 * Manage copilot tool invocations for a single section.
 *
 * - Invokes `POST /api/v1/copilot/offer-section-tools/{toolKey}`.
 * - Never auto-applies draft_fields — caller receives them via the resolved
 *   promise + lastResult and applies via react-hook-form setValue.
 * - Clears state when `offerId` or `sectionSlug` change so stale results
 *   from a previous section never bleed through.
 *
 * Decision R3 from DECISIONS.md: no write-through on copilot tools.
 */
export function useOfferCopilot({
  offerId,
  sectionSlug,
  editionCode,
}: {
  offerId: string;
  sectionSlug: string;
  editionCode?: string;
}): UseOfferCopilotResult {
  const { getToken } = useAuth();

  const [lastResult, setLastResult] = useState<OfferCopilotResult | null>(null);
  const [lastError, setLastError] = useState<Error | null>(null);

  // Derived-state reset: track prev offerId and sectionSlug in state so we
  // can reset lastResult/lastError when the section changes. This is the
  // recommended React pattern for "derived state" (replaces getDerivedStateFromProps).
  // See: https://react.dev/learn/you-might-not-need-an-effect#adjusting-some-state-when-a-prop-changes
  const [prevOfferId, setPrevOfferId] = useState(offerId);
  const [prevSectionSlug, setPrevSectionSlug] = useState(sectionSlug);

  if (prevOfferId !== offerId || prevSectionSlug !== sectionSlug) {
    setPrevOfferId(offerId);
    setPrevSectionSlug(sectionSlug);
    setLastResult(null);
    setLastError(null);
  }

  const mutation = useMutation<OfferCopilotResult, Error, InvokePayload>({
    mutationFn: async ({ toolKey, toolArgs = {} }) => {
      const token = await getToken();
      if (!token) throw new Error("No autenticado");
      return invokeOfferSectionTool({
        toolKey,
        offerId,
        sectionSlug,
        editionCode,
        toolArgs,
        token,
      });
    },
  });

  const invokeTool = useCallback(
    async (toolKey: string, toolArgs: Record<string, string> = {}): Promise<OfferCopilotResult> => {
      try {
        const result = await mutation.mutateAsync({ toolKey, toolArgs });
        setLastResult(result);
        setLastError(null);
        return result;
      } catch (err) {
        const error = err instanceof Error ? err : new Error(String(err));
        setLastError(error);
        throw error;
      }
    },
    [mutation],
  );

  return {
    invokeTool,
    isInvoking: mutation.isPending,
    lastResult,
    lastError,
  };
}
