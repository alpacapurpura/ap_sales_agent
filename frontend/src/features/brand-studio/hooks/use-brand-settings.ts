import { useAuth } from "@clerk/nextjs";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { brandApi } from "@/features/brand-studio/api";
import {
  BrandIdentity,
  KeyFigure,
  ContactData,
  BrandVisuals,
  BrandStrategy,
  BrandStory,
  BrandPositioning,
  BrandNarrative,
  CommunicationAssets,
} from "@/features/brand-studio/types";

import type { BrandSettings } from "@/features/brand-studio/types";

function withDefaults(data: BrandSettings): BrandSettings {
  return {
    ...data,
    visuals: data.visuals ?? {
      primary_color: "#0f172a",
      accent_color: "#3b82f6",
      font_heading: "Inter",
      font_body: "Inter",
      background_color: "#ffffff",
      text_primary_color: "#0f172a",
      text_on_primary: "#ffffff",
      design_style: "Minimalista",
      usage_guidelines: [],
    },
    identity: data.identity ?? ({} as BrandSettings["identity"]),
    strategy: {
      methodology_pillars: [],
      ...data.strategy,
    } as BrandSettings["strategy"],
    story: data.story ?? ({} as BrandSettings["story"]),
    contact: data.contact ?? ({} as BrandSettings["contact"]),
    team: data.team ?? [],
  } as BrandSettings;
}

/**
 *
 */
export function useBrandSettings() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const {
    data: settings,
    isLoading: loading,
    error,
    refetch,
  } = useQuery({
    queryKey: ["brand-settings"],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return null;
      const data = await brandApi.getBrandSettings(token);
      return withDefaults(data);
    },
    staleTime: 1000 * 60 * 5, // 5 minutes cache
  });

  const updateMutation = useMutation({
    mutationFn: async (newSettings: BrandSettings) => {
      const token = await getToken();
      if (!token) throw new Error("No token");
      return brandApi.updateBrandSettings(newSettings, token);
    },
    onSuccess: (updated) => {
      queryClient.setQueryData(["brand-settings"], updated);
    },
    onError: (err) => {
      console.error("Error saving settings:", err);
      toast.error("No se pudo guardar.");
    },
  });

  // Factory for simple key-based updaters
  const createUpdater =
    <K extends keyof BrandSettings>(key: K, successMsg: string) =>
    async (value: BrandSettings[K]) => {
      if (!settings) return;
      try {
        await updateMutation.mutateAsync({ ...settings, [key]: value });
        toast.success(successMsg);
      } catch {
        // mutation error state handles UI feedback
      }
    };

  const updateIdentity = createUpdater("identity", "Identidad corporativa actualizada.");
  const updateVisuals = createUpdater("visuals", "Identidad visual actualizada.");
  // Deprecated: writes to brand_settings.team JSONB. Kept for the legacy
  // InstructorsManager in offer-studio until it migrates to the
  // social_proof team_members API (src/lib/api/team-member.ts).
  const updateTeam = createUpdater("team", "Equipo actualizado.");
  const updateContact = createUpdater("contact", "Datos de contacto actualizados.");
  const updateStrategy = createUpdater("strategy", "Estrategia actualizada.");
  const updateStory = createUpdater("story", "Historia actualizada.");
  const updatePositioning = createUpdater("positioning", "Posicionamiento actualizado.");
  const updateNarrative = createUpdater("narrative", "Narrativa actualizada.");
  const updateCommunicationAssets = createUpdater(
    "communication_assets",
    "Activos de comunicacion actualizados.",
  );

  const updateAllSettings = async (partialSettings: Partial<BrandSettings>) => {
    if (!settings) return;
    const newSettings = {
      ...settings,
      ...partialSettings,
      identity: { ...settings.identity, ...partialSettings.identity },
      visuals: {
        ...settings.visuals,
        ...partialSettings.visuals,
        logos: { ...settings.visuals?.logos, ...partialSettings.visuals?.logos },
      },
      story: { ...settings.story, ...partialSettings.story },
      strategy: { methodology_pillars: [], ...settings.strategy, ...partialSettings.strategy },
      contact: { ...settings.contact, ...partialSettings.contact },
    };

    try {
      await updateMutation.mutateAsync(newSettings);
      toast.success("Configuracion de marca actualizada correctamente.");
    } catch {
      // mutation error state handles UI feedback
    }
  };

  return {
    settings: settings || null,
    loading,
    error,
    saving: updateMutation.isPending,
    updateIdentity,
    updateTeam,
    updateContact,
    updateVisuals,
    updateStrategy,
    updateStory,
    updatePositioning,
    updateNarrative,
    updateCommunicationAssets,
    updateAllSettings,
    refetch,
  };
}
