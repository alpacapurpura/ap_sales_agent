"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery, useQueryClient } from "@tanstack/react-query";

import {
  buyerPersonaApi,
  type BuyerPersona,
  type BuyerPersonaSectionUpdateDTO,
} from "@/lib/api/buyer-persona";

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

  const [isSaving, setIsSaving] = useState(false);
  const [savedAt, setSavedAt] = useState<Date | null>(null);
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
    };
  }, []);

  const save = useCallback(
    async (updates: BuyerPersonaSectionUpdateDTO) => {
      const token = await getToken();
      if (!token) return;
      setIsSaving(true);
      try {
        const updated = await buyerPersonaApi.patch(token, personaId, updates);
        queryClient.setQueryData(queryKey, updated);
        setSavedAt(new Date());
      } catch (err) {
        console.warn("Failed to save persona:", err);
      } finally {
        setIsSaving(false);
      }
    },
    [getToken, personaId, queryClient, queryKey],
  );

  const debouncedSave = useCallback(
    (updates: BuyerPersonaSectionUpdateDTO, delayMs = 1500) => {
      if (debounceTimerRef.current) clearTimeout(debounceTimerRef.current);
      debounceTimerRef.current = setTimeout(() => {
        void save(updates);
      }, delayMs);
    },
    [save],
  );

  return {
    persona: data ?? null,
    isLoading,
    error,
    isSaving,
    savedAt,
    save,
    debouncedSave,
  };
}
