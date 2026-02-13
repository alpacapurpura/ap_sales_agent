import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { 
  BrandSettings, 
  brandApi, 
  BrandIdentity, 
  KeyFigure, 
  AuthorityItem, 
  ContactData,
  BrandVisuals,
  BrandStrategy,
  BrandStory,
  TestimonialItem
} from "@/lib/api/brand";

export function useBrandSettings() {
  const { getToken } = useAuth();
  const [settings, setSettings] = useState<BrandSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      const token = await getToken();
      if (!token) return;
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
      setSettings(data);
    } catch (error) {
      console.error("Error fetching brand settings:", error);
      toast.error("No se pudo cargar la configuración de marca.");
    } finally {
      setLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    fetchSettings();
  }, [fetchSettings]);

  const updateIdentity = async (identity: BrandIdentity) => {
    if (!settings) return;
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const newSettings = { ...settings, identity };
      const updated = await brandApi.updateBrandSettings(newSettings, token);
      setSettings(updated);
      toast.success("Identidad corporativa actualizada.");
    } catch (error) {
        console.error("Error saving identity:", error);
      toast.error("No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  };

  const updateVisuals = async (visuals: BrandVisuals) => {
    if (!settings) return;
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const newSettings = { ...settings, visuals };
      const updated = await brandApi.updateBrandSettings(newSettings, token);
      setSettings(updated);
      toast.success("Identidad visual actualizada.");
    } catch (error) {
        console.error("Error saving visuals:", error);
      toast.error("No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  };

  const updateTeam = async (team: KeyFigure[]) => {
    if (!settings) return;
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const newSettings = { ...settings, team };
      const updated = await brandApi.updateBrandSettings(newSettings, token);
      setSettings(updated);
      toast.success("Equipo actualizado.");
    } catch (error) {
        console.error("Error saving team:", error);
      toast.error("No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  };

  const updateVault = async (vault: AuthorityItem[]) => {
    if (!settings) return;
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const newSettings = { ...settings, authority_vault: vault };
      const updated = await brandApi.updateBrandSettings(newSettings, token);
      setSettings(updated);
      toast.success("Respaldo institucional actualizado.");
    } catch (error) {
        console.error("Error saving vault:", error);
      toast.error("No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  };

  const updateContact = async (contact: ContactData) => {
    if (!settings) return;
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const newSettings = { ...settings, contact };
      const updated = await brandApi.updateBrandSettings(newSettings, token);
      setSettings(updated);
      toast.success("Datos de contacto actualizados.");
    } catch (error) {
        console.error("Error saving contact:", error);
      toast.error("No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  };

  const updateStrategy = async (strategy: BrandStrategy) => {
    if (!settings) return;
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const newSettings = { ...settings, strategy };
      const updated = await brandApi.updateBrandSettings(newSettings, token);
      setSettings(updated);
      toast.success("Estrategia actualizada.");
    } catch (error) {
        console.error("Error saving strategy:", error);
      toast.error("No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  };

  const updateStory = async (story: BrandStory) => {
    if (!settings) return;
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const newSettings = { ...settings, story };
      const updated = await brandApi.updateBrandSettings(newSettings, token);
      setSettings(updated);
      toast.success("Historia actualizada.");
    } catch (error) {
        console.error("Error saving story:", error);
      toast.error("No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  };

  const updateTestimonials = async (testimonials: TestimonialItem[]) => {
    if (!settings) return;
    setSaving(true);
    try {
      const token = await getToken();
      if (!token) return;
      
      const newSettings = { ...settings, testimonials };
      const updated = await brandApi.updateBrandSettings(newSettings, token);
      setSettings(updated);
      toast.success("Testimonios actualizados.");
    } catch (error) {
        console.error("Error saving testimonials:", error);
      toast.error("No se pudo guardar.");
    } finally {
      setSaving(false);
    }
  };

  return {
    settings,
    loading,
    saving,
    updateIdentity,
    updateTeam,
    updateVault,
    updateContact,
    updateVisuals,
    updateStrategy,
    updateStory,
    updateTestimonials,
    refetch: fetchSettings
  };
}
