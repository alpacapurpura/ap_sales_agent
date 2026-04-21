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
  FromVoiceToneResponse,
} from "../types/personality";

const API_URL = config.api.baseUrl;

export const PERSONALITY_KEYS = {
  /** Invalidates all personality queries at once. */
  all: ["personality"] as const,
  presets: ["personality", "presets"] as const,
  active: (tenantId: string) => ["personality", "active", tenantId] as const,
};

// ── Presets ────────────────────────────────────────────────────────────────

/**
 * Fetches the 6 personality preset definitions from the backend catalog.
 * Presets are static — stale time is 10 minutes. Returns an array of
 * `PresetSummary` objects each with key, name, icon, description,
 * sample_message, and base dimensions.
 */
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

/**
 * Fetches the currently active `PersonalityProfile` for the given tenant.
 * Returns `null` when no profile is active (404 from backend). Stale time
 * is 5 minutes — active profile changes infrequently outside explicit user
 * actions. Invalidated by all mutation hooks in this module.
 */
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

/**
 * Activates one of the 6 preset personalities by key (e.g. `"warm_close"`).
 * Creates a new `PersonalityProfile` row with `profile_type="preset"` and
 * sets it as the active profile for the tenant. Deactivates the previously
 * active profile. Invalidates all personality queries on success.
 */
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
      void queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.all });
    },
  });
}

// ── Update Dimensions ──────────────────────────────────────────────────────

/**
 * Updates the 6 personality dimensions of an existing profile via
 * `PUT /{profileId}/dimensions`. The backend recompiles the
 * `system_instruction` on each update. Invalidates all personality queries
 * on success.
 *
 * Mutation variable: `{ profileId: string; dimensions: PersonalityDimensions }`.
 * Returns the updated `PersonalityProfile`.
 */
export function useUpdateDimensions() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      profileId,
      dimensions,
    }: {
      profileId: string;
      dimensions: PersonalityDimensions;
    }): Promise<PersonalityProfile> => {
      const token = await getToken();
      const res = await fetchClient(`${API_URL}/api/v1/brand/personality/${profileId}/dimensions`, {
        method: "PUT",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ dimensions }),
      });
      if (!res.ok) throw new Error(`Error ${res.status}`);
      return res.json() as Promise<PersonalityProfile>;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.all });
    },
  });
}

// ── Simulate Personality ───────────────────────────────────────────────────

/**
 * Triggers a personality simulation for the given profile, returning a set
 * of `SampleExchange` objects representing how the profile would respond in
 * typical sales contexts (greeting, price objection, follow-up, etc.).
 * V1 returns stored sample exchanges — V2 will use LLM-driven simulation.
 */
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

// ── Clone Personality ──────────────────────────────────────────────────────

/**
 * Clones a personality from raw conversational material (text paste or file
 * upload). Runs the `personality_app` LangGraph pipeline on the backend
 * (parser → janitor → psychologist → architect → embedder → simulator).
 * The resulting profile has `is_active=false` until `useActivateProfile` is
 * called — lets users preview and approve before switching. Invalidates all
 * personality queries on success.
 *
 * Accepts `{ textInput?, file?, userName? }`. If `file` is provided, sends
 * multipart/form-data; otherwise sends JSON.
 */
export function useClonePersonality() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      textInput,
      file,
      userName,
    }: {
      textInput?: string;
      file?: File;
      userName?: string;
    }): Promise<PersonalityProfile> => {
      const token = await getToken();
      let body: BodyInit;
      let headers: Record<string, string> = { Authorization: `Bearer ${token}` };

      if (file) {
        const formData = new FormData();
        formData.append("file", file);
        if (textInput) formData.append("text_input", textInput);
        if (userName) formData.append("user_name", userName);
        body = formData;
      } else {
        body = JSON.stringify({ text_input: textInput, user_name: userName });
        headers = { ...headers, "Content-Type": "application/json" };
      }

      const res = await fetchClient(`${API_URL}/api/v1/brand/personality/clone`, {
        method: "POST",
        headers,
        body,
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(err.detail ?? `Error ${res.status}`);
      }
      return res.json() as Promise<PersonalityProfile>;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.all });
    },
  });
}

// ── Activate Profile ───────────────────────────────────────────────────────

/**
 * Activates a pre-existing profile (cloned, custom, or migrated) by its ID.
 * Idempotent — calling on an already-active profile returns the profile
 * unchanged. Deactivates the previously active profile in the same
 * transaction. Returns 404 if the profile does not exist or belongs to a
 * different tenant. Invalidates all personality queries on success.
 */
export function useActivateProfile() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (profileId: string): Promise<PersonalityProfile> => {
      const token = await getToken();
      const res = await fetchClient(`${API_URL}/api/v1/brand/personality/${profileId}/activate`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(err.detail ?? `Error ${res.status}`);
      }
      return res.json() as Promise<PersonalityProfile>;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.all });
    },
  });
}

// ── Migrate from Voice Tone ────────────────────────────────────────────────

/**
 * One-time migration: reads the tenant's legacy `BrandIdentity.voice_tone`
 * free-text, maps it to the nearest personality preset via LLM similarity,
 * creates a `PersonalityProfile` with `profile_type="migrated_from_voice_tone"`,
 * and auto-activates it. Returns the new profile, the matched preset key
 * (or null if no close match), and the match confidence (0.0–1.0).
 *
 * Returns 404 if no legacy voice_tone text exists.
 * Returns 409 if the tenant already has a migrated profile.
 * Invalidates all personality queries on success.
 */
export function useMigrateFromVoiceTone() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (): Promise<FromVoiceToneResponse> => {
      const token = await getToken();
      const res = await fetchClient(`${API_URL}/api/v1/brand/personality/from-voice-tone`, {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({}),
      });
      if (!res.ok) {
        const err = (await res.json().catch(() => ({}))) as { detail?: string };
        throw new Error(err.detail ?? `Error ${res.status}`);
      }
      return res.json() as Promise<FromVoiceToneResponse>;
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.all });
    },
  });
}

// ── Delete Personality ─────────────────────────────────────────────────────

/**
 * Soft-deletes a personality profile by ID. The profile is flagged with
 * `deleted_at` — it no longer appears in listings but its data is preserved
 * for audit. Also removes associated Qdrant style anchors via the backend
 * `delete_with_anchors` service method. Invalidates all personality queries.
 */
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
      void queryClient.invalidateQueries({ queryKey: PERSONALITY_KEYS.all });
    },
  });
}
