import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { 
  BrandSettings, BrandIdentity, KeyFigure, AuthorityItem, ContactData, BrandVisuals, BrandStrategy, BrandStory, TestimonialItem } from "@/features/brand/types";
import { brandApi } from "@/features/brand/api";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

export function useBrandSettings() {
  const { getToken } = useAuth();
  const queryClient = useQueryClient();

  const { data: settings, isLoading: loading, error, refetch } = useQuery({
    queryKey: ['brand-settings'],
    queryFn: async () => {
      const token = await getToken();
      if (!token) return null;
      const data = await brandApi.getBrandSettings(token);
      // Ensure visuals object exists if backend returns incomplete data (migration)
      if (!data.visuals) {
          data.visuals = {
              primary_color: "#0f172a",
              accent_color: "#3b82f6",
              font_heading: "Inter",
              font_body: "Inter",
              background_color: "#ffffff",
              text_primary_color: "#0f172a",
              text_on_primary: "#ffffff",
              design_style: "Minimalista",
              usage_guidelines: []
          };
      }

      // Initialize other sections if missing to prevent null reference errors
      if (!data.identity) data.identity = {};
      
      // Initialize strategy with safe defaults for arrays
      if (!data.strategy) {
        data.strategy = {
            competitors: [],
            methodology_pillars: []
        };
      } else {
        if (!data.strategy.competitors) data.strategy.competitors = [];
        if (!data.strategy.methodology_pillars) data.strategy.methodology_pillars = [];
      }

      if (!data.story) data.story = {};
      if (!data.contact) data.contact = {};
      if (!data.team) data.team = [];
      
      return data;
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
       queryClient.setQueryData(['brand-settings'], updated);
    },
    onError: (err) => {
       console.error("Error saving settings:", err);
       toast.error("No se pudo guardar.");
    }
  });

  const updateIdentity = async (identity: BrandIdentity) => {
    if (!settings) return;
    const newSettings = { ...settings, identity };
    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Identidad corporativa actualizada.");
    } catch {}
  };

  const updateVisuals = async (visuals: BrandVisuals) => {
    if (!settings) return;
    const newSettings = { ...settings, visuals };
    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Identidad visual actualizada.");
    } catch {}
  };

  const updateTeam = async (team: KeyFigure[]) => {
    if (!settings) return;
    const newSettings = { ...settings, team };
    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Equipo actualizado.");
    } catch {}
  };

  const updateVault = async (vault: AuthorityItem[]) => {
    if (!settings) return;
    const newSettings = { ...settings, authority_vault: vault };
    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Respaldo institucional actualizado.");
    } catch {}
  };

  const updateContact = async (contact: ContactData) => {
    if (!settings) return;
    const newSettings = { ...settings, contact };
    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Datos de contacto actualizados.");
    } catch {}
  };

  const updateStrategy = async (strategy: BrandStrategy) => {
    if (!settings) return;
    const newSettings = { ...settings, strategy };
    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Estrategia actualizada.");
    } catch {}
  };

  const updateStory = async (story: BrandStory) => {
    if (!settings) return;
    const newSettings = { ...settings, story };
    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Historia actualizada.");
    } catch {}
  };

  const updateTestimonials = async (testimonials: TestimonialItem[]) => {
    if (!settings) return;
    const newSettings = { ...settings, testimonials };
    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Testimonios actualizados.");
    } catch {}
  };

  const updateAllSettings = async (partialSettings: Partial<BrandSettings>) => {
    if (!settings) return;
    const newSettings = { 
        ...settings, 
        ...partialSettings,
        identity: { ...settings.identity, ...partialSettings.identity },
        visuals: { 
            ...settings.visuals, 
            ...partialSettings.visuals,
            logos: { ...settings.visuals?.logos, ...partialSettings.visuals?.logos }
        },
        story: { ...settings.story, ...partialSettings.story },
        strategy: { ...settings.strategy, ...partialSettings.strategy },
        contact: { ...settings.contact, ...partialSettings.contact },
        team: partialSettings.team || settings.team,
        testimonials: partialSettings.testimonials || settings.testimonials,
        authority_vault: partialSettings.authority_vault || settings.authority_vault,
    };

    try {
        await updateMutation.mutateAsync(newSettings);
        toast.success("Configuración de marca actualizada correctamente.");
    } catch {}
  };

  return {
    settings: settings || null,
    loading,
    error,
    saving: updateMutation.isPending,
    updateIdentity,
    updateTeam,
    updateVault,
    updateContact,
    updateVisuals,
    updateStrategy,
    updateStory,
    updateTestimonials,
    updateAllSettings,
    refetch
  };
}
