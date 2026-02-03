import { useState, useEffect, useCallback } from "react";
import { useAuth } from "@clerk/nextjs";
import { toast } from "sonner";
import { 
  BrandSettings, 
  brandApi, 
  BrandIdentity, 
  KeyFigure, 
  AuthorityItem, 
  ContactData 
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

  return {
    settings,
    loading,
    saving,
    updateIdentity,
    updateTeam,
    updateVault,
    updateContact,
    refetch: fetchSettings
  };
}
