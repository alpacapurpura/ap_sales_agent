"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";

import { useAutoSave } from "@/lib/form-runtime/hooks";
import {
  buyerPersonaApi,
  type BuyerPersona,
  type BuyerPersonaSectionUpdateDTO,
} from "@/lib/api/buyer-persona";

const PERSONA_AUTOSAVE_DELAY_MS = 1500;

/**
 * Single buyer-persona detail hook. Autosave now delegates to the shared
 * useAutoSave primitive (lib/form-runtime/hooks) — same state machine the
 * form-runtime AutosaveBanner consumes, so "saving / saved / error" surfaces
 * uniformly across the product.
 */
export function useBuyerPersona(tenantId: string, personaId: string) {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  const queryKey = useMemo(
    () => ["buyer_persona", tenantId, personaId] as const,
    [tenantId, personaId],
  );

  const { data, isLoading, error } = useQuery<BuyerPersona>({
    queryKey,
    queryFn: async () => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      return buyerPersonaApi.get(token, personaId);
    },
    enabled: Boolean(personaId),
  });

  const saveFn = useCallback(
    async (updates: BuyerPersonaSectionUpdateDTO) => {
      const token = await getToken();
      if (!token) throw new Error("No auth token");
      const updated = await buyerPersonaApi.patch(token, personaId, updates);
      queryClient.setQueryData(queryKey, updated);
    },
    [getToken, personaId, queryClient, queryKey],
  );

  const autosave = useAutoSave<BuyerPersonaSectionUpdateDTO>({
    saveFn,
    delay: PERSONA_AUTOSAVE_DELAY_MS,
  });

  return {
    persona: data ?? null,
    isLoading,
    error,
    /** State machine: "idle" | "saving" | "saved" | "error". */
    saveState: autosave.state,
    /** True while a save is in flight. */
    isSaving: autosave.state === "saving",
    /** Timestamp of the last successful save, or null. */
    savedAt: autosave.lastSavedAt,
    /** Imperative save — bypasses debounce. */
    save: saveFn,
    /** Debounced save (1500 ms). Subsequent calls within the window reset the timer. */
    debouncedSave: autosave.trigger,
    /** Retry the last attempted payload after an error. */
    retry: autosave.retry,
    /** Cancel any pending debounced save. */
    cancel: autosave.cancel,
  };
}
