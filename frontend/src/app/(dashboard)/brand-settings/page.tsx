"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@clerk/nextjs";
import { BrandSettings, brandApi, BrandIdentity, KeyFigure, AuthorityItem, ContactData } from "@/lib/api/brand";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { BrandIdentityForm } from "@/components/brand/brand-identity-form";
import { KeyFiguresForm } from "@/components/brand/key-figures-form";
import { AuthorityVaultForm } from "@/components/brand/authority-vault-form";
import { ContactDataForm } from "@/components/brand/contact-data-form";
import { AvatarManager } from "@/components/brand/avatar-manager";
import { PersonalityCloneForm } from "@/components/brand/personality-clone-form";
import { Loader2, Building2, Phone, Award, Users, Brain, ShieldCheck } from "lucide-react";
import { toast } from "sonner";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

function PlaceholderContent({ title, icon: Icon }: { title: string, icon: any }) {
  return (
    <Card className="w-full min-h-[600px]">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Icon className="h-6 w-6" />
          {title}
        </CardTitle>
        <CardDescription>Esta funcionalidad estará disponible próximamente.</CardDescription>
      </CardHeader>
      <CardContent className="h-[400px] flex items-center justify-center text-muted-foreground bg-muted/10 rounded-md border border-dashed m-6">
        Aqui
      </CardContent>
    </Card>
  );
}

export default function BrandSettingsPage() {
  const { getToken } = useAuth();
  // const { toast } = useToast();
  const [settings, setSettings] = useState<BrandSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    const fetchSettings = async () => {
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
    };
    fetchSettings();
  }, [getToken]);

  const handleSaveIdentity = async (identity: BrandIdentity) => {
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

  const handleSaveTeam = async (team: KeyFigure[]) => {
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

  const handleSaveVault = async (vault: AuthorityItem[]) => {
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

  const handleSaveContact = async (contact: ContactData) => {
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

  if (loading) {
    return <div className="flex justify-center items-center h-full"><Loader2 className="animate-spin" /></div>;
  }

  if (!settings) {
    return <div>Error al cargar configuración.</div>;
  }

  return (
    <div className="hidden space-y-6 p-10 pb-16 md:block">
      <div className="space-y-0.5">
        <h2 className="text-2xl font-bold tracking-tight">Sobre la Marca (Global Brand Settings)</h2>
        <p className="text-muted-foreground">
          Datos inmutables que definen la Identidad y Credibilidad de tu empresa ante el mundo.
        </p>
      </div>
      <div className="border-t my-6" />

      <div className="flex flex-col space-y-8 lg:flex-row lg:space-x-12 lg:space-y-0">
        <Tabs defaultValue="identity" className="flex flex-col lg:flex-row w-full space-y-6 lg:space-y-0 lg:space-x-12">
          <aside className="-mx-4 lg:w-1/5">
            <TabsList className="flex flex-col h-auto items-start justify-start bg-transparent p-0 space-y-1">
                
                {/* Grupo: Global */}
                <div className="w-full px-4 mb-2 mt-2">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Global
                  </h3>
                </div>
                
                <TabsTrigger 
                  value="identity" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Building2 className="mr-2 h-4 w-4" />
                  Información Corporativa
                </TabsTrigger>
                <TabsTrigger 
                  value="contact" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Phone className="mr-2 h-4 w-4" />
                  Datos de Contacto
                </TabsTrigger>

                {/* Grupo: Autoridad */}
                <div className="w-full px-4 mb-2 mt-6">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Autoridad
                  </h3>
                </div>

                <TabsTrigger 
                  value="key_figures" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Users className="mr-2 h-4 w-4" />
                  Key Figures
                </TabsTrigger>

                <TabsTrigger 
                  value="authority_vault" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <ShieldCheck className="mr-2 h-4 w-4" />
                  Respaldo Institucional
                </TabsTrigger>

                {/* Grupo: Marca */}
                <div className="w-full px-4 mb-2 mt-6">
                  <h3 className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
                    Marca
                  </h3>
                </div>

                <TabsTrigger 
                  value="avatars" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Users className="mr-2 h-4 w-4" />
                  Avatares
                </TabsTrigger>
                <TabsTrigger 
                  value="personality" 
                  className="w-full justify-start px-4 py-2 text-left font-medium hover:bg-muted/50 data-[state=active]:bg-muted data-[state=active]:shadow-none border-transparent"
                >
                  <Brain className="mr-2 h-4 w-4" />
                  Personalidad IA
                </TabsTrigger>

            </TabsList>
          </aside>

          <div className="flex-1 lg:max-w-4xl">
            <TabsContent value="identity" className="mt-0">
            <BrandIdentityForm 
                initialData={settings.identity} 
                onSave={handleSaveIdentity}
                isSaving={saving}
            />
            </TabsContent>
            
            <TabsContent value="contact" className="mt-0">
            <ContactDataForm 
                initialData={settings.contact}
                onSave={handleSaveContact}
                isSaving={saving}
            />
            </TabsContent>

            <TabsContent value="key_figures" className="mt-0">
            <KeyFiguresForm 
                initialData={settings.team}
                onSave={handleSaveTeam}
                isSaving={saving}
            />
            </TabsContent>

            <TabsContent value="authority_vault" className="mt-0">
            <AuthorityVaultForm 
                initialData={settings.authority_vault}
                onSave={handleSaveVault}
                isSaving={saving}
            />
            </TabsContent>

            <TabsContent value="avatars" className="mt-0">
                <AvatarManager />
            </TabsContent>

            <TabsContent value="personality" className="mt-0">
                <PersonalityCloneForm />
            </TabsContent>
          </div>
        </Tabs>
      </div>
    </div>
  );
}
