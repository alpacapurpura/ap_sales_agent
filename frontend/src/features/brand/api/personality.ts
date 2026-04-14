"use client";

import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

import { config } from "@/lib/config";
import { fetchClient } from "@/lib/http-client";

import type {
  PersonalityProfile,
  PresetSummary,
  PersonalityDimensions,
  SimulationResponse,
} from "../types/personality";

const API_URL = config.api.baseUrl;

const PERSONALITY_KEYS = {
  presets: ["personality", "presets"] as const,
  active: (tenantId: string) => ["personality", "active", tenantId] as const,
};

// ── Presets ────────────────────────────────────────────────────────────────

export function usePersonalityPresets() {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: PERSONALITY_KEYS.presets,
    queryFn: async (): Promise<PresetSummary[]> => {
      const token = await getToken();
      const res = await fetchClient(`${API_URL}/api/v1/brand/personality/presets`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.json() as Promise<PresetSummary[]>;
    },
    staleTime: 1000 * 60 * 10, // 10 min — presets don't change often
  });
}

// ── Active Profile ─────────────────────────────────────────────────────────

export function useActivePersonality(tenantId: string) {
  const { getToken } = useAuth();
  return useQuery({
    queryKey: PERSONALITY_KEYS.active(tenantId),
    queryFn: async (): Promise<PersonalityProfile | null> => {
      const token = await getToken();
      const res = await fetchClient(`${API_URL}/api/v1/brand/personality/active`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.status === 404) return null;
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.json() as Promise<PersonalityProfile | null>;
    },
    staleTime: 1000 * 60 * 5,
  });
}

// ── Select Preset ──────────────────────────────────────────────────────────

export function useSelectPreset() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (presetKey: string): Promise<PersonalityProfile> => {
      const token = await getToken();
      const res = await fetchClient(`${API_URL}/api/v1/brand/personality/select-preset`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ preset_key: presetKey }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.json() as Promise<PersonalityProfile>;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["personality"] });
    },
  });
}

// ── Update Dimensions ──────────────────────────────────────────────────────

export function useUpdateDimensions() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (dimensions: PersonalityDimensions): Promise<PersonalityProfile> => {
      const token = await getToken();
      const res = await fetchClient(`${API_URL}/api/v1/brand/personality/dimensions`, {
        method: "PATCH",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify(dimensions),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.json() as Promise<PersonalityProfile>;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["personality"] });
    },
  });
}

// ── Simulate Personality ───────────────────────────────────────────────────

export function useSimulatePersonality() {
  const { getToken } = useAuth();
  return useMutation({
    mutationFn: async (profileId: string): Promise<SimulationResponse> => {
      const token = await getToken();
      const url = `${API_URL}/api/v1/brand/personality/${profileId}/simulate`;
      const res = await fetchClient(url, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.json() as Promise<SimulationResponse>;
    },
  });
}

// ── Delete Personality ─────────────────────────────────────────────────────

export function useDeletePersonality() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (profileId: string): Promise<void> => {
      const token = await getToken();
      const url = `${API_URL}/api/v1/brand/personality/${profileId}`;
      const res = await fetchClient(url, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ["personality"] });
    },
  });
}
