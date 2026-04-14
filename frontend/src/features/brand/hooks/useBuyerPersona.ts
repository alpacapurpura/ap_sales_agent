"use client";

import { useCallback, useRef, useState } from "react";
import { useAuth } from "@clerk/nextjs";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";

import {
  buyerPersonaApi,
  type BuyerPersona,
  type BuyerPersonaSectionUpdateDTO,
} from "@/lib/api/buyer-persona";

export function useBuyerPersona(personaId: string) {
  const { getToken } = useAuth();
  const params = useParams<{ tenantId: string }>();
  const tenantId = params?.tenantId ?? "";
  const queryKey = ["buyer_persona", tenantId, personaId] as const;

  const { data, isLoading, error, refetch } = useQuery<BuyerPersona>({
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

  const save = useCallback(
    async (updates: BuyerPersonaSectionUpdateDTO) => {
      const token = await getToken();
      if (!token) return;
      setIsSaving(true);
      try {
        await buyerPersonaApi.patch(token, personaId, updates);
        setSavedAt(new Date());
        await refetch();
      } catch (err) {
        console.warn("Failed to save persona:", err);
      } finally {
        setIsSaving(false);
      }
    },
    [getToken, personaId, refetch],
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
